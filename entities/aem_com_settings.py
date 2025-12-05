from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class AemComSettings:
    permissibility: float
    apply_to: List[str]
    max_iterations: int