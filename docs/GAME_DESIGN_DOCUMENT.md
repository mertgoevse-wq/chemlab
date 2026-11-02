# ChemLab: Origins - Game Design Document (GDD)

**Version:** 1.0  
**Date:** 2026-11-02  
**Status:** Pre-Production  
**Engine:** Godot 4.x (Compatibility / GLES3 / WebGL)  
**Target Platform:** Steam (Windows Desktop, Linux)

---

## Table of Contents

1. [Executive Summary & Vision Statement](#1-executive-summary--vision-statement)
2. [Target Hardware & Engine Specifications](#2-target-hardware--engine-specifications)
3. [Visual Direction & Atmosphere](#3-visual-direction--atmosphere)
4. [Core Gameplay Loops](#4-core-gameplay-loops)
5. [Five Vertical Slice Apparatus](#5-five-vertical-slice-apparatus)
6. [Mode Specifications](#6-mode-specifications)
7. [User Interface & HUD](#7-user-interface--hud)
8. [Progression Systems](#8-progression-systems)
9. [Technical Architecture](#9-technical-architecture)
10. [Asset & Performance Budgets](#10-asset--performance-budgets)

---

## 1. Executive Summary & Vision Statement

### 1.1 Product Overview

**ChemLab: Origins** is a premium scientific 3D simulation and adventure game that synthesizes hard science simulation with engaging first-person exploration. Players inhabit the role of a Junior Research Fellow navigating eleven global laboratory archetypes, mastering apparatus manipulation, reaction kinetics, and safety protocols through hands-on experimentation without real-world consequences.

### 1.2 Design Pillars

| Pillar | Definition | Measurable Outcome |
|--------|------------|-------------------|
| **Scientific Fidelity** | Every reaction is grounded in real thermodynamic data (Cantera), stoichiometric balancing, and validated rate laws | 100+ reagents with accurate SMILES/InChI; NIST-calibrated enthalpy/entropy values |
| **Photorealistic Immersion** | Borosilicate glass IOR 1.474, Beer-Lambert volumetric absorption, liquid meniscus geometry | Visual fidelity benchmark against real lab photography |
| **Universal Accessibility** | Monocular webcam hand tracking with 1-Euro filter smoothing; 100% mouse/keyboard parity | Accessibility audit by third-party evaluation |
| **Zero AI Slop** | No invented reactions; every shader grounded in physical constants | Automated anti-slop audit: all materials traceable to design tokens |

### 1.3 Target Audiences

1. **Researchers & Graduate Students** - Validation of conceptual understanding; sandbox for experimental design
2. **Undergraduate Chemistry Students** - Pedagogical scaffolding through graduated quest progression
3. **Simulation Enthusiasts** - Deep apparatus interaction and photorealistic rendering
4. **Educators** - Classroom-ready lab scenarios aligned to IUPAC/GHS standards

---

## 2. Target Hardware & Engine Specifications

### 2.1 Reference Hardware Profile

| Component | Specification |
|-----------|---------------|
| **System** | Dell Latitude 5530 |
| **CPU** | Intel Core i5-1245U (12th Gen, 10 cores) |
| **RAM** | 16 GB DDR4-3200 |
| **GPU** | Intel Iris Xe Graphics (80 Execution Units) |
| **VRAM** | 128 MB dedicated slice + up to 8 GB shared |
| **Display** | 1920x1080 native |

### 2.2 Performance Envelope

- **Resolution Target:** 720p (1280x720) upscaled to display resolution
- **Framerate Target:** 30-60 FPS with adaptive quality scaling
- **Frame Time Budget:** 16.67ms minimum (60 FPS) / 33.33ms (30 FPS floor)
- **Memory Budget:** < 4 GB total system footprint

### 2.3 Engine Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Renderer** | Godot 4.x Compatibility (GLES3) | Cross-platform support; WebGL fallback for browser embed |
| **Render Scale** | 0.67x (Performance) to 1.0x (Native) | Dynamic XeSS-style upscaling |
| **Shadow Quality** | Low-Medium; 512px cube shadows | VRAM budget compliance |
| **Volumetrics** | Half-resolution trace | Iris Xe constraint |
| **Texture Streaming** | Tiered: VRAM priority, RAM staging | 128 MB VRAM offload strategy |

### 2.4 Iris Xe Optimization Strategy

The Intel Iris Xe optimizer (`src/chemlab/graphics/iris_xe_optimizer.py`) implements:

1. **Memory Partition Plan**: Dedicated VRAM budget (96 MB) + System RAM staging buffers (768 MB)
2. **Dynamic Resolution Scaling**: Quality (0.77x) / Balanced (0.71x) / Performance (0.67x) presets
3. **EEVEE-Equivalent Settings**: Viewport samples capped, half-res ray tracing, shadow cube size 512px
4. **Adaptive Framerate Governor**: Monitors frame time and degrades quality if < 45 FPS sustained

---

## 3. Visual Direction & Atmosphere

### 3.1 Aesthetic Philosophy

**Cleanroom High-Tech Research Institute** — The visual language draws from ISO Class 5/7 cleanroom environments: controlled, precise, clinical yet inviting. No neon cyberpunk, no fantasy alchemy aesthetics. The palette communicates professionalism and scientific gravitas.

### 3.2 Primary Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| **Graphite** | `#1A1D20` | Epoxy workbench surfaces |
| **Ivory** | `#F5F3EE` | Lab coat, paper labels |
| **Petrol** | `#0E3A4C` | Accent lighting, safety signage |
| **Cyan Accent** | `#38E1FF` | Digital readouts, HUD elements |
| **Clinical White** | `#FAFAFA` | Glassware, ceramic surfaces |

### 3.3 Glassware & Fluid Materials

All glassware is constructed from **Borosilicate Glass (Pyrex)**:
- **IOR:** 1.474 (exact physical value)
- **Roughness:** 0.015 (polished optical clarity)
- **Transmission Weight:** 1.0
- **Wall Thickness:** 1.8mm - 2.5mm (explicit geometry, never single-sheet)

**Fluid Token Specs:**
- **Liquid Meniscus:** Concave capillary curve; $h = \frac{2 \gamma \cos \theta}{\rho g r}$; contact angle $\theta \approx 15^\circ$ for aqueous on clean glass
- **Beer-Lambert Absorption:** `Absorption = exp(-\vec{\epsilon} \cdot c \cdot d)`
- **Phase Representation:** Solid precipitates (settled geometry), gas bubbles (particle sprites), fumes (volumetric density field)

### 3.4 Lighting & Environment

- **Primary Lighting:** Overhead 4x T8 fluorescent panels (3200K warm white)
- **Accent Lighting:** Petrol-colored LED strips along fume hood frames
- **Local Illumination:** 60W equivalent magnetic stirrer display glow; Bunsen burner emission shaders
- **Ambient Occlusion:** SSAO with 0.5m radius; half-resolution trace

---

## 4. Core Gameplay Loops

### 4.1 First-Person Locomotion System

The holistic locomotion system (`src/chemlab/cv/holistic_tracker.py`) provides:

- **Desktop Mode:** WASD movement, mouse look, Shift sprint
- **VR Mode (Optional):** Room-scale tracking with guardian bounds
- **Collision:** Capsule collider (radius 0.3m, height 1.8m)
- **Movement Speed:** 3.0 m/s walk; 5.5 m/s sprint; 0.3 m/s when carrying heavy glassware

### 4.2 Dual Input System

**Primary: Monocular Webcam Hand Tracking**

| Gesture | Detection Method | Action |
|---------|-----------------|--------|
| **Pinch-to-Grab** | Thumb tip (LM4) + Index tip (LM8) distance < 55mm | Grabs small apparatus (test tubes, pipettes) |
| **Grab-to-Hold** | Mean fingertip-to-palm distance < 160mm | Holds medium glassware (beakers, flasks) |
| **Tilt-to-Pour** | Wrist rotation angle > 38 degrees from vertical | Initiates liquid transfer |
| **Swirl-to-Mix** | Oscillatory wrist rotation cycle detection | Activates magnetic stirrer |
| **Point-to-Select** | Extended index finger, confidence > 0.85 | HUD button activation |

**Smoothing:** All 21 MediaPipe landmarks pass through **1-Euro Filter** (`src/chemlab/cv/one_euro_filter.py`):
- `min_cutoff: 1.0 Hz`
- `beta: 0.007` (velocity adaptation coefficient)
- `d_cutoff: 1.0 Hz` (derivative filter)

**Fallback: 100% Mouse & Keyboard Parity**
Every hand gesture has a direct mouse/keyboard equivalent. Players may toggle between input modes at any time without disrupting game state.

### 4.3 Interactive Workstations

| Station | Apparati | Primary Interactions |
|---------|----------|---------------------|
| **Wet Bench A** | Erlenmeyer flasks (5), beakers (2), test tube rack (8), measuring cylinder | Pour, swirl, observe color change |
| **Wet Bench B** | Bunsen burner, tripod + gauze, heated beaker, stirrer + hotplate | Ignite, heat, stir, temperature control |
| **Analytical Corner** | Digital scale, buret, pH electrode | Measure mass, titrate, read pH |
| **Fume Hood** | Large-scale synthesis apparatus, scissor jack | Restricted reagent handling |
| **Reagent Shelves** | 12 reagent bottles, 2 wash bottles | Select, pour, rinse |

---

## 5. Five Vertical Slice Apparatus

The vertical slice implements five fully interactive apparati with complete physics, materials, and reaction integration:

### 5.1 Beaker (Cylindrical Glassware)

- **Geometry:** Cylinder with spout; radius 50-55mm, height 90-130mm
- **Materials:** Borosilicate glass (IOR 1.474) + liquid fill (Beer-Lambert)
- **Interactions:** Carry, place, pour into, pour from
- **Reaction States:** Color change, precipitate suspension, bubble generation
- **Poly Budget:** 850 triangles

### 5.2 Erlenmeyer Flask (Conical Synthesis Vessel)

- **Geometry:** Conical body (r_bottom 80mm, r_mid 30mm) + cylindrical neck
- **Materials:** Borosilicate glass, solution volume shader with meniscus
- **Interactions:** Carry, clamp to ring stand, reflux attachment, distillation neck
- **Reaction States:** Oscillating color (BZ reaction), precipitate crystals
- **Poly Budget:** 1,200 triangles

### 5.3 Bunsen Burner / Hotplate Assembly

- **Components:** Cast iron base, brass air collar, rubber gas hose, dual-cone flame geometry
- **Flame Materials:** Inner cone emission (18.0 intensity, cyan), outer cone emission (8.0, violet)
- **Interactions:** Ignite/extinguish, adjust air collar (rotable), place vessel on tripod/stirrer
- **Thermal Effects:** Temperature simulation via Cantera; heat emission shader on nearby objects
- **Poly Budget:** 2,400 triangles (including flame cones)

### 5.4 Digital Scale (Analytical Balance)

- **Display:** 7-segment LED readout shader (red on dark bezel)
- **Interactions:** Place object, tare, read mass (0.01g resolution)
- **Visual Feedback:** Animated digit transitions; weighing animation
- **Poly Budget:** 320 triangles

### 5.5 Buret (Volumetric Titration Apparatus)

- **Geometry:** Long precision cylinder (25mL capacity, 0.05mL graduations)
- **Interactions:** Clamp to burette stand, rotate stopcock, dispense droplets
- **Physics:** Droplet generation (particle sprites), meniscus tracking
- **Reaction States:** Color endpoint detection (phenolphthalein magenta transition)
- **Poly Budget:** 780 triangles

---

## 6. Mode Specifications

### 6.1 Sandbox Mode

**Access:** Unlocked from start (optional tutorial bypass) or via `unlock_all_for_sandbox()` API

**Features:**

| Feature | Specification |
|---------|---------------|
| **Reagent Catalog** | 100+ chemicals with SMILES/InChI, GHS hazard data, physical properties |
| **Time Dilation** | 0.1x (pause) to 100x (crystal growth); discrete presets: 0.5x, 1x, 2x, 5x, 10x, 25x, 50x |
| **Temperature Control** | -20°C to +300°C range; hotplate/Bunsen heating, ice bath cooling |
| **State Save/Restore** | Snapshot serialization to JSON; unlimited save slots |
| **Measurement Export** | CSV/JSON export of volumes, masses, temperatures, pH over time |
| **Molecule Visualizer** | RDKit 3D conformer generation (UFF force field); PDB export |

**Reagent Categories:**
- Inorganic acids/bases (HCl, H2SO4, NaOH, NH3)
- Solvents (ethanol, acetone, DCM, DMSO)
- Indicators (phenolphthalein, bromothymol blue, ferroin)
- Oxidation agents (KMnO4, H2O2, NaClO)
- Precipitating agents (AgNO3, BaCl2, Pb(NO3)2)
- Organic building blocks (malonic acid, salicylic acid)

### 6.2 Adventure Mode (Story Progression)

**Player Rank Hierarchy:**

| Rank | German Title | Completion Threshold |
|------|-------------|---------------------|
| Trainee | Labor-Praktikant (Day 1) | 0 levels |
| Apprentice | Chemielaborant-Lehrling | 1+ levels |
| Journeyman | Technischer Assistent | 4+ levels |
| Senior Synthesist | Synthese-Spezialist | 7+ levels |
| Master Alchemist | Meister-Alchemist | 10 levels |

**10-Level Quest Arc:**

| Level | Title | Core Mechanic | Fume Hood? |
|-------|-------|--------------|-----------|
| 1 | Labortaufe & Indikator | Acid-base neutralization + pH indicator | No |
| 2 | Die Iod-Uhr (Kinetik) | Briggs-Rauscher clock reaction timing | No |
| 3 | Oszillierende BZ-Reaktion | Non-equilibrium oscillating colors | No |
| 4 | Thermische Destillation | Fractional distillation setup | No |
| 5 | Goldener Regen | Lead(II) iodide precipitation | Yes |
| 6 | Chemisches Leuchten | Luminol chemiluminescence + UV | Yes |
| 7 | Thermische Sicherheitskontrolle | Exothermic runaway mitigation | Yes |
| 8 | Katalytische Elefanten-Zahnpasta | Catalytic decomposition foam eruption | Yes |
| 9 | Nichtlineare Oszillation | Mixed-oscillator showcase | Yes |
| 10 | Meister-Alchemist | Free mastery challenge | Optional |

**Safety Score System:**
- Start: 100 points
- Violation penalty: -25 points per infraction (missing fume hood, improper PPE)
- Feedback: Real-time German-language instruction with correction guidance

---

## 7. User Interface & HUD

### 7.1 HUD Architecture (Godot 4.x CanvasLayer)

```
ChemLabHUD (CanvasLayer)
├── TopBar
│   ├── QuestTitleLabel (current objective)
│   ├── QuestStepLabel (instruction detail)
│   ├── QuestProgressBar (visual progress indicator)
│   ├── SafetyBadge (OPTIMAL/CAUTION/HAZARD status)
│   └── ModeToggleButton (Story ↔ Sandbox)
├── LeftHandIndicator (Spatial billboard)
│   └── InteractionState color: READY(green) / HOVER(yellow) / HELD(blue)
├── RightHandIndicator (Spatial billboard)
│   └── Same as LeftHandIndicator
├── MeasurementReadouts (Floating 3D labels)
│   ├── TemperatureDisplay
│   ├── pHIndicatorBar
│   └── MassReadout
├── ScientificNotebook (Toggle panel)
│   ├── ReactionNotes
│   ├── MolecularDiagram
│   └── SafetyDataSheets
└── CelebrationOverlay (Quest completion effects)
    ├── BannerAnimation
    └── ParticleSystem
```

### 7.2 Floating Inspection Tooltips

- **Trigger:** Player approaches apparatus within 0.5m
- **Content:** Chemical name, formula, concentration, GHS hazard diamond
- **Style:** Translucent dark panel (`rgba(15, 20, 28, 0.85)`), cyan border, monospace font

### 7.3 Scientific Notebook

- **Toggled:** `N` key or voice command
- **Sections:**
  1. Reaction Log (chronological entries with timestamps)
  2. Molecular Sketcher (2D structure editor, exportable to SMILES)
  3. GHS Safety Reference (searchable chemical database)
  4. Quest Journal (story objectives and completion status)

### 7.4 Interaction States (Visual Feedback)

| State | Color (RGB) | Condition |
|-------|-------------|-----------|
| READY | `(0.0, 1.0, 0.35)` | Hand open, tracking active |
| HOVER | `(1.0, 0.85, 0.0)` | Within 50mm proximity of glassware |
| HELD | `(0.0, 0.55, 1.0)` | Glassware gripped, kinematic parenting |

### 7.5 Safety Alert Levels

| Status | Color (RGB) | Condition |
|--------|-------------|-----------|
| OPTIMAL | `(0.10, 0.95, 0.35)` | Safe handling, proper PPE |
| CAUTION | `(1.0, 0.65, 0.05)` | Approaching hazard, verbal warning |
| HAZARD_ALERT | `(1.0, 0.15, 0.15)` | Safety violation detected, score penalty |

---

## 8. Progression Systems

### 8.1 Global Laboratory Taxonomy (11 Archetypes)

The `GlobalLabRegistry` (`src/chemlab/world/lab_taxonomy.py`) defines 11 procedurally generated laboratory archetypes:

| # | Archetype ID | Title | Containment Level | Ventilation |
|---|--------------|-------|------------------|-------------|
| 1 | `academic_organic` | Universities Organisch-Chemisches Syntheselabor | Standard Class 1 | Ducted Fume Hood |
| 2 | `analytical_spectroscopy` | Zentrales Analytik-Institut | Standard Class 1 | Laminar Flow (HEPA H14) |
| 3 | `organic_medicinal` | Medicinal Chemistry Suite | Controlled Class 2 | Fume Hood Mandatory |
| 4 | `bsl_containment` | BSL-2/BSL-3 Biosafety Facility | High Containment Class 3 | Negative Pressure Glovebox |
| 5 | `solid_state_materials` | Festkorperchemie & Glovebox | High Containment Class 3 | Inert Atmosphere (< 0.1 ppm O2) |
| 6 | `electrochemistry` | Brennstoffzellen-Forschungszentrum | Controlled Class 2 | Explosion-Proof Ventilation |
| 7 | `industrial_pilot` | Industrielle Pilotanlage | Standard Class 1 | Scrubber Stack |
| 8 | `forensic_investigation` | Forensisches Kriminallabor | Controlled Class 2 | Activated Carbon Filter |
| 9 | `mobile_hazmat` | Mobile Notfall-Umweltlabor | Maximum Containment Class 4 | Positive Pressure Hazmat |
| 10 | `clandestine` | Improvised Clandestine Lab | Unregulated (High Risk) | Passive (Insufficient) |
| 11 | `orbital_microgravity` | Orbital Mikrogravitationslabor | Controlled Class 2 | Closed-Loop Life Support |

### 8.2 Equipment Registry

Comprehensive catalog (`EQUIPMENT_CATALOG`) with 50+ instruments including:
- NMR-400MHz, HPLC-UV-Vis, GC-MS, Raman HazMat identifier
- Analytical balances, pH meters, conductometers
- Gloveboxes, Schlenk lines, rotary evaporators
- Fume hoods, biosafety cabinets, autoclaves

### 8.3 Unlock System

| Item Type | Unlock Condition |
|-----------|-----------------|
| Apparatus (basic) | Story Level 1 |
| Apparatus (advanced) | Story Level 5 |
| Apparatus (glovebox/specialty) | Story Level 8 |
| Reagents (common) | Story Level 1 |
| Reagents (restricted) | Story Level 5 |
| Reagents (precursor) | Story Level 8 |
| Laboratory Archetypes | Story completion milestones |

---

## 9. Technical Architecture

### 9.1 Module Hierarchy

```
chemlab_core/
├── models.py              # Data classes (LiquidMixture, ReactionResult)
├── transport/             # IPC bridge contracts
│   ├── contracts.py       # Message schemas
│   └── websocket.py       # Socket.IO client
├── blender/               # Blender controller bridge
│   ├── controller.py     # bpy integration layer
│   └── scene_sync.py      # State synchronization
└── __init__.py

src/chemlab/
├── cv/                    # Computer vision input
│   ├── hand_tracker.py   # 21-landmark MediaPipe analysis
│   ├── one_euro_filter.py # Jitter attenuation
│   └── holistic_tracker.py # Full-body tracking
├── graphics/              # Rendering pipeline
│   ├── iris_xe_optimizer.py # Hardware profiling
│   └── design_tokens.py   # Material token registry
├── simulation/            # Physics & chemistry
│   ├── catalog.py        # Reagent definitions (100+)
│   ├── consequence.py    # Reaction outcome engine
│   ├── reaction_solver.py # ODE integration
│   ├── cantera_engine.py  # NIST thermodynamics
│   ├── rdkit_engine.py    # 3D conformer generation
│   └── time_controller.py # Dilation engine
├── story/                 # Adventure mode
│   ├── story_manager.py  # Quest state machine
│   └── total_syntheses.py # Advanced recipe chains
├── world/                 # Environment
│   ├── lab_taxonomy.py    # 11 archetypes + equipment
│   └── procedural_labs.py # Dynamic facility generation
├── safety/                # Hazard simulation
│   ├── ghg_signals.py     # GHS pictogram renderer
│   └── runaway_engine.py  # Thermal runaway modeling
└── desktop/               # Native GUI
    └── main_window.py     # PySide6 application

scripts/                   # Blender Python API
├── module_apparatus.py    # Glassware procedural generation
├── module_room.py         # Environment builder
└── chemlab_hud.gd        # Godot HUD controller

simulation/               # Standalone Python simulation
├── free_sim_engine.py    # Sandbox orchestrator
└── experiment_book.py    # Data persistence

tests/                    # Quality assurance
├── test_*.py             # Unit tests (214 tests)
├── headless_blender_test.py
└── validate_scene_assets.py
```

### 9.2 Reaction Solver Architecture

**State Machine:**
```
ReactionSolver
├── mix_liquids(a: LiquidMixture, b: LiquidMixture) -> LiquidMixture
├── apply_neutralization(mixture: LiquidMixture) -> ConsequenceResult
├── apply_precipitation(mixture: LiquidMixture) -> ConsequenceResult
├── apply_gas_evolution(mixture: LiquidMixture) -> ConsequenceResult
└── simulate_oscillator(mixture: LiquidMixture, dt: float) -> tuple[color, pH, temperature]
```

**Numerical Integration:**
- Adaptive Runge-Kutta 4 (RK4) for stiff ODE systems
- Maximum timestep: 50ms
- Stability bounds: NaN/Infinity detection with reset to last valid state

### 9.3 AI Reaction Bridge

- **Primary:** Google Gemini 2.5 Pro via `GoogleMediaBridge`
- **Fallback:** Local reaction prediction using `ReactionCatalog` heuristics
- **Safety:** All AI-generated reactions validated against known chemistry before execution

---

## 10. Asset & Performance Budgets

### 10.1 Iris Xe Compliance Matrix

| Metric | Budget | Enforcement |
|--------|--------|-------------|
| Total Triangles | <= 250,000 | `validate_scene_assets.py` |
| Material Count | <= 64 | Scene audit script |
| Draw Calls | <= 128 | GPU profiler |
| Texture VRAM | <= 96 MB (dedicated) | Memory partition plan |
| Shadow Maps | 512x512 cube (max 4) | EEVEE settings |
| Volumetric Tile Size | 16px (half-res) | Performance governor |

### 10.2 Quality Gate Pipeline

```
Pre-commit hooks (enforced):
1. ruff check + black format (Python)
2. mypy type validation
3. ESLint (JavaScript)

Pre-merge gates (automated CI):
4. Blender headless test (collection hierarchy, zero missing datablocks)
5. Asset budget scan (polygon count, material hygiene)
6. Reaction solver stability test (10,000-step integration, no NaN)
```

### 10.3 Blend File Validation

`chemlab.blend` must pass:
- Collection hierarchy: `01_Architecture` → `08_FX`
- Active camera in each scene
- Zero orphan datablocks
- All materials use Principled BSDF with valid inputs
- Scale applied on all objects (1.0, 1.0, 1.0)

---

## Appendix A: GDD Pillars Summary

| Pillar | Implementation | Validation |
|--------|---------------|------------|
| **Hard Science Simulation** | Cantera thermodynamics (NIST/CRC), RDKit 3D conformers, 100+ reagents with real SMILES/InChI | Unit test coverage > 95% |
| **Photorealistic Rendering** | Borosilicate IOR 1.474, Beer-Lambert absorption, volumetric meniscus | Visual benchmark suite |
| **Universal Accessibility** | Webcam hand tracking + 100% M&K fallback | Third-party accessibility audit |
| **Premium Education** | 10-level story arc, GHS safety training, quantitative feedback | Pedagogical effectiveness study |
| **Performance Guarantee** | Iris Xe optimizer, 720p@60 FPS envelope | Automated frame time profiling |

## Appendix B: Player Progression Loops

```
LOOP 1: TUTORIAL FLOW (Level 1-2)
├── Objective: Learn basic pour/swirl interactions
├── Feedback: Real-time pH indicator + color change
└── Reward: Unlock advanced reagents + next level

LOOP 2: KINETICS MASTERY (Level 3-5)
├── Objective: Time-dependent reactions, precipitation
├── Feedback: Oscillation curves, crystal growth animation
└── Reward: Fume hood clearance + restricted reagents

LOOP 3: SAFETY PROTOCOL (Level 6-8)
├── Objective: Handle hazardous reagents under containment
├── Feedback: Safety score penalties + German-language warnings
└── Reward: Glovebox access + specialty apparatus

LOOP 4: FREE MASTERY (Level 9-10)
├── Objective: Independent experimental design
├── Feedback: Consequence engine generates novel outcomes
└── Reward: Full sandbox + molecule visualizer + export tools
```

---

**Document Control:**  
Author: ChemLab Studio Game Director  
Review: Physics Lead, Graphics Lead, Input Specialist, QA Lead  
Approved: 2026-11-02  
**Next Review:** Pre-Alpha milestone (Q1 2027)