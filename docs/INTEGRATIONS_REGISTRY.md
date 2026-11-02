# ChemLab Integrations & External Dependency Registry

## 1. Executive Summary & Legal Compliance Overview

This document provides a comprehensive security, licensing, architectural, and dependency audit for **ChemLab** (Interactive Virtual Chemistry Laboratory). 

ChemLab is prepared for commercial distribution on the **Steam** platform (Windows 11 / Steam Deck / Proton / Linux). A primary objective of this audit is to verify compliance with:
1. **Open Source Licensing and Commercial Compatibility**: Ensuring no viral copyleft licenses (e.g., GPL-2.0, GPL-3.0) infect or encumber the proprietary commercial game runtime distributed via Steam.
2. **Copyleft Isolation Boundaries**: Enforcing strict architectural isolation (clean decoupling via standard file formats, CLI subprocess boundaries, or out-of-process IPC) for tools subject to GPL.
3. **Data Privacy and Biometric Protection**: Ensuring that computer vision webcam feeds used for hand tracking remain strictly in volatile memory (RAM) and are never persisted to disk or transmitted over networks, complying with GDPR, CCPA, and COPPA.
4. **Offline Resilience & Air-Gapped Simulation**: Guaranteeing that core thermodynamic, kinetic, and chemical reactions operate 100% deterministically offline without requiring mandatory third-party cloud API connectivity.

---

## 2. Master Dependency & Licensing Audit Matrix

| Category | Component | Version / Commit | License | Steam Distribution Compatibility | Dependency Type | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Game Engines & 3D** | Godot Engine | 4.3 / 4.x LTS | MIT | 100% Compatible | Runtime | Verified |
| **Game Engines & 3D** | Blender | 5.2 | GPL-3.0 | Compatible (Asset Creation ONLY; strictly decoupled) | Development | Verified |
| **Game Engines & 3D** | Kenney Assets | v1.0+ | CC0 1.0 Universal | 100% Compatible (Public Domain) | Runtime Asset | Verified |
| **Game Engines & 3D** | Poly Haven | Current Library | CC0 1.0 Universal | 100% Compatible (Public Domain) | Runtime Asset | Verified |
| **Scientific Computing** | Cantera | 3.0.0+ | BSD-3-Clause | 100% Compatible | Runtime | Verified |
| **Scientific Computing** | RDKit | 2024.03+ | BSD-3-Clause | 100% Compatible | Runtime | Verified |
| **Scientific Computing** | ChemPy | 0.8.4+ | BSD-2-Clause | 100% Compatible | Runtime | Verified |
| **Scientific Computing** | SciPy / NumPy | NumPy >= 2.0, SciPy >= 1.13 | BSD-3-Clause | 100% Compatible | Runtime | Verified |
| **Scientific Computing** | Open Babel | 3.1.1+ | GPL-2.0 | Compatible via Subprocess / Offline Tooling ONLY | Dev / Tooling | Isolated |
| **Scientific Computing** | NIST WebBook & PubChem | REST v2 / PUG-REST | US Gov Public Domain | 100% Compatible | Dev Ingest / Online | Verified |
| **Computer Vision** | MediaPipe | >= 1.0.0 | Apache-2.0 | 100% Compatible | Runtime | Verified |
| **Computer Vision** | OpenCV | >= 4.8.0 | Apache-2.0 | 100% Compatible | Runtime | Verified |
| **Computer Vision** | ONNX Runtime | 1.18+ | MIT | 100% Compatible | Runtime | Verified |
| **AI Providers** | Local ONNX / llama.cpp | b3000+ / GGUF | MIT | 100% Compatible | Runtime / DLC | Verified |
| **AI Providers** | Omniroute Local Gateway | v1.x (localhost:20128) | MIT / Proprietary | 100% Compatible | Runtime / Dev | Verified |
| **AI Providers** | NVIDIA NIM | API / BioNeMo | NVIDIA Cloud Terms | Compatible (Opt-in Cloud API) | Optional Cloud | Verified |
| **AI Providers** | Google Gemini 2.5 Pro | v1 / Google GenAI SDK | Google APIs Terms | Compatible (Opt-in Cloud API) | Optional Cloud | Verified |
| **MCP & Agent Tooling**| Blender MCP | 1.0.1 | MIT | Development-Time Only (Not Distributed) | Development | Verified |
| **MCP & Agent Tooling**| Playwright MCP | 1.48+ | Apache-2.0 | Development-Time Only (Not Distributed) | Dev / Testing | Verified |
| **MCP & Agent Tooling**| Windows MCP | 1.0 | MIT / Proprietary | Development-Time Only (Not Distributed) | Development | Verified |
| **MCP & Agent Tooling**| Context7 MCP | 1.0 | SaaS / Dev Terms | Development-Time Only (Not Distributed) | Development | Verified |
| **Desktop & UI** | PySide6 (Qt for Python)| 6.7+ | LGPL-3.0 | Compatible (Dynamically linked shared libraries) | Runtime | Verified |
| **Networking** | websockets | >= 12.0 | BSD-3-Clause | 100% Compatible | Runtime | Verified |
| **Data Validation** | Pydantic | >= 2.0 | MIT | 100% Compatible | Runtime | Verified |

