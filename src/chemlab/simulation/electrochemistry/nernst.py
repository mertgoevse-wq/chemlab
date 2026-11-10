"""
Nernst equation solver.

E = E° - (RT / nF) * ln(Q)
  = E° - (0.05916 / n) * log10(Q)   at T = 298.15 K

All logarithms are natural unless noted. Activities are approximated by
molarity for dilute solutions.
"""

from __future__ import annotations

import math

from chemlab.simulation.electrochemistry.constants import F, R, T0, NERNST_SLOPE_V_DECADE
from chemlab.simulation.electrochemistry.half_reactions import HALF_REACTION_REGISTRY, HalfReaction


class NernstSolver:
    """Computes half-cell and full-cell potentials via the Nernst equation."""

    def half_cell_potential(
        self,
        hr: HalfReaction,
        activities: dict[str, float],
        temperature_k: float = T0,
    ) -> float:
        """
        Half-cell reduction potential:
            E = E° - (RT / nF) * ln(a_red / a_ox)

        ``activities`` maps species -> activity (approx. molarity).
        Missing species default to 1.0.
        """
        a_ox = activities.get(hr.species_ox, 1.0)
        a_red = activities.get(hr.species_red, 1.0)
        if a_ox <= 0.0 or a_red <= 0.0:
            raise ValueError("Activities must be strictly positive for the Nernst equation.")
        q = a_red / a_ox
        return hr.E0_v - (R * temperature_k) / (hr.n * F) * math.log(q)

    def cell_emf(
        self,
        cathode: HalfReaction,
        cathode_activities: dict[str, float],
        anode: HalfReaction,
        anode_activities: dict[str, float],
        temperature_k: float = T0,
    ) -> float:
        """Full-cell EMF: E_cell = E_cathode - E_anode."""
        e_cath = self.half_cell_potential(cathode, cathode_activities, temperature_k)
        e_an = self.half_cell_potential(anode, anode_activities, temperature_k)
        return e_cath - e_an

    def equilibrium_constant(self, e0_v: float, n: int, temperature_k: float = T0) -> float:
        """K = exp(n * F * E° / (R * T)) = 10^(n * E° / 0.05916) at 25 °C."""
        exponent = (n * F * e0_v) / (R * temperature_k)
        # Clamp to avoid overflow
        exponent = max(-700.0, min(700.0, exponent))
        return math.exp(exponent)
