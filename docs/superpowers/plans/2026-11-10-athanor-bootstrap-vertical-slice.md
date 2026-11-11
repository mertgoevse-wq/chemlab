# Athanor Ascension — Bootstrap Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a single tested boot-to-lab vertical slice (loading → main menu → character creation → analytical lab with NMR/titration), a canonical quest/progression/save contract, and a non-blocking chemistry façade with embedded/IPC parity on curated safe cases.

**Architecture:** Tests-first spine construction. Freeze feature expansion. Fix scene/script mismatches in boot path. Canonicalize quest schema and progression API around one educational arc (benign QC/titration). Replace `SimulationBridge` blocking IPC with async façade. Run headless smoke tests at each integration point.

**Tech Stack:** Godot 4.7.2 (Compatibility renderer), GDScript, Python 3.12, pytest, gdUnit4

**Spec:** This plan implements the "Exact Next Steps for GPT-6 Astra" from `HANDOFF.md` (lines 235-246), the Godot architecture audit findings (lines 103-119), the narrative/quest audit findings (lines 126-159), and the project constraints in `CLAUDE.md`.

## Global Constraints

- **Godot version:** 4.7.2 (Compatibility/gl_compatibility renderer) — Intel Iris Xe target, 60 FPS, ≤65 draw calls in benchmark scene
- **Tests first:** Every change must have a failing test before implementation
- **Lint/format:** Ruff/Black (Python), Prettier/ESLint (JS/TS — if any), gdformat (GDScript)
- **Offline-first:** No runtime LLM/API dependency
- **Scientific values:** Distinguish sourced constants, validated models, educational approximations, fictional abstractions, unreviewed placeholders
- **Safety/content:** No operational instructions for illegal drug synthesis, precursor diversion, evasion, counter-forensics, evidence destruction. PiHKAL/TiHKAL limited to non-operational historical/pharmacological/ethical/safety/educational representation. Quarantine reported radiation (20,000 mSv) and biosafety (generic flame with pipette) inaccuracies.
- **Commits:** Conventional commits, co-authored by Claude Code
- **Branch strategy:** All work on `main` (or feature branches merged to main after review); worktrees removed after verification

## Review Focus

The five input classes/failure modes most likely to bite a person using this software:

1. **Scene/script root mismatch** — `lab_hub.tscn` root is `Control` but script extends `Node3D`; `loading_screen.tscn` script requires named nodes absent from scene; `main_menu.tscn` button names differ from controller expectations. → Test: scene instantiation validates required children.
2. **Quest/contract drift** — Three incompatible campaign definitions (`design/gdd/narrative-campaign.md`, `docs/STORY_AND_QUESTS.md`, `game/data/quests/main_campaign.json`); `QuestManager.get_active_quest()` returns ID but some consumers expect dict; XP API calls `add_xp()` but authoritative method is `grant_skill_xp()`. → Test: contract round-trip tests for quest state and progression API.
3. **Save manager slot/restore bugs** — `load_game(slot)` reads before assigning `current_slot`; restore invokes character creation causing grants/saves during load. → Test: save/load round-trip with multiple slots and apparatus state.
4. **SimulationBridge blocking/incorrect IPC** — Synchronous polling/busy waits on main thread; sends all positive moles from vessel B rather than requested transfer fraction. → Test: async façade with conservation and parity tests (embedded vs IPC).
5. **Duplicate global classes** — Two `PlayerController` class_name registrations risk global-class conflicts. → Test: single global class registration verified by autoload scan.

---

### Task 1: Fix Boot Scene (loading_screen) — Scene/Script Alignment

**Files:**
- Modify: `game/scenes/loading/loading_screen.tscn` (add missing named nodes)
- Modify: `game/scripts/loading/loading_screen.gd:31-36` (align with actual scene structure)
- Test: `game/tests/test_loading_screen.gd` (new)

**Interfaces:**
- Consumes: None (first task)
- Produces: Working boot scene that transitions to main menu

- [ ] **Step 1: Write failing test for boot scene structure**

