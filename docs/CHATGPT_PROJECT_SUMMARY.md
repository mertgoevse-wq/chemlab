# ChemLab — Project Summary for ChatGPT

**Project:** ChemLab — Interactive Virtual Chemistry Laboratory  
**Repository:** https://github.com/mertgoevse-wq/chemlab.git  
**Status:** Active development (Pre-Production / Vertical Slice phase)  
**Last Updated:** 2026-11-03  
**License:** MIT

---

## 1. What ChemLab Is (in one paragraph)

ChemLab is a virtual chemistry laboratory: a 3D interactive lab simulation where the player mixes chemicals, runs real chemical reactions (acid-base neutralization, oscillating Briggs-Rauscher clock reactions, foam eruptions, precipitation, chemiluminescence), follows a 10-level story campaign from "Trainee" to "Master Alchemist," and experiments freely in an unlimited sandbox mode with 100+ reagents. It runs as a Python simulation core (desktop GUI + headless tests) plus a Godot 4 3D game client, controlled by webcam hand tracking (MediaPipe) with full mouse/keyboard fallback. Target hardware is a Dell Latitude 5530 with Intel Iris Xe integrated graphics, tuned for 60 FPS @ 1080p.

---

## 2. Project Structure

```
chemlab/
├── README.md                 # German-language project overview
├── pyproject.toml            # Python package config (chemlab v1.0.0, Python >=3.12)
├── launch_chemlab.bat        # Windows launcher
├── launch_chemlab.sh         # Linux launcher
├── chemlab.blend             # Blender 5.2 source scene (DCC asset pipeline)
├── blender_mcp_server.mjs    # Blender MCP bridge
├── blender_client.py
├── blender_live_bridge.py
├── gallery.html              # HTML/JS live reaction visualizer dashboard
├── audio/                    # Procedural SFX (WAV)
├── scripts/                  # Blender Python asset pipeline + Godot HUD (GDScript)
│   ├── chemlab_hud.gd
│   ├── module_apparatus.py
│   ├── module_room.py
│   ├── module_furniture.py
│   ├── module_fluid_simulation.py
│   ├── module_fume_safety.py
│   ├── module_ui_hud.py
│   ├── build_hud.py
│   ├── generate_sfx.py
│   ├── render_hud_gallery.py
│   └── run_quality_gate.py
├── docs/                     # 14 specification documents (see section 4)
├── chemlab_core/             # Legacy/isolated core: Pydantic models, IPC transport, Blender bridge, vision
│   ├── models.py             # GestureType, HandLandmarkFrame, IPCRequest/Response, ReactionState
│   ├── chemistry/reaction_engine.py   # Briggs-Rauscher oscillator (3-phase sigmoid)
│   ├── transport/            # TCP socket server/client + JSON framing
│   ├── blender/              # Blender scene controller & commands
│   └── vision/               # Gesture classifier, synthetic landmarks
├── src/chemlab/              # Modern packaged Python feature set (pyproject packages `src`)
│   ├── models.py             # ChemicalReagent, LiquidMixture, GHSHazard, SimulationState
│   ├── desktop/main_window.py        # PySide6 Qt6 dark-themed cleanroom GUI
│   ├── simulation/           # Cantera thermodynamics, RDKit 3D conformers, reaction solver,
│   │   │                     # side reactions, total syntheses, precursor pathways,
│   │   │                     # reagent registry, time controller
│   │   ├── cantera_engine.py     # NIST/CRC thermodynamics, Arrhenius, titration curves
│   │   ├── rdkit_engine.py       # SMILES→3D conformer, ETKDGv3, UFF, PDB/SDF export
│   │   ├── reaction_solver.py    # mix_liquids, step_simulation, thermal relaxation
│   │   ├── side_reactions.py     # Impurity/byproduct engine (aspirin, paracetamol, acetanilide)
│   │   ├── total_syntheses.py    # Aspirin, paracetamol, caffeine, indigo, benzocaine
│   │   ├── precursor_synthesis.py # 5 precursor pathways (benzaldehyde, salicylic acid, etc.)
│   │   └── reagents.py           # ~16-reagent registry
│   ├── cv/                   # MediaPipe hand tracking, holistic pose, 1-Euro filter
│   ├── story/story_manager.py      # 10-level story progression (PlayerRank, QuestStatus)
│   ├── synthesis/guided_wizard.py  # Guided synthesis wizard
│   ├── world/lab_taxonomy.py       # 11 lab archetypes (BSL-1 to orbital microgravity)
│   ├── world/procedural_labs.py    # Procedural facility generator
│   ├── companion/remote_server.py  # Mobile WebSocket companion (port 8766, PWA in German)
│   ├── sandbox/no_mans_sky_matrix.py # NMS planetary env matrix (gravity, pressure, temp, time-warp)
│   ├── ai/omniroute_bridge.py      # Multi-provider AI bridge (Omniroute → NIM → Gemini → local floor)
│   ├── ai/reagent_computer.py      # AI reagent computer (local/remote LLM fallback)
│   └── media/google_media_bridge.py # Google Gemini bridge
├── simulation/               # Root-level free simulation facade (disconnected from packaging)
│   ├── catalog.py            # 100+ reagent catalog (Reagent dataclass, GHS pictograms)
│   ├── consequence.py        # ConsequenceEngine.mix() reaction matrix
│   ├── free_sim_engine.py    # FreeSimulationEngine (sandbox orchestrator)
│   └── experiment_book.py    # Recipe/JSON export, snapshot photos
├── safety_simulation/        # Safety subsystems (fume hood, thermal runaway, GHS, neutralization drill)
│   ├── fume_hood.py          # ANSI/AIHA Z9.5 face velocity & containment
│   ├── thermal_runaway.py    # Semenov explosion criterion, Antoine vapor pressure
│   ├── ghs.py                # 25 GHS chemical profiles
│   ├── neutralization_drill.py
│   └── safety_officer_engine.py
├── storage/                  # Asset cache (SQLite CAS), cloud sync stubs, schema.sql
│   ├── asset_cache.py
│   ├── cloud_sync.py
│   ├── local_store.py
│   └── schema.sql
├── game/                     # Godot 4 game directory (project scaffolding in progress)
├── tests/                    # ~42 test modules, 214 passing tests
│   ├── test_reaction_engine.py, test_reaction_solver.py, test_story_mode.py
│   ├── test_cantera_engine.py, test_rdkit_engine.py, test_total_syntheses.py
│   ├── test_side_reactions.py, test_free_sim.py, test_companion_remote.py
│   ├── test_hand_tracker.py, test_anti_ai_slop_audit.py, ... etc
├── node_modules/, package/   # Blender MCP addon + Playwright (dev tooling)
└── *.blend1, preview_*.png   # Blender autosaves + preview screenshots
```

