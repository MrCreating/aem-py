from __future__ import annotations

import json
import sys
import subprocess
from datetime import datetime
from numbers import Number
from pathlib import Path
from typing import Any, Dict, Optional


CONTEXTS_DIR = Path("../examples/auto")
OUT_DIR = Path("../out/auto")
PYTHON = sys.executable
MAIN = Path("../main.py")

CONTEXT_GLOB = "*.json"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def _pct(improvement: float, initial: float) -> float:
    if initial <= 0:
        return 0.0
    return (improvement / initial) * 100.0


def _extract_summary(result_obj: Dict[str, Any]) -> Dict[str, Any]:
    summary = (
        result_obj.get("result", {})
        .get("aem_com", {})
        .get("summary", {})
    )

    gi = _safe_float(summary.get("gcompi_initial_total", 0.0)) or 0.0
    gf = _safe_float(summary.get("gcompi_final_total", 0.0)) or 0.0
    imp = _safe_float(summary.get("improvement_total", gi - gf)) or (gi - gf)
    delta = _safe_float(summary.get("delta_total", gf - gi)) or (gf - gi)
    p = summary.get("permissibility", None)

    eff = _pct(imp, gi)

    return {
        "p": p,
        "g_initial": gi,
        "g_final": gf,
        "improvement": imp,
        "delta": delta,
        "eff_pct": eff,
    }


def run_one(context_path: Path, out_dir: Path, i: Number, all_files: Number) -> None:
    cmd = [
        PYTHON,
        str(MAIN),
        "-a",
        "-f", str(context_path),
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"AEM-COM {context_path.name} - ERROR: {err}")
        return

    raw = (proc.stdout or "").strip()
    if not raw:
        print(f"AEM-COM {context_path.name} - ERROR: empty stdout (no json)")
        return

    try:
        result_obj = json.loads(raw)
    except Exception as e:
        print(
            f"AEM-COM {context_path.name} - ERROR: stdout is not valid JSON: {e}"
        )
        return

    summary = _extract_summary(result_obj)

    out_dir.mkdir(parents=True, exist_ok=True)

    ts = _now_stamp()
    out_name = f"{ts}_{context_path.stem}.json"
    out_path = out_dir / out_name

    out_path.write_text(
        json.dumps(result_obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    p = summary["p"]
    gi = summary["g_initial"]
    gf = summary["g_final"]
    imp = summary["improvement"]
    eff = summary["eff_pct"]

    print(
        f"[{i}/{all_files}] "
        f"AEM-COM {context_path.name} - OK: "
        f"p={p} | G0={gi:.6f} -> Gf={gf:.6f} | "
        f"Δ={imp:.6f} | eff={eff:.2f}% | saved={out_path}"
    )


def main() -> int:
    if not MAIN.exists():
        print(f"ERROR: не найден {MAIN}. Запускай скрипт из корня проекта.")
        return 2

    if not CONTEXTS_DIR.exists():
        print(f"ERROR: не найдена папка {CONTEXTS_DIR}")
        return 2

    ctx_files = sorted(CONTEXTS_DIR.glob(CONTEXT_GLOB))
    if not ctx_files:
        print(f"ERROR: в {CONTEXTS_DIR} нет файлов по маске {CONTEXT_GLOB}")
        return 2

    print(f"Found {len(ctx_files)} contexts in {CONTEXTS_DIR.as_posix()}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, ctx in enumerate(ctx_files, start=1):
        run_one(ctx, OUT_DIR, i, len(ctx_files))

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
