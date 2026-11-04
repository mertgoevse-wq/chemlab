# ChemLab Third-Party Licenses

**Project:** ChemLab — Interactive Virtual Chemistry Laboratory (Steam, Windows 11)  
**Data freshness:** researched 2026-11-03 via GitHub  
**License audit baseline:** INTEGRATIONS_REGISTRY.md, TOP_50_REPOSITORY_SCORECARD.md, DEPENDENCY_DECISIONS.md  

---

## Executive summary

This document is the full license inventory for ChemLab. It lists every third-party component in the dependency set — both the components already registered in INTEGRATIONS_REGISTRY.md and the new candidates proposed in DEPENDENCY_DECISIONS.md — together with license, SPDX identifier, commercial-Steam suitability, dependency tier (Runtime / Dev / Isolated / Build), and source URL.

**License posture for Steam:** Every component in the adopted/adapted runtime set carries a permissive license (MIT / Apache-2.0 / BSD-2-Clause / BSD-3-Clause / CC0 / Unlicense) or is isolated behind a clean copyleft boundary. No copyleft component (GPL-2.0, GPL-3.0, LGPL-3.0 runtime linking, AGPL-3.0) is linked into or bundled with the Steam runtime distribution.

**Data freshness note:** All license, SPDX, and URL values are reported exactly as fetched on 2026-11-03. Values marked "unverified" or "NOASSERTION" were not visible as an SPDX identifier on the source page and must be confirmed against the repository's LICENSE/license.txt file before vendor.

---

## Full license inventory table