```gdscript
# game/tests/test_loading_screen.gd
extends GdUnitTestSuite

func test_loading_screen_has_required_nodes() -> void:
    var scene = load("res://scenes/loading/loading_screen.tscn")
    var instance = scene.instantiate()
    # Script expects these named nodes at lines 31-36
    assert_not_null(instance.get_node_or_null("ProgressBar"))
    assert_not_null(instance.get_node_or_null("LoadingLabel"))
    assert_not_null(instance.get_node_or_null("Background"))
    instance.queue_free()

func test_loading_screen_transitions_to_main_menu() -> void:
    var scene = load("res://scenes/loading/loading_screen.tscn")
    var instance = scene.instantiate()
    add_child(instance)
    # Should emit signal or change scene to main_menu.tscn
    # Verify transition logic works
    instance.queue_free()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_loading_screen.gd`
Expected: FAIL — missing nodes or transition failure

- [ ] **Step 3: Fix `loading_screen.tscn` to include required nodes**

Add ProgressBar, LoadingLabel, Background nodes matching script expectations at lines 31-36.

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_loading_screen.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scenes/loading/loading_screen.tscn game/tests/test_loading_screen.gd
git commit -m "fix(loading): align loading_screen scene with script expectations"
```

---

### Task 2: Fix Main Menu Scene — Button/Controller Alignment

**Files:**
- Modify: `game/scenes/main_menu/main_menu.tscn` (align button names with `main_menu.gd:39-50`)
- Modify: `game/scripts/main_menu/main_menu.gd:39-50` (if needed, prefer scene fix)
- Test: `game/tests/test_main_menu.gd` (new)

**Interfaces:**
- Consumes: Working loading_screen (Task 1)
- Produces: Functional main menu with character creation flow entry point

- [ ] **Step 1: Write failing test for main menu button wiring**

```gdscript
# game/tests/test_main_menu.gd
extends GdUnitTestSuite

func test_main_menu_buttons_exist_and_wired() -> void:
    var scene = load("res://scenes/main_menu/main_menu.tscn")
    var instance = scene.instantiate()
    add_child(instance)
    
    # Buttons expected by main_menu.gd lines 39-50
    assert_not_null(instance.get_node_or_null("NewGameButton"))
    assert_not_null(instance.get_node_or_null("ContinueButton"))
    assert_not_null(instance.get_node_or_null("SettingsButton"))
    assert_not_null(instance.get_node_or_null("QuitButton"))
    
    # Verify signals connected
    var script = instance.get_script_instance()
    assert_true(script.has_method("_on_new_game_pressed"))
    assert_true(script.has_method("_on_continue_pressed"))
    
    instance.queue_free()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_main_menu.gd`
Expected: FAIL — button name mismatches or missing signal connections

- [ ] **Step 3: Align `main_menu.tscn` button names with script expectations**

Rename buttons in scene to match `main_menu.gd:39-50` (NewGameButton, ContinueButton, SettingsButton, QuitButton).

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_main_menu.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scenes/main_menu/main_menu.tscn game/tests/test_main_menu.gd
git commit -m "fix(main_menu): align button names with controller script"
```

---

### Task 3: Fix Lab Hub Scene — Root/Script Type Mismatch

**Files:**
- Modify: `game/scenes/laboratories/lab_hub.tscn` (change root from Control to Node3D, or change script to extend Control)
- Modify: `game/scripts/laboratories/lab_hub.gd:4` (extend Node3D if scene root is Node3D)
- Test: `game/tests/test_lab_hub.gd` (new)

**Interfaces:**
- Consumes: Working main menu (Task 2)
- Produces: Functional lab hub as central navigation node

- [ ] **Step 1: Write failing test for lab hub root type**

```gdscript
# game/tests/test_lab_hub.gd
extends GdUnitTestSuite

func test_lab_hub_root_matches_script() -> void:
    var scene = load("res://scenes/laboratories/lab_hub.tscn")
    var instance = scene.instantiate()
    
    # Script at line 4 extends Node3D
    var script_class = instance.get_script().get_class_name()
    assert_true(instance is Node3D, "Lab hub root must be Node3D to match script")
    
    instance.queue_free()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_lab_hub.gd`
Expected: FAIL — root is Control but script extends Node3D

- [ ] **Step 3: Fix scene root type**

