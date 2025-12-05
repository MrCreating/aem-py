from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Problem:
    id: str
    name: str
    description: str
    goal: str
