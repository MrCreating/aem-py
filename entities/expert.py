from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Expert:
    id: str
    name: str
    role: str
    weight: float
