# ChemLab – Interactive Virtual Chemistry Lab

## Übersicht
Ein hochwertiger, fotorealistischer 3D-Chemielabor in Echtzeit, gesteuert durch Echtzeit-Hand-Tracking mit einer normalen Webcam. Mischung und Reaktion von Substanzen werden live animiert, mit realistischen Oszillations-Uhren, spektakulären Schaumeffekten und eigenen Story-Modus-Quests.

> **„Es ist, als ob du einen echten Chemielabor vor dir hättest, greifst hinein und bringst die Teile ins Spiel!“**

## 🤖 Was erledigt dieses Repo?
- **3D-Labor** – erstellt und gerendert in Blender 5.2 für eine hochdetaillierte, physikalisch korrekte Darstellung der Borosilikatglaswaren und Chemikalien.
- **Echtzeit-Hand-Tracking** – nutzt MediaPipe Vision via Python für 21-knotige Hand-Positionen in 60 FPS und einen „Air-Guitar“-Interaktionskatalog (Greifen, Gießen, Schütteln).
- **Chemikalien-Echtzeit-Simulation** – präzise Werkzeug für Brutt-Rauscher-Oszillation, Säure-Base-Neutralisation, Schaumbildung, Fällung und Chemolumineszenz.
- **HTML/JS-Visualizer** – Live-Vorschau und Überwachung der Reaktionen, Erkundung der Modi (Story/Sandbox) und Echtzeit-Statistiken.
- **Multi-Agent-Studio** – 16 selbstständige Subagents von der Aufsicht entwickelten sowohl über Auto-Instaltion der `_claude_studio`-Abteilung als auch über `superpowers:brainstorming`.
- **Story-Modus** – ein Lineares Quest-System des Fortschritts vom Praktikanten bis zum Meister-Alchemisten.
- **Sandbox-Modus** – Freies Spiel ohne Levelgrenzen, mit 100+ natürlichen Substanzen, Vollständiger Unisex-Verfügbarkeit von Reagenzien, Reaktions- und Toxizitäts-GHS-Aufklebern.
- **Hardware-Optimierung** – Fokus auf den Intel Iris Xe der Dell Latitude 5530 für stabile 60 FPS.

## 🚀 Schnelle Übersicht

### 1️⃣ Deine erste chemische Mischung
- **Start:** Einrichten des Chemielabors (Sicherheitsbrille aufsetzen, Bunsenbrenner entflammen, Reagenzgläser aufbauen).
- **Tracking:** Stelle sicher, dass deine rechte Hand sichtbar ist und natürlich Gesten ausführst.
- **Greifen:** Ohne zu klicken – strecke Daumen- und Zeigefinger einfach aneinander, um Reagenzgläser zu greifen.
- **Mischen:** Drehe Handgelenk und gieße Flüssigkeit hinein (der Pfeil zeigt die Geschwindigkeitsvektorrichtung an).
- **Schütteln:** Schnelle Kreisbewegung, um zu schütteln.
- **Loslassen:** Strecke die Handfläche flach aus und stehe einen kleinen Schritt zurück.

### 2️⃣ Erste chemische Reaktionen
- **Säure-Base-Neutralisation:** Mische HCl mit NaOH – farbige Anzeige wechselt zu dunkelblau.
- **Oszillierende Iod-Uhr:** Brigg-Rauscher mit chemilumineszierenden Phasen. Siehst du Perioden, in denen die Flüssigkeit orangefarben → weiß → tiefblau umschlägt? Der blaue Punkt ist genau das Ergebnis von Iod-Stärke-Stabilisierung.
- **Elefanten-Zahn-Schäumung:** Peroxid + Spülvonmittel-Bibliothek (bestimmt durch pip Petrischalen)
- **Fällung:** Mische Bleinitrat + Kaliumiodid → goldfarbene gelbe Kristalle (Rieselfälle).
- **Lumineszenz:** Luminol + Oxidationsmittel (blau leuchtend).

### 3️⃣ Öffne das Story-Modus-Menü – Upgrade-Quest-Reihenfolge
| Level | Questziel | Freischaltung | Notiz |
|--------|---------|--------------|--------|
| **1** | Labortaufe und Indikator | Sicherheitsausrüstung und Grundreagenzien | Einführung in pH-Tests |
| **2** | Die Iod-Uhr (Kinetik) | Magnetrührstab und genau abgemessene Bechergläser | Messung der Zeit für Farbwechsel |
| **3** | Oszillierende BZ-Reaktion | Magnetrührstab und Spezial-Katalysatoren | Beobachtung der Farbwelle |
| **4** | Destillation | Destillierapparat | Extraktion von Ethanol und Wasser |
| **5** | Goldener Regen | Bunsenbrenner und Kreuzinstrument | Kristallisationsreaktion |
| **6** | Chemisches Leuchten | Luminol-Anfangsmischung und Basische Korrektur | Aufnahme von Lichtmuster |
| **7** | Thermische Sicherheitskontrolle | Sicherheitsabzug und Feuerlöscher | Thermische Handhabung |
| **8** | Katalytische Schaumbildung | Flaschenverschluss und Rührschnecke | Effektive Beschleunigung |
| **9** | Schnelle Oszillation | Zusatzmenge an Malonsäure | Verbesserung der Oszillationsfrequenz |
| **10** | Meister-Alchemist | Alle Gerätschaften, Lehrbuch und digitale Lehre | Volles Spiel ohne Einschränkungen |

