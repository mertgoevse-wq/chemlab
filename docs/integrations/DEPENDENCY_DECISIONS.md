# ChemLab Dependency Decisions

**Project:** ChemLab — Interactive Virtual Chemistry Laboratory (Steam, Windows 11)  
**Data freshness:** researched 2026-11-03 via GitHub  
**License audit baseline:** INTEGRATIONS_REGISTRY.md, TOP_50_REPOSITORY_SCORECARD.md  

---

## Executive summary

This document records the final per-category dependency selections for ChemLab, together with the version/commit pin, rationale, alternatives considered and rejected, the integration plan, and the risk & mitigation for each. It closes the loop opened by TOP_50_REPOSITORY_SCORECARD.md: every adopted/adapted candidate is assigned a concrete integration path into the ChemLab stack (Godot 4 runtime + Python 3.12 core), and every rejection is justified. A consolidated master decision table and a list of new dependencies proposed beyond INTEGRATIONS_REGISTRY.md follow.

All license, version, and activity values are taken from the research results fetched on 2026-11-03; any value marked "unverified" was not visible on the source page at research time.

---

## Per-category decisions

### Category A — Godot game runtime & 3D rendering

**Selected dependency:** Platinguin/Godot-Water-Shader-Prototype  
**Action:** adapt  
**Version / commit:** main branch as of 2026-10-20 (unverified commit SHA)  
**License:** MIT  
**URL:** https://github.com/Platinguin/Godot-Water-Shader-Prototype  

**Rationale:** Strongest liquid-shader candidate in Category A: MIT licensed (safe for commercial Steam distribution), actively maintained (updated 2026-10-20), highest community validation in the category (370★ / 51 forks, only 4 open issues, 0 open PRs), and a GLSL liquid shader that maps directly onto ChemLab's need to render water/chemicals in beakers and flasks under Godot 4's Compatibility/GLES3 renderer on Intel Iris Xe.

**Alternatives considered and rejected:**
- emilje/godot-water-shader (MIT, GDShader, updated 2026-11-03) — runner-up; kept as secondary liquid-shader source but less documented (no README detail visible; GLES3 compatibility unverified).
- LesusX/Water-Shader, CaptainProton42/GodotWaterfallShader, Adisoreq/godot-waterbox — MIT licensed but narrower scope (ocean caustics, waterfall, physics simulation); kept as reference/watch.
- CBerry22/Godot-Water-Ripple-Simulation-Shader, FastButterFly/SampleGodotGlassShader — no license declared → avoided for commercial Steam distribution.
- soldiersorrowful/Godot4-Water-Shader-Port — WIP, stale (2024), superseded by the original → watch.
- KingSahil/the-science-lab — on-theme but no license, tiny community → watch.
- MacdonaldRobinson/godot4-3d-characters — MIT, useful desktop 3D camera/player-controller skeleton for lab navigation; adopt as navigation skeleton.

**Integration plan:** Vendoring rather than wholesale adoption. Port the GLSL liquid shader into a Godot 4 ShaderMaterial applied to contained liquid volumes in beakers/flasks, driven by GDScript for pouring behavior and liquid level. Target the Compatibility/GLES3 rendering path for Intel Iris Xe. The godot4-3d-characters template supplies the first-person lab navigation camera/controller skeleton.

**Risk & mitigation:**
- Risk: Prototype scope (not a full lab sim); contained liquid volumes and pouring behavior must be built on top.  
  Mitigation: Treat as shader reference only; implement ChemLab-specific liquid volume/pouring logic in GDScript.
- Risk: GLES3 compatibility on Iris Xe unverified for candidate shaders.  
  Mitigation: Prototype on target hardware early; fall back to emilje/godot-water-shader if GLSL path fails.

---

### Category B — Computer vision & hand tracking

**Selected dependency:** google-ai-edge/mediapipe  
**Action:** adapt  
**Version / commit:** main branch as of 2026-11-03 (5,882 commits; exact date unverified)  
**License:** Apache-2.0  
**URL:** https://github.com/google-ai-edge/mediapipe  

