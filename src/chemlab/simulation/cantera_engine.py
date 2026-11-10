"""
Legacy wrapper for ``src/chemlab/simulation/cantera_engine.py``.

Re-exports the authoritative thermodynamics engine from
``src/chemlab/chemistry/thermodynamics/engine.py`` so existing imports
``from chemlab.simulation.cantera_engine import ...`` keep working without
any change to callers.
"""

from chemlab.chemistry.thermodynamics.engine import (  # noqa: F401
    CanteraThermodynamicsEngine,
    ReactionThermodynamicsResult,
    THERMO_DATABASE,
    THERMO_ENGINE,
    ThermodynamicState,
    R_GAS,
)

__all__ = [
    "CanteraThermodynamicsEngine",
    "ReactionThermodynamicsResult",
    "THERMO_DATABASE",
    "THERMO_ENGINE",
    "ThermodynamicState",
    "R_GAS",
]
