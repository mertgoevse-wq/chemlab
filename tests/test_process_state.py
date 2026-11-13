"""Tests for the bench thermodynamics model."""

import pytest

from chemlab.chemistry.process_state import (
    P_ATM,
    Substance,
    boiling_point_c,
    closed_vessel_pressure_kpa,
    heat_to_temperature_kj,
    mixture_boiling_range,
    phase_at,
    vapor_pressure_kpa,
)

WATER = Substance("water", "Water", 18.015, 0.997, 0.0, 100.0)
ETHANOL = Substance("ethanol", "Ethanol", 46.07, 0.789, -114.1, 78.4)
ACETONE = Substance("acetone", "Acetone", 58.08, 0.784, -94.7, 56.1)
SUGAR = Substance("sucrose", "Sucrose", 342.3, 1.59, 186.0, 0.0)


def test_water_boils_at_100c():
    assert vapor_pressure_kpa(WATER, 100.0) == pytest.approx(P_ATM, rel=0.02)


def test_ethanol_boils_near_78c():
    assert boiling_point_c(ETHANOL) == pytest.approx(78.4, abs=0.6)


def test_acetone_is_more_volatile_than_water():
    assert vapor_pressure_kpa(ACETONE, 25.0) > vapor_pressure_kpa(WATER, 25.0) * 5


def test_phase_transitions():
    assert phase_at(WATER, -10.0) == "solid"
    assert phase_at(WATER, 25.0) == "liquid"
    assert phase_at(WATER, 120.0) == "gas"


def test_boiling_point_drops_at_lower_pressure():
    assert boiling_point_c(WATER, 20.0) < 70.0


def test_closed_vessel_pressure_rises_with_temperature():
    cold = closed_vessel_pressure_kpa(ACETONE, 20.0, 0.5)
    hot = closed_vessel_pressure_kpa(ACETONE, 80.0, 0.5)
    assert hot > cold
    assert hot > P_ATM


def test_closed_vessel_rejects_full_fill():
    with pytest.raises(ValueError):
        closed_vessel_pressure_kpa(WATER, 90.0, 1.0)


def test_substance_without_antoine_uses_clausius_clapeyron():
    # Sucrose decomposes rather than boils, but the fallback must stay finite.
    assert vapor_pressure_kpa(SUGAR, 25.0) >= 0.0


def test_heat_scales_with_mass():
    small = heat_to_temperature_kj(WATER, 100.0, 20.0, 80.0)
    large = heat_to_temperature_kj(WATER, 200.0, 20.0, 80.0)
    assert large == pytest.approx(small * 2.0)
    # 100 g water, 60 K: 5.55 mol * 75.3 J/molK * 60 K ~= 25 kJ
    assert 20.0 < small < 30.0


def test_mixture_range():
    low, high = mixture_boiling_range([ACETONE, WATER])
    assert low < high
    assert low == pytest.approx(56.1, abs=1.0)