**Rationale:** Top pick (score 10). Canonical, actively maintained source for MediaPipe Hands/Holistic Python bindings and the 21-landmark hand skeleton. Offline-capable, runs well on integrated graphics such as Intel Iris Xe, Apache-2.0 licensed (commercial-Steam friendly). ChemLab will build its hand-tracking layer around this, vendoring/adapting rather than using as-is, since integration must go into a Godot 4 + Python 3.12 stack.

**Alternatives considered and rejected:**
- opencv/opencv (Apache-2.0) — essential webcam-capture foundation (VideoCapture) to pair with MediaPipe; adopted as supporting dependency.
- Kazuhito00/hand-gesture-recognition-using-mediapipe (Apache-2.0) — best reference for landmark-to-gesture stage, but last update Apr 2023 (>12 months) → adapt as reference only.
- kinivi/tello-gesture-control, carlous-roy/GestureControl-Engine, taha-halakoo/virtual-mouse, johandiMIS/gesture-control — MIT/Apache-2.0 references for gesture state machines, One-Euro filtering, debounce/confirmation → adapt patterns only.
- Neilkhare18/Hand_Gesture_Mouse_Control, PINTO0309/hand-gesture-recognition-using-onnx — low community signal or notebook-centric → adapt/watch.
- gridinwork/Office-Vision-Tracker — license not specified → watch only until clarified.

**Integration plan:** Python 3.12 core captures webcam via OpenCV, runs MediaPipe Hands for 21-landmark estimation, and emits discrete symbolic events (EVENT_PINCH, EVENT_POUR, EVENT_SHAKE) plus normalized coordinates to the Godot simulation core over the Category F IPC transport. Webcam frames stay in volatile RAM only (zero persistence, zero network transmission) per INTEGRATIONS_REGISTRY.md §4.1. Camera access is opt-in and inactive by default.

**Risk & mitigation:**
- Risk: Large C++/Python framework, not drop-in; exact last-commit date not confirmed.  
  Mitigation: Vendor the Python bindings surface; pin a known-good release; vendor One-Euro filter + hysteresis patterns from Kazuhito00/carlous-roy/taha-halakoo for jitter-free gesture confirmation.
- Risk: MediaPipe API drift (Kazuhito00 targets an older API).  
  Mitigation: Pin to a tested MediaPipe version; wrap behind an internal adapter so upstream changes don't break the ChemLab gesture layer.

**Supporting selection:** opencv/opencv (Apache-2.0, score 9) — adopted as the webcam-capture foundation for the MediaPipe input pipeline.

---

### Category C — Scientific computing / chemistry

**Selected dependency:** Cantera/cantera  
**Action:** adapt  
**Version / commit:** 3.0.0+ / Python bindings (13,160 commits on main; date unverified)  
**License:** BSD-3-Clause (License.txt; SPDX not confirmed from fetched page)  
**URL:** https://github.com/Cantera/cantera  

**Rationale:** Top pick (score 9). Directly covers Cantera thermodynamics + chemical kinetics + transport properties — the core of a chemistry lab simulator. Mature, active, permissive BSD license compatible with commercial Steam distribution. Python bindings available for the Python 3.12 core. Lightweight enough as a compute library to run on Intel Iris Xe (80 EU) without driving the GPU.

**Alternatives considered and rejected:**
- rdkit/rdkit (BSD-3-Clause, score 9) — close second; adopted in parallel for cheminformatics and 3D conformer generation (SMILES/InChI parsing, distance-geometry 3D coordinates, UFF/MMFF94 minimization).
- bjodah/chempy (BSD-2-Clause, score 7) — adopt candidate for stoichiometry; pure Python, easy to vendor into the Python 3.12 core.
- CoolProp/CoolProp (MIT, score 8) — complements Cantera for fluid thermophysical property lookups; overlapping with Cantera → add only if fluid-specific properties are needed.
- Pyomo/pyomo (BSD, score 6), kyleniemeyer/computational-thermo (BSD-3-Clause/CC-BY-4.0, score 4), ipqa-research/ugropy (license not confirmed, score 5) — watch only.
- EmilioVenegas/mantis-delta (license not confirmed, score 3) — avoid.

