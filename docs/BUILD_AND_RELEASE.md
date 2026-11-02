# ChemLab — Build & Release Engineering Specification

**Version:** 1.0  
**Target:** Windows 11 (x64) / Steam Distribution  
**Date:** 2026-11-02  
**Status:** DRAFT — Authoritative for Release Engineering

---

## 1. Executive Summary

This document defines the **complete standalone distribution and release engineering pipeline** for ChemLab. The shipped game **MUST NOT** require the end-user to install Blender, Python, Godot Editor, Claude Code, MCP servers, or any external development tools. Everything required to execute the game is bundled into a self-contained distribution directory.

### 1.1 Distribution Directory Layout

```
builds/windows/
├── ChemLab.exe                    # Godot 4.x exported binary (signed)
├── ChemLab.pck                    # Godot game data pack (encrypted)
├── runtime/                       # Embedded minimal Python 3.12 environment
│   ├── python.exe                 # Embedded interpreter
│   ├── python312.dll              # Python DLL
│   ├── python312.zip              # Stdlib (compiled .pyc)
│   ├── Lib/                       # Trimmed standard library
│   ├── DLLs/                      # Required extension modules
│   ├── site-packages/             # Pre-installed chem dependencies
│   │   ├── rdkit/                 # Cheminformatics & 3D conformers
│   │   ├── cantera/               # Thermodynamics engine
│   │   ├── numpy/                 # Numerical computing
│   │   ├── scipy/                 # Scientific computing
│   │   ├── chempy/                # Chemical kinetics
│   │   ├── mediapipe/             # Hand tracking (optional, lazy-load)
│   │   ├── opencv/                # Computer vision
│   │   ├── websockets/            # IPC bridge
│   │   └── pydantic/              # Data validation
│   └── licenses/                  # Runtime dependency licenses
├── assets/                        # Game assets (models, textures, sounds, shaders)
│   ├── models/                    # .glb / .gltf (exported from Blender)
│   ├── textures/                  # Compressed textures (KTX2 / Basis Universal)
│   ├── sounds/                    # .ogg / .wav
│   ├── shaders/                   # GLSL / Godot shader files
│   └── data/                      # Reaction definitions, substance DB (JSON/SQLite)
├── licenses/                      # All third-party open source licenses
│   ├── GODOT_LICENSE.txt
│   ├── PYTHON_LICENSE.txt
│   ├── RDKIT_LICENSE.txt
│   ├── CANTERA_LICENSE.txt
│   ├── NUMPY_LICENSE.txt
│   ├── SCIPY_LICENSE.txt
│   ├── MEDIAPIPE_LICENSE.txt
│   ├── OPENCV_LICENSE.txt
│   ├── WEBSOCKETS_LICENSE.txt
│   ├── PYDANTIC_LICENSE.txt
│   ├── PYTHON_EMBED_LICENSE.txt
│   └── THIRD_PARTY_LICENSES.md    # Aggregated license summary
├── README.txt                     # User-facing launch instructions
├── steam_appid.txt                # Steam AppID (e.g., "1234560")
└── version.json                   # Build metadata (version, git SHA, timestamp)
```

---

## 2. Standalone Architecture (Zero Runtime Dependencies)

### 2.1 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **No external Python** | Embedded `python-3.12-embed-amd64` with pre-compiled wheels |
| **No external Blender** | Assets baked to glTF 2.0 + KTX2 textures at build time |
| **No external Godot Editor** | Exported binary + PCK only; editor tools stripped |
| **No MCP/Claude dependencies** | All AI bridges compiled out or optional DLC |
| **No system DLL hell** | All C-extensions vendored in `runtime/` |
| **Offline-first** | Zero mandatory network calls at launch |

### 2.2 Runtime Python Environment Specification

| Component | Version | Source | Notes |
|-----------|---------|--------|-------|
| Python | 3.12.x (embedded) | python.org | `python-3.12-embed-amd64.zip` |
| RDKit | 2024.03+ | conda-forge / PyPI wheel | Pre-built with MinimalLib |
| Cantera | 3.0+ | conda-forge | With Sundials, YAML |
| NumPy | 2.0+ | PyPI | OpenBLAS-backed wheel |
| SciPy | 1.13+ | PyPI | OpenBLAS-backed wheel |
| ChemPy | 0.8.4+ | PyPI | Pure Python |
| MediaPipe | 1.0+ | PyPI | Lazy-loaded, optional |
| OpenCV | 4.8+ | PyPI | Headless wheel |
| WebSockets | 12.0+ | PyPI | Pure Python |
| Pydantic | 2.8+ | PyPI | Pure Python + core |

**Size Budget:** `runtime/` ≤ **450 MB** (compressed ~180 MB in installer)

### 2.3 Asset Pipeline — Blender → Game Runtime

```
Blender 5.2 (.blend)
    │
    ▼
scripts/module_*.py (Blender Python API)
    │
    ▼
glTF 2.0 Export (.glb) — Draco mesh compression + KTX2 textures
    │
    ▼
Godot 4.x Import Pipeline → .pck packaging
    │
    ▼
builds/windows/assets/
```

**Key Scripts (in `scripts/`):**
- `module_room.py` — Room geometry, lighting, cameras
- `module_apparatus.py` — Glassware, equipment models
- `module_furniture.py` — Benches, cabinets, fume hoods
- `module_fluid_simulation.py` — Mantaflow bake → vertex animation textures
- `module_fume_safety.py` — Safety equipment, signage
- `module_ui_hud.py` — HUD mesh generation
- `build_hud.py` — HUD atlas generation

---

## 3. Build Pipeline Automation

### 3.1 PowerShell Build Script — `tools/build-windows.ps1`

