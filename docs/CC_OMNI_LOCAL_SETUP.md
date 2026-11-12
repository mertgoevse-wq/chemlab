# ChemLab x OmniRoute Multi-Provider Setup (`cc-omni`)

## Übersicht

Mit `cc-omni auto` wird **Claude Code** gestartet und über das lokale **OmniRoute Gateway** (`127.0.0.1:20128`) zeitgleich mit **mehreren KI-Providern** verbunden. Dadurch wird Claude Code parallel von verschiedenen KI-Modellen bedient – für Hauptaufgaben, Hintergrund-Subagents, parallele Tool-Aufrufe und Verifikation.

Dieses Setup ist **strikt lokal** auf das Projekt `C:\Users\Win11 Pro\Desktop\chemlab` beschränkt und berührt keine globalen Einstellungen oder andere Arbeitsbereiche.

---

## Architektur & Komponenten

```
                                  ┌───────────────────────────────┐
                                  │   Claude Code CLI / Session   │
                                  │   (Scoped to chemlab)         │
                                  └──────────────┬────────────────┘
                                                 │ Anthropic Messages API
                                                 ▼ (http://127.0.0.1:20128)
                        ┌──────────────────────────────────────────────────┐
                        │              OmniRoute Gateway Daemon            │
                        │               (Port 20128, ws/http)              │
                        │                                                  │
                        │  Combo: "chemlab-auto" (Round-Robin & Failover) │
                        │  Combo: "chemlab-p2c"  (Power of 2 Choices)      │
                        │  Combo: "chemlab-omni-auto" (Smart Dynamic)     │
                        └──────┬───────┬───────┬───────┬───────┬───────┬──┘
                               │       │       │       │       │       │
            ┌──────────────────┘       │       │       │       │       └──────────────────┐
            ▼                          ▼       ▼       ▼       ▼                          ▼
   ┌─────────────────┐        ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ ┌──────────┐
   │   Bluesminds    │        │ NVIDIA  │ │ Antigra-│ │ GitHub  │ │     Mistral     │ │ KiloCode │
   │ (Nemotron 30b / │        │   NIM   │ │  vity   │ │ (GPT-4o/│ │ (Codestral) /   │ │ (GPT-5.6/│
   │  Ultra 550b)    │        │  (Free) │ │ (Gemini)│ │  mini)  │ │   Groq (Qwen)   │ │  Gemini) │
   └─────────────────┘        └─────────┘ └─────────┘ └─────────┘ └─────────────────┘ └──────────┘
```

### Der aktive Multi-Provider Multi-Model Pool (12 Modelle)

1. **Bluesminds** (Nutzung des hinterlegten Guthabens):
   - `bluesminds/nvidia/nemotron-3.5-lightning-30b-a3b` (Ultra-schnelle Latenz: ~0.5s)
   - `bluesminds/nvidia/nemotron-3-ultra-550b-a55b` (550B Parameter Reasoning)
2. **NVIDIA NIM (Free)**:
   - `nvidia/nvidia/nemotron-3.5-lightning-30b-a3b`
   - `nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b`
3. **Antigravity**:
   - `antigravity/gemini-3.8-flash-high`
   - `antigravity/gemini-3.8-flash-medium`
4. **GitHub Copilot**:
   - `gh/gpt-4o`
   - `gh/gpt-4o-mini`
5. **Mistral**:
   - `mistral/codestral-latest` (Spezialisiert auf Code-Generierung)
6. **KiloCode**:
   - `kc/openai/gpt-5.6-sol`
   - `kc/google/gemini-3.7-flash`
7. **Groq**:
   - `groq/qwen/qwen3.8-27b` (Extrem schnelle Antworten: ~0.35s)

---

## Verfügbare Befehle

| Befehl | Beschreibung |
|---|---|
| `cc-omni auto` | Startet Claude Code mit dem Multi-Provider Pool `chemlab-auto` |
| `cc-omni auto "<prompt>"` | Startet Claude Code direkt mit einem initialen Prompt |
| `cc-omni p2c` | Nutzt *Power of Two Choices* Latenz-basiertes Load-Balancing |
| `cc-omni smart` | Nutzt OmniRoute's dynamische Auto-Klassifizierung |
| `cc-omni status` | Zeigt den Gateway-Status und alle aktiven Combos an |
| `cc-omni test` | Führt 4 sequentielle Test-Anfragen aus und zeigt die antwortenden Modelle |

---

## Warum ist das Setup strikt lokal?

1. **Projekt-Umgebungsvariablen (`.claude/settings.local.json`)**:
   - Die Konfiguration `ANTHROPIC_BASE_URL: http://127.0.0.1:20128` und `ANTHROPIC_MODEL: chemlab-auto` liegt in `.claude/settings.local.json`.
   - Diese Datei ist in `.gitignore` eingetragen und wird von Claude Code ausschließlich geladen, wenn eine Session im Ordner `chemlab` läuft.
   - Ihre globale Konfiguration `C:\Users\Win11 Pro\.claude\settings.json` bleibt unverändert.

2. **Launcher Guard (`cc-omni.ps1`)**:
   - Der Launcher überprüft beim Start das aktuelle Arbeitsverzeichnis. Falls der Befehl außerhalb aufgerufen wird, wechselt er automatisch in das ChemLab-Projektverzeichnis.

3. **Subagent-Mapping**:
   - `ANTHROPIC_DEFAULT_OPUS_MODEL = "chemlab-auto"`
   - `ANTHROPIC_DEFAULT_SONNET_MODEL = "chemlab-auto"`
   - `ANTHROPIC_DEFAULT_HAIKU_MODEL = "chemlab-auto"`
   Dadurch erhalten auch parallel geforkte Subagents und Workflows Zugriff auf den gesamten Multi-Provider-Pool.

---

## Verifikation & Tests

Der automatische Test kann jederzeit mit pytest ausgeführt werden:
```bash
.venv/Scripts/python.exe -m pytest tests/test_cc_omni_launcher.py -v
```
Ergebnis: **5/5 Tests bestanden** (Isolation, Launcher, Gateway Health, Status-Command, Live-Multi-Provider-Routing).
