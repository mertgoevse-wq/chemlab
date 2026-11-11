"""
ChemLab No Man's Sky Sandbox Matrix & Environmental Physics Engine.
Allows granular real-time configuration of planetary gravity, atmospheric pressure,
ambient temperature, reaction time warp, and safety consequence difficulty.
Applies Clausius-Clapeyron thermodynamic scaling to solvent boiling points
and hydrostatic weir scaling to liquid pouring rates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from chemlab.compat import StrEnum


class HazardDifficulty(StrEnum):
    """Safety consequence strictness in free simulation mode."""

    CREATIVE_GODMODE = "creative_godmode"  # No glass breakage, infinite safety tolerance
    STANDARD_STUDENT = "standard_student"  # Safety officer warnings, soft restarts
    HARDCORE_REALISTIC = "hardcore_realistic"  # Glass shatters, toxic gas damage, lab quarantine


class PlanetaryPreset(StrEnum):
    """Preconfigured planetary atmospheric environments inspired by space exploration."""

    EARTH_STANDARD = "earth_standard"
    ORBITAL_ZERO_G = "orbital_zero_g"
    MARTIAN_SURFACE = "martian_surface"
    VENUSIAN_HYPERBARIC = "venusian_hyperbaric"
    TITAN_CRYOGENIC = "titan_cryogenic"


@dataclass
class LaboratoryEnvironmentMatrix:
    """
    Modular laboratory sandbox environment matrix.
    Affects fluid kinematics, boiling points, and reaction speeds in real time.
    """

    gravity_g: float = 1.0  # 0.0g to 3.0g (Earth = 1.0)
    ambient_pressure_atm: float = 1.0  # 0.001 atm (vacuum) to 50.0 atm
    ambient_temperature_c: float = 22.0  # -200 °C to +500 °C
    time_warp: float = 1.0  # 0.0x (pause) to 100.0x
    hazard_difficulty: HazardDifficulty = HazardDifficulty.STANDARD_STUDENT

    @property
    def boiling_point_water_c(self) -> float:
        """
        Calculates boiling point of pure water under the active ambient pressure
        using the Clausius-Clapeyron equation:
        1/T = 1/T0 - (R / DeltaH_vap) * ln(P / P0)
        """
        t0_kelvin = 373.15  # 100 °C
        r_gas = 8.314  # J/(mol*K)
        delta_h_vap = 40660.0  # J/mol for water at boiling point
        p_ratio = max(1e-4, self.ambient_pressure_atm / 1.0)

        inv_t = (1.0 / t0_kelvin) - (r_gas / delta_h_vap) * math.log(p_ratio)
        t_boiling_k = 1.0 / max(1e-6, inv_t)
        return round(t_boiling_k - 273.15, 2)

    @property
    def pour_velocity_multiplier(self) -> float:
        """
        Hydrostatic efflux velocity scale (Torricelli / Weir equation):
        v ~ sqrt(2 * g * h). At 0.0g, fluids do not pour downward.
        """
        if self.gravity_g <= 0.0:
            return 0.0
        return round(math.sqrt(self.gravity_g), 4)

    @property
    def allow_glass_shattering(self) -> bool:
        return self.hazard_difficulty == HazardDifficulty.HARDCORE_REALISTIC

    @property
    def allow_lethal_toxic_spills(self) -> bool:
        return self.hazard_difficulty == HazardDifficulty.HARDCORE_REALISTIC

    @classmethod
    def from_preset(cls, preset: PlanetaryPreset) -> LaboratoryEnvironmentMatrix:
        """Constructs an authentic environmental matrix from planetary conditions."""
        if preset == PlanetaryPreset.ORBITAL_ZERO_G:
            return cls(
                gravity_g=0.0,
                ambient_pressure_atm=1.0,  # Pressurized station interior
                ambient_temperature_c=21.0,
                time_warp=1.0,
            )
        if preset == PlanetaryPreset.MARTIAN_SURFACE:
            return cls(
                gravity_g=0.38,
                ambient_pressure_atm=0.006,  # 6 mbar CO2 atmosphere
                ambient_temperature_c=-63.0,
                time_warp=1.0,
            )
        if preset == PlanetaryPreset.VENUSIAN_HYPERBARIC:
            return cls(
                gravity_g=0.91,
                ambient_pressure_atm=92.0,  # 92 bar supercritical CO2/N2
                ambient_temperature_c=464.0,
                time_warp=1.0,
            )
        if preset == PlanetaryPreset.TITAN_CRYOGENIC:
            return cls(
                gravity_g=0.14,
                ambient_pressure_atm=1.45,
                ambient_temperature_c=-179.0,  # Liquid methane seas
                time_warp=1.0,
            )
        # Default Earth Standard
        return cls()
