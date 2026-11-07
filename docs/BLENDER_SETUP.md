# ChemLab: Blender 5.2 Authoring & EEVEE Next Setup Guide
**Authoring Tool:** Blender 5.2.3 LTS  
**Target Engine:** Godot 4.7.2 (Compatibility / OpenGL 3.3 / Forward+)  
**Target Hardware Baseline:** Intel Iris Xe 80 EU (128 MB dedicated VRAM / 6 GB shared RAM staging)  
**Authoritative Blendfile:** `chemlab.blend` (Repository Root)  
**Document Version:** 1.0.0 (Production Release)

---

## 1. System Prerequisites & Environment

### 1.1 Software Installation
- **Blender Version:** **Blender 5.2.3 LTS** (or 5.2.x).
  - Executable Path: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
  - Launcher: `C:\Program Files\Blender Foundation\Blender 5.2\blender-launcher.exe`
- **Operating System:** Windows 11 Pro 64-bit (WDDM 3.0+ graphics driver).
- **Python Runtime:** Python 3.12+ (system runtime) / Python 3.11 embedded inside Blender.
- **Node.js:** Node.js LTS (v20+ or v22+) for optional MCP bridge tooling.

### 1.2 Hardware Profile (Dell Latitude 5530 Baseline)
- **CPU:** Intel Core i5-1245U (10 cores / 12 threads).
- **GPU:** Intel Iris Xe Graphics G7 (80 Execution Units, 1.20 GHz peak).
- **Memory:** 16 GB Dual-Channel DDR4-3200 MHz (51.2 GB/s unified memory bandwidth).
- **VRAM Slice:** 128 MB dedicated video memory (WDDM reported). Dynamic shared system memory up to 8,192 MB.

---

## 2. Opening & Working with `chemlab.blend`

The master scene file `chemlab.blend` contains the authoritative models, materials, cleanroom architecture, and spatial HUD assets.

### 2.1 Interactive GUI Launch

To launch Blender with `chemlab.blend` from PowerShell or Git Bash:

```bash
# PowerShell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" "C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend"

# Git Bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" "C:/Users/Win11 Pro/Desktop/chemlab/chemlab.blend"
```

### 2.2 Headless Command-Line Execution

For automated asset audits, validation, and batch exports without starting the GUI:

```bash
# Run headless inspection script
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend" --python-expr "
import bpy
print('Blender Version:', bpy.app.version_string)
print('Total Scene Objects:', len(bpy.data.objects))
print('Total Materials:', len(bpy.data.materials))
"
```

### 2.3 Scene Hierarchy & Collections Structure

The scene in `chemlab.blend` is strictly partitioned into functional collections:

```
Scene Collection
├── 01_Architecture          # Cleanroom epoxy floor, baseboards, acoustic ceiling, LED panels
├── 02_Furniture             # Island workbenches, granite balance slab, cabinetry, reagent racks
├── 03_Safety_Equipment      # Fume hood assembly, sash glass, exhaust plenum, wash sink, carboys
├── 04_Apparatus_Chemicals   # Beakers (150/400 mL), Erlenmeyers, Burets, Burner, Stirrer, Balance
├── 05_Cameras               # Workstation detail camera, Fume hood task view, Overview camera
└── 06_UI_HUD_Spatial        # 3D spatial labels, reagent identification tags, anchor dots
```

**Workflow Rule:** Never place new objects directly in the root `Scene Collection`. Always link new apparatus to `04_Apparatus_Chemicals` or architectural elements to `01_Architecture`.

---

## 3. EEVEE Next Engine Configuration for Intel Iris Xe

Blender 5.2 LTS introduces the redesigned **EEVEE Next** viewport engine. To achieve a stable **60 FPS** on Intel Iris Xe graphics while rendering glass transmission, liquid refractions, and cleanroom lighting, the engine settings must be configured to match `src/chemlab/graphics/iris_xe_optimizer.py`.

### 3.1 Render Properties Configuration

1. In the **Properties** panel, select the **Render** tab.
2. Set **Render Engine** to `EEVEE Next` (or `BLENDER_EEVEE`).
3. Set **Sampling**:
   - **Viewport Samples:** `24` *(halved from default 64 to preserve fill-rate)*
   - **Render Samples:** `64`
4. Configure **Fast Global Illumination (Fast GI)**:
   - **Method:** `GLOBAL_ILLUMINATION`
   - **Resolution:** `2` *(Half-resolution screen-space raymarching)*
   - **Ray Count:** `2`
   - **Step Count:** `8`
   - **Quality:** `0.25`
   - **Bias:** `0.05`