> **Note on duplication:** The codebase currently has several parallel module trees (`chemlab_core/`, `src/chemlab/`, `simulation/`, `safety_simulation/`, `storage/`) that duplicate models, reagent catalogs, and reaction engines. This is documented technical debt (see `docs/CURRENT_STATE_AUDIT.md`). Consolidation into a single canonical `chemistry/` package is Phase 3 of the roadmap.

---

## 3. Core Systems & What Each Does

### 3.1 Reaction & Simulation Engines

| Module | Purpose |
|--------|---------|
| `simulation/consequence.py` | `ConsequenceEngine.mix()` — evaluates arbitrary reagent mixtures in specific vessel environments (main bench, fume hood, glove box, etc.). Detects oscillation (Briggs-Rauscher), explosion (KMnO₄+H₂SO₄), neutralization, endothermic dissolution, precipitation (AgCl, PbI₂ "golden rain", Cu(OH)₂), gas evolution (CO₂ from carbonates, H₂ from Zn+acid). Returns temperature deltas, precipitate mass, gas volume, safety report. |
| `src/chemlab/simulation/reaction_solver.py` | `mix_liquids()` and `step_simulation()` — discrete reaction heuristics for HCl+NaOH, H₂O₂+KI foam, Briggs-Rauscher, PbI₂ precipitation, luminol chemiluminescence; thermal relaxation toward 22°C ambient. |
| `chemlab_core/chemistry/reaction_engine.py` | `BriggsRauscherOscillator` — 3-phase sigmoid-smoothed color cycle (Clear → Amber → Deep Blue) with temperature tracking. |
| `simulation/free_sim_engine.py` | `FreeSimulationEngine` — sandbox orchestrator tying catalog, consequence, time controller, and experiment book together; `run_experiment`, `capture_snapshot`, `export_current_setup_as_recipe`. |
| `simulation/experiment_book.py` | `ExperimentBook`, `Recipe`, `SnapshotPhoto`, `ReagentAddition` — save/load/export recipes as JSON; take snapshots with camera angle + visual state. |
| `simulation/time_controller.py` | `TimeScale` enum (PAUSE 0.0, SLOW_MOTION 0.5, NORMAL 1.0, 2x–50x); `TimeController` with pause/resume, `update(dt)` → sim_dt, step_frame, reset. |

