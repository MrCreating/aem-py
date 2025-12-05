from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from entities.matrix import PairwiseMatrix


@dataclass
class PairwiseMatrices:
    criteria_level: List[PairwiseMatrix] = field(default_factory=list)
    alternative_level: List[PairwiseMatrix] = field(default_factory=list)