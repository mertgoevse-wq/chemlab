# ChemLab: Athanor — Game Concept

> **Working title:** ChemLab: Athanor  
> **Genre:** Open-world chemistry simulation RPG / sandbox simulator  
> **Platform:** PC (Godot 4.7.2), headless-capable for CI  
> **Engine:** Godot 4.7.2 (GDScript), gl_compatibility (OpenGL 3.3 / WebGL 2)  
> **Art pipeline:** Blender 5.2 + Photogrammetry (EEVEE Next, Intel Iris Xe budgets: 128 MB VRAM, ≤65 draw calls, 0.67x internal resolution + AMD FidelityFX CAS upscaling)

## 1. Core Fantasy

The player is a chemist-scientist in an open world who rises from a backyard hobbyist to a master alchemist of legal and clandestine chemistry. They learn real techniques — extraction, distillation, neutralization, titration, PCR, NMR interpretation, total synthesis, nuclear reprocessing, genome editing — through quests and sandbox experimentation, build reputation, run criminal labs, investigate crime scenes, and unlock skills across **12–15 specialized skill trees**. The world responds to the player's scientific reputation: universities offer tenure-track positions, cartels recruit for clandestine production, intelligence agencies approach for forensic consultation, and biotech firms compete for synthetic biology breakthroughs.

**Intelligence Points (IP)** serve as a meta-currency earned through quest completion, laboratory activities, and peer-reviewed publications. IP unlocks **perk trees**, **stat upgrades**, **companion slots**, and **laboratory access tiers** — enabling non-linear player progression beyond traditional XP grinding.

## 2. Setting & Scope (Concept only)

Open-world regions (conceptual, not movement mechanics):
- **Safehaven City** — legal labs, universities, pharmacies, police stations, criminal-lab hotspots, biotech incubators, nuclear regulatory commission.
- **Badlands** — covert lab sites, abandoned industrial zones, planetary-preset sandbox biomes (Earth baseline, Mars zero-G, vacuum boiling, Venusian hyperbaric, Titan cryogenic).
- **Orbital Research Station "Apex"** — microgravity chemistry sandbox, protein crystallization, materials science, radiation biology.
- **Athanor Deep Research Sanctum** — endgame autonomous pilot plant, continuous-flow industrial automation, extreme environment sandbox engine.
- **Nuclear Reactor Complex "Ignis"** — fully enterable nuclear power plant and hot cell facility: PUREX reprocessing, radioisotope isolation, decay chain kinetics, Cherenkov radiation visualization, radioluminescence.
- **Genomics Institute "Helix"** — interactive chromosome browser (karyotype → base pair), CRISPR-Cas9 editing, phenotypic simulation (e.g., Trisomy 21), synthetic biology foundry.

## 3. Key Systems (Phase B Expansion)

### 3.1 Skill & Progression System (12–15 Skill Trees)
| Category | Skills |
|----------|--------|
| **Core Sciences** | Chemistry, Biology, Physics, Mathematics |
| **Applied Investigation** | Forensics, Toxicology, Ballistics, Digital Forensics |
| **Engineering & Instrumentation** | Apparatus Building, Lab Safety, Automation, Containment, Nuclear Engineering |
| **Life Sciences** | Genetics, Biochemistry, Pharmacology, Synthetic Biology |
| **Specialized** | Radiochemistry, Environmental Science, Materials Science, Computational Chemistry |

Each skill follows a classic mastery exponential XP curve with 120 max level, soft cap at 100, and 10 rank titles. **Intelligence Points (IP)** are earned separately and spent on talent trees.

