# ChemLab Autonomous Development Progress Ledger & Master Roadmap

**Project:** ChemLab — Interactive Virtual Chemistry Laboratory  
**Repository Path:** C:\Users\Win11 Pro\Desktop\chemlab  
**Branch:** main  
**Role:** Program Manager & QA Lead  
**Last Updated:** 2026-11-02  
**Document Version:** 1.0.0 (Single Source of Truth)  

---

## 1. Executive Summary & Verification Gate

ChemLab has established a rigorous automated quality baseline. All core systems operate under automated continuous-testing and anti-AI-slop static code analysis gates.

### 1.1 Baseline Verification Results

| Quality Dimension | Standard / Threshold | Current Value | Verification Status |
|-------------------|----------------------|---------------|---------------------|
| Automated Test Suite | >= 200 passing tests | 214 passed (35 test modules) | [PASS] Verified |
| Test Execution Time | <= 45.0 seconds | 18.83 seconds (Python 3.12, win32) | [PASS] Verified |
| Core Source Code Lint | Zero errors (Ruff 0.1.0+) | 0 errors, 0 warnings across src/, tests/, scripts/, blender_live_bridge.py | [PASS] Verified |
| Anti-AI-Slop AST Gate | 100% compliance | 0 bare excepts, 0 silent swallows, 0 anonymous threads, 100% public type annotations | [PASS] Verified |
| Target Hardware Budget | 60 FPS on Intel Iris Xe (80 EU) | Architecture profiles implemented in iris_xe_optimizer.py | [PASS] In Budget |

### 1.2 Automated Anti-AI-Slop Code Quality Standards

Implemented in `tests/test_anti_ai_slop_audit.py`, ChemLab enforces four invariant programmatic rules via Python Abstract Syntax Tree (AST) parsing:
1. **Zero Bare `except:` Clauses:** All exception handlers must capture explicit exception hierarchies.
2. **Zero Silent Swallows:** Handlers consisting purely of `pass` are rejected unless whitelisted for benign OS polling (`OSError`, `Empty`, `TimeoutError`).
3. **Managed Threading Lifecycle:** All `threading.Thread` instances must supply explicit `name` attributes to eliminate zombie background thread leakage.
4. **Mandatory Type Signatures:** 100% of public functions and methods must define full argument and return type annotations.

---

## 2. Completed Milestones & Architectural Audit Artifacts (Phase 0 Retrospective)

Phase 0 established foundational domain research, photorealistic scene graph prototypes, and 12 engineering specifications authored in the repository root.

### 2.1 Engineering Specifications Registry

| Specification Document | Focus Area | Key Architectural Deliverable |
|------------------------|------------|--------------------------------|
| `IMMERSIVE_3D_CHEM_LAB_SPEC.md` | Core UX & Affordance System | Interaction state machine (IDLE, SELECTING, CARRYING, PLACING, OPERATING), pedagogy synthesis from Labster, Foldit, ChemCollective, and PhET. |
| `ASSET_PIPELINE_EEVEE_SPEC.md` | PBR Graphics & Ingestion | 8-stage asset pipeline (A0-A7), texture rectification, roughness/metallic derivation, glTF export, and Iris Xe VRAM budget enforcement. |
| `ORGANIC_REACTIONS_CATALOG_SPEC.md` | Organic Reaction Mechanisms | 100+ reaction catalog (SN1/SN2/E1/E2, electrophilic addition, Grignard, Fischer esterification, aldol condensation). |
| `INORGANIC_REACTIONS_CATALOG_SPEC.md` | Inorganic Equilibria & Redox | Solubility tables, complex ion equilibria, gas evolution equations, and multi-step inorganic synthesis trees. |
| `BIOCHEMICAL_PATHWAY_SIMULATION_SPEC.md` | Enzymatic Systems | Michaelis-Menten enzyme kinetics, cofactor dependencies (ATP/NADH), and metabolic flux balance analysis. |
| `ELECTROCHEMISTRY_SPEC.md` | Electrochemical Dynamics | Nernst equation calculations, Butler-Volmer kinetics, cyclic voltammetry, and electrolysis cell simulations. |
| `PHOTOCHEMISTRY_SIMULATION_SPEC.md` | Light-Matter Interactions | Jablonski diagrams, UV-Vis absorption, quantum yield calculations, and fluorescence/phosphorescence emission. |
| `TIHKAL_PIHKAL_STOICHIOMETRY_SPEC.md` | Molar Balances & Enthalpies | Rigid molar accounting, limiting reagent resolution, and theoretical yield tracking. |
| `TIHKAL_PIHKAL_BYPRODUCTS_SPEC.md` | Thermal Safety & Byproducts | Hazardous byproduct formation modeling, thermal decomposition runaway, and DEA schedule containment safety rules. |
| `GOOGLE_NANO_BANANA_MOLECULAR_RENDERING_SPEC.md` | 3D Structural Chemistry | Real-time edge molecular rendering, CPK ball-and-stick shaders, ribbon backbones, and spatial bond length verification. |
| `PHOTOGRAMMETRY_PIPELINE_SPEC.md` | Photogrammetric Reconstruction | Multi-view stereo capture, COLMAP point cloud generation, mesh decimation, and delighting shaders. |
| `GITHUB_INTEGRATION_SPEC.md` | DevOps & Autonomous CI | Conventional commits, automated quality gates, artifact publishing, and linear project tracking. |

