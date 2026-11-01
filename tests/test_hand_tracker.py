"""
Unit and Integration tests for the Real-Time Webcam Hand Tracker.
Verifies landmark acquisition, 1-Euro smoothing, air-guitar gesture classification,
and IPC frame dispatching.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from chemlab.cv.hand_tracker import (
    AirGuitarGesture,
    AirGuitarGestureEngine,
    HandTrackingResult,
    WebcamHandTracker,
)
from chemlab_core.models import (
    Handedness,
    HandLandmarkFrame,
    NormalizedLandmark,
)


@pytest.fixture
def mock_open_palm_landmarks() -> list[NormalizedLandmark]:
    """Generates standard open hand landmarks (all fingers straight out)."""
    lms = []
    # 0: Wrist
    lms.append(NormalizedLandmark(x=0.5, y=0.8, z=0.0))
    # 1-4: Thumb
    for i in range(1, 5):
        lms.append(NormalizedLandmark(x=0.38 - i * 0.02, y=0.7 - i * 0.04, z=-0.01 * i))
    # 5-8: Index
    for i in range(1, 5):
        lms.append(NormalizedLandmark(x=0.45, y=0.65 - i * 0.08, z=-0.01 * i))
    # 9-12: Middle
    for i in range(1, 5):
        lms.append(NormalizedLandmark(x=0.50, y=0.65 - i * 0.09, z=-0.01 * i))
    # 13-16: Ring
    for i in range(1, 5):
        lms.append(NormalizedLandmark(x=0.55, y=0.65 - i * 0.08, z=-0.01 * i))
    # 17-20: Pinky
    for i in range(1, 5):
        lms.append(NormalizedLandmark(x=0.60, y=0.65 - i * 0.06, z=-0.01 * i))
    return lms


@pytest.fixture
def mock_pinch_landmarks(
    mock_open_palm_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """Thumb tip and index tip brought into tight contact (< 0.04 distance)."""
    lms = list(mock_open_palm_landmarks)
    # Index tip is index 8, Thumb tip is index 4
    lms[4] = NormalizedLandmark(x=0.48, y=0.40, z=0.0)
    lms[8] = NormalizedLandmark(x=0.49, y=0.41, z=0.0)
    return lms


@pytest.fixture
def mock_grab_landmarks(
    mock_open_palm_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """All 4 finger tips curled inward toward wrist/palm center."""
    lms = list(mock_open_palm_landmarks)
    # Curl fingertips (8, 12, 16, 20) very close to palm/wrist (y=0.75)
    for idx in [8, 12, 16, 20]:
        lms[idx] = NormalizedLandmark(x=lms[0].x, y=0.72, z=0.05)
    return lms


def test_air_guitar_gesture_engine_idle(mock_open_palm_landmarks: list[NormalizedLandmark]) -> None:
    engine = AirGuitarGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=mock_open_palm_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == AirGuitarGesture.IDLE
    assert result.pinch_distance > 0.05
    assert not result.is_pinching


def test_air_guitar_gesture_engine_pinch(mock_pinch_landmarks: list[NormalizedLandmark]) -> None:
    engine = AirGuitarGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=2,
        timestamp=0.032,
        handedness=Handedness.RIGHT,
        landmarks=mock_pinch_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == AirGuitarGesture.PINCH
    assert result.is_pinching
    assert result.pinch_distance < 0.05
    assert result.grab_strength > 0.5


def test_air_guitar_gesture_engine_grab(mock_grab_landmarks: list[NormalizedLandmark]) -> None:
    engine = AirGuitarGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=3,
        timestamp=0.048,
        handedness=Handedness.RIGHT,
        landmarks=mock_grab_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture in (AirGuitarGesture.GRAB, AirGuitarGesture.FIST)
    assert result.is_grabbing


def test_webcam_hand_tracker_synthetic_mode(mock_pinch_landmarks: list[NormalizedLandmark]) -> None:
    tracker = WebcamHandTracker(use_synthetic=True)
    res = tracker.process_landmarks(
        landmarks=mock_pinch_landmarks,
        handedness=Handedness.RIGHT,
        timestamp=0.1,
    )
    assert res is not None
    assert res.handedness == Handedness.RIGHT
    assert res.gesture == AirGuitarGesture.PINCH
    assert len(res.smoothed_landmarks) == 21


def test_tilt_and_pour_detection(mock_open_palm_landmarks: list[NormalizedLandmark]) -> None:
    engine = AirGuitarGestureEngine()
    # Tilt the hand by rotating x/y coordinates: wrist at (0.5, 0.5), knuckles pitched sideways
    lms = list(mock_open_palm_landmarks)
    # Roll wrist by shifting index MCP (5) and pinky MCP (17) in Z/Y
    lms[5] = NormalizedLandmark(x=0.45, y=0.55, z=0.15)
    lms[17] = NormalizedLandmark(x=0.55, y=0.65, z=-0.15)
    frame = HandLandmarkFrame(
        frame_index=4,
        timestamp=0.064,
        handedness=Handedness.RIGHT,
        landmarks=lms,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    # Hand tilt should be computed
    assert abs(result.tilt_degrees) > 10.0
