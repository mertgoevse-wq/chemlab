"""
Computer Vision Models for ChemLab.
Hand tracking, gesture recognition, and landmark data structures.
"""

from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from chemlab.compat import UTC, StrEnum


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


class OptimizedGesture(StrEnum):
    """Optimized gesture set for chemistry lab interactions."""

    IDLE = "IDLE"
    PINCH = "PINCH"  # Pickup small apparatus (test tubes, pipettes)
    PINCH_DRAG = "PINCH_DRAG"  # Pinch + move = pour
    POUR = "PINCH_DRAG"  # Backward compatibility alias
    SWIRL = "SWIRL"  # Backward compatibility alias
    GRAB = "GRAB"  # Move vessel (beakers, flasks)
    FIST = "FIST"  # Firm lock on vessel
    SWIPE = "SWIPE"  # Turn knob (stir plate, valve)
    POINT = "POINT"  # Raycast select (UI, balances)
    RELEASE = "RELEASE"


class OptimizedHandResult(BaseModel):
    """Lightweight telemetry packet for optimized pipeline."""

    model_config = ConfigDict(frozen=True)

    timestamp: float
    frame_index: int
    handedness: Handedness
    gesture: OptimizedGesture
    pinch_distance: float
    is_pinching: bool
    is_grabbing: bool
    grab_strength: float
    tilt_degrees: float
    pour_rate: float
    swipe_delta_x: float = 0.0
    swipe_delta_y: float = 0.0
    world_position_3d: tuple[float, float, float] = (0.0, 0.0, 0.0)
    confidence: float = 1.0
    landmarks_smoothed: list[NormalizedLandmark] = []
