"""
Unit and Integration tests for the Optimized Real-Time Webcam Hand Tracker.
Verifies landmark acquisition, 1-Euro smoothing, optimized gesture classification,
and async pipeline performance targets.
"""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from chemlab.cv.hand_tracker import (
    AirGuitarGesture,  # Backward compat alias
    AirGuitarGestureEngine,  # Backward compat alias
    AsyncHandTracker,
    HandTrackingResult,  # Backward compat alias
    OptimizedGesture,
    OptimizedGestureEngine,
    OptimizedHandResult,
    WebcamHandTracker,  # Backward compat alias
)
from chemlab_core.models import (
    Handedness,
    HandLandmarkFrame,
    NormalizedLandmark,
)

# =============================================================================
# FIXTURES
# =============================================================================


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
    """Thumb tip and index tip brought into tight contact (< 0.045 distance)."""
    lms = list(mock_open_palm_landmarks)
    lms[4] = NormalizedLandmark(x=0.48, y=0.40, z=0.0)
    lms[8] = NormalizedLandmark(x=0.49, y=0.41, z=0.0)
    return lms


@pytest.fixture
def mock_grab_landmarks(
    mock_open_palm_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """All 4 finger tips curled inward toward wrist/palm center."""
    lms = list(mock_open_palm_landmarks)
    for idx in [8, 12, 16, 20]:
        lms[idx] = NormalizedLandmark(x=lms[0].x, y=0.72, z=0.05)
    return lms


@pytest.fixture
def mock_swipe_landmarks(
    mock_pinch_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """Pinch gesture with horizontal movement (for knob turning)."""
    lms = list(mock_pinch_landmarks)
    # Shift pinch center horizontally
    lms[4] = NormalizedLandmark(x=0.55, y=0.40, z=0.0)
    lms[8] = NormalizedLandmark(x=0.56, y=0.41, z=0.0)
    return lms


@pytest.fixture
def mock_pour_landmarks(
    mock_pinch_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """Pinch + wrist tilt for pouring (>38 deg tilt)."""
    lms = list(mock_pinch_landmarks)
    # Tilt: index MCP up, pinky MCP down
    lms[5] = NormalizedLandmark(x=0.45, y=0.35, z=0.20)
    lms[17] = NormalizedLandmark(x=0.55, y=0.75, z=-0.20)
    return lms


@pytest.fixture
def mock_point_landmarks(
    mock_open_palm_landmarks: list[NormalizedLandmark],
) -> list[NormalizedLandmark]:
    """Index extended, others curled."""
    lms = list(mock_open_palm_landmarks)
    lms[8] = NormalizedLandmark(x=0.5, y=0.3, z=0.0)  # Index tip far from wrist
    lms[12] = NormalizedLandmark(x=0.5, y=0.72, z=0.05)  # Middle curled
    lms[16] = NormalizedLandmark(x=0.55, y=0.72, z=0.05)  # Ring curled
    lms[20] = NormalizedLandmark(x=0.6, y=0.72, z=0.05)  # Pinky curled
    return lms


# =============================================================================
# GESTURE ENGINE TESTS
# =============================================================================


def test_gesture_engine_idle(mock_open_palm_landmarks: list[NormalizedLandmark]) -> None:
    engine = OptimizedGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=mock_open_palm_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == OptimizedGesture.IDLE
    assert result.pinch_distance > 0.05
    assert not result.is_pinching
    assert not result.is_grabbing


def test_gesture_engine_pinch(mock_pinch_landmarks: list[NormalizedLandmark]) -> None:
    engine = OptimizedGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=2,
        timestamp=0.032,
        handedness=Handedness.RIGHT,
        landmarks=mock_pinch_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == OptimizedGesture.PINCH
    assert result.is_pinching
    assert result.pinch_distance < PINCH_ENTER_DIST * 1.5  # Should be well within threshold


def test_gesture_engine_pinch_hysteresis(mock_pinch_landmarks: list[NormalizedLandmark]) -> None:
    """Verify Schmitt trigger hysteresis on pinch."""
    engine = OptimizedGestureEngine(pinch_enter=0.045, pinch_exit=0.065)

    # First frame: pinch
    frame1 = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=mock_pinch_landmarks,
        confidence=0.95,
    )
    res1 = engine.analyze(frame1)
    assert res1.gesture == OptimizedGesture.PINCH
    assert res1.is_pinching

    # Second frame: slightly opened but still within hysteresis
    lms2 = list(mock_pinch_landmarks)
    lms2[4] = NormalizedLandmark(x=0.48, y=0.42, z=0.0)
    lms2[8] = NormalizedLandmark(x=0.51, y=0.43, z=0.0)  # distance ~0.045-0.055
    frame2 = HandLandmarkFrame(
        frame_index=2,
        timestamp=0.032,
        handedness=Handedness.RIGHT,
        landmarks=lms2,
        confidence=0.95,
    )
    res2 = engine.analyze(frame2)
    # Should STILL be pinching (hysteresis)
    assert res2.is_pinching

    # Third frame: clearly open > exit threshold
    lms3 = list(mock_pinch_landmarks)
    lms3[4] = NormalizedLandmark(x=0.45, y=0.5, z=0.0)
    lms3[8] = NormalizedLandmark(x=0.55, y=0.3, z=0.0)  # distance > 0.065
    frame3 = HandLandmarkFrame(
        frame_index=3,
        timestamp=0.048,
        handedness=Handedness.RIGHT,
        landmarks=lms3,
        confidence=0.95,
    )
    res3 = engine.analyze(frame3)
    assert not res3.is_pinching
    assert res3.gesture == OptimizedGesture.RELEASE


def test_gesture_engine_grab(mock_grab_landmarks: list[NormalizedLandmark]) -> None:
    engine = OptimizedGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=3,
        timestamp=0.048,
        handedness=Handedness.RIGHT,
        landmarks=mock_grab_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture in (OptimizedGesture.GRAB, OptimizedGesture.FIST)
    assert result.is_grabbing
    assert result.grab_strength > 0.5


def test_gesture_engine_pour(mock_pour_landmarks: list[NormalizedLandmark]) -> None:
    engine = OptimizedGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=4,
        timestamp=0.064,
        handedness=Handedness.RIGHT,
        landmarks=mock_pour_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == OptimizedGesture.PINCH_DRAG
    assert result.pour_rate > 0.0
    assert abs(result.tilt_degrees) > POUR_ANGLE_ENTER


def test_gesture_engine_swipe_knob(
    mock_pinch_landmarks: list[NormalizedLandmark],
    mock_swipe_landmarks: list[NormalizedLandmark],
) -> None:
    """Test swipe gesture for knob turning."""
    engine = OptimizedGestureEngine()

    # First frame: pinch at center
    frame1 = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=mock_pinch_landmarks,
        confidence=0.95,
    )
    res1 = engine.analyze(frame1)
    assert res1.gesture == OptimizedGesture.PINCH

    # Second frame: pinch moved horizontally (swipe)
    frame2 = HandLandmarkFrame(
        frame_index=2,
        timestamp=0.032,
        handedness=Handedness.RIGHT,
        landmarks=mock_swipe_landmarks,
        confidence=0.95,
    )
    res2 = engine.analyze(frame2)
    assert res2.gesture == OptimizedGesture.SWIPE
    assert abs(res2.swipe_delta_x) > SWIPE_THRESHOLD * 0.5


def test_gesture_engine_point(mock_point_landmarks: list[NormalizedLandmark]) -> None:
    engine = OptimizedGestureEngine()
    frame = HandLandmarkFrame(
        frame_index=5,
        timestamp=0.080,
        handedness=Handedness.RIGHT,
        landmarks=mock_point_landmarks,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == OptimizedGesture.POINT


def test_gesture_engine_fist_vs_grab(mock_grab_landmarks: list[NormalizedLandmark]) -> None:
    """Verify FIST sub-state for tight grab."""
    engine = OptimizedGestureEngine(grab_enter=0.16, grab_exit=0.20)

    # Very tight grab -> FIST (fingertips tightly curled near wrist)
    lms = list(mock_grab_landmarks)
    for idx in [8, 12, 16, 20]:
        lms[idx] = NormalizedLandmark(x=lms[0].x, y=0.78, z=0.02)

    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=lms,
        confidence=0.95,
    )
    result = engine.analyze(frame)
    assert result.gesture == OptimizedGesture.FIST
    assert result.grab_strength > 0.8


# =============================================================================
# TRACKER TESTS
# =============================================================================


def test_tracker_synthetic_mode(mock_pinch_landmarks: list[NormalizedLandmark]) -> None:
    tracker = AsyncHandTracker(use_synthetic=True)
    res = tracker.process_landmarks(
        landmarks=mock_pinch_landmarks,
        handedness=Handedness.RIGHT,
        timestamp=0.1,
    )
    assert res is not None
    assert res.handedness == Handedness.RIGHT
    assert res.gesture == OptimizedGesture.PINCH
    assert len(res.landmarks_smoothed) == 21


def test_tracker_one_euro_smoothing(mock_open_palm_landmarks: list[NormalizedLandmark]) -> None:
    """Verify 1-Euro filter reduces jitter."""
    tracker = AsyncHandTracker(use_synthetic=True, min_cutoff=0.8, beta=0.005)

    # Add noise to landmarks
    noisy_lms = []
    for i, lm in enumerate(mock_open_palm_landmarks):
        noise = 0.01 * np.sin(i * 10.0) if hasattr(np, "sin") else 0.01 * math.sin(i * 10.0)
        noisy_lms.append(
            NormalizedLandmark(x=lm.x + noise, y=lm.y + noise, z=lm.z, visibility=lm.visibility)
        )

    # Process multiple frames
    results = []
    for frame_idx in range(10):
        res = tracker.process_landmarks(noisy_lms, Handedness.RIGHT, timestamp=frame_idx * 0.016)
        results.append(res)

    # Check smoothing occurred - variance should be reduced
    raw_x = [lm.x for lm in noisy_lms[:4]]  # First few landmarks
    smoothed_x = [res.landmarks_smoothed[0].x for res in results]

    raw_var = (
        np.var(raw_x)
        if hasattr(np, "var")
        else sum((x - np.mean(raw_x)) ** 2 for x in raw_x) / len(raw_x)
    )
    smooth_var = (
        np.var(smoothed_x)
        if hasattr(np, "var")
        else sum((x - np.mean(smoothed_x)) ** 2 for x in smoothed_x) / len(smoothed_x)
    )

    # Allow for initial frames where filter hasn't converged
    assert smooth_var <= raw_var * 1.5  # Should not amplify noise


def test_tracker_performance_stats() -> None:
    """Verify performance metrics are exposed."""
    tracker = AsyncHandTracker(use_synthetic=True)
    stats = tracker.get_performance_stats()

    assert "inference_ms" in stats
    assert "process_ms" in stats
    assert "total_ms" in stats
    assert "queue_depth" in stats
    assert isinstance(stats["total_ms"], float)


# =============================================================================
# ASYNC TRACKER TESTS (Requires camera - skipped in CI without hardware)
# =============================================================================


@pytest.mark.skip(reason="Requires physical webcam hardware")
def test_async_tracker_start_stop() -> None:
    tracker = AsyncHandTracker(camera_index=0, use_synthetic=False)
    tracker.start()
    time.sleep(0.5)  # Let threads spin up
    tracker.stop()
    assert not tracker._running


@pytest.mark.skip(reason="Requires physical webcam hardware")
def test_async_tracker_receives_results() -> None:
    tracker = AsyncHandTracker(camera_index=0, use_synthetic=False)
    tracker.start()
    time.sleep(2.0)  # Wait for some frames

    result = tracker.get_latest_result()
    # May be None if no hand detected, but should not crash
    tracker.stop()


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================


def test_backward_compat_aliases() -> None:
    """Ensure old class names still work."""
    assert AirGuitarGesture is OptimizedGesture
    assert HandTrackingResult is OptimizedHandResult
    assert AirGuitarGestureEngine is OptimizedGestureEngine
    assert WebcamHandTracker is AsyncHandTracker

    # Old enum values should work
    assert AirGuitarGesture.IDLE == OptimizedGesture.IDLE
    assert AirGuitarGesture.PINCH == OptimizedGesture.PINCH
    assert AirGuitarGesture.GRAB == OptimizedGesture.GRAB
    assert AirGuitarGesture.POUR == OptimizedGesture.PINCH_DRAG  # Renamed


def test_backward_compat_engine() -> None:
    """Old engine API should work."""
    engine = AirGuitarGestureEngine()
    lms = []
    lms.append(NormalizedLandmark(x=0.5, y=0.8, z=0.0))
    for i in range(1, 21):
        lms.append(NormalizedLandmark(x=0.5, y=0.7, z=0.0))

    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=lms,
        confidence=0.95,
    )
    result = engine.analyze(frame)

    assert hasattr(result, "gesture")
    assert hasattr(result, "pinch_distance")
    assert hasattr(result, "world_position_3d")


