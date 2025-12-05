from __future__ import annotations

from typing import Any, Dict, List

from entities import (
    PairwiseMatrix,
    PairwiseMatrices,
    Settings,
    AemComSettings,
    Model,
    Criterion,
    Alternative,
    Expert,
    Problem,
    GroupAhpModel
)


class GroupBuilder:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def build(self) -> GroupAhpModel:
        problem = self._build_problem(self._data.get("problem", {}))
        experts = self._build_experts(self._data.get("experts", []))
        ahp_model = self._build_ahp_model(self._data.get("model", {}))
        settings = self._build_settings(self._data.get("settings", {}))
        pairwise_matrices = self._build_pairwise_matrices(
            self._data.get("pairwise_matrices", {})
        )

        return GroupAhpModel(
            problem=problem,
            experts=experts,
            model=ahp_model,
            settings=settings,
            pairwise_matrices=pairwise_matrices,
        )

    @staticmethod
    def _build_problem(problem_data: Dict[str, Any]) -> Problem:
        return Problem(
            id=problem_data.get("id", ""),
            name=problem_data.get("name", ""),
            description=problem_data.get("description", ""),
            goal=problem_data.get("goal", ""),
        )

    @staticmethod
    def _build_experts(experts_data: List[Dict[str, Any]]) -> List[Expert]:
        experts: List[Expert] = []
        for e in experts_data:
            expert = Expert(
                id=e.get("id", ""),
                name=e.get("name", ""),
                role=e.get("role", ""),
                weight=float(e.get("weight", 0.0)),
            )
            experts.append(expert)
        return experts

    @staticmethod
    def _build_ahp_model(model_data: Dict[str, Any]) -> Model:
        criteria_data = model_data.get("criteria", [])
        alternatives_data = model_data.get("alternatives", [])

        criteria: List[Criterion] = []
        for c in criteria_data:
            crit = Criterion(
                id=c.get("id", ""),
                name=c.get("name", ""),
                description=c.get("description", ""),
            )
            criteria.append(crit)

        alternatives: List[Alternative] = []
        for a in alternatives_data:
            alt = Alternative(
                id=a.get("id", ""),
                name=a.get("name", ""),
                description=a.get("description", ""),
            )
            alternatives.append(alt)

        return Model(criteria=criteria, alternatives=alternatives)

    @staticmethod
    def _build_settings(settings_data: Dict[str, Any]) -> Settings:
        ahp_scale = settings_data.get("ahp_scale", "saaty_1_9")
        aem_com_data = settings_data.get("aem_com", {})

        aem_com = AemComSettings(
            permissibility=float(aem_com_data.get("permissibility", 0.0)),
            apply_to=list(aem_com_data.get("apply_to", [])),
            max_iterations=int(aem_com_data.get("max_iterations", 0)),
        )

        return Settings(
            ahp_scale=ahp_scale,
            aem_com=aem_com,
        )

    def _build_pairwise_matrices(
            self, matrices_data: Dict[str, Any]
    ) -> PairwiseMatrices:
        criteria_level_data = matrices_data.get("criteria_level", [])
        alternative_level_data = matrices_data.get("alternative_level", [])

        criteria_level: List[PairwiseMatrix] = []
        for m in criteria_level_data:
            matrix = self._build_pairwise_matrix(
                items=m.get("items", []),
                matrix=m.get("matrix", []),
                expert_id=m.get("expert_id"),
                criterion_id=m.get("criterion_id"),
            )
            criteria_level.append(matrix)

        alternative_level: List[PairwiseMatrix] = []
        for m in alternative_level_data:
            matrix = self._build_pairwise_matrix(
                items=m.get("items", []),
                matrix=m.get("matrix", []),
                expert_id=m.get("expert_id"),
                criterion_id=m.get("criterion_id"),
            )
            alternative_level.append(matrix)

        return PairwiseMatrices(
            criteria_level=criteria_level,
            alternative_level=alternative_level,
        )

    @staticmethod
    def _build_pairwise_matrix(
            items: List[str],
            matrix: List[List[float]],
            expert_id: str | None,
            criterion_id: str | None,
    ) -> PairwiseMatrix:
        numeric_matrix: List[List[float]] = []
        for row in matrix:
            numeric_row: List[float] = []
            for value in row:
                numeric_row.append(float(value))
            numeric_matrix.append(numeric_row)

        return PairwiseMatrix(
            items=list(items),
            matrix=numeric_matrix,
            expert_id=expert_id,
            criterion_id=criterion_id,
        )