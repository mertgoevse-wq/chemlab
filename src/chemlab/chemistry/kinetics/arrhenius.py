"""
Arrhenius Kinetics Utilities
============================

Mathematical helpers for temperature-dependent rate constants.

- k(T) = A * exp(-E_a / (R * T))
- Half-life for first-order: t_1/2 = ln(2) / k
- Temperature acceleration factor: k(T2)/k(T1)
"""

from __future__ import annotations

import math

from chemlab.chemistry.thermodynamics.engine import R_GAS


def arrhenius_rate_constant(
    pre_exponential_a: float,
    activation_energy_kj_mol: float,
    temperature_k: float,
) -> float:
    """Calculate Arrhenius rate constant k(T)."""
    ea_j = activation_energy_kj_mol * 1000.0
    exponent = -ea_j / (R_GAS * temperature_k)
    clamped = max(-700.0, min(700.0, exponent))
    return pre_exponential_a * math.exp(clamped)


def half_life_first_order(rate_constant_k: float) -> float | None:
    """First-order half-life t_1/2 = ln(2) / k."""
    if rate_constant_k <= 1e-12:
        return None
    return math.log(2) / rate_constant_k


def temperature_acceleration_factor(
    activation_energy_kj_mol: float,
    t1_k: float,
    t2_k: float,
) -> float:
    """Ratio k(T2)/k(T1) for same reaction."""
    ea_j = activation_energy_kj_mol * 1000.0
    return math.exp(ea_j / R_GAS * (1.0 / t1_k - 1.0 / t2_k))


__all__ = [
    "arrhenius_rate_constant",
    "half_life_first_order",
    "temperature_acceleration_factor",
]
