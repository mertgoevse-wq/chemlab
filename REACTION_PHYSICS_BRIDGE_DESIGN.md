# ChemLab Adaptive Background Music System Design

## Overview
Integration of Google Flow Music (via Google Media Bridge) for generative adaptive background music in ChemLab. The system provides seamless, reactive musical layers that respond to laboratory state, reaction progress, quest stages, location, and time of day.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ChemLab Audio Manager (GDScript)                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   State     │  │ Transition  │  │   Cache     │  │  Fallback   │    │
│  │  Machine    │  │   Engine    │  │  Manager    │  │ Generator   │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│         └────────────────┼────────────────┼────────────────┘            │
│                          ▼                ▼                             │
│              ┌─────────────────────────────────────────┐                │
│              │         Audio Bus Router                │                │
│              │  Master │ SFX │ Ambient │ UI │ Music    │                │
│              └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Google Media Bridge (Python)                         │
├─────────────────────────────────────────────────────────────────────────┤
│  GoogleService.MUSICLM / GoogleService.MUSIC_FX / GoogleService.FLOW    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │  Generate   │  │   Cache &   │  │  Quota      │                     │
│  │  Audio      │  │  Version    │  │  Fallback   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Music Stems / Layers

| Layer | Purpose | Duration | Loop Points | Crossfade |
|-------|---------|----------|-------------|-----------|
| **ambient_lab_hum** | Base laboratory ambience (HVAC, equipment hum) | 60-120s | Seamless | 2s |
| **synthesis_tension** | Building anticipation during active reactions | 30-60s | Beat-aligned | 1.5s |
| **discovery_triumph** | Quest completion, successful synthesis | 20-40s | Stinger | 1s |
| **danger_runaway** | Thermal runaway, overpressure, safety critical | 15-30s | Urgent loop | 0.5s |
| **sandbox_chill** | Free exploration, idle, creative mode | 60-120s | Seamless | 2s |
| **time_of_day_dusk** | Evening atmosphere modifier | 30-60s | Blend layer | 3s |
| **time_of_day_night** | Late night quiet laboratory | 30-60s | Blend layer | 3s |

## Emotional Arc Mapping

### Game State → Musical Parameters

| Game State | Primary Layer | Secondary Layers | Tempo | Key | Intensity |
|------------|--------------|------------------|-------|-----|-----------|
| **Idle / Menu** | sandbox_chill | ambient_lab_hum | 60-72 BPM | C major | 0.3 |
| **Lab Exploration** | ambient_lab_hum | sandbox_chill | 66 BPM | F major | 0.4 |
| **Reaction Setup** | synthesis_tension | ambient_lab_hum | 78 BPM | D minor | 0.5 |
| **Active Reaction** | synthesis_tension | + danger (if runaway) | 90-110 BPM | D minor / G minor | 0.6-0.9 |
| **Precipitation Forming** | synthesis_tension | + subtle discovery | 84 BPM | A minor | 0.6 |
| **Oscillating Reaction** | synthesis_tension | + rhythmic pulsing | 100 BPM | E minor | 0.7 |
| **Quest Objective Active** | synthesis_tension | + objective motif | 80 BPM | G major | 0.5 |
| **Quest Complete** | discovery_triumph | ambient_lab_hum | 92 BPM | C major | 0.8 |
| **Safety Warning** | danger_runaway | (ducks others) | 120 BPM | C minor | 1.0 |
| **Thermal Runaway** | danger_runaway | + dissonant elements | 140 BPM | F# minor | 1.0 |
| **Evening (18-22h)** | time_of_day_dusk | base layer | -2 semitones | - | 0.3 |
| **Night (22-6h)** | time_of_day_night | base layer | -4 semitones | - | 0.2 |

## Transition Rules

### State Transitions (with crossfade durations)

| From → To | Crossfade | Trigger Condition |
|-----------|-----------|-------------------|
| idle → exploration | 3.0s | Player enters lab scene |
| exploration → reaction_setup | 2.0s | Reagents selected, vessel created |
| reaction_setup → active_reaction | 1.5s | `mix_solutions()` called, reaction starts |
| active_reaction → precipitation | 1.0s | `precipitation_formed` signal |
| active_reaction → oscillating | 1.0s | Briggs-Rauscher/BZ conditions detected |
| active_reaction → thermal_runaway | 0.5s | Temperature > 80°C, pressure > 200 kPa |
| active_reaction → quest_objective | 1.5s | Quest objective becomes active |
| * → quest_complete | 1.0s | `quest_completed` signal |
| * → safety_warning | 0.5s | `safety_warning` / `temperature_alert` signal |
| active_reaction → exploration | 2.5s | Reaction complete, vessel idle > 10s |
| exploration → idle | 3.0s | Player returns to menu |

