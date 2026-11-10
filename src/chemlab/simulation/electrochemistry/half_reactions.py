"""
Standard half-reaction registry for electrochemistry.

All potentials are vs SHE at 25 °C (298.15 K), 1 bar, unit activity.
deltaG0_kj_mol = -n * F * E0 / 1000
"""

from __future__ import annotations

from dataclasses import dataclass

from chemlab.simulation.electrochemistry.constants import F

HALF_REACTION_REGISTRY: dict[str, "HalfReaction"] = {}


@dataclass(frozen=True)
class HalfReaction:
    id: str
    equation: str
    E0_v: float
    n: int
    species_ox: str
    species_red: str

    @property
    def deltaG0_kj_mol(self) -> float:
        return -self.n * F * self.E0_v / 1000.0


def _hr(
    id: str,
    equation: str,
    E0_v: float,
    n: int,
    species_ox: str,
    species_red: str,
) -> HalfReaction:
    hr = HalfReaction(id=id, equation=equation, E0_v=E0_v, n=n, species_ox=species_ox, species_red=species_red)
    HALF_REACTION_REGISTRY[id] = hr
    return hr


# Standard hydrogen electrode
_hr(
    "she",
    "2H+ + 2e- -> H2(g)",
    0.000,
    2,
    "H+",
    "H2(g)",
)

# Metals / metal ions
_hr("cu2_cu", "Cu2+ + 2e- -> Cu(s)", 0.340, 2, "Cu2+", "Cu(s)")
_hr("zn2_zn", "Zn2+ + 2e- -> Zn(s)", -0.763, 2, "Zn2+", "Zn(s)")
_hr("ag_ag", "Ag+ + e- -> Ag(s)", 0.7996, 1, "Ag+", "Ag(s)")
_hr("fe3_fe2", "Fe3+ + e- -> Fe2+", 0.771, 1, "Fe3+", "Fe2+")
_hr("fe2_fe", "Fe2+ + 2e- -> Fe(s)", -0.440, 2, "Fe2+", "Fe(s)")
_hr("al3_al", "Al3+ + 3e- -> Al(s)", -1.662, 3, "Al3+", "Al(s)")
_hr("na_na", "Na+ + e- -> Na(s)", -2.714, 1, "Na+", "Na(s)")

# Non-metals
_hr("cl2_cl", "Cl2(g) + 2e- -> 2Cl-", 1.358, 2, "Cl2(g)", "Cl-")
_hr("o2_h2o", "O2(g) + 4H+ + 4e- -> 2H2O(l)", 1.229, 4, "O2(g)", "H2O(l)")
_hr("o2_oh", "O2(g) + 2H2O(l) + 4e- -> 4OH-", 0.401, 4, "O2(g)", "OH-")
