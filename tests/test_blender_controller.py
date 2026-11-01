"""
Unit tests for the Blender 3D Scene Controller.
Exercises scene command generation and gesture translation in total isolation from Blender GUI.
"""

import pytest

from chemlab_core.blender.controller import BlenderSceneController
from chemlab_core.blender.script_builder import (
    build_chemical_material_script,
    build_rotation_script,
    build_transform_script,
)
from chemlab_core.models import (
    GestureEvent,
    GestureType,
    Handedness,
    IPCRequestType,
    SceneCommand,
    SceneCommandType,
)
from tests.conftest import DummyMockIPCClient


@pytest.mark.unit
def test_script_builder_transform() -> None:
    """Verify transform script generator formats coordinates accurately."""
    script = build_transform_script("Beaker_250ml", dx=0.05, dy=-0.02, dz=0.1)
    assert 'obj = bpy.data.objects.get("Beaker_250ml")' in script
    assert "obj.location.x += 0.050000" in script
    assert "obj.location.y += -0.020000" in script
    assert "obj.location.z += 0.100000" in script


@pytest.mark.unit
def test_script_builder_rotation() -> None:
    """Verify rotation script generator calculates radians properly."""
    script = build_rotation_script("Flask_Erlenmeyer", angle_degrees=45.0, axis="Y")
    assert 'obj = bpy.data.objects.get("Flask_Erlenmeyer")' in script
    assert "math.radians(45.0000)" in script


@pytest.mark.unit
def test_script_builder_chemical_material() -> None:
    """Verify liquid material shader script generator sets Principled BSDF inputs."""
    script = build_chemical_material_script(
        material_name="Mat_Liquid_Iodine",
        color_rgba=(0.85, 0.45, 0.05, 0.85),
        roughness=0.04,
        ior=1.333,
    )
    assert 'mat = bpy.data.materials.get("Mat_Liquid_Iodine")' in script
    assert "bsdf.inputs['Base Color'].default_value = (0.8500, 0.4500, 0.0500, 0.8500)" in script
    assert "bsdf.inputs['Roughness'].default_value = 0.0400" in script


@pytest.mark.unit
def test_controller_dispatch_command(mock_ipc_client: DummyMockIPCClient) -> None:
    """Verify SceneController dispatches formatted code via IPCClient."""
    controller = BlenderSceneController(ipc_client=mock_ipc_client)
    cmd = SceneCommand(
        command_type=SceneCommandType.MOVE_OBJECT,
        target_object="Beaker_500ml",
        transform_delta=(0.0, 0.0, 0.05),
    )

    response = controller.dispatch_command(cmd)
    assert response.status.value == "success"
    assert len(mock_ipc_client.dispatched_requests) == 1

    last_req = mock_ipc_client.dispatched_requests[0]
    assert last_req.type == IPCRequestType.CODE_EXECUTION
    assert last_req.code is not None
    assert 'bpy.data.objects.get("Beaker_500ml")' in last_req.code


@pytest.mark.unit
def test_controller_handle_gesture_pinch(mock_ipc_client: DummyMockIPCClient) -> None:
    """Verify pinch gesture triggers subtle elevation move command."""
    controller = BlenderSceneController(ipc_client=mock_ipc_client)
    gesture = GestureEvent(
        gesture=GestureType.PINCH,
        handedness=Handedness.RIGHT,
        position=(0.5, 0.5, 0.0),
        strength=1.0,
    )

    res = controller.handle_gesture(gesture, target_object="TestTube_01")
    assert res is not None
    assert len(mock_ipc_client.dispatched_requests) == 1
    assert "TestTube_01" in mock_ipc_client.dispatched_requests[0].code


@pytest.mark.unit
def test_controller_handle_gesture_swipe_pour(mock_ipc_client: DummyMockIPCClient) -> None:
    """Verify horizontal swipe triggers container pouring rotation."""
    controller = BlenderSceneController(ipc_client=mock_ipc_client)
    gesture = GestureEvent(
        gesture=GestureType.SWIPE_RIGHT,
        handedness=Handedness.RIGHT,
        position=(0.6, 0.5, 0.0),
        strength=0.9,
    )

    res = controller.handle_gesture(gesture, target_object="GraduatedCylinder")
    assert res is not None
    assert len(mock_ipc_client.dispatched_requests) == 1
    assert "GraduatedCylinder" in mock_ipc_client.dispatched_requests[0].code
    assert "rotation_euler.y" in mock_ipc_client.dispatched_requests[0].code
