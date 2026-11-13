"""Tests for the pyrotechnic composition model."""

import pytest

from chemlab.chemistry.pyrotechnics import (
    Component,
    Composition,
    burn_rate,
    evaluate,
    oxygen_balance,
)


def make(*pairs, name="test", colorant="none", confinement=0.0, moisture=0.0):
    return Composition(
        name=name,
        components=tuple(Component(s, f) for s, f in pairs),
        colorant=colorant,
        confinement=confinement,
        moisture_fraction=moisture,
    )


BLACK_POWDER = make(
    ("potassium_nitrate", 0.75),
    ("charcoal", 0.15),
    ("sulfur", 0.10),
    name="black powder",
)

RED_STAR = make(
    ("potassium_perchlorate", 0.55),
    ("strontium_nitrate", 0.20),
    ("charcoal", 0.15),
    ("dextrin", 0.10),
    name="red star",
    colorant="strontium",
)

CHLORATE_MIX = make(
    ("potassium_chlorate", 0.70),
    ("sulfur", 0.30),
    name="chlorate sulfur",
)


def test_fractions_must_sum_to_one():
    with pytest.raises(ValueError):
        make(("potassium_nitrate", 0.5), ("charcoal", 0.2))


def test_black_powder_oxygen_balance_is_slightly_negative():
    # 75/15/10 black powder is deliberately fuel-rich; it makes CO and K2S.
    assert -0.20 < oxygen_balance(BLACK_POWDER) < -0.05


def test_black_powder_burns():
    assert burn_rate(BLACK_POWDER) > 5.0


def test_confinement_increases_burn_rate():
    open_pile = BLACK_POWDER
    confined = make(
        ("potassium_nitrate", 0.75),
        ("charcoal", 0.15),
        ("sulfur", 0.10),
        confinement=0.8,
    )
    assert burn_rate(confined) > burn_rate(open_pile)


def test_red_star_is_strontium_red():
    result = evaluate(RED_STAR)
    assert result.emission_nm == 606
    assert result.flame_rgb[0] > result.flame_rgb[2]


def test_chlorate_sulfur_is_extreme():
    result = evaluate(CHLORATE_MIX)
    assert result.sensitivity == "extreme"
    assert any("friction" in warning for warning in result.warnings)


def test_moisture_reduces_burn_rate():
    dry = evaluate(BLACK_POWDER)
    wet = evaluate(
        make(
            ("potassium_nitrate", 0.75),
            ("charcoal", 0.15),
            ("sulfur", 0.10),
            moisture=0.05,
        )
    )
    assert wet.burn_rate_mm_s < dry.burn_rate_mm_s


def test_barium_warns_about_toxicity():
    green = make(
        ("potassium_perchlorate", 0.55),
        ("barium_nitrate", 0.25),
        ("charcoal", 0.20),
        colorant="barium",
    )
    result = evaluate(green)
    assert any("Barium" in warning for warning in result.warnings)