5. Configure **Raytracing / Screen Trace Options (`RaytraceEEVEE`)**:
   - **Resolution Scale:** `2` *(Enables half-resolution tracing: `enable_half_res_trace = True`)*
   - **Screen Trace Quality:** `0.25`
   - **Max Roughness:** `0.5`
   - **Use Backface Hit:** `True` *(Critical for double-walled glassware and meniscus refraction)*
   - **Denoise Temporal:** `True`
   - **Denoise Spatial:** `True`
6. Configure **Shadows**:
   - **Shadow Pool Size:** `512 MB`
   - **Shadow Cube Size:** `1024 px` *(Clamped from 2048/4096 to prevent UMA bus saturation)*
   - **Shadow Step Count:** `6`
7. Configure **Volumetrics**:
   - **Tile Size:** `4 px` *(Coarse grid for Bunsen flame smoke and reaction steam)*

### 3.2 Python Script to Apply Iris Xe Settings Automatically

You can apply these exact settings programmatically inside Blender:

```python
import bpy

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderEngine.bl_rna.properties['engine'].enum_items else 'BLENDER_EEVEE'

eevee = scene.eevee
eevee.taa_samples = 24
eevee.taa_render_samples = 64
eevee.shadow_pool_size = 512
eevee.shadow_cube_size = 1024
eevee.shadow_step_count = 6

# Fast GI
eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'
eevee.fast_gi_resolution = 2
eevee.fast_gi_ray_count = 2
eevee.fast_gi_step_count = 8
eevee.fast_gi_quality = 0.25
eevee.fast_gi_bias = 0.05

# Raytrace options
rto = getattr(eevee, 'ray_tracing_options', None)
if rto:
    rto.resolution_scale = 2
    rto.screen_trace_quality = 0.25
    rto.trace_max_roughness = 0.5
    rto.use_backface_hit = True
    rto.denoise_temporal = True

print("Intel Iris Xe EEVEE Next performance tier applied successfully.")
```

### 3.3 Color Management
- **Display Device:** `sRGB`
- **View Transform:** `AgX` (Blender 4/5 default, preserves highlight roll-off on glassware specular highlights)
- **Look:** `Medium High Contrast`
- **Exposure:** `0.0`
- **Gamma:** `1.0`

---

## 4. Export Pipeline to Godot (`game/assets/`)

Godot 4.7.2 consumes binary glTF 2.0 (`.glb`) files. Assets exported from Blender are placed in `game/assets/` under appropriate subdirectories.

### 4.1 Export Directory Target Layout

```
game/assets/
├── apparatus/
│   ├── SM_Beaker_150ml.glb
│   ├── SM_Beaker_400ml.glb
│   ├── SM_Erlenmeyer_250ml.glb
│   ├── SM_Erlenmeyer_500ml.glb
│   ├── SM_TitrationBuret_50ml.glb
│   ├── SM_BunsenBurner.glb
│   ├── SM_MagneticStirrer.glb
│   └── SM_AnalyticalBalance.glb
├── architecture/
│   ├── SM_Cleanroom_Shell.glb
│   ├── SM_Workbench_Central.glb
│   ├── SM_FumeHood_Station.glb
│   └── SM_Safety_Station.glb
└── textures/
    ├── T_Apparatus_Decals_BC.png
    └── T_Furniture_ORM.png
```

### 4.2 Standard glTF 2.0 Export Settings
When exporting manually via **File → Export → glTF 2.0 (.glb/.gltf)**:
- **Format:** `glTF Binary (.glb)`
- **Include:**
  - `Limit to Selected Objects`: Checked
  - `Custom Properties`: Checked
- **Transform:**
  - `+Y Up`: Checked (matches Godot 3D coordinate space)
- **Geometry:**
  - `Apply Modifiers`: Checked
  - `UVs`: Checked
  - `Normals`: Checked
  - `Tangents`: Checked (required for high-precision normal mapping)
  - `Vertex Colors`: Unchecked (unless specifically baking vertex AO)
- **Compression:**
  - `Draco Mesh Compression`: **Checked**
  - `Compression Level`: `6`
  - `Position Quantization`: `14 bits`
  - `Normal Quantization`: `10 bits`
  - `TexCoord Quantization`: `12 bits`
- **Materials:**
  - `Export Materials`: `Export`
  - `Images`: `Automatic`

### 4.3 Automated Batch Export Script (`tools/export_assets_to_godot.py`)

A dedicated Python script automates exporting apparatus collections from `chemlab.blend` into `game/assets/apparatus/`:

