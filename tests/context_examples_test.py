from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from modules import ContextGenerator

SEED = 42
N_EXPERTS = 3
N_CRITERIA = 1
N_ALTS = 5

ROUND_DIGITS = 3

P_LIST = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

OUT_DIR = Path('../examples/auto')


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _p_to_name(p: float) -> str:
    return f"{p:.2f}".replace(".", "_")


def _save_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_ctx(
    *,
    p: float,
    kind: str,
    stamp: str,
    matrix_mode: str,
    strict: bool,
    target_cr: float | None = None,
    sigma: float | None = None,
    quantize: bool = False,
) -> dict:
    g = (
        ContextGenerator()
        .set_seed(SEED)
        .set_sizes(N_EXPERTS, N_CRITERIA, N_ALTS)
        .set_problem_meta(
            problem_id=f"auto_{_p_to_name(p)}_{kind}_{stamp}",
            name=f"AEM-COM auto context (p={p}, kind={kind})",
            description=f"Auto-generated context: p={p}, kind={kind}, seed={SEED}",
            goal="Снизить несовместимость (GCOMPI), меняя только коллективную матрицу",
        )
        .set_weights_mode(ContextGenerator.WEIGHTS_EQUAL)
        .set_aem_settings(
            p=p,
            strict_decrease=strict,
            max_iterations=100,
            initial_mode="pccm",
            apply_to=["alternatives_by_criterion"],
        )
        .set_collective_mode(ContextGenerator.COLLECTIVE_NONE)
    )

    kwargs = dict(
        mode=matrix_mode,
        quantize_to_saaty=quantize,
        round_digits=ROUND_DIGITS,
        target_cr=target_cr,
        sigma=sigma,
    )
    if target_cr is None:
        kwargs["target_cr"] = 0.25
    if sigma is None:
        kwargs["sigma"] = 0.15

    g.set_matrix_generation(**kwargs)

    return g.build(include_collective_matrix=False)

def main() -> int:
    stamp = _stamp()

    SCENARIOS = [
        ("ideal", ContextGenerator.MATRIX_CONSISTENT, True, None, None, False),
        ("realistic", ContextGenerator.MATRIX_INCONSISTENT_TARGET_CR, True, 0.12, None, False),
        ("each_own", ContextGenerator.MATRIX_INCONSISTENT_TARGET_CR, True, 0.35, None, False),
        ("nonsense", ContextGenerator.MATRIX_INCONSISTENT_TARGET_CR, False, 0.70, None, False),
        ("two_camps", ContextGenerator.MATRIX_INCONSISTENT_TARGET_CR, True, 0.25, None, False),
        ("max_inconsistent", ContextGenerator.MATRIX_INCONSISTENT_TARGET_CR, False, 1.00, None, False),
        ("random", ContextGenerator.MATRIX_RANDOM_SAATY, False, None, None, True),
    ]

    total = 0
    for p in P_LIST:
        for (kind, mode, strict, target_cr, sigma, quantize) in SCENARIOS:
            ctx = _build_ctx(
                p=p,
                kind=kind,
                stamp=stamp,
                matrix_mode=mode,
                strict=strict,
                target_cr=target_cr,
                sigma=sigma,
                quantize=quantize,
            )

            fname = f"{_p_to_name(p)}_{kind}_{stamp}.json"
            out_path = OUT_DIR / fname
            _save_json(out_path, ctx)
            total += 1
            print(f"OK: generated {fname} context to {out_path} with {kind} kind.")

    print(f"OK: generated {total} json files -> {OUT_DIR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())