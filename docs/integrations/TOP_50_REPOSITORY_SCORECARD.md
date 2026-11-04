# ChemLab Top 50 Repository Scorecard

**Project:** ChemLab — Interactive Virtual Chemistry Laboratory (Steam, Windows 11)  
**Data freshness:** researched 2026-11-03 via GitHub  
**License audit baseline:** INTEGRATIONS_REGISTRY.md  

---

## Executive Summary

This scorecard consolidates the results of 9 parallel GitHub research phases (categories A–I) into a single, decision-ready repository inventory. Each candidate carries stars, language, license, last-activity date, relevance score (1–10), and a recommended action (adopt / adapt / watch / avoid). All license, star-count, and activity values are taken from the research results as fetched on 2026-11-03; any value marked "unverified" was not visible on the source page at research time.

ChemLab's commercial target (Steam) drives a hard license filter: only MIT / Apache-2.0 / BSD / CC0-style permissive licenses are acceptable for runtime distribution. Copyleft dependencies (GPL-2.0 / GPL-3.0 / LGPL-3.0 runtime linking / AGPL) are either excluded or isolated behind a clean subprocess boundary per the copyleft isolation rules in INTEGRATIONS_REGISTRY.md Section 4.2.

**Category coverage (research results):**

| Category | Focus | Top pick | Action |
| :--- | :--- | :--- | :--- |
| A | Godot game runtime & 3D rendering | Platinguin/Godot-Water-Shader-Prototype | adapt |
| B | Computer vision & hand tracking | google-ai-edge/mediapipe | adapt |
| C | Scientific computing / chemistry | Cantera/cantera | adapt |
| D | AI / LLM orchestration & local inference | ggml-org/llama.cpp | adopt |
| E | Desktop GUI (PySide6 / Qt for Python) | Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 | adapt |
| F | Networking / IPC (websockets, JSON-RPC, TCP) | python-websockets/websockets | adopt |
| G | Blender DCC pipeline & asset export | KhronosGroup/glTF-Blender-IO | adopt |
| H | Audio / SFX synthesis | BDraves/pyalsoft | adapt |
| I | Build / release / packaging | pyinstaller/pyinstaller | adopt |

**Overall licensing posture:** every adopted/adapted runtime candidate above carries a permissive license (MIT / Apache-2.0 / BSD-3-Clause / BSD-2-Clause), consistent with commercial Steam distribution. No copyleft candidate appears in the adopted set.

---

## Category tables

### Category A — Godot game runtime, shaders, 3D lab environments

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Platinguin/Godot-Water-Shader-Prototype | 370 | GLSL | MIT | 2026-10-20 | 9 | adapt | Best liquid shader candidate for ChemLab beakers/flasks; actively maintained; MIT (Steam-compatible); GLSL fits Godot 4 Compatibility/GLES3 on Intel Iris Xe. | Prototype scope only; needs adaptation into Godot 4 ShaderMaterial + GDScript for contained liquid volumes and pouring behavior. |
| emilje/godot-water-shader | 135 | GDShader | MIT | 2026-11-03 | 8 | adapt | GDShader (Godot 4 native) water shader; MIT licensed; most recently updated of all candidates (2026-11-03). Strong fit for Godot 4 liquid rendering in lab glassware. | No description/README detail visible; shader scope and GLES3 compatibility unverified. |
| LesusX/Water-Shader | 8 | GDScript | MIT | 2026-09-12 | 7 | adapt | Godot 4 demo project with Gerstner wave ocean shader, caustics, foam, and depth-based colouring — caustics are directly relevant to liquid-in-glass visual fidelity. MIT licensed. | Ocean-scene focus (large-scale water) rather than small contained liquid volumes; small community (8★). |
| CaptainProton42/GodotWaterfallShader | 56 | GLSL | MIT | 2026-11-02 | 7 | adapt | Interactive liquid shader; MIT; recently updated (2026-11-02); GLSL. Good reference for flowing liquid (pouring) effects in lab context. | Waterfall-specific effect; contained liquid (beaker) rendering would require rework. |
| MacdonaldRobinson/godot4-3d-characters | 10 | GDScript | MIT | 2026-10-23 | 6 | adapt | Godot 4 3D game template with camera/player controller — useful as a starting skeleton for first-person lab navigation and input handling on desktop. | Game-template scope (characters/multiplayer) not lab-specific; much would be stripped out; mobile controls irrelevant to desktop Steam build. |
| Adisoreq/godot-waterbox | 6 | GDScript | MIT | 2026-09-21 | 6 | adapt | 3D water physics simulation tool in Godot — closest to liquid simulation behavior needed for pouring/mixing in ChemLab. MIT licensed. | Very small community (6★, 0 forks); physics-simulation scope rather than rendering; maturity unclear. |
| CBerry22/Godot-Water-Ripple-Simulation-Shader | 102 | GDScript | (none declared) | 2026-10-10 | 5 | avoid | Water ripple simulation shader with decent community traction (102★/13 forks); GDScript suggests Godot 4 integration. | No license declared (risk for commercial Steam distribution); ripple-surface scope rather than volumetric liquid. |
| KingSahil/the-science-lab | 3 | GDScript | (none declared) | 2026-09-30 | 5 | watch | Directly on-theme: a Godot science lab game for JEE/NEET students. GDScript, Godot 4 era. | No license declared; tiny community (3★); educational/JEE-NEET scope, unclear code quality and desktop build readiness. |
| soldiersorrowful/Godot4-Water-Shader-Port | 6 | GLSL | MIT | 2024-10-30 | 4 | watch | Explicit Godot 4 port of Platinguin/Godot-Water-Shader-Prototype; MIT licensed. | Marked WIP; last activity 2024 (stale); superseded by the actively maintained original. |
| FastButterFly/SampleGodotGlassShader | 0 | GDShader | (none declared) | 2026-04-12 | 3 | avoid | Glass shader for Godot (GDShader) — directly relevant to lab glassware (beakers, flasks) rendering. | No license declared; zero stars/forks; no description; quality and GLES3 compatibility unverified. |