### 3.2 Companion & Aetherkin System
Companion creatures providing laboratory support and, later, controlled combat:
- **Working Animals** (unlock Lv. 5–15): Lab Rat (impurity sensing), Instrumented Rat (live toxicity telemetry), Contraband Cat (solvent detection), Search Dog (tracking), Carrier Pigeon (sample courier), Wall Gecko (contamination watch), Lab Axolotl (regeneration model), Archive Raven (notebook recall)
- **Aetherkin** (unlock Lv. 25–75): original alchemical creatures, not a borrowed bestiary. Cinderling (flame stabilisation), Brinejack (desalination), Glasswing Moth (microfracture sensing), Calcine Hound (residue tracking), Mercurial Ferret (spill recovery), Lumen Eel (ROS sensing), Verdant Sloth (plant extraction yield), Obsidian Beetle (radiation shielding), Null Moth (static suppression), Tideglass Serpent (crystal nucleation), Auric Kite (noble-metal sensing), Sable Lynx (night investigation), Halide Newt (halogen leak warning), Xenon Owl (vacuum leak finding), Prism Finch (spectral purity grading), Ferro Snail (magnetic contamination removal)
- **Mythic tier**: Ember Drake (furnace work, molten handling), Chrysalis Warden (one fatal-accident prevention per cycle)
- **Capacity**: 3 companions total (expands to 5 at Lv. 50), max 2 active walking companions
- **Auto-battler**: Companion vs NPC combat is optional and never required for laboratory progression. PvP companion battles are planned for the post-launch online phase (see `docs/ROADMAP.md`) and are not implemented.

