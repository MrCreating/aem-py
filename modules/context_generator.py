from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from modules import PairwiseMatrixGenerator

class ContextGenerator:
    """
    Генератор синтетических контекстов (JSON-структуры) для экспериментов AEM-COM
    """
    EXPERT_WEIGHTS_EQUAL = "equal"
    EXPERT_WEIGHTS_RANDOM = "random"

    # согласованность экспертов

    # они близки друг другу
    GROUP_ALIGNED = "aligned"
    # каждый сам за себя
    GROUP_CONFLICTING = "conflicting"
    # мнения разделились на 2 лагеря
    GROUP_TWO_CAMPS = "two_camps"

    EXPERT_MATRIX_CONSISTENT = "consistent"
    EXPERT_MATRIX_INCONSISTENT_SIGMA = "inconsistent_sigma"
    EXPERT_MATRIX_INCONSISTENT_TARGET_CR = "inconsistent_target_cr"
    EXPERT_MATRIX_RANDOM_SAATY = "random_saaty"

    COLLECTIVE_PCCM = "pccm"
    COLLECTIVE_FROM_EXPERT = "from_expert"
    COLLECTIVE_RANDOM_SAATY = "random_saaty"
    COLLECTIVE_CONSISTENT_FROM_SHARED = "consistent_from_shared"

    def __init__(self):
        self._seed: Optional[int] = None
        self._rng = random.Random()

        self._n_experts = 3
        self._n_criteria = 1
        self._n_alternatives = 5

        self._expert_weights_mode = self.EXPERT_WEIGHTS_RANDOM

        self._group_mode = self.GROUP_ALIGNED

        self._expert_matrix_mode = self.EXPERT_MATRIX_INCONSISTENT_TARGET_CR

        self._expert_sigma = 0.25
        self._expert_target_cr = 0.25
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

        self._aligned_noise_sigma = 0.10
        self._two_camps_split = 0.5
        self._two_camps_distance = 1.0

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

    def set_expert_weights_mode(self, mode: str):
        if mode not in (self.EXPERT_WEIGHTS_EQUAL, self.EXPERT_WEIGHTS_RANDOM):
            raise ValueError("Unknown weights mode")
        self._expert_weights_mode = mode
        return self

    def set_group_mode(self, mode: str):
        if mode not in (self.GROUP_ALIGNED, self.GROUP_CONFLICTING, self.GROUP_TWO_CAMPS):
            raise ValueError("Unknown group mode")
        self._group_mode = mode
        return self

    def set_expert_matrix_mode(
            self,
            mode: str,
            sigma: float = 0.25,
            target_cr: float = 0.25,
            quantize_to_saaty: bool = False,
            round_digits: Optional[int] = 3,
    ):
        if mode not in (
                self.EXPERT_MATRIX_CONSISTENT,
                self.EXPERT_MATRIX_INCONSISTENT_SIGMA,
                self.EXPERT_MATRIX_INCONSISTENT_TARGET_CR,
                self.EXPERT_MATRIX_RANDOM_SAATY,
        ):
            raise ValueError("Unknown expert matrix mode")

        self._expert_matrix_mode = mode
        self._expert_sigma = sigma
        self._expert_target_cr = target_cr
        self._quantize_to_saaty = quantize_to_saaty
        self._round_digits = round_digits
        return self

    def set_collective_mode(self, mode: str, from_expert_index: int = 0):
        if mode not in (
                self.COLLECTIVE_PCCM,
                self.COLLECTIVE_FROM_EXPERT,
                self.COLLECTIVE_RANDOM_SAATY,
                self.COLLECTIVE_CONSISTENT_FROM_SHARED,
        ):
            raise ValueError("Unknown collective mode")
        self._collective_mode = mode
        self._collective_from_expert_index = from_expert_index
        return self

    def set_aem_settings(
            self,
            p: float,
            strict_decrease: bool,
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

    def set_aligned_noise(self, sigma: float):
        self._aligned_noise_sigma = float(sigma)
        return self

    def set_two_camps(self, split: float = 0.5, distance: float = 1.0):
        self._two_camps_split = float(split)
        self._two_camps_distance = float(distance)
        return self

