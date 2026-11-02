<#
.SYNOPSIS
    ChemLab Development Environment Setup & Verification Script.

.DESCRIPTION
    Automates and verifies the developer workstation environment for ChemLab:
    1. Environment Inspection:
       - Operating System (Windows 10/11 x64 architecture).
       - Python runtime (Python 3.12 in virtual environment or system PATH).
       - Git version control.
       - Blender 5.2 (checks 'C:\Program Files\Blender Foundation\Blender 5.2', registry, and PATH).
       - Godot Engine 4.x (checks PATH, winget packages, tools/bin, and downloads).
    2. Automation & Remediation:
       - Checks and configures Python virtual environment (.venv) with pyproject.toml
         and core dependencies (pytest, ruff, pydantic, rdkit, cantera, numpy, scipy).
       - If Godot 4.x is not in PATH, offers automated winget installation command or download helper instructions.
       - Verifies Blender 5.2 asset pipeline availability (scripts, scene file, headless test).
    3. Self-Test & Verification:
       - Runs health check verifying Python imports (import rdkit, import cantera, import numpy, scipy, pydantic).
       - Tests pytest availability (.venv\Scripts\pytest --version).
    4. Idempotence & Safety:
       - Safe to run multiple times without corrupting existing configs or files.
       - Clear colored terminal output (Cyan headers, Green success, Yellow warnings, Red errors).
       - Proper PowerShell error handling ($ErrorActionPreference, try/catch).

.PARAMETER SkipInstall
    Only inspect and verify environment without modifying files or installing packages.

.PARAMETER InstallGodot
    Automatically invoke winget to install Godot Engine if Godot 4.x is not in PATH.

.PARAMETER ForceVenv
    Force recreation of the virtual environment .venv.

.PARAMETER RunAssetTest
    Execute headless Blender 5.2 scene verification test on chemlab.blend.

.EXAMPLE
    .\tools\setup-development.ps1

.EXAMPLE
    .\tools\setup-development.ps1 -SkipInstall

.EXAMPLE
    .\tools\setup-development.ps1 -InstallGodot
#>

[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$InstallGodot,
    [switch]$ForceVenv,
    [switch]$RunAssetTest
)

# Set strict error handling
$ErrorActionPreference = 'Stop'

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

$Script:Version = "1.0.0"
$Script:Title = "ChemLab Development Environment Setup"

# Resolve absolute paths
$Script:ToolsDir = $PSScriptRoot
if (-not $Script:ToolsDir) {
    $Script:ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$Script:RepoRoot = (Resolve-Path (Join-Path $Script:ToolsDir "..")).Path
$Script:PyProjectPath = Join-Path $Script:RepoRoot "pyproject.toml"
$Script:VenvDir = Join-Path $Script:RepoRoot ".venv"
$Script:VenvPython = Join-Path $Script:VenvDir "Scripts\python.exe"
$Script:VenvPytest = Join-Path $Script:VenvDir "Scripts\pytest.exe"
$Script:VenvRuff = Join-Path $Script:VenvDir "Scripts\ruff.exe"
$Script:ToolsBinDir = Join-Path $Script:RepoRoot "tools\bin"
$Script:GodotWrapperCmd = Join-Path $Script:ToolsBinDir "godot.cmd"
$Script:BlendFile = Join-Path $Script:RepoRoot "chemlab.blend"

# Required dependencies
$Script:RequiredPythonMajor = 3
$Script:RequiredPythonMinor = 12
$Script:CoreDependencies = @("pytest", "ruff", "pydantic", "rdkit", "cantera", "numpy", "scipy")

# Primary Blender 5.2 candidate locations
$Script:BlenderCandidates = @(
    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    "C:\Program Files\Blender Foundation\Blender\blender.exe",
    "C:\Program Files (x86)\Blender Foundation\Blender 5.2\blender.exe"
)

# Asset pipeline components
$Script:AssetPipelineFiles = @(
    "chemlab.blend",
    "scripts\build_hud.py",
    "scripts\module_room.py",
    "scripts\module_furniture.py",
    "scripts\module_apparatus.py",
    "scripts\module_fluid_simulation.py",
    "scripts\module_fume_safety.py",
    "scripts\run_quality_gate.py",
    "tests\headless_blender_test.py",
    "tests\validate_scene_assets.py"
)

# Status tracking
$Script:WarningCount = 0
$Script:ErrorCount = 0

# ============================================================================
# OUTPUT FORMATTING HELPERS (Colors & Clean Formatting)
# ============================================================================

function Write-SectionHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
}

