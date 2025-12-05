from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class AemComSettings:
    permissibility: float = 0.15
    apply_to: List[str] = field(default_factory=lambda: ["criteria", "alternatives_by_criterion"])
    max_iterations: int = 100
    initial_mode: str = "aij"
