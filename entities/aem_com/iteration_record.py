from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass
class AemComIterationRecord:
    iteration: int
    pair_indices: Tuple[int, int]
    pair_items: Tuple[str, str]
    t_rs: float
    old_value: float
    new_value: float
    gcompi_value: float