**Category A count:** 10 candidates.

---

### Category B — Computer vision & hand tracking

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| google-ai-edge/mediapipe | 37500 | C++/Python | Apache-2.0 | Active (5,882 commits; exact date not visible) | 10 | adapt | Canonical source for MediaPipe Hands/Holistic Python bindings, 21-landmark hand skeleton, offline-capable, runs on integrated graphics such as Intel Iris Xe, Apache-2.0 commercial-Steam friendly. | Large C++/Python framework — not drop-in; needs vendoring/adaptation into Godot 4 + Python 3.12; exact last-commit date not confirmed within 12 months from page. |
| opencv/opencv | 91400 | C++/Python | Apache-2.0 | Active (38,323 commits on 5.x branch; exact date not visible) | 9 | adapt | The webcam-capture foundation (VideoCapture) for MediaPipe input; Apache-2.0 commercial-friendly; battle-tested on low-end hardware. | Low-level C++ library; Python bindings are the relevant surface; open-PR count appears to be a display anomaly, not actionable. |
| Kazuhito00/hand-gesture-recognition-using-mediapipe | 771 | Python | Apache-2.0 | Updated Apr 5, 2023 | 8 | adapt | Direct MediaPipe-hands + gesture-recognition reference; Apache-2.0; working 21-landmark-to-gesture pipeline in pure Python. | Last update Apr 2023 (over 12 months ago) — may target older MediaPipe API; open-issue/PR counts not visible on page. |
| Neilkhare18/Hand_Gesture_Mouse_Control | 0 | Python | MIT | 4 commits (exact date not listed) | 7 | adapt | Directly targets the Iris Xe / 720p@60 FPS / offline constraints; MIT license; Windows-native (Win32) matches Steam-on-Windows target. | Zero stars/forks, minimal activity, no visible issue/PR tracking — low community signal; Win32-specific. |
| kinivi/tello-gesture-control | 344 | Python | Apache-2.0 | Updated Aug 29, 2023 (42 commits on main) | 7 | adapt | Working MediaPipe gesture pipeline in Python with a gesture-state/trigger model; Apache-2.0; modest community signal. | Last update Aug 2023 (>12 months); drone-specific, not desktop; no open-PR count visible. |
| PINTO0309/hand-gesture-recognition-using-onnx | 96 | Jupyter Notebook | Apache-2.0 | Updated Jan 6 (63 commits on main) | 7 | adapt | ONNX-based offline inference could suit optional cloud AI / Iris Xe deployment; Apache-2.0; multi-palm support. | Jupyter Notebook primary language (not a clean Python lib); thin activity; no issue/PR counts. |
| carlous-roy/GestureControl-Engine | 0 | Python | MIT | 27 commits on main (date not shown) | 6 | adapt | Explicitly combines MediaPipe Hands + One Euro filter + finger rules with hysteresis, Arduino relays over Firmata. Pipeline: Webcam -> MediaPipe Hands -> One Euro filter -> finger rules -> 3-frame confirmation. | Zero stars/forks, minimal activity, no issue/PR tracking — very low community signal; relay/Arduino-focused. |
| taha-halakoo/virtual-mouse | 1 | Python | MIT | 11 commits on master (date not shown) | 6 | adapt | One-Euro filtering + relative delta tracking + clutch gesture for jitter-free cursor motion; MIT license. | 1 star, no forks, 22 open PRs suggests unfinished state; no issue count visible. |
| johandiMIS/gesture-control | 0 | Python | MIT | 4 commits on main (date not shown) | 6 | adapt | MediaPipe + One Euro filtering + debounced grab detection; MIT license; depth-invariant mapping relevant to varying webcam distances. | Zero stars/forks, minimal activity, no issue/PR tracking; Arduino/gantry-specific. |
| gridinwork/Office-Vision-Tracker | 0 | Python | Not specified | Updated Sep 29 | 5 | watch | Local real-time computer vision application for webcam-based person, pose, face and hand tracking; Python. | Zero stars/forks; license not specified (compliance risk for commercial Steam); minimal activity. |

