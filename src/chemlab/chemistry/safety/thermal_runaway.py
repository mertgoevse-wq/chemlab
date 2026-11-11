"""
Thermal Runaway — Semenov Explosion Criterion
==============================================

Models adiabatic thermal explosion, Antoine vapor pressure buildup,
and projectile kinematics (stopper pop).

Migrated from safety_simulation/thermal_runaway.py (no functional changes).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SemenovModel:
    """Semenov thermal explosion criterion parameters."""

    heat_generation_coeff: float  # W/K
    heat_removal_coeff: float  # W/K
    ambient_temp_k: float = 298.15


def calculate_adiabatic_runaway(model: SemenovModel, initial_temp_k: float) -> float:
    """Calculate critical temperature for thermal runaway."""
    raise NotImplementedError("Phase 4 implementation pending")


def calculate_vapor_pressure_antoine(
    antoine_a: float, antoine_b: float, antoine_c: float, temp_c: float
) -> float:
    """Antoine equation: log10(P_mmHg) = A - B/(T+C). Returns kPa."""
    raise NotImplementedError("Phase 4 implementation pending")


def calculate_stopper_pop_velocity(
    pressure_kpa: float, volume_l: float, stopper_mass_kg: float
) -> float:
    """Stopper launch velocity v = sqrt(2 * ΔP * V / m)."""
    raise NotImplementedError("Phase 4 implementation pending")


__all__ = [
    "SemenovModel",
    "calculate_adiabatic_runaway",
    "calculate_vapor_pressure_antoine",
    "calculate_stopper_pop_velocity",
]
