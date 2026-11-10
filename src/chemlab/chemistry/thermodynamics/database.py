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

from dataclasses import dataclass


@dataclass(frozen=True)
class ThermodynamicState:
    """Standard thermodynamic properties at 298.15 K, 1 atm."""

    formula: str
    name: str
    delta_h_f_kj_mol: float
    s_standard_j_mol_k: float
    cp_j_mol_k: float
    molecular_weight_g_mol: float
    density_g_cm3: float = 1.0


# Populated in Phase 1 from src/chemlab/simulation/cantera_engine.py
THERMO_DATABASE: dict[str, ThermodynamicState] = {}

__all__ = ["ThermodynamicState", "THERMO_DATABASE"]