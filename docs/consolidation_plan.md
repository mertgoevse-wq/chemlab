# ChemLab Chemistry Simulation Consolidation Plan

**Project:** Athanor Ascension (ChemLab)
**Date:** 2026-11-05
**Goal:** Merge 4 chemistry engines, 3 reagent databases, and 2 model modules into one authoritative `chemistry/` module at `src/chemlab/chemistry/`

---

## Executive Summary

The ChemLab codebase currently has scattered chemistry functionality across multiple modules with overlapping reagent definitions, duplicate simulation logic, and inconsistent data models. This plan consolidates everything into a single authoritative `chemistry/` module foundation, with clear ownership per concern. The consolidation is Phase 1 of the architecture plan (ARCHITECTURE.md §3.2).

---

## 1. File-by-File Merge Plan

### Legend:
- **A) Authoritative source of truth** — Keep as-is; becomes the single source for this concern
- **B) Subsumed into another** — Functionality merged into another module; original file deprecated
- **C) Deprecated-and-removable** — Can be removed after consolidation; no unique value
- **D) Needs refactor** — Must be modified and relocated; keeps its core logic but changes ownership

---

### Reagent Databases (3 → 1)

| Source File | Classification | Reasoning |
|---|---|---|
| `src/chemlab/simulation/reagents.py` | **A) Authoritative source of truth** | Already the consolidated registry with >200 substances. Has the most complete `Reagent` dataclass with all properties (molar mass, density, CAS, pKa, GHS hazards, storage group, particle type, color). Provides all lookup helpers (`get_reagent`, `list_reagents`, `search_by_formula`, `search_by_category`, `count_by_category`). **This becomes the single reagent registry for the entire project.** |
| `src/chemlab/simulation/cantera_engine.py` | **D) Needs refactor** | Contains `THERMO_DATABASE` with ~80 species that overlap significantly with `reagents.py`. The thermodynamic calculation engine itself is valuable and should be preserved, but its data source must switch to `reagents.py`. Will be refactored to import reagent data from the consolidated registry and relocated to `chemistry/thermodynamics/engine.py`. |
| `src/chemlab/simulation/side_reactions.py` | **B) Subsumed into chemistry/ module** | Side reaction analyzer (aspirin, paracetamol, acetanilide evaluation). Its impurity/severity logic is valuable but should be integrated into `chemistry/safety/` or `chemistry/kinetics/` as a submodule. After consolidation, this file's functions will be importable from the new module. |

---

### Chemistry Engines (4 → consolidated)

| Source File | Classification | Reasoning |
|---|---|---|
| `src/chemlab/simulation/cantera_engine.py` | **D) Needs refactor** (see above) | Its thermodynamic engine will be refactored to use `reagents.py` data and moved to `chemistry/thermodynamics/engine.py`. The Cantera-backed rigorous calculations become the authoritative thermodynamic engine for the new module. |
| `src/chemlab/simulation/rdkit_engine.py` | **B) Subsumed into chemistry/ module** | 3D conformer generation and molecular property calculation from SMILES. Core functionality (SMILES→3D, UFF minimization, property descriptors) is unique and should be preserved. Will be integrated into `chemistry/cheminformatics/rdkit_bridge.py` as the cheminformatics submodule. |
| `src/chemlab/simulation/reaction_solver.py` | **B) Subsumed into chemistry/ module** | Core reaction state machine (`mix_liquids()`, `step_simulation()`, reaction classification). Essential simulation logic that must be in the chemistry core. Will be integrated into `chemistry/simulation/solver.py`, refactored to import reagent data from `reagents.py` instead of hardcoded reagent names/lookups. |
| `src/chemlab/simulation/precursor_synthesis.py` | **B) Subsumed into chemistry/ module** | 5 precursor synthetic pathways (benzaldehyde, salicylic acid, nitroethane, 4-aminophenol, indole). Pathway data should be absorbed into the consolidated reagent catalog. After consolidation, precursor pathways will reference `reagents.py` for reagent definitions and be stored in `chemistry/catalog/`. |

---

### Model Modules (2 sets → consolidated)

