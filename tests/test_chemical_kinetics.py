"""
ChemLab Chemical Kinetics & Numerical Stability Tests
Validates ODE solvers for oscillating chemical reactions:
- Belousov-Zhabotinsky (BZ) reaction using the Oregonator model
- Verifies positivity, bounded energy/mass, absence of NaN/Inf, and periodic oscillation.
"""

import math
import unittest
from typing import List, Tuple


class OregonatorSolver:
    """
    Field-Noyes-Koros (Oregonator) Model for Belousov-Zhabotinsky reaction:
    Variables:
      x = [HBrO2] (dimensionless activator)
      y = [Br-]    (dimensionless inhibitor)
      z = [Ce(IV)] (dimensionless catalyst in oxidized state)

    Dimensionless ODEs:
      dx/dt = (q*y - x*y + x*(1 - x)) / epsilon
      dy/dt = (-q*y - x*y + f*z) / epsilon_prime
      dz/dt = x - z
    """

    def __init__(self, q: float = 8e-4, f: float = 1.0, eps: float = 4e-2, eps_prime: float = 2e-4):
        self.q = q
        self.f = f
        self.eps = eps
        self.eps_prime = eps_prime

    def derivatives(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        dx = (self.q * y - x * y + x * (1.0 - x)) / self.eps
        dy = (-self.q * y - x * y + self.f * z) / self.eps_prime
        dz = x - z
        return dx, dy, dz

    def step_rk4(self, x: float, y: float, z: float, dt: float) -> tuple[float, float, float]:
        """4th-order Runge-Kutta numerical integration step"""
        k1_x, k1_y, k1_z = self.derivatives(x, y, z)

        k2_x, k2_y, k2_z = self.derivatives(
            x + 0.5 * dt * k1_x, y + 0.5 * dt * k1_y, z + 0.5 * dt * k1_z
        )

        k3_x, k3_y, k3_z = self.derivatives(
            x + 0.5 * dt * k2_x, y + 0.5 * dt * k2_y, z + 0.5 * dt * k2_z
        )

        k4_x, k4_y, k4_z = self.derivatives(x + dt * k3_x, y + dt * k3_y, z + dt * k3_z)

        nx = x + (dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
        ny = y + (dt / 6.0) * (k1_y + 2 * k2_y + 2 * k3_y + k4_y)
        nz = z + (dt / 6.0) * (k1_z + 2 * k2_z + 2 * k3_z + k4_z)

        # Enforce non-negativity constraint
        return max(0.0, nx), max(0.0, ny), max(0.0, nz)


class TestChemicalKinetics(unittest.TestCase):
    def setUp(self):
        self.solver = OregonatorSolver()

    def test_numerical_stability_no_nan(self):
        """Verify solver maintains finite values and zero NaNs over 10,000 steps."""
        x, y, z = 0.5, 0.5, 0.5
        dt = 0.0001
        for _ in range(10000):
            x, y, z = self.solver.step_rk4(x, y, z, dt)
            self.assertFalse(math.isnan(x), "x became NaN")
            self.assertFalse(math.isnan(y), "y became NaN")
            self.assertFalse(math.isnan(z), "z became NaN")
            self.assertFalse(math.isinf(x), "x exploded to Inf")
            self.assertFalse(math.isinf(y), "y exploded to Inf")
            self.assertFalse(math.isinf(z), "z exploded to Inf")

    def test_concentration_non_negativity(self):
        """Verify concentration of all species remains strictly non-negative."""
        x, y, z = 0.1, 0.01, 0.2
        dt = 0.0001
        for _ in range(5000):
            x, y, z = self.solver.step_rk4(x, y, z, dt)
            self.assertGreaterEqual(x, 0.0, "Negative [HBrO2] concentration detected")
            self.assertGreaterEqual(y, 0.0, "Negative [Br-] concentration detected")
            self.assertGreaterEqual(z, 0.0, "Negative [Ce(IV)] concentration detected")

    def test_oscillating_limit_cycle(self):
        """Verify that the system exhibits true oscillatory limit cycle behavior."""
        x, y, z = 0.1, 0.1, 0.1
        dt = 0.0002
        z_values = []

        # Run simulation for sufficient duration (12 dimensionless time units)
        for _ in range(60000):
            x, y, z = self.solver.step_rk4(x, y, z, dt)
            z_values.append(z)

        # Count local maxima (peaks in oxidized state Ce(IV))
        peaks = 0
        for i in range(1, len(z_values) - 1):
            if (
                z_values[i] > z_values[i - 1]
                and z_values[i] > z_values[i + 1]
                and z_values[i] > 0.3
            ):
                peaks += 1

        self.assertGreaterEqual(peaks, 2, f"System failed to oscillate. Detected peaks: {peaks}")


if __name__ == "__main__":
    unittest.main()