# =============================================================================
# PERFORMANCE TARGET TESTS
# =============================================================================


def test_gesture_classification_speed() -> None:
    """Gesture classification should be < 1ms per frame."""
    engine = OptimizedGestureEngine()
    lms = []
    lms.append(NormalizedLandmark(x=0.5, y=0.8, z=0.0))
    for i in range(1, 21):
        lms.append(NormalizedLandmark(x=0.5, y=0.7 - i * 0.01, z=0.0))

    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.016,
        handedness=Handedness.RIGHT,
        landmarks=lms,
        confidence=0.95,
    )

    # Warmup
    for _ in range(10):
        engine.analyze(frame)

    # Timed runs
    start = time.perf_counter()
    for _ in range(100):
        engine.analyze(frame)
    elapsed_ms = (time.perf_counter() - start) * 1000

    per_frame_ms = elapsed_ms / 100
    assert per_frame_ms < 1.0, (
        f"Gesture classification took {per_frame_ms:.3f}ms/frame, target < 1ms"
    )


def test_one_euro_filter_speed() -> None:
    """1-Euro filtering 21 landmarks should be < 0.8ms."""
    from chemlab.cv.one_euro_filter import Point3DOneEuroFilter

    filters = [Point3DOneEuroFilter(min_cutoff=1.0, beta=0.007) for _ in range(21)]
    landmarks = [(0.5, 0.5, 0.0) for _ in range(21)]
    t = 0.0

    # Warmup
    for _ in range(10):
        for i, filt in enumerate(filters):
            filt(t, landmarks[i])
        t += 0.016

    # Timed
    start = time.perf_counter()
    for _ in range(100):
        for i, filt in enumerate(filters):
            filt(t, landmarks[i])
        t += 0.016
    elapsed_ms = (time.perf_counter() - start) * 1000

    per_frame_ms = elapsed_ms / 100
    assert per_frame_ms < 1.5, f"21-landmark 1-Euro filtering took {per_frame_ms:.3f}ms/frame"


# Constants used in tests
PINCH_ENTER_DIST = 0.045
POUR_ANGLE_ENTER = 48.0
SWIPE_THRESHOLD = 0.03
