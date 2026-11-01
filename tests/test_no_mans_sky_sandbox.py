"""
Unit tests for the No Man's Sky-style Configurable Laboratory Sandbox Matrix.
Tests thermodynamic scaling with ambient pressure (Clausius-Clapeyron boiling point),
gravity-driven fluid pouring kinetics, time warp dilation, and consequence toggles.
"""

from __future__ import annotations

import pytest

from chemlab.sandbox.no_mans_sky_matrix import (
    HazardDifficulty,
    LaboratoryEnvironmentMatrix,
    PlanetaryPreset,
)


def test_standard_earth_baseline_environment() -> None:
    env = LaboratoryEnvironmentMatrix()
    assert env.gravity_g == 1.0
    assert env.ambient_pressure_atm == 1.0
    assert env.ambient_temperature_c == 22.0
    assert env.time_warp == 1.0
    assert env.boiling_point_water_c == pytest.approx(100.0, abs=0.5)


def test_clausius_clapeyron_boiling_point_under_vacuum() -> None:
    # Under low pressure (0.1 atm, like atop Mount Everest or in vacuum desiccator),
    # water boils at a substantially lower temperature (~45.8 °C)
    env = LaboratoryEnvironmentMatrix(ambient_pressure_atm=0.1)
    assert env.boiling_point_water_c < 55.0
    assert env.boiling_point_water_c > 40.0


def test_planetary_preset_mars_and_orbital_zero_g() -> None:
    # Zero-G Orbital Lab preset
    zero_g = LaboratoryEnvironmentMatrix.from_preset(PlanetaryPreset.ORBITAL_ZERO_G)
    assert zero_g.gravity_g == 0.0
    assert (
        zero_g.pour_velocity_multiplier == 0.0
    )  # Liquids form free floating spheres, no downward pour

    # Martian Surface Lab
    mars = LaboratoryEnvironmentMatrix.from_preset(PlanetaryPreset.MARTIAN_SURFACE)
    assert mars.gravity_g == pytest.approx(0.38, abs=0.01)
    assert mars.ambient_pressure_atm < 0.02
    assert mars.ambient_temperature_c < -40.0


def test_hazard_difficulty_modes() -> None:
    # Godmode: no glass breakage or lethal runaway explosions
    creative = LaboratoryEnvironmentMatrix(hazard_difficulty=HazardDifficulty.CREATIVE_GODMODE)
    assert not creative.allow_glass_shattering
    assert not creative.allow_lethal_toxic_spills

    # Hardcore: strict realistic consequences
    hardcore = LaboratoryEnvironmentMatrix(hazard_difficulty=HazardDifficulty.HARDCORE_REALISTIC)
    assert hardcore.allow_glass_shattering
    assert hardcore.allow_lethal_toxic_spills
