"""
ChemLab Authoritative Chemistry Package
========================================

Consolidated scientific calculation engine unifying:
- Thermodynamics (NIST/CRC constants, Hess's Law, van 't Hoff, titration)
- Kinetics (Arrhenius, ODE solver, Briggs-Rauscher, side reactions)
- Safety (GHS, fume hood, thermal runaway, compatibility)
- Cheminformatics (RDKit bridge, 3D conformers, Lipinski)
- Catalog (200+ authenticated reagents with full GHS data)

All legacy modules (chemlab_core/chemistry, src/chemlab/simulation/*,
simulation/*, safety_simulation/*) are thin wrappers delegating here.
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    "thermodynamics",
    "kinetics",
    "safety",
    "cheminformatics",
    "catalog",
]
