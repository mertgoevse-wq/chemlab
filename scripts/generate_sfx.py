#!/usr/bin/env python3
"""
Audio Synthesizer for ChemLab Simulation Feedback
Generates pristine 44.1kHz 16-bit PCM stereo WAV audio assets:
1. sfx_quest_complete.wav - Shimmering crystal arpeggio for task milestone
2. sfx_level_up.wav       - Cinematic triumphal fanfare with sub-bass impact
3. sfx_pinch_ready.wav    - Subtle high-tech hover blip (Green dot state)
4. sfx_pinch_hover.wav    - Resonant proximity lock cue (Yellow dot state)
5. sfx_pinch_grip.wav     - Tactile glass-clink damped snap (Blue dot state)
6. sfx_safety_alert.wav   - Two-tone warning alert for hazard states
"""

import math
import os
import struct
import wave

SAMPLE_RATE = 44100
AUDIO_DIR = r"C:\Users\Win11 Pro\Desktop\chemlab\audio"


def save_wav(filename, samples_l, samples_r=None):
    if samples_r is None:
        samples_r = samples_l
    filepath = os.path.join(AUDIO_DIR, filename)
    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        frames = bytearray()
        for l, r in zip(samples_l, samples_r):
            # Clip between -1.0 and 1.0
            cl_l = max(-1.0, min(1.0, l))
            cl_r = max(-1.0, min(1.0, r))
            val_l = int(cl_l * 32767.0)
            val_r = int(cl_r * 32767.0)
            frames.extend(struct.pack("<hh", val_l, val_r))
        wav_file.writeframes(frames)
    print(f"Generated audio asset: {filepath}")


def generate_quest_complete():
    duration = 2.4
    total_samples = int(duration * SAMPLE_RATE)
    notes = [
        (0.00, 523.25),  # C5
        (0.12, 659.25),  # E5
        (0.24, 783.99),  # G5
        (0.36, 987.77),  # B5
        (0.48, 1046.50),  # C6
        (0.60, 1318.51),  # E6
    ]
    out_l = [0.0] * total_samples
    out_r = [0.0] * total_samples

    for start_t, freq in notes:
        start_idx = int(start_t * SAMPLE_RATE)
        note_len = total_samples - start_idx
        pan = (freq - 523.25) / (1318.51 - 523.25) * 0.6 - 0.3  # Stereo panning
        gain_l = 0.5 - pan * 0.5
        gain_r = 0.5 + pan * 0.5

        for i in range(note_len):
            t = i / SAMPLE_RATE
            # Crystal bell envelope: fast attack, exponential decay
            env = math.exp(-3.2 * t) * (1.0 - math.exp(-60.0 * t))
            # Harmonics: fundamental + octave + octave fifth
            tone = (
                math.sin(2.0 * math.pi * freq * t) * 0.65
                + math.sin(2.0 * math.pi * freq * 2.0 * t) * 0.25
                + math.sin(2.0 * math.pi * freq * 3.0 * t) * 0.10
            )
            val = tone * env * 0.45
            idx = start_idx + i
            out_l[idx] += val * gain_l
            out_r[idx] += val * gain_r

    # Add subtle sparkling chorus / shimmer tail
    for i in range(int(0.6 * SAMPLE_RATE), total_samples):
        t = (i - 0.6 * SAMPLE_RATE) / SAMPLE_RATE
        shimmer_env = math.exp(-1.8 * t) * 0.12
        shimmer_l = math.sin(2.0 * math.pi * 2093.0 * t + math.sin(12.0 * t)) * shimmer_env
        shimmer_r = math.cos(2.0 * math.pi * 2093.0 * t + math.cos(14.0 * t)) * shimmer_env
        out_l[i] += shimmer_l
        out_r[i] += shimmer_r

    save_wav("sfx_quest_complete.wav", out_l, out_r)


