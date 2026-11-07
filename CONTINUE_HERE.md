# CONTINUE HERE — Auftragsbrief für autonome Modell-/Agenten-Sitzungen

**Projekt:** Athanor Ascension (ehem. „ChemLab: Origins“ / „ChemLab: Athanor“ — Name ist FINAL, nicht wieder ändern)
**Zweck:** Jedes Modell, Programm oder Subagent, das an diesem Repository arbeitet, MUSS zuerst dieses Dokument lesen und der Pflichtlese-Liste in §2 folgen. Ohne diese Lektüre darf weder geplant noch implementiert werden.
**Stand:** 2026-11-05 · **Host:** Windows 11 Pro, Intel i5-1245U / Iris Xe, 16 GB RAM, Python venv unter `.venv`, Godot-Binary lokal unter `tools/bin/godot` bzw. `tools/bin/godot.cmd`.

---

## 0. Notfallregeln (non-negotiable)

1. **Offline-first.** Das Spiel ruft zur Laufzeit NIEMALS Google, LLMs oder ein Netzwerk an. Nano Banana, Veo, Flow Music und der Google Media Hub sind ausschließlich Build-Time-Werkzeuge, keine Projektbestandteile. Erwartete Asset-Pfade stehen in `game/data/media/manifest.json`.
2. **Ehrliche Zahlen.** Alle Simulationswerte beruhen auf realen physikalischen Konstanten (NIST/CRC-Enthalpien, Arrhenius, Bateman, Henderson-Hasselbalch, Paschen). Wo ein Modell empirisch ist, wird es im Code und UI als „empirisch“ markiert. Nie erfundene Werte ausgeben.
3. **Kein AI-Slop.** Kein bare `except:`, keine still geschluckten Fehler, keine anonymen Threads, 100 % Typsicherheit bei öffentlichen Funktionen. Gate: `tests/test_anti_ai_slop_audit.py`.
4. **Kein Blind-Overwrite.** Verifizierte Module nicht ohne funktionierenden Grund überschreiben. Legacy-Probleme zuerst dokumentieren, dann gezielt fixen.
5. **Statuswahrheit.** Nach jeder Arbeitsrunde `docs/ROADMAP.md` (LIVE/PARTIAL/BLUEPRINT) und die Statustabelle in `README.md` nachziehen. Falscher Status ins Readme ist ein Abbruchkriterium.
6. **Kein Netcode einbauen.** PvP/Online ist nur MITZUplanen (server-authoritativ, kein Client-Trust), nicht zu implementieren. Save-Formate und Companion-Datenmodelle bleiben kompatibel.
7. **Safety-Grenze.** Alle chemischen Anleitungen im Spiel bleiben erzählerisch eingepackt im fiktiven Simulator-Kontext mit GHS-Klassifikation, Ausrüstungspflicht und Auswirkungen. Details: `design/gdd/safety-framework.md`, `design/gdd/safety-system.md`.
8. **Kein Test-Gaming.** Assertions abschwächen oder Tests deaktivieren, um „grün“ zu wirken, ist verboten.

---

## 1. Einstieg in 30 Sekunden

Das Projekt teilt sich in drei Ebenen:

- **Python-Wissenschaftskern** (`src/chemlab/`, `chemlab_core/`, `simulation/`, `safety_simulation/`, `storage/`) — läuft getestet (pytest) und liefert echte Chemie-, Physik- und Safety-Berechnungen, offline.
- **Godot-4-Spiel** (`game/`) — die spielbare Vertical Slice mit Fenster-Loading, Menü, Laboratory-Hub, Genom-Archiv, Labor-Terminals (Accelerator, Fusor, Synthese, genomics/Analytical-Bench), Player-Vitals, Quests, Skills und Begleiter (Aetherkin).
- **Blender/DCC-Pipeline** (`chemlab.blend`, `chemlab_cinematic.blend`, `scripts/`) — Asset-Fabrik, die nur im Build über glTF/KTX2 zum Godot-Spiel beiträgt, niemals zur Laufzeit.

Das Spiel heißt **Athanor Ascension**. Der Start läuft über das Loading-Fenster (`res://scenes/loading/loading_screen.tscn`), der Spielbetrieb ist vollständig offline. Google-AI-Pro-Werkzeuge erzeugen ausschließlich Assets (Bilder, Videos, Musik) außerhalb des Spiels — zur Laufzeit ist keinerlei Cloud-Abhängigkeit erlaubt. Arbeit ohne den Pflichtlese-Kontext in §2 ist unzulässig.