| Source File | Classification | Reasoning |
|---|---|---|
| `src/chemlab/skills/skill_types.py` | **A) Authoritative source of truth** (skills model) | Defines the 5 skill disciplines (SAFETY, ANALYTICAL, THERMODYNAMICS, PREPARATIVE, COMPUTATIONAL) with all metadata: `SkillDefinition`, rank titles, apparatus/un reagent/ability unlocks per level. This is the single source for skill type definitions. |
| `src/chemlab/skills/milestones.py` | **A) Authoritative source of truth** (skills model) | Defines all 60+ milestones across 5 disciplines, levels 1–120. `Milestone` dataclass and `MILESTONES` list are the single source for progression unlocks. |
| `src/chemlab/skills/skill_manager.py` | **D) Needs refactor** | Runtime skill management state (XP, level, unlocked content). Core progression logic is valuable but must be refactored to reference the new `chemistry/` module for data rather than maintaining duplicate definitions. Will be relocated/updated to `skills/manager.py` with updated imports. |
| `src/chemlab/synthesis/guided_wizard.py` | **B) Subsumed into chemistry/ module** | Guided synthesis session manager (`GuidanceTier`, `WizardStepState`, `MeasurementInput`, `STAGE_REFERENCE_QUANTITIES`, `GuidedSynthesisSession`). The tier-based guidance logic is UI-facing; after consolidation, this will reference `chemistry/catalog/` protocols rather than maintaining its own reference quantities. |
| `src/chemlab/simulation/total_syntheses.py` | **B) Subsumed into chemistry/ module** | Total synthesis protocol registry (5 protocols: aspirin, paracetamol, caffeine, indigo, benzocaine). After consolidation, protocols will be stored in `chemistry/catalog/` with references to `reagents.py` for reagent definitions. The `SynthesisProtocol`, `SynthesisStage` dataclasses and `SynthesisRegistry` will be the authoritative protocol storage. |

---

## 2. Recommended Execution Order

### Phase 1: Foundation (Weeks 1–2)
1. **Create `src/chemlab/chemistry/` package structure** with `__init__.py`, subpackages: `thermodynamics/`, `kinetics/`, `cheminformatics/`, `safety/`, `catalog/`
2. **Consolidate reagent data**: `reagents.py` becomes the canonical registry. Add `REAGENT_REGISTRY` export from `chemistry/catalog/reagents.py` that re-exports from the existing file.
3. **Migrate `cantera_engine.py` THERMO_DATABASE** to reference `reagents.py` entries. Create `chemistry/thermodynamics/engine.py` with refactored thermodynamics engine that imports reagent data from the consolidated registry.
4. **Update all internal imports** to point to the new `chemistry/` module paths where applicable.

### Phase 2: Engine Integration (Weeks 3–4)
5. **Integrate `rdkit_engine.py`** into `chemistry/cheminformatics/rdkit_bridge.py`. Preserve `smiles_to_3d_molecule()` and property calculation logic. Update any references to use new module paths.
6. **Integrate `reaction_solver.py`** into `chemistry/simulation/solver.py`. Refactor `mix_liquids()` and `step_simulation()` to import reagent data from `reagents.py` instead of hardcoded lookups. Update `LiquidMixture` references if needed.
7. **Integrate `precursor_synthesis.py`** pathways into `chemistry/catalog/`. Convert `PrecursorPathway`/`ReactionStep` dataclasses to use `Reagent` from `reagents.py`. Update all reagent references to use the consolidated registry.

### Phase 3: Model Module Consolidation (Weeks 5–6)
8. **Consolidate `skills/` module**: `skill_types.py` and `milestones.py` remain as the authoritative skills model. Update `skill_manager.py` to import reagent/chemical data from `chemistry/` where needed (e.g., skill unlock reagents should reference `chemistry.catalog.reagents`).
9. **Update `guided_wizard.py`**: Replace `STAGE_REFERENCE_QUANTITIES` with references to `chemistry/catalog/protocols`. Update tier tolerance logic to use data from the consolidated chemistry core.
10. **Update `total_syntheses.py`**: Migrate the 5 synthesis protocols into `chemistry/catalog/`. Update `SynthesisProtocol`/`SynthesisStage` to reference reagent IDs from `reagents.py` instead of string names.

### Phase 4: Cleanup and Verification (Weeks 7–8)
11. **Run full test suite**: `pytest` must pass (256 tests green). Verify all imports resolve correctly.
12. **Deprecate old files**: Mark consolidated files as deprecated with `PendingDeprecationWarning` or remove after 2-week verification period. Update `.gitignore` for any build artifacts.
13. **Update all project imports**: Ensure every file that previously imported from the old scattered modules now imports from `chemistry/`.
14. **Document the new module**: Update `ARCHITECTURE.md` §3.2 to reflect the consolidated structure.

---

## 3. Key Findings: Duplicate Functionality & Conflicts

