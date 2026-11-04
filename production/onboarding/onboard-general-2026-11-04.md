# Onboarding: General Orientation

## Project Summary
ChemLab is an interactive virtual chemistry lab (Blender 5.2 + MediaPipe hand tracking + Python simulation). Codebase mixes a Python package (`chemlab_core`, `src/chemlab`), a Godot game (`game/`), tests (`tests/`), and documentation. No root CLAUDE.md present (framework note: CLAUDE.md ships with framework install — report as missing). 44 tests, 34 src modules, 18 chemlab_core modules.

## Your Role
General contributor. Pick a focused role (`/onboard programmer|designer|qa|...`) for a deeper pass.

## Project Architecture
- Code roots: `chemlab_core/` (core contracts, blender, chemistry, transport, vision), `src/chemlab/` (ai, cv, simulation, skills, story, synthesis, graphics, media, companion, desktop, sandbox), `game/` (Godot), `tests/`.
- Docs: `docs/` (architecture, audits, integrations), root `*.md` specs.
- Agents: `.claude/agents/` (game-director, graphics-lead-blender, input-specialist-cv, physics-lead-chemistry, qa-balancing-lead).
- Skills: `.claude/skills/` (adopt, architecture-decision, ... onboard, etc.) plus vendored game-studios.

### Key Directories
| Directory | Contents | Your Interaction |
|-----------|----------|------------------|
| chemlab_core | Core contracts & engines | Read for architecture |
| src/chemlab | Feature modules | Primary code |
| game | Godot project | UI/scene work |
| tests | pytest suite (44 files) | Run before changes |
| docs | Specs & audits | Reference |
| production | (absent) | Create onboarding here |

### Key Files
| File | Purpose | Read Priority |
|------|---------|--------------|
| README.md | Project overview | High |
| pyproject.toml | Build/test config | High |
| docs/ARCHITECTURE.md | Architecture | High |
| docs/CURRENT_STATE_AUDIT.md | State audit | Medium |

## Current Standards and Conventions
- Python 3.12, Black (line 100), Ruff, mypy strict. pytest. pnpm/npm per global config.
- Conventional commits. Tests first.

## Current State of Your Area
- No `production/` directory existed (created for this doc). No `design/` directory. No session-state. Git clean on main. Recent commits: GHS hazard fix, skills integration, reagent DB consolidation, skill/quest system, ruff fixes.

## Current Sprint Context
Not assessed — no sprint data present (no production/sprint-status).

## Key Dependencies
- Blender 5.2, MediaPipe, OpenCV, numpy, websockets, Godot.

## Common Pitfalls
- No root CLAUDE.md; framework agents/skills live under `.claude/`.
- Mixed Python roots (`.` and `src`) in pythonpath.

## First Tasks
1. Read README.md and docs/ARCHITECTURE.md.
2. Run `pytest` to establish baseline.
3. Pick a role and run `/onboard <role>`.

## Questions to Ask
- Which role/area should I focus on?
- Is there a sprint plan or milestone doc?