### 3.2 Thermodynamics & Kinetics

| Module | Purpose |
|--------|---------|
| `src/chemlab/simulation/cantera_engine.py` | Pure-Python NIST/CRC thermodynamics (no heavy C++ Cantera binding needed). 40+ species with ΔH°f, S°, Cp, density. Hess's Law ΔH/ΔS, Gibbs ΔG, van 't Hoff K_eq (clamped exponents), Arrhenius k(T), half-life, adiabatic temperature rise, Henderson-Hasselbalch titration curves. |
| `src/chemlab/simulation/side_reactions.py` | `SideReactionAnalyzer` — impurity severity (NEGLIGIBLE→CRITICAL). Water-into-acid inversion hazard; aspirin/paracetamol/acetanilide acylation defects (NAPQI, azobenzene, tarring); melting-point depression. |

### 3.3 Cheminformatics & 3D Molecules

| Module | Purpose |
|--------|---------|
| `src/chemlab/simulation/rdkit_engine.py` | `RDKitCheminformaticsEngine` — SMILES→3D molecule via ETKDGv3 distance geometry, UFF minimization (500 iterations), PDB/SDF export, Lipinski Rule of 5 descriptors (MW, LogP, TPSA, HBD/HBA, rotatable bonds, aromatic rings). |

### 3.4 Reagent Catalogs

| Module | Purpose |
|--------|---------|
| `simulation/catalog.py` | `ReagentCatalog` — 100+ `Reagent` entries across 8 categories (acids, bases, transition metal salts, indicators, oxidizers, organic solvents, reducing agents, misc). Each with formula, molar mass, density, color RGBA, GHS pictograms, mp/bp, pKa, solubility, uses, storage, hazard statements. `filter_by_category`, `search`, `get_by_id`. |
| `src/chemlab/simulation/reagents.py` | ~16-reagent `REAGENT_REGISTRY` with `get_reagent()`. |
| `safety_simulation/ghs.py` | 25 `ChemicalProfile` GHS entries. |

### 3.5 Story / Progression (10 Levels)

`src/chemlab/story/story_manager.py` — `StoryProgressionManager`:
- `PlayerRank`: TRAINEE (Labor-Praktikant) → APPRENTICE → JOURNEYMAN → SENIOR_SYNTHESIST → MASTER_ALCHEMIST (Meister-Alchemist)
- `QuestStatus`: LOCKED / IN_PROGRESS / COMPLETED
- 10 levels: Labortaufe & Indikator (HCl+NaOH neutralization, pH 6–8), Die Iod-Uhr (H₂O₂+KI+starch), Oszillierende BZ-Reaktion (malonic acid + KIO₃ + MnSO₄), Thermische Destillation (water→ethanol), Goldener Regen (PbI₂ precipitation, fume hood), Chemisches Leuchten (luminol chemiluminescence), Thermische Sicherheitskontrolle (thermal runaway mitigation), Katalytische Elefanten-Zahnpasta (H₂O₂+KI foam), Briggs-Rauscher Oscillator, Meister-Alchemist (full sandbox)
- `submit_reaction_result()` validates reagents, pH, fume-hood requirement; `unlock_all_for_sandbox()` clears all levels.
- German-language feedback and safety-score penalties (−25 per fume-hood violation).

### 3.6 Computer Vision & Input

