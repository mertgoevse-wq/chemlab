"""
ChemLab Safety Module
=====================

Authoritative laboratory safety calculations:
- GHS hazard classification, pictograms, H/P statements, compatibility matrix
- Fume hood aerodynamics (ANSI/AIHA Z9.5 face velocity, containment)
- Thermal runaway / Semenov explosion criterion, Antoine vapor pressure, stopper pop
- Neutralization drill scenarios and safety officer engine

Public API:
- ghs: check_chemical_compatibility, get_chemical_sds, GHSHazard, enums
- fume_hood: FumeHoodModel, calculate_face_velocity
- thermal_runaway: SemenovModel, calculate_adiabatic_runaway
- neutralization_drill: NeutralizationDrill
- safety_officer_engine: SafetyOfficerEngine
"""

from __future__ import annotations

__all__ = [
    "ghs",
    "fume_hood",
    "thermal_runaway",
    "neutralization_drill",
    "safety_officer_engine",
]