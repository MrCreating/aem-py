from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from modules.group_builder import GroupBuilder

from entities import (
    GroupAhpModel,
)

class Context:
    def __init__(self, group_model: GroupAhpModel) -> None:
        self._group_model = group_model

    @classmethod
    def from_json_file(cls, path: str | Path) -> Context:
        path_obj = Path(path)
        with path_obj.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        builder = GroupBuilder(data)
        group_model = builder.build()

        return cls(group_model)

    @property
    def group_model(self) -> GroupAhpModel:
        return self._group_model

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self._group_model)