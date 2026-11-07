# ChemLab — Athanor Ascension Release Engineering Plan
**Version:** 1.0  
**Target:** Windows 11 / Steam Distribution  
**Date:** 2026-11-06  
**Status:** DRAFT — Release Preparation Phase

---

## 1. Executive Summary

ChemLab (Athanor Ascension) is a high-fidelity offline chemistry simulation with real thermodynamics, kinetics, and safety modeling. The project is currently **playable** with **306 tests collected** (3 pre-existing collection errors to resolve), but requires consolidation of duplicated modules, packaging fixes, and implementation of the comprehensive build pipeline documented in `docs/BUILD_AND_RELEASE.md`.

This release plan outlines the path to a **standalone Windows build** suitable for Steam distribution, with clear milestones, verification gates, and subsystem responsibilities.

---

## 2. Current Build/Export Status Per Platform

| Platform | Status | Current State | Gaps |
|:---------|:-------|:-------------|:---|
| **Windows** | ⚠️ **INCOMPLETE** | - Godot project configured with Compatibility Renderer<br>- Hand-tracking CV works offline<br>- Python chemistry core verified (306 tests collected, 3 pre-existing collection errors to resolve) | - No standalone build script<br>- Missing consolidated modules (chemlab_core, simulation, safety_simulation, storage)<br>- No automated build pipeline<br>- Assets not baked to glTF/KTX2<br>- No compression/binary optimization |
| **Linux** | 🚫 **NOT TARGETED** | - Godot compatibility renderer works | - Requires separate build configuration<br>- Needs Proton Steam integration |
| **macOS** | 🚫 **NOT TARGETED** | - Godot compatibility renderer works | - Requires native macOS build pipeline |
| **Web** | 🚫 **NOT TARGETED** | - Godot Web export possible but not planned | - No Web-based build pipeline |
| **Nintendo Switch** | 🚫 **TBD (MUST PLAN)** | - Target documented but no implementation<br>- Requires Switch SDK integration | - Major hardware adaptation needed<br>- Performance budgeting for Switch constraints |

---

## 3. Export Preset Gaps / Needed Changes

### 3.1 Missing Configuration
- **File:** `game/export_presets.cfg` — **NOT FOUND**
- **Impact:** No defined export presets for Windows/desktop builds
- **Resolution:** Create `game/export_presets.cfg` with Windows Desktop preset matching `docs/BUILD_AND_RELEASE.md` specification:
  ```ini
  [preset Windows Desktop]
  # Godot 4.x export settings for Windows 11 target
  config_version=5
  rendering/renderer/rendering_method=gl_compatibility
  window/size/viewport_width=1280
  window/size/viewport_height=720
  ```

### 3.2 Build Pipeline Requirements
**From `docs/BUILD_AND_RELEASE.md`:**
- PowerShell script `tools/build-windows.ps1` — **PRESENT BUT INCOMPLETE**
- Python runtime embedding (450 MB budget)
- Asset pipeline (Blender → glTF/KTX2)
- Code signing & Steam integration
- Verification & smoke testing

**Current Status:** Script exists but needs:
- Implementation of Python runtime creation
- Asset packaging pipeline
- Steamworks SDK integration
- Full verification suite

---

## 4. Versioning Scheme Proposal

### 4.1 Current Version
- **Git:** `HEAD a03f46d`
- **pyproject.toml:** `1.0.0`
- **project.godot:** `config_version=5`, `features=PackedStringArray("4.3", "Compatibility")`

### 4.2 Recommended Semantic Versioning
```
{major}.{minor}.{patch}-prerelease.YYYY-MM-DD
```

| Release Type | Example | When |
|:-------------|:-------|:---|
| **Major** | `2.0.0` | Breaking changes, major features |
| **Minor** | `1.1.0` | New features, backward compatible |
| **Patch** | `1.0.1` | Bug fixes, performance improvements |
| **Pre-release** | `1.0.0-2026-11-06` | Staging for distribution |

### 4.3 Branch Strategy
```
main/                 → Primary development, latest stable
feature/xxx/          → Feature branches (use GitHub flow)
maintenance/1.0.x/    → Hotfix only (for patch releases)
releases/             → Pre-release builds for QA
```

---

## 5. Build Pipeline (CI or Manual)

### 5.1 Recommended Approach: GitHub Actions CI
**Based on `docs/BUILD_AND_RELEASE.md` §3.3**

