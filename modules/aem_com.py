from __future__ import annotations

import copy
import math
from typing import Dict, List, Optional, Tuple

from modules.context import Context
from modules.math import Math
from modules.gcompi import GcompiCalculator

from entities import (
    GroupAhpModel,
    PairwiseMatrix,
    AemComIterationRecord,
    AemComRunResult,
    CriteriaLevelAemComResult,
    AlternativeLevelAemComResult,
    AemComGlobalResult,
)


class AemCom:
    def __init__(
        self,
        context: Context,
        ahp_math: Optional[Math] = None,
        gcompi: Optional[GcompiCalculator] = None,
        permissibility: Optional[float] = None,
        max_iterations: Optional[int] = None,
    ) -> None:
        self._context = context
        self._math = ahp_math if ahp_math is not None else Math()
        self._gcompi = gcompi if gcompi is not None else GcompiCalculator()

        settings = self._context.group_model.settings.aem_com
        self._rho = permissibility if permissibility is not None else settings.permissibility
        self._max_iterations = max_iterations if max_iterations is not None else settings.max_iterations
        self._initial_mode = getattr(settings, "initial_mode", "aij")

        self._strict_decrease = getattr(settings, "strict_decrease", False)

    def run_on_criteria_level(self) -> CriteriaLevelAemComResult:
        group_model = self._context.group_model
        matrices = group_model.pairwise_matrices.criteria_level

        if not matrices:
            raise ValueError("Нет матриц уровня критериев (criteria_level).")

        items = matrices[0].items
        A_family, alpha = self._extract_family(matrices)
        P_provided = self._get_provided_collective_matrix(criterion_id=None, items=items)
        P0 = self._build_initial_matrix(
            matrices=A_family,
            expert_weights=alpha,
            items=items,
            provided_matrix=P_provided,
        )

        run_result = self._run_aem_com(
            family_matrices=A_family,
            expert_weights=alpha,
            items=items,
            initial_P=P0,
        )

        return CriteriaLevelAemComResult(
            level="criteria",
            run=run_result,
        )

    def run_on_alternative_level_for_criterion(
            self,
            criterion_id: str,
    ) -> AlternativeLevelAemComResult:
        group_model = self._context.group_model
        all_mats = group_model.pairwise_matrices.alternative_level

        matrices = [m for m in all_mats if m.criterion_id == criterion_id]

        if not matrices:
            raise ValueError(f"Нет матриц альтернатив для критерия '{criterion_id}'.")

        items = matrices[0].items
        A_family, alpha = self._extract_family(matrices)
        P_provided = self._get_provided_collective_matrix(criterion_id=criterion_id, items=items)
        P0 = self._build_initial_matrix(
            matrices=A_family,
            expert_weights=alpha,
            items=items,
            provided_matrix=P_provided,
        )

        run_result = self._run_aem_com(
            family_matrices=A_family,
            expert_weights=alpha,
            items=items,
            initial_P=P0,
        )

        return AlternativeLevelAemComResult(
            level="alternatives",
            criterion_id=criterion_id,
            run=run_result,
        )

    def run_full(self) -> AemComGlobalResult:
        group_model = self._context.group_model
        apply_to = group_model.settings.aem_com.apply_to

        criteria_result: Optional[CriteriaLevelAemComResult] = None
        alternatives_results: Dict[str, AlternativeLevelAemComResult] = {}

        total_iterations = 0
        levels_count = 0

        if "criteria" in apply_to:
            criteria_result = self.run_on_criteria_level()
            total_iterations += criteria_result.run.iterations
            levels_count += 1

        if "alternatives_by_criterion" in apply_to:
            for criterion in group_model.model.criteria:
                c_id = criterion.id
                alt_result = self.run_on_alternative_level_for_criterion(c_id)
                alternatives_results[c_id] = alt_result
                total_iterations += alt_result.run.iterations
                levels_count += 1

        global_result = AemComGlobalResult(
            criteria_result=criteria_result,
            alternatives_results=alternatives_results,
            total_iterations=total_iterations,
            levels_count=levels_count,
        )

        self._context.aem_com_result = global_result
        return global_result

    def _extract_family(
            self,
            matrices: List[PairwiseMatrix],
    ) -> Tuple[List[List[List[float]]], List[float]]:
        group_model: GroupAhpModel = self._context.group_model
        weights_by_id: Dict[str, float] = {e.id: e.weight for e in group_model.experts}

        family: List[List[List[float]]] = []
        alpha: List[float] = []

        for m in matrices:
            w_k = weights_by_id.get(m.expert_id, 0.0)
            family.append(m.matrix)
            alpha.append(max(w_k, 0.0))

        return family, alpha

    def _get_provided_collective_matrix(
            self,
            criterion_id: Optional[str],
            items: List[str],
    ) -> Optional[List[List[float]]]:
        group_model = self._context.group_model
        candidates = getattr(group_model.pairwise_matrices, "collective_level", [])
        for pm in candidates:
            if pm.criterion_id != criterion_id:
                continue
            if list(pm.items) != list(items):
                continue
            if not pm.matrix:
                continue
            if len(pm.matrix) != len(items):
                continue
            if any(len(row) != len(items) for row in pm.matrix):
                continue
            return pm.matrix
        return None

    @staticmethod
    def _build_aij_matrix(matrices: List[List[List[float]]], expert_weights: List[float]) -> List[List[float]]:
        if not matrices:
            raise ValueError("Пустое семейство матриц для AIJ.")

        n = len(matrices[0])
        for mat in matrices:
            if len(mat) != n:
                raise ValueError("Все матрицы в семействе должны иметь одинаковый размер.")

        total_w = sum(max(w, 0.0) for w in expert_weights)
        if total_w == 0.0:
            w_norm = [1.0 / len(expert_weights)] * len(expert_weights)
        else:
            w_norm = [max(w, 0.0) / total_w for w in expert_weights]

        aij: List[List[float]] = [[1.0 for _ in range(n)] for _ in range(n)]

        for k, mat in enumerate(matrices):
            alpha_k = w_norm[k]
            if alpha_k == 0.0:
                continue
            for i in range(n):
                for j in range(n):
                    val = mat[i][j]
                    if val <= 0.0:
                        continue
                    aij[i][j] *= val ** alpha_k

        return aij

    def _run_aem_com(
        self,
        family_matrices: List[List[List[float]]],
        expert_weights: List[float],
        items: List[str],
        initial_P: List[List[float]],
    ) -> AemComRunResult:
        n = len(items)
        history: List[AemComIterationRecord] = []

        if n <= 2:
            P = copy.deepcopy(initial_P)
            v0 = self._math.compute_priority_vector(P)
            wG = v0[:]
            gcompi_init = self._gcompi.gcompi_family(family_matrices, expert_weights, v0)
            gcompi_min = self._gcompi.gcompi_family(family_matrices, expert_weights, wG)

            return AemComRunResult(
                items=list(items),
                initial_matrix=copy.deepcopy(initial_P),
                final_matrix=copy.deepcopy(P),
                initial_priorities=list(v0),
                final_priorities=list(v0),
                group_priorities=list(wG),
                gcompi_initial=gcompi_init,
                gcompi_final=gcompi_init,
                gcompi_min=gcompi_min,
                iterations=0,
                history=history,
            )

        P = copy.deepcopy(initial_P)
        v0 = self._math.compute_priority_vector(P)

        AIJ = self._build_aij_matrix(family_matrices, expert_weights)
        wG = self._math.compute_priority_vector(AIJ)

        gcompi_initial = self._gcompi.gcompi_family(family_matrices, expert_weights, v0)
        gcompi_min = self._gcompi.gcompi_family(family_matrices, expert_weights, wG)

        v = v0[:]
        gcompi_current = gcompi_initial

        J: List[Tuple[int, int]] = [(r, s) for r in range(n) for s in range(r + 1, n)]
        iterations = 0

        while J and iterations < self._max_iterations:
            q_values: Dict[Tuple[int, int], float] = {}
            log_q_values: Dict[Tuple[int, int], float] = {}

            for (r, s) in J:
                num = v[r] / v[s]
                den = wG[r] / wG[s] if wG[s] != 0 else 1.0
                if den == 0.0:
                    q = 1.0
                else:
                    q = num / den
                q_values[(r, s)] = q

                if q <= 0.0:
                    log_q = 0.0
                else:
                    log_q = math.log(q)
                log_q_values[(r, s)] = log_q

            chosen_pair: Optional[Tuple[int, int]] = None
            max_abs_log_q = -1.0

            for pair, log_q in log_q_values.items():
                abs_val = abs(log_q)
                if abs_val > max_abs_log_q:
                    max_abs_log_q = abs_val
                    chosen_pair = pair

            if chosen_pair is None or max_abs_log_q <= 0.0:
                break

            r_star, s_star = chosen_pair

            if P[r_star][s_star] > 1.0:
                r = r_star
                s = s_star
            else:
                r = s_star
                s = r_star

            key_minmax = (min(r, s), max(r, s))
            q_rs = q_values.get(key_minmax, 1.0)
            log_q_rs = log_q_values.get(key_minmax, 0.0)

            if q_rs <= 0.0:
                t_star = 1.0
            else:
                t_star = q_rs ** (-n / 2.0)

            if log_q_rs < 0.0:
                t_rs = min(1.0 + self._rho, t_star)
            elif log_q_rs > 0.0:
                t_bound = 1.0 / (1.0 + self._rho) if (1.0 + self._rho) != 0.0 else 1.0
                t_rs = max(t_bound, t_star)
            else:
                t_rs = 1.0

            old_val = P[r][s]
            new_val = old_val * t_rs

            lower = 1.0 / 9.0
            upper = 9.0
            if new_val < lower:
                new_val = lower
            if new_val > upper:
                new_val = upper

            P[r][s] = new_val
            P[s][r] = 1.0 / new_val

            J = [
                (i, j)
                for (i, j) in J
                if not ((i == r_star and j == s_star) or (i == s_star and j == r_star))
            ]

            v_new = self._math.compute_priority_vector(P)
            gcompi_new = self._gcompi.gcompi_family(family_matrices, expert_weights, v_new)

            if self._strict_decrease and gcompi_new >= gcompi_current:
                P[r][s] = old_val
                P[s][r] = 1.0 / old_val
                continue

            iterations += 1
            v = v_new
            gcompi_current = gcompi_new

            pair_items = (items[r], items[s])
            history.append(
                AemComIterationRecord(
                    iteration=iterations,
                    pair_indices=(r, s),
                    pair_items=pair_items,
                    t_rs=t_rs,
                    old_value=old_val,
                    new_value=new_val,
                    gcompi_value=gcompi_current,
                )
            )

        return AemComRunResult(
            items=list(items),
            initial_matrix=copy.deepcopy(initial_P),
            final_matrix=copy.deepcopy(P),
            initial_priorities=list(v0),
            final_priorities=list(v),
            group_priorities=list(wG),
            gcompi_initial=gcompi_initial,
            gcompi_final=gcompi_current,
            gcompi_min=gcompi_min,
            iterations=iterations,
            history=history,
        )

    def _build_initial_matrix(
        self,
        matrices: List[List[List[float]]],
        expert_weights: List[float],
        items: List[str],
        provided_matrix: Optional[List[List[float]]] = None,
    ) -> List[List[float]]:
        mode = (self._initial_mode or "aij").lower()

        if mode in {"provided_collective_matrix", "provided", "pccm", "collective"}:
            if provided_matrix is None:
                raise ValueError(
                    "initial_mode запрошен как 'provided_collective_matrix', но в JSON не передана соответствующая матрица (pairwise_matrices.collective_matrix/collective_level)."
                )
            return [row[:] for row in provided_matrix]

        if mode == "aij":
            return self._build_aij_matrix(matrices, expert_weights)

        n = len(items)

        if mode == "first_expert":
            if not matrices:
                raise ValueError("Пустой список матриц при initial_mode='first_expert'.")

            first = matrices[0]
            return [row[:] for row in first]

        if mode == "identity":
            return [[1.0 for _ in range(n)] for _ in range(n)]

        return self._build_aij_matrix(matrices, expert_weights)