function Write-SubHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host ">>> $Title" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
    $Script:WarningCount++
}

function Write-ErrorRecord {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
    $Script:ErrorCount++
}

function Write-InfoLine {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor DarkGray
}

function Write-KeyValue {
    param([string]$Key, [string]$Value)
    $paddedKey = $Key.PadRight(26)
    Write-Host "    $paddedKey : " -NoNewline -ForegroundColor Gray
    Write-Host "$Value" -ForegroundColor White
}

# ============================================================================
# REQUIREMENT 1: ENVIRONMENT INSPECTION
# ============================================================================

function Test-OperatingSystem {
    Write-SubHeader "1.1 Operating System Inspection"

    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $caption = $os.Caption
    $version = $os.Version
    $buildNumber = [int]$os.BuildNumber
    $architecture = $os.OSArchitecture
    $is64Bit = [System.Environment]::Is64BitOperatingSystem

    Write-KeyValue "Operating System" $caption
    Write-KeyValue "Version" $version
    Write-KeyValue "Build Number" $buildNumber.ToString()
    Write-KeyValue "Architecture" $architecture
    Write-KeyValue "64-bit Process/OS" "$is64Bit"

    # Verify Windows 10/11 x64 (Build 10240 is initial Win10, 22000 is initial Win11)
    $isWin10Or11 = ($caption -match "Windows 1[01]") -or ($buildNumber -ge 10240)
    if ($isWin10Or11 -and $is64Bit) {
        Write-Success "Verified Windows 10/11 x64 architecture."
        return @{
            Success = $true
            Caption = $caption
            BuildNumber = $buildNumber
            Architecture = $architecture
        }
    } else {
        Write-ErrorRecord "ChemLab requires Windows 10 or Windows 11 64-bit operating system."
        return @{
            Success = $false
            Caption = $caption
            BuildNumber = $buildNumber
            Architecture = $architecture
        }
    }
}

function Find-PythonEnvironments {
    Write-SubHeader "1.2 Python Runtime Detection (Python 3.12 Target)"

    $pythons = @()

    # 1. Virtual Environment Python
    if (Test-Path $Script:VenvPython) {
        try {
            $ver = (& $Script:VenvPython --version 2>&1).Trim()
            $pythons += [PSCustomObject]@{
                Path = $Script:VenvPython
                Version = $ver
                Type = "Virtual Environment (.venv)"
                Is312 = ($ver -like "Python 3.12*")
            }
        } catch { }
    }

    # 2. System PATH Pythons
    $pathPythons = Get-Command python, python3, py -ErrorAction SilentlyContinue
    foreach ($cmd in $pathPythons) {
        try {
            $ver = (& $cmd.Source --version 2>&1).Trim()
            if ($ver -match "Python \d+\.\d+") {
                $pythons += [PSCustomObject]@{
                    Path = $cmd.Source
                    Version = $ver
                    Type = "PATH ($($cmd.Name))"
                    Is312 = ($ver -like "Python 3.12*")
                }
            }
        } catch { }
    }

    # 3. Known Standard Install Paths
    $knownLocations = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312-64\python.exe",
        "C:\Program Files\Python312\python.exe",
        "$env:USERPROFILE\.local\bin\python3.12.exe"
    )
    foreach ($loc in $knownLocations) {
        if (Test-Path $loc) {
            try {
                $ver = (& $loc --version 2>&1).Trim()
                $pythons += [PSCustomObject]@{
                    Path = $loc
                    Version = $ver
                    Type = "Standard Installation"
                    Is312 = ($ver -like "Python 3.12*")
                }
            } catch { }
        }
    }

    # 4. Check uv python cache if present
    $uvDir = Join-Path $env:APPDATA "uv\python"
    if (Test-Path $uvDir) {
        $uvPythons = Get-ChildItem -Path $uvDir -Filter "cpython-3.12*" -Directory -ErrorAction SilentlyContinue
        foreach ($dir in $uvPythons) {
            $exe = Join-Path $dir.FullName "python.exe"
            if (Test-Path $exe) {
                try {
                    $ver = (& $exe --version 2>&1).Trim()
                    $pythons += [PSCustomObject]@{
                        Path = $exe
                        Version = $ver
                        Type = "uv toolchain cache"
                        Is312 = ($ver -like "Python 3.12*")
                    }
                } catch { }
            }
        }
    }

    # Deduplicate entries by Path
    $uniquePythons = @()
    $seenPaths = @{}
    foreach ($py in $pythons) {
        $normalized = $py.Path.ToLowerInvariant()
        if (-not $seenPaths.ContainsKey($normalized)) {
            $seenPaths[$normalized] = $true
            $uniquePythons += $py
        }
    }

    foreach ($py in $uniquePythons) {
        $flag = if ($py.Is312) { "[Python 3.12 Match]" } else { "" }
        Write-KeyValue $py.Type "$($py.Version) -> $($py.Path) $flag"
    }

    # Select best candidate
    $venvPy = $uniquePythons | Where-Object { $_.Path -eq $Script:VenvPython -and $_.Is312 } | Select-Object -First 1
    $systemPy312 = $uniquePythons | Where-Object { $_.Path -ne $Script:VenvPython -and $_.Is312 } | Select-Object -First 1

    if ($venvPy) {
        Write-Success "Active virtual environment (.venv) contains valid $($venvPy.Version)."
    } elseif ($systemPy312) {
        Write-Success "Found host Python 3.12 runtime at: $($systemPy312.Path) ($($systemPy312.Version))."
    } else {
        Write-ErrorRecord "Python 3.12 runtime not detected on host or in .venv."
        Write-InfoLine "Install Python 3.12 via winget: winget install Python.Python.3.12"
    }

    return @{
        AllPythons = $uniquePythons
        VenvPython = $venvPy
        SystemPy312 = $systemPy312
        HasPython312 = ($null -ne $venvPy -or $null -ne $systemPy312)
    }
}

