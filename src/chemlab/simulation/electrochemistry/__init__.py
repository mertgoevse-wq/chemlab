"""
ChemLab Electrochemistry simulation package.

Implements galvanic cells, electrolysis (Faraday's laws), voltammetry
(Randles-Sevcik / Cottrell) and corrosion (mixed potential / Tafel / pitting).

Modules:
  * constants     — F, R, T0, Nernst slope, molar masses
  * half_reactions — standard electrode potential registry (vs SHE)
  * nernst         — NernstEquation solver
  * galvanic       — GalvanicCell (EMF, load current, power)
  * electrolysis   — FaradayResult, ElectrolysisCell
  * voltammetry    — VoltammetrySimulator (Randles-Sevcik, Cottrell)
  * corrosion      — CorrosionSimulator (mixed potential, Tafel, Pourbaix, pitting)
  * conductivity   — Kohlareusch / molar conductivity
"""

from chemlab.simulation.electrochemistry.constants import (  # noqa: F401
    AVOGADRO,
    ELECTRON_CHARGE_C,
    F,
    M_ALUMINIUM,
    M_CHLORINE,
    M_COPPER,
    M_HYDROGEN,
    M_IRON,
    M_SILVER,
    M_SODIUM,
    M_ZINC,
    NERNST_SLOPE_V_DECADE,
    R,
    T0,
)
from chemlab.simulation.electrochemistry.electrolysis import (  # noqa: F401
    ElectrolysisCell,
    FaradayResult,
    faraday_mass_deposited,
    faraday_moles_electrons,
)
from chemlab.simulation.electrochemistry.galvanic import (  # noqa: F401
    GalvanicCell,
)
from chemlab.simulation.electrochemistry.half_reactions import (  # noqa: F401
    HALF_REACTION_REGISTRY,
    HalfReaction,
)
from chemlab.simulation.electrochemistry.nernst import (  # noqa: F401
    NernstSolver,
)

__all__ = [
    "F",
    "R",
    "T0",
    "NERNST_SLOPE_V_DECADE",
    "M_COPPER",
    "M_ZINC",
    "M_SILVER",
    "M_IRON",
    "M_ALUMINIUM",
    "M_SODIUM",
    "M_CHLORINE",
    "M_HYDROGEN",
    "ELECTRON_CHARGE_C",
    "AVOGADRO",
    "NernstSolver",
    "GalvanicCell",
    "ElectrolysisCell",
    "FaradayResult",
    "faraday_mass_deposited",
    "faraday_moles_electrons",
    "HALF_REACTION_REGISTRY",
    "HalfReaction",
]