---

## 2. Verbindliche Pflichtlese-Liste (genau in dieser Reihenfolge, VOR Arbeit)

| # | Datei | Warum Pflicht |
|---|-------|---------------|
| 1 | `README.md` | Aktuelle Ehrlichkeits-Tabelle: was LIVE / PARTIAL / geplant ist, plus alle Testbefehle |
| 2 | `docs/ROADMAP.md` | Arbeitsplan, offene Labore, Companion-Runtime, Switch- / Online-Absicht, Build-Time-Media-Regeln |
| 3 | `docs/audits/CHEMLAB_CURRENT_GROUND_TRUTH.md` | Basis: was VERIFIED_WORKING ist, Ruff-/mypy-Befund, Packaging-Lücke, Duplikatregister |
| 4 | `docs/CURRENT_STATE_AUDIT.md` | Wissenschaftliche Fundamente aller Reaktion/Thermo-/Beschleuniger-/Fusor-Subsysteme |
| 5 | `docs/GDD_CHEMLAB_ORIGINS.md` + `docs/GAME_DESIGN_DOCUMENT.md` | Visuelle Richtung (Iris Xe Budgets, Glasmaterial, Apparate), Gameplay-Loops |
| 6 | `design/gdd/game-concept.md` | Phase-B-Erweiterung: 12–15 Skill-Bäume, IP-Wirtschaft, Companion/Aetherkin, Genomik, Kernkraftwerk, Weltplan |
| 7 | `docs/STORY_AND_QUESTS.md` | 10-Level-Kampagne (Intern → Master Alchemist), NPCs, Quest-JSON-Schema |
| 8 | `docs/ARCHITECTURE.md` + `docs/BUILD_AND_RELEASE.md` | Modularchitektur, Konsolidierungsplan, Windows-/Steam-Build-Pipeline |
| 9 | `design/gdd/godot-architecture.md`, `design/gdd/asset-pipeline.md` | Godot-Szenen-/Renderer-Regeln und Blender→glTF-Pipeline |
| 10 | `docs/ASSET_PROMPTS.md` | Fertige Prompts für Nano Banana / Veo / Flow Music (Build-Time only) |
| 11 | `game/project.godot` | Autoload-Liste + `gl_compatibility`-Renderer — nicht ohne Zweck ändern |
| 12 | `game/scripts/quests/quest_manager.gd`, `game/scripts/core/player_vitals.gd`, `game/scripts/progression/skill_manager.gd` | Zentrale Gameplay-Subsysteme, die jedes neue Feature anbinden muss |
| 13 | `game/data/labs/labs.json`, `game/data/companions/species_database.json`, `game/data/genomics/`, `game/data/media/manifest.json` | Datenquellen für Labore, Begleiter, Genomik, Medien |
| 14 | `docs/integrations/DEPENDENCY_DECISIONS.md`, `docs/INTEGRATIONS_REGISTRY.md` | Welche externen Services/Abhängigkeiten sind zugelassen |

Wer ohne mindestens Punkte 1–4 gelesen zu haben arbeitet, wird zurückgestuft.

---

## 3. Aktuelles Projekt-Zeitalter: Was bereits funktioniert

### 3.1 Wissenschaftskern (Python), VERIFIED

