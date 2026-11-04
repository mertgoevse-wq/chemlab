---
name: chemlab-skill
description: Master skill that bundles every available skill (74 claude-code-game-studios + natprd PRD Maker + 3 ChemLab-specialized: design-system, dev-story, story-done) and auto-loads all of them when started. Use as the single entry point for all ChemLab project work.
argument-hint: "[command: list | load | status]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
model: sonnet
---

# /chemlab-skill — Master Skill Bundle for ChemLab

This skill bundles **all available skills** in one entry point. When started, it auto-loads every skill in `.claude/skills/` so the full skill suite is active for any ChemLab task.

## Skills bundled (82 total)

**claude-code-game-studios (74):**
adopt, architecture-decision, architecture-review, art-bible, asset-audit, asset-spec, balance-check, brainstorm, bug-report, bug-triage, changelog, code-review, consistency-check, content-audit, create-architecture, create-control-manifest, create-epics, create-stories, design-review, estimate, gate-check, help, localize, map-systems, milestone-review, onboard, patch-notes, perf-profile, playtest-report, project-stage-detect, propagate-design-change, prototype, qa-plan, quick-design, regression-suite, release-checklist, retrospective, reverse-document, review-all-gdds, scope-check, security-audit, settings, setup-engine, skill-improve, skill-test, smoke-check, soak-test, sprint-plan, sprint-status, start, story-readiness, team-audio, team-combat, team-level, team-live-ops, team-narrative, team-polish, team-qa, team-release, team-ui, tech-debt, test-evidence-review, test-flakiness, test-helpers, test-setup, ux-design, ux-review, vertical-slice

**ChemLab-specialized (3):**
design-system, dev-story, story-done

**PRD Maker (1):**
natprd

**Master bundle (1):**
chemlab-skill

## Auto-load behavior

When `/chemlab-skill` is started:

1. Scan `.claude/skills/` for every skill directory (each containing a `SKILL.md`).
2. Load each skill's `SKILL.md` into context so the skill suite is fully active.
3. Report the list of loaded skills and any that failed to load.
4. Remain ready to delegate to any skill on demand based on the task at hand.

## Commands

| Command | Effect |
|---------|--------|
| (none / default) | Auto-load all skills and report readiness |
| `list` | Print every bundled skill with its one-line description |
| `status` | Confirm which skills are loaded and active |

## How to use

Start `/chemlab-skill` at the beginning of any ChemLab session. It loads the full suite; after that, invoke individual skills by name (e.g. `/brainstorm`, `/natprd`, `/dev-story`, `/design-system`, `/story-done`, `/gate-check`, `/setup-engine`, etc.) as the task requires.

Skills are additive — starting this bundle never removes or overrides any skill, including the ChemLab-specialized ones (design-system, dev-story, story-done).

## Skill file references

Each skill lives at `.claude/skills/<name>/SKILL.md` with optional `scripts/`, `references/`, and `assets/` subdirectories. See the skill-creator skill for the skill authoring format.

## Related

- `skill-creator` — authoring format for individual skills
- `natprd` — PRD Maker skill (bundled)
- `design-system`, `dev-story`, `story-done` — ChemLab-specialized skills (bundled, preserved locally)