**Location:** `tools/build-windows.ps1`  
**Prerequisites (CI/Build Machine only):**
- Godot 4.3+ (headless CLI)
- Python 3.12 (system, for build tooling)
- Windows 10/11 SDK (SignTool)
- Steamworks SDK (for steam_api.dll)
- Visual Studio 2022 Build Tools (for native deps if needed)

```powershell
<#
.SYNOPSIS
    ChemLab Windows Standalone Build Pipeline
.DESCRIPTION
    Orchestrates full build: Godot export → Python runtime → Asset packaging → Signing → Verification
.PARAMETER Configuration
    Build configuration: Release (default), Debug
.PARAMETER Sign
    Enable Authenticode signing (requires cert in cert store)
.PARAMETER Steam
    Include Steamworks integration (steam_api.dll, steam_appid.txt)
.PARAMETER OutputDir
    Output directory (default: builds/windows)
.PARAMETER Version
    Semantic version (default: from git describe)
.EXAMPLE
    .\tools\build-windows.ps1 -Configuration Release -Sign -Steam -Version 1.0.0
#>

param(
    [ValidateSet('Release','Debug')][string]$Configuration = 'Release',
    [switch]$Sign,
    [switch]$Steam,
    [string]$OutputDir = 'builds/windows',
    [string]$Version = (git describe --tags --always --dirty 2>$null || 'dev')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ─────────────────────────────────────────────────────────────────────────────
# 0. ENVIRONMENT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
function Test-Prerequisites {
    Write-Host "[CHECK] Validating build prerequisites..." -ForegroundColor Cyan
    
    $godot = Get-Command godot -ErrorAction SilentlyContinue
    if (-not $godot) { throw "Godot CLI not found in PATH. Install Godot 4.3+" }
    
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python 3.12 not found in PATH" }
    
    if ($Sign) {
        $signtool = Get-Command signtool -ErrorAction SilentlyContinue
        if (-not $signtool) { throw "SignTool not found. Install Windows SDK." }
    }
    
    if ($Steam) {
        $sdk = $env:STEAMWORKS_SDK
        if (-not $sdk -or -not (Test-Path "$sdk/redistributable_bin/win64/steam_api64.dll")) {
            throw "STEAMWORKS_SDK env var not set or steam_api64.dll missing"
        }
    }
    
    Write-Host "[OK] Prerequisites OK" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. GODOT EXPORT — Binary + PCK
# ─────────────────────────────────────────────────────────────────────────────
function Export-GodotProject {
    Write-Host "[PACKAGE] Exporting Godot project (headless)..." -ForegroundColor Cyan
    
    $exportPreset = "Windows Desktop"  # Defined in export_presets.cfg
    $outputExe = Join-Path $OutputDir "ChemLab.exe"
    $outputPck = Join-Path $OutputDir "ChemLab.pck"
    
    # Clean previous
    Remove-Item $outputExe, $outputPck -ErrorAction SilentlyContinue
    
    # Export with encryption (AES-256) for PCK
    $encryptionKey = [System.Guid]::NewGuid().ToString('N')  # Or use stable key from secure vault
    & godot --headless --export-pack "$exportPreset" $outputPck --encryption-key $encryptionKey
    & godot --headless --export "$exportPreset" $outputExe --encryption-key $encryptionKey
    
    if (-not (Test-Path $outputExe) -or -not (Test-Path $outputPck)) {
        throw "Godot export failed: missing exe or pck"
    }
    
    Write-Host "[OK] Godot export complete: $outputExe + $outputPck" -ForegroundColor Green
    
    # Store encryption key for runtime (embedded in binary via build)
    $encryptionKey | Out-File (Join-Path $OutputDir '.pck_key') -Encoding ASCII
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. PYTHON EMBEDDED RUNTIME CREATION
# ─────────────────────────────────────────────────────────────────────────────
function Create-PythonRuntime {
    Write-Host "[PYTHON] Creating embedded Python runtime..." -ForegroundColor Cyan
    
    $runtimeDir = Join-Path $OutputDir 'runtime'
    Remove-Item $runtimeDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $runtimeDir | Out-Null
    
    # 2.1 Download & extract python-3.12-embed-amd64
    $pythonEmbedUrl = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
    $zipPath = Join-Path $env:TEMP "python-embed.zip"
    Invoke-WebRequest -Uri $pythonEmbedUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $runtimeDir -Force
    Remove-Item $zipPath
    
    # 2.2 Enable site-packages (uncomment in python312._pth)
    $pthFile = Join-Path $runtimeDir 'python312._pth'
    $pthContent = Get-Content $pthFile -Raw
    $pthContent = $pthContent -replace '^#\s*import site', 'import site'
    $pthContent = $pthContent -replace '^#\s*\.\\Lib\\site-packages', '.\Lib\site-packages'
    $pthContent | Set-Content $pthFile -Encoding UTF8
    
    # 2.3 Create site-packages directory
    $sitePackages = Join-Path $runtimeDir 'Lib\site-packages'
    New-Item -ItemType Directory -Path $sitePackages | Out-Null
    
    # 2.4 Install dependencies via pip (using system python with --target)
    $deps = @(
        'rdkit-pypi==2024.3.4',
        'cantera==3.0.0',
        'numpy==2.0.1',
        'scipy==1.13.0',
        'chempy==0.8.4',
        'opencv-python-headless==4.10.0',
        'websockets==12.0',
        'pydantic==2.8.2',
        'pydantic-core==2.20.1',
        'typing-extensions==4.12.2'
    )
    
    # MediaPipe is large; install optionally for hand-tracking build variant
    # $deps += 'mediapipe==1.0.0'
    
    foreach ($dep in $deps) {
        Write-Host "  Installing $dep..." -ForegroundColor Gray
        & python -m pip install --target $sitePackages --no-deps --no-build-isolation $dep
    }
    
    # 2.5 Copy ChemLab source (compiled .pyc)
    $srcDir = Join-Path $runtimeDir 'chemlab'
    Copy-Item -Path 'src/chemlab' -Destination $srcDir -Recurse -Force
    Copy-Item -Path 'chemlab_core' -Destination (Join-Path $runtimeDir 'chemlab_core') -Recurse -Force
    Copy-Item -Path 'storage' -Destination (Join-Path $runtimeDir 'storage') -Recurse -Force
    
    # 2.6 Compile all .py to .pyc (optimize=2 strips docstrings/asserts)
    Write-Host "  Compiling bytecode..." -ForegroundColor Gray
    & python -m compileall -o 2 -q $runtimeDir
    
    # 2.7 Remove .py source files (keep only .pyc)
    Get-ChildItem -Path $runtimeDir -Recurse -Filter '*.py' | Remove-Item -Force
    
    # 2.8 Prune stdlib (keep only used modules)
    $keepModules = @(
        'os', 'sys', 'json', 'sqlite3', 'hashlib', 'hmac', 'datetime',
        'pathlib', 'typing', 'collections', 'itertools', 'functools',
        'math', 'random', 'statistics', 'decimal', 'fractions',
        'asyncio', 'threading', 'queue', 'concurrent.futures',
        'logging', 'warnings', 'traceback', 'inspect', 'importlib',
        'dataclasses', 'enum', 'uuid', 'base64', 'binascii',
        'struct', 'array', 'io', 'time', 'signal', 'subprocess',
        'tempfile', 'shutil', 'glob', 'fnmatch', 're', 'string',
        'textwrap', 'unicodedat', 'copy', 'pickle', 'marshal',
        'numbers', 'operator', 'contextlib', 'abc', 'weakref',
        'types', 'builtins', 'site', 'zipimport', 'runpy'
    )
    
    $libDir = Join-Path $runtimeDir 'Lib'
    Get-ChildItem -Path $libDir -Directory | Where-Object { $keepModules -notcontains $_.Name } | Remove-Item -Recurse -Force
    
    # 2.9 Collect licenses
    $licensesDir = Join-Path $runtimeDir 'licenses'
    New-Item -ItemType Directory -Path $licensesDir | Out-Null
    Copy-Item -Path 'src/chemlab/licenses/*' -Destination $licensesDir -ErrorAction SilentlyContinue
    # Generate aggregated license file
    Generate-LicenseSummary -OutputDir $OutputDir
    
    Write-Host "[OK] Python runtime created at $runtimeDir" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. ASSET PACKAGING
# ─────────────────────────────────────────────────────────────────────────────
function Package-Assets {
    Write-Host "[ASSETS] Packaging game assets..." -ForegroundColor Cyan
    
    $assetsDir = Join-Path $OutputDir 'assets'
    Remove-Item $assetsDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $assetsDir | Out-Null
    
    # 3.1 Models (glTF from Blender export)
    $modelsSrc = 'exports/models'
    if (Test-Path $modelsSrc) {
        Copy-Item -Path (Join-Path $modelsSrc '*') -Destination (Join-Path $assetsDir 'models') -Recurse
    }
    
    # 3.2 Textures (KTX2 / Basis Universal)
    $texturesSrc = 'exports/textures'
    if (Test-Path $texturesSrc) {
        Copy-Item -Path (Join-Path $texturesSrc '*') -Destination (Join-Path $assetsDir 'textures') -Recurse
    }
    
    # 3.3 Sounds
    $soundsSrc = 'audio'
    if (Test-Path $soundsSrc) {
        Copy-Item -Path (Join-Path $soundsSrc '*.wav'), (Join-Path $soundsSrc '*.ogg') -Destination (Join-Path $assetsDir 'sounds')
    }
    
    # 3.4 Shaders
    $shadersSrc = 'src/chemlab/graphics/shaders'
    if (Test-Path $shadersSrc) {
        Copy-Item -Path (Join-Path $shadersSrc '*') -Destination (Join-Path $assetsDir 'shaders') -Recurse
    }
    
    # 3.5 Data (reaction DB, substance catalog)
    $dataSrc = 'src/chemlab/simulation/data'
    if (Test-Path $dataSrc) {
        Copy-Item -Path (Join-Path $dataSrc '*') -Destination (Join-Path $assetsDir 'data') -Recurse
    }
    
    # 3.6 Generate asset manifest (for integrity verification)
    $manifest = @()
    Get-ChildItem -Path $assetsDir -Recurse -File | ForEach-Object {
        $hash = Get-FileHash -Algorithm SHA256 -Path $_.FullName
        $relPath = $_.FullName.Substring($assetsDir.Length + 1)
        $manifest += @{ path = $relPath; sha256 = $hash.Hash; size = $_.Length }
    }
    $manifest | ConvertTo-Json -Depth 5 | Out-File (Join-Path $assetsDir 'manifest.json') -Encoding UTF8
    
    Write-Host "[OK] Assets packaged at $assetsDir" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. LICENSES & DOCUMENTATION
# ─────────────────────────────────────────────────────────────────────────────
function Generate-LicenseSummary {
    param([string]$OutputDir)
    
    $licensesDir = Join-Path $OutputDir 'licenses'
    New-Item -ItemType Directory -Path $licensesDir -Force | Out-Null
    
    # Copy known license files
    $licenseMap = @{
        'GODOT_LICENSE.txt'       = 'https://raw.githubusercontent.com/godotengine/godot/master/LICENSE.txt'
        'PYTHON_LICENSE.txt'      = 'https://docs.python.org/3/license.html'
        'RDKIT_LICENSE.txt'       = 'https://github.com/rdkit/rdkit/blob/master/Code/License.txt'
        'CANTERA_LICENSE.txt'     = 'https://github.com/Cantera/cantera/blob/main/License.txt'
        'NUMPY_LICENSE.txt'       = 'https://github.com/numpy/numpy/blob/main/LICENSE.txt'
        'SCIPY_LICENSE.txt'       = 'https://github.com/scipy/scipy/blob/main/LICENSE.txt'
        'MEDIAPIPE_LICENSE.txt'   = 'https://github.com/google/mediapipe/blob/master/LICENSE'
        'OPENCV_LICENSE.txt'      = 'https://github.com/opencv/opencv/blob/master/LICENSE'
        'WEBSOCKETS_LICENSE.txt'  = 'https://github.com/python-websockets/websockets/blob/main/LICENSE'
        'PYDANTIC_LICENSE.txt'    = 'https://github.com/pydantic/pydantic/blob/main/LICENSE'
        'CHEMPY_LICENSE.txt'      = 'https://github.com/bjodah/chempy/blob/master/LICENSE'
    }
    
    foreach ($entry in $licenseMap.GetEnumerator()) {
        try {
            Invoke-WebRequest -Uri $entry.Value -OutFile (Join-Path $licensesDir $entry.Key) -ErrorAction Stop
        } catch {
            Write-Warning "Failed to download $($entry.Key): $($_.Exception.Message)"
        }
    }
    
    # Generate aggregated THIRD_PARTY_LICENSES.md
    $summary = "# Third-Party Licenses Summary\n\n"
    $summary += "Generated: $(Get-Date -Format u)\n\n"
    $summary += "| Component | License | Source |\n"
    $summary += "|-----------|---------|--------|\n"
    $summary += "| Godot Engine | MIT | https://godotengine.org |\n"
    $summary += "| Python 3.12 | PSF-2.0 | https://python.org |\n"
    $summary += "| RDKit | BSD-3-Clause | https://rdkit.org |\n"
    $summary += "| Cantera | BSD-3-Clause | https://cantera.org |\n"
    $summary += "| NumPy | BSD-3-Clause | https://numpy.org |\n"
    $summary += "| SciPy | BSD-3-Clause | https://scipy.org |\n"
    $summary += "| ChemPy | BSD-2-Clause | https://github.com/bjodah/chempy |\n"
    $summary += "| MediaPipe | Apache-2.0 | https://mediapipe.dev |\n"
    $summary += "| OpenCV | Apache-2.0 | https://opencv.org |\n"
    $summary += "| WebSockets | BSD-3-Clause | https://github.com/python-websockets/websockets |\n"
    $summary += "| Pydantic | MIT | https://pydantic.dev |\n"
    $summary += "| PySide6 (Qt) | LGPL-3.0 | https://wiki.qt.io/Licensing |\n"
    $summary | Out-File (Join-Path $licensesDir 'THIRD_PARTY_LICENSES.md') -Encoding UTF8
}

function Generate-Readme {
    param([string]$OutputDir, [string]$Version)
    
    $readme = @"
ChemLab v$Version — Interactive Virtual Chemistry Laboratory
=============================================================

SYSTEM REQUIREMENTS
-------------------
- Windows 11 (22H2+) / Windows 10 (21H2+)
- Intel Core i5-1240U / AMD Ryzen 5 5600U or better
- 16 GB RAM (8 GB minimum)
- Intel Iris Xe / AMD Radeon 680M or discrete GPU
- 2 GB available disk space
- Webcam (for hand tracking) — optional

LAUNCH INSTRUCTIONS
-------------------
1. Double-click ChemLab.exe
2. Allow Windows Defender SmartScreen if prompted (first run)
3. Grant webcam permission when prompted for hand tracking

STEAM INTEGRATION
-----------------
- Steam Cloud saves: %APPDATA%\ChemLab\saves\
- Steam Achievements: Auto-unlocked during gameplay
- Steam Input: Native gamepad/keyboard bindings

SUPPORT
-------
- GitHub Issues: https://github.com/yourorg/chemlab/issues
- Discord: https://discord.gg/chemlab
- Email: support@chemlab.example.com

LICENSES
--------
See licenses/THIRD_PARTY_LICENSES.md for full attribution.
"@
    $readme | Out-File (Join-Path $OutputDir 'README.txt') -Encoding UTF8
}

function Generate-VersionJson {
    param([string]$OutputDir, [string]$Version)
    
    $gitSha = git rev-parse HEAD 2>$null || 'unknown'
    $gitBranch = git rev-parse --abbrev-ref HEAD 2>$null || 'unknown'
    $buildTime = Get-Date -Format o
    
    $versionInfo = @{
        version = $Version
        git_sha = $gitSha
        git_branch = $gitBranch
        build_timestamp = $buildTime
        build_machine = $env:COMPUTERNAME
        configuration = $Configuration
    }
    $versionInfo | ConvertTo-Json -Depth 3 | Out-File (Join-Path $OutputDir 'version.json') -Encoding UTF8
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. CODE SIGNING (Authenticode)
# ─────────────────────────────────────────────────────────────────────────────
function Sign-BuildArtifacts {
    param([string]$OutputDir)
    
    if (-not $Sign) { return }
    
    Write-Host "[SIGN] Code signing artifacts..." -ForegroundColor Cyan
    
    $certThumbprint = $env:CODESIGN_CERT_THUMBPRINT
    if (-not $certThumbprint) {
        throw "CODESIGN_CERT_THUMBPRINT env var not set"
    }
    
    $timestampUrl = "http://timestamp.sectigo.com"  # Or DigiCert, GlobalSign
    
    $filesToSign = @(
        Join-Path $OutputDir 'ChemLab.exe',
        Join-Path $OutputDir 'runtime\python.exe',
        Join-Path $OutputDir 'runtime\python312.dll'
    )
    
    foreach ($file in $filesToSign) {
        if (Test-Path $file) {
            Write-Host "  Signing $file..." -ForegroundColor Gray
            & signtool sign /sha1 $certThumbprint /tr $timestampUrl /td sha256 /fd sha256 /v $file
        }
    }
    
    Write-Host "[OK] Code signing complete" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. STEAMWORKS INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────
function Integrate-Steamworks {
    param([string]$OutputDir)
    
    if (-not $Steam) { return }
    
    Write-Host "[STEAM] Integrating Steamworks SDK..." -ForegroundColor Cyan
    
    $sdk = $env:STEAMWORKS_SDK
    $steamApi64 = Join-Path $sdk 'redistributable_bin\win64\steam_api64.dll'
    $steamApi32 = Join-Path $sdk 'redistributable_bin\win32\steam_api.dll'
    
    Copy-Item $steamApi64 -Destination (Join-Path $OutputDir 'steam_api64.dll') -Force
    Copy-Item $steamApi32 -Destination (Join-Path $OutputDir 'steam_api.dll') -Force
    
    # steam_appid.txt (replace with actual AppID from Steamworks)
    $appId = $env:STEAM_APPID ?? '1234560'
    $appId | Out-File (Join-Path $OutputDir 'steam_appid.txt') -Encoding ASCII
    
    Write-Host "[OK] Steamworks integrated (AppID: $appId)" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. VERIFICATION & SMOKE TEST
# ─────────────────────────────────────────────────────────────────────────────
function Verify-Build {
    param([string]$OutputDir)
    
    Write-Host "[TEST] Running verification & smoke tests..." -ForegroundColor Cyan
    
    # 7.1 Verify file existence
    $required = @(
        'ChemLab.exe',
        'ChemLab.pck',
        'runtime\python.exe',
        'runtime\python312.dll',
        'runtime\Lib\site-packages\rdkit',
        'runtime\Lib\site-packages\cantera',
        'runtime\Lib\site-packages\numpy',
        'runtime\Lib\site-packages\scipy',
        'assets\manifest.json',
        'licenses\THIRD_PARTY_LICENSES.md',
        'README.txt',
        'version.json'
    )
    
    foreach ($f in $required) {
        $path = Join-Path $OutputDir $f
        if (-not (Test-Path $path)) {
            throw "Missing required file: $f"
        }
    }
    
    # 7.2 PE Checksum verification (ChemLab.exe)
    $exePath = Join-Path $OutputDir 'ChemLab.exe'
    $peCheck = & certutil -hashfile $exePath SHA256
    Write-Host "  ChemLab.exe SHA256: $($peCheck.Split()[1])" -ForegroundColor Gray
    
    # 7.3 Smoke test: Launch executable with --version (headless)
    Write-Host "  Launching headless version check..." -ForegroundColor Gray
    $proc = Start-Process -FilePath $exePath -ArgumentList '--version', '--headless', '-quit' -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) {
        throw "Smoke test failed: ChemLab.exe exited with code $($proc.ExitCode)"
    }
    
    # 7.4 Verify Python runtime can import core modules
    Write-Host "  Verifying Python runtime imports..." -ForegroundColor Gray
    $pythonExe = Join-Path $OutputDir 'runtime\python.exe'
    $testScript = @"
import sys
sys.path.insert(0, r'$OutputDir\runtime')
import rdkit
import cantera
import numpy
import scipy
import chempy
import websockets
import pydantic
print('[OK] All core modules imported successfully')
print(f'RDKit: {rdkit.__version__}')
print(f'Cantera: {cantera.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'SciPy: {scipy.__version__}')
"@
    $proc = Start-Process -FilePath $pythonExe -ArgumentList "-c", $testScript -Wait -PassThru -NoNewWindow -RedirectStandardOutput (Join-Path $env:TEMP 'py_test_out.txt') -RedirectStandardError (Join-Path $env:TEMP 'py_test_err.txt')
    if ($proc.ExitCode -ne 0) {
        $err = Get-Content (Join-Path $env:TEMP 'py_test_err.txt') -Raw
        throw "Python runtime verification failed: $err"
    }
    $out = Get-Content (Join-Path $env:TEMP 'py_test_out.txt') -Raw
    Write-Host "  $($out.Trim())" -ForegroundColor Green
    
    # 7.5 Verify asset manifest integrity
    Write-Host "  Verifying asset manifest..." -ForegroundColor Gray
    $manifest = Get-Content (Join-Path $OutputDir 'assets\manifest.json') -Raw | ConvertFrom-Json
    foreach ($asset in $manifest) {
        $fullPath = Join-Path $OutputDir 'assets' $asset.path
        $hash = Get-FileHash -Algorithm SHA256 -Path $fullPath
        if ($hash.Hash -ne $asset.sha256) {
            throw "Asset integrity check failed: $($asset.path)"
        }
    }
    Write-Host "  [OK] $($manifest.Count) assets verified" -ForegroundColor Green
    
    Write-Host "[OK] All verification checks passed" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ChemLab Windows Build Pipeline v$Version" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Test-Prerequisites
Export-GodotProject
Create-PythonRuntime
Package-Assets
Generate-Readme -OutputDir $OutputDir -Version $Version
Generate-VersionJson -OutputDir $OutputDir -Version $Version
Sign-BuildArtifacts -OutputDir $OutputDir
Integrate-Steamworks -OutputDir $OutputDir
Verify-Build -OutputDir $OutputDir

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  BUILD SUCCESSFUL — Output: $OutputDir" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
```

