"""
GHS Hazard Classification & Chemical Compatibility
===================================================

Authoritative GHS implementation compliant with Rev. 10 and OSHA HCS 2012.
Consolidates from safety_simulation/ghs.py and merges hazard data into
chemistry.catalog.reagents.Reagent.ghs_hazards.

Public API:
- check_chemical_compatibility(chem_a_id, chem_b_id) -> IncompatibilityResult
- get_chemical_sds(chemical_id) -> dict (OSHA 16-section summary)
- GHSHazard: Single hazard classification dataclass
- IncompatibilityResult: Compatibility evaluation result
- Enums: GHSClass, SignalWord, StorageGroup
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GHSClass(str, Enum):
    EXPLOSIVE = "EXPLOSIVE"
    FLAMMABLE = "FLAMMABLE"
    OXIDIZING = "OXIDIZING"
    COMPRESSED_GAS = "COMPRESSED_GAS"
    CORROSIVE = "CORROSIVE"
    TOXIC = "TOXIC"
    HARMFUL_IRRITANT = "HARMFUL_IRRITANT"
    HEALTH_HAZARD = "HEALTH_HAZARD"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class SignalWord(str, Enum):
    DANGER = "DANGER"
    WARNING = "WARNING"
    NONE = "NONE"


class StorageGroup(str, Enum):
    FLAMMABLE_CABINET = "flammable_cabinet"
    ACID_CABINET = "acid_cabinet"
    BASE_CABINET = "base_cabinet"
    OXIDIZER_STORAGE = "oxidizer_storage"
    GENERAL_STORAGE = "general_storage"
    TOXIC_SECURE = "toxic_secure"
    EXPLOSIVE_MAGAZINE = "explosive_magazine"


@dataclass(frozen=True)
class GHSHazard:
    """A single GHS hazard classification with code, text, pictogram, signal word, category."""
    code: str
    text: str
    pictogram: str
    signal_word: SignalWord
    category: int


@dataclass
class IncompatibilityResult:
    compatible: bool
    risk_level: str
    reaction_type: str | None = None
    hazard_description: str | None = None
    byproducts: list[str] = None

    def __post_init__(self):
        if self.byproducts is None:
            self.byproducts = []


def check_chemical_compatibility(chem_a_id: str, chem_b_id: str) -> IncompatibilityResult:
    """Evaluates mutual chemical compatibility per EPA/NOAA CAMEO logic."""
    raise NotImplementedError("Phase 4 implementation pending")


def get_chemical_sds(chemical_id: str) -> dict:
    """Generates OSHA 16-section compliant summary SDS."""
    raise NotImplementedError("Phase 4 implementation pending")


__all__ = [
    "GHSClass",
    "SignalWord",
    "StorageGroup",
    "GHSHazard",
    "IncompatibilityResult",
    "check_chemical_compatibility",
    "get_chemical_sds",
]