- **Thermodynamik & Kinetik:** NIST/CRC-gestützte Enthalpie-, Entropie-, Gibbs- und Arrhenius-Berechnungen (`src/chemlab/simulation/cantera_engine.py` — rein Python, keine Cantera-Binärabhängigkeit).
- **Cheminformatik:** RDKit-basierte 3D-Konformer (ETKDGv3, UFF), bzw. SMILES→PDB/SDF (`src/chemlab/simulation/rdkit_engine.py`).
- **Side Reactions:** Untertemperatur-/Uebersink-/Catalyst-Fehler-Modell für Aspirin/Paracetamol/Acetanilid.
- **Gesamt-Synthesen:** Aspirin, Paracetamol, Coffein, Indigo, Benzocain mit echten Zustandsstücken (Reflux, Quenching, Filtration, Rekristallisation).
- **Safety:** Fume-Hood-Aerodynamik (ANSI/AIHA Z9.5), Thermal-Runaway (Semenov), GHS-Datenbank, Sicherheitsbeamte-Engine, Neutralisationsübungen.
- **Computervision:** MediaPipe-Hand-Tracker (21 Landmarks, Gesten pinch/grab/pour/…) + holistischer Pose-Tracker + 1-Euro-Filter — mit Maus-/Tastatur-Fallback, nicht Pflicht.
- **AI-Bridge:** Multi-Provider-Kette Omniroute (localhost:20128) → NVIDIA NIM → Gemini → **deterministischer Offline-Fallback** (kein Netz-Zugang in der Simulation).
- **Prozedurale Welt:** 11 globale Labor-Archetypen + No-Man's-Sky-Umweltmatrix (`src/chemlab/world/`, `src/chemlab/sandbox/`).
- **IPC & Mobile Server:** TCP-IP, Web/Mobile-View (Port 8766), Asset-Cache (SQLite).
- **Testlage:** **256 pytest-Tests grün** in `< 60 s`, Ruff bis auf dokumentierte Legacy-Fehler sauber, mypy-Strict bis auf 13 dokumentierte Annotationen.

### 3.2 Godot-4-Spiel („game/“), Stand LIVE/PARTIAL

| System | Status | Ort |
|---|---|---|
| Loading-Window (animiertes Siegel + Apparatur-Backdrop) | ✅ LIVE | `game/scenes/loading/` |
| Main Menu (Forschungsterminals, Settings) | ✅ LIVE | `game/scenes/main_menu/` |
| Laboratory Network Hub (15 Archetypen + 14 Anzüge) | ✅ LIVE | `game/scenes/laboratories/lab_hub.gd` + `game/data/labs/labs.json` |
| Genome-Archiv (Karyotyp→Locus→Base) | ✅ LIVE | `game/scenes/genomics/` |
| Mutationssimulation (Punktmutationen, mutagen spectra, VUS) | ✅ LIVE | `game/scripts/genomics/genome_simulation.gd` |
| Chromosomen-Dosis (Trisomie 21 / Monosomie X) | ✅ LIVE | same |
| Accelerator-Terminal (Lorentz, Rigidität, Cherenkov, Q-Werte) | ✅ LIVE | `game/scenes/laboratories/accelerator_lab.gd` |
| Fusor-Werkstatt (Bauliste, Paschen, Neutronen, Dosis) | ✅ LIVE | `game/scenes/laboratories/fusor_lab.gd` |
| Aspirin-Synthese (Stöchiometrie, Rückfluss, Quench/Rekristallisation, Assay) | ✅ LIVE | `game/scenes/laboratories/synthesis_lab.gd` |
| Analytical 3D-Bench (begehbare Bank) | 🟡 PARTIAL — Interaktion unvollständig | `game/scenes/laboratories/analytical_lab.tscn` |
| Player-Vitals (HP, Verletzungen, ppm·min, mSv) | ✅ LIVE | `game/scripts/core/player_vitals.gd` |
| Skill-Tracks & XP-Kurve | ✅ LIVE | `game/scripts/progression/skill_manager.gd` |
| Titration-Practicum | ✅ LIVE | `game/scenes/laboratories/titration_practicum.gd` |
| Aetherkin-Begleiter (26 Spezies, datengetrieben) | 🟡 Data LIVE, runtime PARTIAL | `game/data/companions/species_database.json`, `game/scripts/companions/` |
| Chemistry-Kern (256 Python-Tests) | ✅ LIVE (offline) | `src/chemlab/`, `chemlab_core/` |
| Steam/Release-Pipeline | ⬜ Geplant | `docs/BUILD_AND_RELEASE.md`, `tools/build-windows.ps1` |
| Nintendo Switch | ⬜ Ziel dokumentiert, kein Build-Target | `docs/ROADMAP.md` §6 |

Godot-Binary lokal: `tools/bin/godot` & `tools/bin/godot.cmd`. Blend-Dateien: `chemlab.blend`, `chemlab_cinematic.blend`. Screenshots in `docs/screenshots/`.

---

## 4. Was noch fehlt (das ist der konkrete Auftragsplan für weitere Agenten)

### 4.1 Prioritäten