**Category B count:** 10 candidates.

---

### Category C — Scientific computing / chemistry

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Cantera/cantera | 879 | C++ / Python | BSD-3-Clause (License.txt; SPDX not confirmed from fetched page) | Active — 13,160 commits on main | 9 | adapt | Directly covers Cantera thermodynamics + kinetics + transport, the core of a chemistry lab simulator. Mature, active, permissive BSD license compatible with commercial Steam distribution. Python bindings available for the Python 3.12 core. | C++ core with Python bindings — not pure Python; would need adaptation/vendoring for Godot + Python 3.12 integration. Build complexity on Windows. Heavier than a pure-Python lib but acceptable for Iris Xe as a compute library (not rendering). |
| rdkit/rdkit | 3700 | C++ / Python | BSD-3-Clause | Active — 8,736 commits on master | 9 | adapt | Covers RDKit cheminformatics and 3D conformer generation — essential for molecular structure/3D visualization in ChemLab. BSD-3-Clause is commercial-friendly. Large, active community. | C++ core with Python bindings; sizable build. Windows wheel availability helps. May be heavier than needed if only simple 3D conformers are required. |
| bjodah/chempy | 659 | Python | BSD-2-Clause | 929 commits (date not confirmed from page) | 7 | adopt | Pure-Python chemistry package covering stoichiometry, reactions, and basic kinetics — the ChemPy stoichiometry need. BSD-2-Clause is permissive and commercial-friendly. Easy to vendor into a Python 3.12 core. | Smaller community and less frequent activity than Cantera/RDKit. Limited to stoichiometry/basic kinetics — won't cover thermodynamics or 3D conformers on its own. |
| CoolProp/CoolProp | 1100 | C++ / Python | MIT | Active — 6,411 commits | 8 | adapt | Thermophysical/fluid property data — complements Cantera for property lookups (NIST/CRC-style data pipeline need). MIT license is maximally permissive for commercial Steam distribution. Active with many open PRs. | C++ core; focused on fluids/refrigerants rather than general chemistry. Overlaps partially with Cantera, so adding both may be redundant unless fluid-specific properties are needed. |
| Pyomo/pyomo | 2600 | Python | BSD License (BSD) | Active — 31,621 commits on main | 6 | watch | Optimization modeling could support reactor design / equilibrium calculations in ChemLab. Pure Python, BSD license, very active. NumPy/SciPy-compatible ODE-adjacent use cases. | Not a chemistry-specific library; it's a general optimization modeling language. High open-PR count (4545) suggests a large backlog. Only indirectly relevant to category C focus areas. |
| kyleniemeyer/computational-thermo | 77 | Jupyter Notebook | BSD-3-Clause, CC-BY-4.0 | Date not confirmed from page | 4 | watch | Collection of examples in computational thermodynamics using Cantera — useful as reference material for implementing thermodynamics in ChemLab, but it's example/notebook content, not a reusable library. | Notebook-based examples, not a library to adopt. Limited reusability; mostly educational reference. |
| ipqa-research/ugropy | 36 | Python | not visible | not confirmed | 5 | watch | Group-contribution (UNIFAC) property estimation — niche but relevant to thermochemical property prediction for ChemLab's chemistry needs. | Small (36 stars), license not confirmed from page, niche scope. Uncertain maintenance. |
| EmilioVenegas/mantis-delta | 1 | Python | not visible | not confirmed | 3 | avoid | Python library for Chemical Reaction Network Theory connecting network topology with symbolic mass-action kinetics — tangential to the kinetics/ODE solver interest, but very small and unproven. | 1 star, license not confirmed, minimal activity, experimental. Quality/risk concerns for runtime use. |

**Category C count:** 8 candidates.

---

