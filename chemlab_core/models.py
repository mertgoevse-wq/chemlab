"""
Domain Models and Data Contracts.
Strict typing using Pydantic v2 and typing.Annotated with zero implicit Any.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class GestureType(StrEnum):
    """Enumeration of recognized hand gestures for lab interaction."""

    IDLE = "IDLE"
    PINCH = "PINCH"
    GRAB = "GRAB"
    RELEASE = "RELEASE"
    POINT = "POINT"
    SWIPE_LEFT = "SWIPE_LEFT"
    SWIPE_RIGHT = "SWIPE_RIGHT"
    ROTATE_CW = "ROTATE_CW"
    ROTATE_CCW = "ROTATE_CCW"


class Handedness(StrEnum):
    """Hand identity classification."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"


class NormalizedLandmark(BaseModel):
    """Single 3D hand landmark coordinate normalized to [0.0, 1.0]."""

    model_config = ConfigDict(frozen=True)

    x: Annotated[float, Field(ge=-0.5, le=1.5, description="Normalized horizontal coordinate")]
    y: Annotated[float, Field(ge=-0.5, le=1.5, description="Normalized vertical coordinate")]
    z: Annotated[float, Field(ge=-1.0, le=1.0, description="Normalized depth relative to wrist")]
    visibility: Annotated[float, Field(ge=0.0, le=1.0, default=1.0)]


class HandLandmarkFrame(BaseModel):
    """Collection of 21 standard Mediapipe-compatible hand landmarks."""

    model_config = ConfigDict(frozen=True)

    frame_index: Annotated[int, Field(ge=0, description="Sequential video frame index")]
    timestamp: Annotated[float, Field(ge=0.0, description="Capture timestamp in seconds")]
    handedness: Annotated[Handedness, Field(description="Left or right hand indicator")]
    landmarks: Annotated[
        list[NormalizedLandmark],
        Field(min_length=21, max_length=21, description="21 skeletal landmarks"),
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Overall tracking confidence")]


class GestureEvent(BaseModel):
    """Domain event representing a classified physical interaction gesture."""

    model_config = ConfigDict(frozen=True)

    event_id: Annotated[UUID, Field(default_factory=uuid4)]
    gesture: Annotated[GestureType, Field(description="Classified gesture category")]
    handedness: Annotated[Handedness, Field(description="Active hand for gesture")]
    position: Annotated[
        tuple[float, float, float],
        Field(description="3D focal point of gesture (e.g. pinch midpoint)"),
    ]
    strength: Annotated[
        float, Field(ge=0.0, le=1.0, description="Gesture intensity/confidence (0.0 to 1.0)")
    ]
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]


class IPCRequestType(StrEnum):
    """Supported IPC message operations."""

    PING = "ping"
    CODE_EXECUTION = "code"
    FETCH_SCENE = "fetch-scene"
    SAVE_SCENE = "save"
    TRANSFORM_OBJECT = "transform-object"
    UPDATE_MATERIAL = "update-material"
    SIMULATE_REACTION = "simulate-reaction"


class IPCRequest(BaseModel):
    """Typed IPC Request sent from client to Blender MCP bridge."""

    model_config = ConfigDict(extra="forbid")

    request_id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    type: Annotated[IPCRequestType, Field(description="Target operation")]
    code: Annotated[str | None, Field(default=None, description="Python code string to execute")]
    params: Annotated[
        dict[str, Any],
        Field(default_factory=dict, description="Structured call parameters"),
    ]
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]


class IPCStatus(StrEnum):
    """IPC response outcome states."""

    SUCCESS = "success"
    EXECUTED = "executed"
    ERROR = "error"


class IPCResponse(BaseModel):
    """Typed IPC Response returned by Blender MCP bridge."""

    model_config = ConfigDict(extra="forbid")

    request_id: Annotated[str | None, Field(default=None, description="Matching request UUID hex")]
    status: Annotated[IPCStatus, Field(description="Execution result status")]
    result: Annotated[
        dict[str, Any] | list[Any] | str | int | float | bool | None,
        Field(default=None, description="Output payload or stdout capture"),
    ]
    error: Annotated[str | None, Field(default=None, description="Error detail message if failed")]
    duration_ms: Annotated[
        float, Field(ge=0.0, default=0.0, description="Roundtrip processing latency")
    ]


class SceneCommandType(StrEnum):
    """Discrete commands issued by the Blender 3D Scene Controller."""

    SPAWN_APPARATUS = "SPAWN_APPARATUS"
    SELECT_OBJECT = "SELECT_OBJECT"
    MOVE_OBJECT = "MOVE_OBJECT"
    ROTATE_OBJECT = "ROTATE_OBJECT"
    POUR_CONTAINER = "POUR_CONTAINER"
    SET_LIQUID_COLOR = "SET_LIQUID_COLOR"
    SET_EMISSION = "SET_EMISSION"


class SceneCommand(BaseModel):
    """Command payload passed to the Scene Controller for Blender dispatch."""

    model_config = ConfigDict(frozen=True)

    command_id: Annotated[UUID, Field(default_factory=uuid4)]
    command_type: Annotated[SceneCommandType, Field(description="Action identifier")]
    target_object: Annotated[str, Field(description="Blender object name, e.g. Beaker_250ml")]
    transform_delta: Annotated[
        tuple[float, float, float] | None,
        Field(default=None, description="Delta translation (dx, dy, dz) in meters"),
    ]
    color_rgba: Annotated[
        tuple[float, float, float, float] | None,
        Field(default=None, description="Normalized RGBA color value"),
    ]
    angle_degrees: Annotated[
        float | None, Field(default=None, description="Rotation angle for pouring or stirring")
    ]


class OscillatingPhase(StrEnum):
    """Phases in oscillating chemical reactions (e.g. Briggs-Rauscher / Belousov-Zhabotinsky)."""

    CLEAR_INDUCTION = "CLEAR_INDUCTION"
    AMBER_TRIIODIDE = "AMBER_TRIIODIDE"
    DEEP_BLUE_COMPLEX = "DEEP_BLUE_COMPLEX"


class ReactionState(BaseModel):
    """Mathematical state representing an oscillating reaction cycle."""

    model_config = ConfigDict(frozen=True)

    cycle_index: Annotated[int, Field(ge=0, description="Oscillation cycle count")]
    phase: Annotated[OscillatingPhase, Field(description="Current visual/chemical phase")]
    phase_progress: Annotated[float, Field(ge=0.0, le=1.0, description="Progress through phase")]
    color_rgba: Annotated[
        tuple[float, float, float, float], Field(description="Blender shader color")
    ]
    temperature_celsius: Annotated[float, Field(ge=0.0, le=100.0, default=22.5)]
    period_seconds: Annotated[float, Field(gt=0.0, default=6.0)]
