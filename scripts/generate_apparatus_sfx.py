#!/usr/bin/env python3
"""
Apparatus Audio Synthesizer for ChemLab
Generates 44.1kHz 16-bit PCM stereo WAV assets:
1. sfx_boiling_bubble.wav - Multi-rate bubbling and boiling water sound
2. sfx_sizzle.wav         - High-temperature contact sizzling and crackling
3. sfx_flame_loop.wav     - Atmospheric turbulent Bunsen burner flame roar
4. sfx_stirrer_motor.wav  - Smooth magnetic stirrer brushless motor hum
"""

import math
import os
import random
import struct
import wave

SAMPLE_RATE = 44100
TARGET_DIRS = [
    r"C:\Users\Win11 Pro\Desktop\chemlab\audio",
    r"C:\Users\Win11 Pro\Desktop\chemlab\game\audio"
]

def save_wav(filename, samples_l, samples_r=None):
    if samples_r is None:
        samples_r = samples_l
    for out_dir in TARGET_DIRS:
        os.makedirs(out_dir, exist_ok=True)
        filepath = os.path.join(out_dir, filename)
        with wave.open(filepath, "w") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            frames = bytearray()
            for l, r in zip(samples_l, samples_r):
                cl_l = max(-1.0, min(1.0, l))
                cl_r = max(-1.0, min(1.0, r))
                val_l = int(cl_l * 32767.0)
                val_r = int(cl_r * 32767.0)
                frames.extend(struct.pack("<hh", val_l, val_r))
            wav_file.writeframes(frames)
        print(f"Generated apparatus audio asset: {filepath}")

def generate_boiling():
    duration = 3.0
    total_samples = int(duration * SAMPLE_RATE)
    out_l = [0.0] * total_samples
    out_r = [0.0] * total_samples
    random.seed(42)

    # Low churning water rumble (turbulent convection)
    rumble_phase = 0.0
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        rumble = (
            math.sin(2.0 * math.pi * 95.0 * t + math.sin(7.0 * t) * 1.5) * 0.15
            + math.sin(2.0 * math.pi * 140.0 * t + math.cos(9.0 * t) * 1.2) * 0.12
            + (random.random() * 2.0 - 1.0) * 0.04
        )
        out_l[i] += rumble
        out_r[i] += rumble

    # Dense procedural bubble pops
    num_bubbles = int(duration * 65)  # 65 bubbles per second
    for _ in range(num_bubbles):
        start_t = random.uniform(0.0, duration - 0.08)
        start_idx = int(start_t * SAMPLE_RATE)
        f_start = random.uniform(320.0, 750.0)
        f_end = f_start * random.uniform(1.3, 2.2)  # Upward pitch chirp as bubble detaches
        bubble_len = int(random.uniform(0.025, 0.065) * SAMPLE_RATE)
        pan = random.uniform(0.2, 0.8)
        amp = random.uniform(0.18, 0.38)

        for j in range(bubble_len):
            if start_idx + j >= total_samples:
                break
            tau = j / bubble_len
            env = math.sin(math.pi * tau) * math.exp(-3.5 * tau)
            curr_f = f_start + (f_end - f_start) * (tau ** 0.6)
            sig = math.sin(2.0 * math.pi * curr_f * (j / SAMPLE_RATE)) * env * amp
            out_l[start_idx + j] += sig * (1.0 - pan)
            out_r[start_idx + j] += sig * pan

    save_wav("sfx_boiling_bubble.wav", out_l, out_r)

def generate_sizzle():
    duration = 2.0
    total_samples = int(duration * SAMPLE_RATE)
    out_l = [0.0] * total_samples
    out_r = [0.0] * total_samples
    random.seed(101)

    # High frequency granular hiss and boiling steam crackle
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        # Noise band modulation
        mod = 0.5 + 0.5 * math.sin(2.0 * math.pi * 18.0 * t) * math.cos(2.0 * math.pi * 27.0 * t)
        noise_l = (random.random() * 2.0 - 1.0) * 0.16 * mod
        noise_r = (random.random() * 2.0 - 1.0) * 0.16 * mod

        # Micro-crackles
        if random.random() < 0.02:
            crackle = (random.random() * 2.0 - 1.0) * 0.45
            noise_l += crackle
            noise_r += crackle

        out_l[i] = noise_l
        out_r[i] = noise_r

    save_wav("sfx_sizzle.wav", out_l, out_r)

def generate_flame_loop():
    duration = 3.0
    total_samples = int(duration * SAMPLE_RATE)
    out_l = [0.0] * total_samples
    out_r = [0.0] * total_samples
    random.seed(777)

    # Low frequency turbulent gas roar (60 - 160 Hz)
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        tur1 = math.sin(2.0 * math.pi * 78.0 * t + math.sin(11.0 * t)) * 0.22
        tur2 = math.sin(2.0 * math.pi * 124.0 * t + math.cos(15.0 * t)) * 0.18
        gas_hiss = (random.random() * 2.0 - 1.0) * 0.07 * (0.8 + 0.2 * math.sin(25.0 * t))
        out_l[i] = tur1 + tur2 + gas_hiss
        out_r[i] = tur1 * 0.95 + tur2 * 1.05 + gas_hiss

    save_wav("sfx_flame_roaring.wav", out_l, out_r)

def copy_existing_audio():
    # Also ensure original audio files are in game/audio
    src_dir = TARGET_DIRS[0]
    dst_dir = TARGET_DIRS[1]
    for fname in os.listdir(src_dir):
        if fname.endswith(".wav"):
            src_f = os.path.join(src_dir, fname)
            dst_f = os.path.join(dst_dir, fname)
            if not os.path.exists(dst_f):
                import shutil
                shutil.copy2(src_f, dst_f)
                print(f"Copied {fname} to {dst_dir}")

if __name__ == "__main__":
    generate_boiling()
    generate_sizzle()
    generate_flame_loop()
    copy_existing_audio()
    print("Apparatus SFX generated successfully.")
