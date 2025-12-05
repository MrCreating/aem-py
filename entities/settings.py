from __future__ import annotations
from dataclasses import dataclass

from entities.aem_com_settings import AemComSettings


@dataclass
class Settings:
    ahp_scale: str
    aem_com: AemComSettings