### Parameter Transitions (per-frame interpolation)

- **Volume**: Exponential curve (perceptual linear)
- **Pitch**: Semitone interpolation
- **Filter Cutoff**: Logarithmic (Hz)
- **Reverb Send**: Linear 0-1
- **Tempo**: Only on stem change (beat-aligned)

## Google Flow Music Integration

### API Usage (via google_media_bridge.py)

```python
# Generate a music stem
bridge = create_media_bridge(oauth_token="...")
response = bridge.generate_audio(
    prompt="Ambient laboratory soundscape, subtle HVAC hum, "
           "distant glassware clinks, 60 seconds, seamless loop, "
           "C major, 66 BPM, minimal, atmospheric",
    duration_seconds=60
)

# Generate tension layer
response = bridge.generate_audio(
    prompt="Building tension music for chemical synthesis, "
           "pulsing synthesizers, rising harmonic tension, "
           "D minor, 90 BPM, 45 seconds, seamless loop point at 32s",
    duration_seconds=45
)
```

### Prompt Templates per Stem

```python
STEM_PROMPTS = {
    "ambient_lab_hum": (
        "Ambient laboratory atmosphere, subtle HVAC ventilation hum, "
        "distant magnetic stirrer motor, occasional glassware contact, "
        "seamless loop, {key}, {bpm} BPM, {duration}s, "
        "minimal, atmospheric, non-intrusive, high fidelity"
    ),
    "synthesis_tension": (
        "Building musical tension for chemical synthesis process, "
        "pulsing electronic textures, rising harmonic progression, "
        "subtle rhythmic anticipation, {key}, {bpm} BPM, {duration}s, "
        "seamless loop, cinematic, scientific documentary style"
    ),
    "discovery_triumph": (
        "Triumphant discovery moment, warm major resolution, "
        "ascending melodic motif, sense of scientific achievement, "
        "{key}, {bpm} BPM, {duration}s, stinger ending, "
        "uplifting, cinematic, orchestral hybrid"
    ),
    "danger_runaway": (
        "Urgent danger music, thermal runaway emergency, "
        "dissonant clusters, accelerating rhythm, alarm-like pulses, "
        "{key}, {bpm} BPM, {duration}s, seamless loop, "
        "horror thriller tension, high intensity"
    ),
    "sandbox_chill": (
        "Relaxed creative laboratory exploration, "
        "gentle ambient electronic, soft melodic fragments, "
        "{key}, {bpm} BPM, {duration}s, seamless loop, "
        "lo-fi chill, contemplative, non-repetitive"
    ),
}
```

## Caching Strategy

### Local Cache Structure
```
user://music_cache/
├── manifest.json           # Index: stem_id -> {path, hash, version, params}
├── stems/
│   ├── ambient_lab_hum_v1_C_66bpm_60s.ogg
│   ├── synthesis_tension_v2_Dm_90bpm_45s.ogg
│   ├── discovery_triumph_v1_C_92bpm_20s.ogg
│   ├── danger_runaway_v1_Fsm_140bpm_15s.ogg
│   └── sandbox_chill_v1_F_66bpm_90s.ogg
└── metadata/
    └── *.json              # Generation parameters, timestamps
```

### Cache Policy
- **Max cache size**: 500 MB
- **TTL**: 30 days (auto-cleanup on launch)
- **Versioning**: Increment on prompt/parameter change
- **Preload**: Core stems (ambient, sandbox) at startup
- **Lazy load**: Tension, danger, triumph on first need

## Fallback: Procedural Music Generator

### Godot AudioStreamGenerator Implementation

When Google API unavailable (quota, offline, error):

```gdscript
class ProceduralMusicGenerator:
    # Generates stems using:
    # - Additive synthesis for pads
    # - FM synthesis for tension leads
    # - Noise + filtering for ambient textures
    # - Algorithmic composition (Markov chains for melody)
    # - Euclidean rhythms for pulse
```

### Procedural Parameters per Stem

| Stem | Algorithm | Key Parameters |
|------|-----------|----------------|
| ambient_lab_hum | Band-limited noise + slow LFO filter | 20-200 Hz, 0.1 Hz LFO |
| synthesis_tension | Euclidean rhythm (3,8) + FM lead | 90 BPM, D minor pentatonic |
| discovery_triumph | Arpeggiated major triad + pad | C major, 92 BPM |
| danger_runaway | Dissonant cluster + accelerating pulse | F# minor, 120→160 BPM |
| sandbox_chill | Generative ambient (Brian Eno style) | F major, 66 BPM, 7-note cycle |

