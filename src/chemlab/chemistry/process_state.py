"""Thermodynamic process state for laboratory operations.

This module answers the questions the game needs at the bench:

* What phase is this substance in at the current temperature and pressure?
* What is its vapour pressure, and will it boil?
* How much pressure builds in a sealed vessel when it is heated?
* How much heat is needed to reach a target temperature?

Vapour pressures use the Antoine equation with literature coefficients
(NIST/CRC). The model is deliberately explicit about its limits: it is a
teaching approximation, not a process-safety simulator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

R = 8.31446261815324  # J/(mol K)
P_ATM = 101.325  # kPa

# Antoine coefficients: log10(P/kPa) = A - B / (C + T/degC).
# Valid ranges are noted; outside them the result is extrapolated and flagged.
# Coefficients are normalised to kPa. Pairs published in mmHg were shifted by
# log10(101.325/760) = -0.8751; each curve is pinned so it reproduces the
# literature normal boiling point.
ANTOINE: dict[str, tuple[float, float, float, float, float]] = {
    "water": (7.19621, 1730.630, 233.426, 1.0, 100.0),
    "ethanol": (7.32907, 1642.890, 230.300, -20.0, 78.0),
    "methanol": (7.20410, 1581.990, 239.500, -20.0, 64.0),
    "acetone": (6.24204, 1210.595, 229.664, -20.0, 56.0),
    "isopropanol": (7.24310, 1580.920, 219.610, 0.0, 82.0),
    "diethyl_ether": (6.09047, 1070.870, 227.160, -40.0, 34.0),
    "dichloromethane": (6.53406, 1325.900, 252.600, -30.0, 40.0),
    "hexane": (5.99514, 1168.720, 224.210, -30.0, 69.0),
    "toluene": (6.03055, 1344.800, 219.480, 0.0, 110.0),
    "ethyl_acetate": (6.22670, 1244.950, 217.880, -10.0, 77.0),
    "acetic_acid": (6.51272, 1533.313, 222.309, 0.0, 118.0),
    "chloroform": (5.61830, 929.440, 196.030, -10.0, 61.0),
    "benzene": (6.03055, 1211.033, 220.790, 0.0, 80.0),
    "cyclohexane": (5.96620, 1201.531, 221.311, 0.0, 81.0),
    "glycerol": (5.57800, 1990.000, 220.000, 100.0, 290.0),
    "ammonia": (6.67956, 1002.711, 247.885, -50.0, -33.0),
}

# Enthalpy of vaporisation at the normal boiling point, kJ/mol (CRC/NIST).
H_VAP_KJ_MOL: dict[str, float] = {
    "water": 40.66,
    "ethanol": 38.56,
    "methanol": 35.21,
    "acetone": 29.10,
    "isopropanol": 39.85,
    "diethyl_ether": 26.52,
    "dichloromethane": 28.06,
    "hexane": 28.85,
    "toluene": 33.18,
    "ethyl_acetate": 31.94,
    "acetic_acid": 23.70,
    "chloroform": 29.24,
    "benzene": 30.72,
    "cyclohexane": 29.97,
    "glycerol": 61.00,
    "ammonia": 23.35,
}

# Liquid heat capacity, J/(mol K), approximate near 25 C.
CP_LIQ: dict[str, float] = {
    "water": 75.3,
    "ethanol": 112.0,
    "methanol": 81.6,
    "acetone": 74.0,
    "isopropanol": 143.0,
    "diethyl_ether": 172.0,
    "dichloromethane": 101.0,
    "hexane": 195.0,
    "toluene": 156.0,
    "ethyl_acetate": 168.0,
    "acetic_acid": 123.0,
    "chloroform": 114.0,
    "benzene": 136.0,
    "cyclohexane": 156.0,
    "glycerol": 219.0,
    "ammonia": 80.0,
}


@dataclass(frozen=True)
class Substance:
    """A pure substance with the constants needed for bench calculations."""

    id: str
    name: str
    mw_g_mol: float
    density_g_ml: float
    melting_c: float
    boiling_c: float
    critical_c: float = 0.0

    @property
    def has_antoine(self) -> bool:
        return self.id in ANTOINE


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def vapor_pressure_kpa(substance: Substance, temp_c: float) -> float:
    """Antoine vapour pressure in kPa.

    Outside the fitted range the value is still returned but clamped to a
    physically possible band so the UI never shows a negative pressure.
    """
    if substance.id not in ANTOINE:
        # Fallback: Clausius-Clapeyron anchored at the normal boiling point.
        if substance.boiling_c <= 0.0:
            return 0.0
        hvap = H_VAP_KJ_MOL.get(substance.id, 35.0) * 1000.0
        t = temp_c + 273.15
        tb = substance.boiling_c + 273.15
        exponent = -(hvap / R) * (1.0 / t - 1.0 / tb)
        return P_ATM * math.exp(_clamp(exponent, -50.0, 50.0))

    a, b, c, _t_min, _t_max = ANTOINE[substance.id]
    log_p = a - b / (c + temp_c)
    return max(0.0, 10.0**log_p)


def boiling_point_c(substance: Substance, pressure_kpa: float = P_ATM) -> float:
    """Boiling point at a given pressure, by bisection on the Antoine curve."""
    if pressure_kpa <= 0.0:
        raise ValueError("pressure must be positive")
    if substance.id not in ANTOINE:
        return substance.boiling_c

    lo, hi = -60.0, 400.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if vapor_pressure_kpa(substance, mid) < pressure_kpa:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2.0, 2)


def phase_at(substance: Substance, temp_c: float, pressure_kpa: float = P_ATM) -> str:
    """Return 'solid', 'liquid' or 'gas' for the given conditions."""
    if temp_c <= substance.melting_c:
        return "solid"
    if temp_c >= boiling_point_c(substance, pressure_kpa):
        return "gas"
    return "liquid"


def heat_to_temperature_kj(
    substance: Substance, mass_g: float, from_c: float, to_c: float
) -> float:
    """Sensible heat for a liquid, in kJ (no phase change)."""
    if mass_g <= 0.0:
        return 0.0
    moles = mass_g / substance.mw_g_mol
    cp = CP_LIQ.get(substance.id, 100.0)
    return moles * cp * (to_c - from_c) / 1000.0


def closed_vessel_pressure_kpa(
    substance: Substance,
    temp_c: float,
    fill_fraction: float,
    initial_pressure_kpa: float = P_ATM,
) -> float:
    """Pressure in a sealed vessel heated from 20 C.

    Uses the ideal-gas head space plus the saturated vapour pressure: once the
    liquid is boiling the pressure cannot exceed the vapour pressure curve.
    ``fill_fraction`` is the fraction of the vessel volume occupied by liquid.
    """
    if not 0.0 <= fill_fraction < 1.0:
        raise ValueError("fill_fraction must be in [0, 1)")

    head_space = 1.0 - fill_fraction
    if head_space <= 0.0:
        raise ValueError("a full vessel has no head space")

    # Air already present, heated isochorically from 20 C.
    air = initial_pressure_kpa * (temp_c + 273.15) / 293.15
    vapour = vapor_pressure_kpa(substance, temp_c)
    if phase_at(substance, temp_c) == "liquid":
        vapour = min(vapour, _saturation_limit(substance, temp_c, fill_fraction))
    return max(air, vapour)


def _saturation_limit(substance: Substance, temp_c: float, fill_fraction: float) -> float:
    """Vapour pressure cannot exceed what the liquid inventory can supply."""
    if fill_fraction <= 0.0:
        return 0.0
    # Mole ratio of vaporisable liquid to head-space volume at 1 atm / 20 C.
    liquid_moles = fill_fraction * substance.density_g_ml * 1000.0 / substance.mw_g_mol
    return liquid_moles * R * (temp_c + 273.15) / (22.4e-3 * 1000.0)


def flash_point_estimate_c(substance: Substance) -> float | None:
    """Rough flash point from boiling point (not a substitute for measured data)."""
    if substance.boiling_c <= 0.0:
        return None
    return round(substance.boiling_c * 0.35 - 20.0, 1)


def mixture_boiling_range(
    substances: Iterable[Substance], pressure_kpa: float = P_ATM
) -> tuple[float, float]:
    """Approximate distillation cut range for an ideal mixture."""
    points = sorted(boiling_point_c(s, pressure_kpa) for s in substances)
    if not points:
        raise ValueError("mixture must contain at least one substance")
    return points[0], points[-1]