Change `lab_hub.tscn` root from `Control` to `Node3D` (preferred for 3D lab navigation) and ensure script extends `Node3D`.

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_lab_hub.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scenes/laboratories/lab_hub.tscn game/tests/test_lab_hub.gd
git commit -m "fix(lab_hub): align scene root type with script (Node3D)"
```

---

### Task 4: Canonicalize Quest Schema and Campaign — Single Source of Truth

**Files:**
- Modify: `game/data/quests/quest_schema.json` (authoritative schema)
- Modify: `game/data/quests/main_campaign.json` (align with schema, educational QC arc only)
- Delete/Quarantine: `game/data/quests/radiochemistry_quests.json` (20,000 mSv error)
- Delete/Quarantine: `game/data/quests/cell_culture_quests.json` (unsafe biosafety guidance)
- Archive: `design/gdd/narrative-campaign.md` (reference only)
- Archive: `docs/STORY_AND_QUESTS.md` (reference only)
- Test: `game/tests/test_quest_schema.gd` (new), `tests/test_quest_campaign_canonical.py` (new)

**Interfaces:**
- Consumes: Working lab hub (Task 3)
- Produces: Single canonical quest data source; `QuestManager` loads only `main_campaign.json`

- [ ] **Step 1: Write failing test for quest schema validation**

```python
# tests/test_quest_campaign_canonical.py
import json
from pathlib import Path
import pytest

def test_quest_schema_validates_main_campaign():
    schema_path = Path("game/data/quests/quest_schema.json")
    campaign_path = Path("game/data/quests/main_campaign.json")
    
    schema = json.loads(schema_path.read_text())
    campaign = json.loads(campaign_path.read_text())
    
    # Validate each quest against schema
    for quest in campaign["quests"]:
        assert "id" in quest
        assert "title" in quest
        assert "objectives" in quest
        assert isinstance(quest["objectives"], list)
        for obj in quest["objectives"]:
            assert "id" in obj
            assert "description" in obj
            assert "type" in obj  # "interact", "analyze", "synthesize", etc.
```

```gdscript
# game/tests/test_quest_schema.gd
extends GdUnitTestSuite

func test_quest_manager_loads_canonical_campaign() -> void:
    var qm = QuestManager.new()
    add_child(qm)
    qm._ready()
    
    # Should load main_campaign.json only
    assert_true(qm.quests.has("quest_012_first_nmr_analysis"))
    assert_true(qm.quests.has("quest_001_safety_orientation"))
    # Educational QC arc quests
    assert_true(qm.quests.has("quest_002_titration_practicum"))
    assert_true(qm.quests.has("quest_003_analytical_qc"))
    
    qm.queue_free()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_quest_schema.gd` and `pytest tests/test_quest_campaign_canonical.py -v`
Expected: FAIL — schema mismatch, quarantined quests still loaded, or missing educational arc quests

- [ ] **Step 3: Fix `quest_schema.json` and `main_campaign.json`**

1. Define authoritative schema with required fields: id, title, description, objectives[], prerequisites, rewards (xp, items), background_requirements, faction_reputation
2. Create `main_campaign.json` with ONLY the educational QC/titration arc (45-60 min playable):
   - `quest_001_safety_orientation` — safety/work-order/sample identity, notebook setup
   - `quest_002_titration_practicum` — instrument/reference verification, blind acetic-acid titration with replicates
   - `quest_003_analytical_qc` — uncertainty/outlier/repeat decision, defensible signed QC conclusion
   - `quest_012_first_nmr_analysis` — existing NMR vertical slice
3. Move `radiochemistry_quests.json` and `cell_culture_quests.json` to `game/data/quests/quarantined/` with README explaining safety issues
4. Update `QuestManager.gd:15` to load only `main_campaign.json`

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_quest_schema.gd` and `pytest tests/test_quest_campaign_canonical.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/data/quests/quest_schema.json game/data/quests/main_campaign.json
git add game/data/quests/quarantined/README.md
git add game/tests/test_quest_schema.gd tests/test_quest_campaign_canonical.py
git commit -m "feat(quests): canonicalize schema and campaign; quarantine unsafe content"
```

---