| Module | Purpose |
|--------|---------|
| `src/chemlab/cv/hand_tracker.py` | MediaPipe Hands — 21 3D landmarks; gestures: Pinch, Grab, Fist, Pour (>38° tilt), Swirl, Point, Release. |
| `src/chemlab/cv/holistic_tracker.py` | MediaPipe Holistic — 33 skeletal landmarks; knee lifts → walking locomotion, hip shifts → workstation switching, arm extensions → shelf interaction. |
| `src/chemlab/cv/one_euro_filter.py` | Casiez et al. 1-Euro adaptive low-pass filter on (x,y,z) — jitter attenuation without phase lag. |
| `chemlab_core/models.py` | `GestureType`, `Handedness`, `NormalizedLandmark`, `HandLandmarkFrame`, `GestureEvent` — Pydantic v2 frozen domain models. |
| `chemlab_core/vision/` | Vision contracts, gesture classifier, synthetic landmark generator (for headless tests). |

### 3.7 AI & Reasoning

| Module | Purpose |
|--------|---------|
| `src/chemlab/ai/omniroute_bridge.py` | Multi-provider fallback chain: Local Omniroute (127.0.0.1:20128) → NVIDIA NIM → Google Gemini → local deterministic analytical floor. Circuit breaking with cooldowns (30s connection failure, 10min quota exhaustion). |
| `src/chemlab/ai/reagent_computer.py` | AI reagent computer — natural-language chemistry Q&A with offline heuristic fallback. |
| `src/chemlab/media/google_media_bridge.py` | Google Gemini 2.5 Pro bridge with markdown fence stripping, exponential backoff, offline fallback. |

### 3.8 Desktop GUI & Companion

| Module | Purpose |
|--------|---------|
| `src/chemlab/desktop/main_window.py` | PySide6 (Qt6) dark high-tech cleanroom GUI. Tabs: World Laboratories (11 archetypes), Kinetics & Thermodynamics (Cantera + QPainter titration canvas), RDKit 3D (SMILES→3D, PDB/SDF), Blender Live Bridge (TCP 127.0.0.1:9876). |
| `src/chemlab/companion/remote_server.py` | `CompanionRemoteServer` (port 8766) — WebSocket/FastAPI mobile companion. Streams telemetry (temp, pH, stir RPM, workstation, safety score), remote actions (heat/cool/stir/switch_station/emergency_wash), NMS planetary env params, rendered HTML PWA in German. |
| `chemlab_core/transport/` | Threaded TCP server/client with JSON IPCRequest/IPCResponse framing. |

### 3.9 World / Sandbox / Safety

| Module | Purpose |
|--------|---------|
| `src/chemlab/world/lab_taxonomy.py` | 11 lab archetypes across BSL-1 to BSL-4 containment (academic, analytical, medicinal, BSL containment, solid-state materials, electrochemistry, industrial pilot, forensic, mobile HazMat, clandestine, orbital microgravity). |
| `src/chemlab/world/procedural_labs.py` | Procedural facility generation: layouts, equipment degradation, contamination tiers, NPC scientists with dialogue + trade inventories, narrative questlines. |
| `src/chemlab/sandbox/no_mans_sky_matrix.py` | NMS planetary environment matrix — gravity (0–2g), pressure (0.1–10 atm), temperature, time-warp acceleration, Antoine-equation boiling-point shifts. |
| `src/chemlab/synthesis/guided_wizard.py` | Guided synthesis wizard. |
| `src/chemlab/simulation/total_syntheses.py` | 5 total-synthesis protocols: aspirin, paracetamol, caffeine extraction, indigo dye, benzocaine. Stages: reflux, ice-bath quench, vacuum filtration, recrystallization, sublimation; `theoretical_yield_g()`. |
| `src/chemlab/simulation/precursor_synthesis.py` | 5 precursor pathways: benzaldehyde from toluene, Kolbe-Schmitt salicylic acid, Victor Meyer nitroethane, 4-aminophenol, Fischer indole. |
| `safety_simulation/fume_hood.py` | ANSI/AIHA Z9.5 fume hood aerodynamics — face velocity v = Q/A, bypass airflow. |
| `safety_simulation/thermal_runaway.py` | Semenov thermal explosion criterion, Antoine vapor pressure, stopper-pop projectile kinematics. |
| `safety_simulation/safety_officer_engine.py` | Real-time OSHA compliance safety officer. |
| `safety_simulation/neutralization_drill.py` | Neutralization drill scenario. |

### 3.10 Storage & Asset Pipeline