---

## 3. Detailed Component Audits

### 3.1 Game Engines, 3D DCC, and Asset Marketplaces

#### 1. Godot Engine 4.x
- **Component Name & Homepage URL:** Godot Engine (https://godotengine.org/)
- **Version / Commit:** Godot Engine 4.3 / 4.x LTS
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT License.
  - Steam Compatibility: Fully compatible without royalty obligations or source disclosure. The MIT license grants permission to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software. Godot binaries can be compiled into proprietary executables, linked against the Steamworks SDK, and protected by Steam DRM without license conflict.
- **Exact Purpose in ChemLab:**
  - Powers the real-time 3D interactive laboratory rendering, spatial UI HUD (`scripts/chemlab_hud.gd`), particle emission systems (bubbles, aerosol vapors, precipitate clouding), physical collision handling, and camera perspective management.
- **Installation & Verification Status:**
  - Export templates configured; GDScript HUD modules integrated. Verified through scene asset validation routines.
- **Runtime vs Development Dependency:**
  - Runtime Dependency (compiled into game client package).
- **Security, Privacy & Sandboxing Assessment:**
  - Runs in unprivileged user space. Fully compatible with Steam client sandboxing and SteamOS / Proton runtime environments. No background telemetry or external network callbacks are enabled in core release builds.

#### 2. Blender 5.2
- **Component Name & Homepage URL:** Blender (https://www.blender.org/)
- **Version / Commit:** Blender 5.2 (Daily / Mainline builds)
- **License & Commercial Compatibility for Steam distribution:**
  - License: GNU General Public License v3.0 (GPL-3.0).
  - Steam Compatibility: **CRITICAL ARCHITECTURAL BOUNDARY**. GPL-3.0 is a strong copyleft license. Bundling Blender binaries (`blender.exe`) or dynamically linking Blender C/C++ libraries into the Steam runtime distribution would require open-sourcing the entire game under GPL-3.0. Therefore, Blender 5.2 is **STRICTLY RESTRICTED TO ASSET CREATION ONLY**. 
  - 3D models (borosilicate glassware, benches, instruments), materials, and animations created in Blender are exported as neutral standard formats (GLTF 2.0, OBJ, FBX, baked texture maps, and JSON descriptors). Under Free Software Foundation (FSF) legal doctrine, output files produced by GPL software are not derivative works of the software itself and carry no copyleft encumbrance.
- **Exact Purpose in ChemLab:**
  - Offline digital content creation (DCC), procedural laboratory architecture generation (`scripts/module_room.py`, `scripts/module_furniture.py`, `scripts/module_apparatus.py`), EEVEE Next photorealistic shader authoring (borosilicate refractive index, absorption spectrum, volumetric liquids), Mantaflow fluid physics baking (`scripts/module_fluid_simulation.py`), and automated headless asset quality checks (`tests/headless_blender_test.py`).
- **Installation & Verification Status:**
  - Installed in the developer environment. Operational testing verified via `blender_live_bridge.py` and `tests/headless_blender_test.py`.
- **Runtime vs Development Dependency:**
  - Development Dependency ONLY (strictly excluded from final Steam release builds).
- **Security, Privacy & Sandboxing Assessment:**
  - Confined to the developer workstation. Network activity is limited to a local loopback TCP socket (`127.0.0.1:8765`) used during live authoring bridge sessions. No outbound public internet connections.

#### 3. Kenney Assets
- **Component Name & Homepage URL:** Kenney (https://kenney.nl/)
- **Version / Commit:** Kenney Asset Kits (Furniture Kit, Sci-Fi Kit, Interface Pack, Audio Pack - v1.0+)
- **License & Commercial Compatibility for Steam distribution:**
  - License: Creative Commons Zero 1.0 Universal (CC0 1.0 Public Domain Dedication).
  - Steam Compatibility: 100% compatible. CC0 waives all copyright, neighboring, and related rights to the maximum extent permitted by law. Assets can be embedded into commercial closed-source games, modified, redistributed, and sold on Steam without royalties, license fees, or mandatory attribution (attribution retained in CREDITS.md as a best practice).
- **Exact Purpose in ChemLab:**
  - Base geometry and meshes for laboratory fixtures, dials, switches, generic cleanroom apparatus, interface iconography, and tactile audio Foley effects (clicks, level-up chimes, knob twists in `audio/`).
- **Installation & Verification Status:**
  - Packaged in asset caches (`storage/asset_cache.py`, `audio/`). Verification completed via automated asset integrity tests (`tests/validate_scene_assets.py`).
- **Runtime vs Development Dependency:**
  - Runtime Asset Dependency (embedded into compiled game archives).
- **Security, Privacy & Sandboxing Assessment:**
  - Static binary data (Wavefront OBJ, GLTF, WAV audio). Contains no executable bytecode or macros. Processed exclusively through standard engine asset parsers.

#### 4. Poly Haven
- **Component Name & Homepage URL:** Poly Haven (https://polyhaven.com/)
- **Version / Commit:** Poly Haven Asset Library (HDRI Haven, Texture Haven - Current Release)
- **License & Commercial Compatibility for Steam distribution:**
  - License: Creative Commons Zero 1.0 Universal (CC0 1.0 Public Domain Dedication).
  - Steam Compatibility: 100% compatible. Freely usable in commercial titles distributed on Steam without copyright restrictions or royalty encumbrance.
- **Exact Purpose in ChemLab:**
  - High dynamic range environment maps (HDRIs) providing photorealistic laboratory lighting, glass specular reflections, and chromatic dispersion. PBR texture sets (cleanroom tiles, brushed aluminum, stainless steel bench tops).
- **Installation & Verification Status:**
  - Ingested via asset pipeline (`ASSET_PIPELINE_EEVEE_SPEC.md`). Verified in visual renderer checks.
- **Runtime vs Development Dependency:**
  - Runtime Asset Dependency (compiled textures and pre-filtered radiance maps).
- **Security, Privacy & Sandboxing Assessment:**
  - Passive raster image formats (EXR, HDR, PNG). Zero active code execution vectors.

---

### 3.2 Scientific Computing & Chemical Simulation

#### 5. Cantera
- **Component Name & Homepage URL:** Cantera (https://cantera.org/)
- **Version / Commit:** Cantera 3.0.0+ / Python bindings
- **License & Commercial Compatibility for Steam distribution:**
  - License: BSD-3-Clause License.
  - Steam Compatibility: 100% compatible. Permissive BSD license permits inclusion in proprietary commercial applications provided that copyright notices and the disclaimer are retained in product documentation.
- **Exact Purpose in ChemLab:**
  - Core thermodynamics and chemical equilibrium engine (`src/chemlab/simulation/cantera_engine.py`). Computes real-world Gibbs free energy ($\Delta G^\circ$), reaction enthalpies ($\Delta H^\circ$), equilibrium constants ($K_{eq}$), heat capacities ($C_p$), and phase equilibrium using authentic NIST/CRC thermodynamic polynomial data without invented or pseudo-scientific approximations.
- **Installation & Verification Status:**
  - Implemented in `src/chemlab/simulation/cantera_engine.py`. Includes unit-tested graceful fallbacks for environments without compiled C++ binary extensions. Fully verified via `tests/test_cantera_engine.py`.
- **Runtime vs Development Dependency:**
  - Runtime Dependency (bundled as wheel or embedded C++ library in Steam package).
- **Security, Privacy & Sandboxing Assessment:**
  - Fully local, in-memory numerical computation. No external socket calls or file writes during simulation steps. Integrates step-count limits and numerical bounds to prevent denial-of-service hangs from stiff differential equation solvers.

#### 6. RDKit
- **Component Name & Homepage URL:** RDKit (https://www.rdkit.org/)
- **Version / Commit:** RDKit 2024.03+ (rdkit-pypi)
- **License & Commercial Compatibility for Steam distribution:**
  - License: BSD-3-Clause License.
  - Steam Compatibility: 100% compatible with commercial distribution on Steam. Permissive terms permit embedding in proprietary binaries without source code release.
- **Exact Purpose in ChemLab:**
  - Cheminformatics and molecular geometry engine (`src/chemlab/simulation/rdkit_engine.py`). Parses SMILES and InChI identifiers, generates 3D atomic coordinates using distance geometry, minimizes energy via Universal Force Field (UFF) and MMFF94, and produces atomic coordinates (PDB/MolBlock) for 3D molecular ball-and-stick rendering.
- **Installation & Verification Status:**
  - Implemented in `src/chemlab/simulation/rdkit_engine.py` with mockable contracts for continuous integration. Verified via `tests/test_rdkit_engine.py`.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - In-process native execution. Input SMILES strings are strictly validated against maximum character length and syntactical grammar before parsing, mitigating potential native memory corruption or C++ buffer overflow vulnerabilities.

#### 7. ChemPy
- **Component Name & Homepage URL:** ChemPy (https://github.com/bjodah/chempy)
- **Version / Commit:** ChemPy 0.8.4+
- **License & Commercial Compatibility for Steam distribution:**
  - License: BSD-2-Clause License.
  - Steam Compatibility: 100% compatible. Permissive BSD license requires only standard copyright disclaimer retention.
- **Exact Purpose in ChemLab:**
  - Stoichiometric matrix balancing, equilibrium concentration calculations, acid-base titration curve simulations, ionic solubility product ($K_{sp}$) evaluations, and electrochemistry Nernst equation solvers.
- **Installation & Verification Status:**
  - Integrated into simulation packages (`src/chemlab/simulation/reaction_solver.py`, `src/chemlab/simulation/side_reactions.py`). Verified in unit test suite.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Pure Python library. Runs in sandboxed memory, zero OS-level access, zero network operations.

#### 8. SciPy / NumPy
- **Component Name & Homepage URL:** SciPy (https://scipy.org/) & NumPy (https://numpy.org/)
- **Version / Commit:** NumPy >= 2.0.0, SciPy >= 1.13.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: BSD-3-Clause License.
  - Steam Compatibility: 100% compatible. Permissive license allows proprietary bundling on Steam.
- **Exact Purpose in ChemLab:**
  - Matrix algebra, 3D coordinate transformations for computer vision tracking (`src/chemlab/cv/one_euro_filter.py`), numerical Ordinary Differential Equation (ODE) integration for oscillating clock reactions (Belousov-Zhabotinsky, Briggs-Rauscher), and statistical filtering for hand jitter reduction.
- **Installation & Verification Status:**
  - Declared in `pyproject.toml`. Installed and active across all test suites.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Production-grade, highly audited scientific computing stack. Operates strictly in user space with bounded memory buffers.

#### 9. Open Babel
- **Component Name & Homepage URL:** Open Babel (https://openbabel.org/)
- **Version / Commit:** Open Babel 3.1.1+
- **License & Commercial Compatibility for Steam distribution:**
  - License: GNU General Public License v2.0 (GPL-2.0).
  - Steam Compatibility: **CRITICAL ARCHITECTURAL BOUNDARY**. GPL-2.0 is copyleft. Direct in-process linking (C++ API or shared library binding) would obligate ChemLab to be released under GPL-2.0.
  - Architectural Isolation Protocol:
    1. Runtime Default: All runtime cheminformatics in ChemLab are handled exclusively by RDKit (BSD-3-Clause), avoiding any runtime requirement for Open Babel.
    2. Tooling Usage: When used for legacy molecular file format conversions (e.g., legacy CML to MolBlock), Open Babel is executed strictly as an **external independent CLI subprocess** (`obabel.exe`), exchanging data via standard input/output pipes with clean serialization boundaries, adhering strictly to FSF guidelines for non-derivative aggregate works.
- **Exact Purpose in ChemLab:**
  - Batch data conversion utility for ingesting third-party chemical structure databases during catalog preparation (`simulation/catalog.py`).
- **Installation & Verification Status:**
  - Configured as optional offline preprocessing tool. Not required for running standard game loops or passing CI test gates.
- **Runtime vs Development Dependency:**
  - Development / Tooling Dependency ONLY.
- **Security, Privacy & Sandboxing Assessment:**
  - Subprocess invocations employ strict argument whitelisting (no arbitrary user input passed directly to command line), execution timeouts (10 seconds), and restricted working directories.

#### 10. NIST Chemistry WebBook & PubChem APIs
- **Component Name & Homepage URL:** NIST Chemistry WebBook (https://webbook.nist.gov/chemistry/) & PubChem (https://pubchem.ncbi.nlm.nih.gov/)
- **Version / Commit:** NIST SRD 69 / PubChem PUG-REST API v2
- **License & Commercial Compatibility for Steam distribution:**
  - License: US Government Work (Public Domain) / NIH Open Data.
  - Steam Compatibility: 100% compatible. Public domain scientific data can be incorporated into commercial products without licensing fees.
- **Exact Purpose in ChemLab:**
  - Source data for authentic thermochemical constants, standard molar enthalpies of formation ($\Delta H_f^\circ$), heat capacities ($C_p$), GHS hazard pictograms, and CAS registry identifiers.
- **Installation & Verification Status:**
  - Pre-cached into offline database files (`storage/local_store.py`, `simulation/catalog.py`). Eliminates mandatory internet connectivity during gameplay.
- **Runtime vs Development Dependency:**
  - Development-time data ingestion with optional live runtime lookup when online.
- **Security, Privacy & Sandboxing Assessment:**
  - External requests are encrypted via HTTPS (TLS 1.3). Response payloads are validated against strict JSON schemas before database storage. No player telemetry is transmitted.

---

### 3.3 Computer Vision & Natural Interaction

#### 11. MediaPipe
- **Component Name & Homepage URL:** Google MediaPipe (https://developers.google.com/mediapipe)
- **Version / Commit:** MediaPipe >= 1.0.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: Apache License 2.0.
  - Steam Compatibility: 100% compatible. Apache-2.0 allows commercial use, binary modification, and distribution in closed-source commercial video games.
- **Exact Purpose in ChemLab:**
  - Real-time 21-point 3D hand landmark estimation (`src/chemlab/cv/hand_tracker.py`) and holistic body pose tracking (`src/chemlab/cv/holistic_tracker.py`). Detects pinch, grip, pour, and shake gestures in 60 FPS from standard consumer webcams.
- **Installation & Verification Status:**
  - Declared in `pyproject.toml`. Verified in unit and synthetic landmark tests (`tests/test_hand_tracker.py`, `tests/test_holistic_tracker.py`).
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - **STRICT ZERO-PERSISTENCE BIOMETRIC PRIVACY POLICY**: Video frames from the user's webcam are processed directly in volatile RAM buffers. No video frames, photographs, or raw biometric coordinate recordings are ever saved to the local file system or transmitted across any network interface. Tensor memory is immediately overwritten on the subsequent frame.

#### 12. OpenCV (Open Source Computer Vision Library)
- **Component Name & Homepage URL:** OpenCV (https://opencv.org/)
- **Version / Commit:** opencv-python >= 4.8.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: Apache License 2.0 (OpenCV 4.5+).
  - Steam Compatibility: 100% compatible. Permissive Apache-2.0 terms allow binary bundling and commercial monetization.
- **Exact Purpose in ChemLab:**
  - Low-level video stream capture from USB webcams, color-space conversion (BGR to RGB), frame decimation, visual HUD overlay rendering, and synthetic video feed generation for headless test suites (`chemlab_core/vision/synthetic.py`).
- **Installation & Verification Status:**
  - Declared in `pyproject.toml`. Verified in test suite.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Accesses local hardware camera devices exclusively via standard OS media APIs (Windows Media Foundation / Linux V4L2). Camera capture requires explicit user opt-in in settings and is inactive by default.

#### 13. ONNX Runtime
- **Component Name & Homepage URL:** ONNX Runtime (https://onnxruntime.ai/)
- **Version / Commit:** ONNX Runtime 1.18+ (DirectML / CPU Execution Providers)
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT License.
  - Steam Compatibility: 100% compatible. Permissive MIT license allows proprietary closed-source deployment.
- **Exact Purpose in ChemLab:**
  - Edge acceleration for custom gesture recognition classifiers and hardware optimization on Intel Iris Xe integrated graphics (`src/chemlab/graphics/iris_xe_optimizer.py`).
- **Installation & Verification Status:**
  - Integrated with fallback execution paths. Validated in GPU optimization unit tests (`tests/test_iris_xe_optimizer.py`).
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - In-process execution. Only loads locally signed, verified ONNX model graphs. Model inputs and outputs are strictly typed arrays; no arbitrary code execution is permitted within the ONNX execution engine.

---

### 3.4 AI Providers, LLM Runtimes & Gateways

#### 14. Local ONNX Runtime / llama.cpp
- **Component Name & Homepage URL:** llama.cpp (https://github.com/ggerganov/llama.cpp) / ONNX Runtime (https://onnxruntime.ai/)
- **Version / Commit:** llama.cpp b3000+ / GGUF quantized models
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT License.
  - Steam Compatibility: 100% compatible. MIT license allows shipping compiled inference binaries alongside commercial games or as optional free DLC content on Steam.
- **Exact Purpose in ChemLab:**
  - Completely local, offline AI laboratory assistant ("Reagent Computer" in `src/chemlab/ai/reagent_computer.py`). Answers natural-language chemical questions, explains reaction mechanisms, assists in experiment troubleshooting, and provides in-game laboratory safety guidance without latency or external server dependencies.
- **Installation & Verification Status:**
  - Implemented in `src/chemlab/ai/reagent_computer.py` with mockable fallback for CI environments. Verified in `tests/test_ai_reagent_computer.py`.
- **Runtime vs Development Dependency:**
  - Runtime Dependency (optional local model pack).
- **Security, Privacy & Sandboxing Assessment:**
  - 100% air-gapped execution. All user queries, gameplay states, and outputs stay on the local device. Model outputs are parsed through strict Pydantic schemas, preventing prompt-injection attacks from triggering unauthorized state mutations.

#### 15. Omniroute Local Gateway
- **Component Name & Homepage URL:** Omniroute Local Gateway (Internal Architecture: `http://localhost:20128`)
- **Version / Commit:** Omniroute v1.x (Unified Local LLM Routing Gateway)
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT / ChemLab Proprietary Architecture.
  - Steam Compatibility: 100% compatible.
- **Exact Purpose in ChemLab:**
  - Acts as a local multiplexer and protocol adapter (`src/chemlab/ai/omniroute_bridge.py`), dynamically routing AI requests between local inference backends (Ollama, llama.cpp, vLLM) and optional cloud endpoints based on user configuration and hardware capability.
- **Installation & Verification Status:**
  - Fully integrated and verified with automated mock endpoints in `tests/test_omniroute_ai_bridge.py`.
- **Runtime vs Development Dependency:**
  - Runtime & Development Gateway.
- **Security, Privacy & Sandboxing Assessment:**
  - Bound strictly to the local loopback interface (`127.0.0.1:20128` / `localhost`). External network interfaces (`0.0.0.0`) are explicitly refused. Uses local token authentication and strict CORS headers to protect against Cross-Site Request Forgery (CSRF).

#### 16. NVIDIA NIM (Inference Microservices)
- **Component Name & Homepage URL:** NVIDIA NIM (https://www.nvidia.com/en-us/ai/)
- **Version / Commit:** BioNeMo & Molecular Simulation Microservices API
- **License & Commercial Compatibility for Steam distribution:**
  - License: NVIDIA Cloud Software License / API Terms of Service.
  - Steam Compatibility: Compatible as an **OPT-IN CLOUD ENHANCEMENT**. The game client does not bundle proprietary NVIDIA server binaries; users or developers provide their own API credentials.
- **Exact Purpose in ChemLab:**
  - Cloud-accelerated deep molecular conformations, protein binding affinity scoring, and advanced kinetic reaction parameter estimation for advanced research-tier sandbox gameplay.
- **Installation & Verification Status:**
  - Supported via API connector in `src/chemlab/ai/reagent_computer.py`. Tested via mocked API contracts in CI.
- **Runtime vs Development Dependency:**
  - Optional Runtime Cloud Integration (Game functions 100% offline if unconfigured).
- **Security, Privacy & Sandboxing Assessment:**
  - Secure TLS 1.3 outbound connection. API keys are managed in user settings and never transmitted to third parties or embedded in repository source files. Only non-PII chemical molecular formulas are transmitted.

#### 17. Google Gemini 2.5 Pro (Google AI Pro API)
- **Component Name & Homepage URL:** Google Gemini API (https://ai.google.dev/)
- **Version / Commit:** Google GenAI SDK / Gemini 2.5 Pro API endpoint
- **License & Commercial Compatibility for Steam distribution:**
  - License: Google APIs Terms of Service / Apache-2.0 client SDK (`google-genai`).
  - Steam Compatibility: Compatible as an **OPT-IN CLOUD INTEGRATION**.
- **Exact Purpose in ChemLab:**
  - Advanced chemical reaction reasoning bridge, multi-step total synthesis pathway verification, procedural quest generation, and automatic markdown code-fence sanitization (`src/chemlab/media/google_media_bridge.py`).
- **Installation & Verification Status:**
  - Implemented in `src/chemlab/media/google_media_bridge.py` with exponential backoff and automatic offline fallback to internal reaction solvers. Verified by `tests/test_google_media_bridge.py`.
- **Runtime vs Development Dependency:**
  - Optional Runtime Cloud Integration.
- **Security, Privacy & Sandboxing Assessment:**
  - All communication is over authenticated HTTPS. Structured outputs are parsed into rigid Pydantic models. Automatic fallback ensures zero gameplay disruption if network connectivity drops or API rate limits are encountered.

---

### 3.5 Model Context Protocol (MCP) Servers & Claude Code Plugins

#### 18. Blender MCP (Development Time)
- **Component Name & Homepage URL:** Blender MCP Server (https://github.com/ahujasid/blender-mcp)
- **Version / Commit:** v1.0.1 (`blender-mcp-1.0.1.tgz`, `package/`)
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT License.
  - Steam Compatibility: 100% compatible because it is strictly a development-time tool. It is never included in the end-user distribution package.
- **Exact Purpose in ChemLab:**
  - Development-time agentic protocol enabling Claude Code and specialized studio agents (`graphics-lead-blender`, `game-director`) to inspect, build, and modify active Blender 3D scenes, tweak shaders, adjust lighting, and automate asset compilation via standard MCP protocol commands.
- **Installation & Verification Status:**
  - Integrated in repository root (`blender_mcp_server.mjs`, `package/addon/simple_mcp_addon.py`). Verified through active MCP tooling sessions.
- **Runtime vs Development Dependency:**
  - Development Dependency ONLY.
- **Security, Privacy & Sandboxing Assessment:**
  - Operates via local stdio or loopback socket on the developer's workstation. Not exposed to external networks or end users.

#### 19. Playwright MCP (E2E Testing)
- **Component Name & Homepage URL:** Playwright MCP (`@modelcontextprotocol/server-playwright` / https://playwright.dev/)
- **Version / Commit:** Playwright 1.48+ / MCP Server v0.1+
- **License & Commercial Compatibility for Steam distribution:**
  - License: Apache License 2.0.
  - Steam Compatibility: 100% compatible. Development and CI testing infrastructure only.
- **Exact Purpose in ChemLab:**
  - Automated end-to-end testing of the ChemLab web dashboard, HTML/JS visualizer (`gallery.html`), companion server (`src/chemlab/companion/remote_server.py`), and real-time reaction telemetry interfaces.
- **Installation & Verification Status:**
  - Configured in developer environment. Used for automated headless browser regression testing.
- **Runtime vs Development Dependency:**
  - Development & CI Testing Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Executes in sandboxed browser worker processes targeting local test servers (`http://127.0.0.1:8089`). No external internet access required.

#### 20. Windows MCP (System Automation)
- **Component Name & Homepage URL:** Windows MCP Server (Internal Tooling)
- **Version / Commit:** Windows MCP v1.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: MIT / Proprietary Tooling.
  - Steam Compatibility: 100% compatible. Development-time utility only.
- **Exact Purpose in ChemLab:**
  - Automated developer workstation orchestration: launching the native PySide6 desktop GUI (`src/chemlab/desktop/main_window.py`), verifying window focus and process lifecycle, checking Intel Iris Xe GPU utilization, and capturing verification screenshots.
- **Installation & Verification Status:**
  - Active in developer workstation MCP environment.
- **Runtime vs Development Dependency:**
  - Development Dependency ONLY.
- **Security, Privacy & Sandboxing Assessment:**
  - Restricted to developer workstation administrative and automation contexts. Never distributed to players.

#### 21. Context7 (Documentation Lookup)
- **Component Name & Homepage URL:** Context7 (https://context7.com/)
- **Version / Commit:** Context7 MCP Plugin v1.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: SaaS API / Developer Terms.
  - Steam Compatibility: 100% compatible. External developer documentation lookup utility.
- **Exact Purpose in ChemLab:**
  - Dynamic API documentation retrieval for Godot 4.x, Blender 5.2 Python API, RDKit, Cantera, PySide6, and MediaPipe during code generation and agentic maintenance sprints.
- **Installation & Verification Status:**
  - Configured in Claude Code agent environment.
- **Runtime vs Development Dependency:**
  - Development Dependency ONLY.
- **Security, Privacy & Sandboxing Assessment:**
  - Outbound queries contain only open-source library names and query keywords. Transmits no proprietary source code or confidential project files.

---

### 3.6 Desktop UI & Foundation Runtime Libraries

#### 22. PySide6 (Qt for Python)
- **Component Name & Homepage URL:** Qt for Python / PySide6 (https://www.qt.io/qt-for-python)
- **Version / Commit:** PySide6 6.7+
- **License & Commercial Compatibility for Steam distribution:**
  - License: GNU Lesser General Public License v3.0 (LGPL-3.0).
  - Steam Compatibility: **LGPL COMPLIANT ARCHITECTURE**. LGPL-3.0 permits commercial distribution on Steam under closed-source proprietary terms provided that:
    1. PySide6 is dynamically linked (distributed as shared libraries / `.pyd` / `.dll` C-extensions). In Python, PySide6 modules are dynamically loaded at runtime, fulfilling this condition.
    2. Users can replace the LGPL library with a modified version (supported through standard Python site-packages layout).
    3. Copyright notices, LGPL-3.0 license text, and written offer / instructions for obtaining Qt source code are included in the game's distribution folder.
- **Exact Purpose in ChemLab:**
  - Native desktop workbench window (`src/chemlab/desktop/main_window.py`), providing the cleanroom dark scientific dashboard, real-time telemetry panels, apparatus controls, and live reaction charts.
- **Installation & Verification Status:**
  - Installed and verified in desktop application test suite.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Standard GUI framework operating entirely in user space. No unsolicited network connections.

#### 23. WebSockets
- **Component Name & Homepage URL:** websockets (https://websockets.readthedocs.io/)
- **Version / Commit:** websockets >= 12.0
- **License & Commercial Compatibility for Steam distribution:**
  - License: BSD-3-Clause License.
  - Steam Compatibility: 100% compatible.
- **Exact Purpose in ChemLab:**
  - High-frequency real-time event streaming between simulation core, desktop HUD, and the companion remote server (`src/chemlab/companion/remote_server.py`).
- **Installation & Verification Status:**
  - Declared in `pyproject.toml`. Verified in `tests/test_transport.py` and `tests/test_companion_remote.py`.
- **Runtime vs Development Dependency:**
  - Runtime Dependency.
- **Security, Privacy & Sandboxing Assessment:**
  - Server binds strictly to loopback (`127.0.0.1`). Companion mobile mode requires explicit user PIN pairing to prevent unauthorized local network eavesdropping.

---

## 4. Security, Privacy & Sandboxing Architecture

### 4.1 Biometric & Webcam Privacy Assurance
- **Local In-Memory Buffer Processing**: MediaPipe and OpenCV access the webcam stream directly in volatile memory.
- **Zero Video Frame Persistence**: No camera frames, video clips, or biometric face/hand recordings are written to disk.
- **Zero Video Network Transmission**: The webcam stream is never transmitted over local sockets or cloud APIs. Only high-level discrete symbolic events (e.g., `EVENT_PINCH`, `EVENT_POUR`, `EVENT_SHAKE`) and normalized coordinates are passed to the simulation engine.
- **Explicit Consent Toggle**: Camera access is disabled by default until the player explicitly enables Webcam Hand Tracking in the laboratory settings menu. A visual indicator on the HUD confirms when camera capture is active.

### 4.2 Copyleft Infection Firewall (GPL Isolation)
To guarantee 100% legal compliance for proprietary commercial distribution on Steam:
1. **Blender 5.2 (GPL-3.0)**: Used exclusively for asset authoring during development. Only standard asset formats (.gltf, .glb, .obj, .wav, .png) are shipped to end users.
2. **Open Babel (GPL-2.0)**: Fully decoupled. ChemLab's runtime uses RDKit (BSD-3-Clause) for molecular processing. If Open Babel is used for legacy format conversion, it runs as an independent CLI subprocess with strict JSON pipe boundaries.
3. **PySide6 (LGPL-3.0)**: Kept strictly as dynamically loaded shared libraries, accompanied by LGPL notices and replacement instructions.

### 4.3 Network & Air-Gapped Simulation Integrity
- **100% Offline Gameplay**: All core thermodynamic simulations (Cantera), reaction kinetics (reaction_solver), molecular geometries (RDKit), and story quests operate completely offline without internet connectivity.
- **Zero Cloud Requirement**: AI features gracefully degrade to deterministic local catalogs or local quantized SLMs (llama.cpp) when no internet connection or API keys are present.
- **Credential Protection**: User-supplied API keys for optional cloud providers (Gemini, NVIDIA NIM) are stored using OS-native encrypted credential storage (Windows DPAPI / Linux Secret Service) and are never exposed in log files or crash dumps.

---

## 5. Audit Conclusion & Sign-Off

The ChemLab codebase and dependency ecosystem have been audited by the Security & Dependency Auditor. All external dependencies, libraries, asset kits, and MCP servers conform to commercial distribution standards on Steam. Copyleft isolation firewalls are verified, and biometric privacy protections meet global regulatory compliance standards.
