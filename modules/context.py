from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from modules.group_builder import GroupBuilder
from entities import GroupAhpModel


class Context:
    def __init__(
        self,
        group_model: GroupAhpModel,
        result_save_path: Optional[str] = None,
    ) -> None:
        self._group_model = group_model
        self._result_save_path = result_save_path
        self._aem_com_result: Optional[Any] = None

    @classmethod
    def from_json_file(
        cls,
        path: Union[str, Path],
        *,
        result_save_path: Optional[str] = None,
    ) -> "Context":
        path_obj = Path(path)
        with path_obj.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        builder = GroupBuilder(data)
        group_model = builder.build()

        return cls(group_model=group_model, result_save_path=result_save_path)

    @property
    def group_model(self) -> GroupAhpModel:
        return self._group_model

    @property
    def result_save_path(self) -> Optional[str]:
        return self._result_save_path

    @result_save_path.setter
    def result_save_path(self, value: Optional[str]) -> None:
        self._result_save_path = value

    @property
    def aem_com_result(self) -> Optional[Any]:
        return self._aem_com_result

    @aem_com_result.setter
    def aem_com_result(self, value: Any) -> None:
        self._aem_com_result = value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self._group_model)

    def build_result_payload(self) -> Dict[str, Any]:
        if self._aem_com_result is None:
            raise ValueError("В контексте нет результата AEM-COM (Context.aem_com_result is None).")

        gm = self._group_model
        rho = float(gm.settings.aem_com.permissibility)

        details = asdict(self._aem_com_result) if is_dataclass(self._aem_com_result) else self._aem_com_result

        initial_sum = 0.0
        final_sum = 0.0
        min_sum = 0.0

        if getattr(self._aem_com_result, "criteria_result", None) is not None:
            run = self._aem_com_result.criteria_result.run
            initial_sum += float(run.gcompi_initial)
            final_sum += float(run.gcompi_final)
            min_sum += float(run.gcompi_min)

        alt_results = getattr(self._aem_com_result, "alternatives_results", {}) or {}
        for _, alt_res in alt_results.items():
            run = alt_res.run
            initial_sum += float(run.gcompi_initial)
            final_sum += float(run.gcompi_final)
            min_sum += float(run.gcompi_min)

        payload = self.to_dict()
        payload["result"] = {
            "aem_com": {
                "summary": {
                    "permissibility": rho,
                    "gcompi_initial_total": initial_sum,
                    "gcompi_final_total": final_sum,
                    "gcompi_min_total": min_sum,
                    "delta_total": (final_sum - initial_sum),
                    "improvement_total": (initial_sum - final_sum),
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                },
                "details": details,
            }
        }
        return payload

    def save_result_json(self) -> str:
        if not self._result_save_path:
            raise ValueError("result_save_path не задан в Context (некуда сохранять результат).")

        payload = self.build_result_payload()

        p = Path(self._result_save_path)

        if p.suffix.lower() != ".json":
            p.mkdir(parents=True, exist_ok=True)
            fname = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            out_path = (p / fname).resolve()
        else:
            if p.parent:
                p.parent.mkdir(parents=True, exist_ok=True)
            out_path = p.resolve()

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")

        return str(out_path)