```yaml
# .github/workflows/build-windows.yml
name: Windows Build & Release

on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      version:
        description: 'Version tag'
        required: true

jobs:
  build:
    runs-on: windows-2022
    timeout-minutes: 60
    
    env:
      CODESIGN_CERT_THUMBPRINT: ${{ secrets.CODESIGN_CERT_THUMBPRINT }}
      STEAMWORKS_SDK: ${{ secrets.STEAMWORKS_SDK_PATH }}
      STEAM_APPID: ${{ secrets.STEAM_APPID }}
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install Godot
        run: choco install godot --version 4.3.0
      
      - name: Build
        run: .\tools\build-windows.ps1 -Configuration Release -Sign -Steam -Version ${{ github.ref_name }}
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ChemLab-Windows-${{ github.ref_name }}
          path: builds/windows/
```

### 5.2 Manual Pipeline (for now)
**Until CI is implemented:**
1. Ensure clean git state
2. Run validation gates (Section 7)
3. Execute build script manually:
   ```powershell
   .\tools\build-windows.ps1 -Configuration Release -Sign -Steam -Version 1.0.0-2026-11-06
   ```
4. Upload artifacts to Steam Depot via `steamcmd`
5. Create GitHub Release with artifacts

---

## 6. Content Qualification Checklist (Pre-Release)

### 6.1 Test Suite Requirements
- **Python Chemistry Core:** 306 tests collected (3 pre-existing collection errors to resolve)
- **Godot Headless Tests:** All smoke tests passing ✅ (binary at `tools/godot/Godot_v4.3.exe`)
- **Integration Tests:** Cross-module functionality verified
- **Performance Tests:** 60 FPS @ 1080p target hardware validation
- **Security Audits:** Anti-AI slop and vulnerability scans

### 6.2 Asset Requirements
- **3D Models:** All assets baked to glTF 2.0 (Draco compression)
- **Textures:** KTX2 / Basis Universal compressed textures
- **Audio:** Procedural SFX mastering at -12 dBFS
- **Shaders:** Optimized for Compatibility Renderer
- **Manifest:** `assets/manifest.json` with SHA256 integrity

### 6.3 Legal/Compliance
- **Licenses:** All third-party licenses in `licenses/`
- **Code Signing:** EV Code Signing Certificate
- **Antivirus Scan:** Clean VirusTotal report (0/70+ engines)
- **Accessibility:** Screen reader, colorblind, key rebind tested

### 6.4 Build Integrity
- **Reproducible Builds:** Deterministic exports and runtime
- **Size Limits:** `runtime/` ≤ 450 MB, total install ≤ 2.5 GB
- **Performance:** 60 FPS at target hardware (Section 6.3)

---

## 7. Store/Distribution Path Recommendation

### 7.1 Primary Distribution: Steam
**Recommended for PC release**

**Store Page Elements:**
- **App ID:** `1234560` (assign via Steamworks)
- **Build System:** Steam Depot with multi-platform support
- **Distribution:** Compressed installer + standalone executable
- **Cloud Save:** Steam Cloud integration (100 MB/user)

### 7.2 Secondary Distribution: Standalone Installer
**Windows-only, DVD retail alternative**

**Format:** Inno Setup installer (`tools/installer.iss`)
```
# Distribution Directory Structure
builds/installer/
├── ChemLab.exe                    # Godot 4.x exported binary (signed)
├── ChemLab.pck                    # Godot game data pack (encrypted)
├── runtime/                       # Embedded Python 3.12 (450 MB max)
├── assets/                        # Baked glTF/KTX2 assets
├── licenses/                      # Third-party licenses
├── README.txt                     # User launch instructions
├── steam_appid.txt                # "1234560"
└── version.json                   # Build metadata
```

### 7.3 Nintendo Switch Distribution
**For Nintendo Switch target (planned)**

- **Platform:** Nintendo Switch (TBD)
- **Requirements:** SDK integration, NDA, performance budgeting
- **Timeline:** Separate project phase after Windows release

---

## 8. Release Checklist Requirements from Other Subsystems

### 8.1 Performance Subsystem
- **Target Hardware:** Intel Core i5-1245U, Iris Xe (15W TDP)
- **FPS Requirements:** 60 FPS @ 1080p, 30 FPS @ 720p webcam
- **Memory Limits:** ≤ 1.5 GB total, ≤ 4 GB RAM, ≤ 2 GB VRAM
- **Latency:** <100 ms interaction latency

### 8.2 Art Subsystem
- **Asset Pipeline:** Blender → glTF/KTX2 conversion
- **Visual Style:** Real PBR materials, volumetric lighting
- **Quality:** No anti-aliasing artifacts, proper occlusion
- **Budget:** No memory leaks, efficient draw calls (<65)