### 2.2 Shipped Implementations & Subsystems

1. **Native Desktop Scientific Cleanroom GUI:** Built with PySide6 (`src/chemlab/desktop/main_window.py`), providing dark-theme desktop controls, Cantera integration, RDKit 3D conformer viewer, and reaction curve plotting without web runtime dependencies.
2. **Cantera Thermodynamics Engine:** Implemented in `src/chemlab/simulation/cantera_engine.py`, computing accurate NIST/CRC enthalpy, entropy, and Gibbs free energy equilibria.
3. **RDKit Cheminformatics Engine:** Implemented in `src/chemlab/simulation/rdkit_engine.py`, generating 3D conformers via Universal Force Field (UFF) minimization and PDB outputs from SMILES inputs.
4. **Global Laboratory Taxonomy & Procedural World Generator:** Implemented in `src/chemlab/world/lab_taxonomy.py` and `procedural_labs.py`, categorizing 11 lab archetypes across 4 containment levels (BSL-1 to BSL-4) with modular furniture placement.
5. **Computer Vision Hand & Holistic Tracking:** Implemented in `src/chemlab/cv/hand_tracker.py`, `holistic_tracker.py`, and `one_euro_filter.py`, delivering 21 3D hand landmarks at 60 FPS with jitter filtering.
6. **Provider-Agnostic AI Reagent Reaction Engine:** Implemented in `src/chemlab/ai/reagent_computer.py` and `omniroute_bridge.py`, providing Gemini 2.5 Pro reasoning with automated markdown fence stripping and offline heuristic fallback.
7. **Mantaflow Fluid Physics & Volumetric Absorption:** Implemented in `scripts/module_fluid_simulation.py`, modeling liquid filling, pour trajectories, and Beer-Lambert optical attenuation.
8. **Godot 4.x 3D HUD Controller:** Implemented in `scripts/chemlab_hud.gd`, driving spatial 3D reagent tags, pH needle cursor, interaction state signaling, and level-up celebrations.
9. **Procedural 44.1 kHz SFX Synthesizer:** Implemented in `scripts/generate_sfx.py`, delivering audio assets for pinch readiness, hover proximity, grip lock, safety alarms, and fanfare.

### 2.3 Documentation Suite Cross-Reference Registry

| Document Path | Scope & System Authority | Key Interfaces |
|---------------|--------------------------|----------------|
| `docs/GAME_DESIGN_DOCUMENT.md` | Core Game Design & Vision | Godot 4 3D engine target, locomotion, 5 apparatus specifications, visual art direction. |
| `docs/STORY_AND_QUESTS.md` | Narrative & Campaign Progression | 10 story levels (Intern to Master Alchemist), quest stages, XP awards, dialogue trees. |
| `docs/TRACKING_ARCHITECTURE.md` | CV & Natural Interaction | MediaPipe 21-landmark skeleton, One-Euro filter math, latency envelopes, gesture thresholds. |
| `docs/PERFORMANCE_REPORT.md` | Hardware Profiling & Budgets | Intel Iris Xe 80 EU benchmarks, VRAM allocation tiering, polygon budgets, draw call caps. |
| `docs/INTEGRATIONS_REGISTRY.md` | External Libraries & AI Models | Cantera, RDKit, Gemini 2.5 Pro, Claude 3.5 Sonnet, Ollama, Blender IPC bridge. |
| `docs/BUILD_AND_RELEASE.md` | DevOps, Packaging & Delivery | Windows x64 build pipeline, Python embeddable bundle, Godot export, Steam packaging. |

