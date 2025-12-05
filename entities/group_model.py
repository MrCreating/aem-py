from __future__ import annotations
from dataclasses import dataclass
from typing import List

from entities.problem import Problem
from entities.expert import Expert
from entities.model import Model
from entities.settings import Settings
from entities.matrices import PairwiseMatrices


@dataclass
class GroupAhpModel:
    problem: Problem
    experts: List[Expert]
    model: Model
    settings: Settings
    pairwise_matrices: PairwiseMatrices
