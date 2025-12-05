from __future__ import annotations

from dataclasses import asdict
from typing import List, Tuple

from modules import (
    Context,
    Math
)

from entities import (
    GroupAhpModel,
    PairwiseMatrix,
)


class Validator:
    def __init__(self, context: Context) -> None:
        self._context = context
        self._errors: List[str] = []
        self._ahp_math = Math()

    def validate(self, strict: bool = False) -> int:
        self._errors = []

        group_model = self._context.group_model

        checks_total = 0
        checks_passed = 0

        for ok, msg in self._check_problem(group_model):
            checks_total += 1
            if ok:
                checks_passed += 1
            else:
                self._errors.append(msg)

        for ok, msg in self._check_experts(group_model, strict=strict):
            checks_total += 1
            if ok:
                checks_passed += 1
            else:
                self._errors.append(msg)

        for ok, msg in self._check_model(group_model):
            checks_total += 1
            if ok:
                checks_passed += 1
            else:
                self._errors.append(msg)

        for ok, msg in self._check_pairwise_matrices(group_model, strict=strict):
            checks_total += 1
            if ok:
                checks_passed += 1
            else:
                self._errors.append(msg)

        if checks_total == 0:
            return 0

        percent = int(round(100.0 * checks_passed / checks_total))

        if strict and self._errors:
            if percent == 100:
                percent = 99

        return percent

    def validate_consistency(self) -> List[Tuple[PairwiseMatrix, float]]:
        result: List[Tuple[PairwiseMatrix, float]] = []
        group_model: GroupAhpModel = self._context.group_model

        for m in group_model.pairwise_matrices.criteria_level:
            os = self._ahp_math.compute_relative_consistency(m.matrix)
            perc = self._ahp_math.consistency_to_percent(os)
            result.append((m, perc))

        for m in group_model.pairwise_matrices.alternative_level:
            os = self._ahp_math.compute_relative_consistency(m.matrix)
            perc = self._ahp_math.consistency_to_percent(os)
            result.append((m, perc))

        return result

    def get_errors(self) -> List[str]:
        return list(self._errors)

    @staticmethod
    def _check_problem(group_model: GroupAhpModel) -> List[Tuple[bool, str]]:
        checks: List[Tuple[bool, str]] = []

        p = group_model.problem

        checks.append((
            bool(p.id.strip()),
            "Не задан problem.id" if not p.id.strip() else "",
        ))
        checks.append((
            bool(p.name.strip()),
            "Не задан problem.name" if not p.name.strip() else "",
        ))
        checks.append((
            bool(p.goal.strip()),
            "Не задан problem.goal" if not p.goal.strip() else "",
        ))

        checks.append((
            bool(p.description.strip()),
            "Рекомендуется заполнить problem.description" if not p.description.strip() else "",
        ))

        return [(ok, msg) for ok, msg in checks if msg or not ok]

    @staticmethod
    def _check_experts(group_model: GroupAhpModel, strict: bool) -> List[Tuple[bool, str]]:
        checks: List[Tuple[bool, str]] = []

        experts = group_model.experts
        checks.append((
            len(experts) > 0,
            "Список экспертов пуст (experts).",
        ))

        total_weight = 0.0
        for e in experts:
            checks.append((
                bool(e.id.strip()),
                f"Эксперт без id: {asdict(e)}" if not e.id.strip() else "",
            ))
            checks.append((
                bool(e.name.strip()),
                f"Эксперт {e.id} без name." if not e.name.strip() else "",
            ))
            checks.append((
                e.weight >= 0.0,
                f"Вес эксперта {e.id} отрицательный: {e.weight}." if e.weight < 0.0 else "",
            ))
            total_weight += max(e.weight, 0.0)

        if experts:
            if strict:
                ok = abs(total_weight - 1.0) < 1e-6
                msg = f"Сумма весов экспертов должна быть 1.0, сейчас {total_weight:.6f}."
                checks.append((ok, msg if not ok else ""))
            else:
                ok = True
                if abs(total_weight - 1.0) > 0.05 and len(experts) > 0:
                    ok = False
                    msg = (
                        f"Сумма весов экспертов заметно отличается от 1.0 "
                        f"(сейчас {total_weight:.3f})."
                    )
                else:
                    msg = ""
                checks.append((ok, msg))

        return [(ok, msg) for ok, msg in checks if msg or not ok]

    @staticmethod
    def _check_model(group_model: GroupAhpModel) -> List[Tuple[bool, str]]:
        checks: List[Tuple[bool, str]] = []

        criteria = group_model.model.criteria
        alternatives = group_model.model.alternatives

        checks.append((
            len(criteria) > 0,
            "Список критериев пуст (model.criteria).",
        ))
        checks.append((
            len(alternatives) > 0,
            "Список альтернатив пуст (model.alternatives).",
        ))

        for c in criteria:
            checks.append((
                bool(c.id.strip()),
                f"Критерий без id: {asdict(c)}" if not c.id.strip() else "",
            ))
            checks.append((
                bool(c.name.strip()),
                f"Критерий {c.id} без name." if not c.name.strip() else "",
            ))

        for a in alternatives:
            checks.append((
                bool(a.id.strip()),
                f"Альтернатива без id: {asdict(a)}" if not a.id.strip() else "",
            ))
            checks.append((
                bool(a.name.strip()),
                f"Альтернатива {a.id} без name." if not a.name.strip() else "",
            ))

        return [(ok, msg) for ok, msg in checks if msg or not ok]

    def _check_pairwise_matrices(
        self,
        group_model: GroupAhpModel,
        strict: bool,
    ) -> List[Tuple[bool, str]]:
        checks: List[Tuple[bool, str]] = []

        criteria_ids = {c.id for c in group_model.model.criteria}
        alternative_ids = {a.id for a in group_model.model.alternatives}
        expert_ids = {e.id for e in group_model.experts}

        for m in group_model.pairwise_matrices.criteria_level:
            checks.extend(self._check_single_matrix(
                m,
                allowed_items=criteria_ids,
                expert_ids=expert_ids,
                expect_criterion_id=False,
                strict=strict,
                level_name="criteria_level",
            ))

        for m in group_model.pairwise_matrices.alternative_level:
            checks.extend(self._check_single_matrix(
                m,
                allowed_items=alternative_ids,
                expert_ids=expert_ids,
                expect_criterion_id=True,
                strict=strict,
                level_name="alternative_level",
            ))

        return [(ok, msg) for ok, msg in checks if msg or not ok]

    @staticmethod
    def _check_single_matrix(
        matrix_obj: PairwiseMatrix,
        allowed_items: set[str],
        expert_ids: set[str],
        expect_criterion_id: bool,
        strict: bool,
        level_name: str,
    ) -> List[Tuple[bool, str]]:
        checks: List[Tuple[bool, str]] = []

        items = matrix_obj.items
        n = len(items)
        mat = matrix_obj.matrix

        checks.append((
            n > 0,
            f"Пустой список items в матрице ({level_name}, expert_id={matrix_obj.expert_id})."
            if n == 0 else "",
        ))
        checks.append((
            len(mat) == n,
            f"Число строк матрицы не совпадает с числом items "
            f"({level_name}, expert_id={matrix_obj.expert_id})."
            if len(mat) != n else "",
        ))

        for row_idx, row in enumerate(mat):
            checks.append((
                len(row) == n,
                f"Число столбцов в строке {row_idx} матрицы не совпадает с числом items "
                f"({level_name}, expert_id={matrix_obj.expert_id})."
                if len(row) != n else "",
            ))

        checks.append((
            matrix_obj.expert_id in expert_ids,
            f"Матрица ({level_name}) с неизвестным expert_id={matrix_obj.expert_id}."
            if matrix_obj.expert_id not in expert_ids else "",
        ))

        if expect_criterion_id:
            checks.append((
                matrix_obj.criterion_id is not None,
                f"Матрица альтернатив ({level_name}, expert_id={matrix_obj.expert_id}) "
                f"не содержит criterion_id."
                if matrix_obj.criterion_id is None else "",
            ))

        for item in items:
            checks.append((
                item in allowed_items,
                f"Матрица ({level_name}, expert_id={matrix_obj.expert_id}) "
                f"содержит неизвестный элемент '{item}'."
                if item not in allowed_items else "",
            ))

        for i in range(n):
            for j in range(n):
                if i >= len(mat) or j >= len(mat[i]):
                    continue
                value = mat[i][j]

                if value <= 0.0:
                    checks.append((
                        False,
                        f"Матрица ({level_name}, expert_id={matrix_obj.expert_id}) содержит "
                        f"неположительное значение a[{i},{j}]={value}.",
                    ))
                    continue

                if strict:
                    if not (1.0 / 9.0 <= value <= 9.0):
                        checks.append((
                            False,
                            f"Матрица ({level_name}, expert_id={matrix_obj.expert_id}) содержит "
                            f"значение a[{i},{j}]={value}, выходящее за шкалу Саати [1/9, 9].",
                        ))

        return checks