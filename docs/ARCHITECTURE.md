# ChemLab — Target System Architecture Specification
**Document ID:** `DOC-CHEMLAB-ARCH-001`  
**Version:** 1.0.0  
**Status:** Approved / Authoritative System Design  
**Date:** 2026-11-02  
**Target Platform:** Windows 11 Pro 64-bit (Standalone Executable)  
**Target Hardware:** Intel Core i5-1245U (15W cTDP), Intel Iris Xe Graphics (80 EUs, 128 MB VRAM aperture, 16 GB shared RAM)  
**Performance Target:** 60 FPS @ 1080p, <100 ms interaction latency, <1.5 GB total system memory  

---

## 1. System Vision & Architecture Paradigm

ChemLab is designed as a **standalone, high-performance, touchless 3D interactive virtual chemistry laboratory**.

### 1.1 Fundamental Architectural Principles

1. **Strict DCC Separation:** Blender is strictly a Development-Time Digital Content Creation (DCC) tool used for 3D modeling, UV unwrapping, procedural PBR texture generation, and simulation baking. **Blender is never a runtime dependency for the published game.**
2. **Authoritative Scientific Core:** All chemistry, thermodynamic balances, Arrhenius kinetics, vapor pressure buildups, and safety equations are executed by an authoritative scientific calculation engine (`chemistry/`). The rendering layer never invents chemical state.
3. **Decoupled Asynchronous Tracking:** Computer vision tracking (MediaPipe webcam hand/pose tracking) runs in an independent, low-priority process to prevent CPU thread starvation and GPU thermal throttling on 15W Intel U-series hardware.
4. **Resilient Intelligence Tier:** AI chemical reasoning follows a fail-safe tier from local inference to cloud APIs down to an authoritative, deterministic analytical chemistry floor.
5. **Deterministic Performance Budget:** The game runtime is built on Godot 4 utilizing the **Compatibility Renderer** (OpenGL ES 3.0 / WebGL 2) to guarantee stable 60 FPS on integrated Intel Iris Xe silicon.

---

## 2. High-Level System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            CHEMLAB STANDALONE GAME                                |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                            GAME RUNTIME (Godot 4)                           |  |
|  |  +---------------------------+  +----------------------------------------+  |  |
|  |  |    Rendering Pipeline     |  |          Gameplay Subsystems           |  |  |
|  |  |  - Compatibility (GLES3)  |  |  - Quest & Progression Manager         |  |  |
|  |  |  - 1080p Dynamic Res      |  |  - Reagent Inventory & Bench Storage   |  |  |
|  |  |  - Optimized Glass Shader |  |  - Experiment Book & Recipe System     |  |  |
|  |  |  - Particle VFX & Decals  |  |  - Sandbox Planetary Matrix (NMS)      |  |  |
|  |  +---------------------------+  +----------------------------------------+  |  |
|  |                                |                                            |  |
|  |  +-----------------------------+-----------------------------------------+  |  |
|  |  |                 Godot-to-Core Bridge Layer (IPC / C++)                |  |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  +-----------------------------------|-----------------------------------------+  |
|                                      | Local High-Speed IPC (Named Pipes/TCP)     |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  |                        AUTHORITATIVE SCIENTIFIC CORE                        |  |
|  |                                                                             |  |
|  |  +------------------------+  +-----------------------+  +----------------+  |  |
|  |  |  Thermodynamics        |  |  Chemical Kinetics    |  | Safety Physics |  |  |
|  |  |  - NIST Delta H / S / G|  |  - Arrhenius Engine   |  | - Fume Hood    |  |  |
|  |  |  - van 't Hoff K_eq    |  |  - Side-Reactions     |  | - Semenov BLEVE|  |  |
|  |  |  - Titration Curves    |  |  - Total Syntheses    |  | - GHS Hazard   |  |  |
|  |  +------------------------+  +-----------------------+  +----------------+  |  |
|  |                                                                             |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |  | Consolidated Reagent Database (>100 Authenticated Species)           |  |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------------+  |
|                                      ^                                            |
|                                      | Inter-Process Messages                     |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  |                        BACKGROUND WORKER DAEMONS                            |  |
|  |                                                                             |  |
|  |  +------------------------------------+  +-------------------------------+  |  |
|  |  |      Tracking Daemon (Vision)      |  |   Intelligence Daemon (AI)    |  |  |
|  |  |  - Webcam MediaPipe Vision (30 FPS)|  |  - Local Omniroute / LLM      |  |  |
|  |  |  - 1-Euro Adaptive Filter (60 FPS) |  |  - Multi-Provider Fallback    |  |  |
|  |  |  - Mouse / Keyboard Fallback       |  |  - Local Analytical Floor     |  |  |
|  |  +------------------------------------+  +-------------------------------+  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                       ^
                                       | Offline Asset Export (.glb / .gltf)