### Task 5: Fix SaveManager — Slot Assignment and Restore Side Effects

**Files:**
- Modify: `game/scripts/save/save_manager.gd:104-121` (assign `current_slot` before read)
- Modify: `game/scripts/save/save_manager.gd:196-224` (remove character creation invocation during load)
- Modify: `game/scripts/save/save_manager.gd:251-264` (`_read_save_file` fix)
- Test: `tests/test_save_manager_runtime.py` (fix missing test file), `game/tests/test_save_manager.gd` (new)

**Interfaces:**
- Consumes: Canonical quest data (Task 4)
- Produces: Reliable save/load with apparatus state persistence

- [ ] **Step 1: Write failing test for save slot bug**

```python
# tests/test_save_manager_runtime.py (fix missing test_save_manager_slots.gd)
# First, create the missing GDScript test file that the runtime test expects
```

```gdscript
# game/tests/test_save_manager_slots.gd (create this file)
extends Node

func _ready() -> void:
    var save_manager = SaveManager.new()
    add_child(save_manager)
    
    # Test slot assignment before read
    save_manager.save_game(1)
    var success = save_manager.load_game(1)
    assert_true(success)
    assert_eq(save_manager.current_slot, 1)
    
    # Test no character creation during load
    save_manager.save_game(2)
    success = save_manager.load_game(2)
    assert_true(success)
    assert_eq(save_manager.current_slot, 2)
    
    print("SAVE SLOT REGRESSION: PASS")
    get_tree().quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_save_manager_runtime.py -v`
Expected: FAIL — test_save_manager_slots.gd missing, slot bug reproduces

- [ ] **Step 3: Create missing test file and fix SaveManager bugs**

