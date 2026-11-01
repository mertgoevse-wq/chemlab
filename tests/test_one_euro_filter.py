"""
Unit tests for the 1-Euro Filter used to eliminate tracking jitter in 3D hand tracking.
Verifies noise attenuation at low speeds and zero-lag tracking at high velocities.
"""

from __future__ import annotations

import math

import pytest

from chemlab.cv.one_euro_filter import OneEuroFilter, Point3DOneEuroFilter


def test_one_euro_filter_initialization() -> None:
    filt = OneEuroFilter(t0=0.0, x0=1.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0)
    assert filt.last_x == 1.0
    assert filt.last_t == 0.0


def test_one_euro_filter_jitter_smoothing() -> None:
    """A stationary signal with high-frequency noise should be strongly smoothed."""
    filt = OneEuroFilter(t0=0.0, x0=0.5, min_cutoff=0.8, beta=0.005)

    # Send noisy stationary signal
    outputs = []
    t = 0.0
    dt = 1.0 / 60.0
    for i in range(60):
        t += dt
        noise = 0.05 * math.sin(i * 10.0)
        noisy_val = 0.5 + noise
        smoothed = filt(t, noisy_val)
        outputs.append(smoothed)

    # Variance of the output should be significantly lower than raw noise
    raw_var = sum((0.05 * math.sin(i * 10.0)) ** 2 for i in range(60)) / 60.0
    out_var = sum((v - 0.5) ** 2 for v in outputs[-30:]) / 30.0
    assert out_var < raw_var * 0.35, "1-Euro filter must attenuate high-frequency tremor jitter"


def test_one_euro_filter_high_velocity_responsiveness() -> None:
    """When a fast step/swipe happens, filter should adaptively increase cutoff and follow."""
    filt = OneEuroFilter(t0=0.0, x0=0.0, min_cutoff=1.0, beta=0.1)

    # Warm up at 0
    t = 0.0
    dt = 1.0 / 60.0
    for _ in range(10):
        t += dt
        filt(t, 0.0)

    # Step change to 1.0
    t += dt
    filt(t, 1.0)
    t += dt
    y2 = filt(t, 1.0)
    assert y2 > 0.25, "High beta must allow responsive adaptation to fast movements within 2 frames"


def test_point3d_filter_smooths_all_axes() -> None:
    p_filter = Point3DOneEuroFilter(min_cutoff=1.0, beta=0.01)
    smoothed = p_filter(0.016, (0.2, 0.3, 0.5))
    assert len(smoothed) == 3
    assert abs(smoothed[0] - 0.2) < 1e-4
    assert abs(smoothed[1] - 0.3) < 1e-4
    assert abs(smoothed[2] - 0.5) < 1e-4
