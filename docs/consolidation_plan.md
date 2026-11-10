# ChemLab — Chemistry Module Consolidation Plan

**Document ID:** `DOC-CHEMLAB-CONSOLIDATION-001`  
**Version:** 1.0.0  
**Status:** Approved / Authoritative Plan  
**Date:** 2026-11-10  
**Target:** Consolidate 4 chemistry engines, 3 reagent databases, and 2 model modules into authoritative `src/chemlab/chemistry/` package while maintaining 100% backward compatibility (all 256 pytest tests must pass).

---

## 1. Executive Summary

The ChemLab codebase currently has significant structural fragmentation:

| Concern | Current Duplicates | Lines (approx.) | Test Files |
|---------|-------------------|-----------------|------------|
| **Chemistry Engines** | 4 modules | ~1,800 | `test_cantera_engine.py`, `test_reaction_solver.py`, `test_reaction_engine.py`, `test_free_sim.py` |
| **Reagent Databases** | 3 modules | ~3,200 | `test_reagents.py`, `test_ghs.py`, `test_free_sim.py` |
| **Data Models** | 2 modules | ~600 | `test_models.py` |

**Goal:** Single authoritative `src/chemlab/chemistry/` package per `ARCHITECTURE.md §3.2` with thin wrappers preserving all existing import paths. Zero functional code changes in Phase 1 — only structural reorganization and delegation.

---

## 2. Target Structure (per ARCHITECTURE.md §3.2)

```
src/chemlab/chemistry/
├── __init__.py                 # Public API exports, version
├── thermodynamics/
│   ├── __init__.py
│   ├── database.py             # NIST/CRC standard properties (ΔH°f, S°, Cp, MW, ρ)
│   └── engine.py               # Hess enthalpy, entropy, Gibbs, van 't Hoff, titration
├── kinetics/
│   ├── __init__.py
│   ├── arrhenius.py            # Arrhenius rate constants, temperature acceleration
│   ├── solver.py               # Stiff ODE numerical integration & concentration profiles
│   └── side_reactions.py       # Non-ideal side-products, addition-order hazards, tarring
├── safety/
│   ├── __init__.py
│   ├── ghs.py                  # GHS hazard pictograms, H/P statements, exposure limits
│   ├── fume_hood.py            # ANSI/AIHA Z9.5 face velocity & aerodynamic containment
│   └── thermal_runaway.py      # Semenov thermal explosion, Antoine VP, stopper pop
├── cheminformatics/
│   ├── __init__.py
│   └── rdkit_bridge.py         # SMILES to 3D conformer, UFF minimization, Lipinski
└── catalog/
    ├── __init__.py
    └── reagents.py             # Consolidated registry of 200+ chemical reagents
```

---

## 3. Module-to-Module Consolidation Mapping

### 3.1 Chemistry Engines — 4 → 3 Target Modules

| Source Module | Target Module | Functions/Classes Moved | Notes |
|---------------|---------------|-------------------------|-------|
| `chemlab_core/chemistry/reaction_engine.py` | `chemistry/kinetics/solver.py` | `BriggsRauscherOscillator`, `lerp_color`, `COLOR_CLEAR/AMBER/DEEP_BLUE` | Analytical oscillator → kinetics solver |
| `src/chemlab/simulation/cantera_engine.py` | `chemistry/thermodynamics/engine.py` | `CanteraThermodynamicsEngine`, `ThermodynamicState`, `ReactionThermodynamicsResult`, `THERMO_DATABASE`, `THERMO_ENGINE` | **Authoritative thermodynamics** — NIST constants preserved verbatim |
| `src/chemlab/simulation/cantera_engine.py` | `chemistry/thermodynamics/database.py` | `THERMO_DATABASE` (dict) | Split out for clarity |
| `src/chemlab/simulation/reaction_solver.py` | `chemistry/kinetics/solver.py` | `mix_liquids()`, `step_simulation()`, `_classify_reaction_type()`, `MIXING_KW`, `NEUTRALIZATION_KW`, `OBSCILLATOR_KW`, `CATALYST_MULTIPLIER` | **Authoritative kinetics solver** — LiquidMixture state machine |
| `src/chemlab/simulation/side_reactions.py` | `chemistry/kinetics/side_reactions.py` | `SideReactionAnalyzer`, `detect_addition_order_hazard()`, `analyze_aspirin_synthesis()`, `analyze_paracetamol_synthesis()`, `analyze_acetanilide_synthesis()` | Non-ideal impurity modeling |
| `simulation/consequence.py` | `chemistry/kinetics/solver.py` | `ConsequenceEngine`, `ConsequenceResult`, `ConsequenceType`, `ReactionEffect`, `VesselEnvironment`, `OscillationCycle` | Free-sim consequence matrix → unified solver |
| `simulation/free_sim_engine.py` | `chemistry/kinetics/solver.py` (facade only) | `FreeSimulationEngine`, `ActiveExperimentState` | Thin facade delegating to catalog + solver |
| `simulation/time_controller.py` | `chemistry/kinetics/solver.py` (or keep separate) | `TimeController`, `TimeScale` | Utility, not chemistry-specific — evaluate in Phase 3 |
| `simulation/experiment_book.py` | **NOT MOVED** — gameplay layer | `ExperimentBook`, `Recipe`, `ReagentAddition`, `SnapshotPhoto` | Belongs in `gameplay/` per ARCHITECTURE.md |

