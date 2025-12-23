from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional

from modules import PairwiseMatrixGenerator


class ContextGenerator:
    """
    Генератор полного контекста
    """

    # веса экспертов
    WEIGHTS_EQUAL = "equal"
    WEIGHTS_RANDOM = "random"

    # режимы генерации матриц экспертов
    MATRIX_CONSISTENT = "consistent"
    MATRIX_INCONSISTENT_SIGMA = "inconsistent_sigma"
    MATRIX_INCONSISTENT_TARGET_CR = "inconsistent_target_cr"
    MATRIX_RANDOM_SAATY = "random_saaty"

    # режимы начальной коллективной матрицы
    COLLECTIVE_NONE = "none"
    COLLECTIVE_PCCM = "pccm"
    COLLECTIVE_FROM_EXPERT = "from_expert"
    COLLECTIVE_RANDOM_SAATY = "random_saaty"

    def __init__(self):
        self._seed: Optional[int] = None
        self._rng = random.Random()

        self._n_experts = 3
        self._n_criteria = 1
        self._n_alternatives = 5

        self._weights_mode = self.WEIGHTS_RANDOM

        self._matrix_mode = self.MATRIX_INCONSISTENT_TARGET_CR
        self._sigma = 0.25
        self._target_cr = 0.25
        self._quantize_to_saaty = False
        self._round_digits: Optional[int] = 3

        self._collective_mode = self.COLLECTIVE_PCCM
        self._collective_from_expert_index = 0

        self._problem_id = "synthetic_context"
        self._problem_name = "Synthetic AEM-COM context"
        self._problem_desc = "Synthetic dataset for AEM-COM tests"
        self._problem_goal = "Reduce incompatibility (GCOMPI) by changing collective matrix"

        self._aem_p = 0.25
        self._aem_strict = True
        self._aem_max_iter = 100
        self._aem_apply_to = ["alternatives_by_criterion"]
        self._aem_initial_mode = "pccm"

    def set_seed(self, seed: Optional[int]):
        self._seed = seed
        self._rng = random.Random(seed)
        return self

    def set_sizes(self, n_experts: int, n_criteria: int, n_alternatives: int):
        if n_experts < 1:
            raise ValueError("n_experts must be >= 1")
        if n_criteria < 1:
            raise ValueError("n_criteria must be >= 1")
        if n_alternatives < 2:
            raise ValueError("n_alternatives must be >= 2")
        self._n_experts = n_experts
        self._n_criteria = n_criteria
        self._n_alternatives = n_alternatives
        return self

    def set_problem_meta(self, problem_id: str, name: str, description: str, goal: str):
        self._problem_id = problem_id
        self._problem_name = name
        self._problem_desc = description
        self._problem_goal = goal
        return self

    def set_weights_mode(self, mode: str):
        if mode not in (self.WEIGHTS_EQUAL, self.WEIGHTS_RANDOM):
            raise ValueError("Unknown weights mode")
        self._weights_mode = mode
        return self

    def set_matrix_generation(
        self,
        mode: str,
        *,
        sigma: float = 0.25,
        target_cr: float = 0.25,
        quantize_to_saaty: bool = False,
        round_digits: Optional[int] = 3,
    ):
        if mode not in (
            self.MATRIX_CONSISTENT,
            self.MATRIX_INCONSISTENT_SIGMA,
            self.MATRIX_INCONSISTENT_TARGET_CR,
            self.MATRIX_RANDOM_SAATY,
        ):
            raise ValueError("Unknown matrix mode")

        self._matrix_mode = mode
        self._sigma = float(sigma)
        self._target_cr = float(target_cr)
        self._quantize_to_saaty = bool(quantize_to_saaty)
        self._round_digits = round_digits
        return self

    def set_collective_mode(self, mode: str, from_expert_index: int = 0):
        if mode not in (
            self.COLLECTIVE_NONE,
            self.COLLECTIVE_PCCM,
            self.COLLECTIVE_FROM_EXPERT,
            self.COLLECTIVE_RANDOM_SAATY,
        ):
            raise ValueError("Unknown collective mode")
        self._collective_mode = mode
        self._collective_from_expert_index = int(from_expert_index)
        return self

    def set_aem_settings(
        self,
        p: float,
        strict_decrease: bool,
        *,
        max_iterations: int = 100,
        initial_mode: str = "pccm",
        apply_to: Optional[List[str]] = None,
    ):
        self._aem_p = float(p)
        self._aem_strict = bool(strict_decrease)
        self._aem_max_iter = int(max_iterations)
        self._aem_initial_mode = str(initial_mode)
        if apply_to is not None:
            self._aem_apply_to = list(apply_to)
        return self

    def build(self, include_collective_matrix: bool = True) -> Dict[str, Any]:
        experts = self._build_experts()
        criteria = self._build_criteria()
        alternatives = self._build_alternatives()

        criteria_level = self._build_criteria_level(experts, criteria)
        alternative_level = self._build_alternative_level(experts, criteria, alternatives)

        ctx: Dict[str, Any] = {
            "problem": {
                "id": self._problem_id,
                "name": self._problem_name,
                "description": self._problem_desc,
                "goal": self._problem_goal,
            },
            "experts": experts,
            "model": {"criteria": criteria, "alternatives": alternatives},
            "settings": {
                "ahp_scale": "saaty_1_9",
                "aem_com": {
                    "strict_decrease": self._aem_strict,
                    "permissibility": self._aem_p,
                    "apply_to": self._aem_apply_to,
                    "max_iterations": self._aem_max_iter,
                    "initial_mode": self._aem_initial_mode,
                },
            },
            "pairwise_matrices": {
                "criteria_level": criteria_level,
                "alternative_level": alternative_level,
            },
        }

        if include_collective_matrix and self._collective_mode != self.COLLECTIVE_NONE:
            collective = self._build_collective_matrix(experts, criteria, alternatives, alternative_level)
            if collective is not None:
                ctx["pairwise_matrices"]["collective_matrix"] = collective

        return ctx

    # сборка

    def _build_experts(self) -> List[Dict[str, Any]]:
        weights = self._generate_weights(self._n_experts, self._weights_mode)

        out: List[Dict[str, Any]] = []
        for i in range(self._n_experts):
            out.append(
                {
                    "id": f"e{i+1}",
                    "name": f"DM{i+1}",
                    "role": f"Decision Maker {i+1}",
                    "weight": weights[i],
                }
            )
        return out

    def _build_criteria(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for i in range(self._n_criteria):
            out.append({"id": f"C{i}", "name": f"Criterion {i}", "description": f"synthetic criterion {i}"})
        return out

    def _build_alternatives(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for i in range(self._n_alternatives):
            out.append({"id": f"A{i+1}", "name": f"Alternative {i+1}", "description": str(i + 1)})
        return out

    def _build_criteria_level(self, experts: List[Dict[str, Any]], criteria: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(criteria) == 1:
            c_id = criteria[0]["id"]
            return [{"expert_id": e["id"], "items": [c_id], "matrix": [[1.0]]} for e in experts]

        out: List[Dict[str, Any]] = []
        for ei, e in enumerate(experts):
            gen = self._new_mps_generator(seed_offset=1000 + ei, n=len(criteria))
            a = self._generate_matrix(gen)
            out.append({"expert_id": e["id"], "items": [c["id"] for c in criteria], "matrix": a})
        return out

    def _build_alternative_level(
        self,
        experts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        alternatives: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        items = [a["id"] for a in alternatives]

        for ci, c in enumerate(criteria):
            c_id = c["id"]
            for ei, e in enumerate(experts):
                gen = self._new_mps_generator(seed_offset=2000 + ci * 100 + ei, n=len(alternatives))
                a = self._generate_matrix(gen)
                out.append({"criterion_id": c_id, "expert_id": e["id"], "items": items, "matrix": a})

        return out

    def _build_collective_matrix(
        self,
        experts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        alternatives: List[Dict[str, Any]],
        alternative_level: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if len(criteria) != 1:
            return None

        items = [a["id"] for a in alternatives]

        if self._collective_mode == self.COLLECTIVE_PCCM:
            return {"method": "PCCM", "items": items, "matrix": [[1.0 if i == j else 1.0 for j in range(len(items))] for i in range(len(items))]}

        if self._collective_mode == self.COLLECTIVE_RANDOM_SAATY:
            gen = self._new_mps_generator(seed_offset=9000, n=len(items))
            gen.quantize_to_saaty(True)
            a = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_RANDOM_SAATY)
            return {"method": "RANDOM_SAATY", "items": items, "matrix": a}

        if self._collective_mode == self.COLLECTIVE_FROM_EXPERT:
            idx = max(0, min(len(experts) - 1, self._collective_from_expert_index))
            expert_id = experts[idx]["id"]

            c_id = criteria[0]["id"]
            for row in alternative_level:
                if row["criterion_id"] == c_id and row["expert_id"] == expert_id:
                    return {"method": "FROM_EXPERT", "items": items, "matrix": row["matrix"]}
            return None

        return None

    def _new_mps_generator(self, seed_offset: int, n: int) -> PairwiseMatrixGenerator:
        base_seed = 0 if self._seed is None else int(self._seed)
        gen = PairwiseMatrixGenerator().set_seed(base_seed + seed_offset).set_n(n).set_round_digits(self._round_digits)
        if self._quantize_to_saaty:
            gen.quantize_to_saaty(True)
        return gen

    def _generate_matrix(self, gen: PairwiseMatrixGenerator) -> List[List[float]]:
        if self._matrix_mode == self.MATRIX_CONSISTENT:
            return gen.generate_pairwise(PairwiseMatrixGenerator.MODE_CONSISTENT)

        if self._matrix_mode == self.MATRIX_RANDOM_SAATY:
            gen.quantize_to_saaty(True)
            return gen.generate_pairwise(PairwiseMatrixGenerator.MODE_RANDOM_SAATY)

        if self._matrix_mode == self.MATRIX_INCONSISTENT_SIGMA:
            gen.set_sigma(self._sigma)
            return gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

        if self._matrix_mode == self.MATRIX_INCONSISTENT_TARGET_CR:
            gen.set_target_cr(self._target_cr)
            return gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

        raise ValueError("Unknown matrix mode")

    def _generate_weights(self, n: int, mode: str) -> List[float]:
        if mode == self.WEIGHTS_EQUAL:
            return [1.0 / n] * n

        if mode == self.WEIGHTS_RANDOM:
            vals = [math.exp(self._rng.uniform(-1.0, 1.0)) for _ in range(n)]
            s = sum(vals)
            return [v / s for v in vals]

        raise ValueError("Unknown weights mode")
