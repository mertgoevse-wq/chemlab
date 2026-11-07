# Audio Design Document — ChemLab: Athanor Ascension

**Version:** 1.0 | **Date:** 2026-11-06 | **Target:** Godot 4.7.2, Intel Iris Xe (128 MB VRAM)

---

## 1. Current Audio State Assessment

### 1.1 Files Discovered
- **`game/audio/sfx_*.wav`** — 19 sound effects with `.import` counterparts
- **`game/default_bus_layout.tres`** — Audio bus layout with 4 buses
- **No runtime audio scripts found** in `game/scripts/` (no AudioManager, no AudioPlayer autoload)
- **No audio manifest** in `game/data/media/manifest.json` (only build-time assets: images/video)

### 1.2 Bus Architecture (from `default_bus_layout.tres`)
| Bus | Name   | Volume (dB) | Send To | Purpose               |
|-----|--------|-------------|---------|-----------------------|
| 0   | Master | 0.0         | —       | Master out            |
| 1   | SFX    | 0.0         | Master  | Sound effects         |
| 2   | Ambient| 0.0         | Master  | Ambient/background    |
| 3   | UI     | 0.0         | Master  | UI clicks/feedback    |

### 1.3 Audio in Godot Project
- **Renderer:** `gl_compatibility` (OpenGL 3.3 / WebGL 2)
- **Hardware target:** Dell Latitude 5530, Intel Iris Xe, 128 MB VRAM budget
- **Performance targets:** ≤65 draw calls, 0.67x internal resolution + FidelityFX CAS upscaling
- **Offline-first:** No runtime Google/AI calls; all audio is bundled/prepared at build time

### 1.4 Procedural vs Sampled
- **Currently sampled:** All 19 WAV files are pre-rendered assets
- **Procedural usage:** `AudioServer.set_bus_pitch_drop(pitch)` used in titration code (`addictive-gameplay-loops.md §3.1`) to vary pitch of `sfx_buret_drop.wav` from 0.8→1.2 as pH 7→9
- **Gap:** No procedural SFX generation system; no reverb/spatial effects configured

---

## 2. Procedural SFX Needs Per Gameplay System

### 2.1 Chemistry System
| Event | Current Asset | Need | Procedural/Sampled | Notes |
|-------|--------------|------|--------------------|-------|
| **Buret drop impact** | `sfx_buret_drop.wav` | Pitch automation (0.8→1.2 as pH rises) | **Procedural pitch shift** via `AudioServer.set_bus_pitch_drop()` | Already referenced in GDScript; bus routing needed |
| **Boiling / reflux** | `sfx_boiling_bubble.wav` | Loopable steam/vapor sound | **Procedural** (Godot AudioStreamNoise) | Low CPU; parameterize intensity |
| **Liquid pour** | `sfx_liquid_pour.wav` | Variable duration, streamed | **Streamed sample** | 1–5 s range; loop with variance |
| **Sizzle (frying/heating)** | `sfx_sizzle.wav` | Short burst on heat application | **Sampled** | 0.3–1.5 s |
| **Flame roar** | `sfx_flame_roaring.wav` | Dynamic intensity | **Procedural pitch + volume** | Map to reaction temperature |
| **Glassware slide/place** | `sfx_glass_slide.wav` | Placement feedback | **Sampled** | Short <0.3 s |
| **Valve click** | `sfx_valve_click.wav` | On/off actuation | **Sampled** | Sharp transient |
| **Safety alert** | `sfx_safety_alert.wav` | Hazard warnings | **Sampled + spatial** | Priority bus routing |
| **Quest discovery** | `sfx_quest_complete.wav` variant | "NEW ENTRY" Codex hook | **Sampled variant** | Unique sound per first synthesis |

### 2.2 Combat / Companion System
| Event | Need | Approach |
|-------|------|----------|
| **Companion impact** (hits, touches) | New category | **Procedural**: Light impact impulse with random pitch; low CPU |
| **Gas leak / fume hood airflow** | Ambient loop | **Procedural**: White noise + low-pass filter, parameterized by ventilation rate |
| **Reaction exothermic/endothermic** | Visual-audio cue | **Mixed**: Short sample + pitch envelope |

### 2.3 UI System
| Event | Current Asset | Need | Approach |
|-------|--------------|------|----------|
| **UI clicks** | `sfx_balance_beep.wav` | General UI feedback | **Keep sampled**; route to UI bus |
| **Level up** | `sfx_level_up.wav` | Progression milestone | **Keep sampled** |
| **Pinch/hover/ready** | `sfx_pinch_*.wav` | Input interactions | **Keep sampled**; UI bus |
| **Pinch grip** | `sfx_pinch_grip.wav` | Touch/gesture | **Keep sampled** |

---

## 3. Adaptive Music Design

