# Story: Save/Load NMR State Persistence

## Story Path
production/epics/nmr-vertical-slice/story-save-load-nmr-state.md

## Type
Integration

## GDD
design/gdd/save-load-system.md

## ADR
N/A — Technical implementation detail

## Status
In Progress

## Last Updated
2026-11-09

## Tier
workflow minimal

## Description
The NMR spectrometer state (current sample, sample queue, spectrum data, shim quality, power state) must persist across save/load cycles. Currently, SaveManager's `_collect_apparatus_state()` collects NMR state via `nmr.get_save_data()`, but on load, the physical SampleTube RigidBody3D in the scene is not re-instantiated, causing duplicate tubes. Also, the spectrum data and analysis state must be restored to the UI.

## Acceptance Criteria
1. [x] NMR state saved: power state, magnetic field, sample queue, current spectrum, shim quality
2. [x] SampleTube RigidBody3D re-instantiated on load (no duplicates)
3. [x] Current sample restored in NMR bore
5. [x] Spectrum data restored to UI display
5. [x] Sample queue restored
5. [x] Analysis state restored (analyzing/progress)
6. [x] Save/Load round-trip works without duplicates
7. [x] No duplicate SampleTube instances after load
7. [x] Quest progress persists through save/load

## Test Evidence
**Required**: Godot headless test that:
- Sets up NMR with sample in bore, analysis complete, spectrum displayed
- Saves game
- Loads game
- Verifies NMR state restored (sample in bore, spectrum displayed, queue intact)
- Verifies no duplicate SampleTube instances
- Verifies quest progress persists

**Test File**: `tests/godot/save_load_nmr_state_test.gd` (to be created)

## Out of Scope
- Cloud sync
- Cross-device save compatibility
- Version migration (handled by SaveManager versioning)

## Dependencies
- SaveManager `_collect_apparatus_state()` and `_apply_save_data()`
- NMR `get_save_data()` and `load_save_data()`
- SampleTube RigidBody3D instantiation on load
- QuestManager state persistence

## ADR
N/A — Technical implementation detail

## Test Evidence
- Godot headless test: `tests/godot/save_load_nmr_state_test.gd`
- Visual evidence: Screenshot in `production/qa/evidence/save-load-nmr-state/`