+--------------------------------------|--------------------------------------------+
|                    DEVELOPMENT-TIME DCC ASSET PIPELINE                            |
|  - Blender 5.2 EEVEE Next           - Google Media Harvesting                     |
|  - High-Poly Apparatus Models       - Procedural PBR Material Bake (AO/Norm/Rough)|
|  - MolecularNodes PDB Generator     - Draco Mesh Compression                      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Subsystem Specifications

### 3.1 `game/` — Godot 4 Standalone 3D Game Runtime
- **Engine Version:** Godot Engine 4.7 LTS (Compatibility Renderer).
- **Renderer Selection:** **Compatibility Renderer** (OpenGL ES 3.0 / WebGL 2).
  - *Rationale:* Eliminates Vulkan compute pipeline overhead on Intel Iris Xe. Reduces driver-side CPU overhead and memory bandwidth saturation, guaranteeing 60 FPS at 1080p within a 15W package TDP.
- **Glassware Rendering:** Optimized custom spatial shader using single-pass screen-space refraction with a constant Index of Refraction ($n = 1.458$ for Borosilicate glass 3.3). Avoids multipass ray-traced glass refraction.
- **Input Management:** Dual-mode input controller:
  - *Primary:* Touchless webcam tracking via IPC telemetry coordinates.
  - *Secondary:* Hardware mouse and keyboard fallback (`RayCast3D` pick-up, mouse wheel pour-tilt, right-click swirl).
- **Audio Subsystem:** Procedural positional SFX (liquid pouring, sizzling, effervescence, glass clinking, vacuum suction, explosion shockwaves).

### 3.2 `chemistry/` — Authoritative Scientific Core
The authoritative calculation engine unifies all scientific code into a single, cohesive Python package:

```
chemistry/
├── __init__.py
├── thermodynamics/
│   ├── __init__.py
│   ├── database.py             # NIST / CRC standard properties (H, S, Cp, MW, rho)
│   └── engine.py               # Hess enthalpy, entropy, Gibbs, van 't Hoff, titration
├── kinetics/
│   ├── __init__.py
│   ├── arrhenius.py            # Arrhenius rate constants, temperature acceleration
│   ├── solver.py               # Stiff ODE numerical integration & concentration profiles
│   └── side_reactions.py       # Non-ideal side-products, addition-order hazards, tarring
├── safety/
│   ├── __init__.py
│   ├── ghs.py                  # GHS hazard pictograms, H/P statements, exposure limits
│   ├── fume_hood.py            # ANSI/AIHA Z9.5 face velocity & aerodynamic containment
│   └── thermal_runaway.py      # Semenov thermal explosion, Antoine VP, stopper pop
├── cheminformatics/
│   ├── __init__.py
│   └── rdkit_bridge.py         # SMILES to 3D conformer, UFF minimization, Lipinski
└── catalog/
    ├── __init__.py
    └── reagents.py             # Consolidated registry of 100+ chemical reagents
```

