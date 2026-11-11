"""
Thermodynamic Database — NIST/CRC Standard Properties
=====================================================

Authoritative constants for 40+ pure chemical species.
Each entry carries: ΔH°f (kJ/mol), S° (J/(mol·K)), Cp (J/(mol·K)),
molecular weight (g/mol), density (g/cm³).

Source: NIST Chemistry WebBook, CRC Handbook of Chemistry and Physics.
DO NOT INVENT VALUES — only add verified literature constants.
"""

from __future__ import annotations

from chemlab.chemistry.thermodynamics.engine import (
    THERMO_DATABASE,
    ThermodynamicState,
)

__all__ = ["ThermodynamicState", "THERMO_DATABASE"]
