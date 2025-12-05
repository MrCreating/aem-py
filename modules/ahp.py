from __future__ import annotations

from typing import Dict, List, Optional

from modules.context import Context
from modules.math import Math

from entities import (
    GroupAhpModel,
    PairwiseMatrix,
    AhpResult,
)


class AHP:
    """
    Реализация группового AHP (за основу взял реализацию https://github.com/DM-app-tools/AHP, но переписал на Python).

    Логика:
      - агрегирует матрицы экспертов по критериям и альтернативам
        через взвешенное геометрическое среднее (Aij с весами экспертов)
      - считает веса критериев и OS
      - считает локальные веса альтернатив по каждому критерию и OS
      - считает итоговые глобальные веса альтернатив

    На этом классе потом будет строиться AEM-COM
    """

    def __init__(self, context: Context, math: Optional[Math] = None) -> None:
        self._context = context
        self._math = math if math is not None else Math()

    def solve(self) -> AhpResult:
        group_model: GroupAhpModel = self._context.group_model

        expert_weights: Dict[str, float] = {
            e.id: e.weight for e in group_model.experts
        }

        agg_criteria_matrix, crit_items = self._aggregate_criteria_level(
            group_model=group_model,
            expert_weights=expert_weights,
        )

        criteria_weights_vec = self._math.compute_priority_vector(agg_criteria_matrix)
        criteria_weights: Dict[str, float] = {
            crit_items[i]: criteria_weights_vec[i]
            for i in range(len(crit_items))
        }

        crit_os = self._math.compute_relative_consistency(agg_criteria_matrix)
        crit_os_percent = self._math.consistency_to_percent(crit_os)

        alt_weights_by_criterion: Dict[str, Dict[str, float]] = {}
        alt_os_by_criterion: Dict[str, float] = {}
        alt_os_percent_by_criterion: Dict[str, float] = {}

        for criterion in group_model.model.criteria:
            c_id = criterion.id

            agg_alt_matrix, alt_items = self._aggregate_alternative_level_for_criterion(
                group_model=group_model,
                expert_weights=expert_weights,
                criterion_id=c_id,
            )

            if agg_alt_matrix is None or not alt_items:
                continue

            local_weights_vec = self._math.compute_priority_vector(agg_alt_matrix)
            alt_weights: Dict[str, float] = {
                alt_items[i]: local_weights_vec[i]
                for i in range(len(alt_items))
            }
            alt_weights_by_criterion[c_id] = alt_weights

            os = self._math.compute_relative_consistency(agg_alt_matrix)
            alt_os_by_criterion[c_id] = os
            alt_os_percent_by_criterion[c_id] = self._math.consistency_to_percent(os)

        global_alt_weights = self._compute_global_alternative_weights(
            criteria_weights=criteria_weights,
            alt_weights_by_criterion=alt_weights_by_criterion,
        )

        result = AhpResult(
            criteria_weights=criteria_weights,
            criteria_consistency_os=crit_os,
            criteria_consistency_percent=crit_os_percent,
            alt_weights_by_criterion=alt_weights_by_criterion,
            alt_consistency_os_by_criterion=alt_os_by_criterion,
            alt_consistency_percent_by_criterion=alt_os_percent_by_criterion,
            global_alt_weights=global_alt_weights,
        )

        return result

    def _aggregate_criteria_level(
        self,
        group_model: GroupAhpModel,
        expert_weights: Dict[str, float],
    ) -> tuple[List[List[float]], List[str]]:
        matrices: List[PairwiseMatrix] = group_model.pairwise_matrices.criteria_level

        if not matrices:
            raise ValueError("В контексте нет матриц уровня критериев")

        base_items = matrices[0].items
        n = len(base_items)

        aggregated: List[List[float]] = [
            [1.0 for _ in range(n)] for _ in range(n)
        ]

        total_weight = sum(max(expert_weights.get(m.expert_id, 0.0), 0.0) for m in matrices)
        if total_weight == 0.0:
            total_weight = float(len(matrices))

        for m in matrices:
            w_k = expert_weights.get(m.expert_id, 0.0)
            if w_k < 0.0:
                w_k = 0.0

            w_rel = w_k / total_weight if total_weight > 0 else 0.0

            index_map = self._build_index_map(base_items, m.items)

            for i in range(n):
                for j in range(n):
                    mi = index_map[i]
                    mj = index_map[j]
                    value = m.matrix[mi][mj]

                    if value > 0.0 and w_rel > 0.0:
                        aggregated[i][j] *= value ** w_rel

        return aggregated, base_items

    def _aggregate_alternative_level_for_criterion(
        self,
        group_model: GroupAhpModel,
        expert_weights: Dict[str, float],
        criterion_id: str,
    ) -> tuple[Optional[List[List[float]]], List[str]]:
        matrices = [
            m for m in group_model.pairwise_matrices.alternative_level
            if m.criterion_id == criterion_id
        ]

        if not matrices:
            return None, []

        base_items = matrices[0].items
        n = len(base_items)

        aggregated: List[List[float]] = [
            [1.0 for _ in range(n)] for _ in range(n)
        ]

        total_weight = sum(max(expert_weights.get(m.expert_id, 0.0), 0.0) for m in matrices)
        if total_weight == 0.0:
            total_weight = float(len(matrices))

        for m in matrices:
            w_k = expert_weights.get(m.expert_id, 0.0)
            if w_k < 0.0:
                w_k = 0.0
            w_rel = w_k / total_weight if total_weight > 0 else 0.0

            index_map = self._build_index_map(base_items, m.items)

            for i in range(n):
                for j in range(n):
                    mi = index_map[i]
                    mj = index_map[j]
                    value = m.matrix[mi][mj]
                    if value > 0.0 and w_rel > 0.0:
                        aggregated[i][j] *= value ** w_rel

        return aggregated, base_items

    @staticmethod
    def _build_index_map(base_items: List[str], other_items: List[str]) -> List[int]:
        pos: Dict[str, int] = {item: idx for idx, item in enumerate(other_items)}
        index_map: List[int] = []
        for item in base_items:
            if item not in pos:
                raise ValueError(f"Элемент '{item}' отсутствует в матрице эксперта")
            index_map.append(pos[item])
        return index_map

    @staticmethod
    def _compute_global_alternative_weights(
        criteria_weights: Dict[str, float],
        alt_weights_by_criterion: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        global_weights: Dict[str, float] = {}

        for c_id, w_c in criteria_weights.items():
            alt_weights = alt_weights_by_criterion.get(c_id, {})
            for alt_id, w_local in alt_weights.items():
                global_weights[alt_id] = global_weights.get(alt_id, 0.0) + w_c * w_local

        total = sum(global_weights.values())
        if total > 0.0:
            for alt_id in list(global_weights.keys()):
                global_weights[alt_id] = global_weights[alt_id] / total

        return global_weights