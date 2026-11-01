"""
Unit tests for MediaPipe Holistic Full-Body, Arm, and Leg Locomotion Tracking.
Tests 33-landmark pose processing, knee-step locomotion detection,
workstation switching via weight shift, and 1-Euro smoothing on skeleton joints.
"""

from __future__ import annotations

import pytest

from chemlab.cv.holistic_tracker import (
    BodyPoseFrame,
    HolisticTrackingResult,
    LabWorkstation,
    LocomotionState,
    MediaPipeHolisticEngine,
    PoseLandmarkPoint,
)


def _make_dummy_pose_landmarks(
    left_knee_y: float = 0.75,
    right_knee_y: float = 0.75,
    hip_mid_x: float = 0.5,
    left_wrist_y: float = 0.6,
) -> list[PoseLandmarkPoint]:
    """Generates 33 mock pose landmarks centered around reasonable baseline coordinates."""
    points = [PoseLandmarkPoint(x=0.5, y=0.5, z=0.0) for _ in range(33)]
    # 11, 12: shoulders
    points[11] = PoseLandmarkPoint(x=0.4, y=0.3, z=0.0)
    points[12] = PoseLandmarkPoint(x=0.6, y=0.3, z=0.0)
    # 15, 16: wrists
    points[15] = PoseLandmarkPoint(x=0.35, y=left_wrist_y, z=0.0)
    points[16] = PoseLandmarkPoint(x=0.65, y=0.6, z=0.0)
    # 23, 24: hips
    points[23] = PoseLandmarkPoint(x=hip_mid_x - 0.1, y=0.55, z=0.0)
    points[24] = PoseLandmarkPoint(x=hip_mid_x + 0.1, y=0.55, z=0.0)
    # 25, 26: knees
    points[25] = PoseLandmarkPoint(x=hip_mid_x - 0.1, y=left_knee_y, z=0.0)
    points[26] = PoseLandmarkPoint(x=hip_mid_x + 0.1, y=right_knee_y, z=0.0)
    # 27, 28: ankles
    points[27] = PoseLandmarkPoint(x=hip_mid_x - 0.1, y=0.9, z=0.0)
    points[28] = PoseLandmarkPoint(x=hip_mid_x + 0.1, y=0.9, z=0.0)
    return points


def test_stationary_standing_detection() -> None:
    engine = MediaPipeHolisticEngine()
    frame = BodyPoseFrame(timestamp_s=1.0, landmarks=_make_dummy_pose_landmarks())
    res = engine.analyze(frame)
    assert res.locomotion == LocomotionState.STATIONARY
    assert res.current_workstation == LabWorkstation.MAIN_BENCH
    assert not res.is_reaching_high_shelf


def test_alternating_knee_step_locomotion() -> None:
    engine = MediaPipeHolisticEngine()
    # Feed alternating knee lifts simulating stepping in place
    for step in range(6):
        t = 1.0 + step * 0.25
        # Lift left knee on even, right knee on odd
        lk_y = 0.60 if step % 2 == 0 else 0.75
        rk_y = 0.75 if step % 2 == 0 else 0.60
        frame = BodyPoseFrame(
            timestamp_s=t,
            landmarks=_make_dummy_pose_landmarks(left_knee_y=lk_y, right_knee_y=rk_y),
        )
        res = engine.analyze(frame)

    assert res.locomotion == LocomotionState.STEPPING_FORWARD
    assert res.step_cadence_hz > 0.5


def test_lateral_weight_shift_workstation_navigation() -> None:
    engine = MediaPipeHolisticEngine()
    # Shift hips far to the left (lean toward fume hood)
    for step in range(5):
        frame = BodyPoseFrame(
            timestamp_s=1.0 + step * 0.1,
            landmarks=_make_dummy_pose_landmarks(hip_mid_x=0.25),
        )
        res = engine.analyze(frame)

    assert res.current_workstation == LabWorkstation.FUME_HOOD

    # Shift hips far to the right (lean toward analytical bench)
    for step in range(10):
        frame = BodyPoseFrame(
            timestamp_s=2.0 + step * 0.1,
            landmarks=_make_dummy_pose_landmarks(hip_mid_x=0.80),
        )
        res = engine.analyze(frame)

    assert res.current_workstation == LabWorkstation.ANALYTICAL_BENCH


def test_upper_arm_reach_detection() -> None:
    engine = MediaPipeHolisticEngine()
    # Left wrist lifted above shoulder height (y=0.15 is higher than shoulder y=0.3)
    frame = BodyPoseFrame(
        timestamp_s=1.0,
        landmarks=_make_dummy_pose_landmarks(left_wrist_y=0.15),
    )
    res = engine.analyze(frame)
    assert res.is_reaching_high_shelf
    assert res.active_reaching_arm == "left"
