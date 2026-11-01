"""
Unit tests for the chemical reaction simulation engine.
Validates oscillating kinetics (Briggs-Rauscher) and RGBA shader color generation.
"""

import pytest

from chemlab_core.chemistry.reaction_engine import (
    COLOR_AMBER,
    COLOR_CLEAR,
    COLOR_DEEP_BLUE,
    BriggsRauscherOscillator,
    lerp_color,
)
from chemlab_core.models import OscillatingPhase


@pytest.mark.unit
def test_lerp_color_boundaries() -> None:
    """Verify linear interpolation at extremes and intermediate fractions."""
    c1 = (0.0, 0.0, 0.0, 1.0)
    c2 = (1.0, 1.0, 1.0, 1.0)

    assert lerp_color(c1, c2, 0.0) == c1
    assert lerp_color(c1, c2, 1.0) == c2
    mid = lerp_color(c1, c2, 0.5)
    assert mid == (0.5, 0.5, 0.5, 1.0)


@pytest.mark.unit
def test_oscillator_cycle_progression() -> None:
    """Verify reaction steps sequentially through Clear, Amber, and Deep Blue phases."""
    period = 6.0
    oscillator = BriggsRauscherOscillator(period_seconds=period)

    # 1. At t=0.5s (early cycle) -> CLEAR_INDUCTION
    s1 = oscillator.step(0.5)
    assert s1.phase == OscillatingPhase.CLEAR_INDUCTION
    assert s1.cycle_index == 0
    # Clear color has high red and green (transparent glass tint)
    assert s1.color_rgba[0] > 0.8

    # 2. Advance to t=2.5s -> AMBER_TRIIODIDE
    s2 = oscillator.step(2.0)
    assert s2.phase == OscillatingPhase.AMBER_TRIIODIDE
    assert s2.cycle_index == 0
    # Amber has high red and moderate green, low blue
    assert s2.color_rgba[0] > s2.color_rgba[2]

    # 3. Advance to t=4.5s -> DEEP_BLUE_COMPLEX
    s3 = oscillator.step(2.0)
    assert s3.phase == OscillatingPhase.DEEP_BLUE_COMPLEX
    assert s3.cycle_index == 0
    # Deep blue has dominant blue component
    assert s3.color_rgba[2] > s3.color_rgba[0]

    # 4. Advance past period (t=6.5s) -> wraps back to cycle 1 CLEAR_INDUCTION
    s4 = oscillator.step(2.0)
    assert s4.phase == OscillatingPhase.CLEAR_INDUCTION
    assert s4.cycle_index == 1


@pytest.mark.unit
def test_oscillator_negative_time_rejection() -> None:
    """Verify oscillator rejects negative delta_time values."""
    oscillator = BriggsRauscherOscillator(period_seconds=6.0)
    with pytest.raises(ValueError):
        oscillator.step(-1.0)