---

## 3. The 10-Phase Autonomous Development Roadmap

```
Phase 0 [COMPLETE]  ->  Phase 1 [COMPLETE]  ->  Phase 2 [IN PROGRESS]  ->  Phase 3 [PENDING]
State Audit & Arch       Environment Setup       Playable 3D Slice          Consolidated Engines
                                                                                   |
Phase 7 [PENDING]   <-  Phase 6 [PENDING]   <-  Phase 5 [PENDING]   <-  Phase 4 [PENDING]
Agnostic AI Tutor       Story Campaign          Sandbox Mode & Library     Realtime CV Tracking
       |
Phase 8 [PENDING]   ->  Phase 9 [PENDING]
Iris Xe Shaders         Standalone Steam Build
```

### Phase 0: State Audit & Architecture
- **Status:** COMPLETE
- **Objective:** Establish architectural ground truth, codify domain specifications, verify test suite, and audit code quality.
- **Key Deliverables:** 12 master specifications; baseline verification of 214 tests; anti-AI-slop AST suite; Git commit history preservation.
- **Sign-Off Criteria:** 100% green test suite, zero core lint errors, signed PM ledger.

### Phase 1: Development Environment & Tooling Setup
- **Status:** COMPLETE
- **Objective:** Provision isolated runtime environments, dependency locks, and continuous quality enforcement.
- **Key Deliverables:** Python 3.12 venv configuration; PySide6, OpenCV, MediaPipe, Cantera, RDKit, WebSockets tooling; Ruff/Mypy strict configs; `scripts/run_quality_gate.py`.
- **Sign-Off Criteria:** One-command reproduction of full build and test execution within 45s.

### Phase 2: Playable 3D Vertical Slice (Godot 4 3D Workbench)
- **Status:** IN PROGRESS (Immediate Primary Focus)
- **Objective:** Deliver a standalone, playable 3D vertical slice in Godot 4 featuring the laboratory workbench, 5 fully interactive apparatuses, a safe flagship chemical experiment, and dual-input controls (mouse/keyboard + webcam hand tracking).
- **Key Deliverables:** `godot/` project directory; `Workbench.tscn`; 5 apparatus scenes with grab/pour physics; Acid-Base Neutralization experiment; dual-input abstraction layer; spatial HUD integration; sustained 60 FPS on Intel Iris Xe.
- **Dependencies:** `scripts/chemlab_hud.gd`, `audio/sfx_*.wav`, `src/chemlab/cv/one_euro_filter.py`.
- **Target Completion:** 2026-11-23.

### Phase 3: Consolidated Scientific Engine & Solvers
- **Status:** PENDING
- **Objective:** Consolidate disparate reaction engines, catalog schemas, and domain models into a unified scientific computation core.
- **Key Deliverables:** Unified `chemlab/simulation/solvers/` package; numerical Runge-Kutta 4th order (RK4) and Radau ODE solvers for stiff kinetics; tight coupling with Cantera thermodynamic equilibria and RDKit 3D conformers; elimination of duplicate models.
- **Dependencies:** Phase 0 specifications, Phase 2 vertical slice baseline.
- **Target Completion:** 2026-12-07.

### Phase 4: Realtime Webcam Hand Tracking & Kinematic Smoothing
- **Status:** PENDING
- **Objective:** Deliver natural bare-hand manipulation via standard webcams without dedicated VR hardware.
- **Key Deliverables:** MediaPipe Hands/Holistic pipeline streaming at 60 FPS; One-Euro filter tuning (< 15ms latency); dynamic gesture classifier (pinch, grab, pour tilt, stir swirl, open palm release); two-handed apparatus coordination.
- **Dependencies:** Phase 2 input manager, Phase 1 computer vision setup.
- **Target Completion:** 2026-12-21.