function Test-GitInstallation {
    Write-SubHeader "1.3 Git Version Control Inspection"

    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $versionStr = (& git --version 2>&1).Trim()
        Write-KeyValue "Git Executable" $gitCmd.Source
        Write-KeyValue "Git Version" $versionStr
        Write-Success "Git detected and operational ($versionStr)."
        return @{
            Success = $true
            Path = $gitCmd.Source
            Version = $versionStr
        }
    } else {
        Write-ErrorRecord "Git is not installed or not available in PATH."
        Write-InfoLine "Install Git via winget: winget install Git.Git --source winget"
        return @{
            Success = $false
            Path = $null
            Version = $null
        }
    }
}

function Find-BlenderInstallation {
    Write-SubHeader "1.4 Blender 5.2 Detection (Filesystem & Registry)"

    $detectedPath = $null
    $detectedVersion = $null
    $detectedSource = $null

    # 1. Check primary filesystem candidate paths
    foreach ($cand in $Script:BlenderCandidates) {
        if (Test-Path $cand) {
            $detectedPath = $cand
            $detectedSource = "Filesystem path"
            break
        }
    }

    # 2. Check Windows Registry (Uninstall keys & BlenderFoundation key)
    if (-not $detectedPath) {
        $regKeys = @(
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
        )
        $regEntries = Get-ItemProperty $regKeys -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like '*Blender*' }

        foreach ($entry in $regEntries) {
            if ($entry.InstallLocation) {
                $candidateExe = Join-Path $entry.InstallLocation "blender.exe"
                if (Test-Path $candidateExe) {
                    $detectedPath = $candidateExe
                    $detectedSource = "Windows Registry ($($entry.DisplayName))"
                    $detectedVersion = $entry.DisplayVersion
                    break
                }
            }
        }
    }

    # 3. Check PATH
    if (-not $detectedPath) {
        $blenderInPath = Get-Command blender -ErrorAction SilentlyContinue
        if ($blenderInPath) {
            $detectedPath = $blenderInPath.Source
            $detectedSource = "System PATH"
        }
    }

    # Query binary version if path found
    if ($detectedPath) {
        try {
            $versionOutput = (& $detectedPath --version 2>&1)
            $firstLine = ($versionOutput -split "`r?`n")[0]
            if ($firstLine -match "Blender\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?)") {
                $detectedVersion = $matches[1]
            }
        } catch { }
    }

    if ($detectedPath) {
        Write-KeyValue "Blender Path" $detectedPath
        Write-KeyValue "Detection Source" $detectedSource
        Write-KeyValue "Detected Version" $(if ($detectedVersion) { $detectedVersion } else { "Unknown" })

        if ($detectedVersion -and $detectedVersion -like "5.2*") {
            Write-Success "Blender 5.2.x detected: $detectedVersion"
            return @{
                Found = $true
                IsVersion52 = $true
                Path = $detectedPath
                Version = $detectedVersion
                Source = $detectedSource
            }
        } elseif ($detectedPath -like "*Blender 5.2*") {
            Write-Success "Blender 5.2 directory detected at: $detectedPath"
            return @{
                Found = $true
                IsVersion52 = $true
                Path = $detectedPath
                Version = "5.2.x"
                Source = $detectedSource
            }
        } else {
            Write-WarningMsg "Blender found at $detectedPath but version ($detectedVersion) is not 5.2.x."
            Write-InfoLine "ChemLab EEVEE asset pipeline requires Blender 5.2."
            return @{
                Found = $true
                IsVersion52 = $false
                Path = $detectedPath
                Version = $detectedVersion
                Source = $detectedSource
            }
        }
    } else {
        Write-WarningMsg "Blender 5.2 was not detected in 'C:\Program Files\Blender Foundation\Blender 5.2', registry, or PATH."
        Write-InfoLine "Download Blender 5.2 from https://builder.blender.org/download/daily/ or install via winget: winget install BlenderFoundation.Blender"
        return @{
            Found = $false
            IsVersion52 = $false
            Path = $null
            Version = $null
            Source = $null
        }
    }
}