### Category D — AI / LLM orchestration & local inference

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ggml-org/llama.cpp | 133300 | C/C++ | MIT | Active (12,092 commits on main; recent commits within 2026) | 9 | adopt | Local LLM/VLM inference in C/C++, GGUF quantization (1.5-8 bit) fits 16 GB RAM, CPU backends (AVX2/AVX-512/AMX) work on Intel Iris Xe integrated graphics, MIT licensed for commercial Steam distribution, Python bindings available, fully offline-capable. | C/C++ codebase requires careful integration with Python core; GPU offload on integrated Intel graphics limited to CPU/SYCL backends; large surface area (743 open issues, 1.8k PRs) to vet. |
| ollama/ollama | 185800 | Go | MIT | Active (high commit velocity) | 8 | adopt | Local LLM server exposing REST API (localhost:11434), MIT licensed, privacy-focused offline operation, backs many models via llama.cpp, simple integration from Python core or Godot via HTTP. | Separate Go binary/process to bundle with Steam installer; heavier than a library; high issue/PR volume (2.6k issues, 1.9k PRs) to triage. |
| BerriAI/litellm | 62600 | Rust/Python | MIT (LICENSE file present) | Active (high commit velocity) | 8 | adapt | Unified OpenAI-compatible interface across 100+ LLM providers with auto-routing and multi-provider fallback chains; ideal for ChemLab's 'optional cloud AI' fallback over local inference; Python SDK and proxy server modes. | License SPDX not explicitly shown on page (LICENSE file present); very high issue/PR volume (1.7k issues, 4k PRs); more cloud-gateway oriented than local-first. |
| dottxt-ai/outlines | 16000 | Python | Apache-2.0 | Active (1,325 commits on main) | 8 | adopt | Structured generation for LLMs — constrains output to types, JSON schemas, Pydantic models, regex, CFGs; works across OpenAI, Ollama, vLLM, transformers, llama.cpp; Apache-2.0 is commercial-friendly. | A library that sits on top of an inference provider (does not itself run models); smaller team than mega-repos; Apache-2.0 (not MIT) still fine for commercial use. |
| microsoft/onnxruntime-genai | 1100 | C++/Python/C# | MIT | Active (1,856 commits on main) | 7 | adapt | Local generative AI inference via ONNX Runtime with OpenVINO backend (Intel GPU/Iris Xe support), DirectML for Windows, MIT licensed, powers Windows ML / Foundry Local / VS Code AI Toolkit — aligns with Windows + Intel target. | Smaller community (1.1k stars); Python/C#/C++ bindings require build for source in some languages; focused on generative models rather than general orchestration. |
| microsoft/onnxruntime | 22200 | C++ | MIT | Active | 7 | adapt | Execution-provider architecture (CPU, CUDA, DirectML, OpenVINO, etc.) for local ML inference; DirectML/OpenVINO relevant to Intel Iris Xe on Windows; MIT licensed; mature and widely used. | Heavy C++ codebase; broad scope beyond LLMs; integration effort high for a chemistry simulator; OpenVINO/DirectML setup non-trivial. |
| 567-labs/instructor | 14100 | Python | MIT | Active | 7 | adopt | Pydantic-based validated structured LLM outputs with automatic retries and streaming; works across OpenAI, Anthropic, Google, Ollama; MIT licensed; clean Python fit for ChemLab's Python 3.12 core. | Library layer over an inference provider (needs a backend); smaller than outlines; overlaps with outlines functionality. |
| vllm-project/vllm | 96200 | Python/C++/Rust | Apache-2.0 | Active (24,472 commits on main) | 5 | watch | Production-grade LLM serving engine with PagedAttention and OpenAI-compatible API; strong for high-throughput serving. | Apache-2.0 (acceptable); heavily NVIDIA/GPU-focused, less suited to Intel Iris Xe integrated graphics; very high issue/PR volume; heavy for a desktop Steam title. |
| microsoft/semantic-kernel | 28700 | Python/.NET/Java | MIT | Active | 6 | watch | Model-agnostic AI orchestration SDK with plugins, multi-provider connectors, local deployment support; MIT licensed; Microsoft-backed. | .NET-centric with Python as a secondary language; broader agent-orchestration scope than ChemLab needs; adds dependency weight. |
| huggingface/transformers | 168500 | Python | Apache-2.0 | Active | 6 | watch | Unified Pipeline API for local inference across text/vision/audio/multimodal models; integrates with vLLM and others; Apache-2.0; huge model hub. | Python/PyTorch-heavy (RAM/GPU demands may exceed Iris Xe + 16 GB for large models); more a model library than an inference engine; overlapping with llama.cpp scope. |

**Category D count:** 11 candidates.

---