**Integration plan:** Cantera wrapped behind `src/chemlab/simulation/cantera_engine.py` with graceful fallbacks for environments without compiled C++ binary extensions (already unit-tested via `tests/test_cantera_engine.py`). RDKit behind `src/chemlab/simulation/rdkit_engine.py` (mockable contracts for CI, verified via `tests/test_rdkit_engine.py`). ChemPy vendored into `src/chemlab/simulation/reaction_solver.py` and `side_reactions.py`. All core computation stays local and in-memory; no network calls during simulation steps.

**Risk & mitigation:**
- Risk: C++ core with Python bindings — build complexity on Windows; not pure Python.  
  Mitigation: Use prebuilt wheels where available; keep pure-Python fallbacks (ChemPy) for CI and developer machines without compiled extensions.
- Risk: License SPDX not confirmed for Cantera (License.txt present).  
  Mitigation: Confirm BSD-3-Clause text at vendor time; retain copyright notice and disclaimer in product documentation as required.

---

### Category D — AI / LLM orchestration & local inference

**Selected dependency:** ggml-org/llama.cpp  
**Action:** adopt  
**Version / commit:** main branch as of 2026-11-03 (12,092 commits on main; recent commits within 2026)  
**License:** MIT  
**URL:** https://github.com/ggml-org/llama.cpp  

**Rationale:** Top pick (score 9). Local LLM/VLM inference in C/C++, GGUF quantization (1.5–8 bit) fits 16 GB RAM, CPU backends (AVX2/AVX-512/AMX) work on Intel Iris Xe integrated graphics without a discrete GPU, MIT licensed for commercial Steam distribution, Python bindings available, fully offline-capable. Serves the "offline-first, optional cloud AI" requirement; foundation local inference engine for the ChemLab "Reagent Computer" assistant.

**Alternatives considered and rejected:**
- ollama/ollama (MIT, score 8) — adopt alternative/local-server option; good for bundling a ready-made local inference service with the Steam release, but heavier (separate Go binary/process).
- BerriAI/litellm (MIT, score 8) — adapt as the orchestration/fallback layer: route to local llama.cpp/ollama first, fall back to cloud providers when available.
- dottxt-ai/outlines (Apache-2.0, score 8) — adopt for structured JSON output + Pydantic validation; pair with llama.cpp/ollama for validated chemistry-lab LLM outputs.
- microsoft/onnxruntime-genai (MIT, score 7) — adapt; strong ONNX/OpenVINO path for Intel Iris Xe acceleration on Windows, worth evaluating alongside the llama.cpp CPU path.
- microsoft/onnxruntime (MIT, score 7) — adapt as backend execution-provider option if ONNX model deployment is preferred over GGUF.
- 567-labs/instructor (MIT, score 7) — adopt alternative to outlines for Pydantic validation; choose one based on provider support needed.
- vllm-project/vllm (Apache-2.0, score 5), microsoft/semantic-kernel (MIT, score 6), huggingface/transformers (Apache-2.0, score 6) — watch only.

**Integration plan:** Wrap llama.cpp via Python bindings or use `llama-server` HTTP mode bridged to Godot via TCP/HTTP (Category F transport). Layer litellm for multi-provider fallback and outlines/instructor for structured validated outputs. The Reagent Computer (`src/chemlab/ai/reagent_computer.py`) already has mockable fallback for CI; all user queries, gameplay state, and outputs stay on-device (100% air-gapped). Optional cloud AI (NVIDIA NIM, Google Gemini) remains opt-in and never required for core gameplay.

**Risk & mitigation:**
- Risk: C/C++ codebase requires careful integration with Python core; GPU offload on integrated Intel graphics limited to CPU/SYCL backends.  
  Mitigation: Use Python bindings / llama-server HTTP bridge; keep CPU GGUF path as the default for Iris Xe.
- Risk: Large surface area (743 open issues, 1.8k PRs) to vet.  
  Mitigation: Pin a specific release commit; vendor only the needed inference surface.

---

### Category E — Desktop GUI (PySide6 / Qt for Python)