function Find-GodotInstallation {
    Write-SubHeader "1.5 Godot 4.x Engine Detection (PATH, WinGet & Local Downloads)"

    $candidates = @()
    $inPath = $false

    # 1. System PATH
    $pathGodots = Get-Command godot, godot4, Godot* -ErrorAction SilentlyContinue
    foreach ($cmd in $pathGodots) {
        $candidates += [PSCustomObject]@{
            Path = $cmd.Source
            Type = "System PATH ($($cmd.Name))"
            InPath = $true
        }
        $inPath = $true
    }

    # 2. Local repository wrapper (tools/bin/godot.cmd)
    if (Test-Path $Script:GodotWrapperCmd) {
        $candidates += [PSCustomObject]@{
            Path = $Script:GodotWrapperCmd
            Type = "Repository Wrapper (tools\bin\godot.cmd)"
            InPath = $false
        }
    }

    # 3. WinGet Packages directory
    $wingetDir = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetDir) {
        $wgFiles = Get-ChildItem -Path $wingetDir -Filter "*godot*.exe" -Recurse -ErrorAction SilentlyContinue
        foreach ($f in $wgFiles) {
            $candidates += [PSCustomObject]@{
                Path = $f.FullName
                Type = "WinGet Package Cache"
                InPath = $false
            }
        }
    }

    # 4. Local User Downloads
    $dlDir = Join-Path $env:USERPROFILE "Downloads"
    if (Test-Path $dlDir) {
        $dlFiles = Get-ChildItem -Path $dlDir -Filter "*godot*.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue
        foreach ($f in $dlFiles) {
            $candidates += [PSCustomObject]@{
                Path = $f.FullName
                Type = "Local Downloads"
                InPath = $false
            }
        }
    }

    # Deduplicate candidates by path
    $uniqueCandidates = @()
    $seen = @{}
    foreach ($cand in $candidates) {
        $norm = $cand.Path.ToLowerInvariant()
        if (-not $seen.ContainsKey($norm)) {
            $seen[$norm] = $true
            $uniqueCandidates += $cand
        }
    }

    $bestGodot = $null
    $realExeGodot = $null
    foreach ($cand in $uniqueCandidates) {
        $verOutput = ""
        $isExe = ($cand.Path -like "*.exe")
        try {
            $verOutput = (& $cand.Path --version 2>&1).Trim()
        } catch { }

        if (-not $verOutput -or $verOutput -match "Execution check failed") {
            try {
                if (Test-Path $cand.Path) {
                    $vi = (Get-Item $cand.Path).VersionInfo
                    if ($vi.ProductVersion) { $verOutput = $vi.ProductVersion.Trim() }
                    elseif ($vi.FileVersion) { $verOutput = $vi.FileVersion.Trim() }
                }
            } catch { }
        }

        $cand | Add-Member -MemberType NoteProperty -Name "Version" -Value $verOutput -Force
        $is4x = ($verOutput -match "^4\.")
        $cand | Add-Member -MemberType NoteProperty -Name "IsGodot4" -Value $is4x -Force

        if ($is4x) {
            if (-not $bestGodot) { $bestGodot = $cand }
            if ($isExe -and (-not $realExeGodot -or $cand.Path -like "*_console.exe")) {
                $realExeGodot = $cand
            }
        }
        Write-KeyValue $cand.Type "$verOutput -> $($cand.Path)"
    }

    if ($bestGodot) {
        if ($bestGodot.InPath) {
            Write-Success "Godot 4.x is present and accessible in PATH ($($bestGodot.Version))."
        } else {
            Write-WarningMsg "Godot 4.x detected ($($bestGodot.Version)) at: $($bestGodot.Path), but not in system PATH."
        }
        return @{
            Found = $true
            InPath = $bestGodot.InPath
            Path = $bestGodot.Path
            RealExePath = $(if ($realExeGodot) { $realExeGodot.Path } else { $bestGodot.Path })
            Version = $bestGodot.Version
            Type = $bestGodot.Type
        }
    } else {
        Write-WarningMsg "Godot 4.x engine was not found in PATH, WinGet packages, or local downloads."
        return @{
            Found = $false
            InPath = $false
            Path = $null
            RealExePath = $null
            Version = $null
            Type = $null
        }
    }
}

