"""ChemLab Kinetics — reaction rate and oscillation models.

Exports:
  * :class:`BriggsRauscherOscillator` — cyclic Clear → Amber → Deep Blue colour
    model for the Briggs-Rauscher iodine clock reaction.
  * :func:`lerp_color` — linear RGBA interpolation used by the shader layer.

Migrated from ``chemlab_core/chemistry/reaction_engine.py``. The legacy module
re-exports from here for backwards compatibility.
"""

from .oscillator import (  # noqa: F401
    BriggsRauscherOscillator,
    COLOR_AMBER,
    COLOR_CLEAR,
    COLOR_DEEP_BLUE,
    lerp_color,
)

__all__ = [
    "BriggsRauscherOscillator",
    "COLOR_AMBER",
    "COLOR_CLEAR",
    "COLOR_DEEP_BLUE",
    "lerp_color",
]