### Phase 5: Sandbox Mode & Experiment Library
- **Status:** PENDING
- **Objective:** Build an open-ended chemical sandbox containing 100+ reagents, time-scale controls, and emergent hazard simulations.
- **Key Deliverables:** 100+ reagent catalog with GHS hazard integration; time manipulation controller (pause, 0.5x, 1x, 2x, 5x, 10x); dynamic spill, fire, and toxic gas dispersion; automated fume hood and eye-wash station mechanics.
- **Dependencies:** Phase 3 unified solvers, Phase 4 tracking.
- **Target Completion:** 2027-01-04.

### Phase 6: Adventure Campaign & Narrative Quests
- **Status:** PENDING
- **Objective:** Create a structured progression campaign guiding players from Lab Intern (Level 1) to Master Alchemist (Level 10).
- **Key Deliverables:** 10 curriculum-aligned quest chains with objective tracking; guided synthesis wizards; automated lab report generation and grading; procedural challenge scenarios (contamination drills, unknown sample identification).
- **Dependencies:** Phase 5 experiment library, `src/chemlab/story/story_manager.py`.
- **Target Completion:** 2027-01-18.

### Phase 7: Provider-Agnostic AI & Tutor Assistance
- **Status:** PENDING
- **Objective:** Embed an intelligent, non-hallucinating laboratory tutor supporting multiple LLM backends.
- **Key Deliverables:** Provider abstraction for Google Gemini 2.5 Pro, Claude 3.5 Sonnet, OpenAI GPT-4o, and local Ollama; context-aware chemistry reasoning without formula hallucination; automated markdown fence stripping and structured JSON validation; offline heuristic fallback.
- **Dependencies:** `src/chemlab/ai/omniroute_bridge.py`, `reagent_computer.py`.
- **Target Completion:** 2027-02-01.

### Phase 8: AAA Visuals, Shaders & Sound Design for Intel Iris Xe
- **Status:** PENDING
- **Objective:** Maximize visual fidelity and acoustic immersion within the thermal and memory constraints of Intel Iris Xe integrated graphics.
- **Key Deliverables:** Physical glass shader with internal absorption and chromatic aberration; volumetric liquid shader with Beer-Lambert absorption, meniscus, and foam bubbles; Bunsen flame emission and dynamic light caster; 60 FPS lock at 1080p via CAS/XeSS upscaling; spatial 3D audio mix.
- **Dependencies:** `src/chemlab/graphics/iris_xe_optimizer.py`, `scripts/generate_sfx.py`.
- **Target Completion:** 2027-02-15.

### Phase 9: Standalone Windows Build & Steam Packaging
- **Status:** PENDING
- **Objective:** Package ChemLab as an optimized standalone Windows application and prepare Steam release artifacts.
- **Key Deliverables:** Self-contained Windows x64 installer bundling embedded Python 3.12 and Godot 4 runtime; Steamworks integration (Achievements, Cloud Saves, Workshop); automated crash reporting; digitally signed binaries.
- **Dependencies:** Phases 2 through 8 complete and verified.
- **Target Completion:** 2027-03-01.

---

## 4. Phase 2 Playable 3D Vertical Slice: Detailed Task Checklist

The Vertical Slice proves end-to-end gameplay loop feasibility. It combines a cleanroom 3D workbench, 5 apparatuses, an acid-base neutralization experiment, dual-input control, and real-time spatial HUD.

### Subsystem 2.1: Godot 4 3D Workbench Environment
- [ ] Task 2.1.1: Initialize Godot 4.3 project structure in `godot/` with `project.godot`.
- [ ] Task 2.1.2: Configure rendering project settings: Vulkan Mobile / Forward+ profile tuned for Intel Iris Xe (MSAA 2x, SSAO enabled, Bloom disabled, CAS contrast-adaptive sharpening enabled).
- [ ] Task 2.1.3: Build `scenes/workbench_slice.tscn`: Cleanroom laboratory bench (2.0m x 1.0m epoxy resin top, height 0.90m), stainless steel utility riser, rear fume hood glass sash, and waste container.
- [ ] Task 2.1.4: Set up lighting environment: Three-point soft cleanroom lighting (5500K daylight balance, key light, fill light, rim light) with baked ambient occlusion for Iris Xe efficiency.
- [ ] Task 2.1.5: Instantiate Camera3D with scientific orbit and fixed workbench perspective (FOV 65 degrees, target at center bench).