### 3.2 Reagent Databases — 3 → 1 Target Module

| Source Module | Target Module | Data Moved | Entry Count |
|---------------|---------------|------------|-------------|
| `src/chemlab/simulation/reagents.py` | `chemistry/catalog/reagents.py` | `Reagent` dataclass, `ReagentCategory`, `ParticleType`, `SignalWord`, `StorageGroup`, `GHSHazard`, `_REAGENTS` dict, `REAGENT_REGISTRY`, `get_reagent()`, `list_reagents()`, `search_by_formula()`, `search_by_category()`, `count_by_category()` | ~200 (authoritative) |
| `simulation/catalog.py` | `chemistry/catalog/reagents.py` | Merge unique entries: `ReagentCategory` enum values, `GHSPictogram` enum, `Reagent` dataclass fields (`melting_point_c`, `boiling_point_c`, `pka`, `solubility_g_per_100ml_water`, `common_uses`, `storage_note`, `hazard_statements`), `_REAGENTS` list (100+), `ReagentCatalog` class | ~100 unique entries not in src/chemlab |
| `safety_simulation/ghs.py` | `chemistry/safety/ghs.py` + `chemistry/catalog/reagents.py` | `ChemicalProfile` → merge into `Reagent.ghs_hazards`; `CHEMICAL_DATABASE` (25) → merge unique; `check_chemical_compatibility()` → `chemistry/safety/ghs.py`; `get_chemical_sds()` → `chemistry/safety/ghs.py` | 25 profiles |

**Merge Strategy for Reagent Catalog:**
- **Authoritative base:** `src/chemlab/simulation/reagents.py` (already has 200+ entries with full GHS, CAS, particle types, colors)
- **Add missing from `simulation/catalog.py`:** ~80 unique reagents (transition metal salts, indicators, oxidizers, organic solvents not in src/chemlab)
- **Add missing from `safety_simulation/ghs.py`:** 3 unique profiles (chlorine, copper_sulfate duplicate check, silver_nitrate duplicate check)
- **Unify GHS representation:** `GHSHazard` dataclass (from src/chemlab) replaces both `GHSPictogram` enum (simulation/catalog) and `GHSClass/GHSPictogram/SignalWord` enums (safety_simulation/ghs.py)
- **Single `REAGENT_REGISTRY` dict** with case-insensitive lookup, aliases preserved

### 3.3 Data Models — 2 → Split by Domain

