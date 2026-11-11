"""
ChemLab Core Data Models
Strictly typed dataclasses and enums for chemical states, computer vision tracking, and interaction events.
"""

from __future__ import annotations

from dataclasses import dataclass

from chemlab.compat import StrEnum


class GHSHazard(StrEnum):
    """Globally Harmonized System (GHS) chemical hazard pictograms."""

    FLAMMABLE = "GHS02_Flammable"
    OXIDIZING = "GHS03_Oxidizing"
    CORROSIVE = "GHS05_Corrosive"
    TOXIC = "GHS06_Acute_Toxicity"
    HEALTH_HAZARD = "GHS08_Health_Hazard"
    ENVIRONMENTAL = "GHS09_Aquatic_Toxicity"


class ReactionType(StrEnum):
    """Identified chemical reaction events for VFX and gameplay feedback."""

    NONE = "none"
    ACID_BASE_NEUTRALIZATION = "acid_base_neutralization"
    CATALYTIC_FOAM_ERUPTION = "catalytic_foam_eruption"
    OSCILLATING_COLOR_WAVE = "oscillating_color_wave"
    PRECIPITATION_FALL = "precipitation_fall"
    CHEMILUMINESCENT_GLOW = "chemiluminescent_glow"
    THERMAL_RUNAWAY = "thermal_runaway"


@dataclass(frozen=True)
class ChemicalReagent:
    """Represents a pure chemical substance or stock solution."""

    id: str
    name: str
    formula: str
    molar_mass: float  # g/mol
    density_g_ml: float = 1.0
    ph: float = 7.0
    color_rgb: tuple[float, float, float] = (0.95, 0.98, 1.0)
    ghs_hazards: tuple[GHSHazard, ...] = ()
    is_catalyst: bool = False
    description: str = ""


@dataclass
class LiquidMixture:
    """Represents the fluid content inside a beaker, flask, or test tube."""

    volume_ml: float
    temperature_c: float
    reagent_moles: dict[str, float]
    color_rgb: tuple[float, float, float] = (0.95, 0.98, 1.0)
    turbidity: float = 0.0  # 0.0 = crystal clear, 1.0 = completely opaque precipitate
    bubble_rate: float = 0.0  # 0.0 = still, 1.0 = vigorous boiling / foam
    foam_volume_ml: float = 0.0
    oscillation_phase: int = 0  # 0: Clear, 1: Amber, 2: Deep Blue
    oscillation_timer_s: float = 0.0
    emission_glow: float = 0.0  # 0.0 = normal, >0.0 = chemiluminescent glow intensity

    @property
    def ph(self) -> float:
        """Calculates effective solution pH based on molar concentrations."""
        import math

        vol_l = max(1e-6, self.volume_ml / 1000.0)
        hcl_moles = self.reagent_moles.get("hcl", 0.0)
        naoh_moles = self.reagent_moles.get("naoh", 0.0)
        net_acid = hcl_moles - naoh_moles
        if net_acid > 1e-7:
            conc_h = net_acid / vol_l
            return max(0.0, min(7.0, -math.log10(max(1e-14, conc_h))))
        if net_acid < -1e-7:
            conc_oh = abs(net_acid) / vol_l
            poh = -math.log10(max(1e-14, conc_oh))
            return max(7.0, min(14.0, 14.0 - poh))
        return 7.0

    def clone(self) -> LiquidMixture:
        """Deep copy helper for immutable simulation stepping."""
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


@dataclass(frozen=True)
class HandLandmark:
    """Single 3D anatomical landmark coordinate from computer vision."""

    x: float  # Normalized 0..1 or metric X
    y: float  # Normalized 0..1 or metric Y
    z: float  # Relative depth Z
    visibility: float = 1.0


@dataclass
class HandTrackingFrame:
    """Processed tracking frame for one hand with gesture states."""

    hand_id: str  # 'Left' or 'Right'
    timestamp_ns: int
    confidence: float
    landmarks: list[HandLandmark]
    is_pinching: bool = False
    pinch_distance_mm: float = 100.0
    tilt_angle_deg: float = 0.0
    swirl_speed_rad_s: float = 0.0
    wrist_world_pos: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class ApparatusState:
    """Current dynamic state of a 3D laboratory object."""

    id: str
    name: str
    position: tuple[float, float, float]
    rotation_euler: tuple[float, float, float]
    is_held: bool = False
    held_by_hand: str | None = None
    liquid: LiquidMixture | None = None
    is_pouring: bool = False
    pour_flow_rate_ml_s: float = 0.0
    temperature_sensor_c: float = 20.0