### 3.3 `tracking/` — Computer Vision & Gesture Recognition
- **Execution Architecture:** Runs in an isolated OS process (`chemlab-tracker.exe`).
- **Vision Pipeline:**
  1. Captures camera frames via OpenCV (`cv2.VideoCapture`).
  2. Submits frames to MediaPipe Hands / Holistic at 30 FPS.
  3. Applies the **1-Euro Filter** to eliminate high-frequency spatial jitter.
  4. Classifies gestures: `PINCH`, `GRAB`, `POUR` ($\text{wrist tilt} > 38^\circ$), `SWIRL`, and `POINT`.
  5. Translates body poses into virtual lab locomotion and workstation zoning.
  6. Dispatches serialized telemetry packets to Godot over local IPC at 60 Hz.
- **Automatic Fallback:** If no webcam is detected or tracking confidence falls below $0.50$, input falls back to mouse/keyboard without interrupting simulation.

### 3.4 `intelligence/` — Multi-Provider Chemical Reasoning
- **Fallback Architecture:**
  $$\text{Local Omniroute / ONNX} \longrightarrow \text{NVIDIA NIM} \longrightarrow \text{Google Gemini} \longrightarrow \text{Local Deterministic Floor}$$
- **Local Analytical Floor:** When offline or unauthenticated, the engine falls back to analytical Arrhenius kinetics, balancing equations deterministically without generating invalid chemical formulas.

### 3.5 `gameplay/` — Progression, Quests & Simulation Modes
- **Story Progression:** 10-tier progression from *Trainee* to *Master Alchemist* (`story_manager.py`).
- **Safety Auditing:** Real-time OSHA compliance evaluation awarding safety points and penalizing violations (unshielded reactions, sash opened high with volatile solvents, inverted water-acid addition).
- **Sandbox Matrix:** Unlimited access to 100+ reagents, variable gravity ($0$ to $2g$), variable barometric pressure ($0.1$ to $10\text{ atm}$), and time acceleration up to $50\times$.
- **Experiment Book:** In-game lab notebook recording stoichiometric ratios, yield percentages, reaction observations, and exportable JSON recipes.

### 3.6 `assets/` — Blender 5.2 DCC Asset Creation Pipeline
- **Role:** Purely an offline authoring and simulation bake pipeline.
- **Artifacts:**
  - Standard GLB/glTF 2.0 binaries (`assets/models/*.glb`) with Draco mesh compression.
  - Packed PBR texture maps (Albedo, Normal, Roughness/AO/Metalness packed into single channels).
  - PDB molecular structures pre-baked via RDKit and MolecularNodes.

---

## 4. Communication & Runtime Contracts

### 4.1 Godot $\longleftrightarrow$ Scientific Core IPC Contract

Communication between the Godot game client and the Scientific Core daemon occurs over a high-speed local TCP socket (`127.0.0.1:8765`) or Windows Named Pipe (`\\.\pipe\chemlab_core`):

#### 1. Mix Reagents Request
```json
{
  "request_id": "req_001",
  "command": "MIX_REAGENTS",
  "payload": {
    "vessel_id": "beaker_01",
    "reagents": [
      { "id": "salicylic_acid", "moles": 0.05 },
      { "id": "acetic_anhydride", "moles": 0.08 }
    ],
    "catalyst": "h2so4",
    "temperature_c": 65.0,
    "addition_order_correct": true,
    "in_fume_hood": true
  }
}
```

#### 2. Simulation Step Response
```json
{
  "request_id": "req_001",
  "status": "SUCCESS",
  "data": {
    "vessel_id": "beaker_01",
    "reaction_name": "Aspirin-Synthese",
    "conversion_ratio": 0.94,
    "temperature_c": 68.2,
    "is_exothermic": true,
    "delta_h_kj_mol": -18.4,
    "color_rgba": [0.96, 0.96, 0.98, 0.90],
    "turbidity": 0.65,
    "precipitate_formed": true,
    "precipitate_name": "Acetylsalicylsäure",
    "bubbles_per_second": 0.0,
    "side_products": [
      { "name": "Essigsäure", "mass_fraction": 0.06 }
    ],
    "safety_warnings": []
  }
}
```

