"""ChemLab Thermodynamics — NIST/CRC-based calculation core.

Exports the authoritative :class:`CanteraThermodynamicsEngine`, the shared
:data:`THERMO_ENGINE` singleton, :class:`ThermodynamicState`,
:class:`ReactionThermodynamicsResult`, and :data:`THERMO_DATABASE`.

Migrated from ``src/chemlab/simulation/cantera_engine.py`` and
``chemlab_core/chemistry/reaction_engine.py``. Both legacy modules re-export
from this package for backwards compatibility.
"""

from .engine import (  # noqa: F401
    R_GAS,
    THERMO_DATABASE,
    THERMO_ENGINE,
    CanteraThermodynamicsEngine,
    ReactionThermodynamicsResult,
    ThermodynamicState,
)

__all__ = [
    "CanteraThermodynamicsEngine",
    "ReactionThermodynamicsResult",
    "THERMO_DATABASE",
    "THERMO_ENGINE",
    "ThermodynamicState",
    "R_GAS",
]