```bash
# Execute headless automated export
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend" --python "C:\Users\Win11 Pro\Desktop\chemlab\tools\export_assets_to_godot.py"
```

### 4.4 Material Binding in Godot 4

When Godot 4 imports `.glb` files, materials must be mapped to the project's custom shaders:
1. **Borosilicate Glass Surfaces**: Override the imported material slot with a `ShaderMaterial` referencing `res://shaders/glass_shader.gdshader`.
   - Set `glass_color = Color(0.96, 0.98, 1.0, 0.08)`
   - Set `ior = 1.458`
   - Set `roughness = 0.015`
2. **Liquid Volumes**: Override the interior liquid mesh material with a `ShaderMaterial` referencing `res://shaders/liquid_shader.gdshader`.
   - Configure `container_height` and `container_radius` to match physical vessel dimensions.
   - Bind `liquid_color`, `ior`, and `turbidity` dynamically from the reagent state machine.

---

## 5. Cinematic night grade (headless)

`tools/blender_cinematic_grade.py` is the reproducible art-direction pass over the master scene. It does not overwrite `chemlab.blend`; it writes `chemlab_cinematic.blend` and three graded stills.

```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b chemlab.blend \
  --python tools/blender_cinematic_grade.py
```

What it changes, and why:

| Step | Reason |
|---|---|
| Regrades albedo (walls 0.30, floor 0.04, ceiling 0.09, casework 0.12) | The source is authored near-white (walls 0.92, floor 0.75). Under any bright rig that reads as a white box. |
| Procedural grain only on floor and casework | Albedo noise on walls at room scale reads as damp concrete, not cleanroom. |
| Ceiling panels to standby, hood task light kept at 5.0 | Night shift: the fixtures are off, the work light is the story. |
| World volume haze (density 0.006) | Beams need a medium. A volume **mesh** also renders its opaque surface and swallows the frame — keep haze on the world. |
| AgX, exposure 0.55, three area lights + strip | Preserves highlight roll-off on glass and stainless; the strip catches beaker rims and the meniscus. |
| Fume-hood sash retrofit | The upper body was a closed box whose front face hid the interior, so every frontal shot was a blank panel. The face becomes glass and gets a steel frame and sash rail. |

Outputs: `docs/screenshots/cine_establish.png`, `cine_bench.png`, `cine_hood.png` (1600×900).

## 6. Blender MCP Bridge & Automation Status

The ChemLab repository includes an MCP (Model Context Protocol) integration for bidirectional communication between Claude Code and the Blender GUI:
- `blender_client.py`: Python CLI client utilizing socket IPC.
- `blender_live_bridge.py`: Python server and queue handler running inside Blender's embedded runtime (port 8765).
- `blender_mcp_server.mjs`: Node.js Stdio MCP server bridging Claude Code tool calls to Blender socket commands (port 9876).

### 5.1 Current Connection Status: verified live
With Blender open and `chemlab_startup.py` initialised, the addon listens on `9876` and accepts JSON-line RPC (`execute_code`, `get_scene_info`). `.mcp.json` in the repository root registers it for MCP clients:

```json
{"mcpServers": {"blender-live": {"command": "node", "args": ["blender_mcp_server.mjs"],
  "env": {"BLENDER_HOST": "127.0.0.1", "BLENDER_PORT": "9876"}}}}
```

A verified round trip ran scene edits, an EEVEE still, and `save_as_mainfile` inside the running GUI session.

**Pipeline Policy:**
- The asset pipeline **must never block** on the live bridge.
- The reproducible workflow for validation and exporting is **headless execution** (`blender.exe -b chemlab.blend --python <script.py>`).
- The MCP bridge is for interactive sessions where a human is watching the viewport.

### 5.2 Launching the Live Bridge for Interactive Sessions

When interactive AI pair-programming inside the Blender GUI is desired:
1. Open `chemlab.blend` in Blender 5.2.
2. In Blender's **Scripting** workspace, open `C:\Users\Win11 Pro\Desktop\chemlab\blender_live_bridge.py`.
3. Click **Run Script** (or press `Alt + P`).
   - The system console will display: `[INFO] Blender Live Bridge listening on 127.0.0.1:8765`.
   - The queue timer runs on Blender's main thread every 16 ms to safely execute scene operations without threading deadlocks.
4. From an external terminal or Claude Code, test the live connection:
   ```bash
   python blender_client.py --ping
   # Expected output: Blender MCP Bridge Online: True
   ```
5. Fetch the live scene object hierarchy:
   ```bash
   python blender_client.py --scene
   ```
