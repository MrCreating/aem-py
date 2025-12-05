from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Criterion:
    id: str
    name: str
    description: str