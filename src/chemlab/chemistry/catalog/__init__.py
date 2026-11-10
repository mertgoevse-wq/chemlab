"""ChemLab Catalog — authoritative chemical reagent database.

Exports:
  * :class:`Reagent` — frozen dataclass with authentic physical/chemical properties
  * :data:`REAGENT_REGISTRY` — public registry mapping id → Reagent
  * :func:`get_reagent`, :func:`list_reagents`, :func:`search_by_formula`,
    :func:`search_by_category`, :func:`count_by_category`
  * :class:`ReagentCategory`, :class:`ParticleType`, :class:`SignalWord`,
    :class:`StorageGroup`, :class:`GHSHazard`

Consolidated from:
  * src/chemlab/simulation/reagents.py
  * simulation/catalog.py
  * safety_simulation/ghs.py
"""

from .reagents import (  # noqa: F401
    REAGENT_REGISTRY,
    GHSHazard,
    ParticleType,
    Reagent,
    ReagentCategory,
    SignalWord,
    StorageGroup,
    count_by_category,
    get_reagent,
    list_reagents,
    search_by_category,
    search_by_formula,
)

__all__ = [
    "REAGENT_REGISTRY",
    "GHSHazard",
    "ParticleType",
    "Reagent",
    "ReagentCategory",
    "SignalWord",
    "StorageGroup",
    "count_by_category",
    "get_reagent",
    "list_reagents",
    "search_by_category",
    "search_by_formula",
]