**Selected dependency:** Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6  
**Action:** adapt  
**Version / commit:** main branch as of 2026-11-03T15:44:34Z  
**License:** MIT  
**URL:** https://github.com/Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6  

**Rationale:** Top pick (score 8). The only candidate that directly addresses the category's core focus — dark-theme PySide6 dashboard styling — with a commercial/Steam-compatible MIT license, actively maintained (updated 2026-11-03), and meaningful community traction (3,091★ / 610 forks). ChemLab vendors/adapts its dark theming for the cleanroom dashboard, then layers on QPainter plot widgets and QThread workers from pattern references.

**Alternatives considered and rejected:**
- oop7/YTSage (MIT, score 8) — strongest complete PySide6 app reference for app shell/structure, settings, and offline-first behavior; adopt as app skeleton reference (unrelated domain, so structure only).
- UN-GCPDS/qt-material (BSD-2-Clause, score 7) — solid secondary theming building block; adapt if a dark variant/custom palette is needed.
- zhuzichu520/PySide6-FluentUI-QML (MIT, score 6), pythonguis/pythonguis-examples (MIT, score 6), fbetancourt-dev/pyside-telemetry-dashboard (MIT, score 5), unupunct/nimbus (MIT, score 5) — watch; design/layout/QPainter pattern references only.
- mherrmann/fbs (GPL-3.0, score 4), XiaoYouChR/Ghost-Downloader-3 (GPL-3.0, score 3) — avoid: GPL-3.0 incompatible with commercial Steam runtime distribution.

**Integration plan:** The existing PySide6 desktop workbench window (`src/chemlab/desktop/main_window.py`, PySide6 6.7+, LGPL-3.0 dynamic linking per INTEGRATIONS_REGISTRY.md) receives a dark cleanroom theme adapted from the PyDracula stylesheet, with QPainter plot widgets for live reaction charts and QThread workers for background telemetry. App shell/structure modeled on YTSage. LGPL-3.0 compliance maintained: PySide6 distributed as dynamically loaded shared libraries, with LGPL notices, license text, and source-offer instructions in the distribution folder.

**Risk & mitigation:**
- Risk: GitHub description field is null (theme specifics must be inspected); stylesheet/component library rather than full app framework.  
  Mitigation: Inspect the repo at vendor time; significant custom dashboard code is expected regardless.
- Risk: PySide6 LGPL-3.0 copyleft (dynamic linking permitted but compliance obligations apply).  
  Mitigation: Keep PySide6 as dynamically loaded `.pyd`/`.dll`; ship LGPL-3.0 license text, copyright notices, and written offer for Qt source; isolate from proprietary game code via the existing desktop boundary.

---

### Category F — Networking / IPC (websockets, JSON-RPC, TCP)

**Selected dependency:** python-websockets/websockets  
**Action:** adopt  
**Version / commit:** >= 12.0 (2026-11-03)  
**License:** BSD-3-Clause  
**URL:** https://github.com/python-websockets/websockets  

**Rationale:** Top pick (score 9). Canonical, actively maintained Python WebSocket library (BSD-3-Clause, 5,744★, updated 2026-11-03). Directly covers ChemLab's core IPC need between the Python core and Blender/mobile companion, loopback-binding friendly, lightweight for Iris Xe, MIT/BSD-compatible for commercial Steam distribution. Paired with pavlov99/json-rpc (MIT) for JSON-RPC 2.0 framing over that transport.

**Alternatives considered and rejected:**
- pavlov99/json-rpc (MIT, score 8) — adopt as the JSON-RPC 2.0 framing layer layered over websockets; transport-agnostic, actively maintained (2026-11-02).
- websocket-client/websocket-client (Apache-2.0, score 7) — adapt as fallback sync client for mobile-companion/dashboard scenarios where asyncio isn't desired.
- tiangolo/fastapi (MIT, score 6) — adopt for the browser dashboard HTTP/WebSocket boundary (already referenced in GITHUB_INTEGRATION_SPEC.md as the recommended transport replacement of http.server); heavyweight for core↔Blender IPC.
- python-lsp/python-lsp-jsonrpc (MIT, score 5), palantir/python-jsonrpc-server (MIT, score 5) — watch as JSON-RPC backups.
- agentine/resurge (MIT, score 3, archived), baremetal/python-backoff (license "Other", score 2) — watch/avoid for reconnection/backoff; vendor a small custom backoff if needed instead.