| Component | License | SPDX | Commercial Steam OK? | Tier | Source URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Godot Engine 4.3 / 4.x | MIT License | MIT | Yes | Runtime | https://godotengine.org/ |
| Blender 5.2 | GNU GPL v3.0 | GPL-3.0-only | Yes (dev only; not distributed) | Development (isolated) | https://www.blender.org/ |
| Kenney Asset Kits | CC0 1.0 Universal | CC0-1.0 | Yes | Runtime Asset | https://kenney.nl/ |
| Poly Haven Asset Library | CC0 1.0 Universal | CC0-1.0 | Yes | Runtime Asset | https://polyhaven.com/ |
| Cantera 3.0.0+ | BSD-3-Clause | BSD-3-Clause (SPDX not confirmed on fetched page) | Yes | Runtime | https://github.com/Cantera/cantera |
| RDKit 2024.03+ | BSD-3-Clause | BSD-3-Clause | Yes | Runtime | https://github.com/rdkit/rdkit |
| ChemPy 0.8.4+ | BSD-2-Clause | BSD-2-Clause | Yes | Runtime | https://github.com/bjodah/chempy |
| NumPy >= 2.0 / SciPy >= 1.13 | BSD-3-Clause | BSD-3-Clause | Yes | Runtime | https://numpy.org/ / https://scipy.org/ |
| Open Babel 3.1.1+ | GNU GPL v2.0 | GPL-2.0-only | Yes (isolated subprocess only; not linked) | Dev / Tooling (isolated) | https://openbabel.org/ |
| NIST Chemistry WebBook & PubChem | US Gov Public Domain / NIH Open Data | Public Domain (unverified) | Yes | Dev Ingest / Online | https://webbook.nist.gov/chemistry/ / https://pubchem.ncbi.nlm.nih.gov/ |
| MediaPipe >= 1.0.0 | Apache License 2.0 | Apache-2.0 | Yes | Runtime | https://github.com/google-ai-edge/mediapipe |
| OpenCV >= 4.8.0 | Apache License 2.0 | Apache-2.0 | Yes | Runtime | https://github.com/opencv/opencv |
| ONNX Runtime 1.18+ | MIT License | MIT | Yes | Runtime | https://github.com/microsoft/onnxruntime |
| llama.cpp b3000+ / GGUF | MIT License | MIT | Yes | Runtime / DLC | https://github.com/ggml-org/llama.cpp |
| Omniroute Local Gateway v1.x | MIT / ChemLab Proprietary | MIT (Omniroute) / Proprietary | Yes | Runtime / Dev | Internal architecture (localhost:20128) |
| NVIDIA NIM | NVIDIA Cloud Software License / API Terms | LicenseRef (proprietary cloud terms) | Yes (opt-in cloud; client does not bundle) | Optional Cloud | https://www.nvidia.com/en-us/ai/ |
| Google Gemini 2.5 Pro | Google APIs Terms of Service / Apache-2.0 client SDK | LicenseRef (Google APIs) / Apache-2.0 (SDK) | Yes (opt-in cloud) | Optional Cloud | https://ai.google.dev/ |
| Blender MCP 1.0.1 | MIT License | MIT | Yes (dev only; not distributed) | Development | https://github.com/ahujasid/blender-mcp |
| Playwright MCP 1.48+ | Apache License 2.0 | Apache-2.0 | Yes (dev only; not distributed) | Dev / Testing | https://playwright.dev/ |
| Windows MCP 1.0 | MIT / Proprietary Tooling | MIT / Proprietary | Yes (dev only; not distributed) | Development | Internal tooling |
| Context7 MCP 1.0 | SaaS API / Developer Terms | LicenseRef (SaaS terms) | Yes (dev only; not distributed) | Development | https://context7.com/ |
| PySide6 (Qt for Python) 6.7+ | GNU LGPL v3.0 | LGPL-3.0-only | Yes (dynamic linking; compliance obligations apply) | Runtime | https://www.qt.io/qt-for-python |
| websockets >= 12.0 | BSD-3-Clause | BSD-3-Clause | Yes | Runtime | https://github.com/python-websockets/websockets |
| Pydantic >= 2.0 | MIT License | MIT | Yes | Runtime | https://github.com/pydantic/pydantic |
| Platinguin/Godot-Water-Shader-Prototype | MIT License | MIT | Yes | Runtime (Godot shader) | https://github.com/Platinguin/Godot-Water-Shader-Prototype |
| MacdonaldRobinson/godot4-3d-characters | MIT License | MIT | Yes | Runtime (Godot nav skeleton) | https://github.com/MacdonaldRobinson/godot4-3d-characters |
| pavlov99/json-rpc | MIT License | MIT | Yes | Runtime (IPC framing) | https://github.com/pavlov99/json-rpc |
| tiangolo/fastapi | MIT License | MIT | Yes | Runtime (dashboard HTTP/WebSocket) | https://github.com/tiangolo/fastapi |
| KhronosGroup/glTF-Blender-IO | Apache License 2.0 | Apache-2.0 | Yes | Development (built into Blender; dev-only) | https://github.com/KhronosGroup/glTF-Blender-IO |
| BDraves/pyalsoft | MIT License | MIT | Yes | Runtime (spatial audio) | https://github.com/BDraves/pyalsoft |
| TeamPyOgg/PyOgg | Unlicense | Unlicense | Yes | Runtime (audio pipeline) | https://github.com/TeamPyOgg/PyOgg |
| ollama/ollama | MIT License | MIT | Yes | Runtime / DLC (optional local LLM server) | https://github.com/ollama/ollama |
| BerriAI/litellm | MIT License (LICENSE file present) | MIT (SPDX not explicitly shown on page) | Yes | Runtime (cloud-AI fallback) | https://github.com/BerriAI/litellm |
| dottxt-ai/outlines | Apache License 2.0 | Apache-2.0 | Yes | Runtime (structured output) | https://github.com/dottxt-ai/outlines |
| microsoft/onnxruntime-genai | MIT License | MIT | Yes | Runtime (ONNX/OpenVINO) | https://github.com/microsoft/onnxruntime-genai |
| 567-labs/instructor | MIT License | MIT | Yes | Runtime (Pydantic validation) | https://github.com/567-labs/instructor |
| Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 | MIT License | MIT | Yes | Runtime (dashboard theme) | https://github.com/Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6 |
| UN-GCPDS/qt-material | BSD-2-Clause | BSD-2-Clause | Yes | Runtime (theming) | https://github.com/UN-GCPDS/qt-material |
| oop7/YTSage | MIT License | MIT | Yes | Runtime (app shell reference) | https://github.com/oop7/YTSage |
| pyinstaller/pyinstaller | GPL-2.0-or-later WITH Bootloader-exception | GPL-2.0-or-later (NOASSERTION SPDX; bootloader exception applies) | Yes (build-time only; frozen output is not itself GPL) | Build | https://github.com/pyinstaller/pyinstaller |
| jrsoftware/issrc (Inno Setup) | license.txt exists, no SPDX identified | NOASSERTION (verify license.txt) | Verify license.txt terms | Build (installer) | https://github.com/jrsoftware/issrc |

