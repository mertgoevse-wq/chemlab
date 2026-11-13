# Skill Packs Integration — CCGS + game-dev

**Date:** 2026-11-13

## What was installed

| Source | Repo | Installed as | Count |
|---|---|---|---|
| Claude Code Game Studios | `Donchitos/Claude-Code-Game-Studios` (main, v1.3.0) | `.claude/skills/<name>` + existing 51 agents | 78 skill folders (4 newly synced: `cut`, `next-step`, `project-settings`, `write-changelog`) |
| game-dev plugin | `fcsouza/agent-skills` → `plugins/game-dev` | `.claude/skills/gamedev-<skill>` | 25 skills |
| Project-specific | this repository | `.claude/skills/chemlab-skill` | 1 |

Total skill folders: **106**. Vendored sources live in `tools/vendor/game-dev/` (sparse
checkout, 25 skill folders) and `Claude-Code-Game-Studios/` (full checkout of `origin/main`).
Both are ignored by the project `.gitignore` where applicable; do not edit them in place.

## How the game-dev skills map onto Athanor

| Skill | Applied to |
|---|---|
| `gamedev-game-design-fundamentals` | reviewed the synthesis → analysis → quest loop |
| `gamedev-quest-mission-design` | verified 97 quest ids and 11 chained `next_quest_id` links |
| `gamedev-quest-narrative-coherence` | checked quest graph for dangling links (0 found) |
| `gamedev-skill-progression-trees` | checked skill caps and XP curve references |
| `gamedev-worldbuilding` | kept faction/lab lore separate from chemistry data |
| `gamedev-ui-ux-game` | reviewed the radial wheel, HUD and bench actuator layout |
| `gamedev-game-economy-design` | XP/item reward fields audited for completeness |
| `gamedev-procedural-gen` | matches the procedural apparatus/bench generation already used |
| `gamedev-game-review` | produced `production/reviews/CODE_REVIEW_2026-11-13.md` |
| `gamedev-claude-code-game-workflow` | used as the routing index for this session |

Skills that assume a **server-authoritative online game** (`game-backend-architecture`,
`matchmaking-system`, `redis-game-patterns`, `bullmq-game-queues`, `stripe-game-payments`,
`betterauth-integration`, `postgres-game-schema`, `gameplay-analytics`, `game-state-sync`,
`elevenlabs-sound-music`, `monitoring-game-ops`, `ci-cd-game`) are installed but intentionally
**not** wired: Athanor is offline-first and has no server in the loop. They remain available
for a future companion/telemetry service.

## How to invoke

- CCGS: `/code-review`, `/gate-check`, `/perf-profile`, `/dev-story`, `/story-done`, …
- game-dev: `/gamedev-quest-mission-design`, `/gamedev-game-review`, …

## Artifacts produced by this integration

- `production/reviews/CODE_REVIEW_2026-11-13.md`
- `production/reviews/DEAD_CODE_AUDIT_2026-11-13.md`
- `production/reviews/GATE_CHECK_2026-11-13.md`
- `docs/blender/BLENDER_MCP.md`

## Note on "use every skill"

There are 106 skills; many are mutually exclusive workflows (for example `hotfix` vs
`launch-checklist`, or Unity/Unreal specialists that do not apply to Godot). Every skill is
installed and discoverable. This session executed the ones that produce evidence for the
current task — review, gate check, tech debt, quest coherence, security, workflow routing —
and recorded the rest as available rather than fabricating outputs for them.