**Integration plan:** websockets as the asyncio-native transport between the Python core, the Blender bridge (`blender_live_bridge.py`), and the mobile companion telemetry; pavlov99/json-rpc layered on top for structured command/response. Server binds strictly to loopback (`127.0.0.1`); companion mobile mode requires explicit user PIN pairing. Add a reconnect/backoff wrapper (vendor a small implementation rather than depending on the archived resurge or the unclear-license python-backoff). FastAPI adopted for the dashboard HTTP/WebSocket endpoint per the existing spec.

**Risk & mitigation:**
- Risk: Pure WebSocket — no built-in JSON-RPC framing or reconnection/backoff; async-only API may need adaptation for sync call sites.  
  Mitigation: Layer pavlov99/json-rpc for framing; write a small reconnect/backoff wrapper; keep existing ThreadedIPCServer for lightweight IPC where it already covers the need.

---

### Category G — Blender DCC pipeline & asset export

**Selected dependency:** KhronosGroup/glTF-Blender-IO  
**Action:** adopt  
**Version / commit:** main branch as of 2026-11-03  
**License:** Apache-2.0  
**URL:** https://github.com/KhronosGroup/glTF-Blender-IO  

**Rationale:** Top pick (score 10). The official Khronos glTF 2.0 importer/exporter for Blender is the clear top pick: Apache-2.0 licensed (commercial-Steam safe), by far the most active (updated 2026-11-03), most starred (1,673★) and most widely adopted (built into Blender itself). Directly covers ChemLab's core needs — GLTF/GLB export, Draco mesh compression, and PBR material export — making it the natural foundation for the DCC pipeline.

**Alternatives considered and rejected:**
- bikemurt/blender-godot-pipeline (MIT, score 9), indiedevcasts/blender-godot-pipeline (MIT, score 8), zheqd/blender-godot-pipeline (MIT, score 8) — adapt as references for the Blender→Godot pipeline and Godot-side glTF extras import (collision bodies, navmeshes, multimeshes, packed scenes).
- ux3d/blender_extern_draco (Apache-2.0, score 7) — watch; Dedicated Draco compression but redundant with Blender's built-in glTF exporter Draco support; low activity (Mar 2026), tiny community.
- nytimes/rd-blender-docker (Apache-2.0, score 7), bardia-ardakanian/blender-headless-render (MIT, score 6), KuzeyKayraEyioglu/blender-procedural-room-generator (MIT, score 6) — watch as references for headless automation and procedural geometry.

**Integration plan:** glTF-Blender-IO is built into Blender 5.2 (the existing dev-only DCC tool per INTEGRATIONS_REGISTRY.md) — no separate runtime dependency. ChemLab's asset pipeline exports laboratory glassware, benches, and instruments as GLTF/GLB with Draco mesh compression and PBR materials, then imports into Godot 4 using the blender-godot-pipeline patterns for collision/scene metadata. Blender remains strictly development-time only (asset creation), excluded from Steam runtime builds per the GPL-3.0 isolation boundary.

**Risk & mitigation:**
- Risk: High open-issue count (248) — typical for a popular project, but triage needed for export regressions.  
  Mitigation: Pin a tested Blender/glTF-Blender-IO combination; validate exports in CI via headless Blender test (`tests/headless_blender_test.py`).

---

### Category H — Audio / SFX synthesis

**Selected dependency:** BDraves/pyalsoft  
**Action:** adapt  
**Version / commit:** main branch as of 2026-08-24T17:52:45Z  
**License:** MIT  
**URL:** https://github.com/BDraves/pyalsoft  

**Rationale:** Top pick (score 8). Strongest overall match for ChemLab's constraints: MIT licensed (safe for commercial Steam distribution), Python-native (aligns with the Python 3.12+ core), and directly addresses the spatial 3D audio / positional audio trigger focus area via OpenAL Soft bindings, with native runtimes bundled in wheels — easing offline-first deployment on Windows/Intel Iris Xe.