### 8.3 Audio Subsystem
- **Procedural SFX:** All game sounds generated procedural
- **Performance:** No audio dropped frames
- **Master Level:** -12 dBFS maximum peak
- **Compression:** Ogg/Vorbis for files, no WAV bloat

### 8.4 Chemistry Subsystem
- **Algorithm Quality:** NIST/CRC constants, Arrhenius kinetics
- **Test Coverage:** 306 tests collected (3 pre-existing collection errors to resolve)
- **Offline Capability:** Zero runtime network dependencies
- **Safety Modeling:** GHS compliance, fume hood simulation

### 8.5 Computer Vision Subsystem
- **Hand Tracking:** MediaPipe 30 FPS with 1-Euro filter
- **Fallback:** Mouse/keyboard input when camera unavailable
- **Performance:** 1-Euro filter smooth tracking
- **Optional:** Lazy-load MediaPipe (reduce startup time)

---

## 9. Immediate Action Items (Next 48 Hours)

### 9.1 Critical Path
1. **Create `game/export_presets.cfg`** with Windows Desktop preset
2. **Implement `tools/build-windows.ps1`** (Python runtime, asset packaging)
3. **Install Godot** for headless testing
4. **Consolidate duplicated modules** (Phase A reconciliation)
5. **Run full test suite** with validation gates (Section 7)

### 9.2 Phase A Reconciliation
- Merge chemistry engines into single `src/chemlab/` package
- Move `chemlab_core/`, `simulation/`, `safety_simulation/`, `storage/` into proper packages
- Resolve reagent database duplication
- Ensure type safety (13 mypy errors resolved)

### 9.3 Packaging Fixes
- Fix `pyproject.toml` packaging configuration
- Add missing `requirements-windows.txt`
- Create proper Python embedded runtime structure

---

## 10. Risk Mitigation

### 10.1 Known Risks
1. **Hardware Dependency:** Intel Iris Xe GPU requirements
   - **Mitigation:** Compatibility Renderer fallback
2. **Package Size:** 450 MB Python runtime
   - **Mitigation:** Aggressive stdlib pruning, optional MediaPipe
3. **Testing Infrastructure:** Godot not installed
   - **Mitigation:** Install Godot for validation
4. **Module Duplication:** 4 overlapping implementations
   - **Mitigation:** Consolidation before release

### 10.2 Contingency Plans
- **Windows 11 Target:** Alternative graphics driver fallback
- **Python Runtime:** Smaller runtime, optional dependencies
- **Performance:** Dynamic resolution scaling if needed
- **Testing:** Docker-based Godot CI environment

---

## 11. Success Criteria

### 11.1 Technical Requirements
- ✅ 306 Python tests passing (after fixing 3 collection errors)
- ✅ Standalone Windows executable with embedded Python
- ✅ 60 FPS @ 1080p on target hardware
- ✅ Zero runtime network dependencies
- ✅ Complete Steam integration
- ✅ Code signing and antivirus clean

### 11.2 Business Requirements
- ✅ Launch on Steam (App ID assigned)
- ✅ Multi-language support (EN/DE/ES/JA)
- ✅ Store compliance (ratings, descriptions, artwork)
- ✅ Achievement system functional
- ✅ Cloud save synchronization
- ✅ Performance baseline verified

---

## 12. Timeline

**Phase 1 (Immediate - 48 hours):**
- Consolidate modules
- Create export_presets.cfg
- Implement build pipeline

**Phase 2 (Next 5 days):**
- Full test suite execution
- Godot installation and validation
- Asset pipeline setup

**Phase 3 (Next 2 weeks):**
- Build automation
- Smoke testing
- Packaging verification

**Phase 4 (Post-release):**
- Performance monitoring
- Hotfix preparation
- Platform expansion (Linux/macOS)

---

## 13. Verification Gates

### 13.1 Pre-Build Gates
- [ ] Clean git state
- [ ] All modules consolidated
- [ ] 306 tests passing (collection errors resolved)
- [ ] Godot installed and functional

### 13.こり Release Gates
- [ ] Standalone build successful
- [ ] Smoke test passes on clean VM
- [ ] Size budget met
- [ ] Performance baseline verified
- [ ] Code signed and antivirus clean
- [ ] Steam integration complete

---

**Next Review:** Phase C / Feature Completion sprint
**Owner:** Release Engineering Lead
**Next Checkpoint:** Build script implementation status

---

*This release plan is the authoritative specification for ChemLab Windows build and distribution. All changes must be reflected here before implementation.*

**Document ID:** DOC-CHEMLAB-REL-001
**Version:** 1.0
**Status:** DRAFT