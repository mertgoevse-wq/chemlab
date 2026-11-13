# Blender MCP — setup and generated assets

## What was broken

The repository shipped an MCP server and a Blender add-on that could not talk to each other:

| Component | Port | Message types |
|---|---|---|
| `blender_mcp_server.mjs` (MCP side) | 9877 | `execute_code`, `get_scene_info` |
| `package/addon/simple_mcp_addon.py` (Blender side) | 8765 | `code`, `fetch-scene` |

Port 8765 is also claimed by the project's own `Blender Live Bridge` add-on, which auto-starts
inside Blender as a Python HTTP server (`TradeOraControl`). With `SO_REUSEADDR` the MCP bridge
appeared to bind but every request was answered by the wrong server.

## What was fixed

1. `blender_mcp_server.mjs` now reads `BLENDER_HOST` / `BLENDER_PORT` and maps MCP tool names
   onto the add-on protocol (`execute_code` → `{type:"code", code}`, `get_scene_info` →
   `{type:"fetch-scene"}`). Responses are parsed up to the newline frame.
2. `.mcp.json` points the server at **127.0.0.1:9877**, clear of the live bridge.
3. `tools/blender/blender_mcp_headless.py` runs the same protocol inside headless Blender with
   no GUI, and binds **without** `SO_REUSEADDR` so a second process cannot steal the port.
4. `tools/blender/mcp_exec.py` is a small CLI client for scripts and one-liners.

## Running it

```bash
# Start Blender with the MCP bridge (background)
BLENDER_MCP_PORT=9877 \
BLENDER_MCP_WORKSPACE="C:/Users/Win11 Pro/Desktop/chemlab" \
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
  --background --python tools/blender/blender_mcp_headless.py

# Inspect the live scene
BLENDER_MCP_PORT=9877 .venv/Scripts/python.exe tools/blender/mcp_exec.py --fetch

# Run arbitrary bpy code
BLENDER_MCP_PORT=9877 .venv/Scripts/python.exe tools/blender/mcp_exec.py \
  --code "import bpy; print(len(bpy.data.objects))"
```

The GUI path still works: enable the add-on (`View3D > Sidebar > MCP > Start`) and set
`BLENDER_PORT` to whatever the add-on reports.

## Assets generated through the bridge

`tools/blender/build_lab_textures.py` produces seamless 1024×1024 PBR maps using periodic
value noise inside Blender's image API, then saves a source `.blend`:

| File | Use |
|---|---|
| `game/assets/textures/floor_epoxy_albedo.png` / `_normal.png` | `LabHub._mat_floor` (uv 8×8) |
| `game/assets/textures/steel_brushed_albedo.png` / `_normal.png` | `LabHub._mat_pillar` / `_mat_arch` (uv 2×2) |
| `assets/blender/lab_textures.blend` | editable source datablocks |

`game/assets/textures/manifest.json` now marks both materials `ready` with their paths.
`lab_hub.gd` loads them through `ResourceLoader.exists()` guards, so a checkout without the
generated files still renders with flat colours.

## Conventions for future Blender work

- Units are metres, Z-up in Blender (glTF export converts to Y-up automatically).
- Keep apparatus pivots at bench-contact height so `apparatus_practicum.gd` scales behave.
- Export only `.glb`; keep the `.blend` source under `assets/blender/`.
- Bake to 1024 or 2048; the target GPU is Intel Iris Xe with a 60 FPS budget.
