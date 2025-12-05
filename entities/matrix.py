from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PairwiseMatrix:
    items: List[str]
    matrix: List[List[float]]
    expert_id: Optional[str] = None
    criterion_id: Optional[str] = None

    def __post_init__(self) -> None:
        n = len(self.items)
        if len(self.matrix) != n:
            raise ValueError(
                f"Matrix must have {n} rows, got {len(self.matrix)}"
            )
        for row in self.matrix:
            if len(row) != n:
                raise ValueError(
                    "Matrix must be square and match length of items list"
                )