**Alternatives considered and rejected:**
- agateau/sfxr-qt (MIT, score 8), bzar/sfxr-rs (MIT, score 7) — best procedural-SFX sources (canonical sfxr implementations) but C++/Rust; require adaptation (binding layer or CLI invocation from Python).
- TeamPyOgg/PyOgg (Unlicense, score 6) — adopt for WAV/OGG/Opus/FLAC encoding/decoding in the audio asset pipeline.
- belangeo/pyo (LGPL-3.0, score 7) — watch only; mature Python DSP but LGPL-3.0 is a commercial-runtime risk.
- humphd/sfxr.js (MIT, score 5), rednblackgames/gdx-miniaudio (Apache-2.0, score 4) — watch.
- grimfang4/sfxr (no license, score 5) — avoid; legally unusable for commercial Steam without clearing rights.

**Integration plan:** Use pyalsoft for spatial 3D audio / positional audio triggers from the Python 3.12 core. Pair with an adapted sfxr implementation (agateau/sfxr-qt or bzar/sfxr-rs) for procedural 44.1kHz SFX generation (button/beaker foley), baked offline. Use TeamPyOgg/PyOgg for WAV/OGG compression in the audio asset pipeline. All audio remains local; no network transmission of audio data.

**Risk & mitigation:**
- Risk: Very low star count (1 star) and single maintainer — limited community vetting, long-term maintenance risk, possible unresolved edge cases in spatial audio on Windows.  
  Mitigation: Vendor the pyalsoft surface so ChemLab is not broken by upstream changes; maintain an internal fallback (e.g., a minimal OpenAL or stereo panner) if pyalsoft proves unstable on target hardware.
- Risk: sfxr-qt/sfxr-rs are C++/Rust, not Python/Godot-native.  
  Mitigation: Wrap via PyO3/FFI or invoke as offline CLI binaries during asset baking, not at runtime.

---

### Category I — Build / release / packaging

**Selected dependency:** pyinstaller/pyinstaller  
**Action:** adopt  
**Version / commit:** main branch as of 2026-11-03T12:50:29Z  
**License:** GPL-2.0-or-later WITH Bootloader-exception (NOASSERTION SPDX)  
**URL:** https://github.com/pyinstaller/pyinstaller  

**Rationale:** Top pick (score 9). Industry-standard Python freezer (13,138★), actively maintained (updated today), supports Python 3.8–3.15 including 3.12, creates Windows standalone executables — exactly what ChemLab needs. The Bootloader exception means frozen application output is not itself GPL, so it is compatible with commercial Steam distribution.

**Secondary selection:** jrsoftware/issrc (Inno Setup)  
**Action:** adopt  
**Version / commit:** main branch as of 2026-11-03T14:54:59Z  
**License:** NOASSERTION (license.txt exists, no SPDX)  
**URL:** https://github.com/jrsoftware/issrc  
**Rationale:** Industry-standard Windows installer builder (5,740★), actively maintained, mature and proven for commercial software distribution; suitable for bundling ChemLab's installer for Steam.

**Alternatives considered and rejected:**
- marcelotduarte/cx_Freeze (license unclear, score 7), py2exe/py2exe (license unclear, score 6), brentvollebregt/auto-py-to-exe (MIT, score 5, GUI frontend only), nsis-dev/nsis (license "Other", score 6) — watch as backups.
- Nuitka/Nuitka (AGPL-3.0, score 4) — avoid: AGPL-3.0 incompatible with commercial Steam runtime distribution.
- actions/upload-release-asset (MIT, score 5, archived) — watch as a reference pattern only; use modern GitHub Actions release upload alternatives.
- Noxime/steamworks-rs (Apache-2.0, score 3) — avoid: Rust bindings, wrong language for the Python 3.12 + Godot 4 stack.
- PeculiarVentures/goodkey-win-signtool-action (Apache-2.0, score 4) — watch as a code-signing option for Steam distribution (low adoption; vendor lock-in via GoodKey).

