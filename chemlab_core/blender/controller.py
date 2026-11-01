"""
Decoupled Blender 3D Scene Controller.
Translates domain interactions into Blender operations via an injected IPCClient.
"""

import logging

from chemlab_core.blender.contracts import SceneController
from chemlab_core.blender.script_builder import (
    build_chemical_material_script,
    build_rotation_script,
    build_transform_script,
)
from chemlab_core.exceptions import BlenderControllerError
from chemlab_core.models import (
    GestureEvent,
    GestureType,
    IPCRequest,
    IPCRequestType,
    IPCResponse,
    ReactionState,
    SceneCommand,
    SceneCommandType,
)
from chemlab_core.transport.contracts import IPCClient

logger = logging.getLogger(__name__)


class BlenderSceneController(SceneController):
    """High-level controller manipulating Blender 3D scene through an abstract IPC client."""

    def __init__(self, ipc_client: IPCClient) -> None:
        self._client = ipc_client

    def dispatch_command(self, command: SceneCommand) -> IPCResponse:
        """Execute a structured SceneCommand in the Blender environment."""
        code: str

        match command.command_type:
            case SceneCommandType.MOVE_OBJECT:
                dx, dy, dz = command.transform_delta or (0.0, 0.0, 0.0)
                code = build_transform_script(command.target_object, dx, dy, dz)

            case SceneCommandType.ROTATE_OBJECT | SceneCommandType.POUR_CONTAINER:
                angle = command.angle_degrees or 45.0
                code = build_rotation_script(command.target_object, angle_degrees=angle)

            case SceneCommandType.SET_LIQUID_COLOR:
                rgba = command.color_rgba or (0.2, 0.6, 1.0, 0.8)
                code = build_chemical_material_script(
                    material_name=f"Mat_Liquid_{command.target_object}",
                    color_rgba=rgba,
                )

            case _:
                raise BlenderControllerError(
                    f"Unsupported command type: {command.command_type}",
                    details={"command": command.model_dump()},
                )

        request = IPCRequest(
            type=IPCRequestType.CODE_EXECUTION,
            code=code,
            params={"command_type": command.command_type.value},
        )
        return self._client.send_request(request)

    def handle_gesture(self, gesture: GestureEvent, target_object: str) -> IPCResponse | None:
        """Map hand gestures to physical manipulations of apparatus in the 3D scene."""
        match gesture.gesture:
            case GestureType.PINCH:
                # Fine grab: elevate container slightly
                command = SceneCommand(
                    command_type=SceneCommandType.MOVE_OBJECT,
                    target_object=target_object,
                    transform_delta=(0.0, 0.0, 0.02 * gesture.strength),
                )
                return self.dispatch_command(command)

            case GestureType.GRAB:
                # Full grab: follow gesture displacement
                gx, gy, gz = gesture.position
                # Normalized coordinate displacement scaled to laboratory meters
                delta_x = (gx - 0.5) * 0.1
                delta_y = (gy - 0.5) * 0.1
                command = SceneCommand(
                    command_type=SceneCommandType.MOVE_OBJECT,
                    target_object=target_object,
                    transform_delta=(delta_x, delta_y, 0.0),
                )
                return self.dispatch_command(command)

            case GestureType.SWIPE_LEFT | GestureType.SWIPE_RIGHT:
                # Pour container by tilting 60 degrees
                tilt = 60.0 if gesture.gesture == GestureType.SWIPE_RIGHT else -60.0
                command = SceneCommand(
                    command_type=SceneCommandType.POUR_CONTAINER,
                    target_object=target_object,
                    angle_degrees=tilt * gesture.strength,
                )
                return self.dispatch_command(command)

            case GestureType.RELEASE | GestureType.IDLE:
                # No action needed on idle/release
                return None

            case _:
                logger.debug(
                    "Unhandled gesture type %s for object %s", gesture.gesture, target_object
                )
                return None

    def apply_reaction_state(self, target_container: str, reaction: ReactionState) -> IPCResponse:
        """Update chemical liquid material shaders in Blender to reflect reaction progression."""
        command = SceneCommand(
            command_type=SceneCommandType.SET_LIQUID_COLOR,
            target_object=target_container,
            color_rgba=reaction.color_rgba,
        )
        return self.dispatch_command(command)

    def get_scene_summary(self) -> dict[str, object]:
        """Query Blender for current active objects and collections."""
        req = IPCRequest(type=IPCRequestType.FETCH_SCENE)
        res = self._client.send_request(req)
        if isinstance(res.result, dict):
            return res.result
        return {"raw": res.result}