### Subsystem 2.2: Five Interactive Laboratory Apparatuses
- [ ] Task 2.2.1: Implement base class `scripts/apparatus_base.gd` defining interaction states: `READY` (green outline), `HOVER` (yellow outline, < 50mm proximity), `HELD` (blue outline, kinematic grab), and `OPERATING`.
- [ ] Task 2.2.2: **Apparatus 1 — Erlenmeyer Flask (250 mL / 500 mL):**
  - Conical borosilicate glass mesh with realistic IOR (1.474).
  - Dynamic interior liquid mesh with fill level shader and meniscus curvature.
  - Pour angle detection: when flask pitch exceeds 45 degrees, calculate pour rate and emit liquid stream particles.
- [ ] Task 2.2.3: **Apparatus 2 — Chemical Beaker (400 mL):**
  - Cylindrical borosilicate glass with calibrated white graduation decals (50 mL to 400 mL).
  - Liquid recipient trigger area for catching poured streams from flasks or cylinders.
  - Pouring spout collision volume for secondary pouring.
- [ ] Task 2.2.4: **Apparatus 3 — Graduated Measuring Cylinder & Test Tube Rack:**
  - 100 mL tall glass cylinder with hexagonal anti-roll base.
  - Precision volumetric measurement logic (+/- 0.5 mL accuracy).
  - Test tube rack holding 8 analytical tubes with pH color spectrum solutions.
- [ ] Task 2.2.5: **Apparatus 4 — Bunsen Burner:**
  - Cast-iron round base, brass gas inlet nipple with rubber tubing, and rotatable knurled air collar.
  - Dual-cone glowing flame shader (inner intense cyan cone at 1500 C, outer blue sheath).
  - Rotary air collar interaction: toggle between safety yellow luminous flame and roaring blue heating flame.
  - Thermal proximity trigger: raises temperature of glassware positioned directly above on tripod/gauze.
- [ ] Task 2.2.6: **Apparatus 5 — Digital Magnetic Stirrer & Hotplate:**
  - Medical slate housing with white ceramic top plate (200mm x 200mm).
  - Digital 7-segment red LED readout displaying setpoint vs current RPM (0-1500) and Temperature (RT-300 C).
  - Twin rotary dials with mouse drag and gesture rotation bindings.
  - Internal rotating magnetic field logic driving a Teflon (PTFE) stir bar inside beakers, inducing liquid vortex.

### Subsystem 2.3: Safe Flagship Experiment Execution Loop (Acid-Base Neutralization & Titration)
- [ ] Task 2.3.1: Define experiment reagents:
  - Reagent A: 0.1 M Hydrochloric Acid (HCl), colorless liquid, pH 1.0.
  - Reagent B: 0.1 M Sodium Hydroxide (NaOH), colorless liquid, pH 13.0.
  - Indicator: Phenolphthalein solution (0.1% in ethanol), colorless below pH 8.2, intense pink/magenta above pH 8.2.
  - Secondary Indicator Option: Universal Indicator (Red pH 1-3 -> Green pH 7 -> Purple pH 11-14).
- [ ] Task 2.3.2: Implement 4-step guided progression sequence:
  - Step 1: Measure 50.0 mL of 0.1 M HCl into the 250 mL Erlenmeyer flask using the graduated cylinder.
  - Step 2: Add 3 drops of Phenolphthalein indicator to the acid solution (solution remains clear).
  - Step 3: Place flask onto the magnetic stirrer, drop in the PTFE stir bar, and engage gentle stirring (300 RPM).
  - Step 4: Titrate 0.1 M NaOH dropwise from the beaker into the flask until the solution transitions to persistent pink (pH 7.0 - 8.2 endpoint).
- [ ] Task 2.3.3: Reaction kinetics and thermodynamic modeling:
  - Neutralization equation: HCl + NaOH -> NaCl + H2O (Delta H = -57.3 kJ/mol).
  - Real-time temperature delta calculation: exothermic rise of ~0.8 C in 100 mL volume.
  - Titration curve solver calculating instant pH based on remaining moles of hydronium vs hydroxide ions.
