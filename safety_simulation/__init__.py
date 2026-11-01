"""
Chemical Safety & Hazard Simulation Package
GHS Classification, Fume Hood Aerodynamics, Thermal Runaway Dynamics,
Neutralization Drills, Emergency Eyewash & Safety Shower Management.
"""

from .ghs import (
    GHSClass,
    GHSPictogram,
    SignalWord,
    StorageGroup,
    ChemicalProfile,
    CHEMICAL_DATABASE,
    check_chemical_compatibility,
    IncompatibilityResult,
    get_chemical_sds
)

from .fume_hood import (
    FumeHoodSimulation,
    FumeHoodMode,
    FumeHoodAlarmState,
    FumeHoodState,
    AirflowVector3D,
    StreamlineParticle
)

from .thermal_runaway import (
    ThermalVesselSimulation,
    VesselType,
    ReliefType,
    VesselState,
    StopperPopReport,
    RuptureReport,
    ShrapnelFragment
)

from .neutralization_drill import (
    AcidSpillNeutralizationDrill,
    EmergencyShowerEyewashDrill,
    NeutralizationState,
    DrillScoreReport,
    SpillLocation,
    StationType,
    ExposureType
)

from .safety_officer_engine import (
    ChemicalSafetyOfficerEngine,
    SafetyIncidentEvent
)

from .blender_bridge import BlenderSafetyVisualizer

__all__ = [
    "GHSClass",
    "GHSPictogram",
    "SignalWord",
    "StorageGroup",
    "ChemicalProfile",
    "CHEMICAL_DATABASE",
    "check_chemical_compatibility",
    "IncompatibilityResult",
    "get_chemical_sds",
    "FumeHoodSimulation",
    "FumeHoodMode",
    "FumeHoodAlarmState",
    "FumeHoodState",
    "AirflowVector3D",
    "StreamlineParticle",
    "ThermalVesselSimulation",
    "VesselType",
    "ReliefType",
    "VesselState",
    "StopperPopReport",
    "RuptureReport",
    "ShrapnelFragment",
    "AcidSpillNeutralizationDrill",
    "EmergencyShowerEyewashDrill",
    "NeutralizationState",
    "DrillScoreReport",
    "SpillLocation",
    "StationType",
    "ExposureType",
    "ChemicalSafetyOfficerEngine",
    "SafetyIncidentEvent",
    "BlenderSafetyVisualizer"
]
