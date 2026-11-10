"""
Side Reaction Analysis — Non-Ideal Impurity Modeling
=====================================================

Models realistic side products and hazards from suboptimal synthesis conditions:
- Addition order hazards (water into conc. H2SO4)
- Temperature-dependent defects (aspirin, paracetamol, acetanilide)
- Catalyst absence/presence effects
- Oligomerization, oxidation, tar formation

Consolidated from src/chemlab/simulation/side_reactions.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SideReactionType(Enum):
    ADDITION_ORDER_HAZARD = "addition_order_hazard"
    UNDER_TEMPERATURE = "under_temperature"
    OVER_TEMPERATURE = "over_temperature"
    MISSING_CATALYST = "missing_catalyst"
    OVER_ACETYLATION = "over_acetylation"
    AIR_OXIDATION = "air_oxidation"
    OLIGOMERIZATION = "oligomerization"
    MELTING_POINT_DEPRESSION = "melting_point_depression"


@dataclass
class SideReactionResult:
    reaction_type: SideReactionType
    description: str
    side_products: list[str]
    yield_penalty_percent: float
    safety_warning: str | None = None


class SideReactionAnalyzer:
    """Analyzes synthesis conditions for non-ideal side reactions."""

    def detect_addition_order_hazard(
        self,
        reagent_a: str,
        reagent_b: str,
        order: str,  # "a_into_b" or "b_into_a"
    ) -> SideReactionResult | None:
        raise NotImplementedError("Phase 3 implementation pending")

    def analyze_aspirin_synthesis(
        self,
        temperature_c: float,
        has_catalyst: bool,
        addition_order_correct: bool,
    ) -> list[SideReactionResult]:
        raise NotImplementedError("Phase 3 implementation pending")

    def analyze_paracetamol_synthesis(
        self,
        temperature_c: float,
        has_catalyst: bool,
        reaction_time_min: float,
    ) -> list[SideReactionResult]:
        raise NotImplementedError("Phase 3 implementation pending")

    def analyze_acetanilide_synthesis(
        self,
        temperature_c: float,
        crystallization_temp_c: float,
    ) -> list[SideReactionResult]:
        raise NotImplementedError("Phase 3 implementation pending")


__all__ = [
    "SideReactionType",
    "SideReactionResult",
    "SideReactionAnalyzer",
]