| Module | Purpose |
|--------|---------|
| `storage/asset_cache.py` | SQLite content-addressable storage cache with LRU eviction. |
| `storage/cloud_sync.py` | Cloud sync stubs. |
| `storage/local_store.py` / `schema.sql` | Local data store + SQL schema. |
| `scripts/module_apparatus.py` | Procedural Blender glassware generation (beakers, flasks, cylinders). |
| `scripts/module_room.py` / `module_furniture.py` | Blender environment/furniture builders. |
| `scripts/module_fluid_simulation.py` | Mantaflow fluid physics + Beer-Lambert absorption. |
| `scripts/module_fume_safety.py` / `module_ui_hud.py` | Fume safety + UI HUD modules. |
| `scripts/chemlab_hud.gd` | Godot 4 HUD controller (CanvasLayer: quest title, progress bar, safety badge, pH needle, spatial labels, SFX). |
| `scripts/generate_sfx.py` | Procedural 44.1 kHz SFX synthesizer (pinch, hover, grip, safety alarm, fanfare). |
| `scripts/run_quality_gate.py` | One-command quality gate (tests + lint + type-check). |

### 3.11 Blender / DCC Pipeline

- `chemlab.blend` — Blender 5.2 EEVEE Next source scene (borosilicate glass IOR 1.474, PBR materials, 11 apparatus types, cleanroom environment).
- `blender_mcp_server.mjs` + `blender_client.py` / `blender_live_bridge.py` — Blender MCP bridge for agentic scene control (TCP 127.0.0.1:8765).
- `chemlab_core/blender/` — Blender scene controller, contracts, script builder.
- Blender is strictly a development-time DCC tool; exported GLB/glTF assets feed the Godot runtime (never a runtime dependency).

---

## 4. Specification Documents (`docs/`)

| Document | Focus |
|----------|-------|
| `ARCHITECTURE.md` | Target standalone game architecture: Godot 4 Compatibility Renderer, unified `chemistry/` core, tracking + intelligence daemons, IPC contracts, hardware budgets for Iris Xe. |
| `CURRENT_STATE_AUDIT.md` | Phase 0 codebase audit: 214 tests passing, duplication analysis, packaging flaw (pyproject only packages `src/`), hardware bottleneck analysis (Iris Xe VRAM, thermal throttling), scientific validity table, reuse/relocation plan. |
| `DEVELOPMENT_PROGRESS.md` | 10-phase autonomous roadmap ledger; Phase 0 & 1 complete, Phase 2 (playable 3D vertical slice) in progress; quality gates (214 tests, zero Ruff errors, anti-AI-slop AST suite); bug tracker (BUG-001..004) and risk register (RSK-01..04). |
| `GAME_DESIGN_DOCUMENT.md` | Full GDD: vision, hardware, visual direction (cleanroom palette, borosilicate IOR 1.474, Beer-Lambert absorption), gameplay loops, 5 vertical-slice apparatuses, mode specs (sandbox + story), UI/HUD, progression, technical architecture, asset/performance budgets. |
| `STORY_AND_QUESTS.md` | Narrative & quest design: Kavli-Helmholtz Institute setting, characters (Dr. Vance, Prof. Thorne, Julian Voss / Project Athanor anomaly), 5-discipline skill tree, JSON quest schema, 5 vertical-slice quests with quantitative tolerances, dialogue trees, audio logs, verification test matrix. |
| `INTEGRATIONS_REGISTRY.md` | Dependency & licensing audit: Godot (MIT), Blender (GPL-3.0, DCC-only), RDKit/Cantera/NumPy/SciPy (BSD), MediaPipe/OpenCV (Apache), PySide6 (LGPL), AI providers (Gemini/NIM/local), Steam distribution compliance, biometric privacy, copyleft isolation firewall. |
| `PERFORMANCE_REPORT.md` | Iris Xe performance profiling: frame-time budget (rendering ≤9ms, CV ≤4ms, chemistry ≤2.5ms, UI ≤1.17ms), triangle/draw-call/VRAM budgets. |
| `SCIENTIFIC_VALIDATION.md` | Scientific validity status: Hess's law, van 't Hoff, Arrhenius, Henderson-Hasselbalch, ETKDGv3, UFF, fume hood aerodynamics, Semenov — all validated against NIST/CRC/Atkins/Perry references; zero-fake-values policy. |
| `TRACKING_ARCHITECTURE.md` | CV architecture: MediaPipe 21-landmark skeleton, 1-Euro filter math, latency envelopes, gesture thresholds. |
| `BUILD_AND_RELEASE.md` | DevOps: Windows x64 build pipeline, Python embeddable bundle, Godot export, Steam packaging. |
| `ASSET_PIPELINE_EEVEE_SPEC.md` | 8-stage PBR asset pipeline, texture rectification, glTF export, Iris Xe VRAM budget. |
| `IMMERSIVE_3D_CHEM_LAB_SPEC.md` | Interaction state machine (IDLE/SELECTING/CARRYING/PLACING/OPERATING), pedagogy sources. |
| `ORGANIC_REACTIONS_CATALOG_SPEC.md` / `INORGANIC_REACTIONS_CATALOG_SPEC.md` | Reaction mechanism catalogs (SN1/SN2, Grignard, Fischer esterification, solubility, redox). |
| `BIOCHEMICAL_PATHWAY_SIMULATION_SPEC.md` | Michaelis-Menten enzyme kinetics, cofactor dependencies, metabolic flux. |
| `ELECTROCHEMISTRY_SPEC.md` | Nernst equation, Butler-Volmer kinetics, cyclic voltammetry. |
| `PHOTOCHEMISTRY_SIMULATION_SPEC.md` | Jablonski diagrams, UV-Vis absorption, quantum yield, fluorescence. |
| `TIHKAL_PIHKAL_STOICHIOMETRY_SPEC.md` | Molar accounting, limiting reagent resolution, theoretical yield tracking. |
| `TIHKAL_PIHKAL_BYPRODUCTS_SPEC.md` | Hazardous byproduct formation, thermal decomposition runaway, DEA schedule containment. |
| `GOOGLE_NANO_BANANA_MOLECULAR_RENDERING_SPEC.md` | Real-time molecular rendering, CPK shaders, ribbon backbones. |
| `PHOTOGRAMMETRY_PIPELINE_SPEC.md` | Multi-view stereo, COLMAP, mesh decimation, delighting shaders. |
| `GITHUB_INTEGRATION_SPEC.md` | Conventional commits, automated quality gates, artifact publishing, linear project tracking. |

