"""
Legacy wrapper for ``chemlab_core/chemistry/reaction_engine.py``.

Re-exports both the authoritative thermodynamics engine from
``src/chemlab/chemistry/thermodynamics/engine.py`` and the Briggs-Rauscher
oscillator from ``src/chemlab/chemistry/kinetics/oscillator.py`` so existing
imports ``from chemlab_core.chemistry.reaction_engine import ...`` keep working
without any change to callers.
"""

from chemlab.chemistry.kinetics.oscillator import (  # noqa: F401
    BriggsRauscherOscillator,
    COLOR_AMBER,
    COLOR_CLEAR,
    COLOR_DEEP_BLUE,
    lerp_color,
)
from chemlab.chemistry.thermodynamics.engine import (  # noqa: F401
    CanteraThermodynamicsEngine,
    ReactionThermodynamicsResult,
    THERMO_DATABASE,
    THERMO_ENGINE,
    ThermodynamicState,
    R_GAS,
)

__all__ = [
    "BriggsRauscherOscillator",
    "COLOR_AMBER",
    "COLOR_CLEAR",
    "COLOR_DEEP_BLUE",
    "lerp_color",
    "CanteraThermodynamicsEngine",
    "ReactionThermodynamicsResult",
    "THERMO_DATABASE",
    "THERMO_ENGINE",
    "ThermodynamicState",
    "R_GAS",
]
