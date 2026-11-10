"""
Kinetics Solver — Authoritative Reaction Simulation
====================================================

Core simulation primitives for liquid mixing, reaction stepping,
oscillating reactions (Briggs-Rauscher), and consequence evaluation.

Consolidates from:
- src/chemlab/simulation/reaction_solver.py (mix_liquids, step_simulation, LiquidMixture)
- chemlab_core/chemistry/reaction_engine.py (BriggsRauscherOscillator)
- simulation/consequence.py (ConsequenceEngine, ConsequenceResult, enums)
- simulation/free_sim_engine.py (FreeSimulationEngine facade)

Public API:
- LiquidMixture: Mutable fluid state (volume, temp, moles, color, turbidity, bubbles, foam, oscillation)
- ReactionType: Enum of identified reaction events
- mix_liquids(): Blend two mixtures conserving volume, heat, color
- step_simulation(): Advance simulation by dt, returns (new_mixture, reaction_type)
- BriggsRauscherOscillator: Analytical 3-phase color cycle
- ConsequenceEngine: Evaluate arbitrary reagent combos in lab environments
- ConsequenceResult: Outcome with temp delta, effects, precipitate, gas, safety report
- FreeSimulationEngine: High-level facade for free-form experimentation
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReactionType(Enum):
    """Identified chemical reaction events for VFX and gameplay feedback."""

    NONE = "none"
    ACID_BASE_NEUTRALIZATION = "acid_base_neutralization"
    CATALYTIC_FOAM_ERUPTION = "catalytic_foam_eruption"
    OSCILLATING_COLOR_WAVE = "oscillating_color_wave"
    PRECIPITATION_FALL = "precipitation_fall"
    CHEMILUMINESCENT_GLOW = "chemiluminescent_glow"
    THERMAL_RUNAWAY = "thermal_runaway"


@dataclass
class LiquidMixture:
    """Represents the fluid content inside a vessel."""

    volume_ml: float
    temperature_c: float
    reagent_moles: dict[str, float]
    color_rgb: tuple[float, float, float] = (0.95, 0.98, 1.0)
    turbidity: float = 0.0
    bubble_rate: float = 0.0
    foam_volume_ml: float = 0.0
    oscillation_phase: int = 0
    oscillation_timer_s: float = 0.0
    emission_glow: float = 0.0

    def clone(self) -> LiquidMixture:
        return LiquidMixture(
            volume_ml=self.volume_ml,
            temperature_c=self.temperature_c,
            reagent_moles=dict(self.reagent_moles),
            color_rgb=self.color_rgb,
            turbidity=self.turbidity,
            bubble_rate=self.bubble_rate,
            foam_volume_ml=self.foam_volume_ml,
            oscillation_phase=self.oscillation_phase,
            oscillation_timer_s=self.oscillation_timer_s,
            emission_glow=self.emission_glow,
        )


# Rate constants (moved from reaction_solver.py)
MIXING_KW: float = 0.6
NEUTRALIZATION_KW: float = 1.2
OSCILLATOR_KW: float = 0.08
CATALYST_MULTIPLIER: dict[str, float] = {
    "potassium_iodide": 5.0,
    "manganese_sulfate": 4.0,
    "manganese_dioxide": 3.5,
}


def mix_liquids(a: LiquidMixture, b: LiquidMixture) -> LiquidMixture:
    """Blend two liquid mixtures conserving volume, color, thermal equilibrium."""
    raise NotImplementedError("Phase 3 implementation pending")


def step_simulation(mixture: LiquidMixture, dt_s: float) -> tuple[LiquidMixture, ReactionType]:
    """Advance simulation by dt seconds."""
    raise NotImplementedError("Phase 3 implementation pending")


# Briggs-Rauscher oscillator (from reaction_engine.py)
COLOR_CLEAR = (0.92, 0.96, 0.98, 0.45)
COLOR_AMBER = (0.85, 0.45, 0.05, 0.85)
COLOR_DEEP_BLUE = (0.05, 0.08, 0.45, 0.95)


class OscillatingPhase(Enum):
    CLEAR_INDUCTION = "CLEAR_INDUCTION"
    AMBER_TRIIODIDE = "AMBER_TRIIODIDE"
    DEEP_BLUE_COMPLEX = "DEEP_BLUE_COMPLEX"


@dataclass
class ReactionState:
    cycle_index: int
    phase: OscillatingPhase
    phase_progress: float
    color_rgba: tuple[float, float, float, float]
    temperature_celsius: float = 22.5
    period_seconds: float = 6.0


class BriggsRauscherOscillator:
    """Simulates chemical oscillations of the Briggs-Rauscher reaction."""

    def __init__(self, period_seconds: float = 6.0) -> None:
        if period_seconds <= 0.0:
            raise ValueError("Oscillation period must be strictly positive")
        self._period = period_seconds
        self._elapsed_time = 0.0
        self._cycle_index = 0

    def reset(self) -> None:
        self._elapsed_time = 0.0
        self._cycle_index = 0

    def step(self, delta_time: float) -> ReactionState:
        raise NotImplementedError("Phase 3 implementation pending")


# Consequence engine types (from consequence.py)
class VesselEnvironment(Enum):
    MAIN_BENCH = "main_bench"
    FUME_HOOD = "fume_hood"
    GLOVE_BOX = "glove_box"
    HEATING_MANTLE = "heating_mantle"
    ICE_BATH = "ice_bath"


class ConsequenceType(Enum):
    NO_VISIBLE_REACTION = "no_visible_reaction"
    EXOTHERMIC_NEUTRALIZATION = "exothermic_neutralization"
    ENDOTHERMIC_DISSOLUTION = "endothermic_dissolution"
    PRECIPITATION = "precipitation"
    GAS_EVOLUTION = "gas_evolution"
    EXPLOSION = "explosion"
    OSCILLATING_REACTION = "oscillating_reaction"
    REDOX_COLOR_SHIFT = "redox_color_shift"
    THERMAL_DECOMPOSITION = "thermal_decomposition"


class ReactionEffect(Enum):
    HEAT_RELEASE = "heat_release"
    COOLING = "cooling"
    PRECIPITATE = "precipitate"
    EFFERVESCENCE = "effervescence"
    FLAME = "flame"
    VAPOR_CLOUD = "vapor_cloud"
    COLOR_CHANGE = "color_change"
    ODOR_RELEASE = "odor_release"
    SHOCKWAVE = "shockwave"


@dataclass
class OscillationCycle:
    period_seconds: float
    color_sequence: list[tuple[float, float, float, float]]
    phase_names: list[str]


@dataclass
class ConsequenceResult:
    consequence: ConsequenceType
    initial_temp_c: float
    final_temp_c: float
    temp_delta_c: float
    effects: list[ReactionEffect] = None
    precipitate_name: str | None = None
    precipitate_color: tuple[float, float, float, float] | None = None
    precipitate_mass_g: float = 0.0
    gas_released_formula: str | None = None
    gas_volume_liters: float = 0.0
    is_contained: bool = True
    safety_report: str = "Conditions nominal."
    oscillation_cycle: OscillationCycle | None = None
    mixture_color_rgba: tuple[float, float, float, float] = (0.95, 0.98, 1.0, 1.0)
    details: str = ""


class ConsequenceEngine:
    """Evaluates arbitrary reagent mixtures in specific laboratory environments."""

    def mix(
        self,
        vessel_env: VesselEnvironment,
        reagent_ids: list[str],
        volumes_ml: list[float] | None = None,
        masses_or_volumes: list[float] | None = None,
        initial_temp_c: float = 20.0,
    ) -> ConsequenceResult:
        raise NotImplementedError("Phase 3 implementation pending")


# Free simulation facade (from free_sim_engine.py)
@dataclass
class ActiveExperimentState:
    id: str
    environment: VesselEnvironment
    apparatus: list[str]
    reagent_ids: list[str]
    quantities: list[float]
    consequence_result: ConsequenceResult | None = None
    current_temperature_c: float = 20.0
    liquid_color_rgba: tuple[float, float, float, float] = (0.95, 0.98, 1.0, 0.92)
    turbidity: float = 0.0
    bubble_rate: float = 0.0
    fume_density: float = 0.0


class FreeSimulationEngine:
    """Central engine orchestrating free-form experimentation."""

    def __init__(self):
        raise NotImplementedError("Phase 3 implementation pending")

    def run_experiment(
        self,
        vessel_env: VesselEnvironment,
        reagent_ids: list[str],
        quantities: list[float] | None = None,
        apparatus: list[str] | None = None,
        initial_temp_c: float = 20.0,
    ) -> ConsequenceResult:
        raise NotImplementedError("Phase 3 implementation pending")

    def capture_snapshot(
        self,
        title: str,
        camera_angle: dict[str, float] | None = None,
        resolution: tuple[int, int] = (1920, 1080),
    ):
        raise NotImplementedError("Phase 3 implementation pending")

    def export_current_setup_as_recipe(
        self,
        title: str,
        filepath: str,
        author: str = "Lead Chemist",
        description: str = "Free simulation experimental setup",
    ):
        raise NotImplementedError("Phase 3 implementation pending")


__all__ = [
    # Core types
    "LiquidMixture",
    "ReactionType",
    # Core functions
    "mix_liquids",
    "step_simulation",
    # Rate constants
    "MIXING_KW",
    "NEUTRALIZATION_KW",
    "OSCILLATOR_KW",
    "CATALYST_MULTIPLIER",
    # Briggs-Rauscher
    "COLOR_CLEAR",
    "COLOR_AMBER",
    "COLOR_DEEP_BLUE",
    "OscillatingPhase",
    "ReactionState",
    "BriggsRauscherOscillator",
    # Consequence engine
    "VesselEnvironment",
    "ConsequenceType",
    "ReactionEffect",
    "OscillationCycle",
    "ConsequenceResult",
    "ConsequenceEngine",
    # Free simulation facade
    "ActiveExperimentState",
    "FreeSimulationEngine",
]