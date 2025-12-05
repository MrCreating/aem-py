from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from .criteria_result import CriteriaLevelAemComResult
from .alternative_result import AlternativeLevelAemComResult


@dataclass
class AemComGlobalResult:
    """
    Общий результат AEM-COM по всей модели:

      - результат по критериям (опционально),
      - результаты по альтернативам для каждого критерия,
      - агрегированные цифры (количество итераций и т.п.)
    """

    criteria_result: Optional[CriteriaLevelAemComResult] = None
    alternatives_results: Dict[str, AlternativeLevelAemComResult] = field(default_factory=dict)

    total_iterations: int = 0
    levels_count: int = 0