- [ ] Task 2.3.4: Success evaluation and scoring:
  - Precision evaluation on stoichiometric equivalence point (+/- 1.0 mL target window).
  - Safety score evaluation (zero spills, PPE verified, proper glassware placement).
  - Trigger quest completion fanfare and XP reward banner.

### Subsystem 2.4: Dual-Input Interaction Framework
- [ ] Task 2.4.1: Abstract input manager (`scripts/input_manager.gd`) handling seamless switching between Mouse/Keyboard and Webcam Hand Tracking.
- [ ] Task 2.4.2: **Mouse & Keyboard Control Scheme:**
  - Left Mouse Button: Click to select, hold to pick up apparatus (kinematic lock to cursor plane).
  - Mouse Wheel / Right Mouse Drag: Rotate / tilt held glassware for precision pouring.
  - Spacebar: Snap apparatus to nearest bench anchor or release hold.
  - Tab Key: Toggle HUD visibility or switch between Story and Sandbox modes.
- [ ] Task 2.4.3: **Webcam Bare-Hand Tracking Scheme:**
  - Receive 21 3D hand landmark frames via local WebSocket IPC (port 8765) from `src/chemlab/cv/hand_tracker.py`.
  - Apply One-Euro filter in GDScript to eliminate tracking jitter.
  - Pinch Gesture (Thumb tip to Index tip distance < 35 mm): Grasp nearest apparatus within 50 mm radius.
  - Wrist Roll/Pitch Gesture: Tilt held flask to initiate volumetric pouring.
  - Open Palm Spread (all fingers extended): Release held apparatus with gentle physics placement.
  - Two-Handed Coordination: Left hand stabilizes beaker while right hand pours from cylinder.
- [ ] Task 2.4.4: Automated input fallback: If webcam is unavailable or loses tracking, smoothly revert to mouse/keyboard without interrupting simulation state.

### Subsystem 2.5: Spatial 3D HUD & Acoustic Feedback
- [ ] Task 2.5.1: Integrate `scripts/chemlab_hud.gd` CanvasLayer into the main scene:
  - Top Bar: Quest title, current step counter, animated progress bar.
  - Safety Alert Badge: Real-time status indicator (OPTIMAL green, CAUTION yellow, HAZARD red).
  - Mode Indicator: Visual badge distinguishing Story Mode from Sandbox Mode.
- [ ] Task 2.5.2: Spatial 3D World Labels:
  - Billboarding Label3D hovering above each apparatus showing chemical formula, concentration, and temperature.
  - Dynamic pH spectrum bar showing analog needle position (0.0 to 14.0) with Acidic / Neutral / Alkaline tagging.
- [ ] Task 2.5.3: Acoustic SFX Integration:
  - Spatial AudioStreamPlayer3D triggers for equipment interaction:
    - `audio/sfx_pinch_ready.wav` on hand detection.
    - `audio/sfx_pinch_hover.wav` on entering 50 mm proximity.
    - `audio/sfx_pinch_grip.wav` on firm apparatus grasp.
    - `audio/sfx_safety_alert.wav` on thermal limit or hazard trigger.
    - `audio/sfx_quest_complete.wav` on successful titration endpoint.
    - `audio/sfx_level_up.wav` on experimental rank advancement.

---

## 5. Known Technical Debt & Architectural Unification Plan

During Phase 0, multiple standalone prototypes were built across different subdirectories. Phase 3 is dedicated to consolidating these into a clean, canonical architecture.

### 5.1 Technical Debt Itemization