### 3.3 Perspective & Navigation
- **Primary**: First-person ego-shooter perspective for tactile, immersive laboratory manipulation
- **Optional**: Third-person toggle (Assassin's Creed / Call of Duty style controls)
- **Dual Control Schemes**: Webcam-based hand tracking (OneEuroFilter, pinch Schmitt triggers) + standard keyboard/mouse

### 3.4 Advanced Genetics & Molecular Biology Lab
- **Real genomic datasets**: Human GRCh38, Mouse GRCm39, model organisms (C. elegans, D. melanogaster, A. thaliana, S. cerevisiae, E. coli K-12)
- **Interactive chromosome browser**: Zoom from whole karyotypes down to individual nucleotide base pairs
- **Simulation**: Point mutations, CRISPR-Cas9 PAM recognition, aneuploidies (e.g., chr21 triplication → simulated Trisomy 21 phenotypic traits)
- **Phenotypic outcome prediction**: Gene expression cascades, metabolic pathway disruption, developmental phenotypes

### 3.5 Comprehensive Synthesis & Unit Operations
Beyond basic APIs (aspirin, paracetamol, caffeine):
- **Natural product extractions**: Alkaloids (caffeine, curcumin, capsaicin, morphine), terpenes (limonene, menthol, artemisinin), flavonoids
- **Crystallization**: Cooling, evaporative, anti-solvent, seeding, fractional, melt
- **Distillation**: Fractional, vacuum, steam, azeotropic, short-path, molecular
- **Chromatography**: Column, TLC, HPLC-DAD, GC-MS, flash, SFC
- **Multi-step total syntheses**: Retrosynthetic analysis, protecting group strategies, chiral resolution

### 3.6 Walkable Nuclear Reactor & Radiochemistry Facility
- **Fully enterable**: Reactor core, turbine hall, control room, spent fuel pool, hot cells, reprocessing plant
- **PUREX cycle**: TBP/n-dodecane solvent extraction, U/Pu partitioning, fission product separation
- **Radioisotope isolation**: Mo-99/Tc-99m generator, I-131, Cs-137, Sr-90, Co-60, Pu-238
- **Decay chain kinetics**: Bateman equations, secular/transient equilibrium, activity calculations
- **Ephemeral elements**: Francium (relativistic DFT predictions), Astatine (halogen/metalloid properties), Cherenkov blue glow, uranyl salt green fluorescence, radioluminescence

### 3.7 AI-Powered Real-Time Physics & Reaction Bridge
- **Google AI Pro / Claude APIs** via Google Media Bridge / OmniRoute
- **Real-time physical simulation**: Fluid dynamics, heat transfer, reaction-diffusion
- **Realistic reaction appearance**: Color transitions, precipitation morphologies, gas evolution, phase separation
- **Dynamic stoichiometry prediction**: RL-guided retrosynthesis, yield optimization

### 3.8 Google Flow Music & Atmospheric SFX
- **Adaptive generative background music**: Streaming via Google Flow Music / Media Bridge, seamless stem cross-fading, loop without interruption
- **Procedural sound effects**: Glassware clinks, bubbling, vacuum pumps, Geiger counters, centrifuge whine, magnetic stirrer hum, fume hood airflow

### 3.9 Addictive Gameplay Loops (Psychological Engagement)
- **Discovery dopamine**: New reagent unlocks, spectral peak identification, "first synthesis" moments
- **Codex completion**: Reagent encyclopedia, synthesis recipe book, organism genome atlas, isotope chart
- **Micro feedback loops**: Pour → observe → measure → adjust (seconds)
- **Macro feedback loops**: Plan → execute → analyze → publish → reputation gain (hours)
- **Prestige systems**: New Game+ with retained IP, laboratory legacy, mentor apprentices

### 3.10 Live Development MCP Connection
- **ChemLab MCP Server**: Real-time game state inspection, hot-reload scripts, scene graph visualization, reaction debugger, variable watch

### 3.11 Target Hardware Constraints
- **Dell Latitude 5530**: Intel Core i5/i7, 16 GB RAM, Intel Iris Xe Graphics
- **VRAM Budget**: 128 MB (Draco-compressed meshes, texture atlasing, shader LODs)
- **Performance Target**: 60 FPS, ≤65 draw calls, 0.67x internal render resolution + AMD FidelityFX CAS upscaling

## 4. Educational Intent

Every synthesis in-game mirrors a real procedure with authentic stoichiometry, safety (GHS, fume hood, neutralization drills), and analytical verification. The simulator is a teaching aid first, entertainment second. No real-world hazardous instructions are rendered outside the fictional simulator context. Players gain genuine laboratory competence transferable to real wet-lab work.

## 5. Naming Proposals

1. **ChemLab: Athanor** (proposed — the alchemical furnace, symbol of transformation)
2. **ChemLab: Origins** (current placeholder)
3. **Reagent & Ruin**
4. **The Synthesis Simulator**
5. **Labcraft**
6. **ChemWorld**
7. **Athanor Chronicles**
8. **Elemental Ascension**

## 6. Open Questions for the User

1. Preferred title from the list above, or a new suggestion?
2. How much real procedural detail should be visible vs. abstracted for gameplay?
3. Any regions, lab types, or synthesis targets you want prioritized?
4. Companion system: Should mundane animals be captured/tamed or purchased/unlocked?
5. Nuclear facility: Emphasize power generation or radiochemistry/isotope production?
6. Genetics lab: Focus on human medical genetics or broader synthetic biology?
7. IP economy: Should IP be tradeable between players (future multiplayer) or strictly single-player?

---

## 7. Phase B Implementation Roadmap

### Phase B-1: Core Systems Expansion (Weeks 1-3)
- [ ] Overhaul `skills.json` → 12–15 skill trees with IP integration
- [ ] Create `companions.json` data model
- [ ] Implement `IntelligencePoints` GDScript autoload
- [ ] First-person camera controller with hand tracking bridge

### Phase B-2: Simulation Engine Deepening (Weeks 3-6)
- [ ] `analytical_engine.py`: NMR, GC-MS, HPLC-DAD, balance, buret, pH meter
- [ ] `genetics_engine.py`: PCR cycling, gel electrophoresis, Sanger, CRISPR, chromosome browser
- [ ] `nuclear_engine.py`: Bateman decay, PUREX, radiation attenuation, Cherenkov shader
- [ ] `radioactive_catalog.py`: 200+ isotopes, decay chains, relativistic properties

### Phase B-3: Content & Worldbuilding (Weeks 6-9)
- [ ] Synthesis protocols expansion: natural products, crystallization, distillation variants
- [ ] Genomic database integration: GRCh38, GRCm39, model organisms
- [ ] Nuclear facility 3D layout + hot cell mechanics
- [ ] Companion AI: buffs, auto-battler, evolution

### Phase B-4: Polish & Integration (Weeks 9-12)
- [ ] Google Flow Music bridge + spatial SFX system
- [ ] ChemLab MCP server for live development
- [ ] Iris Xe profiling: shader optimization, draw call reduction, VRAM budgeting
- [ ] Playtest analytics: retention funnels, skill progression curves, companion engagement

---

*Document Version: 2.0.0 | Phase B Specification | 2026-11-04*