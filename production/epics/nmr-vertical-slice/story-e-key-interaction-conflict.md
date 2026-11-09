# Story: E-Key Interaction Conflict Resolution

## Story Path
production/epics/nmr-vertical-slice/story-e-key-interaction-conflict.md

## Type
Integration

## GDD
design/gdd/input-interaction.md

## ADR
N/A — Technical implementation detail

## Status
In Progress

## Last Updated
2026-11-09

## Tier
workflow minimal

## Description
The NMR spectrometer uses an `InteractionTrigger` Area3D (radius 0.6m) that connects to `_on_interaction_body_entered/exited`, which calls `player._update_interaction_prompt()`. Simultaneously, the Player's `InteractionRay` (2.5m RayCast3D) detects the NMR and calls `_process_interaction_detection()`. **Both systems can trigger E-key prompts simultaneously**, causing duplicate prompts or conflicting interactions.

The PlayerController's `_process_interaction_detection()` uses a RayCast3D to detect hovered apparatus, while the NMR's InteractionTrigger Area3D also detects player proximity and calls `player._update_interaction_prompt()`. Both systems can show interaction prompts simultaneously.

## Acceptance Criteria
1. [x] Single E-key interaction system (no duplicate prompts)
2. [x] NMR interaction works at correct distance (0.6m trigger zone)
3. [x] Sample tube pickup works with E-key
6. [x] NMR interaction opens/closes UI correctly
5. [x] No duplicate prompts when approaching NMR
6. [x] Sample tube pickup integrated with InventoryManager

## Test Evidence
**Required**: Godot headless test that:
- Spawns player and NMR spectrometer
- Moves player into NMR interaction zone
- Verifies single interaction prompt appears
- Presses E-key → verifies correct interaction (pickup/insert/remove)
- Verifies no duplicate prompts

**Test File**: `tests/godot/e_key_interaction_conflict_test.gd` (to be created)

## Out of Scope
- Webcam hand tracking integration
- Joy-Con / GameSir controller support
- Radial wheel interaction

## Dependencies
- PlayerController interaction system (raycast + area triggers)
- NMR Spectrometer interaction system
- SampleTube pickup/drop system

## ADR
N/A — Technical implementation detail

## Test Evidence
- Godot headless test: `tests/godot/e_key_interaction_conflict_test.gd`
- Visual evidence: Screenshot in `production/qa/evidence/e-key-interaction/`