## GDScript Audio Manager API

```gdscript
# Autoload: MusicManager

# High-level state control
MusicManager.set_game_state(GameState.ACTIVE_REACTION)
MusicManager.set_game_state(GameState.QUEST_COMPLETE)
MusicManager.set_game_state(GameState.IDLE)

# Reactive triggers (auto-managed via signals)
MusicManager.on_reaction_started(vessel_id, reaction_type)
MusicManager.on_precipitation_formed(vessel_id, precipitate_name)
MusicManager.on_thermal_runaway(vessel_id, temp_c)
MusicManager.on_quest_objective_started(quest_id, objective_id)
MusicManager.on_quest_completed(quest_id, xp, safety_score)
MusicManager.on_safety_warning(severity, message)

# Manual layer control (for cutscenes, menus)
MusicManager.set_layer_volume("ambient_lab_hum", 0.5)
MusicManager.crossfade_to_state(target_state, duration=2.0)

# Configuration
MusicManager.set_master_volume(0.8)
MusicManager.set_generative_enabled(true)  # Use Google Flow
MusicManager.set_cache_enabled(true)
```

## IPC Communication

### Godot → Python (Music Generation Requests)

```json
{
  "request_id": "music_gen_001",
  "command": "GENERATE_MUSIC_STEM",
  "payload": {
    "stem_type": "synthesis_tension",
    "parameters": {
      "key": "D_minor",
      "bpm": 90,
      "duration_seconds": 45,
      "loop_point_seconds": 32,
      "intensity": 0.7,
      "instruments": ["pulse_synth", "pad", "sub_bass"],
      "mood": "anticipation"
    },
    "cache_key": "synthesis_tension_Dm_90bpm_v2"
  }
}
```

### Python → Godot (Response)

```json
{
  "request_id": "music_gen_001",
  "status": "SUCCESS",
  "data": {
    "asset_url": "file:///user/music_cache/stems/synthesis_tension_v2_Dm_90bpm_45s.ogg",
    "duration_seconds": 45.0,
    "loop_start_seconds": 32.0,
    "loop_end_seconds": 45.0,
    "bpm": 90,
    "key": "D_minor",
    "generated_at": 1699999999.0
  }
}
```

## Integration Points

### Signals to Connect (in MusicManager._ready())

```gdscript
# From SimulationBridge
SimulationBridge.reaction_completed.connect(_on_reaction_completed)
SimulationBridge.vessel_state_changed.connect(_on_vessel_state_changed)
SimulationBridge.safety_warning.connect(_on_safety_warning)
SimulationBridge.temperature_alert.connect(_on_temperature_alert)
SimulationBridge.precipitation_formed.connect(_on_precipitation_formed)
SimulationBridge.ph_changed.connect(_on_ph_changed)

# From QuestManager
QuestManager.quest_started.connect(_on_quest_started)
QuestManager.objective_completed.connect(_on_objective_completed)
QuestManager.quest_completed.connect(_on_quest_completed)
QuestManager.safety_warning_triggered.connect(_on_quest_safety_warning)
QuestManager.fanfare_celebration_started.connect(_on_fanfare)

# From InputManager (time of day, location)
InputManager.tracker_connection_changed.connect(_on_tracker_changed)

# Time of day (system)
Time.time_changed.connect(_on_time_changed)  # Custom signal
```

## Testing Strategy

### Unit Tests
- State machine transitions
- Crossfade timing accuracy
- Cache hit/miss behavior
- Fallback generator output validation

### Integration Tests
- Full reaction sequence: idle → setup → active → precipitation → complete
- Quest chain: start → objectives → completion → fanfare
- Safety cascade: warning → critical → runaway → recovery
- Time of day transitions

### Audio Quality Tests
- Loop seamlessness (spectral analysis at loop points)
- Crossfade artifact detection
- Loudness consistency (LUFS)
- Frequency masking between layers

## Performance Budget

| Component | Target |
|-----------|--------|
| MusicManager process() | < 0.1 ms/frame |
| Stem crossfade (4 layers) | < 0.5 ms |
| Cache load (async) | < 50 ms |
| Google API request | < 5 s (background) |
| Procedural generation | < 200 ms/stem |
| Memory (cached stems) | < 200 MB |

## Future Extensions

1. **Adaptive Instrumentation**: Add/remove instruments based on reaction complexity
2. **Player Skill Adaptation**: Simpler music for novices, richer for experts
3. **Multiplayer Sync**: Shared music state across network sessions
4. **Accessibility**: Visual music representation, reduced intensity mode
5. **Live Coding**: Real-time parameter tweaking via dev console