### Duplicate Reagent Definitions
- `cantera_engine.py` `THERMO_DATABASE` (~80 species) overlaps heavily with `reagents.py` `REAGENT_REGISTRY` (>200 species). Identical entries: `water`, `HCl`, `NaOH`, `sulfuric_acid`, `acetic_acid`, `ethanol`, `methanol`, `acetone`, `benzene`, `toluene`, etc.
- `reagents.py` is the consolidated superior version (more entries, complete `Reagent` dataclass with GHS hazards, storage groups, particle types, color signatures).

### Conflicting Reaction Classification
- `reaction_solver.py` has its own reaction classification logic (acid-base, catalytic foam, oscillating color wave, precipitation, chemiluminescence) using hardcoded reagent name checks.
- `cantera_engine.py` provides thermodynamic calculations but doesn't classify reaction types in the same way.
- After consolidation, `reaction_solver.py` will import reagent data from `reagents.py` for classification decisions, ensuring consistency.

### Skills/Model Module Overlap
- `skill_types.py` defines reagent unlocks per skill level (e.g., level 10: `["hcl", "naoh"]`).
- `milestones.py` defines similar reagent unlocks per milestone level.
- After consolidation, skill/ milestone reagent unlocks should reference the authoritative `reagents.py` registry, ensuring a single source of truth for which reagents are available at each progression level.

### Synthesis Protocol Duplication
- `total_syntheses.py` has 5 complete protocols (aspirin, paracetamol, caffeine, indigo, benzocaine).
- `guided_wizard.py` has `STAGE_REFERENCE_QUANTITIES` for aspirin and paracetamol stages with expected reagent amounts.
- After consolidation, `guided_wizard.py` will reference `total_syntheses.py` protocols (moved to `chemistry/catalog/`) for stage definitions, eliminating the duplicate reference data.

---

## 4. Authority Assignment Summary

| Concern | Authoritative Module | Source Files |
|---|---|---|
| **Reagent database** | `chemistry.catalog.reagents` | `reagents.py` (A), `cantera_engine.py` (D), `side_reactions.py` (B) |
| **Thermodynamics engine** | `chemistry.thermodynamics.engine` | `cantera_engine.py` (D, refactored) |
| **Cheminformatics (3D/Properties)** | `chemistry.cheminformatics.rdkit_bridge` | `rdkit_engine.py` (B) |
| **Reaction simulation** | `chemistry.simulation.solver` | `reaction_solver.py` (B) |
| **Precursor pathways** | `chemistry.catalog.precursors` | `precursor_synthesis.py` (B) |
| **Safety/side reactions** | `chemistry.safety.side_reactions` | `side_reactions.py` (B) |
| **Skill types** | `skills.skill_types` | `skill_types.py` (A) |
| **Milestones** | `skills.milestones` | `milestones.py` (A) |
| **Skill runtime state** | `skills.manager` | `skill_manager.py` (D, refactored) |
| **Synthesis protocols** | `chemistry.catalog.protocols` | `total_syntheses.py` (B), `guided_wizard.py` (B) |

---

## 5. Migration Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Broken imports across codebase** | Run `grep -r "from chemlab.simulation" --include="*.py" .` before/after; use IDE-wide rename/refactor; update all files in batch. |
| **Lost thermodynamic data** | Cantera engine preserves calculation rigor; data migration from `THERMO_DATABASE` to `reagents.py` entries is straightforward (both use same formula-based lookup). |
| **Skill progression breaks** | `skill_types.py` and `milestones.py` remain unchanged (A classification). Only `skill_manager.py` is refactored (D). Run full pytest suite. |
| **Synthesis protocols fail** | `total_syntheses.py` protocols migrate to `chemistry/catalog/` with reagent ID references. Test each protocol (aspirin synthesis especially) after migration. |
| **RDKit property changes** | `rdkit_engine.py` functionality preserved in new location. The `MolecularProperties` dataclass structure remains identical. |

---

## 6. Success Criteria

- [ ] `pytest` passes (256 tests green) after consolidation
- [ ] All imports resolve to `chemistry/` module paths
- [ ] No duplicate reagent definitions remain in the codebase (verify with `grep -r "THERMO_DATABASE\|Reagent(" src/chemlab/ --include="*.py" | grep -v "reagents.py" | wc -l` = 0)
- [ ] Skill progression still unlocks correct reagents at each level
- [ ] All 5 total synthesis protocols (aspirin, paracetamol, caffeine, indigo, benzocaine) remain fully functional
- [ ] RDKit 3D conformer generation still works
- [ ] Reaction simulation (mixing, step progress) still works correctly
- [ ] Safety/side reaction evaluation still produces correct reports

---