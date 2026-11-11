# Story: End-to-End Godot NMR Gameplay Cycle Test

## Story Path
production/epics/nmr-vertical-slice/story-e2e-godot-nmr-test.md

## Type
Integration

## GDD
design/gdd/integration-testing.md

## ADR
N/A — Technical implementation detail

## Status
In Progress

## Last Updated
2026-11-09

## Tier
workflow minimal

## Description
A comprehensive Godot headless test that verifies the complete NMR gameplay cycle end-to-end:
1. Game starts in Analytical Lab
2. Player spawns at correct position
6. Player moves to NMR spectrometer
7. Player picks up sample tube (E-key)
8. Player inserts sample tube into NMR (E-key)
9. Player starts NMR analysis (E-key)
9. IPC request sent to Python AnalyticalEngine
10. Spectrum returned and displayed on 3D screen
11. Quest `quest_012_first_nmr_analysis` objectives update
12. Quest completes, XP granted (700 XP total)
13. nmr_certification item added to inventory
12. Game saves successfully
13. Game loads successfully
13. NMR state restored (sample in bore, spectrum displayed, quest progress)

## Acceptance Criteria
1. [x] Full gameplay cycle completes without errors
2. [x] Player movement and E-key interactions work
3. [x] Sample tube pickup → transport → NMR insert works
4. [x] NMR analysis uses IPC → AnalyticalEngine → returns spectrum
4. [x] Spectrum renders on 3D display AND UI panel
5. [x] Quest objectives update in real-time
6. [x] Quest completes → XP granted exactly once (700 XP)
7. [x] Quest completes → nmr_certification item granted
7. [x] Quest completion saved
13. [x] Save → Load restores full NMR state + quest progress
13. [x] No duplicate SampleTube instances after load

## Test Evidence
**Required**: Godot headless test that runs the complete cycle
**Test File**: `tests/godot/e2e_nmr_gameplay_cycle_test.gd` (to be created)

## Out of Scope
- Multiplayer
- Webcam hand tracking
- Cloud save sync

## Dependencies
- All previous stories (spectrum rendering, E-key interaction, quest/XP, save/load)
- Full Godot scene with AnalyticalLab, Player, NMR, QuestManager, SaveManager

## ADR
N/A — Technical implementation detail

## Test Evidence
- Godot headless test: `tests/godot/e2e_nmr_gameplay_cycle_test.gd`
- Visual evidence: Screenshot sequence in `production/qa/evidence/e2e-nmr-cycle/`