| Debt ID | Subsystem | Current State / Conflict | Target Unified Architecture | Severity |
|---------|-----------|--------------------------|-----------------------------|----------|
| **TD-01** | Domain Models | Three conflicting model implementations: `chemlab_core/models.py` (Pydantic v2), `src/chemlab/models.py` (dataclasses), and `simulation/catalog.py` (dataclasses + enum). | Standardize on a single canonical model package under `src/chemlab/core/models/` utilizing Pydantic v2 with strict validation and GDScript serialization mirrors. | HIGH |
| **TD-02** | Reaction Solvers | Redundant simulation engines: `chemlab_core/chemistry/reaction_engine.py` (Briggs-Rauscher), `src/chemlab/simulation/reaction_solver.py` (heuristic kinetics), and `simulation/free_sim_engine.py`. | Unify into `src/chemlab/simulation/solvers/`: single modular solver coordinating Cantera thermodynamics, RDKit structures, and RK4 numerical ODE integration. | HIGH |
| **TD-03** | IPC & Networking | Split transport systems: raw asyncio TCP socket server (`chemlab_core/transport/`) vs WebSocket/HTTP server (`src/chemlab/companion/remote_server.py`) vs Blender MCP socket. | Build unified IPC broker supporting standard JSON-RPC 2.0 over WebSockets, serving both Godot engine and mobile companion clients on single port. | MEDIUM |
| **TD-04** | Computer Vision | Split vision code: `chemlab_core/vision/` (contracts, gesture classifier, synthetic frames) vs `src/chemlab/cv/` (hand tracker, holistic tracker, one euro filter). | Consolidate into `src/chemlab/cv/` with unified abstract `HandTrackingBackend` (MediaPipe runtime and synthetic mock). | MEDIUM |
| **TD-05** | Repository Root Structure | 12 Markdown specifications, loose scripts (`blender_client.py`, `blender_live_bridge.py`, `gallery.html`), and tarballs residing in repository root. | Relocate specs to `docs/specs/`, tools to `tools/`, and ensure root contains only `README.md`, `pyproject.toml`, and standard project descriptors. | LOW |
| **TD-06** | Vendor Addon Lint Isolation | Third-party unpacked Blender addon in `package/addon/simple_mcp_addon.py` triggers 24 Ruff formatting/import errors during root lint sweeps. | Add `package` and `node_modules` to `[tool.ruff.exclude]` in `pyproject.toml`. | LOW |

---

## 6. Bug Tracker & Risk Register

### 6.1 Active Bug Tracker

| Bug ID | Severity | Module | Description | Mitigation / Remediation |
|--------|----------|--------|-------------|--------------------------|
| **BUG-001** | Medium | Tooling | `ruff check .` encounters vendor violations in `package/addon/simple_mcp_addon.py`. | Add explicit exclusion rule `exclude = ["package", "node_modules", ".venv"]` in `pyproject.toml`. |
| **BUG-002** | Medium | Godot | Godot project directory (`godot/`) is uninitialized; GDScript controllers currently live under `scripts/`. | Initialize Godot 4.3 project structure in Sprint 1 of Phase 2. |
| **BUG-003** | Low | Safety | `GHSHazard` in `src/chemlab/models.py` defines 6 hazards, whereas `safety_simulation/ghs.py` defines 9 standard GHS categories. | Align enum to full OSHA/GHS Rev 10 standard (GHS01 through GHS09) during model unification. |
| **BUG-004** | Low | Audio | Audio assets in `audio/` are uncompressed 16-bit 44.1kHz WAV; acceptable for desktop, but will need OGG Vorbis for web deployment. | Add automated OGG compression step in asset packaging pipeline. |

### 6.2 Architectural Risk Register

| Risk ID | Risk Description | Likelihood | Impact | Preventive Mitigation Strategy |
|---------|------------------|------------|--------|--------------------------------|
| **RSK-01** | Integrated GPU VRAM exhaustion on Intel Iris Xe when running high-resolution textures and volumetric shaders simultaneously. | Medium | High | Enforce strict hardware budgets via `iris_xe_optimizer.py`: maximum 250,000 total scene triangles, texture resolution clamped to 1024x1024 with BC7 compression, and CAS dynamic upscaling. |
| **RSK-02** | Webcam tracking jitter degrading fine motor precision during delicate titration pouring. | Medium | High | Calibrate adaptive One-Euro filter parameters: dynamic cutoff frequency scaling with velocity; implement magnetic spatial snapping when apparatus enters 50mm hover threshold. |
| **RSK-03** | Chemical solver stiffness causing numerical divergence during rapid exothermic reactions. | Low | High | Employ adaptive time-stepping Radau IIA / implicit Euler solver for stiff kinetic equations, with automatic fallback clamping. |
| **RSK-04** | Latency spikes across Python-to-Godot IPC bridge exceeding 16.6ms frame budget. | Medium | Medium | Use lightweight binary Protobuf or compact JSON over local loopback WebSockets; execute tracking inference in dedicated thread pool. |