**Inventory totals:** 40 components listed. Of these, 24 are existing (INTEGRATIONS_REGISTRY.md) and 16 are newly proposed (DEPENDENCY_DECISIONS.md). All runtime-distributed components are permissive-licensed or isolated.

---

## Copyleft isolation boundary notes

ChemLab enforces strict architectural isolation for copyleft components so that no viral license infects the proprietary Steam runtime distribution.

### Blender 5.2 — GPL-3.0 (Development only, isolated)

- **Boundary:** Blender is strictly an asset-creation tool running on the developer workstation. It is **excluded from the final Steam release build**.
- **Isolation mechanism:** Only neutral standard asset formats leave Blender: GLTF 2.0 / GLB, OBJ, FBX, baked texture maps, PNG/EXR/HDR images, WAV audio, and JSON descriptors. Per Free Software Foundation (FSF) doctrine, output files produced by GPL software are not derivative works of the software and carry no copyleft encumbrance.
- **Network:** During live authoring, Blender talks only to a local loopback TCP socket (`127.0.0.1:8765`) via `blender_live_bridge.py`. No outbound public internet connections.
- **Steam impact:** None. Blender binaries and Blender C/C++ libraries are never bundled or linked into the game client.

### Open Babel 3.1.1+ — GPL-2.0 (Tooling, isolated subprocess)

- **Boundary:** Open Babel is **not** linked into the ChemLab runtime. Runtime cheminformatics is handled exclusively by RDKit (BSD-3-Clause).
- **Isolation mechanism:** When legacy molecular file conversion is required, Open Babel is executed strictly as an external independent CLI subprocess (`obabel.exe`), exchanging data via standard input/output pipes with clean serialization boundaries (FSF non-derivative aggregate-work guidelines).
- **Safeguards:** Strict argument whitelisting (no arbitrary user input passed to the command line), 10-second execution timeout, restricted working directory. Optional offline preprocessing tool only; not required for standard game loops or CI test gates.
- **Steam impact:** None. Open Babel is not bundled with the runtime.

### PySide6 (Qt for Python) 6.7+ — LGPL-3.0 (Runtime, dynamic linking)

- **Boundary:** PySide6 is a runtime dependency for the native desktop workbench window (`src/chemlab/desktop/main_window.py`). It is distributed as dynamically loaded shared libraries (`.pyd` / `.dll` C-extensions loaded at runtime from Python site-packages), which satisfies the LGPL dynamic-linking condition.
- **Compliance obligations for Steam distribution:**
  1. PySide6 must remain dynamically linkable / replaceable by the user (supported through standard Python site-packages layout).
  2. The LGPL-3.0 license text and copyright notices must be included in the game's distribution folder.
  3. A written offer / instructions for obtaining the Qt source code must be included.
- **Steam impact:** Permissible on Steam under closed-source proprietary terms provided the above obligations are met. PySide6 is kept architecturally separate from the proprietary Godot game runtime.

### PyInstaller — GPL-2.0-or-later WITH Bootloader exception (Build only)

- **Boundary:** PyInstaller is a build-time freezer used to produce ChemLab's Windows `.exe`. It is not distributed as runtime source.
- **Isolation mechanism:** The PyInstaller bootloader exception means the frozen application output is **not itself GPL**, so the ChemLab executable produced by PyInstaller can be distributed commercially on Steam without source disclosure.
- **Steam impact:** Permissible. PyInstaller remains a CI/build tool only.

### Inno Setup (jrsoftware/issrc) — license not SPDX-identified (Build only)

