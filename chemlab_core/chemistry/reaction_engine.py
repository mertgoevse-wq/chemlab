"""
Chemical Reaction Simulation Engine.
Implements mathematical models for oscillating reactions (Briggs-Rauscher / BZ).
Outputs continuous RGBA colors for photorealistic liquid rendering.
"""

import math
from typing import Final

from chemlab_core.models import OscillatingPhase, ReactionState

# Optical RGBA color definitions for Briggs-Rauscher reaction phases:
# Phase 1: Clear / Watery colorless solution (Malonic acid + MnSO4 + H2O2 + KIO3)
COLOR_CLEAR: Final[tuple[float, float, float, float]] = (0.92, 0.96, 0.98, 0.45)
# Phase 2: Amber gold / triiodide intermediate (I3- formation)
COLOR_AMBER: Final[tuple[float, float, float, float]] = (0.85, 0.45, 0.05, 0.85)
# Phase 3: Deep midnight blue (Starch-triiodide helical complex)
COLOR_DEEP_BLUE: Final[tuple[float, float, float, float]] = (0.05, 0.08, 0.45, 0.95)


def lerp_color(
    c1: tuple[float, float, float, float],
    c2: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    """Linear interpolation between two RGBA colors."""
    clamped_t = max(0.0, min(1.0, t))
    return (
        c1[0] + (c2[0] - c1[0]) * clamped_t,
        c1[1] + (c2[1] - c1[1]) * clamped_t,
        c1[2] + (c2[2] - c1[2]) * clamped_t,
        c1[3] + (c2[3] - c1[3]) * clamped_t,
    )


class BriggsRauscherOscillator:
    """Simulates chemical oscillations of the Briggs-Rauscher reaction.

    The cycle repeats smoothly:
    1. Clear / Colorless (Induction phase)
    2. Amber / Gold (Rapid I- and I3- accumulation)
    3. Deep Blue / Purple (Starch-triiodide complex saturation)
    followed by radical reduction back to Clear.
    """

    def __init__(self, period_seconds: float = 6.0) -> None:
        if period_seconds <= 0.0:
            raise ValueError("Oscillation period must be strictly positive")
        self._period = period_seconds
        self._elapsed_time = 0.0
        self._cycle_index = 0

    def reset(self) -> None:
        """Reset reaction timer to initial state."""
        self._elapsed_time = 0.0
        self._cycle_index = 0

    def step(self, delta_time: float) -> ReactionState:
        """Advance reaction simulation by delta_time seconds and return updated state."""
        if delta_time < 0.0:
            raise ValueError("delta_time cannot be negative")

        self._elapsed_time += delta_time
        self._cycle_index = int(self._elapsed_time // self._period)

        # Normalized progress within the current oscillation cycle [0.0, 1.0)
        cycle_progress = (self._elapsed_time % self._period) / self._period

        phase: OscillatingPhase
        phase_progress: float
        current_color: tuple[float, float, float, float]

        # Three equal stages in the cycle
        if cycle_progress < 0.333:
            # Stage 1: Clear -> Amber
            phase = OscillatingPhase.CLEAR_INDUCTION
            phase_progress = cycle_progress / 0.333
            # Sigmoid smoothing for realistic sudden chemical color flip
            smoothed_t = 1.0 / (1.0 + math.exp(-12.0 * (phase_progress - 0.7)))
            current_color = lerp_color(COLOR_CLEAR, COLOR_AMBER, smoothed_t)

        elif cycle_progress < 0.666:
            # Stage 2: Amber -> Deep Blue
            phase = OscillatingPhase.AMBER_TRIIODIDE
            phase_progress = (cycle_progress - 0.333) / 0.333
            smoothed_t = 1.0 / (1.0 + math.exp(-14.0 * (phase_progress - 0.5)))
            current_color = lerp_color(COLOR_AMBER, COLOR_DEEP_BLUE, smoothed_t)

        else:
            # Stage 3: Deep Blue -> Clear
            phase = OscillatingPhase.DEEP_BLUE_COMPLEX
            phase_progress = (cycle_progress - 0.666) / 0.334
            smoothed_t = 1.0 / (1.0 + math.exp(-10.0 * (phase_progress - 0.6)))
            current_color = lerp_color(COLOR_DEEP_BLUE, COLOR_CLEAR, smoothed_t)

        return ReactionState(
            cycle_index=self._cycle_index,
            phase=phase,
            phase_progress=phase_progress,
            color_rgba=current_color,
            temperature_celsius=22.5 + 0.3 * math.sin(cycle_progress * 2.0 * math.pi),
            period_seconds=self._period,
        )