1. **Consolidation** — 4 Chemie-Engines / 3 Reagenzien-Datenbanken / 2 Modell-Module in ein autoritatives `chemistry/`-Modul zusammenführen (Plan: `docs/ARCHITECTURE.md` §3.2), inklusive Packaging-Fix (pyproject).
2. **Zusätzliche Labore** — 9 von 15 Laboren fehlen noch (Elektrochemie, Zellkultur, Radiochemie, Materialien, Cleanroom, Pilot, Forensik, Orbital, Kryo). Jedes Labor braucht, in dieser Reihenfolge: Terminal-Scene mit physikalisch getriebener Interaktion + eine echte Unit-Operation + Ausfallmodi, danach Blender-Dressing.
3. **Genomik vertiefen** — mehr Genom-Datensätze (Mensch GRCh38 als Kern, dazu Modellorganismen laut `design/gdd/game-concept.md`), Genom-Browser im DNA-Look-und-Feel (Zoom wie die AC-Genom-Ansicht), Live-Simulation von Punktmutationen mit Genotyp→Phänotyp-Vorschau; Mutationen chemisch auslösbar.
4. **Aetherkin erweitern** — mehr Tiere/Wesen (Ziel 35–50), echte Runtime-Fähigkeiten mitである Skill-Einfluss, Portraits + 3D-Idle-Assets. Clan-Name „Aetherkin“ bleibt.
5. **Bau-Apparatur anleiten** — visuelle/interaktive, lehrhafte Bauanleitungen für physikalische Geräte (Fusor, Plasmareaktor, Schaltkreise) mit echtem Lerneffekt, im Spiel-Codex dokumentiert.
6. **Offline-KI-Modell für Chemie-Simulation** — deterministische offline Berechnung von Produkten, Reaktionswegen und Polymerz, keine Runtime-APIs. Basis: `src/chemlab/ai/reagent_computer.py`.
7. **Chemie-Erweiterung** — mehr Alkaloide, Terpene, Flavonoide, Alltagsstoffe (Küche, Bau, Kosmetik, Papier, Glas), mehrere Reaktionskatalog-Spezifikationen (`ORGANIC_REACTIONS_CATALOG_SPEC.md`, `INORGANIC_REACTIONS_CATALOG_SPEC.md`, `BIOCHEMICAL_PATHWAY_SIMULATION_SPEC.md`, `ELECTROCHEMISTRY_SPEC.md`, `PHOTOCHEMISTRY_SIMULATION_SPEC.md`).
8. **Accelerator-Labor mit „KI im Hintergrund“** — während der Ausführung echtes, offenes Offline-Modell, alle berechneten Werte real (keine illustrative Werte).
9. **Straßensystem (Punkte-Verlust) vertiefen** — HP-, Verletzungs-, Radio-/Chemie-Dosis-/Inkarzerations-Werte in `player_vitals.gd` an Gameplay-Die-Back koppeln; nie direkt XP/HP-Delta als Loot nutzen.
10. **Charaktererstellung & Story-Video** — Start-Screen: Namensfeld, Spezies-Auswahl, Berufshintergrund; danach Veo-Story-Video als Videosequenz (Build-Time, kein Runtime-Aufruf).
11. **Steam-ready** — Screenshots-Set (1840×720), Trailer (Veo), Steam-Page-Copy, Achieve-Plan, Build-Pipeline verifizieren (`tools/build-windows.ps1`).
12. **Nintendo Switch**: nur MITPLANEN — kompatibler Renderer bleibt, Gamepad-Parität, 720p UI-Skalierung, ≤ 3.2 GB RAM, ≤ 1 GB Texturen, keine Webcam-Abhängigkeit.
13. **Build-Time-Media (Google AI Pro via Playwright mit `cache/chrome-profile`)** — Bilder (Nano Banana), Story-/Trailer-Video (Veo), Ambient-Stage (Flow Music). Vermehrte Asset-Pfade in `game/data/media/manifest.json` integrieren, Prompts in `docs/ASSET_PROMPTS.md` pflegen.
14. **Duplikate-Dateien und Backups** — redundante Backups (`*.blend1`) und Dev-Artefakte aus dem Git-Track entfernen (`*.blend1` etc. in `.gitignore` aufnehmen), Build-Cache sauber halten.
15. **README-Mehrsprachigkeit** — `README.md` (EN) + `README.de.md` + `README.es.md` + `README.ja.md` synchron halten, echte Screenshots je Laborterminal einbauen.

