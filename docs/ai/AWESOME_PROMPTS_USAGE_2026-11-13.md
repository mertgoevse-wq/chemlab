# Awesome-Prompts Analysis and Application — 2026-11-13

**Source:** `ai-boost/awesome-prompts`, vendored at `tools/vendor/awesome-prompts`
**Commit:** `f26786e` (2026-11-13)
**Machine-readable index:** `docs/ai/AWESOME_PROMPTS_INDEX_2026-11-13.json`

---

## 1. What is actually in the repository

| Metric | Count |
|---|---:|
| Markdown + text files in the checkout | 458 |
| Markdown files | 94 |
| Plain-text agent prompts | 364 |
| English prompt-library files | 39 |
| Everyday prompts documented in the library | 3,030 |
| Game-specific prompts in `library/en/games.md` | 71 |
| Named game/agent prompts read in full | 7 |

The repository is not a single prompt pack. It is three layers:

1. **A 3,030-prompt everyday library** (`library/en/*.md`, `library/zh/*.md`) — writing,
   coding, research, business, games. Most entries are one-paragraph chat prompts.
2. **~364 role/system prompts** (`prompts/*.txt`) — long-form agent identities with
   deliverables, workflows and success metrics. These are the useful layer for game work.
3. **Frameworks, papers and agent-ecosystem material** in `README.md` — prompt engineering,
   context engineering, evaluation, security.

**Honest limit:** applying all 3,030 everyday prompts to Athanor is neither possible nor
meaningful — most are for marketing copy, language learning, chess or emoji translation.
What *was* done: a structural index of every file, a full read of the seven game/agent
prompts that map to the project, and a review of all 71 game prompts in `games.md`, each
marked as applied candidate or not applicable in the JSON index.

---

## 2. Prompts used, and what they produced

| Prompt | Framework used | Artifact |
|---|---|---|
| `prompts/Immersive_Narrative_Designer.txt` | vision, worldbuilding, character tiers, player agency, dialogue, implementation hand-off | `design/act_ii_nitrogen_age.md` |
| `prompts/Game_Level_Designer.txt` | spatial architecture, metrics, flow, encounter/challenge taxonomy, accessibility, performance budget | `design/pyrotechnics_bay_layout.md` |
| `prompts/Game_Economy_Designer.txt` | currency architecture adapted to a no-monetisation offline RPG, progression bands, reward pacing, sink analysis | `production/reviews/ECONOMY_AUDIT_2026-11-13.md` |
| `prompts/game_ai_designer.txt` | deterministic simulation over "AI theatre", behaviour budgets, offline-first constraints | `src/chemlab/chemistry/process_state.py`, `src/chemlab/chemistry/pyrotechnics.py`, `game/scripts/labs/pyrotechnics_model.gd` |
| `prompts/game_designer.txt` | mechanic documentation standard (purpose, inputs, outputs, edge cases, failure states) | quest objective and reward fields in `quest_manager.gd` |
| `prompts/game_studio_multi_agent_orchestrator.txt` | work split into analysis → implementation → verification → review | this session's batch order and `production/reviews/*` |
| `prompts/game_asset_sprite_forge.txt` | asset-generation checklist | evaluated and deliberately not used for 3D apparatus; the Blender procedural pipeline already produces game-ready GLBs with consistent scale |

The **71 game prompts** in `games.md` were reviewed as a checklist. 23 were applicable
candidates (game system design, procedural content, physics architecture, level design,
narrative, economy, review, simulation); 48 were not applicable to a hard-science offline
RPG (chess, Gomoku, emoji, football commentary, text-adventure toys, VR chatroom horror,
match-3, snake, etc.). The per-prompt disposition is in the JSON index — no claim is made
that a chess prompt improved the game.

---

## 3. What was built from the analysis

| Work | Evidence |
|---|---|
| Act II narrative bible with cast, beats, dialogue and a three-way disposition fork | `design/act_ii_nitrogen_age.md` |
| Pyrotechnics test-bay level design with metric table, flow, failure states and performance budget | `design/pyrotechnics_bay_layout.md` |
| Quest XP curve audit with tier bands and a documented tier-6 outlier | `production/reviews/ECONOMY_AUDIT_2026-11-13.md` |
| Two Act II quests (nitrogen fixation, ammonia pilot) and four pyrotechnics quests | `game/scripts/quests/quest_manager.gd` |
| Offline process-state model (Antoine, phase, pressure) and pyrotechnics model (oxygen balance, burn rate, flame colour) | `src/chemlab/chemistry/`, 18 Python tests |
| Pyrotechnics laboratory scene and 3D test cell | `game/scenes/laboratories/pyrotechnics_lab.tscn` |
| Detailed 13 apparatus models (bevel, weighted normals, rating plate, LED, screws, cable gland) | `tools/generate_apparatus_models.py`, regenerated GLBs |

---

## 4. Other repositories analysed

| Repository | Commit | Installed | Used for |
|---|---|---|---|
| `Donchitos/Claude-Code-Game-Studios` | `abc0de7`, v1.3.0 | 78 skill folders | review, gate check, quest coherence, tech-debt audit, workflow routing |
| `fcsouza/agent-skills` → `plugins/game-dev` | `a06a4d1` | 25 skills | quest/mission design, narrative coherence, skill progression, game economy, UI review |
| Project-specific | — | 1 skill | Athanor conventions |
| **Total** | | **106 skill folders** | |

The detailed mapping and the explicit list of skills that were installed but intentionally
not wired (server-authoritative multiplayer, matchmaking, Stripe, Redis, analytics) are in
`docs/integrations/SKILLS_INTEGRATION_2026-11-13.md`. Those skills assume an online backend;
Athanor is offline-first, so pretending to use them would be fabrication.

**Skills are working tools, not content:** they were used to review and shape the work
(quest graph checks, economy audit, gate check, code review), not copied into the game as
gameplay systems. That matches the request to use them as agents rather than install them
as features.

---

## 5. Limits and what remains

- 3,030 everyday prompts were indexed, not individually applied. Applying marketing and
  language-learning prompts to a chemistry RPG would produce noise, not content.
- 71 game prompts were reviewed; 23 were applicable. The rest are documented as N/A.
- The three-way Act II disposition fork is designed but not yet a quest objective. It is
  flagged as the next implementation step in `design/act_ii_nitrogen_age.md`.
- Multiplayer, open-world streaming and companion combat remain later milestones. The
  offline simulation and quest graph were prioritised because they are the foundation those
  systems would sit on.

---

## 6. Reproduce

```bash
# Rebuild the machine-readable index
.venv/Scripts/python.exe - <<'PY'
import json, pathlib, re
root = pathlib.Path("tools/vendor/awesome-prompts")
games = (root / "library/en/games.md").read_text(encoding="utf-8")
titles = re.findall(r"<summary><b>([^<]+)</b>", games)
print(len(titles), "game prompts")
PY

# Verify the produced artifacts exist
ls design/act_ii_nitrogen_age.md design/pyrotechnics_bay_layout.md \
   production/reviews/ECONOMY_AUDIT_2026-11-13.md \
   docs/ai/AWESOME_PROMPTS_INDEX_2026-11-13.json
```
