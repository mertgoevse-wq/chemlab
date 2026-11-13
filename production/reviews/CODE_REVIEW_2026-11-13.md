# Athanor Ascension — Comprehensive Code Review

**Date:** 2026-11-13
**Scope:** whole repository after consolidating `main` with `origin/claude/upbeat-banach-c46a7d`
**Skill applied:** `/code-review` (CCGS), `/game-review` (game-dev), `/security-audit`, `/tech-debt`
**Reviewer:** Buffy (autonomous session)

---

## 1. Verdict

**PASS WITH CONCERNS.**

The game builds and runs headlessly, all Python tests pass, every GDScript file parses,
and the merge introduced no regressions after four defects were repaired. The remaining
concerns are structural (very large scripts), tooling (mypy blocked by a third-party stub),
and style debt (106 ruff findings). None of them block play.

---

## 2. Evidence collected

| Check | Command | Result |
|---|---|---|
| Godot scene smoke test | `tools/bin/godot --headless --path game --script res://scripts/smoke_test.gd` | **31 passed, 0 failed** |
| Python suite | `.venv/Scripts/python.exe -m pytest -q` | **521 passed, 2 skipped** |
| GDScript parse scan | `godot --headless --path game --editor --quit` | **0 script/parse errors** |
| JSON validity | Python `json.loads` over `game/**/*.json` | **0 invalid files** |
| Quest graph | regex over `quest_manager.gd` | **97 quest ids, 11 `next_quest_id` refs, 0 dangling** |
| TODO/FIXME/HACK | `rg` over `game/` and `src/` | **1** |
| Ruff | `ruff check src tests simulation safety_simulation storage chemlab_core` | **106 findings** (style, mostly tests) |
| Mypy | `mypy src/chemlab` | **blocked** — `rdkit-stubs` ships invalid syntax (`Chem/rdMolDescriptors.pyi:10`) |
| Secrets | tracked `.env`/keys + API-key regex | **none found** |

### Godot test suite (verified by exit code)

Passing: `test_ai_reaction_bridge`, `test_apparatus_and_practicum`, `test_character_customization`,
`test_companion_and_resonance`, `test_genome_simulation`, `test_lab_hub_integration`,
`test_lab_physics`, `test_loading_screen`, `test_main_menu_modes`, `test_nmr_spectrometer_cycle`,
`test_open_world_and_mastery`, `test_photorealistic_bench`, `test_player_controller`,
`test_progression`, `test_quest_campaign`, `test_save_manager_slots`, `test_synthesis_catalog`,
`test_synthesis_chemistry`, `test_synthesis_flow`, `test_titration_flow`,
`test_vogel_and_tropanes`, `test_webcam_input_manager`.

`test_nmr_spectrometer_cycle` previously hung because `assert()` abort left `SceneTree` alive;
the underlying parse error is fixed and the suite now exits 0.

---

## 3. Defects found and fixed

| # | Severity | Location | Problem | Fix |
|---|---|---|---|---|
| 1 | **Blocker** | `game/scenes/apparatus/nmr_sample_tube.gd`, `nmr_spectrometer.gd` | Merged branch used `RigidBody3D.FREEZE_MODE_NONE`, which does not exist in Godot 4.7. Both scripts failed to parse; the NMR scene loaded as a bare `StaticBody3D`. | Removed the invalid constant; `freeze = false` already restores normal physics. |
| 2 | **Blocker** | `game/scripts/save/save_manager.gd` (during merge) | Conflict region duplicated the NMR save/restore block. | Took `main`'s clean version; verified single occurrence. |
| 3 | High | `game/tests/test_ai_reaction_bridge.gd` | GDScript lambdas capture locals **by value**; `recorded_resp = resp` inside the callback never reached the assertion, so two valid bridge APIs were reported broken. | Accumulate into an `Array` (captured by reference) and read `recorded[0]`. |
| 4 | Medium | `game/scenes/laboratories/photorealistic_bench.gd` + `game/data/synthesis/hofmann_ergot_and_lysergamides.json` | Bench opened the room-temperature LSD protocol (`default_temp: 20.0`), so the heating mantle could never rise above ambient; the actuator test was correct and the data choice was wrong. | Default the distillation bench to `limonene_citrus_steam_distillation`, with aspirin then LSD as fallbacks. Mantle now reaches 45.5 °C in 2 s. |

---

## 4. Architecture observations

**Strengths**

- Clean dual-engine split: `SimulationBridge` owns IPC vs. embedded fallback, so the game is
  genuinely offline-capable.
- Simulation logic is data-driven (`synthesis_catalog.gd`, JSON protocol libraries) instead of
  hard-coded per reaction.
- Quest graph is internally consistent (no dangling chains) and uses stable string ids.
- Assets are procedurally generated in Godot, so the project renders without an art pipeline.

**Concerns (non-blocking)**

1. **God objects.** `photorealistic_bench.gd` (1,800 lines) mixes UI construction, 3D scene
   building, thermodynamics and protocol state. `quest_manager.gd` (1,768) mixes catalog data
   with runtime state. `simulation_bridge.gd` (1,491) mixes transport, chemistry and AI routing.
   Recommended split: data → `game/data/`, one controller per concern.
2. **Duplicated legacy cores.** `chemlab_core/`, `simulation/`, `safety_simulation/` and
   `storage/` overlap `src/chemlab/`. They are **not dead**: tests and `src/chemlab/cv` import
   them. Migration should be a separate, test-backed task, not a deletion.
3. **Ruff style debt (106).** Mostly `SIM102`, import order and `assert` style in tests.
   Worth a `ruff --fix` pass in a dedicated commit so review diffs stay readable.
4. **Type checking is unverified.** Mypy cannot run because of a broken third-party stub file.
   Pin a working `rdkit-stubs` version or exclude it, then re-enable.
5. **Performance is NOT ASSESSED.** The design target is 60 FPS / ≤65 draw calls on Intel Iris Xe,
   but no profiler capture exists in the repository. Per the perf-profile skill, reporting
   headroom without data would be a false pass.

---

## 5. Security review

- No tracked `.env`, private keys, credentials or API-key literals were found.
- `.gitignore` covers `.env*`, `*.secret`, `*.pem`, `*.key`, `credentials.json`, `token.json`.
- Blender/Godot MCP servers bind to loopback only.
- The new Blender bridge binds an explicit port without `SO_REUSEADDR`; the earlier setting let a
  second process silently steal the socket on Windows.
- Remaining risk: `package/addon/simple_mcp_addon.py` executes arbitrary Python by design. It is a
  developer tool, must never ship in an export, and should stay behind loopback.

---

## 6. Merge report

| Item | Value |
|---|---|
| Branch merged | `origin/claude/upbeat-banach-c46a7d` (2 commits, NMR vertical slice) |
| Divergence | 33 commits on `main`, merge-base `27c119e` |
| Conflicted files | 16 |
| Resolution | `main` kept for overlapping engines/tests; NMR apparatus merged by hand |
| Worktrees | only one existed (`C:/Users/Win11 Pro/Desktop/chemlab`) — nothing else to fold in |
| Result | single `main` branch, all local history intact |

`main` is 36 commits ahead of `origin/main`; **nothing was pushed** (not requested).

---

## 7. Recommended next steps

1. Split `photorealistic_bench.gd` and `quest_manager.gd` (tech-debt epic).
2. Run `ruff --fix` and re-enable mypy with a pinned stub.
3. Capture a real profiler trace in the bench scene before claiming the 60 FPS budget.
4. Migrate `simulation/` and `safety_simulation/` tests onto `src/chemlab/`, then delete the
   legacy packages in one verified change.