| Source Module | Target Location | Classes Moved |
|---------------|-----------------|---------------|
| `chemlab_core/models.py` | `chemistry/thermodynamics/engine.py` (reaction models) | `OscillatingPhase`, `ReactionState` |
| `chemlab_core/models.py` | `src/chemlab/cv/models.py` (vision models) | `GestureType`, `Handedness`, `NormalizedLandmark`, `HandLandmarkFrame`, `GestureEvent` |
| `chemlab_core/models.py` | `src/chemlab/simulation/ipc_bridge_server.py` (IPC models) | `IPCRequestType`, `IPCRequest`, `IPCStatus`, `IPCResponse` |
| `chemlab_core/models.py` | `src/chemlab/desktop/main_window.py` or new `blender/` | `SceneCommandType`, `SceneCommand` |
| `src/chemlab/models.py` | `chemistry/catalog/reagents.py` | `ChemicalReagent` → merged into `Reagent` |
| `src/chemlab/models.py` | `chemistry/kinetics/solver.py` | `LiquidMixture`, `ReactionType`, `GHSHazard` |
| `src/chemlab/models.py` | `src/chemlab/cv/models.py` | `HandLandmark`, `HandTrackingFrame`, `ApparatusState` |

---

## 4. Wrapper Modules — Backward Compatibility Layer

**CRITICAL RULE:** No old import path may break. Every legacy module becomes a thin wrapper that re-exports from the new authoritative location.

### 4.1 `chemlab_core/chemistry/reaction_engine.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.kinetics.solver
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

# Re-export all public symbols from the new authoritative location
from src.chemlab.chemistry.kinetics.solver import (
    BriggsRauscherOscillator,
    lerp_color,
    COLOR_CLEAR,
    COLOR_AMBER,
    COLOR_DEEP_BLUE,
)

__all__ = [
    "BriggsRauscherOscillator",
    "lerp_color",
    "COLOR_CLEAR",
    "COLOR_AMBER",
    "COLOR_DEEP_BLUE",
]

# Type-checking shim for mypy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.chemlab.chemistry.kinetics.solver import (
        BriggsRauscherOscillator as _BriggsRauscherOscillator,
        lerp_color as _lerp_color,
    )
```

### 4.2 `src/chemlab/simulation/cantera_engine.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.thermodynamics
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.thermodynamics.database import THERMO_DATABASE
from src.chemlab.chemistry.thermodynamics.engine import (
    CanteraThermodynamicsEngine,
    ThermodynamicState,
    ReactionThermodynamicsResult,
    THERMO_ENGINE,
)

__all__ = [
    "CanteraThermodynamicsEngine",
    "ThermodynamicState",
    "ReactionThermodynamicsResult",
    "THERMO_DATABASE",
    "THERMO_ENGINE",
    "R_GAS",
]

# Re-export module-level constant
from src.chemlab.chemistry.thermodynamics.engine import R_GAS
```

### 4.3 `src/chemlab/simulation/reaction_solver.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.kinetics.solver
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.kinetics.solver import (
    mix_liquids,
    step_simulation,
    ReactionType,
    MIXING_KW,
    NEUTRALIZATION_KW,
    OSCILLATOR_KW,
    CATALYST_MULTIPLIER,
)

__all__ = [
    "mix_liquids",
    "step_simulation",
    "ReactionType",
    "MIXING_KW",
    "NEUTRALIZATION_KW",
    "OSCILLATOR_KW",
    "CATALYST_MULTIPLIER",
]
```

### 4.4 `src/chemlab/simulation/side_reactions.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.kinetics.side_reactions
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.kinetics.side_reactions import (
    SideReactionAnalyzer,
    detect_addition_order_hazard,
    analyze_aspirin_synthesis,
    analyze_paracetamol_synthesis,
    analyze_acetanilide_synthesis,
)

__all__ = [
    "SideReactionAnalyzer",
    "detect_addition_order_hazard",
    "analyze_aspirin_synthesis",
    "analyze_paracetamol_synthesis",
    "analyze_acetanilide_synthesis",
]
```

### 4.5 `simulation/catalog.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.catalog.reagents
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.catalog.reagents import (
    Reagent,
    ReagentCategory,
    GHSPictogram,  # Kept as alias for compatibility
    ReagentCatalog,
)

__all__ = [
    "Reagent",
    "ReagentCategory",
    "GHSPictogram",
    "ReagentCatalog",
]

# Compatibility: GHSPictogram enum values must match old expectations
# The new module provides StrEnum with same values
```

### 4.6 `simulation/consequence.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.kinetics.solver
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.kinetics.solver import (
    ConsequenceEngine,
    ConsequenceResult,
    ConsequenceType,
    ReactionEffect,
    VesselEnvironment,
    OscillationCycle,
)