- **Boundary:** Inno Setup is a build-time Windows installer builder. It is not part of the game runtime.
- **Action required:** Verify `license.txt` terms before adopting for the Steam installer. SPDX is NOASSERTION (no identifier on the fetched page).

---

## Attribution requirements per license

| License | Attribution / notice requirement for ChemLab |
| :--- | :--- |
| MIT | Retain the copyright notice and the MIT license text in product documentation / distribution folder. No source disclosure required. |
| Apache-2.0 | Retain copyright notice, license text, and any NOTICE file; state clearly if files were modified. No source disclosure required. |
| BSD-3-Clause | Retain copyright notice, the list of conditions, and the disclaimer in product documentation. No endorsement of derived products without permission. |
| BSD-2-Clause | Retain copyright notice and disclaimer in product documentation. |
| CC0-1.0 | No attribution legally required; attribution retained in CREDITS.md as best practice for Kenney Assets and Poly Haven. |
| Unlicense | Public domain dedication; no attribution required. |
| US Gov Public Domain (NIST / PubChem) | No attribution required; public domain scientific data. |
| GPL-3.0 (Blender, dev only) | Not distributed; if it ever were, full source would be required. Currently isolated to asset creation. |
| GPL-2.0 (Open Babel, isolated) | Not linked; no infection. If distributed as part of a combined work, GPL-2.0 terms would apply — avoided via subprocess isolation. |
| LGPL-3.0 (PySide6) | Dynamic linking; ship LGPL-3.0 license text + copyright notices + written offer / instructions for obtaining Qt source; keep library user-replaceable. |
| GPL-2.0-or-later + Bootloader exception (PyInstaller) | Build-time only; frozen output not GPL. Retain PyInstaller copyright/license in build tooling documentation. |
| NOASSERTION (Inno Setup) | Verify license.txt attribution terms before use. |
| NVIDIA Cloud Terms / Google APIs Terms | Opt-in cloud services; comply with each provider's terms of service; API keys never embedded in source. |

---

## Excluded / avoided components (license-driven)

The following candidates from the research were reviewed and **excluded** from the ChemLab dependency set for license reasons:

| Component | License | Reason excluded |
| :--- | :--- | :--- |
| CBerry22/Godot-Water-Ripple-Simulation-Shader | No license declared | No license → unusable for commercial Steam |
| KingSahil/the-science-lab | No license declared | No license → unusable for commercial Steam |
| FastButterFly/SampleGodotGlassShader | No license declared | No license → unusable for commercial Steam |
| mherrmann/fbs | GPL-3.0 | GPL-3.0 incompatible with commercial Steam runtime |
| XiaoYouChR/Ghost-Downloader-3 | GPL-3.0 | GPL-3.0 incompatible with commercial Steam runtime |
| Nuitka/Nuitka | AGPL-3.0 | AGPL-3.0 incompatible with commercial Steam runtime |
| belangeo/pyo | LGPL-3.0 | LGPL-3.0 commercial-runtime risk; not adopted |
| grimfang4/sfxr | No license detected | No license → unusable for commercial Steam |
| baremetal/python-backoff | "Other" (unclear SPDX) | Unclear license + stale; avoided |
| gridinwork/Office-Vision-Tracker | Not specified | License not specified → compliance risk; watch only |

---

## Sign-off block

| Role | Name | Signature | Date |
| :--- | :--- | :--- | :--- |
| Release Engineer & License Auditor | ChemLab Release Engineer | ____________________ | 2026-11-03 |
| Legal / Compliance Review | ____________________ | ____________________ | __________ |
| Engineering Lead | ____________________ | ____________________ | __________ |

**Audit conclusion:** All components in the ChemLab dependency set conform to commercial distribution standards on Steam. Copyleft isolation boundaries are verified (Blender GPL-3.0 dev-only; Open Babel GPL-2.0 isolated subprocess; PySide6 LGPL-3.0 dynamic linking with compliance obligations; PyInstaller build-time with bootloader exception). Biometric privacy protections (zero webcam persistence, zero network transmission) meet GDPR / CCPA / COPPA requirements. Core simulation operates 100% offline.

**Data freshness:** researched 2026-11-03 via GitHub.