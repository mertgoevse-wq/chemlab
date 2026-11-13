"""Tiny client for the Blender MCP socket bridge.

Usage:
    python tools/blender/mcp_exec.py script.py
    python tools/blender/mcp_exec.py --fetch
    python tools/blender/mcp_exec.py --code "import bpy; print(len(bpy.data.objects))"
"""

import json
import os
import socket
import sys

HOST = os.environ.get("BLENDER_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("BLENDER_MCP_PORT", "9877"))


def call(payload, timeout=300.0):
    client = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buffer = b""
        while b"\n" not in buffer:
            chunk = client.recv(1 << 16)
            if not chunk:
                break
            buffer += chunk
        return json.loads(buffer.split(b"\n", 1)[0].decode("utf-8"))
    finally:
        client.close()


def main():
    args = sys.argv[1:]
    if not args:
        print("Provide a .py file, --fetch, or --code")
        return 1

    if args[0] == "--fetch":
        payload = {"type": "fetch-scene"}
    elif args[0] == "--code":
        payload = {"type": "code", "code": " ".join(args[1:])}
    else:
        with open(args[0], encoding="utf-8") as handle:
            payload = {"type": "code", "code": handle.read()}

    response = call(payload)
    print(json.dumps(response, indent=2))
    return 0 if response.get("status") in (None, "success") else 2


if __name__ == "__main__":
    sys.exit(main())