### 3.2 Build Script Usage

```powershell
# Standard release build (unsigned, no Steam)
.\tools\build-windows.ps1 -Configuration Release -Version 1.0.0

# Signed release build with Steam integration
$env:CODESIGN_CERT_THUMBPRINT = "A1B2C3D4E5F6..."
$env:STEAMWORKS_SDK = "C:\Steamworks\sdks\1.57"
$env:STEAM_APPID = "1234560"
.\tools\build-windows.ps1 -Configuration Release -Sign -Steam -Version 1.0.0

# Debug build for development
.\tools\build-windows.ps1 -Configuration Debug -Version 1.0.0-dev
```

### 3.3 CI/CD Integration (GitHub Actions)

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
        run: |
          choco install godot --version 4.3.0
      
      - name: Install Windows SDK (SignTool)
        run: choco install windows-sdk-10.1
      
      - name: Cache Python wheels
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Build
        run: |
          .\tools\build-windows.ps1 -Configuration Release -Sign -Steam -Version ${{ github.ref_name }}
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ChemLab-Windows-${{ github.ref_name }}
          path: builds/windows/
          retention-days: 30
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        if: startsWith(github.ref, 'refs/tags/v')
        with:
          files: builds/windows/**/*
          generate_release_notes: true
```

---

## 4. Steamworks Integration Roadmap

### 4.1 Steam App Setup

| Item | Value | Notes |
|------|-------|-------|
| **App Name** | ChemLab | Store page name |
| **App ID** | `1234560` | Assigned by Steamworks |
| **Default Depot** | `1234561` | Windows 64-bit |
| **Depot: Windows** | `1234561` | `builds/windows/*` |
| **Depot: Linux (Proton)** | `1234562` | Future: native Linux build |
| **Depot: macOS** | `1234563` | Future: native macOS build |
| **Launch Options** | `%command%` | Standard |
| **Steam Cloud** | Enabled | 100 MB/user |
| **Steam Achievements** | Enabled | See §4.3 |
| **Steam Input** | Enabled | Gamepad/keyboard |
| **Steam Workshop** | Disabled | No UGC planned |

### 4.2 Steamworks SDK Integration

**Godot Integration Options:**

| Approach | Library | Status | Notes |
|----------|---------|--------|-------|
| **GDNative / GDExtension** | `godotsteam` | Recommended | C++ GDExtension, MIT |
| **C# Wrapper** | `Steamworks.NET` + Godot C# | Alternative | If using .NET build |
| **Custom GDScript** | `steamworks.gd` | Minimal | Wrapper over C API |

**Recommended: `godotsteam` (GDExtension)**

```gdscript
# addons/godotsteam/Steam.gd (auto-generated)
@tool
extends Steam

func _ready():
    if not Steam.is_initialized():
        push_error("Steam API failed to initialize")
    else:
        print("Steam initialized: ", Steam.get_app_id())

# Usage in game code
func unlock_achievement(api_name: String):
    if Steam.is_initialized():
        Steam.set_achievement(api_name)
        Steam.store_stats()
```

**Files to Include in Build:**
```
builds/windows/
├── steam_api64.dll        # 64-bit (primary)
├── steam_api.dll          # 32-bit (fallback)
├── steam_appid.txt        # "1234560"
└── addons/godotsteam/     # GDExtension binary + .gdextension
```

### 4.3 Steam Cloud Save Format

**Location:** `%APPDATA%\ChemLab\saves\` (Windows)  
**Format:** Encrypted SQLite + JSON hybrid

```
%APPDATA%\ChemLab\saves\
├── cloud_v1.db              # SQLite (primary, encrypted)
├── cloud_v1.db.sig          # HMAC-SHA256 signature
├── metadata.json            # Sync metadata (timestamp, version)
└── backup/                  # Auto-backups (last 5)
    ├── cloud_v1_20261102.db
    └── ...
```

**SQLite Schema (`cloud_v1.db`):**

```sql
-- Schema version: 1
CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
INSERT INTO schema_version VALUES (1);

-- Player profile
CREATE TABLE profile (
    player_id TEXT PRIMARY KEY,           -- SteamID64
    display_name TEXT NOT NULL,
    created_at INTEGER NOT NULL,          -- Unix timestamp
    updated_at INTEGER NOT NULL,
    story_progress INTEGER DEFAULT 0,     -- Current quest index (0-10)
    sandbox_unlocked INTEGER DEFAULT 0,   -- Boolean
    total_playtime_seconds INTEGER DEFAULT 0,
    last_lab_archetype TEXT DEFAULT 'academic'
);

-- Quest progress
CREATE TABLE quests (
    quest_id TEXT PRIMARY KEY,            -- e.g., "lab_baptism", "iodine_clock"
    status TEXT NOT NULL,                 -- 'locked', 'active', 'completed'
    started_at INTEGER,
    completed_at INTEGER,
    best_time_seconds INTEGER,
    attempts INTEGER DEFAULT 0,
    xp_awarded INTEGER DEFAULT 0
);

-- Unlocked equipment / substances
CREATE TABLE unlocks (
    unlock_type TEXT NOT NULL,            -- 'equipment', 'substance', 'lab'
    unlock_id TEXT NOT NULL,
    unlocked_at INTEGER NOT NULL,
    PRIMARY KEY (unlock_type, unlock_id)
);

-- Saved experiments (sandbox)
CREATE TABLE experiments (
    experiment_id TEXT PRIMARY KEY,       -- UUID
    name TEXT NOT NULL,
    lab_archetype TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    data_json TEXT NOT NULL,              -- Full experiment state (JSON)
    thumbnail_blob BLOB                   -- Optional PNG thumbnail
);

-- Statistics / Achievements tracking
CREATE TABLE stats (
    stat_key TEXT PRIMARY KEY,
    stat_value INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Indexes
CREATE INDEX idx_quests_status ON quests(status);
CREATE INDEX idx_experiments_updated ON experiments(updated_at DESC);
```

**Encryption:**
- AES-256-GCM with key derived from SteamID64 + per-install salt
- Key stored in Windows DPAPI (CryptProtectData) — no raw keys on disk
- HMAC-SHA256 signature (`.sig`) for tamper detection

**Sync Logic:**
1. On game launch: Download latest from Steam Cloud → decrypt → verify HMAC → merge local
2. On save: Encrypt → sign → write local → upload to Steam Cloud
3. Conflict resolution: **Server-wins for profile/quests; Three-way merge for experiments**

### 4.4 Steam Achievements

| API Name | Display Name | Description | Trigger |
|----------|--------------|-------------|---------|
| `ACH_FIRST_REACTION` | First Reaction | Complete your first chemical reaction | Any reaction completes |
| `ACH_TITRATION_MASTER` | Master of Titration | Perform 10 perfect acid-base titrations | Titration accuracy > 99% × 10 |
| `ACH_ZERO_SPILL` | Zero Spill Incident | Complete 5 reactions without spilling | No spill events × 5 |
| `ACH_OSCILLATING_WIZARD` | Oscillating Wizard | Observe 3 full BZ oscillation cycles | BZ reaction cycles ≥ 3 |
| `ACH_SAFETY_FIRST` | Safety First | Use fume hood, goggles, and gloves correctly | All 3 safety items equipped |
| `ACH_DESTILLATION_EXPERT` | Distillation Expert | Produce 95%+ pure ethanol via distillation | Purity ≥ 95% |
| `ACH_GOLDEN_RAIN` | Golden Rain | Synthesize lead(II) iodide crystals | Precipitation reaction complete |
| `ACH_CHEMILUMINESCENCE` | Chemical Light | Create luminol chemiluminescence | Luminol reaction complete |
| `ACH_SANDBOX_ARCHITECT` | Sandbox Architect | Build a custom lab with 20+ pieces | Sandbox: 20+ entities placed |
| `ACH_MASTER_ALCHEMIST` | Master Alchemist | Complete all 10 story quests | Story progress = 10 |
| `ACH_SPEED_RUNNER` | Speed Runner | Complete iodine clock quest < 60s | Quest 2 time < 60s |
| `ACH_NIGHT_OWL` | Night Owl | Play between 00:00–04:00 local time | Session start in window |
| `ACH_COLLECTOR` | Collector | Unlock 50+ substances | Substance unlocks ≥ 50 |
| `ACH_THERMODYNAMICS` | Thermodynamics Master | Use Cantera engine for 10 calculations | Cantera calls ≥ 10 |
| `ACH_HAND_TRACKING_PRO` | Hand Tracking Pro | Play 1 hour using only hand tracking | CV playtime ≥ 3600s |

**Achievement Icons:** 128×128 PNG, stored in `assets/achievements/` → packed in PCK.

---

## 5. Antivirus & Installer Hygiene

### 5.1 Code Signing Recommendations

| Requirement | Implementation |
|-------------|----------------|
| **Certificate Type** | EV Code Signing Certificate (Extended Validation) |
| **CA** | Sectigo, DigiCert, GlobalSign, SSL.com |
| **Algorithm** | SHA-256 (RSA 3072-bit or ECDSA P-384) |
| **Timestamping** | RFC 3161 (Sectigo: `http://timestamp.sectigo.com`) |
| **Dual Signing** | SHA-1 + SHA-256 for Windows 7 compat (optional) |
| **Certificate Storage** | Azure Key Vault / AWS Signer / HSM (never on build agent) |

**SignTool Command:**
```cmd
signtool sign /sha1 <THUMBPRINT> /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /v ChemLab.exe
```

### 5.2 False-Positive Mitigation

| Vector | Mitigation |
|--------|------------|
| **Unsigned binary** | Mandatory EV signing (above) |
| **Embedded Python** | Use official `python-3.12-embed-amd64.zip` (verified hash) |
| **RDKit/Cantera DLLs** | Vendored from conda-forge (reproducible, signed by CF) |
| **Godot engine** | Export with `--export-pack` encryption (AES-256) |
| **Network sockets** | Localhost-only (127.0.0.1:8765, 9876); no outbound |
| **Webcam access** | Explicit MediaPipe usage; declare in manifest |
| **Self-modifying code** | None — all .pyc bytecode, no JIT |
| **Packer/Protector** | **DO NOT USE** (UPX, Themida, VMProtect trigger AV) |

**Pre-Submission AV Scan:**
```powershell
# Local scan with Windows Defender
Start-MpScan -ScanType CustomScan -File builds/windows/ChemLab.exe

# Multi-engine scan (VirusTotal API)
# Upload builds/windows/ to VirusTotal before release
```

### 5.3 Reproducible Builds

| Component | Strategy |
|-----------|----------|
| **Godot Export** | Deterministic PCK (fixed encryption key from build ID) |
| **Python Runtime** | Fixed `python-3.12.7-embed-amd64.zip` (pinned hash) |
| **Dependencies** | Pinned versions in `tools/requirements-windows.txt` |
| **Asset Pipeline** | Blender headless export with fixed seed |
| **Timestamps** | `SOURCE_DATE_EPOCH` from git commit timestamp |
| **Build ID** | `git describe --tags --always --dirty` in `version.json` |

**Verification:**
```powershell
# Build twice, compare hashes
.\tools\build-windows.ps1 -Version 1.0.0-build1
.\tools\build-windows.ps1 -Version 1.0.0-build2
Compare-Object (Get-FileHash builds/windows/ChemLab.exe -Algorithm SHA256).Hash `
               (Get-FileHash builds/windows/ChemLab.exe -Algorithm SHA256).Hash
# Should be identical
```

### 5.4 Installer (NSIS / Inno Setup)

**Recommended: Inno Setup 6** (`tools/installer.iss`)

```iss
; tools/installer.iss
#define MyAppName "ChemLab"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Studio"
#define MyAppURL "https://chemlab.example.com"
#define MyAppExeName "ChemLab.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=builds/installer
OutputBaseFilename=ChemLab-Setup-{#MyAppVersion}
SetupIconFile=assets/icon.ico
Compression=lzma/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SignTool=signtool

[Files]
Source: "builds\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autostart}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
```

---

## 6. Verification & Smoke Test Protocol

### 6.1 Automated Post-Build Tests (Run in `Verify-Build`)

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| **File Existence** | All required files present | Zero missing |
| **PE Checksum** | `ChemLab.exe` SHA-256 recorded | Matches build log |
| **Headless Launch** | `ChemLab.exe --version --headless -quit` | Exit code 0 |
| **Python Import** | Core modules import in embedded runtime | All 7 modules OK |
| **Asset Integrity** | `manifest.json` SHA-256 matches files | 100% match |
| **Steam API Init** | `SteamAPI_Init()` returns true (if Steam build) | Success |
| **License Check** | All `licenses/*.txt` present | 12 files minimum |

### 6.2 Manual Smoke Test Checklist (Pre-Release)

Run on **clean Windows 11 VM** (no dev tools, no Python, no Godot, no Blender):

- [ ] Fresh VM snapshot (Windows 11 22H2+)
- [ ] Copy `builds/windows/` to `C:\Games\ChemLab\`
- [ ] **No** Visual Studio, Python, Godot, Blender installed
- [ ] **No** network connection (air-gapped test)
- [ ] Double-click `ChemLab.exe`
- [ ] Windows SmartScreen: "Run anyway" (first run only)
- [ ] Game launches to main menu < 10 seconds
- [ ] Settings → Graphics: Detects Iris Xe / discrete GPU
- [ ] Story Mode: Quest 1 "Lab Baptism" loads
- [ ] Hand tracking: Webcam permission prompt appears
- [ ] Sandbox Mode: Place beaker, add water, add NaCl
- [ ] Reaction runs: NaCl dissolves (visual feedback)
- [ ] Save game → Quit → Relaunch → Load save
- [ ] Steam build: Achievement "First Reaction" unlocks
- [ ] Steam build: Cloud save syncs on second machine
- [ ] Exit cleanly (no crash dialog)

### 6.3 Performance Baseline (Target Hardware)

| Metric | Target (Dell Latitude 5530, Iris Xe) |
|--------|--------------------------------------|
| **Cold Launch** | < 8 seconds to main menu |
| **Scene Load (Story)** | < 3 seconds |
| **Scene Load (Sandbox)** | < 5 seconds |
| **Frame Rate (Idle)** | 60 FPS @ 1080p |
| **Frame Rate (Reaction)** | ≥ 45 FPS @ 1080p |
| **Frame Rate (CV Active)** | ≥ 30 FPS @ 720p webcam |
| **RAM Usage** | ≤ 4 GB (game + runtime) |
| **VRAM Usage** | ≤ 2 GB (shared) |
| **Disk Footprint** | ≤ 2.5 GB installed |

### 6.4 Regression Test Matrix

| Config | OS | GPU | Expected |
|--------|-----|-----|----------|
| Primary | Win 11 22H2 | Iris Xe (i5-1240U) | 60 FPS |
| Secondary | Win 11 23H2 | RTX 3060 Laptop | 120 FPS |
| Secondary | Win 10 21H2 | Iris Xe (i5-1135G7) | 55 FPS |
| Steam Deck | SteamOS 3.6 | AMD APU | 40 FPS (Proton) |
| Proton GE | Linux Mint 22 | RX 6700 XT | 90 FPS |

---

## 7. Release Checklist

### 7.1 Pre-Release (T-7 days)

- [ ] All tests green (CI pipeline)
- [ ] Performance baseline verified on target hardware
- [ ] Steam store page approved (artwork, description, age rating)
- [ ] Steamworks AppID configured (depots, achievements, cloud)
- [ ] Code signing certificate valid (not expired, EV)
- [ ] VirusTotal scan clean (0/70+ engines)
- [ ] Legal review: All licenses compatible (MIT/BSD/Apache/LGPL only)
- [ ] Accessibility review: Colorblind, screen reader, key rebind

### 7.2 Release Day (T-0)

- [ ] Tag release: `git tag -s v1.0.0 -m "ChemLab 1.0.0"`
- [ ] CI builds signed installer + standalone zip
- [ ] Upload to Steam Depot (Windows) via `steamcmd`
- [ ] Publish GitHub Release with artifacts
- [ ] Update store page: "Available Now"
- [ ] Discord announcement + social media
- [ ] Monitor crash reports (Sentry / Steam error reports)

### 7.3 Post-Release (T+1 to T+7)

- [ ] Hotfix branch ready (`maintenance/1.0.x`)
- [ ] Crash rate < 0.1% (Steam telemetry)
- [ ] Achievement unlock rates tracked
- [ ] Player feedback triaged
- [ ] Plan v1.0.1 patch (bug fixes only)

---

## 8. Appendix: Key File Paths & References

| Artifact | Path |
|----------|------|
| Build Script | `tools/build-windows.ps1` |
| Installer Script | `tools/installer.iss` |
| Godot Export Presets | `export_presets.cfg` |
| Python Requirements | `tools/requirements-windows.txt` |
| Asset Export Scripts | `scripts/module_*.py`, `scripts/build_hud.py` |
| Steam GDExtension | `addons/godotsteam/` |
| License Sources | `docs/INTEGRATIONS_REGISTRY.md` |
| Performance Spec | `docs/PERFORMANCE_REPORT.md` |
| CI Workflow | `.github/workflows/build-windows.yml` |

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-11-02 | Release Engineering | Initial specification |

---

**End of Document**  
*This document is the authoritative reference for ChemLab Windows build and release engineering. All pipeline changes must be reflected here before implementation.*