__all__ = [
    "ConsequenceEngine",
    "ConsequenceResult",
    "ConsequenceType",
    "ReactionEffect",
    "VesselEnvironment",
    "OscillationCycle",
]
```

### 4.7 `simulation/free_sim_engine.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.kinetics.solver (facade)
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

from src.chemlab.chemistry.kinetics.solver import (
    FreeSimulationEngine,
    ActiveExperimentState,
)

__all__ = [
    "FreeSimulationEngine",
    "ActiveExperimentState",
]
```

### 4.8 `safety_simulation/ghs.py` → Wrapper

```python
"""
LEGACY WRAPPER — Delegates to src.chemlab.chemistry.safety.ghs AND catalog
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

# Safety functions
from src.chemlab.chemistry.safety.ghs import (
    check_chemical_compatibility,
    get_chemical_sds,
    IncompatibilityResult,
    GHSClass,
    GHSPictogram,
    SignalWord,
    StorageGroup,
)

# ChemicalProfile is now merged into catalog.Reagent — provide compatibility shim
from src.chemlab.chemistry.catalog.reagents import Reagent as ChemicalProfile
from src.chemlab.chemistry.catalog.reagents import REAGENT_REGISTRY as CHEMICAL_DATABASE

__all__ = [
    "check_chemical_compatibility",
    "get_chemical_sds",
    "IncompatibilityResult",
    "ChemicalProfile",
    "CHEMICAL_DATABASE",
    "GHSClass",
    "GHSPictogram",
    "SignalWord",
    "StorageGroup",
]
```

### 4.9 `chemlab_core/models.py` → Split Wrappers

**File stays but becomes minimal re-exports:**

```python
"""
LEGACY WRAPPER — Split re-exports to domain-specific modules
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

# Reaction/oscillation models → thermodynamics
from src.chemlab.chemistry.thermodynamics.engine import (
    OscillatingPhase,
    ReactionState,
)

# Vision models → cv
from src.chemlab.cv.models import (
    GestureType,
    Handedness,
    NormalizedLandmark,
    HandLandmarkFrame,
    GestureEvent,
)

# IPC models → simulation/ipc_bridge_server
from src.chemlab.simulation.ipc_bridge_server import (
    IPCRequestType,
    IPCRequest,
    IPCStatus,
    IPCResponse,
)

# Blender scene commands → desktop or new blender module
from src.chemlab.desktop.main_window import (
    SceneCommandType,
    SceneCommand,
)

__all__ = [
    "OscillatingPhase",
    "ReactionState",
    "GestureType",
    "Handedness",
    "NormalizedLandmark",
    "HandLandmarkFrame",
    "GestureEvent",
    "IPCRequestType",
    "IPCRequest",
    "IPCStatus",
    "IPCResponse",
    "SceneCommandType",
    "SceneCommand",
]
```

### 4.10 `src/chemlab/models.py` → Split Wrappers

```python
"""
LEGACY WRAPPER — Split re-exports to domain-specific modules
DO NOT ADD NEW CODE HERE. All new development goes to the authoritative module.
"""
from __future__ import annotations

# Chemical models → catalog
from src.chemlab.chemistry.catalog.reagents import (
    Reagent as ChemicalReagent,
    ReagentCategory,
    GHSHazard,  # Re-export from catalog
)

# Kinetics models → kinetics/solver
from src.chemlab.chemistry.kinetics.solver import (
    LiquidMixture,
    ReactionType,
)

# Vision/tracking models → cv
from src.chemlab.cv.models import (
    HandLandmark,
    HandTrackingFrame,
    ApparatusState,
)

