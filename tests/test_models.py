"""
Unit tests for domain models and data contracts.
Verifies strict validation constraints and Pydantic schema enforcement.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from chemlab_core.models import (
    GestureEvent,
    GestureType,
    Handedness,
    HandLandmarkFrame,
    IPCRequest,
    IPCRequestType,
    IPCResponse,
    IPCStatus,
    NormalizedLandmark,
    OscillatingPhase,
    ReactionState,
    SceneCommand,
    SceneCommandType,
)


def test_normalized_landmark_valid() -> None:
    """Verify valid normalized landmark coordinates."""
    lm = NormalizedLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0)
    assert lm.x == 0.5
    assert lm.y == 0.5
    assert lm.z == 0.0


def test_normalized_landmark_out_of_bounds() -> None:
    """Verify out-of-bounds coordinates raise ValidationError."""
    with pytest.raises(ValidationError):
        NormalizedLandmark(x=2.5, y=0.5, z=0.0)  # x must be <= 1.5


def test_hand_landmark_frame_length_constraint() -> None:
    """Verify HandLandmarkFrame strictly enforces exactly 21 landmarks."""
    valid_landmarks = [NormalizedLandmark(x=0.1, y=0.1, z=0.0) for _ in range(21)]
    frame = HandLandmarkFrame(
        frame_index=1,
        timestamp=0.033,
        handedness=Handedness.RIGHT,
        landmarks=valid_landmarks,
        confidence=0.95,
    )
    assert len(frame.landmarks) == 21

    # Negative test: 20 landmarks should fail validation
    with pytest.raises(ValidationError):
        HandLandmarkFrame(
            frame_index=1,
            timestamp=0.033,
            handedness=Handedness.RIGHT,
            landmarks=valid_landmarks[:-1],
            confidence=0.95,
        )


def test_gesture_event_serialization() -> None:
    """Verify roundtrip JSON serialization of GestureEvent."""
    evt = GestureEvent(
        gesture=GestureType.PINCH,
        handedness=Handedness.RIGHT,
        position=(0.45, 0.65, -0.02),
        strength=0.88,
    )
    json_data = evt.model_dump_json()
    restored = GestureEvent.model_validate_json(json_data)
    assert restored.gesture == GestureType.PINCH
    assert restored.position == (0.45, 0.65, -0.02)
    assert restored.strength == pytest.approx(0.88)


def test_ipc_request_and_response() -> None:
    """Verify IPC request and response model validation."""
    req_id = uuid4().hex
    req = IPCRequest(
        request_id=req_id,
        type=IPCRequestType.CODE_EXECUTION,
        code="print('test')",
        params={"speed": 10},
    )
    assert req.type == IPCRequestType.CODE_EXECUTION
    assert req.code == "print('test')"

    res = IPCResponse(
        request_id=req_id,
        status=IPCStatus.SUCCESS,
        result={"message": "ok"},
        duration_ms=4.2,
    )
    assert res.status == IPCStatus.SUCCESS
    assert res.duration_ms == 4.2


def test_reaction_state_model() -> None:
    """Verify chemical reaction state structure and boundary validation."""
    state = ReactionState(
        cycle_index=2,
        phase=OscillatingPhase.AMBER_TRIIODIDE,
        phase_progress=0.45,
        color_rgba=(0.85, 0.45, 0.05, 0.85),
        temperature_celsius=23.1,
        period_seconds=6.0,
    )
    assert state.phase == OscillatingPhase.AMBER_TRIIODIDE
    assert state.cycle_index == 2


def test_scene_command_immutable() -> None:
    """Verify SceneCommand is frozen against mutation."""
    cmd = SceneCommand(
        command_type=SceneCommandType.MOVE_OBJECT,
        target_object="Beaker_250ml",
        transform_delta=(0.01, 0.0, 0.0),
    )
    with pytest.raises(ValidationError):
        # Frozen models do not permit assignment
        cmd.target_object = "Flask"  # type: ignore[misc]
