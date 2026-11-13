"""Headless Blender MCP bridge.

Runs inside Blender in background mode and exposes the same newline-delimited
JSON socket protocol as ``package/addon/simple_mcp_addon.py`` (default port
8765), so ``blender_mcp_server.mjs`` can drive Blender without a GUI session.

Start with:
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
        --background --python tools/blender/blender_mcp_headless.py

Supported request types:
    {"type": "fetch-scene"}
    {"type": "code", "code": "<python>"}
"""

import contextlib
import io
import json
import os
import socket
import sys
import traceback

import bpy

HOST = os.environ.get("BLENDER_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("BLENDER_MCP_PORT", "9877"))
WORKSPACE = os.environ.get("BLENDER_MCP_WORKSPACE", os.getcwd())


def scene_info():
    info = {"scene_name": bpy.context.scene.name, "objects": []}
    for obj in bpy.context.scene.objects:
        info["objects"].append(
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "dimensions": list(obj.dimensions),
            }
        )
    return info


def execute(code):
    """Execute bpy code on the main thread and capture its output."""
    if not code.strip():
        return {"status": "error", "error": "No code provided"}

    stdout = io.StringIO()
    stderr = io.StringIO()
    namespace = {"bpy": bpy, "__name__": "__main__", "__file__": "<mcp>"}
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(code, "<mcp>", "exec"), namespace)
        return {
            "status": "success",
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }
    except Exception as exc:  # surfaced to the MCP client for diagnosis
        return {
            "status": "error",
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "stdout": stdout.getvalue(),
        }


def handle(request):
    kind = request.get("type", "")
    if kind == "fetch-scene":
        return scene_info()
    if kind == "code":
        return execute(request.get("code", ""))
    return {"status": "error", "error": f"Unknown message type: {kind!r}"}


def serve():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # No SO_REUSEADDR: on Windows it lets a second process silently steal the port.
    server.bind((HOST, PORT))
    server.listen(4)
    print(f"[BlenderMCP] listening on {HOST}:{PORT}", flush=True)

    while True:
        client, _address = server.accept()
        client.settimeout(120.0)
        buffer = ""
        try:
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                try:
                    request = json.loads(buffer)
                except json.JSONDecodeError:
                    continue
                response = handle(request)
                client.sendall((json.dumps(response) + "\n").encode("utf-8"))
                break
        except Exception as exc:
            try:
                client.sendall(
                    (json.dumps({"status": "error", "error": str(exc)}) + "\n").encode(
                        "utf-8"
                    )
                )
            except OSError:
                pass
        finally:
            client.close()


if __name__ == "__main__":
    os.chdir(WORKSPACE)
    serve()