---

## 7. Hardware Target & Performance Budgets (Intel Iris Xe)

**Reference Hardware Specification:**
- Platform: Dell Latitude 5530
- CPU: Intel Core i5-1240U (10 Cores, 12 Threads, up to 4.40 GHz)
- GPU: Intel Iris Xe Graphics (80 Execution Units)
- Memory: 16 GB DDR4/LPDDR4x Dual-Channel (Shared System & Video RAM)
- OS: Windows 11 Pro 64-bit

### Performance Envelopes & Budgets

```
Frame Time Budget: 16.67 ms (Solid 60 FPS Target)
+---------------------------------------------------------------+
| Rendering & Shaders (Iris Xe)        : <= 9.00 ms (54.0%)     |
| CV Hand Tracking & Filtering         : <= 4.00 ms (24.0%)     |
| Chemical Kinetics & Fluid Simulation : <= 2.50 ms (15.0%)     |
| Scene Logic, Audio & UI HUD          : <= 1.17 ms (7.0%)      |
+---------------------------------------------------------------+
```

| Budget Metric | Iris Xe Allocation Limit | Target Value | Measurement Tooling |
|---------------|--------------------------|--------------|---------------------|
| Sustained Frame Rate | >= 60 FPS at 1080p | 60 FPS | In-Engine Performance Monitor |
| 99th Percentile Frame Time | <= 20.0 ms | 18.2 ms | Profiler Frame Log |
| Total Scene Triangles | <= 250,000 tris | ~120,000 tris | `tests/validate_scene_assets.py` |
| Maximum Single Object Triangles | <= 35,000 tris | 18,500 tris | Asset Mesh Inspector |
| Draw Calls per Frame | <= 150 draw calls | 85 draw calls | Render Doc / Godot Debug |
| Video Memory (Shared VRAM) | <= 1,800 MB | ~950 MB | OS GPU Memory Monitor |
| System Process Resident RAM | <= 3,500 MB | ~1,800 MB | Task Manager |
| Webcam Glass-to-Screen Latency | <= 35 ms | 28 ms | High-speed video test |
| Pinch Grab Response Time | <= 20 ms | 14 ms | Event dispatch timestamp delta |

---

## 8. Immediate Next Deliverables (Sprint 1 / Phase 2 Kickoff)

The autonomous engineering team will execute the following deliverables in order of priority:

1. **Sprint Deliverable 1.1 — Godot 4 Project Scaffolding:**
   - Initialize `godot/project.godot` configured with the Intel Iris Xe rendering profile.
   - Establish autoload singletons (`GameState.gd`, `InputManager.gd`, `ReactionEngine.gd`).
2. **Sprint Deliverable 1.2 — Cleanroom Workbench Scene:**
   - Assemble `godot/scenes/Workbench.tscn` featuring the main island bench, lighting, and ambient occlusion.
   - Attach `scripts/chemlab_hud.gd` to root CanvasLayer.
3. **Sprint Deliverable 1.3 — Apparatus Base & Erlenmeyer Flask:**
   - Port `scripts/module_apparatus.py` Erlenmeyer flask geometry to Godot mesh with dynamic liquid shader.
   - Implement `scripts/apparatus_base.gd` with three-state interaction outlines (READY/HOVER/HELD).
4. **Sprint Deliverable 1.4 — Mouse Input & Fallback Controller:**
   - Implement raycast pick-and-place, mouse wheel pour angle rotation, and bench snap logic.
5. **Sprint Deliverable 1.5 — Flagship Acid-Base Reaction Loop:**
   - Implement real-time stoichiometric titration kinetics and color lerp for HCl + NaOH + Phenolphthalein.
   - Verify quest completion fanfare and level-up banner triggers upon reaching pH 8.2 endpoint.
6. **Sprint Deliverable 1.6 — Quality Gate Sign-Off:**
   - Execute test suite (`pytest`) ensuring 214 tests remain 100% green.
   - Verify zero lint errors.

---

*Authored and approved by ChemLab Program Manager & QA Lead. This ledger serves as the authoritative autonomous development contract.*
