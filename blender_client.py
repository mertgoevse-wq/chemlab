#!/usr/bin/env python3
"""
Blender Live Client CLI for ChemLab MCP Bridge.
Communicates directly with the running Blender GUI via strictly typed IPC requests.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from chemlab_core.config import SETTINGS
from chemlab_core.exceptions import ChemLabError
from chemlab_core.models import IPCRequest, IPCRequestType
from chemlab_core.transport.client import SocketIPCClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("blender_client")


def execute_code_snippet(code: str) -> int:
    """Execute arbitrary Python code inside the running Blender instance."""
    with SocketIPCClient(config=SETTINGS.ipc) as client:
        req = IPCRequest(type=IPCRequestType.CODE_EXECUTION, code=code)
        try:
            res = client.send_request(req)
            print(json.dumps(res.model_dump(), indent=2))
            return 0 if res.status.value in ("success", "executed") else 1
        except ChemLabError as exc:
            logger.error("IPC communication error: %s", exc)
            return 1


def fetch_scene_info() -> int:
    """Retrieve detailed scene object hierarchy from Blender."""
    with SocketIPCClient(config=SETTINGS.ipc) as client:
        req = IPCRequest(type=IPCRequestType.FETCH_SCENE)
        try:
            res = client.send_request(req)
            print(json.dumps(res.model_dump(), indent=2))
            return 0
        except ChemLabError as exc:
            logger.error("Failed to query scene: %s", exc)
            return 1


def ping_bridge() -> int:
    """Check if the Blender MCP socket receiver is listening and responsive."""
    with SocketIPCClient(config=SETTINGS.ipc) as client:
        is_online = client.ping()
        print(f"Blender MCP Bridge Online: {is_online}")
        return 0 if is_online else 1


def save_project_file(filepath: Path | None = None) -> int:
    """Request Blender save its main project file to disk."""
    target_path = filepath or SETTINGS.scene.default_project_path
    code = f'import bpy\nbpy.ops.wm.save_mainfile(filepath=r"{target_path}")\nprint("Saved to {target_path}")'
    return execute_code_snippet(code)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="ChemLab Blender Live Client")
    parser.add_argument("--eval", "-e", type=str, help="Python code string to execute in Blender")
    parser.add_argument(
        "--file", "-f", type=Path, help="Python script file path to execute in Blender"
    )
    parser.add_argument("--scene", "-s", action="store_true", help="Fetch scene object hierarchy")
    parser.add_argument("--save", action="store_true", help="Save the active .blend project")
    parser.add_argument("--ping", action="store_true", help="Ping Blender MCP socket server")

    args = parser.parse_args()

    if args.ping:
        sys.exit(ping_bridge())

    if args.scene:
        sys.exit(fetch_scene_info())

    if args.save:
        sys.exit(save_project_file())

    if args.file:
        if not args.file.exists():
            logger.error("Script file not found: %s", args.file)
            sys.exit(1)
        code_content = args.file.read_text(encoding="utf-8")
        sys.exit(execute_code_snippet(code_content))

    if args.eval:
        sys.exit(execute_code_snippet(args.eval))

    parser.print_help()


if __name__ == "__main__":
    main()
