from __future__ import annotations
from dataclasses import dataclass, field

from .run_result import AemComRunResult


@dataclass
class CriteriaLevelAemComResult:
    """
    Результат AEM-COM на уровне критериев.
    """

    level: str = "criteria"
    run: AemComRunResult = field(default_factory=AemComRunResult)