### 3.1 Philosophy
- **Flow Music is build-time only** (Google Flow Music / Media Bridge) — no runtime procedural generation permitted (offline-first constraint)
- **In-game music must be score-based / layered** using Godot AudioStreams with runtime cross-fading
- **Intensity layers** tied to gameplay state (synthesis complexity, safety level, companion activity)

### 3.2 Proposed Structure: Three-Layer Adaptive Music
| Layer | When Active | Musical Role | Godot Implementation |
|-------|-------------|--------------|----------------------|
| **A Section** (base) | Default lab exploration | Drone / tonic, establishes key and tempo | `AudioPlayer` with `AudioStreamPlayer.seek()` for looping |
| **B Section** (development) | Active synthesis in progress | Arpeggiated motifs, increasing rhythm density | Cross-fade from A → B as synthesis stages activate |
| **C Section** (crisis) | Safety violation / thermal runaway / quest critical | Dissonant stabs, rising pitch, percussion hit | Trigger on `player_vitals.gd` hazard signals or `QuestManager` alerts |

### 3.3 Cross-Fade Logic (GDScript sketch)
```gdscript
# In an AudioPlayer node
var current_section = "A"
var target_section = "A"

func _process(delta):
    # Determine section from game state
    var new_section = determine_section()  # A/B/C based on synthesis progress, safety, etc.
    
    if new_section != current_section:
        target_section = new_section
        fade_to_section(target_section)

func fade_to_section(target: String, duration: float = 2.0) -> void:
    # Cross-fade between two AudioStream loops
    # Uses AudioMixers on each bus with volume automation
    pass
```

### 3.4 Intensity Mapping
| Game State | Section | Musical Cue |
|------------|---------|-------------|
| Calm lab, no active synth | A | Tonic drone, slow arpeggios |
| Multi-stage synthesis active (e.g., reflux + distillation) | B | Faster tempo, brighter intervals |
| Safety score < 70% / thermal runaway detected | C | Rising semitones, rhythmic pounding, stingers |
| Codex "NEW ENTRY" discovery | C → A | Brass hit, then resolve to tonic |

---

## 4. Audio Budget

| Metric | Estimate | Rationale |
|----------|----------|-----------|
| **Sample memory** | ~3 MB total | 19 WAVs @ 22.05 kHz, 16-bit, stereo (compressed via Godot OGG at export) |
| **Streaming** | 2–3 active streams max | Pour, boil, ambient airflow; others preloaded |
| **Procedural CPU** | < 1% Iris Xe | Pitch/volume automation only; no DSP graph |
| **Bus processing** | 4 buses × minimal FX | Master bus limiter only; no per-bus reverb to save VRAM |
| **Peak concurrent** | 5 sounds | 3 chemistry + 1 UI + 1 ambient; all others preloaded/queued |

### 4.1 Memory Constraints
- **Iris Xe 128 MB VRAM** is the hard limit (from `game-concept.md §3.11`)
- Audio assets must be exported as **OGG Vorbis** at Godot default quality (≈ 64 kbps stereo)
- Long loops (ambient) should be **single-channel** (mono) where possible
- Fallback to **procedural generation** if any asset slot is empty (per `ASSET_PROMPTS.md` fallback rules)

---

## 5. Mix Bus Architecture Recommendation

### 5.1 Recommended Layout (4 buses — already configured)
```
Master (bus 0)
  ├── SFX (bus 1) — all sound effects
  ├── Ambient (bus 2) — loops, gas flow, HVAC
  └── UI (bus 3) — clicks, beeps, level up
```

### 5.2 Additions Recommended
1. **Music bus** (new bus 5, send to Master at -∞ dB under normal conditions, bring up during C-section crises)
   - Separate from SFX so music can be ducked during critical sound effects
2. **Safety bus** (new bus 4, optional)
   - Route `sfx_safety_alert.wav` here for independent volume control
   - Allows "mute alerts" accessibility option without killing all SFX

### 5.3 Godot Implementation Notes
- Use `AudioServer.set_bus_volume_db(db)` per bus
- Use `AudioServer.set_bus_mix_bus(bus, target_bus)` for routing effects (reverb, compression) — keep minimal to save CPU
- **Accessibility:** Route all UI SFX to UI bus with independent volume control; safety alerts can be routed to master or a dedicated "alert" bus

---

## 6. Missing Audio Content List (Top 15 SFX Needed)

