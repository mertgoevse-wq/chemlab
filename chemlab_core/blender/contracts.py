"""
Contracts for the Blender 3D Scene Controller.
Decoupled from camera hardware and direct socket implementations.
"""

from typing import Protocol, runtime_checkable

from chemlab_core.models import (
    GestureEvent,
    IPCResponse,
    ReactionState,
    SceneCommand,
)


@runtime_checkable
class SceneController(Protocol):
    """Protocol for interacting with the 3D Blender scene representation."""

    def dispatch_command(self, command: SceneCommand) -> IPCResponse:
        """Execute a concrete 3D scene operation in Blender."""
        ...

    def handle_gesture(self, gesture: GestureEvent, target_object: str) -> IPCResponse | None:
        """Translate a physical user hand gesture into a 3D scene manipulation."""
        ...

    def apply_reaction_state(self, target_container: str, reaction: ReactionState) -> IPCResponse:
        """Update chemical liquid material shaders to reflect reaction state."""
        ...

    def get_scene_summary(self) -> dict[str, object]:
        """Fetch summary of objects and active materials in the scene."""
        ...