---

## 5. Safety Boundaries (Important for ChatGPT Context)

- **PiHKAL/TIHKAL content** (`TIHKAL_PIHKAL_STOICHIOMETRY_SPEC.md`, `TIHKAL_PIHKAL_BYPRODUCTS_SPEC.md`) is treated strictly as **educational stoichiometry and molar accounting only** — limiting-reagent resolution, theoretical yield tracking, and hazardous-byproduct modeling. The existing specs explicitly state the project does **not** provide step-by-step synthetic procedures for controlled substances.
- **Side-reaction/impurity engine** models genuine organic-synthesis literature defects (aspirin oligomerization, paracetamol NAPQI oxidation, acetanilide diacylation) for pedagogical safety training, not as actionable routes.
- **Explosion/containment modeling** (KMnO₄+H₂SO₄, perchloric acid+solvent) is simulated as a contained fume-hood hazard with safety-score penalties, not as instructions.
- **GHS hazard data** is used for in-game pictograms and safety scoring only.

---

## 6. Quality Gates & Verification

- **Test suite:** 214 passing tests across 42 test modules (`pytest`), headless (no GUI/GPU), ~5 seconds runtime.
- **Linting:** Ruff with strict selection (`E, F, I, W, UP, B, C4, PTH, SIM`), zero errors on core source.
- **Anti-AI-slop AST audit** (`tests/test_anti_ai_slop_audit.py`): zero bare `except:`, zero silent swallows, managed thread lifecycles (named threads), 100% public type annotations.
- **Type-checking:** mypy strict mode, Python 3.12.
- **Formatting:** Black, line-length 100.
- **Quality gate script:** `scripts/run_quality_gate.py` — one-command test + lint + type-check.

---

## 7. Integration Points (How the Pieces Talk)

```
Godot 4 game client  ←IPC (TCP/Named Pipe)→  Python scientific core
                                               ↑
                                  Tracking daemon (MediaPipe + 1-Euro filter, 30 FPS inference → 60 Hz telemetry)
                                               ↑
                                  Intelligence daemon (Omniroute → NIM → Gemini → deterministic floor)
```

