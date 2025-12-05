from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Alternative:
    id: str
    name: str
    description: str