### 4.2 Pflichtordre für die Nächste Sitzung („Was mache ich zuerst?“)

1. Baseline verifizieren (pytest + Godot-Headless-Tests + Smoke-Test) — nur bei grünem Status einsteigen.
2. Duplikate konsolidieren, dann nochmal alle Tests.
3. Kernarbeiten: Charakter-Erstellung, Veo-Story-Video, Genomik-Vertiefung.
4. Restliche 9 Labore nacheinander ausarbeiten und abrechnen.
5. Aetherkin-Erweiterung + Runtime-Fähigkeiten.
6. Performance/Art: Blender-Asset-Durchlauf, Rendering-Budgets halten, Performance-Report bei Bedarf aktualisieren.
7. READMEs sync + Screenshots.
8. Steam/Release-Pipeline verifizieren (NICHT pushen, nicht deployen).

---

## 5. Reproduzierbare Befehle (Verification Gate)

Vor dem Abhaken einer Aufgabe MUSS der Agent diese Checks in diesem lokalen Umfeld ausführen, und alle müssen grün sein (oder gezielt begründete Ausnahmen dokumentieren):

```bash
# 1) Python-Chemie-Kern (≥ 256 passed)
.venv/Scripts/python.exe -m pytest

# 2) Godot headless tests
tools/bin/godot.cmd --headless --path game --script res://scripts/smoke_test.gd
tools/bin/godot.cmd --headless --path game --script res://tests/test_genome_simulation.gd
tools/bin/godot.cmd --headless --path game --script res://tests/test_lab_physics.gd
tools/bin/godot.cmd --headless --path game --script res://tests/test_synthesis_chemistry.gd
tools/bin/godot.cmd --headless --path game --script res://tests/test_synthesis_flow.gd

# 3) Spiel — wirklich öffnen (nicht nur headless)
tools/bin/godot.cmd --path game

# 4) Lint / Typpr (optional)
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m mypy src/chemlab
```

Wer Aufgaben abhakt OHNE diese Checks in dem lokalen Umfeld ausgeführt zu haben, darf nicht „fertig“ behaupten. Tests dürfen nicht abgeschwächt, deaktiviert oder mit Zufallsgeneratoren gefüttert werden.

---

## 6. Liste der zu nutzenden Skills (parallel via Subagenten+)

Im Original-Claude-Code-Environment können installierte Skills parallel ausgeführt werden. In der Freebuff-/Codebuff-Sitzung, die dieses Dokument erzeugte, gibt es keinen Subagent-Dispatcher — das Fan-out ist daher explizit Auftrag für die nächste Sitzung.

Relevante claude-code-game-studios-Skills, die parallel laufen müssen, sobald wiederraum ist (lass zu, sofern der Folder existiert):

- `brainstorm`, `qa-plan`, `architecture-decision`, `design-review`, `code-review`, `consistency-check`, `content-audit`, `scope-check`, `tech-debt`
- `test-setup`, `test-helpers`, `test-flakiness`, `test-evidence-review`, `regression-suite`
- `security-audit`, `perf-profile`, `balance-check`, `asset-audit`, `release-checklist`
- `onboard`, `help`, `start`, `map-systems`, `vertical-slice`, `milestone-review`, `gate-check`
- `localize`, `skill-improve`, `skill-test`, `patch-notes`, `changelog`

Verteilung auf Subagenten:
- **Subagent A (Arbeitsweise):** `architecture-decision`, `design-review`, `code-review`, `security-audit`
- **Subagent B (Test/QA):** `test-setup`, `test-helpers`, `test-flakiness`, `qa-plan`, `regression-suite`
- **Subagent C (Ingenieurs-Layout):** `content-audit`, `consistency-check`, `scope-check`, `tech-debt`
- **Subagent D (Balance & Release):** `balance-check`, `asset-audit`, `release-checklist`, `perf-profile`
- **Subagent E (Lokalisierung):** `localize` — README- DE/EN/ES/JA sync, UI-Strings, Barcode/Screenshots-Templates
- **Subagent F (Art-Pipeline):** Blender-/Veo-/Nano-Banana-Prompts pflegen und Assets in `game/data/media/manifest.json` registrieren.

Die Skill-Ergebnisse sind ins Projekt einzubauen (Integration), nicht nur als Bericht abzulegen.

---

## 7. Orientierung: Wo weiterhin an gesetzt wird

