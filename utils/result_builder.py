import dataclasses
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any

from modules import Context


def build_result_block(context: Context, global_result: Any) -> Dict[str, Any]:
    gm = context.group_model
    rho = gm.settings.aem_com.permissibility

    result_dict = asdict(global_result) if dataclasses.is_dataclass(global_result) else global_result

    initial_sum = 0.0
    final_sum = 0.0
    min_sum = 0.0

    if getattr(global_result, "criteria_result", None) is not None:
        run = global_result.criteria_result.run
        initial_sum += float(run.gcompi_initial)
        final_sum += float(run.gcompi_final)
        min_sum += float(run.gcompi_min)

    alt_results = getattr(global_result, "alternatives_results", {}) or {}
    for _, alt_res in alt_results.items():
        run = alt_res.run
        initial_sum += float(run.gcompi_initial)
        final_sum += float(run.gcompi_final)
        min_sum += float(run.gcompi_min)

    summary = {
        "permissibility": float(rho),
        "gcompi_initial_total": initial_sum,
        "gcompi_final_total": final_sum,
        "gcompi_min_total": min_sum,
        "delta_total": (final_sum - initial_sum),
        "improvement_total": (initial_sum - final_sum),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    return {
        "aem_com": {
            "summary": summary,
            "details": result_dict,
        }
    }