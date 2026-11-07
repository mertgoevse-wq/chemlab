#!/usr/bin/env python3
"""
Flow Music / Suno / Audio Generation Pipeline for ChemLab

Generates ambient lab music, reaction sounds, and UI sounds
using AI music generation (Flow Music, Suno, or similar).

Requirements:
- Suno API key or similar music generation service
- Or use manual generation workflow with prompts

Usage:
    python flow_music_generate.py --mode ambient
    python flow_music_generate.py --mode reactions
    python flow_music_generate.py --mode ui
    python flow_music_generate.py --mode all
    python flow_music_generate.py --dry-run  # Show prompts only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "game" / "data" / "media" / "manifest.json"

# ─── Audio Prompt Library ────────────────────────────────────────────────────

AMBIENT_TRACKS = [
    {
        "id": "ambient_analytical_lab",
        "name": "Analytical Lab Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: analytical chemistry lab. "
            "Continuous low hum of HPLC pumps (60Hz fundamental with harmonics), "
            "periodic autosampler needle clicks (every 30s), "
            "nitrogen gas cylinder regulator hiss, "
            "distant fume hood airflow whoosh, "
            "occasional keyboard typing from data station, "
            "subtle epoxy floor footstep reverb. "
            "4500K color temperature equivalent in sound - clean, precise, clinical. "
            "Seamless loop, 2 minutes, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/ambient/ambient_analytical_lab.wav",
    },
    {
        "id": "ambient_synthesis_lab",
        "name": "Synthesis Lab Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: organic synthesis lab. "
            "Rotary evaporator motor whine (varying pitch with vacuum), "
            "magnetic stirrer rhythmic clicking (adjustable RPM), "
            "condenser water flow gurgle, "
            "fume hood sash movement (metal-on-metal), "
            "Schlenk line vacuum pump cyclic thrum, "
            "glass joint grinding (occasional), "
            "solvent cabinet door soft close. "
            "Warm, organic texture - 5500K equivalent. "
            "Seamless loop, 2 minutes, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/ambient/ambient_synthesis_lab.wav",
    },
    {
        "id": "ambient_radiochemistry_hotcell",
        "name": "Radiochemistry Hot Cell Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: radiochemistry hot cell. "
            "Lead glass window muffles external sound. "
            "Remote manipulator servo whines (precision movement), "
            "gamma survey meter steady click rate (background radiation), "
            "shielded vial transfer clunk (mechanical), "
            "HVAC filtered airflow (constant), "
            "occasional lead brick placement thud. "
            "Cold, heavy, shielded feeling - blue-green equivalent. "
            "Seamless loop, 2 minutes, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/ambient/ambient_radiochemistry_hotcell.wav",
    },
    {
        "id": "ambient_accelerator_hall",
        "name": "Accelerator Hall Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: particle accelerator hall. "
            "Magnet power supply harmonic drone (multiples of 50/60Hz), "
            "cryogenic compressor cycle (helium, 1.4K), "
            "beam diagnostics: BPM button clicks, wire scanner swoosh, "
            "interlock system relay clacks (periodic), "
            "concrete tunnel reverb (long decay, 3s RT60), "
            "distant klystron waveguide hum. "
            "Industrial, vast, cold - 4000K equivalent. "
            "Seamless loop, 3 minutes, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 180,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/ambient/ambient_accelerator_hall.wav",
    },
    {
        "id": "ambient_fusor_workshop",
        "name": "Fusor Workshop Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: fusor/fusion workshop. "
            "Turbomolecular pump ramp-up/down (frequency sweep 0-50kHz), "
            "high voltage capacitor bank charging whine (rising pitch), "
            "deuterium regulator solenoid click, "
            "neutron detector pulses (sporadic, Poisson distributed), "
            "ballast resistor thermal expansion ticks, "
            "viewport cooling fan. "
            "High tension, electric potential energy. "
            "Seamless loop, 2 minutes, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/ambient/ambient_fusor_workshop.wav",
    },
    {
        "id": "ambient_genomics_lab",
        "name": "Genomics Lab Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: genomics/sequencing lab. "
            "Thermal cycler Peltier whine (ramp up/down 95°C-4°C), "
            "gel rig buffer circulation pump, "
            "sequencer fluidics: peristaltic pumps, valve manifold clicks, "
            "flow cell loading mechanism, "
            "cluster generation laser (faint high-pitched), "
            "cleanroom HVAC (HEPA filtered, consistent). "
            "Ultra-clean, precise, cool - 6500K equivalent. "
            "Seamless loop, 2 minutes, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/ambient/ambient_genomics_lab.wav",
    },
    {
        "id": "ambient_cleanroom_iso5",
        "name": "Cleanroom ISO 5 Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: ISO 5 cleanroom. "
            "Laminar flow ceiling: uniform white noise (filtered), "
            "bunny suit fabric rustle (minimal movement), "
            "wafer handling robot: linear motor glide, vacuum end-effector engage, "
            "particle counter sample pulse (every 60s), "
            "photolithography stepper: stage move, shutter, exposure flash (muffled), "
            "yellow safe light ballast hum. "
            "Sterile, controlled, silent-floor. "
            "Seamless loop, 2 minutes, -22 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -22,
        "output": "game/assets/audio/ambient/ambient_cleanroom_iso5.wav",
    },
    {
        "id": "ambient_pilot_plant",
        "name": "Pilot Plant Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: chemical pilot plant. "
            "Large pump cavitation rumble (controlled), "
            "heat exchanger steam hammer (periodic), "
            "relief valve venting (safety, scheduled), "
            "PLC cabinet relay logic clicking, "
            "control room: operator voice (muffled, intercom), "
            "column liquid level gurgle, "
            "steam trace line expansion creaks. "
            "Industrial scale, gritty, warm. "
            "Seamless loop, 3 minutes, -14 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 180,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -14,
        "output": "game/assets/audio/ambient/ambient_pilot_plant.wav",
    },
    {
        "id": "ambient_microgravity_lab",
        "name": "Microgravity Lab Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: orbital microgravity lab. "
            "Life support: CO2 scrubber cycle, O2 regulator hiss, "
            "thermal control fluid pump (silent in vacuum, structure-borne), "
            "experiment rack: capacitor microphonic hum, "
            "free-floating object gentle impacts (Velcro, tape), "
            "astronaut breathing in comms loop (subtle), "
            "Earth limb view: no sound but implied vastness. "
            "Isolated, weightless, quiet. "
            "Seamless loop, 2 minutes, -24 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -24,
        "output": "game/assets/audio/ambient/ambient_microgravity_lab.wav",
    },
    {
        "id": "ambient_cryogenic_lab",
        "name": "Cryogenic Lab Ambience",
        "category": "ambient",
        "prompt": (
            "Ambient laboratory soundscape: cryogenic laboratory. "
            "Dilution refrigerator: 1K pot pulse tube (1.4Hz thump), "
            "mixing chamber: He-3/He-4 circulation (silent), "
            "LN2 dewar: boil-off hiss, phase separator burble, "
            "superconducting magnet: persistent mode switch (occasional click), "
            "thermal contraction ticks (metal, random), "
            "vacuum pump: roots blower whine. "
            "Extreme cold, quantum silence. "
            "Seamless loop, 2 minutes, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "music, melody, rhythm, beats, voices, speech, alarms, sudden loud sounds, compression artifacts",
        "duration_sec": 120,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/ambient/ambient_cryogenic_lab.wav",
    },
    {
        "id": "ambient_main_menu",
        "name": "Main Menu Theme",
        "category": "ambient",
        "prompt": (
            "Musical theme: Athanor Ascension main menu. "
            "Minimalist ambient electronic. "
            "Fundamental: low C (32.7Hz) sub-bass felt not heard. "
            "Harmonics: glass armonica tones (bowed glass rods), "
            "periodic: struck tuning fork (512Hz) decaying, "
            "texture: granular synthesis of lab sounds (bubble, click, hiss), "
            "progression: none - static harmony, evolving timbre. "
            "Key: C minor (relative Eb major), no third - ambiguous. "
            "Length: 60s seamless loop, -14 LUFS, 48kHz/24-bit WAV + OGG."
        ),
        "negative": "drums, percussion, rhythm section, vocals, lyrics, melody, chord progression, compression artifacts",
        "duration_sec": 60,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -14,
        "output": "game/assets/audio/ambient/ambient_main_menu.wav",
    },
    {
        "id": "ambient_loading_screen",
        "name": "Loading Screen Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: loading screen. "
            "Slow attack pad: additive synthesis (odd harmonics only), "
            "modulation: very slow LFO (0.01Hz) on filter cutoff, "
            "event: each asset load triggers soft bell tone (pentatonic), "
            "progress: subtle pitch rise (quarter tone per 25%), "
            "completion: major chord resolution (C-Eb-G-Bb), quick decay. "
            "Adaptive length: 8-30s, seamless if looped, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 30,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/ambient/ambient_loading_screen.wav",
    },
    {
        "id": "ambient_character_select",
        "name": "Character Select Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: character creation screen. "
            "Four variations (one per species), crossfade on selection. "
            "Human: warm piano + subtle strings (hopeful). "
            "Sylvan: wooden flute + forest ambience (organic). "
            "Cinder-kin: low synth drone + metallic percussion (intense). "
            "Deep-kin: hydrophones + sub-bass + filtered noise (immersive). "
            "Each: 30s loop, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 30,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/ambient/ambient_character_select.wav",
    },
    {
        "id": "ambient_quest_hub",
        "name": "Quest Hub Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: quest board / hub area. "
            "Gentle arpeggiator: electric piano (Rhodes), "
            "chord progression: i - VI - III - VII (Cm - Ab - Eb - Bb), "
            "tempo: 66 BPM, rubato, "
            "notification chime layer: new quest available (pentatonic), "
            "completion fanfare: brief (I - IV - I), "
            "loop: 45s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 45,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/ambient/ambient_quest_hub.wav",
    },
    {
        "id": "ambient_skill_tree",
        "name": "Skill Tree Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: skill tree / progression screen. "
            "Modular synth sequence: 8-step Euclidean rhythm (3,8), "
            "notes: pentatonic minor, quantized, "
            "each skill unlock: adds voice to chord (additive harmony), "
            "mastery tier: filter opens, timbre brightens, "
            "reset/prestige: grand piano chord, long decay. "
            "Loop: 60s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 60,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/ambient/ambient_skill_tree.wav",
    },
    {
        "id": "ambient_codex_reading",
        "name": "Codex/Encyclopedia Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: reading codex entries. "
            "Sparse: solo cello (low register), "
            "occasional: page turn Foley (paper, digital), "
            "cross-reference link: soft harp harmonic, "
            "diagram view: adds subtle sine wave drone, "
            "video embed: pauses music, plays video audio. "
            "Loop: 90s, -22 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 90,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -22,
        "output": "game/assets/audio/ambient/ambient_codex_reading.wav",
    },
    {
        "id": "ambient_safety_incident",
        "name": "Safety Incident Tension",
        "category": "ambient",
        "prompt": (
            "Musical tension: safety incident / near miss. "
            "Dissonant cluster: minor seconds, tritones, "
            "heartbeat: sub-bass kick (60 BPM), "
            "escalation: density increases, register rises, "
            "resolution: consonant major chord (safety restored), "
            "all-clear: single bell tone, long decay. "
            "Adaptive: 10-60s based on severity, -12 LUFS peak, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, fast rhythm, vocals, lyrics, melody, compression artifacts",
        "duration_sec": 30,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -12,
        "output": "game/assets/audio/ambient/ambient_safety_incident.wav",
    },
    {
        "id": "ambient_experiment_success",
        "name": "Experiment Success Fanfare",
        "category": "ambient",
        "prompt": (
            "Musical reward: experiment completed / milestone. "
            "Ascending major arpeggio: C-E-G-C-E-G (2 octaves), "
            "timbre: celesta + glockenspiel + sine, "
            "harmonics bloom: reverb tail 8s, "
            "sub-bass: fundamental reinforces, "
            "variations: 3 (minor, major, Lydian), randomized. "
            "Duration: 4s, -10 LUFS, 48kHz/24-bit WAV + OGG."
        ),
        "negative": "drums, percussion, vocals, lyrics, dissonance, compression artifacts",
        "duration_sec": 4,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -10,
        "output": "game/assets/audio/ambient/ambient_experiment_success.wav",
    },
    {
        "id": "ambient_level_up",
        "name": "Level Up / Prestige",
        "category": "ambient",
        "prompt": (
            "Musical reward: skill level up / prestige. "
            "Whoosh up (white noise sweep 20Hz-20kHz, 0.5s), "
            "impact: orchestral hit (tam-tam + low brass), "
            "shimmer: harmonic series glissando up, "
            "resolve: major 9 chord (C-E-G-B-D), "
            "tail: 6s reverb, "
            "prestige variant: adds choir pad (aaa). "
            "Duration: 5s, -8 LUFS peak, 48kHz/24-bit WAV + OGG."
        ),
        "negative": "drums, percussion (except tam-tam), vocals, lyrics, dissonance, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -8,
        "output": "game/assets/audio/ambient/ambient_level_up.wav",
    },
    {
        "id": "ambient_discovery_moment",
        "name": "Scientific Discovery Moment",
        "category": "ambient",
        "prompt": (
            "Musical moment: novel compound synthesized / paper published. "
            "Sparse: solo violin harmonics (ascending), "
            "cluster: dense chord builds (micropolyphony), "
            "breakthrough: sudden silence (0.5s), "
            "revelation: pure sine wave fundamental + perfect fifth, "
            "decay: 10s, fading to ambient lab sound. "
            "Duration: 8s, -14 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, vocals, lyrics, rhythm, compression artifacts",
        "duration_sec": 8,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -14,
        "output": "game/assets/audio/ambient/ambient_discovery_moment.wav",
    },
    {
        "id": "ambient_credits",
        "name": "Credits Theme",
        "category": "ambient",
        "prompt": (
            "Musical theme: end credits. "
            "Full arrangement of main theme: "
            "piano intro (main_menu motif), "
            "strings enter (slow, sustained), "
            "woodwinds: counter-melody, "
            "brass: chordal support (no melody), "
            "percussion: crotales, tam-tam rolls, "
            "finale: full ensemble, major resolution, "
            "fade to silence over 30s. "
            "Duration: 3 minutes, -14 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, drum kit, fast rhythm, vocals, lyrics, compression artifacts",
        "duration_sec": 180,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -14,
        "output": "game/assets/audio/ambient/ambient_credits.wav",
    },
    {
        "id": "ambient_easter_egg",
        "name": "Easter Egg / Secret Discovery",
        "category": "ambient",
        "prompt": (
            "Musical sting: hidden content found. "
            "Retro: 8-bit chiptune arpeggio (NES-style), "
            "reference: 'Chemlab' spelled in solfege (Do-Re-Mi...), "
            "glitch: bitcrush decay, "
            "resolve: warm major chord, analog synth. "
            "Duration: 3s, -12 LUFS, 48kHz/24-bit WAV + OGG."
        ),
        "negative": "drums, percussion, vocals, lyrics, modern production, compression artifacts",
        "duration_sec": 3,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -12,
        "output": "game/assets/audio/ambient/ambient_easter_egg.wav",
    },
    {
        "id": "ambient_pause_menu",
        "name": "Pause Menu Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: pause menu. "
            "Low-pass filtered version of current area ambience, "
            "added: gentle sine wave drone (tonic), "
            "menu navigation: soft click (wood block), "
            "selection: soft chime (pentatonic), "
            "resume: crossfade out over 1s. "
            "Adaptive length, -24 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 30,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -24,
        "output": "game/assets/audio/ambient/ambient_pause_menu.wav",
    },
    {
        "id": "ambient_settings_menu",
        "name": "Settings Menu Ambience",
        "category": "ambient",
        "prompt": (
            "Musical ambience: settings/options menu. "
            "Minimal: single sustained chord (add9), "
            "slider adjust: pitch bend (quarter tone), "
            "toggle: click (different pitch per setting), "
            "apply: confirmation chord (I-IV-I), "
            "reset: descending arpeggio. "
            "Loop: 45s, -22 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "drums, percussion, vocals, lyrics, sudden loud sounds, compression artifacts",
        "duration_sec": 45,
        "loop": True,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -22,
        "output": "game/assets/audio/ambient/ambient_settings_menu.wav",
    },
]

REACTION_SOUNDS = [
    # Organic Reactions (10)
    {
        "id": "reaction_aldol_condensation",
        "name": "Aldol Condensation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: aldol condensation. "
            "Dropwise addition: individual droplet impacts (water on glass), "
            "exotherm: gentle bubble formation (nucleation sites), "
            "color change: subtle timbre shift (spectral), "
            "crystallization: tiny crystal lattice formation sounds (high freq), "
            "completion: soft chime. "
            "Duration: 5s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_aldol_condensation.wav",
    },
    {
        "id": "reaction_grignard_formation",
        "name": "Grignard Formation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Grignard reagent formation. "
            "Magnesium turnings activation: iodine crystal pop, "
            "initiation: slight exotherm bubble burst, "
            "addition: organic halide drops (viscous), "
            "surface: magnesium consumption (metallic rustle), "
            "completion: ether reflux gentle boil. "
            "Duration: 8s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 8,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_grignard_formation.wav",
    },
    {
        "id": "reaction_diels_alder",
        "name": "Diels-Alder Cycloaddition",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Diels-Alder [4+2] cycloaddition. "
            "Concerted: no intermediates, smooth transition. "
            "Heat: sealed tube pressure creak, "
            "molecular: orbital symmetry fulfilled (descending glissando), "
            "product: crystalline precipitate (delicate tinkle), "
            "Duration: 4s, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 4,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/reactions/reaction_diels_alder.wav",
    },
    {
        "id": "reaction_friedel_crafts",
        "name": "Friedel-Crafts Acylation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Friedel-Crafts acylation. "
            "AlCl3 catalyst: fine powder pour (soft hiss), "
            "acyl chloride addition: lachrymatory vapor (sharp), "
            "complexation: Lewis acid-base adduct formation (subtle click), "
            "aromatic substitution: electrophilic attack (soft pop), "
            "quench: ice water crackle, HCl gas evolution (hiss). "
            "Duration: 6s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 6,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_friedel_crafts.wav",
    },
    {
        "id": "reaction_wittig",
        "name": "Wittig Olefination",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Wittig reaction. "
            "Ylide formation: n-BuLi addition (cold, sharp), "
            "phosphonium salt deprotonation: gas evolution (bubbles), "
            "aldehyde addition: betaine/oxaphosphetane (silent), "
            "elimination: triphenylphosphine oxide precipitation (fine dust), "
            "alkene product: distinct from carbonyl (spectral shift). "
            "Duration: 5s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_wittig.wav",
    },
    {
        "id": "reaction_suzuki_coupling",
        "name": "Suzuki-Miyaura Coupling",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Suzuki coupling. "
            "Pd catalyst: nanoparticle suspension (colloidal shimmer), "
            "base addition: carbonate fizz, "
            "transmetalation: B-O to B-C (molecular click), "
            "reductive elimination: biaryl formation (harmonic convergence), "
            "catalyst recovery: filtration (paper tear). "
            "Duration: 6s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 6,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_suzuki_coupling.wav",
    },
    {
        "id": "reaction_heck_reaction",
        "name": "Heck Reaction",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: Heck reaction. "
            "Oxidative addition: Pd(0) to Pd(II) (electronic shift), "
            "migratory insertion: alkene coordination (glide), "
            "beta-hydride elimination: H transfer (breath), "
            "product release: Pd(0) regeneration (resolve), "
            "base neutralization: amine-HCl salt (soft). "
            "Duration: 5s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_heck_reaction.wav",
    },
    {
        "id": "reaction_hydrogenation",
        "name": "Catalytic Hydrogenation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: H2 hydrogenation. "
            "H2 balloon: gas pressure hiss, "
            "catalyst: Pd/C slurry (black suspension pour), "
            "uptake: pressure drop gauge (mechanical tick), "
            "exotherm: warm bath circulation, "
            "completion: H2 consumption stops, filter cake (paper). "
            "Duration: 10s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 10,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_hydrogenation.wav",
    },
    {
        "id": "reaction_oxidation_pcc",
        "name": "PCC Oxidation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: PCC oxidation (alcohol to aldehyde). "
            "PCC addition: orange solid (crunch), "
            "molecular sieves: bead pour (rattle), "
            "reaction: colorless to yellow (spectral), "
            "workup: ether/ether extraction (glug-glug), "
            "filtration: celite pad (slow drip). "
            "Duration: 5s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_oxidation_pcc.wav",
    },
    {
        "id": "reaction_reduction_lah",
        "name": "LiAlH4 Reduction",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: LiAlH4 reduction. "
            "LiAlH4 addition: grey powder (puff), "
            "ether solvent: cold bath clink, "
            "vigorous: H2 gas evolution (rapid bubbles), "
            "exotherm: reflux condenser knock, "
            "quench: water dropwise (violent hiss), then MeOH, then NaOH. "
            "Duration: 8s, -14 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 8,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -14,
        "output": "game/assets/audio/reactions/reaction_reduction_lah.wav",
    },

    # Inorganic / Physical (10)
    {
        "id": "reaction_acid_base_titration",
        "name": "Acid-Base Titration",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: titration endpoint. "
            "Burette drops: rhythmic impacts (metronome), "
            "indicator: color change flash (visual-audio sync), "
            "pH jump: equivalence point (pitch shift), "
            "overshoot: warning tone, "
            "back-titration: reverse rhythm. "
            "Duration: 4s, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 4,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/reactions/reaction_acid_base_titration.wav",
    },
    {
        "id": "reaction_precipitation",
        "name": "Precipitation Reaction",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: precipitation. "
            "Mixing: two clear solutions (swirl), "
            "nucleation: first crystals (tiny clicks), "
            "growth: particle collision (rustle), "
            "settling: sedimentation (low freq), "
            "supernatant clarity: silence. "
            "Duration: 3s, -22 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 3,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -22,
        "output": "game/assets/audio/reactions/reaction_precipitation.wav",
    },
    {
        "id": "reaction_complexation",
        "name": "Metal-Ligand Complexation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: complexation. "
            "Ligand addition: color change (timbre shift), "
            "chelate effect: entropy-driven (subtle), "
            "geometry change: octahedral/tetrahedral (harmonic), "
            "UV-Vis: d-d transition (spectral), "
            "stability: silence = equilibrium. "
            "Duration: 3s, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 3,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/reactions/reaction_complexation.wav",
    },
    {
        "id": "reaction_redox",
        "name": "Redox Reaction",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: electron transfer. "
            "Half-cells: salt bridge (gel squish), "
            "electron flow: wire (inaudible), "
            "potential: voltmeter beep (endpoint), "
            "color: oxidation state change (spectral), "
            "completion: current drops to zero. "
            "Duration: 4s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 4,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_redox.wav",
    },
    {
        "id": "reaction_electrolysis",
        "name": "Electrolysis",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: electrolysis. "
            "Power on: transformer hum, "
            "anode: O2 bubbles (fine foam), "
            "cathode: H2 bubbles (larger, faster), "
            "gas collection: inverted tube displacement (glug), "
            "power off: silence, gas evolution stops. "
            "Duration: 6s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 6,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_electrolysis.wav",
    },
    {
        "id": "reaction_crystallization",
        "name": "Crystallization",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: slow crystallization. "
            "Supersaturation: silent, "
            "seed crystal: microscopic *click*, "
            "growth: layer by layer (inaudible), "
            "harvest: vacuum filtration (pump), "
            "crystals: dry, hard, *tink* on glass. "
            "Duration: 4s, -22 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 4,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -22,
        "output": "game/assets/audio/reactions/reaction_crystallization.wav",
    },
    {
        "id": "reaction_sublimation",
        "name": "Sublimation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: sublimation. "
            "Vacuum: pump down (frequency drop), "
            "heating: gentle (no boil), "
            "deposition: frost growth on cold finger (silent), "
            "collection: scrape (metal on glass), "
            "product: pure, needle-like. "
            "Duration: 5s, -20 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -20,
        "output": "game/assets/audio/reactions/reaction_sublimation.wav",
    },
    {
        "id": "reaction_distillation",
        "name": "Fractional Distillation",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: distillation. "
            "Pot: boiling (bubble chorus), "
            "column: reflux (condensate returns), "
            "head: vapor temp rise (thermometer tick), "
            "cut: receiver switch (tap turn), "
            "fraction: distinct bp (silence between). "
            "Duration: 8s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 8,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_distillation.wav",
    },
    {
        "id": "reaction_extraction",
        "name": "Liquid-Liquid Extraction",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: separatory funnel extraction. "
            "Shake: two phases emulsify (swish), "
            "vent: pressure release (hiss), "
            "settle: interface sharpens (visual), "
            "drain: lower phase (glug-glug), "
            "repeat: rhythm. "
            "Duration: 5s, -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 5,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_extraction.wav",
    },
    {
        "id": "reaction_chromatography",
        "name": "Column Chromatography",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: flash chromatography. "
            "Load: sample on column (pipette), "
            "elute: solvent front (steady drip), "
            "fractions: test tube *clink* each, "
            "TLC: UV spot (beep), "
            "pool: combine (pour), "
            "rotavap: solvent removal (whine). "
            "Duration: 10s, -16 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 10,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -16,
        "output": "game/assets/audio/reactions/reaction_chromatography.wav",
    },
    {
        "id": "reaction_pcr_cycle",
        "name": "PCR Thermal Cycling",
        "category": "reaction",
        "prompt": (
            "Chemical reaction sound: PCR cycle. "
            "Denature: 98°C (Peltier whine up), "
            "anneal: 60°C (whine down), "
            "extend: 72°C (hold), "
            "cycle repeat: 30x (rhythm), "
            "completion: hold 4°C (silent). "
            "Duration: 6s (compressed), -18 LUFS, 48kHz/24-bit WAV."
        ),
        "negative": "explosion, loud bang, music, vocals, compression artifacts",
        "duration_sec": 6,
        "loop": False,
        "format": "wav",
        "sample_rate": 48000,
        "bit_depth": 24,
        "lufs": -18,
        "output": "game/assets/audio/reactions/reaction_pcr_cycle.wav",
    },
]

UI_SOUNDS = [
    # Navigation & Interaction (15)
    {
        "id": "ui_button_click",
        "name": "Button Click",
        "category": "ui",
        "prompt": (
            "UI sound: button press. "
            "Short: 50ms, "
            "transient: gentle click (wood), "
            "body: sine 800Hz -> 400Hz (pitch drop), "
            "tail: 20ms exponential decay, "
            "variations: 3 (primary, secondary, disabled). "
            "Format: OGG Vorbis, -16 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.1,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -16,
        "output": "game/assets/audio/ui/ui_button_click.ogg",
    },
    {
        "id": "ui_button_hover",
        "name": "Button Hover",
        "category": "ui",
        "prompt": (
            "UI sound: button hover/focus. "
            "Very short: 30ms, "
            "tone: soft sine 1200Hz, "
            "attack: 5ms, release: 25ms, "
            "volume: -30 LUFS (subtle), "
            "no click transient. "
            "Format: OGG Vorbis."
        ),
        "negative": "click, long decay, reverb, music, vocals, loud",
        "duration_sec": 0.05,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -30,
        "output": "game/assets/audio/ui/ui_button_hover.ogg",
    },
    {
        "id": "ui_tab_switch",
        "name": "Tab Switch",
        "category": "ui",
        "prompt": (
            "UI sound: tab navigation. "
            "Short: 80ms, "
            "transient: page turn (paper), "
            "body: two-tone (major third, 600/760Hz), "
            "direction: ascending = forward, descending = back, "
            "tail: 30ms. "
            "Format: OGG Vorbis, -18 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh",
        "duration_sec": 0.15,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -18,
        "output": "game/assets/audio/ui/ui_tab_switch.ogg",
    },
    {
        "id": "ui_menu_open",
        "name": "Menu Open",
        "category": "ui",
        "prompt": (
            "UI sound: menu/dialog open. "
            "Short: 150ms, "
            "whoosh: filtered noise (100Hz-2kHz) up, "
            "impact: soft *thock* (felt), "
            "settle: subtle room tone, "
            "close: reverse whoosh (down). "
            "Format: OGG Vorbis, -16 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.2,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -16,
        "output": "game/assets/audio/ui/ui_menu_open.ogg",
    },
    {
        "id": "ui_menu_close",
        "name": "Menu Close",
        "category": "ui",
        "prompt": (
            "UI sound: menu/dialog close. "
            "Short: 100ms, "
            "whoosh: filtered noise down, "
            "impact: gentle *thud*, "
            "silence: immediate. "
            "Format: OGG Vorbis, -18 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.15,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -18,
        "output": "game/assets/audio/ui/ui_menu_close.ogg",
    },
    {
        "id": "ui_slider_drag",
        "name": "Slider Drag",
        "category": "ui",
        "prompt": (
            "UI sound: continuous slider. "
            "Loopable grain: 50ms ticks (pentatonic), "
            "pitch maps to value (0-100%), "
            "volume: -24 LUFS, "
            "smooth interpolation between grains. "
            "Format: OGG Vorbis."
        ),
        "negative": "click, long decay, reverb, music, vocals, loud",
        "duration_sec": 0.05,
        "loop": True,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -24,
        "output": "game/assets/audio/ui/ui_slider_drag.ogg",
    },
    {
        "id": "ui_dropdown_open",
        "name": "Dropdown Open",
        "category": "ui",
        "prompt": (
            "UI sound: dropdown/combobox open. "
            "Short: 100ms, "
            "expansion: quick whoosh up, "
            "item reveal: subtle cascade (30ms stagger), "
            "settle: silence. "
            "Format: OGG Vorbis, -20 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.15,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -20,
        "output": "game/assets/audio/ui/ui_dropdown_open.ogg",
    },
    {
        "id": "ui_checkbox_toggle",
        "name": "Checkbox Toggle",
        "category": "ui",
        "prompt": (
            "UI sound: checkbox on/off. "
            "On: 60ms, click + sine 800->1000Hz rise. "
            "Off: 60ms, click + sine 1000->800Hz fall. "
            "Format: OGG Vorbis, -18 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.1,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -18,
        "output": "game/assets/audio/ui/ui_checkbox_toggle.ogg",
    },
    {
        "id": "ui_radio_select",
        "name": "Radio Button Select",
        "category": "ui",
        "prompt": (
            "UI sound: radio button selection. "
            "Short: 50ms, "
            "transient: *pop* (bubble), "
            "body: major triad (root-3rd-5th), "
            "deselect: inverse (falling). "
            "Format: OGG Vorbis, -18 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.1,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -18,
        "output": "game/assets/audio/ui/ui_radio_select.ogg",
    },
    {
        "id": "ui_toast_notification",
        "name": "Toast Notification",
        "category": "ui",
        "prompt": (
            "UI sound: toast/snackbar appear. "
            "Short: 200ms, "
            "chime: pentatonic (3 notes, ascending), "
            "body: soft pad chord, "
            "dismiss: same chime descending. "
            "Format: OGG Vorbis, -16 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.3,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -16,
        "output": "game/assets/audio/ui/ui_toast_notification.ogg",
    },
    {
        "id": "ui_error_alert",
        "name": "Error Alert",
        "category": "ui",
        "prompt": (
            "UI sound: error/validation failure. "
            "Short: 300ms, "
            "transient: *buzz* (square wave 200Hz), "
            "body: minor second dissonance, "
            "shake: stereo pan L-R-L (3x), "
            "urgent but not alarming. "
            "Format: OGG Vorbis, -12 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, melodic, loud",
        "duration_sec": 0.4,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -12,
        "output": "game/assets/audio/ui/ui_error_alert.ogg",
    },
    {
        "id": "ui_success_confirm",
        "name": "Success Confirmation",
        "category": "ui",
        "prompt": (
            "UI sound: action completed successfully. "
            "Short: 250ms, "
            "chime: major triad arpeggio up (root-3rd-5th-octave), "
            "body: warm pad, "
            "resolution: instant. "
            "Format: OGG Vorbis, -14 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, dissonance, loud",
        "duration_sec": 0.3,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -14,
        "output": "game/assets/audio/ui/ui_success_confirm.ogg",
    },
    {
        "id": "ui_warning_alert",
        "name": "Warning Alert",
        "category": "ui",
        "prompt": (
            "UI sound: warning/caution. "
            "Short: 400ms, "
            "pattern: three pulses (tritone), "
            "rhythm: triplet feel, "
            "body: suspended chord, "
            "not urgent, attention-grabbing. "
            "Format: OGG Vorbis, -14 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.5,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -14,
        "output": "game/assets/audio/ui/ui_warning_alert.ogg",
    },
    {
        "id": "ui_level_up_stinger",
        "name": "Level Up Stinger",
        "category": "ui",
        "prompt": (
            "UI sound: skill level up. "
            "Duration: 1.5s, "
            "whoosh up: white noise sweep 20Hz-20kHz, "
            "impact: orchestral hit (tam-tam + low brass), "
            "shimmer: harmonic glissando up, "
            "resolve: major 9 chord, "
            "tail: 1s reverb. "
            "Format: OGG Vorbis, -10 LUFS."
        ),
        "negative": "music, vocals, long decay, harsh",
        "duration_sec": 1.5,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -10,
        "output": "game/assets/audio/ui/ui_level_up_stinger.ogg",
    },
    {
        "id": "ui_quest_complete",
        "name": "Quest Complete Fanfare",
        "category": "ui",
        "prompt": (
            "UI sound: quest completed. "
            "Duration: 2s, "
            "fanfare: brass quartet (I-IV-V-I), "
            "percussion: cymbal roll + triangle, "
            "resolve: major chord + celesta, "
            "tail: 1s. "
            "Format: OGG Vorbis, -12 LUFS."
        ),
        "negative": "music, vocals, long decay, harsh",
        "duration_sec": 2.0,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -12,
        "output": "game/assets/audio/ui/ui_quest_complete.ogg",
    },
    {
        "id": "ui_achievement_unlock",
        "name": "Achievement Unlock",
        "category": "ui",
        "prompt": (
            "UI sound: achievement earned. "
            "Duration: 3s, "
            "sparkle: high-frequency noise burst (filtered), "
            "chime: music box (celesta), "
            "announcer: *ding* (sine 2000Hz), "
            "resolve: warm pad. "
            "Format: OGG Vorbis, -12 LUFS."
        ),
        "negative": "music, vocals, long decay, harsh",
        "duration_sec": 3.0,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -12,
        "output": "game/assets/audio/ui/ui_achievement_unlock.ogg",
    },

    # Gameplay Feedback (5)
    {
        "id": "ui_item_pickup",
        "name": "Item Pickup",
        "category": "ui",
        "prompt": (
            "UI sound: collect item. "
            "Short: 100ms, "
            "transient: *pop* (bubble), "
            "pitch: varies by rarity (common=low, legendary=high), "
            "body: none, "
            "stack: rapid retrigger (5ms gap). "
            "Format: OGG Vorbis, -16 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.15,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -16,
        "output": "game/assets/audio/ui/ui_item_pickup.ogg",
    },
    {
        "id": "ui_craft_complete",
        "name": "Crafting Complete",
        "category": "ui",
        "prompt": (
            "UI sound: synthesis/crafting finished. "
            "Duration: 1s, "
            "build: rising pitch sequence (assembly), "
            "complete: *click* (final piece), "
            "result: success chime (major), "
            "fail: error buzz (minor second). "
            "Format: OGG Vorbis, -14 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 1.0,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -14,
        "output": "game/assets/audio/ui/ui_craft_complete.ogg",
    },
    {
        "id": "ui_save_game",
        "name": "Game Saved",
        "category": "ui",
        "prompt": (
            "UI sound: save game. "
            "Short: 200ms, "
            "write: magnetic head *scratch* (nostalgic), "
            "confirm: soft *chime* (pentatonic), "
            "auto-save: quieter (-24 LUFS). "
            "Format: OGG Vorbis, -18 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.25,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -18,
        "output": "game/assets/audio/ui/ui_save_game.ogg",
    },
    {
        "id": "ui_load_game",
        "name": "Game Loaded",
        "category": "ui",
        "prompt": (
            "UI sound: load game. "
            "Short: 300ms, "
            "read: magnetic head *scratch*, "
            "data: ascending digital arpeggio, "
            "ready: warm chord (major 7), "
            "transition: crossfade to gameplay. "
            "Format: OGG Vorbis, -16 LUFS."
        ),
        "negative": "long decay, reverb, music, vocals, harsh, loud",
        "duration_sec": 0.4,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -16,
        "output": "game/assets/audio/ui/ui_load_game.ogg",
    },
    {
        "id": "ui_focus_change",
        "name": "Focus Change / Accessibility",
        "category": "ui",
        "prompt": (
            "UI sound: keyboard focus movement (accessibility). "
            "Very short: 20ms, "
            "tone: pure sine 1000Hz, "
            "volume: -28 LUFS (barely audible), "
            "direction: none (same each time), "
            "screen reader compatible. "
            "Format: OGG Vorbis."
        ),
        "negative": "click, long decay, reverb, music, vocals, loud",
        "duration_sec": 0.03,
        "loop": False,
        "format": "ogg",
        "sample_rate": 48000,
        "bit_depth": 16,
        "lufs": -28,
        "output": "game/assets/audio/ui/ui_focus_change.ogg",
    },
]


def load_manifest() -> dict:
    if ASSET_MANIFEST.exists():
        with open(ASSET_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": 1, "assets": []}


def save_manifest(manifest: dict):
    ASSET_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(ASSET_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_items_by_mode(mode: str):
    if mode == "ambient":
        return AMBIENT_TRACKS
    elif mode == "reactions":
        return REACTION_SOUNDS
    elif mode == "ui":
        return UI_SOUNDS
    elif mode == "all":
        return AMBIENT_TRACKS + REACTION_SOUNDS + UI_SOUNDS
    else:
        return []


def generate_audio(item: dict, api_key: str | None, dry_run: bool) -> dict:
    result = {
        "id": item["id"],
        "name": item["name"],
        "category": item["category"],
        "status": "pending",
        "output_path": item["output"],
        "prompt": item["prompt"],
        "negative": item.get("negative", ""),
        "duration_sec": item.get("duration_sec", 1),
        "loop": item.get("loop", False),
        "format": item.get("format", "wav"),
        "sample_rate": item.get("sample_rate", 48000),
        "bit_depth": item.get("bit_depth", 24),
        "lufs": item.get("lufs", -18),
    }

    if dry_run:
        result["status"] = "dry-run"
        return result

    output_path = ROOT / item["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # No automated generation pipeline yet - requires Suno/UDIO API or similar
    if api_key:
        result["status"] = "skipped"
        result["error"] = "Direct audio API not yet implemented; requires Suno/UDIO API integration"
    else:
        result["status"] = "skipped"
        result["error"] = "No audio generation API configured; prompts ready for manual generation"

    return result


def main():
    parser = argparse.ArgumentParser(description="Flow Music / Audio Generator")
    parser.add_argument("--mode", choices=["ambient", "reactions", "ui", "all"],
                        default="all", help="Generation mode")
    parser.add_argument("--api-key", help="Audio generation API key (Suno, UDIO, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--limit", type=int, help="Limit number of items to generate")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated assets")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("SUNO_API_KEY") or os.environ.get("UDIO_API_KEY")

    items = get_items_by_mode(args.mode)
    if args.limit:
        items = items[:args.limit]

    manifest = load_manifest()
    existing_ids = {a["id"] for a in manifest.get("assets", [])}

    print(f"Mode: {args.mode}")
    print(f"Items to process: {len(items)}")
    if args.dry_run:
        print("\n--- DRY RUN: Audio Prompts ---\n")
        for item in items:
            if args.resume and item["id"] in existing_ids:
                continue
            print(f"[{item['id']}] {item['name']} ({item['category']})")
            print(f"  Duration: {item.get('duration_sec', 1)}s | Loop: {item.get('loop', False)}")
            print(f"  Format: {item.get('format', 'wav')} | {item.get('sample_rate', 48000)}Hz/{item.get('bit_depth', 24)}bit | {item.get('lufs', -18)} LUFS")
            print(f"  Prompt: {item['prompt'][:150]}...")
            print(f"  Negative: {item.get('negative', '')[:80]}...")
            print(f"  Output: {item['output']}")
            print()
        return 0

    results = []
    for i, item in enumerate(items, 1):
        if args.resume and item["id"] in existing_ids:
            print(f"[{i}/{len(items)}] Skipping {item['id']} (already in manifest)")
            continue

        print(f"[{i}/{len(items)}] Processing {item['id']} ({item['name']})...")
        result = generate_audio(item, api_key, args.dry_run)
        results.append(result)

        manifest.setdefault("assets", []).append(result)
        save_manifest(manifest)

        status = result["status"]
        if status == "generated":
            print(f"  ✓ Generated")
        elif status == "dry-run":
            print(f"  ○ Dry run")
        else:
            print(f"  ○ Skipped: {result.get('error', 'Unknown')}")

    generated = sum(1 for r in results if r["status"] == "generated")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"\n--- Summary ---")
    print(f"Generated: {generated}")
    print(f"Skipped: {skipped}")
    print(f"Manifest updated: {ASSET_MANIFEST}")

    return 0


if __name__ == "__main__":
    sys.exit(main())