**Gameplay-Verweise**
- `game/scripts/labs/` — alle offline physikalischen Modelle (Genomik, Reaktion, Synthese, Partikelphysik)
- `game/scripts/core/player_vitals.gd` — HP / Verletzungen / Exposition / Dosis
- `game/scripts/quests/` — Quest-Shell; Schema: `docs/STORY_AND_QUESTS.md`
- `game/scripts/progression/` — Skill-Tracks, Invention Points (IPs)
- `game/scripts/companions/` — Companion-System (Aetherkin)
- `game/scripts/genomics/` — Genom-Archiv (Karyotyp → Locus → Base); Daten aus `game/data/genomics/`

**Rendering-Verweise**
- `game/scenes/loading/` — Intro-Loader (animiertes Siegel + Backdrop). Ziel: mit Veo-Ouverture-Video-Asset und Blender-Dressing verstärken, ohne Compatibility-Renderer-Budget zu verletzen.
- `game/scenes/main_menu/` — Research-Terminal-Layout
- `game/scenes/laboratories/` — Lab-Hub (15 Archetypen, 14 Anzüge)
- `game/scenes/apparatus/` — per-Experiment-Geräte-Szenen (Bürette, Beaker, Rührer, Brenner, Erlenmeyer, Waage …)
- `game/scenes/genomics/` — 3D-Genom-Interface (kanonisch für Zoom-Visualität)

**Asset-Pipeline**
- `chemlab.blend` (analytische Notebook-Szene), `chemlab_cinematic.blend` (Cinematic-Setup) → glTF/KTX2-Pipeline laut `design/gdd/asset-pipeline.md`
- Materialparameter: IOR 1.474 (Borosilikat), Roughness 0.015, Beer-Lambert-Absorption, Meniskuskurve
- Performance-Budgets: `docs/PERFORMANCE_REPORT.md`

**Qualitäts-Gate**
- `tests/test_anti_ai_slop_audit.py`, `scripts/run_quality_gate.py`
- Für Godot-Screenshot-Captures: `game/tests/capture_ui.gd` (ohne Playwright, direkt über Godot)

---

## 8. Was du als Agent NICHT tun sollst

- Keine KI/Netz-Abhängigkeit zur Runtime bauen (Playwright nur externer Build-Helper, kein Bestandteil des Spieles).
- Keine Ergebnisse durch „kleingeschriebene“ Zahlen fälschen.
- „Fantastic Beasts“ / „Aetherkin“ nicht zurückbenennen; das Spiel heißt **Athanor Ascension** — FINAL.
- Keine Gameplay-Screenshots fälschen/„schön retuschierten“; echte Runtime-Captures ablegen.
- Keine Subagenten starten, die ohne die Pflichtlese-Liste arbeiten — jeder Sub-Agent-Prompt MUSS CONTINUE_HERE.md als ersten Zwangsschritt enthalten.
- Kein Deployment / Push / Release ohne explizite User-Anweisung.

---

## 9. Schnelleinstieg, wenn der Milestone-Status unbekannt ist

1. `pytest` + Godot-Headless-Tests laufbar? Dann in den Feature-Aufarbeitungseinstieg gehen.
2. Sonst: `docs/ARCHITECTURE.md`, Abschnitt „Consolidation“ umsetzen und Packaging fixen.
3. Sonst: Labor-Setout (`docs/ROADMAP.md` §2) ausbauen — 9 Terminals.
4. Sonst: Aetherkin-/Genomik-Erweiterung.
5. Sonst: Build-time Media (Nano Banana / Veo / Flow Music) via Playwright mit bestehendem Google-Profil.
6. Danach `docs/ROADMAP.md` + `README.md` verifiziert nachziehen und Commits sauber führen.

---

## 10. Sign-off

Erstellt von Buffy (Freebuff / Codebuff) am 2026-11-05 auf Basis von:
`docs/CURRENT_STATE_AUDIT.md`, `docs/audits/CHEMLAB_CURRENT_GROUND_TRUTH.md`, `docs/ROADMAP.md`, `README.md`, `design/gdd/game-concept.md`, `docs/STORY_AND_QUESTS.md`, `docs/GDD_CHEMLAB_ORIGINS.md`, `game/project.godot`, Testauswertung (256 pytest-Tests grün).

Änderung nur mit wissenschaftlich begründeten Daten-/Status-Nachweis.
