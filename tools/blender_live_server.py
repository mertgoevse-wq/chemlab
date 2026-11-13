"""
ChemLab Blender Live Server (Port 9877). Legacy helper: the MCP headless bridge
uses the same port, so run only one of them at a time.
Runs inside Blender to communicate with blender_mcp_server.mjs / Claude Code.
Provides live code execution and scene inspection with viewport redraw.
"""

import io
import json
import logging
import os
import queue
import socket
import sys
import threading
import time
import traceback

import bpy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BlenderLiveServer")

HOST = "127.0.0.1"
PORT = int(os.environ.get("BLENDER_LIVE_PORT", "9877"))

# Command queue for thread-safe execution on Blender main thread
_command_queue = queue.Queue()
_server_running = True
_server_sock = None


def _execute_in_main_thread(command_type, params):
    """Executes bpy operations inside Blender's main loop context."""
    if command_type == "execute_code":
        code_str = params.get("code", "")
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        err = None

        try:
            # Execute in globals with bpy pre-imported
            exec(code_str, {"bpy": bpy, "__name__": "__main__"})
        except Exception as e:
            err = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # Tag 3D viewports for redraw
        try:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "VIEW_3D":
                        area.tag_redraw()
        except Exception:
            pass

        return {
            "status": "error" if err else "success",
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue() or (err if err else ""),
        }

    elif command_type == "get_scene_info":
        objects = []
        for obj in bpy.data.objects:
            mats = [slot.material.name for slot in obj.material_slots if slot.material]
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(v, 4) for v in obj.location],
                "dimensions": [round(v, 4) for v in obj.dimensions],
                "materials": mats,
                "visible": obj.visible_get() if hasattr(obj, "visible_get") else True,
            })

        return {
            "status": "success",
            "objects": objects,
            "total_objects": len(objects),
            "scene_name": bpy.context.scene.name if bpy.context.scene else "",
            "render_engine": bpy.context.scene.render.engine if bpy.context.scene else "",
        }

    else:
        return {"status": "error", "message": f"Unknown command type: {command_type}"}


def _timer_callback():
    """Polls queue from Blender's main timer."""
    while not _command_queue.empty():
        try:
            cmd_type, params, result_queue = _command_queue.get_nowait()
            result = _execute_in_main_thread(cmd_type, params)
            result_queue.put(result)
        except queue.Empty:
            break
        except Exception as e:
            logger.exception("Error in timer callback")

    return 0.05  # Repeat every 50ms


def _client_handler(client_sock, client_addr):
    """Handles an individual client connection."""
    client_sock.settimeout(60.0)
    buffer = ""

    try:
        while _server_running:
            chunk = client_sock.recv(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    payload = json.loads(line)
                    cmd_type = payload.get("type", "")
                    params = payload.get("params", {})

                    result_queue = queue.Queue()
                    _command_queue.put((cmd_type, params, result_queue))

                    # Wait for execution on main thread
                    result = result_queue.get(timeout=30.0)
                    response_data = json.dumps(result) + "\n"
                    client_sock.sendall(response_data.encode("utf-8"))
                except Exception as e:
                    err_resp = json.dumps({"status": "error", "message": str(e)}) + "\n"
                    client_sock.sendall(err_resp.encode("utf-8"))

    except Exception as e:
        logger.debug("Client handler ended for %s: %s", client_addr, e)
    finally:
        try:
            client_sock.close()
        except Exception:
            pass


def _listener_loop():
    """Socket listener thread."""
    global _server_sock, _server_running
    _server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        _server_sock.bind((HOST, PORT))
        _server_sock.listen(5)
        _server_sock.settimeout(1.0)
        logger.info(f"Blender Live Server listening on {HOST}:{PORT}")
        print(f"=== Blender Live Server Listening on {HOST}:{PORT} ===")

        while _server_running:
            try:
                client_sock, client_addr = _server_sock.accept()
                t = threading.Thread(
                    target=_client_handler,
                    args=(client_sock, client_addr),
                    daemon=True,
                )
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    except Exception as e:
        logger.error(f"Failed to start Blender Live Server on {HOST}:{PORT}: {e}")
    finally:
        if _server_sock:
            try:
                _server_sock.close()
            except Exception:
                pass


def start_server():
    """Entry point called inside Blender."""
    # Register timer for main-thread execution
    if not bpy.app.timers.is_registered(_timer_callback):
        bpy.app.timers.register(_timer_callback, persistent=True)

    thread = threading.Thread(target=_listener_loop, daemon=True, name="BlenderLive-Listener")
    thread.start()
    print("ChemLab Blender Live Server thread started successfully.")


if __name__ == "__main__" or "bpy" in sys.modules:
    start_server()