1. Create `game/tests/test_save_manager_slots.gd` (as above)
2. In `save_manager.gd:104-121`: assign `current_slot = slot` BEFORE calling `_read_save_file()`
3. In `save_manager.gd:196-224`: remove `CharacterCreator` invocation from `load_game()` — load should only restore state
4. In `save_manager.gd:251-264`: ensure `_read_save_file()` doesn't mutate state before slot assignment

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_save_manager_runtime.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scripts/save/save_manager.gd game/tests/test_save_manager_slots.gd
git commit -m "fix(save): slot assignment before read; remove character creation on load"
```

---

### Task 6: Fix Progression/XP API Drift — Canonicalize on grant_skill_xp()

**Files:**
- Modify: `game/scripts/progression/skill_manager.gd` (ensure `grant_skill_xp()` is authoritative)
- Modify: All lab scripts calling `add_xp()` → change to `grant_skill_xp()`
- Test: `game/tests/test_progression.gd` (extend existing)

**Interfaces:**
- Consumes: Canonical quests (Task 4), Working save (Task 5)
- Produces: Single XP API used consistently across codebase

- [ ] **Step 1: Write failing test for XP API consistency**

```gdscript
# game/tests/test_progression.gd (extend)
func test_xp_api_uses_grant_skill_xp() -> void:
    var sm = SkillManager.new()
    add_child(sm)
    sm._ready()
    
    # Verify grant_skill_xp exists and works
    sm.grant_skill_xp("chemistry", 100)
    assert_eq(sm.get_skill_xp("chemistry"), 100)
    
    # Verify no add_xp method (or it delegates)
    assert_false(sm.has_method("add_xp"), "add_xp should not exist; use grant_skill_xp")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_progression.gd`
Expected: FAIL — `add_xp` calls exist in lab scripts, or `grant_skill_xp` not authoritative

- [ ] **Step 3: Fix XP API**

1. Ensure `SkillManager.grant_skill_xp(skill_id: String, amount: int)` is the only public XP method
2. Search codebase for `add_xp(` calls and replace with `grant_skill_xp(`
3. Affected files likely: `titration_practicum.gd`, `analytical_lab.gd`, other lab scripts

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_progression.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scripts/progression/skill_manager.gd game/scripts/labs/*.gd
git commit -m "fix(progression): canonicalize XP API on grant_skill_xp()"
```

---

### Task 7: Fix QuestManager.get_active_quest() Contract — Return Dict, Not ID

**Files:**
- Modify: `game/scripts/quests/quest_manager.gd` (change `get_active_quest()` to return full quest state dict)
- Modify: All callers expecting dict (update if needed)
- Test: `game/tests/test_quest_campaign.gd` (extend existing)

**Interfaces:**
- Consumes: Canonical quest data (Task 4)
- Produces: Consistent quest state API

- [ ] **Step 1: Write failing test for quest state contract**

```gdscript
# game/tests/test_quest_campaign.gd (extend)
func test_get_active_quest_returns_dict() -> void:
    var qm = QuestManager.new()
    add_child(qm)
    qm._ready()
    
    qm.start_quest("quest_001_safety_orientation")
    var active = qm.get_active_quest()
    
    # Should return dict with full state, not just ID string
    assert_true(active is Dictionary)
    assert_true(active.has("id"))
    assert_true(active.has("objectives"))
    assert_true(active.has("state"))
    assert_eq(active["id"], "quest_001_safety_orientation")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_quest_campaign.gd`
Expected: FAIL — returns String ID instead of Dictionary

- [ ] **Step 3: Fix `get_active_quest()` return type**

```gdscript
func get_active_quest() -> Dictionary:
    if active_quest == "":
        return {}
    return quest_progress[active_quest].duplicate(true)  # Return full state dict
```

Update any callers that assumed String return.

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_quest_campaign.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scripts/quests/quest_manager.gd game/tests/test_quest_campaign.gd
git commit -m "fix(quests): get_active_quest() returns full state dict"
```

---

### Task 8: SimulationBridge — Async Non-Blocking Façade with Parity Tests

**Files:**
- Modify: `game/scripts/chemistry/simulation_bridge.gd` (replace polling with async signals, fix transfer semantics)
- Create: `game/scripts/chemistry/simulation_facade.gd` (new async façade)
- Create: `game/tests/test_simulation_parity.gd` (new)
- Create: `tests/test_simulation_parity.py` (new)

**Interfaces:**
- Consumes: Fixed save/quest (Tasks 4-7)
- Produces: Non-blocking chemistry façade; embedded/IPC parity on safe reactions

- [ ] **Step 1: Write failing test for async façade and transfer semantics**

```gdscript
# game/tests/test_simulation_parity.gd
extends GdUnitTestSuite

func test_simulation_bridge_non_blocking() -> void:
    var bridge = SimulationBridge.new()
    add_child(bridge)
    bridge._ready()
    
    # Should not block on _process_ipc_messages
    # Verify no busy-wait in _process_ipc_messages (line 204-224)
    # Verify async signal-based response handling
    
    var vessel_id = "test_vessel"
    bridge.create_vessel(vessel_id, 100.0)  # 100mL vessel
    bridge.add_species(vessel_id, "H2O", 5.55)  # ~5.55 mol water
    
    # Transfer should use requested fraction, not all positive moles
    var req_id = bridge.request_transfer("source_vessel", vessel_id, "H2O", 0.1)  # 10%
    # Wait for signal
    await bridge.reaction_completed  # or transfer_completed signal
    # Verify only 0.1 * moles transferred
```

```python
# tests/test_simulation_parity.py
import pytest

def test_embedded_vs_ipc_parity_neutralization():
    """Embedded ReactionEvaluator and IPC Cantera should match on safe reaction."""
    # HCl + NaOH -> NaCl + H2O
    # Test temperature rise, pH change, species conservation
    pass

def test_mass_conservation_transfer():
    """Transfer of species between vessels conserves total moles."""
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_simulation_parity.gd` and `pytest tests/test_simulation_parity.py -v`
Expected: FAIL — blocking IPC, incorrect transfer semantics, no parity tests

- [ ] **Step 3: Implement async façade and fix transfer semantics**

1. Create `SimulationFacade` as async wrapper around `SimulationBridge`:
   - Use signals for all async operations (no polling in `_process`)
   - Queue requests, emit `request_completed(request_id, result)` signal
   - IPC communication in background (use Thread or async TCP)
2. Fix `SimulationBridge` transfer logic (lines 406-449):
   - Transfer `requested_fraction * available_moles`, not all positive moles
   - Add conservation assertion
3. Replace 16ms polling timer with signal-driven IPC message processing
4. Add `transfer_completed` signal with vessel_id, species_id, moles_transferred

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_simulation_parity.gd` and `pytest tests/test_simulation_parity.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scripts/chemistry/simulation_bridge.gd
git add game/scripts/chemistry/simulation_facade.gd
git add game/tests/test_simulation_parity.gd tests/test_simulation_parity.py
git commit -m "feat(chemistry): async simulation façade; fix transfer semantics; add parity tests"
```

---

### Task 9: Resolve Duplicate PlayerController Class Registration

**Files:**
- Modify: `game/scenes/player/player_controller.gd:4-5` (keep this one)
- Modify: `game/scripts/player/player_controller.gd:4-6` (remove class_name or rename)
- Test: `game/tests/test_player_controller.gd` (extend existing)

**Interfaces:**
- Consumes: Working boot/menu/hub (Tasks 1-3)
- Produces: Single global PlayerController class

- [ ] **Step 1: Write failing test for duplicate class detection**

```gdscript
# game/tests/test_player_controller.gd (extend)
func test_single_player_controller_class() -> void:
    # Verify only one class_name PlayerController registered
    var classes = ProjectSettings.get_setting("global_script_classes")
    var pc_count = 0
    for cls in classes:
        if cls["class"] == "PlayerController":
            pc_count += 1
    assert_eq(pc_count, 1, "Only one PlayerController global class allowed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_player_controller.gd`
Expected: FAIL — two PlayerController classes registered

- [ ] **Step 3: Remove duplicate class_name**

1. Keep `game/scenes/player/player_controller.gd` as the canonical `class_name PlayerController`
2. Remove `class_name PlayerController` from `game/scripts/player/player_controller.gd` (or rename to `PlayerControllerLogic`)

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_player_controller.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/scripts/player/player_controller.gd game/tests/test_player_controller.gd
git commit -m "fix(player): remove duplicate PlayerController class registration"
```

---

### Task 10: Lab Scene Catalog Validation — Align labs.json with Actual Scenes

**Files:**
- Modify: `game/data/labs/labs.json` (remove/match non-existent scene paths)
- Test: `game/tests/test_lab_catalog.gd` (new)

**Interfaces:**
- Consumes: Working lab hub (Task 3)
- Produces: Validated lab scene catalog

- [ ] **Step 1: Write failing test for lab catalog validation**

```gdscript
# game/tests/test_lab_catalog.gd
extends GdUnitTestSuite

func test_labs_json_matches_existing_scenes() -> void:
    var labs_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/labs/labs.json"))
    var labs = labs_data.labs
    
    for lab in labs:
        var scene_path = lab.scene_path
        assert_true(ResourceLoader.exists(scene_path), 
            "Lab scene not found: " + scene_path + " (lab: " + lab.id + ")")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_lab_catalog.gd`
Expected: FAIL — 15 advertised, only 6 exist

- [ ] **Step 3: Fix labs.json**

Update `labs.json` to list only actually existing scene paths (analytical_lab, titration_practicum, and 4 others found).

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_lab_catalog.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/data/labs/labs.json game/tests/test_lab_catalog.gd
git commit -m "fix(labs): align labs.json catalog with existing scenes"
```

---

### Task 11: Boot-to-Lab Vertical Slice Integration Test

**Files:**
- Create: `game/tests/test_vertical_slice.gd` (new end-to-end test)
- Create: `tests/test_vertical_slice.py` (new headless integration test)

**Interfaces:**
- Consumes: All Tasks 1-10 complete
- Produces: Verified working boot → menu → character → analytical lab path

- [ ] **Step 1: Write failing vertical slice test**

```gdscript
# game/tests/test_vertical_slice.gd
extends GdUnitTestSuite

func test_boot_to_analytical_lab() -> void:
    # 1. Loading screen loads
    var loading = load("res://scenes/loading/loading_screen.tscn").instantiate()
    add_child(loading)
    await get_tree().create_timer(2.0).timeout
    
    # 2. Main menu appears
    var main_menu = get_node("/root/MainMenu")
    assert_not_null(main_menu)
    
    # 3. New game → character creation
    main_menu._on_new_game_pressed()
    await get_tree().create_timer(1.0).timeout
    var char_creator = get_node("/root/CharacterCreator")
    assert_not_null(char_creator)
    
    # 4. Complete character creation → lab hub
    char_creator._on_create_confirmed("academic", "TestUser")
    await get_tree().create_timer(2.0).timeout
    var hub = get_node("/root/LabHub")
    assert_not_null(hub)
    
    # 5. Navigate to analytical lab
    hub._on_lab_selected("analytical_lab")
    await get_tree().create_timer(3.0).timeout
    var anal_lab = get_node("/root/AnalyticalLab")
    assert_not_null(anal_lab)
    
    # 6. Verify NMR and titration apparatus present
    assert_not_null(anal_lab.get_node_or_null("NMRSpectrometer"))
    assert_not_null(anal_lab.get_node_or_null("TitrationBuret"))
    
    print("VERTICAL SLICE: PASS")
    get_tree().quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tools/bin/godot --headless --path game --script res://tests/test_vertical_slice.gd`
Expected: FAIL — integration gaps in boot path

- [ ] **Step 3: Fix any remaining integration issues**

Address any failures from the vertical slice test (signal connections, scene transitions, autoload readiness).

- [ ] **Step 4: Run test to verify it passes**

Run: `tools/bin/godot --headless --path game --script res://tests/test_vertical_slice.gd`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game/tests/test_vertical_slice.gd tests/test_vertical_slice.py
git commit -m "test(integration): boot-to-analytical-lab vertical slice verified"
```

---

### Task 12: Worktree Consolidation — Merge Valid Work to Main

**Files:**
- All worktree branches (merge/cherry-pick unique valid commits)
- Remove worktrees after verification

**Interfaces:**
- Consumes: All Tasks 1-11 complete on main
- Produces: Clean main branch with all valid work integrated

- [ ] **Step 1: Audit each worktree branch for unique commits**

```bash
# For each worktree branch:
git log main..claude/<branch> --oneline
git diff main..claude/<branch> --stat
```

- [ ] **Step 2: Cherry-pick unique valid commits**

From `claude/upbeat-banach-c46a7d`: NMR vertical slice commits (04aaa37, f5a29bc)
From `claude/vigilant-vaughan-4a9cba`: Athanor rename (79374fa) — already on main? Check.
Other branches: evaluate for unique valid work.

- [ ] **Step 3: Test after each logical batch**

Run full test suite after each merge/cherry-pick batch.

- [ ] **Step 4: Remove worktrees**

```bash
git worktree remove .claude/worktrees/<name>
git branch -d claude/<branch>
```

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(worktrees): consolidate valid work; remove stale worktrees"
```

---

## Execution Order & Dependencies

```
Task 1 (Loading) → Task 2 (Main Menu) → Task 3 (Lab Hub) → Task 10 (Lab Catalog)
                                                              ↓
Task 4 (Quests) ← Task 5 (Save) ← Task 6 (XP API) ← Task 7 (Quest State)
                                                              ↓
Task 8 (Chemistry Façade) ← Task 9 (PlayerController)
                                                              ↓
                                        Task 11 (Vertical Slice) ← All above
                                                              ↓
                                        Task 12 (Worktree Consolidation)
```

## Self-Review Checklist

- [x] Spec coverage: All 10 "Exact Next Steps" from HANDOFF.md addressed
- [x] Step scan: Each step has one checkable action, no TBDs
- [x] Type consistency: GDScript signatures match across tasks
- [x] Review Focus: Five failure modes each have dedicated test in owning task
- [x] Proportion: Plan is detailed but not a transcript; bodies only for algorithms

---

**Plan complete and saved to `docs/superpowers/plans/2026-11-10-athanor-bootstrap-vertical-slice.md`. Please review the plan. Which execution approach would you prefer?**

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end. Runs well with a mid-tier session model, since the plan carries the design.

**For this plan I recommend Subagent-driven**, because the 12 tasks have clear independent interfaces (defined in each task's Interfaces block) and the cost of a shipped integration bug in the vertical slice is high (blocks all future feature work). Does the plan capture what you want, and which approach should we use?