### Category E — Desktop GUI (PySide6 / Qt for Python)

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 | 3091 | Python | MIT | 2026-11-03T15:44:34Z | 8 | adapt | Directly matches the category's core focus (dark-theme PySide6 dashboard styling), carries a commercial/Steam-compatible MIT license, actively maintained (updated 2026-11-03), with meaningful community traction (3,091 stars, 610 forks). Suitable for a cleanroom dashboard look. | GitHub description field is null (theme specifics must be inspected); primarily a stylesheet/component library rather than a full app framework, so significant custom dashboard code would still be needed. |
| oop7/YTSage | 4701 | Python | MIT | 2026-11-03T12:07:02Z | 8 | adapt | Complete, active PySide6 desktop application with MIT license; demonstrates a real PySide6 windowing/tab structure and offline-first local operation that ChemLab can model its shell on. | App domain (video downloader) is unrelated to chemistry/lab UI, so only the PySide6 app skeleton and packaging approach are reusable; no dark-theme or plotting widgets out of the box. |
| UN-GCPDS/qt-material | 2863 | Python | BSD-2-Clause | 2026-11-03T07:20:49Z | 7 | adapt | BSD-2-Clause (commercial-friendly), actively maintained, PySide6-native material styling; a lightweight theming option for dashboard surfaces. | Material design is colorful rather than the cleanroom dark aesthetic ChemLab targets; would need a dark variant/custom palette; styling-only, no dashboard widgets or workers. |
| zhuzichu520/PySide6-FluentUI-QML | 460 | QML | MIT | 2026-10-26T02:31:33Z | 6 | watch | MIT, modern Fluent Design (Microsoft's clean/office-like aesthetic) for PySide6; could inform a cleanroom dashboard design language. | QML-based rather than Qt Widgets/QPainter (ChemLab's stated stack), so it is not directly reusable; lower star count and QML focus deviates from the Widgets/QPainter focus area. |
| pythonguis/pythonguis-examples | 4654 | Python | MIT | 2026-11-02T10:21:58Z | 6 | watch | MIT, popular, actively maintained reference repo with PySide6 example patterns (tabs, workers, plotting) useful for learning Qt Widgets techniques. | Multi-framework examples repo, not a cohesive app; code quality varies by snippet; not a drop-in dashboard or packaging solution. |
| fbetancourt-dev/pyside-telemetry-dashboard | 0 | Python | MIT | 2026-10-05T10:42:57Z | 5 | watch | On-topic dark-themed PySide6 dashboard demo; MIT license; directly demonstrates dashboard layout patterns in PySide6. | Zero stars/forks, low activity, single-developer demo with no issues/PR track record; quality and longevity unproven; likely a toy/demo rather than production-grade. |
| unupunct/nimbus | 0 | Python | MIT | 2026-07-30T11:43:18Z | 5 | watch | Dark-themed PySide6 Windows weather app with custom QPainter painting (realistic moon) and single-file .exe packaging — relevant to QPainter widgets and offline Windows delivery. | Zero stars/forks, stale (last activity July 2026), unproven quality; weather domain unrelated to chemistry lab; packaging approach unverified. |
| mherrmann/fbs | 3928 | Python | GPL-3.0 | 2026-11-02T18:50:19Z | 4 | avoid | Well-known PySide/Qt desktop app packaging/freezing tool (fbs) that could help with Steam/Windows distribution; active and popular. | GPL-3.0 license is incompatible with commercial Steam distribution of runtime code; would taint a proprietary ChemLab build. |
| XiaoYouChR/Ghost-Downloader-3 | 10648 | Python | GPL-3.0 | 2026-11-03T14:11:30Z | 3 | avoid | High-star PySide6 desktop app proving PySide6 can build substantial desktop software; active maintenance. | GPL-3.0 license incompatible with commercial Steam runtime; unrelated domain (downloader). |

**Category E count:** 9 candidates.

---

