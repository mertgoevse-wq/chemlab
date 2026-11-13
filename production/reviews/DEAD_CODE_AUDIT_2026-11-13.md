# Dead Code & Repository Hygiene Audit

**Date:** 2026-11-13
**Skills applied:** `/tech-debt`, `/code-review`, `/asset-audit`

## Removed

| Item | Size / count | Why it was dead |
|---|---|---|
| `.cache/chrome-profile/**` | 276 tracked files | A browser profile cache committed to git. Regenerated automatically by any Chromium run; never read by the project. |
| `blender-mcp-1.0.1.tgz` | vendor archive | Duplicate of `package/`; referenced only by a historical registry note. |
| `iflow-mcp-pranav-deshmukh-blender-mcp-1.0.0.tgz` | vendor archive | Same, second fork. |
| `package/dist/**` | 3 build files | Prebuilt npm output for an MCP server that `.mcp.json` does not load (it loads root `blender_mcp_server.mjs`). |
| `package/8809_process.log` | log | Stray process log. |
| `CUsersWin11/`, `Chemlab/`, `ProDesktopchemlab*` (7 dirs) | empty | Artifacts of malformed Windows paths; contained no files. |

## Kept deliberately (looked dead, but is live)

| Path | Evidence it is used |
|---|---|
| `chemlab_core/` | imported by `tests/conftest.py`, `tests/test_models.py`, `tests/test_blender_controller.py`, and by `src/chemlab/cv/hand_tracker.py` |
| `simulation/` | imported by `tests/test_free_sim.py` |
| `safety_simulation/` | imported by `tests/test_fume_hood.py`, `test_ghs.py`, `test_neutralization_drill.py`, `test_safety_officer_engine.py` |
| `storage/` | imported by `tests/test_asset_cache.py`, `tests/test_cloud_sync.py` |
| `package/addon/simple_mcp_addon.py` | kept as the Blender add-on reference; the headless bridge mirrors its protocol |
| `nmr_spectrometer.glb` (root) | superseded by `game/assets/apparatus/SM_NMR_Spectrometer.glb`; left in place pending asset-owner decision (not deleted without confirmation) |

## Brand-name scrub

Fourteen project-owned files contained third-party game brand names. All were rewritten to
Athanor-native wording, and three design docs were renamed:

- `design/ac_visual_upgrade.md` → `design/visual_upgrade.md`
- `design/companion_combat_ac.md` → `design/companion_combat.md`
- `design/narrative_ac_style.md` → `design/narrative_style.md`

Files touched: `CLAUDE.md`, `integration_report.json`, `design/missing_labs_design.md`,
`design/gdd/game-concept.md`, `game/data/equipment/equipment_database.json`,
`game/data/quests/quest_schema.json`, `game/scenes/genomics/genome_browser.gd`,
`game/scripts/companions/companion_data.gd`, `game/scripts/core/inventory_manager.gd`,
`game/scripts/input/input_manager.gd`, `game/scripts/quests/quest_overlay.gd`.

Residual matches are confined to `tools/vendor/` (third-party documentation), `.claude/`
(upstream skill packs) and `.venv/` (installed packages). The codon table entry `"GTA": "V"`
in `src/chemlab/genomics/sequence.py` is genetics, not a brand.

## Follow-up (not done — needs a decision)

- Root-level specification `.md` files duplicate `docs/ai/` copies. Consolidating them is a
  documentation-ownership decision, not a code fix.
- `beispiel*.jpg/.avif` are untracked reference images supplied by the project owner;
  intentionally left untouched.