__all__ = [
    "ChemicalReagent",
    "ReagentCategory",
    "GHSHazard",
    "LiquidMixture",
    "ReactionType",
    "HandLandmark",
    "HandTrackingFrame",
    "ApparatusState",
]
```

---

## 5. Test Strategy — Zero Test Changes Required

### 5.1 Core Principle

**No test file is modified, deleted, or renamed.** All 256 existing tests must continue to pass without any changes to test code. This is achieved by:

1. **Preserving all import paths** via wrapper modules (Section 4)
2. **Preserving all public APIs** (classes, functions, constants, enums) with identical signatures
3. **Preserving all module-level constants** (`THERMO_ENGINE`, `REAGENT_REGISTRY`, `CHEMICAL_DATABASE`, etc.)

### 5.2 Test File Coverage Map

| Test File | Tests | Imports From | Protected By Wrapper |
|-----------|-------|--------------|---------------------|
| `test_cantera_engine.py` | 8 | `chemlab.simulation.cantera_engine` | ✅ Wrapper 4.2 |
| `test_reaction_solver.py` | 4 | `chemlab.models`, `chemlab.simulation.reaction_solver`, `chemlab.simulation.reagents` | ✅ Wrappers 4.3, 4.9, 4.10 |
| `test_reagents.py` | 10 | `chemlab.simulation.reagents` | ✅ Catalog is authoritative |
| `test_free_sim.py` | 20+ | `simulation.catalog`, `simulation.consequence`, `simulation.free_sim_engine`, `simulation.experiment_book`, `simulation.time_controller` | ✅ Wrappers 4.5, 4.6, 4.7 |
| `test_reaction_engine.py` | 5+ | `chemlab_core.chemistry.reaction_engine` | ✅ Wrapper 4.1 |
| `test_ghs.py` | 10+ | `safety_simulation.ghs` | ✅ Wrapper 4.8 |
| `test_models.py` | 10+ | `chemlab_core.models`, `chemlab.models` | ✅ Wrappers 4.9, 4.10 |
| `test_side_reactions.py` | 5+ | `chemlab.simulation.side_reactions` | ✅ Wrapper 4.4 |
| `test_thermal_runaway.py` | 5+ | `safety_simulation.thermal_runaway` | ✅ (stays in safety/) |
| `test_fume_hood.py` | 5+ | `safety_simulation.fume_hood` | ✅ (stays in safety/) |

### 5.3 Validation Protocol

```bash
# Phase 1 validation (after each consolidation step):
cd C:\Users\Win11 Pro\Desktop\chemlab
.venv/Scripts/python.exe -m pytest tests/test_cantera_engine.py -v
.venv/Scripts/python.exe -m pytest tests/test_reaction_solver.py -v
.venv/Scripts/python.exe -m pytest tests/test_reagents.py -v
.venv/Scripts/python.exe -m pytest tests/test_free_sim.py -v
.venv/Scripts/python.exe -m pytest tests/test_reaction_engine.py -v
.venv/Scripts/python.exe -m pytest tests/test_ghs.py -v
.venv/Scripts/python.exe -m pytest tests/test_models.py -v
.venv/Scripts/python.exe -m pytest tests/test_side_reactions.py -v