- **Godot ↔ Python Core:** JSON-RPC-style packets over local TCP (`127.0.0.1:8765`) or Windows Named Pipe (`\\.\pipe\chemlab_core`). Mix-reagents request → simulation-step response (conversion ratio, temperature, color RGBA, precipitate, side products, safety warnings).
- **Tracking daemon → Godot:** 60 Hz gesture telemetry (gesture type, cursor position, wrist tilt, pinch distance, confidence).
- **Companion server:** WebSocket on port 8766; mobile PWA reads telemetry and issues remote actions (heat/cool/stir/emergency wash).
- **Desktop GUI:** PySide6 standalone window (developer workbench), connects to core via IPC.
- **Blender:** DCC-only; exports GLB/glTF + PBR textures for Godot; live MCP bridge for agentic scene editing during development.

---

## 8. Roadmap (from `DEVELOPMENT_PROGRESS.md`)

```
Phase 0 [COMPLETE]  State Audit & Architecture
Phase 1 [COMPLETE]  Environment & Tooling Setup
Phase 2 [IN PROGRESS]  Playable 3D Vertical Slice (Godot 4 workbench, 5 apparatuses, acid-base titration, dual input)
Phase 3 [PENDING]   Consolidated Scientific Engine & Solvers (unify duplication, RK4/Radau ODE solvers)
Phase 4 [PENDING]   Realtime Webcam Hand Tracking & Kinematic Smoothing
Phase 5 [PENDING]   Sandbox Mode & Experiment Library (100+ reagents, time dilation 0.1x–100x)
Phase 6 [PENDING]   Adventure Campaign & Narrative Quests (10 levels, guided wizards, lab reports)
Phase 7 [PENDING]   Provider-Agnostic AI & Tutor Assistance
Phase 8 [PENDING]   AAA Visuals, Shaders & Sound for Intel Iris Xe
Phase 9 [PENDING]   Standalone Windows Build & Steam Packaging
```

Immediate next steps (Phase 2 Sprint 1): initialize `godot/project.godot`, build the cleanroom workbench scene, apparatus base + Erlenmeyer flask, mouse input fallback, flagship acid-base reaction loop, quality-gate sign-off.

---

## 9. Target Hardware

- **Reference:** Dell Latitude 5530 — Intel Core i5-1245U (12th gen, 10 cores/12 threads, 15W cTDP), Intel Iris Xe (80 EUs), 16 GB DDR4 shared RAM, 128 MB dedicated VRAM aperture, Windows 11 Pro.
- **Performance target:** 60 FPS @ 1080p (30 FPS floor), <100 ms interaction latency, <1.5 GB system memory, ≤110 MB VRAM usage.
- **Renderer:** Godot 4 Compatibility Renderer (OpenGL ES 3.0 / WebGL 2) to avoid Vulkan fillrate saturation on Iris Xe.

---

## 10. How to Run / Develop

```bash
# Clone
git clone https://github.com/mertgoevse-wq/chemlab.git
cd chemlab

# Install (Python 3.12+)
python -m pip install -e .[dev]

# Run tests
pytest

# Run quality gate
python scripts/run_quality_gate.py

# Desktop GUI (PySide6)
python -m src.chemlab.desktop.main_window

# Companion server (mobile PWA, port 8766)
python -m src.chemlab.companion.remote_server

# Launchers: launch_chemlab.bat (Windows) / launch_chemlab.sh (Linux)
```

**Dependencies:** opencv-python, mediapipe, numpy, websockets (runtime); pytest, black, ruff, mypy (dev). Optional: PySide6 (desktop GUI), RDKit, Cantera (scientific core — with graceful fallback stubs).

---

## 11. Repository Metadata

- **Git remote:** `https://github.com/mertgoevse-wq/chemlab.git` (origin, fetch + push)
- **Default branch:** `main`
- **Git user:** Senior Switch Developer
- **License:** MIT
- **Primary language:** Python 3.12; GDScript (Godot); Blender Python; HTML/JS (gallery dashboard)

---

*This document is intended to give ChatGPT a complete, accurate picture of the ChemLab project so it can understand context, architecture, and code when asked questions about the repository. It reflects the repository state as of 2026-11-03.*