| # | SFX Name | Source Recommendation | Priority |
|---|----------|----------------------|----------|
| 1 | `sfx_buret_drop_pitched` | Pitch-automated version of existing `sfx_buret_drop.wav` (0.8→1.2 as pH 7→9) | **Critical** — core titration feedback |
| 2 | `sfx_boil_loop` | Ambient boiling/reflux loop (procedural noise + sine mod) | **Critical** — synthesis atmosphere |
| 3 | `sfx_safety_alert_stereo` | Spatialized safety warning; distinct from UI bus | **Critical** — hazard communication |
| 4 | `sfx_glass_place` | Glassware placement on bench | **High** — tactile feedback |
| 5 | `sfx_valve_turn` | Slow valve rotation (different from click) | **High** — apparatus control |
| 6 | `sfx_flame_low` | Low/medium flame loop | **High** — heating operations |
| 7 | `sfx_flame_high` | High flame / approaching runaway | **High** — thermal danger |
| 8 | `sfx_pour_steady` | Continuous pour stream | **High** — liquid handling |
| 9 | `sfx_pour_stop` | Pour completion cue | **High** — endpoint feedback |
| 10 | `sfx_bubble_single` | Individual bubble rise (for distillation/boiling) | **Medium** — refinement |
| 11 | `sfx_steam_vent` | Steam release valve | **Medium** — pressure events |
| 12 | `sfx_centrifuge_spin` | Centrifuge motor hum | **Medium** — separation operations |
| 13 | `sfx_nmr_sweep` | NMR field sweep sound | **Medium** — analytical feedback |
| 14 | `sfx_codex_unlock` | "NEW ENTRY" discovery cue | **Medium** — progression hook |
| 15 | `sfx_companion_ability` | Companion skill activation | **Low** — companion system |

**Source provenance:** All should be **procedural/programmatic** where possible (low VRAM) or **high-quality short samples** (≤0.5 s) for transients. Reference existing files in `game/audio/` as tonal/quality base.

---

## 7. Performance Considerations (Iris Xe CPU)

### 7.1 Procedural Audio CPU Cost
| Operation | Estimated CPU | Notes |
|-----------|--------------|-------|
| `AudioServer.set_bus_pitch_drop()` | Negligible | Single float parameter; negligible overhead |
| `AudioStreamPlayer.play()` (preloaded) | Negligible | Preloaded sounds ~0.01% CPU at idle |
| Brief sample play (≤1 s) | ~0.5% per instance | 19 sounds; most play <1% of time |
| Streaming loop (ambient) | ~1–2% | One long loop; keep stereo minimal |
| DSP effects (reverb/compression) | ~3–5% per bus | Avoid on Iris Xe; use bus-level sparingly |

### 7.2 Recommendations
- **Preload all SFX** at startup (`AudioLoader.preload(path)`) — avoid runtime `ResourceLoader.load()`
- **Use `set_volume_db()`** not `set_volume()` for fine control; avoids redundant DSP conversion
- **One-shot sounds** (clicks, impacts) → preloaded `AudioStreamPlayer2D` or `AudioStreamPlayer3D`
- **Streaming loops** (boil, ambient airflow) → `AudioStreamPlayer` with `stream` flag; set `loop=true`
- **Avoid spatial 3D audio** for most SFX (use 2D with panning); saves positional calculation
- **Safety:** Cap total simultaneous instances at 8; queue overflow → silent drop (not an error)
- **Test on target hardware:** Use Godot profiler (`Profile → Audio`) on a Dell Latitude 5530 / Iris Xe to verify ≤5% audio CPU

---

## 8. Implementation Roadmap (Next Session)

| # | Task | Owner | Dependencies |
|---|------|-------|--------------|
| 1 | Route all 19 existing SFX to `SFX` bus (bus 1) via `AudioStreamPlayer` nodes | Audio lead | Bus layout defined |
| 2 | Implement pitch automation for `sfx_buret_drop` via `AudioServer.set_bus_pitch_drop()` | GDScript dev | Titration code in `addictive-gameplay-loops.md` |
| 3 | Add music buses: A/B/C sections with cross-fade logic | Audio lead + Music composer | Game state flags (synthesis progress, safety) |
| 4 | Create procedural ambient loop (boil/vent) via `AudioStreamNoise` + filters | GDScript dev | Iris Xe CPU budget verified |
| 5 | Implement accessibility: UI bus independent volume; safety mute toggle | UI lead | Bus 3 + optional bus 4 |
| 6 | Profile audio CPU on target hardware (Iris Xe) | Performance lead | All audio implemented |
| 7 | Write fallback procedural generation for any missing asset slot | Audio lead | Build-time asset pipeline rules |

---

## References (in-project)
- `game/project.godot` — `[audio]` section, bus layout reference
- `game/default_bus_layout.tres` — current 4-bus layout
- `design/gdd/game-concept.md §3.8` — Flow Music & Atmospheric SFX concept
- `design/gdd/addictive-gameplay-loops.md §3.1` — titration pitch mapping, quest complete sound
- `design/gdd/safety-system.md §4` — safety warning audio
- `design/gdd/sandbox-mode.md §4` — stopper pop audio
- `design/gdd/skill-system.md §5` — forensic audio extraction
- `game/data/media/manifest.json` — build-time asset manifest (no audio slots)
- `game/scripts/core/player_vitals.gd` — hazard signals for music layer C
- `game/scripts/quests/quest_manager.gd` — quest completion / Codex triggers

---
*End of Audio Design Document*