def generate_level_up():
    duration = 3.0
    total_samples = int(duration * SAMPLE_RATE)
    out_l = [0.0] * total_samples
    out_r = [0.0] * total_samples

    # Sub-bass impact at t=0
    for i in range(int(1.2 * SAMPLE_RATE)):
        t = i / SAMPLE_RATE
        bass_freq = 70.0 * math.exp(-1.8 * t) + 40.0
        bass_env = math.exp(-3.0 * t) * 0.6
        bass_tone = math.sin(2.0 * math.pi * bass_freq * t) * bass_env
        out_l[i] += bass_tone
        out_r[i] += bass_tone

    # Fanfare chords (F major -> G major -> C major)
    chords = [
        (0.10, [349.23, 440.00, 523.25]),  # F4, A4, C5
        (0.35, [392.00, 493.88, 587.33]),  # G4, B4, D5
        (0.65, [523.25, 659.25, 783.99, 1046.50]),  # C5, E5, G5, C6 (Power Triumph)
    ]

    for start_t, freq_list in chords:
        start_idx = int(start_t * SAMPLE_RATE)
        chord_len = total_samples - start_idx
        decay_rate = 1.5 if start_t > 0.6 else 4.0
        chord_amp = 0.40 if start_t > 0.6 else 0.25

        for i in range(chord_len):
            t = i / SAMPLE_RATE
            env = math.exp(-decay_rate * t) * (1.0 - math.exp(-50.0 * t))
            sig = 0.0
            for idx_f, f in enumerate(freq_list):
                # Rich synth brass overtone series
                saw_approx = (
                    math.sin(2.0 * math.pi * f * t)
                    + 0.5 * math.sin(4.0 * math.pi * f * t)
                    + 0.25 * math.sin(6.0 * math.pi * f * t)
                )
                sig += saw_approx * (0.8 / len(freq_list))
            val = sig * env * chord_amp
            target_idx = start_idx + i
            out_l[target_idx] += val * 0.95
            out_r[target_idx] += val * 1.05

    save_wav("sfx_level_up.wav", out_l, out_r)


def generate_pinch_ready():
    duration = 0.10
    total_samples = int(duration * SAMPLE_RATE)
    out = [0.0] * total_samples
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-35.0 * t) * (1.0 - math.exp(-200.0 * t))
        tone = math.sin(2.0 * math.pi * 920.0 * t) * env * 0.25
        out[i] = tone
    save_wav("sfx_pinch_ready.wav", out)


def generate_pinch_hover():
    duration = 0.14
    total_samples = int(duration * SAMPLE_RATE)
    out = [0.0] * total_samples
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-22.0 * t) * math.sin(math.pi * t / duration)
        # Gentle dual harmonic warble
        tone = (
            (math.sin(2.0 * math.pi * 660.0 * t) * 0.6 + math.sin(2.0 * math.pi * 880.0 * t) * 0.4)
            * env
            * 0.28
        )
        out[i] = tone
    save_wav("sfx_pinch_hover.wav", out)


def generate_pinch_grip():
    duration = 0.18
    total_samples = int(duration * SAMPLE_RATE)
    out = [0.0] * total_samples
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        # Damped mechanical glass snap: initial sharp pop followed by micro glass ring
        click_env = math.exp(-120.0 * t) * 0.5
        ring_env = math.exp(-25.0 * t) * 0.3
        click = math.sin(2.0 * math.pi * 320.0 * t) * click_env
        ring = math.sin(2.0 * math.pi * 2150.0 * t) * ring_env
        out[i] = (click + ring) * 0.45
    save_wav("sfx_pinch_grip.wav", out)


def generate_safety_alert():
    duration = 0.65
    total_samples = int(duration * SAMPLE_RATE)
    out = [0.0] * total_samples
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        # Pulse 1: 0 - 0.25s at 740 Hz
        # Pulse 2: 0.32 - 0.57s at 587 Hz
        tone = 0.0
        if t < 0.25:
            env = math.sin(math.pi * (t / 0.25))
            tone = math.sin(2.0 * math.pi * 740.0 * t) * env * 0.35
        elif 0.32 <= t < 0.57:
            env = math.sin(math.pi * ((t - 0.32) / 0.25))
            tone = math.sin(2.0 * math.pi * 587.0 * t) * env * 0.35
        out[i] = tone
    save_wav("sfx_safety_alert.wav", out)


if __name__ == "__main__":
    os.makedirs(AUDIO_DIR, exist_ok=True)
    generate_quest_complete()
    generate_level_up()
    generate_pinch_ready()
    generate_pinch_hover()
    generate_pinch_grip()
    generate_safety_alert()
    print("All audio feedback sound cues generated successfully.")