### 4.2 Tracking Daemon $\longleftrightarrow$ Godot Runtime Contract

Dispatched from `chemlab-tracker` to Godot at 60 Hz:

```json
{
  "timestamp_ms": 1730548900120,
  "hand": "RIGHT",
  "gesture": "POUR",
  "cursor_position": { "x": 0.524, "y": 0.418, "z": 0.680 },
  "wrist_tilt_degrees": 48.5,
  "pour_flow_rate": 0.75,
  "pinch_distance": 0.12,
  "is_grabbing": true,
  "confidence": 0.98
}
```

---

## 5. Hardware Budgets for Intel Iris Xe (15W TDP)

To sustain a rock-solid 60 FPS on the Dell Latitude 5530 (Core i5-1245U, 16 GB RAM, Iris Xe), the game runtime strictly enforces the following resource budgets:

| Metric | Target Budget | Upper Safe Limit | Enforcement Strategy |
|---|---|---|---|
| **Frame Rate** | 60 FPS (16.6 ms) | $\ge 45$ FPS (22.2 ms) | Dynamic resolution scaling down to 77% (XeSS/CAS) |
| **Draw Calls** | $\le 120$ per frame | 180 per frame | Mesh instancing for test tubes and glassware |
| **Scene Triangles** | $\le 200,000$ tris | 350,000 tris | 3-tier LOD switching (LOD0: 15k, LOD1: 5k, LOD2: 1.5k) |
| **Dedicated VRAM** | $\le 110$ MB | 128 MB aperture | Texture mip-clamping, zero uncompressed 4K textures |
| **Shared System RAM** | $\le 850$ MB | 1,500 MB | CAS SQLite LRU asset cache eviction |
| **Texture Formats** | BC1 / BC7 (1024²) | 2048² (hero bench only) | Automated asset pipeline mipmap baking |
| **CPU Utilization** | $\le 25\%$ (3 cores) | 35% package power | Tracking worker capped at 30 FPS inference |
| **Package Power** | $\le 15$ Watts | 20 Watts short burst | Eliminates thermal clock throttling |

---

## 6. Implementation Roadmap

### Phase 0: Foundation Audit & Architecture (Completed)
- [x] Complete scientific codebase audit across all modules and tests.
- [x] Document current state, duplications, and packaging limitations (`CURRENT_STATE_AUDIT.md`).
- [x] Formulate target standalone game architecture (`ARCHITECTURE.md`).

### Phase 1: Core Consolidation & Packaging (Immediate Next Step)
- [ ] Consolidate all duplicate chemistry modules into authoritative `src/chemlab/chemistry/`.
- [ ] Merge `simulation/catalog.py` and `safety_simulation/ghs.py` into single unified reagent database.
- [ ] Update `pyproject.toml` to package all core modules cleanly.
- [ ] Implement headless IPC daemon interface for the authoritative core.

### Phase 2: Standalone Godot 4 Client & Asset Pipeline
- [ ] Initialize Godot 4.7 project with Compatibility renderer configured for Intel Iris Xe.
- [ ] Build automated Blender export script: `scripts/export_glb_assets.py` (converting `chemlab.blend` to Draco-compressed GLBs).
- [ ] Implement Godot IPC client consuming Scientific Core simulation packets.
- [ ] Implement custom glass shader and liquid filling shaders in Godot.

### Phase 3: Tracking & Gameplay Integration
- [ ] Package `chemlab-tracker` daemon streaming 1-Euro filtered landmarks.
- [ ] Implement Godot touchless cursor and gesture interaction handlers.
- [ ] Implement 10-level Story Mode quest progression in Godot.
- [ ] Validate 60 FPS performance on Intel Iris Xe under full thermal load.
