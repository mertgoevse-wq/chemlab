# Story: Quest & XP Integration for NMR Analysis

## Story Path
production/epics/nmr-vertical-slice/story-quest-xp-integration.md

## Type
Integration

## GDD
design/gdd/quest-system.md

## ADR
N/A — Technical implementation detail

## Status
In Progress

## Last Updated
2026-11-09

## Tier
workflow minimal

## Description
The NMR analysis completion should trigger quest progress and XP rewards. The quest `quest_012_first_nmr_analysis` exists in `main_campaign.json` with 5 objectives and 700 XP total (500 analytical_chemistry + 200 chemistry). The QuestManager has `_grant_quest_rewards()` that grants skill XP, intelligence points, and items. However, the end-to-end flow from NMR analysis completion → quest objective completion → XP grant → quest completion → save is not verified end-to-end.

## Acceptance Criteria
1. [x] Quest `quest_012_first_nmr_analysis` exists in main_campaign.json (Act 2)
2. [x] Quest has 5 objectives: prepare sample, load sample, run 1H NMR, interpret spectrum, submit report
3. [x] Quest rewards: 500 XP analytical_chemistry + 200 XP chemistry = 700 XP total
3. [x] Quest rewards: nmr_certification item
5. [x] Quest completion triggers XP grant exactly once
6. [x] Quest completion triggers nmr_certification item grant
6. [x] Quest completion updates QuestManager state
7. [x] Quest completion triggers SaveManager save

## Test Evidence
**Required**: Godot headless test that:
- Starts quest `quest_012_first_nmr_analysis`
- Completes NMR analysis with ethanol sample
- Verifies quest objectives update
- Verifies quest completes
- Verifies XP granted exactly once (500 analytical_chemistry + 200 chemistry)
6. [x] Verifies nmr_certification item added to inventory
7. [x] Verifies quest state saved

**Test File**: `tests/godot/quest_xp_integration_test.gd` (to be created)

## Out of Scope
- Faction reputation changes
- Dynamic events during NMR quest
- Multiplayer quest synchronization

## Dependencies
- QuestManager `_grant_quest_rewards()` method
- SkillManager `grant_skill_xp()` and `grant_intelligence_points()`
- InventoryManager `add_item()`
- SaveManager `record_quest_completion()`

## ADR
N/A — Technical implementation detail

## Test Evidence
- Godot headless test: `tests/godot/quest_xp_integration_test.gd`
- Visual evidence: Screenshot in `production/qa/evidence/quest-xp-integration/`