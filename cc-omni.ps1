<#
.SYNOPSIS
  cc-omni - ChemLab Multi-Provider OmniRoute Launcher for Claude Code
.DESCRIPTION
  Connects multiple AI providers (Antigravity, AgentRouter, GitHub, Mistral, KiloCode, NVIDIA, OpenRouter)
  simultaneously to Claude Code via the local OmniRoute Gateway (127.0.0.1:20128).
  Strictly scoped to the local ChemLab project (C:\Users\Win11 Pro\Desktop\chemlab).
.EXAMPLE
  cc-omni auto
  cc-omni auto "Analysiere Aspirin-Synthese"
  cc-omni status
  cc-omni test
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode = "auto",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\Win11 Pro\Desktop\chemlab"
$OmniRoutePort = 20128
$OmniRouteUrl = "http://127.0.0.1:$OmniRoutePort"
$OmniRouteServerScript = "C:\Users\Win11 Pro\AppData\Roaming\npm\node_modules\omniroute\dist\server-ws.mjs"
$ClaudeExe = "C:\Users\Win11 Pro\.local\bin\claude.exe"

if (-not (Test-Path $ClaudeExe)) {
    $found = Get-Command claude -ErrorAction SilentlyContinue
    if ($found) {
        $ClaudeExe = $found.Source
    } else {
        Write-Error "[cc-omni] FEHLER: claude.exe konnte nicht gefunden werden."
        exit 1
    }
}

# 1. Enforce local ChemLab project directory
$CurrentDir = (Get-Location).Path
if ($CurrentDir -ne $ProjectRoot) {
    Write-Host "[cc-omni] Hinweis: cc-omni ist strikt lokal fuer chemlab konfiguriert." -ForegroundColor Yellow
    Write-Host "[cc-omni] Wechsle zu: $ProjectRoot" -ForegroundColor Cyan
    Set-Location $ProjectRoot
}

# 2. Check / Start OmniRoute daemon
function Test-OmniRouteHealth {
    try {
        $res = Invoke-WebRequest -Uri "$OmniRouteUrl/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return ($res.StatusCode -eq 200)
    } catch {
        return $false
    }
}

if (-not (Test-OmniRouteHealth)) {
    Write-Host "[cc-omni] Starte OmniRoute Server im Hintergrund auf Port $OmniRoutePort..." -ForegroundColor Yellow
    if (Test-Path $OmniRouteServerScript) {
        Start-Process -FilePath "node" -ArgumentList "`"$OmniRouteServerScript`"" -WindowStyle Hidden
    } else {
        Start-Process -FilePath "omniroute" -ArgumentList "serve" -WindowStyle Hidden
    }

    $retries = 15
    while ($retries -gt 0 -and -not (Test-OmniRouteHealth)) {
        Start-Sleep -Milliseconds 800
        $retries--
    }

    if (-not (Test-OmniRouteHealth)) {
        Write-Error "[cc-omni] FEHLER: OmniRoute Gateway konnte nicht gestartet werden."
        exit 1
    }
    Write-Host "[cc-omni] OmniRoute Server erfolgreich gestartet!" -ForegroundColor Green
}

# 3. Handle Special Subcommands (status, test)
if ($Mode -eq "status") {
    Write-Host "=== OMNIROUTE CHEMLAB STATUS ===" -ForegroundColor Cyan
    Write-Host "Gateway:   $OmniRouteUrl (ONLINE)" -ForegroundColor Green
    Write-Host "Projekt:   $ProjectRoot" -ForegroundColor Gray
    node "C:\Users\Win11 Pro\AppData\Roaming\npm\node_modules\omniroute\bin\omniroute.mjs" combo list
    exit 0
}

if ($Mode -eq "test") {
    Write-Host "=== TESTE MULTI-PROVIDER ROUTING (chemlab-auto) ===" -ForegroundColor Cyan
    $headers = @{
        "Authorization" = if ($env:ANTHROPIC_AUTH_TOKEN) { "Bearer $env:ANTHROPIC_AUTH_TOKEN" } else { "Bearer omniroute-no-auth" }
        "anthropic-version" = "2023-06-01"
    }
    1..4 | ForEach-Object {
        $n = $_
        $body = @{
            model = "chemlab-auto"
            max_tokens = 30
            messages = @(@{ role = "user"; content = "Test round $n. State model name only." })
        } | ConvertTo-Json
        try {
            $r = Invoke-RestMethod -Uri "$OmniRouteUrl/v1/messages" -Method Post -Headers $headers -ContentType "application/json" -Body $body -TimeoutSec 15
            [PSCustomObject]@{
                Turn = $n
                Model = $r.model
                Antwort = (($r.content | ForEach-Object { $_.text }) -join '').Trim()
            }
        } catch {
            [PSCustomObject]@{ Turn = $n; Model = "ERROR"; Antwort = $_.Exception.Message }
        }
    } | Format-Table -AutoSize
    exit 0
}

# 4. Resolve Target Model
$TargetModel = "chemlab-auto"
if ($Mode -and $Mode -ne "auto") {
    # If the user passed a different combo or flag as first argument
    if ($Mode -eq "p2c") {
        $TargetModel = "chemlab-p2c"
    } elseif ($Mode -eq "smart") {
        $TargetModel = "chemlab-omni-auto"
    } elseif ($Mode -eq "builtin-auto") {
        $TargetModel = "auto"
    } elseif ($Mode -eq "coding") {
        $TargetModel = "auto/coding"
    } elseif ($Mode.StartsWith("-")) {
        # First arg was a claude flag, retain default model
        $ClaudeArgs = @($Mode) + $ClaudeArgs
        $TargetModel = "chemlab-auto"
    } else {
        $TargetModel = $Mode
    }
}

# 5. Set Environment Variables for Claude Code
$env:ANTHROPIC_BASE_URL = $OmniRouteUrl
$env:ANTHROPIC_MODEL = $TargetModel
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = $TargetModel
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = $TargetModel
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $TargetModel
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "190000"

if (-not $env:ANTHROPIC_AUTH_TOKEN) {
    $env:ANTHROPIC_AUTH_TOKEN = "omniroute-no-auth"
}
$env:ANTHROPIC_API_KEY = $env:ANTHROPIC_AUTH_TOKEN

# 6. Display Dashboard Banner
Write-Host ""
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  CHEMLAB x OMNIROUTE MULTI-PROVIDER CLAUDE CODE BRIDGE                   " -ForegroundColor White
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Scope:        $ProjectRoot (Local Project Only)" -ForegroundColor Yellow
Write-Host "  Gateway:      $OmniRouteUrl (ONLINE)" -ForegroundColor Green
Write-Host "  Mode:         $Mode -> Model: $TargetModel" -ForegroundColor White
Write-Host "  Strategy:     Multi-Provider Concurrency (Round-Robin / P2C Failover)" -ForegroundColor Gray
Write-Host "  Providers:    Bluesminds (Credit) | NVIDIA NIM Free (Nemotron 30b/120b/550b)" -ForegroundColor DarkGray
Write-Host "                Antigravity (Gemini 3.8 Flash) | GitHub (GPT-4o/mini)" -ForegroundColor DarkGray
Write-Host "                Mistral (Codestral) | KiloCode (GPT-5.6/Gemini) | Groq (Qwen 3.8)" -ForegroundColor DarkGray
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

# 7. Execute Claude Code
if ($ClaudeArgs -and $ClaudeArgs.Count -gt 0) {
    & $ClaudeExe @ClaudeArgs
} else {
    & $ClaudeExe
}
