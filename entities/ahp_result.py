from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AhpResult:
    """
    criteria_weights - веса критериев (глобальные, после агрегации)
    criteria_consistency_os - OS (CR) матрицы критериев
    criteria_consistency_percent - тот же OS, переведённый в %
    alt_weights_by_criterion - локальные веса альтернатив по каждому критерию
    alt_consistency_os_by_criterion - OS для матриц альтернатив по критериям
    alt_consistency_percent_by_criterion - OS в процентах
    global_alt_weights - итоговые веса альтернатив (по всем критериям)
    """
    criteria_weights: Dict[str, float] = field(default_factory=dict)
    criteria_consistency_os: float = 0.0
    criteria_consistency_percent: float = 0.0

    alt_weights_by_criterion: Dict[str, Dict[str, float]] = field(default_factory=dict)
    alt_consistency_os_by_criterion: Dict[str, float] = field(default_factory=dict)
    alt_consistency_percent_by_criterion: Dict[str, float] = field(default_factory=dict)

    global_alt_weights: Dict[str, float] = field(default_factory=dict)
