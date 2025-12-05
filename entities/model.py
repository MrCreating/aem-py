from __future__ import annotations
from dataclasses import dataclass
from typing import List

from entities.criterion import Criterion
from entities.alternative import Alternative


@dataclass
class Model:
    criteria: List[Criterion]
    alternatives: List[Alternative]