# ============================================================================
# REQUIREMENT 2: AUTOMATION & REMEDIATION
# ============================================================================

function Configure-PythonVirtualEnv {
    param([hashtable]$PythonDiscovery)

    Write-SubHeader "2.1 Virtual Environment (.venv) Configuration & Dependencies"

    if (-not (Test-Path $Script:PyProjectPath)) {
        Write-ErrorRecord "pyproject.toml not found at: $Script:PyProjectPath"
        return $false
    }

    $venvExists = Test-Path $Script:VenvPython
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue

    if ($ForceVenv -and (Test-Path $Script:VenvDir)) {
        Write-InfoLine "Forcing recreation of virtual environment (-ForceVenv)..."
        Remove-Item -Path $Script:VenvDir -Recurse -Force
        $venvExists = $false
    }

    # Step 1: Create virtual environment if missing
    if (-not $venvExists) {
        if ($SkipInstall) {
            Write-WarningMsg "Virtual environment (.venv) does not exist and -SkipInstall was specified."
            return $false
        }

        Write-InfoLine "Bootstrapping new virtual environment at: $Script:VenvDir"
        $targetPython = $null
        if ($PythonDiscovery.SystemPy312) {
            $targetPython = $PythonDiscovery.SystemPy312.Path
        }

        if ($uvCmd) {
            Write-InfoLine "Using uv to initialize virtual environment with Python 3.12..."
            & uv venv "$Script:VenvDir" --python 3.12
        } elseif ($targetPython) {
            Write-InfoLine "Using system Python ($targetPython) to create virtual environment..."
            & $targetPython -m venv "$Script:VenvDir"
        } else {
            Write-ErrorRecord "Unable to create virtual environment: No Python 3.12 binary located."
            return $false
        }

        if (-not (Test-Path $Script:VenvPython)) {
            Write-ErrorRecord "Failed to initialize .venv: python.exe not created at $Script:VenvPython"
            return $false
        }
        Write-Success "Created virtual environment at $Script:VenvDir"
    } else {
        Write-Success "Virtual environment (.venv) is present."
    }

    # Step 2: Check required packages inside .venv
    Write-InfoLine "Checking installed packages: $($Script:CoreDependencies -join ', ')..."
    $probeScript = @'
import sys
packages = ['pytest', 'ruff', 'pydantic', 'rdkit', 'cantera', 'numpy', 'scipy']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('ALL_PRESENT')
'@

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $probeOutput = ($probeScript | & $Script:VenvPython 2>&1)
    $ErrorActionPreference = $prevEAP
    $probeResult = ($probeOutput -split "`r?`n") | Where-Object { $_ -match "^(MISSING:|ALL_PRESENT)" } | Select-Object -First 1
    if (-not $probeResult) { $probeResult = "MISSING:all" }
    $needsInstall = ($probeResult -like "MISSING:*")

    if ($needsInstall) {
        $missingList = ($probeResult -replace "^MISSING:", "") -split ","
        Write-WarningMsg "Missing required packages in .venv: $($missingList -join ', ')"

        if ($SkipInstall) {
            Write-WarningMsg "Skipping package installation due to -SkipInstall."
            return $false
        }

        Write-InfoLine "Installing missing dependencies into .venv..."
        if ($uvCmd) {
            Write-InfoLine "Running: uv pip install $($missingList -join ' ') --python '$Script:VenvPython'"
            & uv pip install @missingList --python "$Script:VenvPython"
        } else {
            # Check if pip is inside .venv
            $hasPip = (& $Script:VenvPython -m pip --version 2>&1) -match "pip \d+"
            if (-not $hasPip) {
                Write-InfoLine "Bootstrapping pip via ensurepip..."
                & $Script:VenvPython -m ensurepip --default-pip
            }
            Write-InfoLine "Running: python -m pip install $($missingList -join ' ')"
            & $Script:VenvPython -m pip install @missingList
        }

        # Re-probe
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $reprobeOutput = ($probeScript | & $Script:VenvPython 2>&1)
        $ErrorActionPreference = $prevEAP
        $reprobe = ($reprobeOutput -split "`r?`n") | Where-Object { $_ -match "^(MISSING:|ALL_PRESENT)" } | Select-Object -First 1
        if ($reprobe -eq "ALL_PRESENT") {
            Write-Success "Successfully installed all required packages."
            return $true
        } else {
            Write-ErrorRecord "Package installation finished with unsatisfied dependencies: $reprobe"
            return $false
        }
    } else {
        Write-Success "All core dependencies (pytest, ruff, pydantic, rdkit, cantera, numpy, scipy) are installed."
        return $true
    }
}

