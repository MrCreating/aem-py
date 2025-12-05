from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .iteration_record import AemComIterationRecord


@dataclass
class AemComRunResult:
    """
    Результат работы AEM-COM для одного уровня МПС

    items: порядок альтернатив/критериев, соответствующий матрицам
    initial_matrix: начальная коллективная P (до AEM-COM)
    final_matrix: итоговая коллективная P' (после AEM-COM)
    initial_priorities: v0 — вектор приоритетов для initial_matrix
    final_priorities: v' — вектор приоритетов для final_matrix
    group_priorities: w_G — групповой вектор
    gcompi_initial: GCOMPI(A, v0)
    gcompi_final: GCOMPI(A, v')
    gcompi_min: GCOMPI(A, w_G) — теоретический минимум в этом контексте
    iterations: фактическое количество итераций
    history: список записей по итерациям
    """

    items: List[str] = field(default_factory=list)

    initial_matrix: List[List[float]] = field(default_factory=list)
    final_matrix: List[List[float]] = field(default_factory=list)

    initial_priorities: List[float] = field(default_factory=list)
    final_priorities: List[float] = field(default_factory=list)
    group_priorities: List[float] = field(default_factory=list)

    gcompi_initial: float = 0.0
    gcompi_final: float = 0.0
    gcompi_min: float = 0.0

    iterations: int = 0
    history: List[AemComIterationRecord] = field(default_factory=list)