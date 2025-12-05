from __future__ import annotations
from dataclasses import dataclass, field

from .run_result import AemComRunResult


@dataclass
class AlternativeLevelAemComResult:
    """
    Результат AEM-COM на уровне альтернатив для одного критерия
    """

    level: str = "alternatives"
    criterion_id: str = ""
    run: AemComRunResult = field(default_factory=AemComRunResult)