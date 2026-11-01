"""
ChemLab Simulation Core Package
Free Simulation Mode:
- Reagent catalog (>100 chemical entries with GHS pictograms)
- Consequence matrices (thermodynamics, precipitates, gas release, fume hood containment)
- Simulation time controller (0.0x pause, 0.5x slow-mo, up to 50x time-lapse)
- Experiment Book & Recipe JSON Export
"""

from simulation.catalog import GHSPictogram, Reagent, ReagentCatalog, ReagentCategory
from simulation.consequence import (
    ConsequenceEngine,
    ConsequenceResult,
    ConsequenceType,
    ReactionEffect,
    VesselEnvironment,
)
from simulation.experiment_book import (
    ExperimentBook,
    ReagentAddition,
    Recipe,
    SnapshotPhoto,
)
from simulation.free_sim_engine import FreeSimulationEngine
from simulation.time_controller import TimeController, TimeScale

__all__ = [
    "ReagentCatalog",
    "Reagent",
    "ReagentCategory",
    "GHSPictogram",
    "ConsequenceEngine",
    "ConsequenceType",
    "ReactionEffect",
    "VesselEnvironment",
    "ConsequenceResult",
    "TimeController",
    "TimeScale",
    "ExperimentBook",
    "Recipe",
    "ReagentAddition",
    "SnapshotPhoto",
    "FreeSimulationEngine",
]