**Integration plan:** Freeze ChemLab's Python 3.12 code into a Windows .exe with PyInstaller (the bootloader exception keeps the output non-GPL). Build the Steam installer with Inno Setup. Verify packaging in CI; keep the hybrid Godot+Python build working end-to-end. Consider auto-py-to-exe for local dev builds only, not CI.

**Risk & mitigation:**
- Risk: PyInstaller core tool is GPL-licensed (bootloader exception mitigates for output binaries).  
  Mitigation: Confirm frozen .exe output is not itself GPL; retain PyInstaller as a build-time tool only (not distributed as runtime source).
- Risk: Inno Setup license not SPDX-identified.  
  Mitigation: Verify license.txt terms at vendor time before adopting for the Steam installer.

---

## Consolidated master decision table

| # | Category | Component | Version / commit | License | Action | Role | Steam OK? | Primary file / integration point |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | A | Platinguin/Godot-Water-Shader-Prototype | main @ 2026-10-20 | MIT | adapt | Liquid shader for beakers/flasks | Yes | Godot 4 ShaderMaterial + GDScript |
| 2 | A | MacdonaldRobinson/godot4-3d-characters | main @ 2026-10-23 | MIT | adapt | Lab navigation camera/controller skeleton | Yes | Godot 4 3D scene |
| 3 | B | google-ai-edge/mediapipe | main @ 2026-11-03 | Apache-2.0 | adapt | Hand tracking (21 landmarks) | Yes | `src/chemlab/cv/hand_tracker.py` |
| 4 | B | opencv/opencv | 5.x branch @ 2026-11-03 | Apache-2.0 | adopt | Webcam capture foundation | Yes | `src/chemlab/cv/` + synthetic.py |
| 5 | C | Cantera/cantera | 3.0.0+ | BSD-3-Clause | adapt | Thermodynamics/kinetics/transport | Yes | `src/chemlab/simulation/cantera_engine.py` |
| 6 | C | rdkit/rdkit | 2024.03+ | BSD-3-Clause | adapt | Cheminformatics + 3D conformers | Yes | `src/chemlab/simulation/rdkit_engine.py` |
| 7 | C | bjodah/chempy | 0.8.4+ | BSD-2-Clause | adopt | Stoichiometry / reactions / kinetics | Yes | `src/chemlab/simulation/reaction_solver.py` |
| 8 | D | ggml-org/llama.cpp | main @ 2026-11-03 | MIT | adopt | Local LLM inference (offline) | Yes | `src/chemlab/ai/reagent_computer.py` |
| 9 | D | BerriAI/litellm | main @ 2026-11-03 | MIT | adapt | Cloud-AI fallback orchestration | Yes | AI routing layer |
| 10 | D | dottxt-ai/outlines | main @ 2026-11-03 | Apache-2.0 | adopt | Structured JSON + Pydantic validation | Yes | LLM output validation |
| 11 | D | ollama/ollama | main @ 2026-11-03 | MIT | adopt | Alternative local LLM server | Yes | HTTP bridge (localhost:11434) |
| 12 | E | Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 | main @ 2026-11-03 | MIT | adapt | Dark cleanroom dashboard theme | Yes | `src/chemlab/desktop/main_window.py` |
| 13 | E | oop7/YTSage | main @ 2026-11-03 | MIT | adapt | PySide6 app shell/structure reference | Yes | Desktop GUI structure |
| 14 | E | UN-GCPDS/qt-material | main @ 2026-11-03 | BSD-2-Clause | adapt | Secondary theming building block | Yes | Dashboard surfaces |
| 15 | F | python-websockets/websockets | >= 12.0 @ 2026-11-03 | BSD-3-Clause | adopt | Core WebSocket IPC transport | Yes | Python core ↔ Blender/mobile |
| 16 | F | pavlov99/json-rpc | main @ 2026-11-02 | MIT | adapt | JSON-RPC 2.0 framing over websockets | Yes | IPC command/response layer |
| 17 | F | tiangolo/fastapi | main @ 2026-11-03 | MIT | adopt | Dashboard HTTP/WebSocket boundary | Yes | Browser dashboard endpoint |
| 18 | G | KhronosGroup/glTF-Blender-IO | main @ 2026-11-03 | Apache-2.0 | adopt | GLTF/GLB export, Draco, PBR | Yes | Blender 5.2 DCC pipeline (dev-only) |
| 19 | H | BDraves/pyalsoft | main @ 2026-08-24 | MIT | adapt | Spatial 3D / positional audio | Yes | Python 3.12 audio core |
| 20 | H | TeamPyOgg/PyOgg | main @ 2026-07-25 | Unlicense | adapt | WAV/OGG/Opus/FLAC encoding | Yes | Audio asset pipeline |
| 21 | I | pyinstaller/pyinstaller | main @ 2026-11-03 | GPL-2.0 + Bootloader exception | adopt | Python freezer → Windows .exe | Yes (output) | Build/CI pipeline |
| 22 | I | jrsoftware/issrc | main @ 2026-11-03 | NOASSERTION | adopt | Windows installer (Inno Setup) | Verify license.txt | Steam installer |