# Full suite validation (must pass 256 tests):
.venv/Scripts/python.exe -m pytest tests/ -v --tb=short
```

### 5.4 Type-Check Validation

```bash
.venv/Scripts/python.exe -m mypy src/chemlab --ignore-missing-imports --follow-imports=skip --no-site-packages
```

Must produce ≤13 errors (current baseline) — no new errors introduced.

---

## 6. Phased Implementation Order

### Phase 1: Infrastructure & Thermodynamics (Week 1)

**Deliverables:**
- [ ] Create `src/chemlab/chemistry/` directory structure with `__init__.py` files
- [ ] Create `thermodynamics/database.py` — move `THERMO_DATABASE` from `cantera_engine.py`
- [ ] Create `thermodynamics/engine.py` — move `CanteraThermodynamicsEngine`, `ThermodynamicState`, `ReactionThermodynamicsResult`, `THERMO_ENGINE`, `R_GAS`
- [ ] Create wrapper: `src/chemlab/simulation/cantera_engine.py` (Section 4.2)
- [ ] Run `test_cantera_engine.py` — **must pass 8/8**

**Risk:** Low — pure data/constants move, no logic changes.

### Phase 2: Reagent Catalog Consolidation (Week 1-2)

**Deliverables:**
- [ ] Create `catalog/reagents.py` — merge three databases into single authoritative registry
  - Base: `src/chemlab/simulation/reagents.py` (~200 entries)
  - Add unique from `simulation/catalog.py` (~80 entries)
  - Add unique from `safety_simulation/ghs.py` (~3 entries)
  - Unify GHS to single `GHSHazard` dataclass
- [ ] Create wrappers:
  - `src/chemlab/simulation/reagents.py` → re-exports from catalog (already authoritative, minimal)
  - `simulation/catalog.py` (Section 4.5)
  - `safety_simulation/ghs.py` (Section 4.8)
- [ ] Run `test_reagents.py`, `test_free_sim.py::TestReagentCatalog`, `test_ghs.py` — **all must pass**

**Risk:** Medium — large data merge, must ensure no duplicate IDs, CAS numbers consistent.

### Phase 3: Kinetics & Solver Consolidation (Week 2)

**Deliverables:**
- [ ] Create `kinetics/solver.py` — consolidate:
  - `reaction_solver.py`: `mix_liquids`, `step_simulation`, `ReactionType`, constants
  - `reaction_engine.py`: `BriggsRauscherOscillator`, color constants
  - `consequence.py`: `ConsequenceEngine`, `ConsequenceResult`, enums, `VesselEnvironment`
  - `free_sim_engine.py`: `FreeSimulationEngine`, `ActiveExperimentState` (facade)
- [ ] Create `kinetics/side_reactions.py` — move `side_reactions.py` logic
- [ ] Create `kinetics/arrhenius.py` — extract Arrhenius math from thermodynamics engine
- [ ] Create wrappers (Sections 4.1, 4.3, 4.4, 4.6, 4.7)
- [ ] Run `test_reaction_solver.py`, `test_reaction_engine.py`, `test_free_sim.py::TestConsequenceEngine`, `test_free_sim.py::TestFreeSimulationEngine`, `test_side_reactions.py` — **all must pass**

**Risk:** Medium — logic consolidation, but well-tested.

### Phase 4: Safety Module Consolidation (Week 2-3)

**Deliverables:**
- [ ] Create `safety/ghs.py` — `check_chemical_compatibility`, `get_chemical_sds`, enums
- [ ] Move `safety_simulation/fume_hood.py` → `safety/fume_hood.py` (no changes)
- [ ] Move `safety_simulation/thermal_runaway.py` → `safety/thermal_runaway.py` (no changes)
- [ ] Move `safety_simulation/neutralization_drill.py` → `safety/neutralization_drill.py` (no changes)
- [ ] Move `safety_simulation/safety_officer_engine.py` → `safety/safety_officer_engine.py` (no changes)
- [ ] Create wrapper `safety_simulation/ghs.py` (Section 4.8)
- [ ] Run `test_ghs.py`, `test_fume_hood.py`, `test_thermal_runaway.py`, `test_neutralization_drill.py`, `test_safety_officer_engine.py` — **all must pass**

**Risk:** Low — mostly file moves, `ghs.py` already wrapped.

### Phase 5: Model Split & Wrapper Completion (Week 3)

**Deliverables:**
- [ ] Move vision models from `chemlab_core/models.py` → `src/chemlab/cv/models.py`
- [ ] Move IPC models from `chemlab_core/models.py` → `src/chemlab/simulation/ipc_bridge_server.py`
- [ ] Move Blender models from `chemlab_core/models.py` → `src/chemlab/desktop/main_window.py` (or new `blender/`)
- [ ] Update `chemlab_core/models.py` wrapper (Section 4.9)
- [ ] Update `src/chemlab/models.py` wrapper (Section 4.10)
- [ ] Run `test_models.py`, `test_vision.py`, `test_hand_tracker.py`, `test_holistic_tracker.py`, `test_ipc_bridge_server.py` — **all must pass**

**Risk:** Medium — cross-cutting, but models are pure dataclasses.

### Phase 6: Packaging & pyproject.toml Fix (Week 3)

**Deliverables:**
- [ ] Update `pyproject.toml` `[tool.setuptools.packages.find]` to properly include all packages:
  ```toml
  [tool.setuptools.packages.find]
  where = ["src"]
  include = ["chemlab*"]
  ```
  (The new structure puts everything under `src/chemlab/`)
- [ ] Verify `pip install -e .` produces wheel with all modules
- [ ] Run full test suite: **256 tests must pass**
- [ ] Run mypy: **≤13 errors (baseline)**
- [ ] Run ruff: **no new errors**

**Risk:** Low — packaging only.

---

## 7. Rollback Plan

### 7.1 Per-Phase Rollback Triggers

| Phase | Rollback Trigger | Rollback Action |
|-------|------------------|-----------------|
| 1 | `test_cantera_engine.py` fails | `git restore src/chemlab/simulation/cantera_engine.py chemlab_core/chemistry/reaction_engine.py` |
| 2 | Any reagent test fails | `git restore src/chemlab/simulation/reagents.py simulation/catalog.py safety_simulation/ghs.py` |
| 3 | Any solver/consequence test fails | `git restore src/chemlab/simulation/reaction_solver.py chemlab_core/chemistry/reaction_engine.py simulation/consequence.py simulation/free_sim_engine.py src/chemlab/simulation/side_reactions.py` |
| 4 | Any safety test fails | `git restore safety_simulation/` |
| 5 | Any model/vision/IPC test fails | `git restore chemlab_core/models.py src/chemlab/models.py src/chemlab/cv/models.py src/chemlab/simulation/ipc_bridge_server.py` |
| 6 | Packaging broken | `git restore pyproject.toml` |

### 7.2 Full Rollback Procedure

```bash
# Nuclear option — restore entire repo to pre-consolidation state
cd C:\Users\Win11 Pro\Desktop\chemlab
git stash  # or git reset --hard HEAD~{n} where n = commits in this plan
.venv/Scripts/python.exe -m pytest tests/ -v  # Verify 256 tests pass
```

### 7.3 Branch Strategy

All work happens on `feature/chemistry-consolidation` branch. `main` remains pristine. Merge only after **all 256 tests pass + mypy baseline + ruff clean**.

---

## 8. Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Authoritative thermodynamics = `cantera_engine.py`** | Only module with real NIST/CRC constants, 8 passing tests, used by Godot IPC bridge |
| **Authoritative kinetics = `reaction_solver.py`** | Only module with `LiquidMixture` state machine, `mix_liquids`/`step_simulation`, 4 passing tests |
| **Authoritative catalog = `src/chemlab/simulation/reagents.py`** | Most complete (200+ entries), modern `Reagent` dataclass with particle types, CAS, full GHS |
| **GHS unification = `GHSHazard` dataclass** | Single source replaces 3 enum systems; carries code, text, pictogram, signal word, category |
| **Wrapper pattern (not deletion)** | Zero-breaking-changes guarantee; all 256 tests untouched; rollback is `git restore` |
| **Models split by domain** | `chemlab_core/models.py` and `src/chemlab/models.py` are domain-mixed; split follows ARCHITECTURE.md boundaries |
| **`experiment_book.py` stays in `simulation/`** | It's gameplay persistence, not chemistry — ARCHITECTURE.md puts it in `gameplay/` (future move) |
| **`time_controller.py` stays in `simulation/`** | Utility class, not chemistry-specific; evaluate in future refactor |

---

## 9. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Test pass rate** | 256/256 | `pytest tests/` |
| **Type-check errors** | ≤13 (baseline) | `mypy src/chemlab` |
| **Lint errors** | 0 new | `ruff check` |
| **Import compatibility** | 100% | All legacy import paths work |
| **Packaging** | Clean wheel | `pip install -e . && python -c "import chemlab.chemistry; print('OK')"` |
| **No functional changes** | Verified | `git diff --stat` shows only moves + wrappers |

---

## 10. Appendix: Complete Wrapper Code Snippets

All wrapper code snippets are provided in **Section 4** above. Each wrapper:

1. Contains **only re-exports** — zero logic
2. Preserves **exact `__all__`** from original module
3. Includes **TYPE_CHECKING block** for mypy
4. Has **header comment** marking as legacy wrapper
5. Is **< 50 lines** — trivial to review and audit

---

**End of Consolidation Plan**

*Next step: Begin Phase 1 implementation. Create directory structure and thermodynamics modules.*