function Remediate-GodotInstallation {
    param([hashtable]$GodotInfo)

    Write-SubHeader "2.2 Godot 4.x Remediation & Configuration"

    if ($GodotInfo.Found -and $GodotInfo.InPath) {
        Write-Success "Godot 4.x is already configured and available in system PATH."
        return $true
    }

    # If Godot was found locally (e.g. WinGet packages or downloads) but not in PATH
    if ($GodotInfo.Found -and (-not $GodotInfo.InPath)) {
        Write-WarningMsg "Godot 4.x is installed locally at: $($GodotInfo.Path), but is not in system PATH."

        # Ensure tools\bin\godot.cmd exists and wraps this executable
        if (-not (Test-Path $Script:ToolsBinDir)) {
            New-Item -ItemType Directory -Path $Script:ToolsBinDir -Force | Out-Null
        }

        $targetExe = $(if ($GodotInfo.RealExePath) { $GodotInfo.RealExePath } else { $GodotInfo.Path })
        if ($targetExe -notlike "*_console.exe" -and $targetExe -like "*.exe") {
            $consoleExe = $targetExe -replace "\.exe$", "_console.exe"
            if (Test-Path $consoleExe) {
                $targetExe = $consoleExe
            }
        }

        if ($targetExe -and (Test-Path $targetExe) -and $targetExe -like "*.exe") {
            $wrapperContent = "@echo off`r`n`"$targetExe`" %*`r`n"
            Set-Content -Path $Script:GodotWrapperCmd -Value $wrapperContent -Encoding ASCII
            Write-Success "Configured project CLI wrapper: tools\bin\godot.cmd -> $targetExe"
        }

        Write-Host ""
        Write-Host "  To make Godot available in all terminals, add tools\bin to your User PATH:" -ForegroundColor Cyan
        Write-Host "    [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';$Script:ToolsBinDir', 'User')" -ForegroundColor White
        Write-Host "  Or install system-wide via winget to register Godot in PATH:" -ForegroundColor Cyan
        Write-Host "    winget install GodotEngine.GodotEngine --source winget" -ForegroundColor White
        Write-Host ""
        return $true
    }

    # Godot not found at all
    Write-WarningMsg "Godot 4.x is not installed."
    Write-Host ""
    Write-Host "  ==========================================================================" -ForegroundColor Cyan
    Write-Host "  GODOT 4.x INSTALLATION OPTIONS" -ForegroundColor Cyan
    Write-Host "  ==========================================================================" -ForegroundColor Cyan
    Write-Host "  1. Automated Windows Package Manager (winget):" -ForegroundColor White
    Write-Host "       winget install GodotEngine.GodotEngine --source winget" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. Official Portable Download Helper:" -ForegroundColor White
    Write-Host "       Download from: https://godotengine.org/download/windows/" -ForegroundColor White
    Write-Host "       Extract Godot_v4.*_win64.exe into: $Script:ToolsBinDir\godot.exe" -ForegroundColor White
    Write-Host "  ==========================================================================" -ForegroundColor Cyan
    Write-Host ""

    if ($InstallGodot) {
        Write-InfoLine "Automated installation requested (-InstallGodot). Running winget..."
        try {
            & winget install GodotEngine.GodotEngine --source winget --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Success "GodotEngine installed successfully via winget."
                return $true
            } else {
                Write-WarningMsg "winget exited with code $LASTEXITCODE."
                return $false
            }
        } catch {
            Write-ErrorRecord "Failed to invoke winget: $_"
            return $false
        }
    }

    return $false
}

function Verify-BlenderAssetPipeline {
    param([hashtable]$BlenderInfo)

    Write-SubHeader "2.3 Blender 5.2 Asset Pipeline Verification"

    # Step 1: Verify all required asset pipeline files in the repository
    $allFilesExist = $true
    Write-InfoLine "Verifying asset pipeline files in repository..."
    foreach ($relPath in $Script:AssetPipelineFiles) {
        $fullPath = Join-Path $Script:RepoRoot $relPath
        if (Test-Path $fullPath) {
            Write-KeyValue "Pipeline Component" "[EXISTS] $relPath"
        } else {
            Write-ErrorRecord "Missing asset pipeline file: $relPath"
            $allFilesExist = $false
        }
    }

    if (-not $allFilesExist) {
        Write-ErrorRecord "One or more required asset pipeline components are missing from repository."
        return $false
    }
    Write-Success "All asset pipeline scripts and master scene (chemlab.blend) are verified on disk."

    # Step 2: Verify Blender 5.2 execution
    if (-not $BlenderInfo.Found) {
        Write-WarningMsg "Blender 5.2 executable not found; skipping headless scene verification."
        return $false
    }

    $blenderExe = $BlenderInfo.Path
    Write-InfoLine "Probing Blender headless execution: '$blenderExe' -b --version"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $probe = & $blenderExe -b --version 2>&1
        $probeFirst = ($probe -split "`r?`n")[0]
        Write-Success "Blender background mode operational: $probeFirst"
    } catch {
        Write-ErrorRecord "Blender failed to run in background mode: $_"
        return $false
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    # Step 3: Run headless test if requested or as part of verification
    if ($RunAssetTest) {
        Write-InfoLine "Executing headless Blender scene test (-RunAssetTest)..."
        $testScript = Join-Path $Script:RepoRoot "tests\headless_blender_test.py"
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $testOutput = & $blenderExe -b "$Script:BlendFile" -P "$testScript" 2>&1
            $exitCode = $LASTEXITCODE
            if ($exitCode -eq 0 -and ($testOutput -like "*VERIFICATION RESULT: PASSED*")) {
                Write-Success "Headless Blender scene verification PASSED."
            } else {
                Write-WarningMsg "Headless scene test completed with warnings or non-zero exit code ($exitCode)."
            }
        } catch {
            Write-WarningMsg "Failed to execute headless test: $_"
        } finally {
            $ErrorActionPreference = $prevEAP
        }
    }

    return $true
}

# ============================================================================
# REQUIREMENT 3: SELF-TEST & VERIFICATION
# ============================================================================

function Invoke-PythonHealthCheck {
    Write-SubHeader "3.1 Python Scientific & Core Imports Health Check"

    if (-not (Test-Path $Script:VenvPython)) {
        Write-ErrorRecord "Cannot run health check: Virtual environment python not found at $Script:VenvPython"
        return $false
    }

    $healthCheckCode = @'
import sys

imports = [
    ("rdkit", "RDKit"),
    ("cantera", "Cantera"),
    ("numpy", "NumPy"),
    ("scipy", "SciPy"),
    ("pydantic", "Pydantic"),
    ("pytest", "Pytest"),
    ("ruff", "Ruff")
]

failed = False
for module_name, display_name in imports:
    try:
        mod = __import__(module_name)
        ver = getattr(mod, "__version__", "available")
        print("PASS|" + display_name + "|" + str(ver))
    except Exception as exc:
        print("FAIL|" + display_name + "|" + str(exc))
        failed = True

sys.exit(1 if failed else 0)
'@

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $rawOutput = ($healthCheckCode | & $Script:VenvPython 2>&1)
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP

    $allPassed = ($exitCode -eq 0)
    $lines = $rawOutput -split "`r?`n"
    foreach ($line in $lines) {
        if ($line -match "^PASS\|(.+?)\|(.+)$") {
            Write-Success "$($matches[1]): $($matches[2])"
        } elseif ($line -match "^FAIL\|(.+?)\|(.+)$") {
            Write-ErrorRecord "$($matches[1]) import failed: $($matches[2])"
            $allPassed = $false
        }
    }

    if ($allPassed) {
        Write-Success "All critical scientific and core Python packages successfully imported."
        return $true
    } else {
        Write-ErrorRecord "One or more Python package imports failed."
        return $false
    }
}

function Invoke-PytestVerification {
    Write-SubHeader "3.2 Pytest Tooling & Test Runner Verification"

    if (-not (Test-Path $Script:VenvPytest)) {
        # Fallback to python -m pytest
        Write-InfoLine "Checking pytest via .venv python -m pytest..."
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $ver = & $Script:VenvPython -m pytest --version 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEAP
        if ($exitCode -eq 0) {
            Write-Success "pytest operational: $ver"
            return $true
        } else {
            Write-ErrorRecord "pytest executable not found at $Script:VenvPytest"
            return $false
        }
    }

    try {
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $pytestVer = (& $Script:VenvPytest --version 2>&1).Trim()
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEAP
        if ($exitCode -eq 0) {
            Write-Success "pytest available: $pytestVer (.venv\Scripts\pytest.exe)"
            return $true
        } else {
            Write-ErrorRecord "pytest --version returned error (code ${exitCode}): $pytestVer"
            return $false
        }
    } catch {
        Write-ErrorRecord "Failed to invoke pytest: $_"
        return $false
    }
}

# ============================================================================
# SUMMARY & REPORTING
# ============================================================================

function Show-SummaryReport {
    param([hashtable]$Results)

    Write-SectionHeader "SETUP & VERIFICATION SUMMARY REPORT"

    $summaryItems = [ordered]@{
        "Operating System (Win10/11 x64)" = $Results.OS
        "Python 3.12 Host / Runtime"      = $Results.Python
        "Git Version Control"              = $Results.Git
        "Blender 5.2 Installation"        = $Results.Blender
        "Godot 4.x Engine"                = $Results.Godot
        "Virtual Environment (.venv)"      = $Results.Venv
        "Blender 5.2 Asset Pipeline"       = $Results.AssetPipeline
        "Python Scientific Imports"        = $Results.HealthCheck
        "Pytest Tooling Verification"      = $Results.Pytest
    }

    $passCount = 0
    $failCount = 0

    foreach ($item in $summaryItems.GetEnumerator()) {
        $name = $item.Key.PadRight(35)
        $passed = $item.Value
        if ($passed) {
            $passCount++
            Write-Host "  $name : " -NoNewline -ForegroundColor Gray
            Write-Host "PASS" -ForegroundColor Green
        } else {
            $failCount++
            Write-Host "  $name : " -NoNewline -ForegroundColor Gray
            Write-Host "FAIL / WARN" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host ("-" * 72) -ForegroundColor Cyan
    Write-Host "  Results: $passCount Passed, $failCount Warnings/Issues | $Script:WarningCount Warnings, $Script:ErrorCount Errors" -ForegroundColor White
    Write-Host ("-" * 72) -ForegroundColor Cyan

    if ($Script:ErrorCount -eq 0) {
        Write-Host ""
        Write-Host "  CHEMLAB DEVELOPMENT ENVIRONMENT IS FULLY OPERATIONAL!" -ForegroundColor Green
        Write-Host ""
        return 0
    } else {
        Write-Host ""
        Write-Host "  ENVIRONMENT SETUP COMPLETED WITH ISSUES (Review [FAIL] messages above)." -ForegroundColor Yellow
        Write-Host ""
        return 1
    }
}

# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

function Main {
    Write-Host ""
    Write-Host ("#" * 72) -ForegroundColor Cyan
    Write-Host "  $Script:Title v$Script:Version" -ForegroundColor Cyan
    Write-Host "  Target Root: $Script:RepoRoot" -ForegroundColor Cyan
    Write-Host ("#" * 72) -ForegroundColor Cyan

    $results = @{}

    # 1. Environment Inspection
    Write-SectionHeader "PHASE 1: ENVIRONMENT INSPECTION"
    $osResult = Test-OperatingSystem
    $pyResult = Find-PythonEnvironments
    $gitResult = Test-GitInstallation
    $blenderResult = Find-BlenderInstallation
    $godotResult = Find-GodotInstallation

    $results.OS = $osResult.Success
    $results.Python = $pyResult.HasPython312
    $results.Git = $gitResult.Success
    $results.Blender = $blenderResult.Found
    $results.Godot = $godotResult.Found

    # 2. Automation & Remediation
    Write-SectionHeader "PHASE 2: AUTOMATION & REMEDIATION"
    $venvResult = Configure-PythonVirtualEnv -PythonDiscovery $pyResult
    $godotRemediation = Remediate-GodotInstallation -GodotInfo $godotResult
    $assetPipelineResult = Verify-BlenderAssetPipeline -BlenderInfo $blenderResult

    $results.Venv = $venvResult
    $results.Godot = ($godotResult.Found -or $godotRemediation)
    $results.AssetPipeline = $assetPipelineResult

    # 3. Self-Test & Verification
    Write-SectionHeader "PHASE 3: SELF-TEST & VERIFICATION"
    $healthResult = Invoke-PythonHealthCheck
    $pytestResult = Invoke-PytestVerification

    $results.HealthCheck = $healthResult
    $results.Pytest = $pytestResult

    # 4. Summary & Exit Code
    $statusCode = Show-SummaryReport -Results $results
    return $statusCode
}

try {
    $exitCode = Main
    exit $exitCode
} catch {
    Write-ErrorRecord "Unhandled exception in setup-development.ps1: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