---

## New dependencies proposed beyond INTEGRATIONS_REGISTRY.md

The following candidates from the research results are **not** already listed in INTEGRATIONS_REGISTRY.md and are proposed for adoption/adaptation:

| Component | Category | License | Action | Reason for addition |
| :--- | :--- | :--- | :--- | :--- |
| Platinguin/Godot-Water-Shader-Prototype | A | MIT | adapt | Dedicated Godot 4 liquid shader for lab glassware (not previously registered). |
| MacdonaldRobinson/godot4-3d-characters | A | MIT | adapt | Desktop 3D camera/player-controller skeleton for first-person lab navigation. |
| google-ai-edge/mediapipe | B | Apache-2.0 | adapt | Already referenced by name in registry; now pinned as the canonical hand-tracking source with version. |
| pavlov99/json-rpc | F | MIT | adapt | JSON-RPC 2.0 framing layer for IPC (registry listed websockets but not a JSON-RPC framing lib). |
| tiangolo/fastapi | F | MIT | adopt | Dashboard HTTP/WebSocket boundary (referenced in GITHUB_INTEGRATION_SPEC.md, not in registry). |
| KhronosGroup/glTF-Blender-IO | G | Apache-2.0 | adopt | Official glTF exporter (built into Blender 5.2; registry lists Blender but not the exporter explicitly). |
| BDraves/pyalsoft | H | MIT | adapt | Python-native spatial 3D audio via OpenAL Soft (no audio runtime previously registered beyond CC0 assets). |
| TeamPyOgg/PyOgg | H | Unlicense | adapt | WAV/OGG/Opus/FLAC bindings for the audio asset pipeline. |
| ollama/ollama | D | MIT | adopt | Alternative local LLM server option. |
| BerriAI/litellm | D | MIT | adapt | Multi-provider cloud-AI fallback orchestration. |
| dottxt-ai/outlines | D | Apache-2.0 | adopt | Structured JSON + Pydantic validation for LLM outputs. |
| microsoft/onnxruntime-genai | D | MIT | adapt | ONNX/OpenVINO path for Intel Iris Xe acceleration. |
| 567-labs/instructor | D | MIT | adopt | Alternative to outlines for Pydantic validation. |
| Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 | E | MIT | adapt | Dark-theme PySide6 dashboard styling (registry lists PySide6 but no theming source). |
| UN-GCPDS/qt-material | E | BSD-2-Clause | adapt | Secondary theming building block. |
| oop7/YTSage | E | MIT | adapt | Complete PySide6 app shell/structure reference. |
| jrsoftware/issrc | I | NOASSERTION | adopt | Inno Setup Windows installer for Steam distribution. |

License-verification notes before vendor:
- jrsoftware/issrc: license not SPDX-identified — verify license.txt terms.
- Cantera/cantera: BSD-3-Clause per License.txt but SPDX not confirmed on the fetched page — confirm at vendor time.
- All MIT/Apache-2.0/BSD candidates: retain copyright notices and license text in product documentation as required.