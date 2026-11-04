# Athanor Ascension — Roadmap & Platform Plan

**Status date:** 2026-11-04  
**Engine:** Godot 4.7.2 (Compatibility renderer)  
**Art pipeline:** Blender 5.2 → glTF 2.0

This is the working plan, not a marketing page. Items are marked **LIVE**, **PARTIAL** or **BLUEPRINT**.

## 1. What is LIVE now

| System | Where | State |
|---|---|---|
| Loading window with animated sigil and apparatus backdrop | `game/scenes/loading/` | LIVE |
| Main menu with research terminals | `game/scenes/main_menu/` | LIVE |
| Laboratory Network hub (15 archetypes, 14 suits) | `game/scenes/laboratories/lab_hub.gd` | LIVE (index + equipment logic) |
| Interactive genome archive (karyotype → base view) | `game/scenes/genomics/` | LIVE |
| Point mutations with curated HGVS/protein/phenotype output | `game/scripts/genomics/genome_simulation.gd` | LIVE |
| Chemical mutagen exposure with real mutation spectra | same | LIVE |
| Chromosome dosage model (trisomy/monosomy) | same | LIVE |
| Aspirin synthesis (stoichiometry, reflux, workup, assay) | `game/scenes/laboratories/synthesis_lab.gd` | LIVE |
| Relativistic beam physics + activation terminal | `game/scenes/laboratories/accelerator_lab.gd` | LIVE |
| Fusor build checklist + plasma/neutron/dose model | `game/scenes/laboratories/fusor_lab.gd` | LIVE |
| Player health, injuries, chemical and radiation dose | `game/scripts/core/player_vitals.gd` | LIVE |
| 3D analytical bench (walkable) | `game/scenes/laboratories/analytical_lab.tscn` | PARTIAL |
| Aetherkin companions (26 species, data-driven) | `game/data/companions/species_database.json` | LIVE data, PARTIAL runtime |
| Chemistry core (256 Python tests) | `src/chemlab/`, `chemlab_core/` | LIVE offline |
| Data-driven skill tracks, XP curve, milestone unlocks | `game/scripts/progression/skill_manager.gd` | LIVE |
| Skill codex (levels, milestone ladder, unlock ledger) | `game/scenes/progression/` | LIVE |
| Titration practicum (real charge-balance pH, endpoint scoring) | `game/scenes/laboratories/titration_practicum.gd` | LIVE |

## 2. Laboratories

Fifteen archetypes are specified in `game/data/labs/labs.json`:

teaching, analytical instrument, organic synthesis, electrochemistry, genomics,
cell culture, radiochemistry hot cell, accelerator, fusor/plasma, materials &
metallurgy, cleanroom fabrication, industrial pilot plant, forensic toxicology,
orbital microgravity, cryogenic & vacuum.

**LIVE terminals:** analytical (3D bench), genomics, accelerator, fusor, organic synthesis (aspirin).<br>
**Next to fit out:** electrochemistry, cell culture, radiochemistry, materials,
cleanroom, pilot plant, forensic, orbital, cryogenic.

Each remaining lab needs, in this order:
1. A terminal scene driven by physical quantities (not a static menu).
2. One real unit operation with a measurable outcome.
3. Failure modes that teach the actual constraint (thermal runaway, contamination,
   criticality, vacuum loss, aseptic breach).
4. Blender set dressing only after the interaction is correct.

## 3. Suits and protection

Fourteen suits in `labs.json`, each with protection and penalty vectors. The hub
already applies an averaged protection factor to `PlayerVitals`. Still needed:
per-hazard mitigation (chemical vs thermal vs radiological), mobility penalties
that change interaction speed, and suit breach events.

## 4. Genome browser

Implemented: zoomable karyotype, curated gene spans, hotspot edits, VUS handling,
mutagen spectra, dosage model, phenotype aggregation.

Next:
- transcript/exon track (needs a real GTF subset, not invented coordinates)
- CRISPR guide search with PAM and off-target scoring
- variant import (VCF) with population frequency context
- save/load of edited genomes (already serialisable in `save_data`)

## 5. Companions / Aetherkin

26 species are in the data file: 8 working animals and 18 original Aetherkin,
including two mythic tiers. The runtime (`companion.gd`, `companion_manager.gd`)
still needs:
- species portraits and 3D/idle assets
- ability execution hooks that actually change lab outcomes
- care decay balancing and evolution VFX

PvP companion battles are **NOT implemented**. The data model keeps `battle_role`
and `battle_abilities` so a later online phase can use them. Do not advertise PvP
until netcode, anti-cheat and server authority exist.

## 6. Nintendo Switch

Switch is a **target platform, not a current build target**. Godot's Switch export
requires the Nintendo SDK under NDA; it is not downloadable with the public editor.

Engineering constraints to respect now so the port stays possible:
- Renderer already `gl_compatibility`; keep it.
- No webcam dependency in the critical path: mouse/keyboard and gamepad must
  remain first-class (Switch has no webcam).
- UI must be readable at 1280×720 handheld and scale to 1920×1080 docked.
- Target ≤ 3.2 GB RAM and ≤ 1 GB texture budget; current asset budget is lower.
- All new interactions need a gamepad mapping (the current player controller has
  keyboard/mouse only for some actions).
- No runtime network calls for core simulation: everything is offline.

## 7. Online / PvP (planned, not built)

If it happens: server-authoritative economy, no client-trusted mutation results,
separate PvP profile so story progress cannot be gamed, and no real hazardous
synthesis instructions in user-generated content. Until then, keep all state local.

## 8. Build-time media generation (Google AI Pro)

The project treats Nano Banana / Veo / Flow Music as **build-time tools only**:
generated files are imported as ordinary assets, and the game never calls Google
services at runtime. Prompts and negative prompts live in
`docs/ASSET_PROMPTS.md`; expected paths and fallbacks live in
`game/data/media/manifest.json`.

Important: this development environment has no browser automation into a Google
account, so no images or videos were generated here. The prompts are ready to run
manually, and the manifest tells the importer exactly where each file goes.
