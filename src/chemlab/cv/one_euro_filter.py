"""
1-Euro Filter Implementation for 3D Hand Tracking Jitter Attenuation.
Casiez, Roussel, & Vogel (CHI 2012): http://cristal.univ-lille.fr/~casiez/1euro/
Dynamically adjusts low-pass cutoff frequency based on movement velocity.
"""

from __future__ import annotations

import math


def _smoothing_factor(dt: float, cutoff: float) -> float:
    r = 2.0 * math.pi * cutoff * dt
    return r / (r + 1.0)


def _exponential_smoothing(alpha: float, x: float, x_prev: float) -> float:
    return alpha * x + (1.0 - alpha) * x_prev


class OneEuroFilter:
    """
    1D adaptive low-pass filter with velocity-proportional cutoff frequency.
    """

    def __init__(
        self,
        t0: float,
        x0: float,
        dx0: float = 0.0,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.last_x = float(x0)
        self.last_dx = float(dx0)
        self.last_t = float(t0)

    def __call__(self, t: float, x: float) -> float:
        t = float(t)
        x = float(x)
        dt = t - self.last_t

        if dt <= 1e-6:
            return self.last_x

        # 1. Estimate signal derivative (velocity)
        dx = (x - self.last_x) / dt

        # 2. Filter derivative using fixed cutoff d_cutoff
        a_d = _smoothing_factor(dt, self.d_cutoff)
        hat_dx = _exponential_smoothing(a_d, dx, self.last_dx)

        # 3. Compute dynamic cutoff frequency based on velocity magnitude
        cutoff = self.min_cutoff + self.beta * abs(hat_dx)

        # 4. Filter original signal using dynamic cutoff
        a = _smoothing_factor(dt, cutoff)
        hat_x = _exponential_smoothing(a, x, self.last_x)

        # 5. Store state for next iteration
        self.last_x = hat_x
        self.last_dx = hat_dx
        self.last_t = t

        return hat_x


class Point3DOneEuroFilter:
    """
    Filters 3D coordinates (x, y, z) independently using 1-Euro filters.
    """

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.filters: tuple[OneEuroFilter, OneEuroFilter, OneEuroFilter] | None = None

    def __call__(self, t: float, point: tuple[float, float, float]) -> tuple[float, float, float]:
        if self.filters is None:
            self.filters = (
                OneEuroFilter(
                    t, point[0], min_cutoff=self.min_cutoff, beta=self.beta, d_cutoff=self.d_cutoff
                ),
                OneEuroFilter(
                    t, point[1], min_cutoff=self.min_cutoff, beta=self.beta, d_cutoff=self.d_cutoff
                ),
                OneEuroFilter(
                    t, point[2], min_cutoff=self.min_cutoff, beta=self.beta, d_cutoff=self.d_cutoff
                ),
            )
            return point

        fx, fy, fz = self.filters
        return (fx(t, point[0]), fy(t, point[1]), fz(t, point[2]))