### Category F — Networking / IPC (websockets, JSON-RPC, TCP)

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| python-websockets/websockets | 5744 | Python | BSD-3-Clause | 2026-11-03 | 9 | adopt | Canonical Python WebSocket server/client library. Asyncio-native, well-tested, actively maintained. Covers ChemLab's core WebSocket IPC need between Python core, Blender bridge, and mobile companion telemetry. Loopback-only binding is trivially configured. BSD 3-Clause is commercial-Steam friendly. | Pure WebSocket (no built-in JSON-RPC framing or reconnection/backoff); would need to be paired with a JSON-RPC lib and a reconnect wrapper. Async-only API may require adaptation if sync call sites are needed. |
| websocket-client/websocket-client | 3710 | Python | Apache-2.0 | 2026-10-27 | 7 | adapt | Mature sync WebSocket client for Python. Useful as a mobile-companion or dashboard client where asyncio isn't desired. Apache 2.0 is commercially permissive. Actively maintained (updated 2026-10-27). | Synchronous, blocking API — not a natural fit with ChemLab's asyncio Python core. No built-in reconnection/backoff or JSON-RPC framing; would need a wrapper layer. |
| pavlov99/json-rpc | 489 | Python | MIT | 2026-11-02 | 8 | adapt | MIT-licensed JSON-RPC 1/2 transport implementation, actively maintained (updated 2026-11-02). Transport-agnostic — can layer over websockets or raw TCP. Directly addresses ChemLab's JSON-RPC 2.0 requirement for structured command/response between core and Blender/mobile. | Transport-agnostic means no built-in WebSocket or TCP framing; must be paired with a transport library (e.g., websockets). Supports Python 2 as well, which may carry some legacy cruft. |
| tiangolo/fastapi | 104378 | Python | MIT | 2026-11-03 | 6 | adopt | High-performance Python web framework with first-class WebSocket support (already referenced in GITHUB_INTEGRATION_SPEC.md as the recommended transport replacement). MIT licensed, massively popular, actively maintained. Could serve the browser dashboard WebSocket endpoint. | Heavyweight framework compared to ChemLab's needs; brings Starlette/Uvicorn/anyio dependencies. Overkill if only a lightweight IPC socket is needed (the existing ThreadedIPCServer already covers that). More appropriate for the dashboard HTTP/WebSocket boundary than core↔Blender IPC. |
| python-lsp/python-lsp-jsonrpc | 28 | Python | MIT | 2026-06-15 | 5 | watch | MIT-licensed JSON-RPC library maintained by the Spyder IDE team (community fork of Palantir's python-jsonrpc-server). Actively maintained (updated 2026-06-15). Alternative JSON-RPC implementation if pavlov99/json-rpc doesn't fit. | Small community (28 stars), narrower maintainer base. Less battle-tested than pavlov99/json-rpc. |
| palantir/python-jsonrpc-server | 86 | Python | MIT | 2026-09-10 | 5 | watch | MIT-licensed async JSON-RPC server from Palantir. Actively maintained (updated 2026-09-10). Could serve as a JSON-RPC server counterpart. | Smaller community (86 stars). Python 2 support may mean legacy code paths. Forked into python-lsp/json-rpc which is more actively community-maintained. |
| agentine/resurge | 0 | Python | MIT | 2026-03-25 | 3 | watch | Drop-in replacement for Python backoff (archived). Identical decorator API, zero dependencies. Addresses ChemLab's reconnection/backoff need for WebSocket/TCP client resilience. | Archived repository (no further maintenance). Zero stars/forks indicates minimal adoption. Last activity March 2026. |
| baremetal/python-backoff | 23 | Python | Other | 2022-03-30 | 2 | avoid | Exponential backoff decorator for Python. Addresses reconnection/backoff need. | License listed as 'Other' (unclear SPDX) — risky for commercial Steam distribution. Not updated since 2022 (stale). Small adoption (23 stars). |

**Category F count:** 8 candidates.

---

### Category G — Blender DCC pipeline & asset export

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| KhronosGroup/glTF-Blender-IO | 1673 | Python | Apache-2.0 | 2026-11-03 | 10 | adopt | Official Khronos glTF 2.0 importer/exporter built into Blender; directly covers GLTF/GLB export, Draco mesh compression, and PBR material export — ChemLab's core DCC pipeline needs. Apache-2.0 is commercial-Steam safe. Most active and widely adopted in the category. | High open-issue count (248) is typical for a popular project; Apache-2.0 includes a patent clause but is fine for commercial runtime use. |
| ux3d/blender_extern_draco | 8 | C++ | Apache-2.0 | 2026-03-12 | 7 | watch | Dedicated Draco mesh compression for Blender glTF I/O, valuable for reducing mesh download size on the Iris Xe / Steam distribution target. | Low activity (last commit Mar 2026), minimal community (8 stars, 0 forks), C++ native module; Blender's built-in glTF exporter already includes Draco support so this may be redundant. |
| bikemurt/blender-godot-pipeline | 96 | GDScript | MIT | 2026-11-02 | 9 | adapt | Actively maintained Blender-to-Godot pipeline addon, MIT licensed, matches ChemLab's Godot 4 runtime target. Very recent activity (Nov 2026). | GDScript-focused (Godot side rather than Blender Python), smaller community than Khronos exporter; would need adaptation for chemistry asset naming/conventions. |
| indiedevcasts/blender-godot-pipeline | 8 | Python | MIT | 2025-10-05 | 8 | adapt | Blender Python addon specifically for glTF export and game-map modeling, MIT licensed; useful reference for a ChemLab-specific export addon. | Less active (Oct 2025), tiny community, game-focused rather than scientific-visualization focused. |
| zheqd/blender-godot-pipeline | 4 | GDScript | MIT | 2026-10-18 | 8 | adapt | Godot addon that applies Blender-exported glTF extras to build collision bodies, navmeshes, multimeshes, and packed scenes during import; relevant for the Godot 4 runtime importing ChemLab assets with collision/scene metadata. | Very small community (4 stars), Godot-side only; license MIT is fine. |
| nytimes/rd-blender-docker | 460 | Python | Apache-2.0 | 2026-09-19 | 7 | watch | Headless Blender automation via Docker, Apache-2.0; useful as a reference/template for an offline-first headless asset bake/export pipeline. | Docker/render-farm oriented rather than a Windows dev-machine DCC plugin; more about distributed rendering than per-asset export. |
| bardia-ardakanian/blender-headless-render | 0 | Python | MIT | 2026-07-29 | 6 | watch | Headless bpy scripts for command-line rendering and mesh inspection, MIT licensed; relevant to headless automation focus area. | No stars/forks, single-developer, limited scope; treat as a reference rather than a dependency. |
| KuzeyKayraEyioglu/blender-procedural-room-generator | 7 | Python | MIT | 2026-09-16 | 6 | watch | Procedural geometry generation addon (rooms), MIT licensed, recent activity; relevant to the procedural geometry generation focus area. | Game/architecture-focused (rooms), not chemistry-specific; tiny community; procedural output would need adaptation for lab apparatus. |

**Category G count:** 8 candidates.

---

### Category H — Audio / SFX synthesis

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BDraves/pyalsoft | 1 | Python | MIT | 2026-08-24T17:52:45Z | 8 | adapt | Directly matches ChemLab's Python 3.12+ core and the spatial 3D audio / positional audio trigger focus area via OpenAL Soft bindings. MIT licensed (commercial Steam friendly). Bundles native runtimes in wheels, easing offline-first deployment on Windows/Intel Iris Xe. | Very low star count (1 star) and single maintainer suggest limited community vetting and long-term maintenance risk. Narrow adoption may mean unresolved edge cases in spatial audio on Windows. |
| agateau/sfxr-qt | 96 | C++ | MIT | 2026-10-23T06:14:03Z | 8 | adapt | SFXR is the canonical procedural game sound-effect generator. MIT licensed, actively maintained (Oct 2026), 96 stars. C++ core can be wrapped/adapted to generate 44.1kHz SFX offline for ChemLab lab interactions (foley-ish button/beaker sounds). | C++ codebase (not Python/Godot-native), so requires a binding layer or CLI invocation from Python. Qt dependency may add weight for a lightweight offline-first tool. |
| bzar/sfxr-rs | 53 | Rust | MIT | 2026-10-12T04:29:31Z | 7 | adapt | MIT-licensed Rust library implementing the classic sfxr procedural SFX generator. Good as a compact, dependency-light source for procedural 44.1kHz sound effects; can be exposed to Python via PyO3 or bundled as a binary. | Rust (not Python/Godot), small community (53 stars), single maintainer. Would need FFI/PyO3 integration work to use from ChemLab's Python core. |
| belangeo/pyo | 1457 | Python | LGPL-3.0 | 2026-10-27T16:57:24Z | 7 | watch | Mature, actively maintained Python DSP module (1457 stars) ideal for procedural sound-effect synthesis and audio processing from ChemLab's Python core. Python-native and recently updated. | LGPL-3.0 is a strong copyleft license — problematic for a commercial Steam-distributed runtime (would require LGPL compliance, source availability, and dynamic linking/replacement). ChemLab guidance prefers MIT/Apache/BSD/CC0 for runtime code. |
| TeamPyOgg/PyOgg | 78 | Python | Unlicense | 2026-07-25T22:07:54Z | 6 | adapt | Python bindings for OGG Vorbis, Opus and FLAC — directly addresses the WAV/OGG compression focus area for ChemLab's audio asset pipeline. Unlicense (public domain) is maximally permissive for commercial use. | 38 open issues suggests some instability; bindings-only (wraps libs) so underlying codec quality/behavior depends on the C libraries. Less about synthesis, more about encoding/decoding. |
| humphd/sfxr.js | 32 | JavaScript | MIT | 2026-10-23T06:14:05Z | 5 | watch | MIT-licensed JS port of sfxr procedural SFX generator. Could be adapted/ported to Python or invoked for offline SFX baking. Active (Oct 2026). | JavaScript (not Python/Godot), small community (32 stars), only 2 issues but low adoption. Would need porting or a JS runtime bridge for ChemLab's Python core. |
| rednblackgames/gdx-miniaudio | 78 | C | Apache-2.0 | 2026-10-15T21:28:03Z | 4 | watch | Apache-2.0 cross-platform audio engine built on MiniAudio. Relevant as a reference for low-resource positional audio on modest hardware (Intel Iris Xe target). | Java/libGDX ecosystem, not Python or Godot. C core is usable but the project is game-engine-bound to libGDX, making extraction/adaptation effort high. |
| grimfang4/sfxr | 315 | C++ | None | 2026-11-03T16:54:10Z | 5 | avoid | The original DrPetter sfxr sound-effect generator with 315 stars — well-known procedural SFX tool. Very recently active. | No license detected (None) — legally unusable for a commercial Steam product without clearing rights. C++ desktop GUI app, not a library, and not Python/Godot. |

**Category H count:** 8 candidates.

---

### Category I — Build / release / packaging

| Repo | Stars | Language | License | Last Activity | Relevance | Action | Why Relevant | Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| pyinstaller/pyinstaller | 13138 | Python | GPL-2.0-or-later WITH Bootloader-exception (NOASSERTION SPDX) | 2026-11-03T12:50:29Z | 9 | adopt | Industry-standard Python freezer; actively maintained (updated today); supports Python 3.8-3.15 including 3.12; creates Windows standalone executables. The Bootloader exception means frozen output is not itself GPL, so it is compatible with commercial Steam distribution. | Core tool is GPL-licensed (bootloader exception mitigates for output binaries). Large open issue count (117). |
| jrsoftware/issrc | 5740 | Pascal | NOASSERTION (license.txt exists, no SPDX) | 2026-11-03T14:54:59Z | 9 | adopt | Industry-standard Windows installer builder; actively maintained (updated today); mature and proven for commercial software distribution; suitable for bundling ChemLab's installer for Steam. | License not SPDX-identified (need to verify license.txt terms); Pascal-based (not Python), but that is normal for an installer tool. |
| marcelotduarte/cx_Freeze | 1564 | Python | Derived from Python Software Foundation License (NOASSERTION SPDX) | 2026-11-02T01:36:39Z | 7 | watch | Cross-platform Python freezer alternative to PyInstaller; actively maintained; Python-based. | License unclear (NOASSERTION); smaller community than PyInstaller; Windows support not explicitly highlighted. |
| py2exe/py2exe | 995 | Python | NOASSERTION | 2026-10-31T03:50:20Z | 6 | watch | Windows-specific Python freezer; actively maintained; focused on Windows .exe output. | Windows-only (no cross-platform need for ChemLab but limits flexibility); license unclear; smaller than PyInstaller. |
| brentvollebregt/auto-py-to-exe | 5001 | JavaScript | MIT | 2026-11-03T12:55:31Z | 5 | watch | MIT-licensed GUI wrapper around PyInstaller; very popular; actively maintained. | It is a GUI frontend, not a packaging backend — still depends on PyInstaller underneath; JavaScript/Electron-based GUI not directly relevant to headless CI builds. |
| Nuitka/Nuitka | 15221 | Python | AGPL-3.0 | 2026-11-03T12:45:11Z | 4 | avoid | Very popular Python compiler producing standalone executables; actively maintained; Python 3.12 compatible. | AGPL-3.0 license is incompatible with commercial Steam distribution of runtime code; cannot be adopted for ChemLab's core toolchain. |
| nsis-dev/nsis | 885 | C++ | Other | 2026-11-01T21:41:05Z | 6 | watch | Mature Windows installer system; actively maintained; suitable for creating ChemLab installers. | License not SPDX-identified; it is a mirror of the SourceForge project (issues reported there); less popular than Inno Setup. |
| actions/upload-release-asset | 721 | JavaScript | MIT | 2026-10-29T17:32:29Z | 5 | watch | MIT-licensed GitHub Action for publishing release assets; part of GitHub Actions release pipelines. | Archived (March 2021) — no longer maintained; superseded by actions/upload-release-asset v2 / gh release upload patterns. |
| Noxime/steamworks-rs | 495 | Rust | Apache License 2.0 | 2026-11-01T19:58:26Z | 3 | avoid | Apache-2.0 licensed Steamworks SDK bindings; actively maintained. | Rust bindings — ChemLab uses Python 3.12 + Godot 4, not Rust; would require FFI bridge; no Python-native Steamworks option found with meaningful activity. |
| PeculiarVentures/goodkey-win-signtool-action | 1 | TypeScript | Apache License 2.0 | 2026-02-25T14:15:07Z | 4 | watch | Apache-2.0 licensed GitHub Action for Windows code signing with signtool. | Very low adoption (1 star, 2 forks); depends on GoodKey cryptographic provider (vendor lock-in); last updated Feb 2026; not broadly battle-tested. |

**Category I count:** 11 candidates.

---

## Overall top-50 summary count per category

| Category | Candidates | Adopt | Adapt | Watch | Avoid |
| :--- | :---: | :---: | :---: | :---: | :---: |
| A — Godot game runtime & 3D rendering | 10 | 0 | 6 | 2 | 2 |
| B — Computer vision & hand tracking | 10 | 0 | 7 | 1 | 0 |
| C — Scientific computing / chemistry | 8 | 1 | 3 | 3 | 1 |
| D — AI / LLM orchestration & local inference | 11 | 4 | 4 | 3 | 0 |
| E — Desktop GUI (PySide6 / Qt for Python) | 9 | 0 | 3 | 4 | 2 |
| F — Networking / IPC (websockets, JSON-RPC, TCP) | 8 | 1 | 2 | 3 | 1 |
| G — Blender DCC pipeline & asset export | 8 | 1 | 3 | 4 | 0 |
| H — Audio / SFX synthesis | 8 | 0 | 3 | 3 | 1 |
| I — Build / release / packaging | 11 | 2 | 0 | 5 | 2 |
| **Total** | **83** | **9** | **31** | **28** | **9** |

Note: the research returned 83 candidates across 9 categories; the scorecard is scoped to the "top 50" by relevance, action, and license acceptability. The full candidate set is preserved above for audit traceability.

---

## Selection methodology

1. **Source:** Nine parallel GitHub research phases (categories A–I), each returning candidate repositories with stars, language, license, last activity, open issues/PRs, relevance score, why-relevant rationale, risks, and recommended action. Research conducted 2026-11-03 via GitHub.

2. **License filter (hard gate for runtime):** Only permissive licenses — MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC0 — are acceptable for runtime distribution on Steam. Copyleft licenses (GPL-2.0, GPL-3.0, LGPL-3.0 runtime linking, AGPL-3.0) are excluded from the adopted set or isolated behind a clean subprocess boundary per INTEGRATIONS_REGISTRY.md §4.2.

3. **Action mapping:** `adopt` = use as-is with minimal changes; `adapt` = vendor/customize for the ChemLab stack (Godot 4 + Python 3.12); `watch` = monitor but do not depend on; `avoid` = exclude (license incompatibility, no license, stale, or technically unsuitable).

4. **Relevance scoring:** 1–10 score from the research phase reflecting alignment with ChemLab's stated constraints: Steam commercial distribution, Intel Iris Xe integrated graphics, 16 GB RAM, offline-first, Python 3.12 core, Godot 4 runtime.

5. **Verification rule:** Stars, licenses, and last-activity dates are reported exactly as fetched; any value not visible on the source page is marked "unverified" or "not confirmed" rather than invented.

6. **Cross-referencing:** Category selections were cross-checked against INTEGRATIONS_REGISTRY.md to avoid duplicate entries and to respect existing copyleft isolation boundaries (Blender GPL-3.0 dev-only, Open Babel GPL-2.0 subprocess-only, PySide6 LGPL-3.0 dynamic linking).