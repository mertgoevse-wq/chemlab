"""
ChemLab Kinetics — reaction rate and oscillation models.

Exports:
  * :class:`BriggsRauscherOscillator` — cyclic Clear → Amber → Deep Blue colour
    model for the Briggs-Rauscher iodine clock reaction.
  * :func:`lerp_color` — linear RGBA interpolation used by the shader layer.

Migrated from ``chemlab_core/chemistry/reaction_engine.py``. The legacy module
re-exports from here for backwards compatibility.
"""

from __future__ import annotations

import math
from typing import Final

from chemlab_core.models import OscillatingPhase, ReactionState

# Optical RGBA colour definitions for Briggs-Rauscher reaction phases:
# Phase 1: Clear / watery colourless solution
COLOR_CLEAR: Final[tuple[float, float, float, float]] = (0.92, 0.96, 0.98, 0.45)
# Phase 2: Amber gold / triiodide intermediate (I3- formation)
COLOR_AMBER: Final[tuple[float, float, float, float]] = (0.85, 0.45, 0.05, 0.85)
# Phase 3: Deep midnight blue (starch-triiodide helical complex)
COLOR_DEEP_BLUE: Final[tuple[float, float, float, float]] = (0.05, 0.08, 0.45, 0.95)


def lerp_color(
    c1: tuple[float, float, float, float],
    c2: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    """Linear interpolation between two RGBA colours."""
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
    1. Clear / colourless (induction phase)
    2. Amber / gold (rapid I- and I3- accumulation)
    3. Deep blue / purple (starch-triiodide complex saturation)
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
        """Advance reaction simulation by ``delta_time`` seconds."""
        if delta_time < 0.0:
            raise ValueError("delta_time cannot be negative")

        self._elapsed_time += delta_time
        self._cycle_index = int(self._elapsed_time // self._period)

        cycle_progress = (self._elapsed_time % self._period) / self._period

        phase: OscillatingPhase
        phase_progress: float
        current_color: tuple[float, float, float, float]

        if cycle_progress < 0.333:
            phase = OscillatingPhase.CLEAR_INDUCTION
            phase_progress = cycle_progress / 0.333
            smoothed_t = 1.0 / (1.0 + math.exp(-12.0 * (phase_progress - 0.7)))
            current_color = lerp_color(COLOR_CLEAR, COLOR_AMBER, smoothed_t)
        elif cycle_progress < 0.666:
            phase = OscillatingPhase.AMBER_TRIIODIDE
            phase_progress = (cycle_progress - 0.333) / 0.333
            smoothed_t = 1.0 / (1.0 + math.exp(-14.0 * (phase_progress - 0.5)))
            current_color = lerp_color(COLOR_AMBER, COLOR_DEEP_BLUE, smoothed_t)
        else:
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


class OregonatorModel:
    """Field-Noyes-Koros (Oregonator) 3-variable ODE model for the Belousov-Zhabotinsky reaction.

    Variables:
      x = [HBrO2] (dimensionless activator intermediate)
      y = [Br-]    (dimensionless inhibitor ion)
      z = [Ce(IV)] (dimensionless oxidized metal catalyst / ferroin indicator)

    Differential system:
      dx/dt = (q*y - x*y + x*(1 - x)) / epsilon
      dy/dt = (-q*y - x*y + f*z) / epsilon_prime
      dz/dt = x - z

    Generates limit-cycle periodic color transitions:
      Ferroin [Fe(phen)3]2+ (red) <-> Ferriin [Fe(phen)3]3+ (blue).
    """

    COLOR_FERROIN_RED: Final[tuple[float, float, float, float]] = (0.85, 0.12, 0.12, 0.95)
    COLOR_FERRIIN_BLUE: Final[tuple[float, float, float, float]] = (0.10, 0.35, 0.90, 0.95)
    MAX_INTERNAL_TIMESTEP: Final[float] = 5.0e-4

    def __init__(
        self,
        q: float = 8.0e-4,
        f: float = 1.0,
        eps: float = 4.0e-2,
        eps_prime: float = 2.0e-4,
    ) -> None:
        self.q = q
        self.f = f
        self.eps = eps
        self.eps_prime = eps_prime

    def derivatives(
        self,
        x: float,
        y: float,
        z: float,
    ) -> tuple[float, float, float]:
        """Compute instantaneous derivatives dx/dt, dy/dt, dz/dt."""
        dx = (self.q * y - x * y + x * (1.0 - x)) / self.eps
        dy = (-self.q * y - x * y + self.f * z) / self.eps_prime
        dz = x - z
        return dx, dy, dz

    def step_rk4(
        self,
        state: tuple[float, float, float],
        dt: float,
    ) -> tuple[float, float, float]:
        """Advance by ``dt`` with stable RK4 substeps for this stiff ODE system."""
        if dt < 0.0:
            raise ValueError("dt cannot be negative")
        if dt == 0.0:
            return state

        substep_count = max(1, math.ceil(dt / self.MAX_INTERNAL_TIMESTEP))
        substep_dt = dt / substep_count
        next_state = state
        for _ in range(substep_count):
            next_state = self._step_rk4_once(next_state, substep_dt)
        return next_state

    def _step_rk4_once(
        self,
        state: tuple[float, float, float],
        dt: float,
    ) -> tuple[float, float, float]:
        """Apply one RK4 step no larger than ``MAX_INTERNAL_TIMESTEP``."""
        x, y, z = state
        k1_x, k1_y, k1_z = self.derivatives(x, y, z)

        k2_x, k2_y, k2_z = self.derivatives(
            x + 0.5 * dt * k1_x,
            y + 0.5 * dt * k1_y,
            z + 0.5 * dt * k1_z,
        )

        k3_x, k3_y, k3_z = self.derivatives(
            x + 0.5 * dt * k2_x,
            y + 0.5 * dt * k2_y,
            z + 0.5 * dt * k2_z,
        )

        k4_x, k4_y, k4_z = self.derivatives(
            x + dt * k3_x,
            y + dt * k3_y,
            z + dt * k3_z,
        )

        nx = x + (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
        ny = y + (dt / 6.0) * (k1_y + 2.0 * k2_y + 2.0 * k3_y + k4_y)
        nz = z + (dt / 6.0) * (k1_z + 2.0 * k2_z + 2.0 * k3_z + k4_z)

        # Roundoff may produce tiny negatives near the invariant boundary.
        return max(0.0, nx), max(0.0, ny), max(0.0, nz)

    def get_color(self, state: tuple[float, float, float]) -> tuple[float, float, float, float]:
        """Map catalyst oxidation state z to ferroin indicator color (red <-> blue)."""
        _, _, z = state
        # The default parameter set keeps z near 0.004-0.32 after transients.
        t = max(0.0, min(1.0, (z - 0.004) / 0.316))
        return lerp_color(self.COLOR_FERROIN_RED, self.COLOR_FERRIIN_BLUE, t)
