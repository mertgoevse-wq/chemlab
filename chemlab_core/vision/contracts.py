"""
Abstract contracts for Computer Vision tracking and gesture classification.
Decoupled completely from network I/O and 3D rendering.
"""

from typing import Protocol, runtime_checkable

from chemlab_core.models import GestureEvent, HandLandmarkFrame


@runtime_checkable
class LandmarkProvider(Protocol):
    """Protocol for sources yielding hand landmark frames (webcam, synthetic, stream)."""

    def get_next_frame(self) -> HandLandmarkFrame:
        """Produce the next sequential hand landmark frame."""
        ...

    def reset(self) -> None:
        """Reset internal frame counters or generators."""
        ...


@runtime_checkable
class GestureClassifier(Protocol):
    """Protocol for gesture classification engines."""

    def classify(self, frame: HandLandmarkFrame) -> GestureEvent:
        """Classify skeletal landmarks into a high-level gesture event."""
        ...
