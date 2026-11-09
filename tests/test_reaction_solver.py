"""
Tests for ChemLab Chemical Simulation & Reaction Solver
Verifies stoichiometry, fluid mixing, pH indicator transitions, and oscillating clock state machines.
"""

import pytest

from chemlab.models import ChemicalReagent, LiquidMixture
from chemlab.simulation.reaction_solver import (
    ReactionType,
    mix_liquids,
    step_simulation,
)
from chemlab.simulation.reagents import REAGENT_REGISTRY, get_reagent


def test_reagent_registry_lookup():
    """Verify registry contains fundamental chemicals with valid GHS safety data."""
    hcl = get_reagent("hcl")
    assert hcl.formula == "HCl"
    assert hcl.ph < 2.0
    # Check for GHS05 (Corrosive) pictogram in hazards
    assert any(h.pictogram == "GHS05" for h in hcl.ghs_hazards)

    naoh = get_reagent("naoh")
    assert naoh.formula == "NaOH"
    assert naoh.ph > 12.0
    # Check for GHS05 (Corrosive) pictogram in hazards
    assert any(h.pictogram == "GHS05" for h in naoh.ghs_hazards)


def test_liquid_mixing_volume_and_temp():
    """Mixing two liquids must conserve total volume and calculate weighted thermal equilibrium."""
    water_cold = LiquidMixture(
        volume_ml=100.0,
        temperature_c=20.0,
        reagent_moles={"water": 5.55},
        color_rgb=(0.95, 0.98, 1.0),
    )
    water_hot = LiquidMixture(
        volume_ml=100.0,
        temperature_c=80.0,
        reagent_moles={"water": 5.55},
        color_rgb=(0.95, 0.98, 1.0),
    )

    mixed = mix_liquids(water_cold, water_hot)
    assert pytest.approx(mixed.volume_ml, rel=1e-3) == 200.0
    assert pytest.approx(mixed.temperature_c, rel=1e-3) == 50.0
    assert pytest.approx(mixed.reagent_moles["water"], rel=1e-3) == 11.1


def test_acid_base_neutralization():
    """Mixing equimolar HCl and NaOH must neutralize pH to ~7 and produce exothermic heat."""
    acid = LiquidMixture(
        volume_ml=50.0,
        temperature_c=20.0,
        reagent_moles={"water": 2.7, "hcl": 0.05, "universal_indicator": 0.0001},
        color_rgb=(0.95, 0.15, 0.15),  # Red in acid
    )
    base = LiquidMixture(
        volume_ml=50.0,
        temperature_c=20.0,
        reagent_moles={"water": 2.7, "naoh": 0.05},
        color_rgb=(0.95, 0.98, 1.0),
    )

    mixed = mix_liquids(acid, base)
    result, event = step_simulation(mixed, dt_s=1.0)

    # Equimolar neutralization
    assert result.reagent_moles.get("hcl", 0.0) < 0.005
    assert result.reagent_moles.get("naoh", 0.0) < 0.005
    assert result.reagent_moles.get("nacl", 0.0) > 0.04
    # Exothermic reaction releases heat
    assert result.temperature_c > 20.0
    # Indicator transitions towards neutral green (0.1, 0.8, 0.2)
    assert result.color_rgb[1] > result.color_rgb[0]  # Green > Red


def test_briggs_rauscher_oscillation():
    """
    Briggs-Rauscher oscillating iodine clock must periodically cycle colors:
    Clear -> Amber -> Midnight Blue -> Clear.
    """
    br_mixture = LiquidMixture(
        volume_ml=150.0,
        temperature_c=22.0,
        reagent_moles={
            "water": 8.0,
            "malonic_acid": 0.02,
            "potassium_iodate": 0.03,
            "hydrogen_peroxide": 0.10,
            "manganese_sulfate": 0.002,
            "starch": 0.001,
        },
        color_rgb=(0.95, 0.98, 1.0),  # Initial clear
    )

    # Step simulation forward across 10 seconds in 0.5s increments
    colors_observed = []
    current = br_mixture

    for _ in range(20):
        current, event = step_simulation(current, dt_s=0.5)
        colors_observed.append(current.color_rgb)

    # Verify that color shifts occurred (not static)
    initial_color = colors_observed[0]
    has_changed = any(
        abs(c[0] - initial_color[0]) > 0.2
        or abs(c[1] - initial_color[1]) > 0.2
        or abs(c[2] - initial_color[2]) > 0.2
        for c in colors_observed
    )
    assert has_changed, "Briggs-Rauscher reaction must oscillate colors over time"


def test_elephant_toothpaste_catalysis():
    """H2O2 decomposition with KI catalyst generates rapid gas bubbles and expanding foam."""
    h2o2_soap = LiquidMixture(
        volume_ml=50.0,
        temperature_c=20.0,
        reagent_moles={"water": 2.5, "hydrogen_peroxide": 0.08, "dish_soap": 0.01},
        color_rgb=(0.9, 0.9, 0.95),
    )
    ki_catalyst = LiquidMixture(
        volume_ml=10.0,
        temperature_c=20.0,
        reagent_moles={"water": 0.5, "potassium_iodide": 0.02},
        color_rgb=(0.95, 0.98, 1.0),
    )

    mixed = mix_liquids(h2o2_soap, ki_catalyst)
    result, event = step_simulation(mixed, dt_s=0.5)

    assert event == ReactionType.CATALYTIC_FOAM_ERUPTION
    assert result.bubble_rate > 0.5
    assert result.foam_volume_ml > 50.0
    assert result.temperature_c > 22.0  # Exothermic