### 4️⃣ Sandbox-Modus – Deine chemische Welt
- **100+ natürliche Reagenzien** – Alkohol, Säuren, Basen, Oxidationsmittel, Salze, Indikatoren, Reaktionen unter Kamera im Zapfluft herzen.
- **Beliebiger Reaktionszustand** – sofort, spontan, ohne Levelbarriere.
- **Zeitreihensteuerung** – verlangsamt, beschleunigt, time-lapse. Perfekt für das Experimentieren von Granaten, Säure-Base-Verhältnis oder neuer Katalysatoren.
- **Auto-Sicherheit** – Sicherer Feuerlöscher, Abzug und praktischer Schutzmechanismus.
- **Vollständiges Digitallabor** – Ohne die Laboreinrichtung für halbdurchsuchte Behälter.

### 5️⃣ Berufliche Simulationseffekte
| Effekt | Realistisches Modell | Echtzeit-Schlüsselwort |
|----------|-------------------|----------------------|
| **Oszillation** | 3-Phasen-Verhaltens-Pseudocode (Farbberechnung mit RGB-Schwellwert und in-situ-Schwindel-Puffer) | `oscillation_phase` | `oscillation_timer_s` |
| **Schaumbildung** | partikelbasierte Volumen-Zunahme + topfierendiges Gasblasen mit Decay-Flag | `bubble_rate`, `foam_volume_ml` |
| **Chemische Färbung** | Proportionale Mischen der RGB-Färbungssignaturen aller Reactanten | `color_rgb` pro Substanz | `turbidity` für Trübung |
| **Volumenänderung** | Speicherung von Reaktions- und Verdünnungseffekten. Durch mischen (Summe von Volumen) | `volume_ml` |
| **Stundenstunden** | Verringerung der End-Kabel-Effizienz des Lösungsstoff-Konzentrats mit der Zeit (Molekulare Bruchionen) | `reagent_moles` | `reagent_modes` |
| **Temperaturänderung** | Exotherme/Endotherme-Offset basierend auf den Enthalpien-Nährung und -Thermischen Effekten | `temperature_c` |
| **Fällung** | Fluoridations-/Fällungs-Effekt mit visueller Trübung | `turbidity` | `emission_glow` |

### 6️⃣ Hardware- und Softwarearchitektur
- **Engine:** Blender 5.2 EEVEE Next für 3D-Assets.
- **Computer Vision:** MediaPipe Hands (60 FPS, 21-Knoten-Skelett) + OpenCV für Live-Bildanalyse.
- **Netzwerk:** Socket-Bridge TCP (127.0.0.1:8765) für verzögerungsfreie Echtzeit-Synchronisation.
- **Plattform:** Windows 11 Pro, Python 3.12 (Tensor-Profil für i5-1240U), Intel Iris Xe Grafikkarte (80 Execution Units), 16 GB RAM.
- **Frontend:** Browser-basiertes HTML/JS Visualisierungspanel.
- **Multi-Agent:** 16 spezialisierte Unteragenten, die Themen von Reaktionen bis zu GPS-Tracking abdecken, und innerhalb von ~2 Minuten Feedback bereitstellen.

## 🛠 Wie man ChemLab auf einem Laptop läuft

### Voraussetzungen
```bash
# Verwende die mitgelieferte Python 3.12 aus der Umgebung
git clone https://github.com/Donchitos/Claude-Code-Game-Studios C:/Users/Win11 Pro/Desktop/game-studios
cd "/c/Users/Win11 Pro/Desktop/chemlab"
# Pip installiere Abhängigkeiten
"/c/Users/Win11 Pro/AppData/Local/Programs/Python/Python312/python.exe" -m pip install -e .[dev]
```

### Führe die Simulation aus
```bash
# Starter-Skript (Öffnet http://localhost:8089)
"/c/Users/Win11 Pro/AppData/Local/Programs/Python/Python312/python.exe" -m pip install fastapi websockets
# Nutzung: Server öffnet HTTP-Vorschau auf port 8089
"/c/Users/Win11 Pro/AppData/Local/Programs/Python/Python312/python.exe" -m http.server 8089 --bind 127.0.0.1 --directory "C:/Users/Win11 Pro/Desktop/chemlab"
# Öffne das interaktive visuelle Dashboard für das Labor
# (Dieses Fenster bleibt geöffnet und kann über das In-App-Browser-Fenster geöffnet werden)
```

### Spielen mit Story- und Sandbox-Modus
- **Story-Modus:** Folge den Anweisungen im Story-Modus-Panel (Quest-Antworten, Freischaltung der Ausrüstung).
- **Sandbox-Modus:** Kein Bedarf an Freischaltung – alles sofort verfügbar.
- **Web-Dashboard:** Die In-App-Browser-Fenster öffnen das interaktive Dashboard mit Monitor-Oberfläche.

## 📰 Lizenz
MIT Lizenz – Veröffentlicht unter der MIT Lizenz. Frei für kommerzielle und private Verwendung.

## 📚 Referenzen
- **Google MediaPipe Vision:** https://developers.google.com/mediapipe
- **Blender**: https://www.blender.org
- **Python 3.12 Optimierung für i5-1240U:** gehaltener Server auf /cpu-benchmarks
- **Python-Paketmanager:** pip/setuptools
- **GitHub-Dokumentation:** https://docs.github.com
- **Claude Code Multi-Agent Engine:** https://github.com/Donchitos/Claude-Code-Game-Studios

## 👥 Beiträge
Wir begrüßen Open-Source-Mitwirkende! Öffne einfach ein Problem oder PR und erstelle eine Funktionsliste.