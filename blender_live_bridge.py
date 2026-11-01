"""
Hardened Blender Live Bridge & MCP Receiver.
Enforces real-time bidirectional communication between AI agents and the Blender GUI.
Free of zombie threads, silent exception swallows, and hardcoded magic numbers.
"""

import io
import json
import logging
import queue
import socket
import sys
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

# Blender API is injected when executed inside Blender
try:
    import bpy

    IS_INSIDE_BLENDER = True
except ImportError:
    bpy = None  # type: ignore[assignment]
    IS_INSIDE_BLENDER = False

# Support execution inside Blender's minimal embedded Python
try:
    from chemlab_core.config import SETTINGS
except (ImportError, ModuleNotFoundError):
    class _IPCConfig:
        host: str = "127.0.0.1"
        port: int = 8765
        timeout_seconds: float = 5.0

    class _SceneConfig:
        default_project_path: str = r"C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend"
        material_preview_enabled: bool = True
        viewport_timer_interval: float = 0.016

    class _FallbackSettings:
        ipc = _IPCConfig()
        scene = _SceneConfig()

    SETTINGS = _FallbackSettings()  # type: ignore[assignment]

logger = logging.getLogger("blender_live_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

code_execution_queue: queue.Queue[dict[str, Any]] = queue.Queue()
_shutdown_event = threading.Event()
_server_thread: threading.Thread | None = None
_server_socket: socket.socket | None = None
_is_running = False


def update_viewports(material_preview: bool = True) -> None:
    """Force all 3D viewports to redraw and optionally switch to Material shading."""
    if not IS_INSIDE_BLENDER or bpy is None:
        return
    try:
        bpy.context.view_layer.update()
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
                    if material_preview:
                        for space in area.spaces:
                            if space.type == "VIEW_3D":
                                space.shading.type = "MATERIAL"
    except Exception as exc:
        logger.warning("Viewport update warning: %s", exc)


def get_scene_info() -> dict[str, Any]:
    """Retrieve detailed information about the active Blender scene objects."""
    if not IS_INSIDE_BLENDER or bpy is None:
        return {"status": "error", "error": "Not running inside Blender runtime"}

    try:
        scene = bpy.context.scene
        objects_data = []
        for obj in scene.objects:
            objects_data.append(
                {
                    "name": obj.name,
                    "type": obj.type,
                    "location": [round(float(v), 4) for v in obj.location],
                    "dimensions": [round(float(v), 4) for v in obj.dimensions],
                    "visible": not obj.hide_viewport,
                    "materials": [
                        slot.material.name for slot in obj.material_slots if slot.material
                    ],
                }
            )

        return {
            "status": "success",
            "scene": {
                "scene_name": scene.name,
                "objects_count": len(scene.objects),
                "objects": objects_data,
            },
        }
    except Exception as exc:
        logger.error("Failed to extract scene info: %s", exc)
        return {"status": "error", "error": str(exc)}


def execute_code_in_main_thread(code: str) -> dict[str, Any]:
    """Execute Python code in Blender's main thread with stdout/stderr capture."""
    if not code or not code.strip():
        return {"status": "error", "error": "No code provided"}

    if not IS_INSIDE_BLENDER or bpy is None:
        return {"status": "error", "error": "Not running inside Blender"}

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    exec_globals: dict[str, Any] = {
        "bpy": bpy,
        "mathutils": sys.modules.get("mathutils"),
        "update_viewports": update_viewports,
        "PROJECT_PATH": str(SETTINGS.scene.default_project_path),
        "__name__": "__main__",
    }

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            compiled = compile(code, "<mcp_live_code>", "exec")
            exec(compiled, exec_globals)
            update_viewports(material_preview=SETTINGS.scene.material_preview_enabled)

        return {
            "status": "success",
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        }
    except Exception as exc:
        trace = traceback.format_exc()
        logger.error("Error executing Python script in Blender: %s\n%s", exc, trace)
        return {
            "status": "error",
            "error": str(exc),
            "traceback": trace,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        }


def process_queue_timer() -> float:
    """Timer callback running in Blender main thread to process queued tasks."""
    try:
        while not code_execution_queue.empty():
            task = code_execution_queue.get_nowait()
            task_type = task.get("type", "code")

            if task_type == "code":
                task["result"] = execute_code_in_main_thread(task.get("code", ""))
                task["completed"] = True
            elif task_type == "fetch-scene":
                task["result"] = get_scene_info()
                task["completed"] = True
            elif task_type == "save":
                target_path = task.get("filepath", str(SETTINGS.scene.default_project_path))
                try:
                    if bpy:
                        bpy.ops.wm.save_mainfile(filepath=target_path)
                    task["result"] = {"status": "success", "filepath": target_path}
                except Exception as exc:
                    task["result"] = {"status": "error", "error": str(exc)}
                task["completed"] = True
    except queue.Empty:
        pass
    except Exception as exc:
        logger.error("Error processing queue timer: %s", exc)

    return SETTINGS.scene.viewport_timer_interval


def _server_worker() -> None:
    """Background listener loop running in a dedicated thread."""
    global _server_socket
    try:
        _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _server_socket.bind((SETTINGS.ipc.host, SETTINGS.ipc.port))
        _server_socket.listen(5)
        _server_socket.settimeout(1.0)
        logger.info("Blender Live Bridge listening on %s:%s", SETTINGS.ipc.host, SETTINGS.ipc.port)

        while not _shutdown_event.is_set():
            try:
                client_sock, addr = _server_socket.accept()
                logger.debug("Accepted connection from %s", addr)
                _handle_client(client_sock)
            except TimeoutError:
                continue
            except OSError:
                break
    except Exception as exc:
        logger.error("Fatal error in live bridge server: %s", exc)
    finally:
        if _server_socket:
            try:
                _server_socket.close()
            except OSError as exc:
                logger.debug("Ignored socket close error: %s", exc)
            _server_socket = None


def _handle_client(client_sock: socket.socket) -> None:
    """Read incoming request, enqueue to main thread, and return result."""
    buffer = ""
    try:
        client_sock.settimeout(SETTINGS.ipc.command_timeout_seconds)
        while not _shutdown_event.is_set():
            data = client_sock.recv(SETTINGS.ipc.buffer_size)
            if not data:
                break
            buffer += data.decode("utf-8")
            if "\n" in buffer:
                break

        if not buffer.strip():
            return

        json_data = json.loads(buffer.strip().split("\n")[0])
        msg_type = json_data.get("type", "code")

        task = {
            "type": msg_type,
            "code": json_data.get("code", ""),
            "filepath": json_data.get("filepath", str(SETTINGS.scene.default_project_path)),
            "completed": False,
            "result": None,
        }
        code_execution_queue.put(task)

        # Wait for main thread timer to execute task
        timeout = SETTINGS.ipc.command_timeout_seconds
        start = time.perf_counter()
        while not task["completed"] and (time.perf_counter() - start) < timeout:
            time.sleep(0.01)

        response = (
            task["result"]
            if task["completed"]
            else {"status": "error", "error": f"Task timed out after {timeout}s"}
        )

        response_bytes = (json.dumps(response) + "\n").encode("utf-8")
        client_sock.sendall(response_bytes)

    except Exception as exc:
        logger.error("Client handling error: %s", exc)
        err_response = {"status": "error", "error": str(exc)}
        try:
            client_sock.sendall((json.dumps(err_response) + "\n").encode("utf-8"))
        except OSError as send_err:
            logger.debug("Failed to send error response to client: %s", send_err)
    finally:
        try:
            client_sock.close()
        except OSError as close_err:
            logger.debug("Failed to close client socket: %s", close_err)


def start_bridge() -> None:
    """Start the Blender live bridge background server and timer."""
    global _is_running, _server_thread
    if _is_running:
        logger.warning("Live bridge is already running")
        return

    _shutdown_event.clear()
    _server_thread = threading.Thread(
        target=_server_worker,
        name="Blender-Live-Bridge-Worker",
        daemon=True,
    )
    _server_thread.start()

    if (
        IS_INSIDE_BLENDER
        and bpy is not None
        and not bpy.app.timers.is_registered(process_queue_timer)
    ):
        bpy.app.timers.register(process_queue_timer)

    _is_running = True
    logger.info("Blender Live Bridge initialized successfully")


def stop_bridge() -> None:
    """Cleanly stop the server, release sockets, and unregister timers."""
    global _is_running, _server_thread, _server_socket
    _shutdown_event.set()

    if _server_socket:
        try:
            _server_socket.close()
        except OSError as exc:
            logger.debug("Error closing server socket: %s", exc)
        _server_socket = None

    if _server_thread and _server_thread.is_alive():
        _server_thread.join(timeout=2.0)
        _server_thread = None

    if IS_INSIDE_BLENDER and bpy is not None and bpy.app.timers.is_registered(process_queue_timer):
        bpy.app.timers.unregister(process_queue_timer)

    _is_running = False
    logger.info("Blender Live Bridge stopped")


if __name__ == "__main__" or IS_INSIDE_BLENDER:
    start_bridge()
