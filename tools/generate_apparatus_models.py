r"""
Blender 5.x Headless Procedural Generator for Laboratory Apparatus Suite.
Generates photorealistic, game-ready GLB assets with PBR materials for Athanor Ascension:
- SM_Rotovap.glb (Rotary Evaporator)
- SM_SchlenkLine.glb (Dual-Manifold Inert Gas / Vacuum Schlenk Line)
- SM_SoxhletExtractor.glb (Soxhlet Extraction System with Condenser)
- SM_HPLC_System.glb (Modular High-Performance Liquid Chromatograph)
- SM_Centrifuge.glb (High-Speed Benchtop Microcentrifuge)
- SM_UVVis_Spectrophotometer.glb (Dual-Beam UV-Vis Spectrometer)
- SM_Glovebox.glb (Inert Atmosphere Glovebox with Airlock Antechamber)
- SM_AnalyticalBalance.glb (Precision 4-Decimal Draft-Shield Balance)

Execution:
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python tools/generate_apparatus_models.py
"""

import os
import sys
import math
from pathlib import Path
import bpy
from mathutils import Vector

# When executed through the Blender MCP bridge __file__ is "<mcp>", so resolve
# against the workspace explicitly instead of the script location.
WORKSPACE = Path(os.environ.get("ATHANOR_WORKSPACE", Path.cwd())).resolve()
OUTPUT_DIR = WORKSPACE / "game" / "assets" / "apparatus"
if not (WORKSPACE / "game" / "project.godot").exists():
    raise RuntimeError(f"Not an Athanor workspace: {WORKSPACE}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_scene():
    """Removes all objects and meshes from the current scene."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)


def create_pbr_material(name, base_color, metallic=0.0, roughness=0.5, transmission=0.0, ior=1.45, emission_color=(0,0,0,1), emission_strength=0.0):
    """Creates a Principled BSDF material configured for PBR glTF export."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        nodes.get("Material Output").inputs[0].links.new(bsdf.outputs[0])

    # Assign inputs safely across Blender versions
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = base_color
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = ior
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def setup_materials():
    """Builds a standard dictionary of photorealistic laboratory materials."""
    return {
        "glass": create_pbr_material("M_BorosilicateGlass", (0.85, 0.92, 0.96, 1.0), metallic=0.05, roughness=0.1, transmission=0.85, ior=1.47),
        "amber_glass": create_pbr_material("M_AmberGlass", (0.45, 0.22, 0.05, 1.0), metallic=0.05, roughness=0.15, transmission=0.6, ior=1.52),
        "stainless": create_pbr_material("M_StainlessSteel", (0.82, 0.84, 0.86, 1.0), metallic=0.92, roughness=0.22),
        "chassis_dark": create_pbr_material("M_ChassisDark", (0.12, 0.14, 0.17, 1.0), metallic=0.3, roughness=0.45),
        "chassis_light": create_pbr_material("M_ChassisLight", (0.88, 0.90, 0.92, 1.0), metallic=0.1, roughness=0.35),
        "acrylic_clear": create_pbr_material("M_AcrylicClear", (0.92, 0.95, 0.98, 1.0), metallic=0.0, roughness=0.08, transmission=0.9, ior=1.49),
        "rubber_black": create_pbr_material("M_ButylRubber", (0.05, 0.05, 0.06, 1.0), metallic=0.0, roughness=0.85),
        "brass": create_pbr_material("M_BrassValve", (0.85, 0.68, 0.25, 1.0), metallic=0.85, roughness=0.3),
        "display_screen": create_pbr_material("M_DisplayScreen", (0.02, 0.08, 0.05, 1.0), metallic=0.0, roughness=0.2, emission_color=(0.1, 0.85, 0.4, 1.0), emission_strength=1.5),
        "accent_cyan": create_pbr_material("M_AccentCyan", (0.15, 0.75, 0.85, 1.0), metallic=0.2, roughness=0.3),
        "accent_amber": create_pbr_material("M_AccentAmber", (0.95, 0.55, 0.1, 1.0), metallic=0.2, roughness=0.3),
        "liquid_blue": create_pbr_material("M_SolventBlue", (0.2, 0.45, 0.85, 1.0), metallic=0.0, roughness=0.12, transmission=0.7),
        "liquid_gold": create_pbr_material("M_ExtractGold", (0.85, 0.65, 0.15, 1.0), metallic=0.0, roughness=0.15, transmission=0.65),
        "ptfe_white": create_pbr_material("M_PTFE_White", (0.95, 0.95, 0.95, 1.0), metallic=0.0, roughness=0.25),
        "liquid_biphasic_organic": create_pbr_material("M_BiphasicOrganic", (0.90, 0.72, 0.22, 1.0), metallic=0.0, roughness=0.1, transmission=0.75),
        "liquid_biphasic_aqueous": create_pbr_material("M_BiphasicAqueous", (0.82, 0.92, 0.98, 1.0), metallic=0.0, roughness=0.1, transmission=0.85),
        "superconductor_cryo": create_pbr_material("M_SuperconductorCryo", (0.88, 0.91, 0.94, 1.0), metallic=0.95, roughness=0.12),
        "ceramic_white": create_pbr_material("M_CeramicWhite", (0.96, 0.96, 0.95, 1.0), metallic=0.0, roughness=0.18),
        "epoxy_black": create_pbr_material("M_EpoxyResinBlack", (0.08, 0.08, 0.09, 1.0), metallic=0.1, roughness=0.35),
    }


def _detail_material(name, color, metallic=0.0, roughness=0.4, emission=None):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if emission is not None:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = 4.0
    return mat


def _scene_bounds(meshes):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
    return lo, hi


def _add_detail_box(name, size, location, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def detail_pass():
    """Adds game-ready detail that every apparatus benefits from.

    Bevel + weighted normals remove the hard CG edge look; a rating plate,
    panel screws, a status LED and a cable gland give the silhouettes readable
    industrial detail at gameplay distance. Geometry stays low-poly: the bevel
    is 2 segments and the props are a few dozen triangles each.
    """
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        return

    lo, hi = _scene_bounds(meshes)
    dims = hi - lo
    if min(dims.x, dims.y, dims.z) < 0.02:
        return

    for obj in meshes:
        obj_dims = obj.dimensions
        if min(obj_dims.x, obj_dims.y, obj_dims.z) < 0.01 or len(obj.data.polygons) < 8:
            continue
        bevel = obj.modifiers.new("DetailBevel", 'BEVEL')
        bevel.width = min(0.0035, min(obj_dims) * 0.04)
        bevel.segments = 2
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = math.radians(30.0)
        normal = obj.modifiers.new("DetailNormals", 'WEIGHTED_NORMAL')
        normal.keep_sharp = True

    steel = _detail_material("M_DetailSteel", (0.55, 0.57, 0.60, 1.0), 0.85, 0.28)
    dark = _detail_material("M_DetailPlate", (0.05, 0.06, 0.07, 1.0), 0.4, 0.45)
    led = _detail_material("M_DetailLED", (0.10, 0.85, 0.95, 1.0), 0.0, 0.2, (0.10, 0.85, 0.95, 1.0))

    centre_x = (lo.x + hi.x) * 0.5
    front_y = lo.y - 0.0015

    # Rating plate and status LED on the front face.
    plate_w = max(0.06, min(dims.x * 0.22, 0.24))
    plate_h = max(0.025, min(dims.z * 0.06, 0.05))
    _add_detail_box(
        "Detail_RatingPlate",
        (plate_w, 0.002, plate_h),
        (centre_x, front_y, lo.z + dims.z * 0.42),
        dark,
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=max(0.006, min(dims.x, dims.z) * 0.012),
        location=(hi.x - dims.x * 0.06, front_y - 0.002, hi.z - dims.z * 0.08),
    )
    indicator = bpy.context.active_object
    indicator.name = "Detail_StatusLED"
    indicator.data.materials.append(led)

    # Panel screws at the four front corners.
    screw_r = max(0.004, min(dims.x, dims.z) * 0.008)
    for sx in (lo.x + dims.x * 0.06, hi.x - dims.x * 0.06):
        for sz in (lo.z + dims.z * 0.08, hi.z - dims.z * 0.08):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=screw_r, depth=0.003, location=(sx, front_y - 0.001, sz)
            )
            screw = bpy.context.active_object
            screw.rotation_euler[0] = math.radians(90.0)
            screw.data.materials.append(steel)

    # Cable gland at the rear.
    bpy.ops.mesh.primitive_cylinder_add(
        radius=max(0.008, dims.x * 0.012),
        depth=0.02,
        location=(centre_x, hi.y + 0.005, lo.z + dims.z * 0.12),
    )
    gland = bpy.context.active_object
    gland.rotation_euler[0] = math.radians(90.0)
    gland.data.materials.append(steel)


def export_glb(filepath):
    """Exports all scene objects into an optimized binary GLTF (.glb) file."""
    detail_pass()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=str(filepath),
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported: {filepath}")


# -----------------------------------------------------------------------------
# 1. Rotary Evaporator (Rotovap)
# -----------------------------------------------------------------------------
def build_rotovap(mats):
    clean_scene()

    # Base Plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.025))
    base = bpy.context.active_object
    base.name = "Rotovap_Base"
    base.scale = (0.45, 0.40, 0.05)
    base.data.materials.append(mats["chassis_dark"])

    # Vertical Lift Column
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.65, location=(-0.12, 0.08, 0.35))
    col = bpy.context.active_object
    col.name = "Rotovap_Column"
    col.data.materials.append(mats["stainless"])

    # Motor Drive Unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.05, 0.05, 0.55))
    motor = bpy.context.active_object
    motor.name = "Rotovap_MotorHead"
    motor.scale = (0.22, 0.18, 0.16)
    motor.rotation_euler = (0, math.radians(-30), 0)
    motor.data.materials.append(mats["chassis_light"])

    # Digital Speed Display on Motor
    bpy.ops.mesh.primitive_plane_add(size=0.08, location=(-0.05, -0.045, 0.57))
    disp = bpy.context.active_object
    disp.name = "Rotovap_Display"
    disp.scale = (1.0, 0.4, 1.0)
    disp.rotation_euler = (math.radians(90), 0, 0)
    disp.data.materials.append(mats["display_screen"])

    # Water Bath Heating Basin
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.12, location=(0.14, -0.05, 0.12))
    bath = bpy.context.active_object
    bath.name = "Rotovap_WaterBath"
    bath.data.materials.append(mats["stainless"])

    # Water in Bath
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.08, location=(0.14, -0.05, 0.13))
    water = bpy.context.active_object
    water.name = "Rotovap_BathWater"
    water.data.materials.append(mats["liquid_blue"])

    # Rotating Evaporating Flask (Round bottom dipping into bath)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0.12, -0.05, 0.22))
    flask_evap = bpy.context.active_object
    flask_evap.name = "Rotovap_EvaporationFlask"
    flask_evap.data.materials.append(mats["glass"])

    # Condenser (Vertical cooling column with internal coil)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.55, location=(-0.16, -0.08, 0.65))
    condenser = bpy.context.active_object
    condenser.name = "Rotovap_Condenser"
    condenser.data.materials.append(mats["glass"])

    # Internal Condenser Coil (Helix representation)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.45, location=(-0.16, -0.08, 0.65))
    coil = bpy.context.active_object
    coil.name = "Rotovap_CondenserCoil"
    coil.data.materials.append(mats["glass"])

    # Receiving Flask (Catching distillate at base of condenser)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=(-0.16, -0.08, 0.32))
    flask_rec = bpy.context.active_object
    flask_rec.name = "Rotovap_ReceivingFlask"
    flask_rec.data.materials.append(mats["glass"])

    # Solvent in Receiving Flask
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.065, location=(-0.16, -0.08, 0.30))
    distillate = bpy.context.active_object
    distillate.name = "Rotovap_Distillate"
    distillate.scale = (1.0, 1.0, 0.6)
    distillate.data.materials.append(mats["liquid_blue"])

    export_glb(OUTPUT_DIR / "SM_Rotovap.glb")


# -----------------------------------------------------------------------------
# 2. Dual-Manifold Schlenk Line
# -----------------------------------------------------------------------------
def build_schlenk_line(mats):
    clean_scene()

    # Support Rod Stand
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.02))
    base = bpy.context.active_object
    base.name = "Schlenk_StandBase"
    base.scale = (0.70, 0.25, 0.04)
    base.data.materials.append(mats["chassis_dark"])

    # Vertical Support Rods (left & right)
    for x in [-0.28, 0.28]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.75, location=(x, 0, 0.40))
        rod = bpy.context.active_object
        rod.name = f"Schlenk_Rod_{'L' if x < 0 else 'R'}"
        rod.data.materials.append(mats["stainless"])

    # Dual Glass Manifold Tubes (Upper = Inert Gas, Lower = High Vacuum)
    # Upper Manifold (Inert Gas N2/Ar)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.62, location=(0, 0.04, 0.52))
    manifold_gas = bpy.context.active_object
    manifold_gas.name = "Schlenk_GasManifold"
    manifold_gas.rotation_euler = (0, math.radians(90), 0)
    manifold_gas.data.materials.append(mats["glass"])

    # Lower Manifold (High Vacuum)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.62, location=(0, 0.04, 0.44))
    manifold_vac = bpy.context.active_object
    manifold_vac.name = "Schlenk_VacManifold"
    manifold_vac.rotation_euler = (0, math.radians(90), 0)
    manifold_vac.data.materials.append(mats["glass"])

    # 4 Double-Oblique Stopcock Valves with PTFE Plugs
    stopcock_xs = [-0.21, -0.07, 0.07, 0.21]
    for i, x in enumerate(stopcock_xs):
        # Stopcock Valve Body
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.10, location=(x, 0.04, 0.48))
        valve = bpy.context.active_object
        valve.name = f"Schlenk_StopcockBody_{i+1}"
        valve.data.materials.append(mats["glass"])

        # PTFE Valve Handle
        bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.04, location=(x, 0.07, 0.48))
        handle = bpy.context.active_object
        handle.name = f"Schlenk_PTFEHandle_{i+1}"
        handle.rotation_euler = (math.radians(90), 0, 0)
        handle.data.materials.append(mats["chassis_light"])

        # Downward Hose Barb
        bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.08, location=(x, 0.04, 0.38))
        barb = bpy.context.active_object
        barb.name = f"Schlenk_HoseBarb_{i+1}"
        barb.data.materials.append(mats["glass"])

    # Cold Trap (Liquid Nitrogen Dewar + Vacuum Finger Trap)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.28, location=(-0.38, 0.05, 0.22))
    dewar = bpy.context.active_object
    dewar.name = "Schlenk_DewarFlask"
    dewar.data.materials.append(mats["stainless"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.34, location=(-0.38, 0.05, 0.28))
    trap = bpy.context.active_object
    trap.name = "Schlenk_GlassFingerTrap"
    trap.data.materials.append(mats["glass"])

    # Digital Vacuum Sensor Gauge
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.38, 0.02, 0.44))
    gauge = bpy.context.active_object
    gauge.name = "Schlenk_VacuumGauge"
    gauge.scale = (0.08, 0.06, 0.06)
    gauge.data.materials.append(mats["chassis_dark"])

    export_glb(OUTPUT_DIR / "SM_SchlenkLine.glb")


# -----------------------------------------------------------------------------
# 3. Soxhlet Extraction System
# -----------------------------------------------------------------------------
def build_soxhlet_extractor(mats):
    clean_scene()

    # Heating Mantle Base
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.14, location=(0, 0, 0.07))
    mantle = bpy.context.active_object
    mantle.name = "Soxhlet_HeatingMantle"
    mantle.data.materials.append(mats["chassis_dark"])

    # Temperature Dial
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.02, location=(0, -0.14, 0.07))
    dial = bpy.context.active_object
    dial.name = "Soxhlet_MantleDial"
    dial.rotation_euler = (math.radians(90), 0, 0)
    dial.data.materials.append(mats["accent_amber"])

    # Boiling Round-Bottom Flask (500 mL)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0, 0, 0.16))
    flask = bpy.context.active_object
    flask.name = "Soxhlet_BoilingFlask"
    flask.data.materials.append(mats["glass"])

    # Solvent Liquid in Flask
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0, 0, 0.14))
    liquid = bpy.context.active_object
    liquid.name = "Soxhlet_SolventLiquid"
    liquid.scale = (1.0, 1.0, 0.7)
    liquid.data.materials.append(mats["liquid_gold"])

    # Flask Ground Glass Joint Neck
    bpy.ops.mesh.primitive_cylinder_add(radius=0.028, depth=0.08, location=(0, 0, 0.28))
    neck = bpy.context.active_object
    neck.name = "Soxhlet_FlaskNeck"
    neck.data.materials.append(mats["glass"])

    # Soxhlet Extraction Body Chamber
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.26, location=(0, 0, 0.44))
    chamber = bpy.context.active_object
    chamber.name = "Soxhlet_ExtractionChamber"
    chamber.data.materials.append(mats["glass"])

    # Porous Cellulose Extraction Thimble (Contains natural product)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.18, location=(0, 0, 0.42))
    thimble = bpy.context.active_object
    thimble.name = "Soxhlet_CelluloseThimble"
    thimble.data.materials.append(mats["chassis_light"])

    # Vapor Bypass Side Tube
    bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=0.26, location=(0.055, 0, 0.44))
    vapor_tube = bpy.context.active_object
    vapor_tube.name = "Soxhlet_VaporBypassTube"
    vapor_tube.data.materials.append(mats["glass"])

    # Siphon Arm Tube
    bpy.ops.mesh.primitive_cylinder_add(radius=0.007, depth=0.22, location=(-0.055, 0, 0.41))
    siphon = bpy.context.active_object
    siphon.name = "Soxhlet_SiphonCapillary"
    siphon.data.materials.append(mats["glass"])

    # Allihn Bulb Condenser (Mounted on top)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.35, location=(0, 0, 0.74))
    condenser = bpy.context.active_object
    condenser.name = "Soxhlet_Condenser"
    condenser.data.materials.append(mats["glass"])

    # Cooling Water Hose Nipples
    for z in [0.62, 0.86]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.04, location=(0.055, 0, z))
        nipple = bpy.context.active_object
        nipple.name = f"Soxhlet_WaterNipple_{'In' if z < 0.7 else 'Out'}"
        nipple.rotation_euler = (0, math.radians(90), 0)
        nipple.data.materials.append(mats["glass"])

    export_glb(OUTPUT_DIR / "SM_SoxhletExtractor.glb")


# -----------------------------------------------------------------------------
# 4. Modular HPLC Chromatography System
# -----------------------------------------------------------------------------
def build_hplc_system(mats):
    clean_scene()

    # Solvent Tray (Top)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.62))
    tray = bpy.context.active_object
    tray.name = "HPLC_SolventTray"
    tray.scale = (0.42, 0.36, 0.05)
    tray.data.materials.append(mats["chassis_light"])

    # 4 Solvent Reservoir Bottles (Amber and Clear)
    bottle_coords = [(-0.12, -0.08), (0.12, -0.08), (-0.12, 0.08), (0.12, 0.08)]
    for i, (bx, by) in enumerate(bottle_coords):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.18, location=(bx, by, 0.74))
        bot = bpy.context.active_object
        bot.name = f"HPLC_SolventBottle_{i+1}"
        bot.data.materials.append(mats["amber_glass"] if i % 2 == 0 else mats["glass"])

        # PTFE Cap
        bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.03, location=(bx, by, 0.84))
        cap = bpy.context.active_object
        cap.name = f"HPLC_BottleCap_{i+1}"
        cap.data.materials.append(mats["accent_cyan"])

    # Module 1: Quaternary Solvent Pump Module
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.48))
    pump = bpy.context.active_object
    pump.name = "HPLC_PumpModule"
    pump.scale = (0.44, 0.42, 0.18)
    pump.data.materials.append(mats["chassis_light"])

    # Module 2: Autosampler Unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.28))
    autosampler = bpy.context.active_object
    autosampler.name = "HPLC_AutosamplerModule"
    autosampler.scale = (0.44, 0.42, 0.18)
    autosampler.data.materials.append(mats["chassis_light"])

    # Autosampler Sample Door Window
    bpy.ops.mesh.primitive_plane_add(size=0.12, location=(0, -0.215, 0.28))
    door = bpy.context.active_object
    door.name = "HPLC_AutosamplerDoor"
    door.rotation_euler = (math.radians(90), 0, 0)
    door.data.materials.append(mats["acrylic_clear"])

    # Module 3: Column Compartment & Diode Array Detector (DAD)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.09))
    detector = bpy.context.active_object
    detector.name = "HPLC_DetectorModule"
    detector.scale = (0.44, 0.42, 0.18)
    detector.data.materials.append(mats["chassis_dark"])

    # Status LED Strip across chassis
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.212, 0.12))
    led = bpy.context.active_object
    led.name = "HPLC_StatusLED"
    led.scale = (0.38, 0.005, 0.015)
    led.data.materials.append(mats["display_screen"])

    export_glb(OUTPUT_DIR / "SM_HPLC_System.glb")


# -----------------------------------------------------------------------------
# 5. Benchtop Microcentrifuge
# -----------------------------------------------------------------------------
def build_centrifuge(mats):
    clean_scene()

    # Main Chassis (Streamlined body)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.16, location=(0, 0, 0.08))
    body = bpy.context.active_object
    body.name = "Centrifuge_Chassis"
    body.scale = (1.0, 1.15, 1.0)
    body.data.materials.append(mats["chassis_light"])

    # Stainless Steel Rotor Chamber Basin
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.08, location=(0, -0.02, 0.13))
    chamber = bpy.context.active_object
    chamber.name = "Centrifuge_Chamber"
    chamber.data.materials.append(mats["stainless"])

    # 24-Place Fixed Angle Aluminum Rotor (45 degrees)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.04, location=(0, -0.02, 0.14))
    rotor = bpy.context.active_object
    rotor.name = "Centrifuge_Rotor"
    rotor.data.materials.append(mats["stainless"])

    # Central Rotor Lock Nut
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.03, location=(0, -0.02, 0.17))
    nut = bpy.context.active_object
    nut.name = "Centrifuge_LockNut"
    nut.data.materials.append(mats["accent_cyan"])

    # Microcentrifuge Tubes (1.5 mL Eppendorf placed in rotor)
    for i in range(8):
        angle = (2 * math.pi / 8) * i
        tx = 0.075 * math.cos(angle)
        ty = -0.02 + 0.075 * math.sin(angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.035, location=(tx, ty, 0.15))
        tube = bpy.context.active_object
        tube.name = f"Centrifuge_Tube_{i+1}"
        tube.data.materials.append(mats["acrylic_clear"])

    # Transparent Hinged Lid
    bpy.ops.mesh.primitive_cylinder_add(radius=0.175, depth=0.03, location=(0, 0, 0.18))
    lid = bpy.context.active_object
    lid.name = "Centrifuge_Lid"
    lid.scale = (1.0, 1.12, 1.0)
    lid.data.materials.append(mats["acrylic_clear"])

    # Front Digital Speed / Timer Display
    bpy.ops.mesh.primitive_plane_add(size=0.10, location=(0, -0.19, 0.10))
    disp = bpy.context.active_object
    disp.name = "Centrifuge_ControlPanel"
    disp.scale = (1.0, 0.45, 1.0)
    disp.rotation_euler = (math.radians(65), 0, 0)
    disp.data.materials.append(mats["display_screen"])

    export_glb(OUTPUT_DIR / "SM_Centrifuge.glb")


# -----------------------------------------------------------------------------
# 6. UV-Vis Spectrophotometer
# -----------------------------------------------------------------------------
def build_uv_vis(mats):
    clean_scene()

    # Desktop Spectrophotometer Casing
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.11))
    body = bpy.context.active_object
    body.name = "UVVis_Chassis"
    body.scale = (0.48, 0.38, 0.22)
    body.data.materials.append(mats["chassis_light"])

    # Hinged Sample Chamber Door
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.11, -0.04, 0.23))
    door = bpy.context.active_object
    door.name = "UVVis_SampleDoor"
    door.scale = (0.16, 0.16, 0.03)
    door.data.materials.append(mats["chassis_dark"])

    # Cuvette Holder Cell (Inside chamber)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.11, -0.04, 0.17))
    holder = bpy.context.active_object
    holder.name = "UVVis_CuvetteTurret"
    holder.scale = (0.06, 0.06, 0.05)
    holder.data.materials.append(mats["stainless"])

    # 10mm Standard Quartz Cuvette
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.11, -0.04, 0.19))
    cuvette = bpy.context.active_object
    cuvette.name = "UVVis_QuartzCuvette"
    cuvette.scale = (0.018, 0.018, 0.045)
    cuvette.data.materials.append(mats["glass"])

    # Colored Analyte in Cuvette
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.11, -0.04, 0.18))
    analyte = bpy.context.active_object
    analyte.name = "UVVis_AnalyteSolution"
    analyte.scale = (0.014, 0.014, 0.03)
    analyte.data.materials.append(mats["liquid_blue"])

    # LCD Spectrum Graph Display
    bpy.ops.mesh.primitive_plane_add(size=0.18, location=(0.11, -0.04, 0.23))
    screen = bpy.context.active_object
    screen.name = "UVVis_DisplayScreen"
    screen.scale = (1.0, 0.65, 1.0)
    screen.data.materials.append(mats["display_screen"])

    # Navigation Keypad
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.11, -0.14, 0.225))
    keypad = bpy.context.active_object
    keypad.name = "UVVis_Keypad"
    keypad.scale = (0.14, 0.06, 0.015)
    keypad.data.materials.append(mats["chassis_dark"])

    export_glb(OUTPUT_DIR / "SM_UVVis_Spectrophotometer.glb")


# -----------------------------------------------------------------------------
# 7. Inert Atmosphere Glovebox
# -----------------------------------------------------------------------------
def build_glovebox(mats):
    clean_scene()

    # Main Stainless Steel Isolation Chamber
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.45))
    chamber = bpy.context.active_object
    chamber.name = "Glovebox_MainChamber"
    chamber.scale = (0.90, 0.65, 0.70)
    chamber.data.materials.append(mats["stainless"])

    # Sloped Front Viewing Window (Tempered Polycarbonate / Laminated Safety Glass)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, -0.33, 0.48))
    window = bpy.context.active_object
    window.name = "Glovebox_FrontWindow"
    window.scale = (0.82, 0.45, 1.0)
    window.rotation_euler = (math.radians(75), 0, 0)
    window.data.materials.append(mats["acrylic_clear"])

    # Two Glove Port Flanges (Circular aluminum rings)
    for x in [-0.22, 0.22]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.03, location=(x, -0.32, 0.38))
        flange = bpy.context.active_object
        flange.name = f"Glovebox_PortRing_{'L' if x < 0 else 'R'}"
        flange.rotation_euler = (math.radians(90), 0, 0)
        flange.data.materials.append(mats["stainless"])

        # Butyl Rubber Heavy-Duty Gloves (Extending inside)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.35, location=(x, -0.15, 0.38))
        glove = bpy.context.active_object
        glove.name = f"Glovebox_ButylGlove_{'L' if x < 0 else 'R'}"
        glove.rotation_euler = (math.radians(90), 0, 0)
        glove.data.materials.append(mats["rubber_black"])

    # Cylindrical Transfer Airlock Antechamber (Right Side)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.38, location=(0.60, 0, 0.42))
    airlock = bpy.context.active_object
    airlock.name = "Glovebox_Antechamber"
    airlock.rotation_euler = (0, math.radians(90), 0)
    airlock.data.materials.append(mats["stainless"])

    # Airlock Quick-Lock Door Handwheel
    bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.03, location=(0.80, 0, 0.42))
    door = bpy.context.active_object
    door.name = "Glovebox_AirlockDoor"
    door.rotation_euler = (0, math.radians(90), 0)
    door.data.materials.append(mats["brass"])

    # Gas Purification Column (Rear)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.65, location=(-0.30, 0.38, 0.50))
    purifier = bpy.context.active_object
    purifier.name = "Glovebox_PurificationTower"
    purifier.data.materials.append(mats["chassis_dark"])

    # Pressure & Oxygen Display
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.32, -0.31, 0.72))
    sensor = bpy.context.active_object
    sensor.name = "Glovebox_PPM_SensorDisplay"
    sensor.scale = (0.12, 0.04, 0.06)
    sensor.data.materials.append(mats["display_screen"])

    export_glb(OUTPUT_DIR / "SM_Glovebox.glb")


# -----------------------------------------------------------------------------
# 8. Precision Analytical Balance
# -----------------------------------------------------------------------------
def build_analytical_balance(mats):
    clean_scene()

    # Base Housing
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.035))
    base = bpy.context.active_object
    base.name = "Balance_BaseHousing"
    base.scale = (0.32, 0.38, 0.07)
    base.data.materials.append(mats["chassis_light"])

    # 4 Adjustable Leveling Brass Feet
    for fx in [-0.14, 0.14]:
        for fy in [-0.16, 0.16]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.015, location=(fx, fy, 0.007))
            foot = bpy.context.active_object
            foot.name = "Balance_LevelingFoot"
            foot.data.materials.append(mats["brass"])

    # Glass Draft Shield Enclosure (3 Sliding Doors)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.04, 0.19))
    shield = bpy.context.active_object
    shield.name = "Balance_DraftShield"
    shield.scale = (0.24, 0.24, 0.24)
    shield.data.materials.append(mats["glass"])

    # Stainless Steel Draft Shield Corner Frame
    # Central Weighing Pan
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.006, location=(0, 0.04, 0.09))
    pan = bpy.context.active_object
    pan.name = "Balance_WeighingPan"
    pan.data.materials.append(mats["stainless"])

    # Glass Sub-chamber Floor
    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.005, location=(0, 0.04, 0.075))
    subpan = bpy.context.active_object
    subpan.name = "Balance_SubFloor"
    subpan.data.materials.append(mats["glass"])

    # Sloped Front Control Panel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.14, 0.065))
    panel = bpy.context.active_object
    panel.name = "Balance_FrontPanel"
    panel.scale = (0.28, 0.08, 0.02)
    panel.rotation_euler = (math.radians(-25), 0, 0)
    panel.data.materials.append(mats["chassis_dark"])

    # High-Precision Backlit LCD (0.0000 g)
    bpy.ops.mesh.primitive_plane_add(size=0.09, location=(0, -0.14, 0.08))
    disp = bpy.context.active_object
    disp.name = "Balance_LCD_Display"
    disp.scale = (1.0, 0.40, 1.0)
    disp.rotation_euler = (math.radians(-25), 0, 0)
    disp.data.materials.append(mats["display_screen"])

    # Tare and Zero Push Buttons
    for bx in [-0.07, 0.07]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.01, location=(bx, -0.14, 0.055))
        btn = bpy.context.active_object
        btn.name = f"Balance_Button_{'Tare' if bx < 0 else 'Zero'}"
        btn.rotation_euler = (math.radians(-25), 0, 0)
        btn.data.materials.append(mats["accent_cyan"])

    export_glb(OUTPUT_DIR / "SM_AnalyticalBalance.glb")


# -----------------------------------------------------------------------------
# 9. Separatory Funnel Extraction Station (500 mL)
# -----------------------------------------------------------------------------
def build_separatory_funnel(mats):
    clean_scene()

    # Retort Stand Base Plate (Heavy Cast Iron)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.015))
    base = bpy.context.active_object
    base.name = "SepFunnel_StandBase"
    base.scale = (0.30, 0.22, 0.03)
    base.data.materials.append(mats["chassis_dark"])

    # Vertical Stainless Steel Support Rod
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.75, location=(-0.10, 0.05, 0.38))
    rod = bpy.context.active_object
    rod.name = "SepFunnel_SupportRod"
    rod.data.materials.append(mats["stainless"])

    # Bosshead Clamp on Rod
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.10, 0.05, 0.42))
    boss = bpy.context.active_object
    boss.name = "SepFunnel_Bosshead"
    boss.scale = (0.035, 0.035, 0.04)
    boss.data.materials.append(mats["chassis_dark"])

    # Extension Arm & Ring Clamp with Cork Lining
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.12, location=(-0.04, 0.03, 0.42))
    arm = bpy.context.active_object
    arm.name = "SepFunnel_ClampArm"
    arm.rotation_euler = (0, math.radians(90), math.radians(20))
    arm.data.materials.append(mats["stainless"])

    # Cast Iron Ring Collar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.012, location=(0.02, 0.0, 0.42))
    ring = bpy.context.active_object
    ring.name = "SepFunnel_SupportRing"
    ring.data.materials.append(mats["chassis_dark"])

    # Pear-Shaped Funnel Upper Bulb (Spherical/Oval Top)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.062, location=(0.02, 0.0, 0.44))
    bulb = bpy.context.active_object
    bulb.name = "SepFunnel_GlassBulb"
    bulb.scale = (1.0, 1.0, 1.25)
    bulb.data.materials.append(mats["glass"])

    # Funnel Conical Lower Body Tapering Downwards
    bpy.ops.mesh.primitive_cone_add(radius1=0.058, radius2=0.012, depth=0.14, location=(0.02, 0.0, 0.30))
    cone = bpy.context.active_object
    cone.name = "SepFunnel_GlassCone"
    cone.rotation_euler = (math.radians(180), 0, 0)
    cone.data.materials.append(mats["glass"])

    # Upper Ground Glass Joint Neck
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.05, location=(0.02, 0.0, 0.54))
    neck = bpy.context.active_object
    neck.name = "SepFunnel_Neck"
    neck.data.materials.append(mats["glass"])

    # Hexagonal Glass Stopper with Penny Head
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.03, location=(0.02, 0.0, 0.56))
    stopper_plug = bpy.context.active_object
    stopper_plug.name = "SepFunnel_StopperPlug"
    stopper_plug.data.materials.append(mats["glass"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.02, 0.0, 0.585))
    stopper_head = bpy.context.active_object
    stopper_head.name = "SepFunnel_StopperHead"
    stopper_head.scale = (0.032, 0.008, 0.022)
    stopper_head.data.materials.append(mats["glass"])

    # Liquid Phase 1: Dense Chlorinated Organic Layer (Bottom, Gold/Alkaloid extract)
    bpy.ops.mesh.primitive_cone_add(radius1=0.038, radius2=0.010, depth=0.07, location=(0.02, 0.0, 0.265))
    org_phase = bpy.context.active_object
    org_phase.name = "SepFunnel_OrganicLayer"
    org_phase.rotation_euler = (math.radians(180), 0, 0)
    org_phase.data.materials.append(mats["liquid_biphasic_organic"])

    # Liquid Phase 2: Lighter Aqueous Layer (Top, Clear/Aqueous blue tint)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.08, location=(0.02, 0.0, 0.36))
    aq_phase = bpy.context.active_object
    aq_phase.name = "SepFunnel_AqueousLayer"
    aq_phase.data.materials.append(mats["liquid_biphasic_aqueous"])

    # PTFE Precision Stopcock Bore Barrel
    bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.05, location=(0.02, 0.0, 0.20))
    barrel = bpy.context.active_object
    barrel.name = "SepFunnel_StopcockBarrel"
    barrel.data.materials.append(mats["glass"])

    # PTFE Stopcock Plug & Cross-Handle (White fluoropolymer)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.065, location=(0.02, 0.0, 0.20))
    plug = bpy.context.active_object
    plug.name = "SepFunnel_PTFEPlug"
    plug.rotation_euler = (math.radians(90), 0, 0)
    plug.data.materials.append(mats["ptfe_white"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.02, 0.035, 0.20))
    handle = bpy.context.active_object
    handle.name = "SepFunnel_PTFEHandle"
    handle.scale = (0.035, 0.008, 0.012)
    handle.data.materials.append(mats["ptfe_white"])

    # Narrow Glass Delivery Stem below Stopcock
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.08, location=(0.02, 0.0, 0.14))
    stem = bpy.context.active_object
    stem.name = "SepFunnel_DeliveryStem"
    stem.data.materials.append(mats["glass"])

    # Receiving Erlenmeyer Flask (250 mL) on Stand Base
    bpy.ops.mesh.primitive_cone_add(radius1=0.045, radius2=0.016, depth=0.085, location=(0.02, 0.0, 0.055))
    flask = bpy.context.active_object
    flask.name = "SepFunnel_ReceivingFlask"
    flask.data.materials.append(mats["glass"])

    export_glb(OUTPUT_DIR / "SM_SeparatoryFunnel_500ml.glb")


# -----------------------------------------------------------------------------
# 10. Superconducting NMR Spectrometer (500 MHz Cryomagnet & Console)
# -----------------------------------------------------------------------------
def build_nmr_spectrometer(mats):
    clean_scene()

    # Main Cryostat Magnet Cylinder (Liquid Helium / Nitrogen Dewar)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.48, depth=1.10, location=(0, 0, 0.95))
    dewar = bpy.context.active_object
    dewar.name = "NMR_CryomagnetDewar"
    dewar.data.materials.append(mats["superconductor_cryo"])

    # Dewar Upper Annular Cap Ring
    bpy.ops.mesh.primitive_cylinder_add(radius=0.50, depth=0.06, location=(0, 0, 1.52))
    cap = bpy.context.active_object
    cap.name = "NMR_TopCap"
    cap.data.materials.append(mats["chassis_light"])

    # Cryogen Fill & Exhaust Ports (Liquid N2 / Liquid He Cryo Towers)
    for px, py, label in [(-0.25, 0.15, "LiquidHe_Port"), (0.25, 0.15, "LiquidN2_Port"), (0.0, -0.28, "QuenchExhaust")]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.22, location=(px, py, 1.63))
        tower = bpy.context.active_object
        tower.name = f"NMR_{label}"
        tower.data.materials.append(mats["stainless"])

        bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.05, location=(px, py, 1.75))
        valve = bpy.context.active_object
        valve.name = f"NMR_{label}_Valve"
        valve.data.materials.append(mats["brass"])

    # 3 Vibration-Isolated Damped Support Legs (Triangular base)
    for angle_deg in [0, 120, 240]:
        rad = math.radians(angle_deg)
        lx = math.cos(rad) * 0.46
        ly = math.sin(rad) * 0.46
        # Leg Cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.48, location=(lx, ly, 0.24))
        leg = bpy.context.active_object
        leg.name = f"NMR_SupportLeg_{angle_deg}"
        leg.data.materials.append(mats["chassis_dark"])
        # Pneumatic Isolation Damping Foot
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.04, location=(lx, ly, 0.02))
        foot = bpy.context.active_object
        foot.name = f"NMR_IsolatorFoot_{angle_deg}"
        foot.data.materials.append(mats["rubber_black"])

    # Central Vertical Bore Chamber & Sample Insertion Funnel
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.20, location=(0, 0, 1.60))
    funnel = bpy.context.active_object
    funnel.name = "NMR_BoreFunnel"
    funnel.data.materials.append(mats["chassis_dark"])

    # 24-Position Sample Autosampler Ring
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.025, location=(0, 0, 1.56))
    carousel = bpy.context.active_object
    carousel.name = "NMR_AutosamplerCarousel"
    carousel.data.materials.append(mats["acrylic_clear"])

    # Sample Tube with Turbine Spinner in Central Position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.18, location=(0, 0, 1.68))
    tube = bpy.context.active_object
    tube.name = "NMR_SampleTube_5mm"
    tube.data.materials.append(mats["glass"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.02, location=(0, 0, 1.66))
    spinner = bpy.context.active_object
    spinner.name = "NMR_SpinnerTurbine"
    spinner.data.materials.append(mats["accent_cyan"])

    # RF Acquisition Console Tower adjacent to magnet
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.85, 0.0, 0.70))
    console = bpy.context.active_object
    console.name = "NMR_RFConsoleCabinet"
    console.scale = (0.50, 0.55, 1.40)
    console.data.materials.append(mats["chassis_dark"])

    # Spectrum Acquisition Monitor Display
    bpy.ops.mesh.primitive_plane_add(size=0.42, location=(0.59, 0.0, 1.15))
    screen = bpy.context.active_object
    screen.name = "NMR_SpectrumMonitor"
    screen.scale = (1.0, 0.65, 1.0)
    screen.rotation_euler = (math.radians(90), 0, math.radians(-90))
    screen.data.materials.append(mats["display_screen"])

    # Status LED Strip on Console
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.60, -0.18, 1.35))
    led = bpy.context.active_object
    led.name = "NMR_StatusIndicator"
    led.scale = (0.02, 0.12, 0.03)
    led.data.materials.append(mats["accent_cyan"])

    export_glb(OUTPUT_DIR / "SM_NMR_Spectrometer.glb")


# -----------------------------------------------------------------------------
# 11. Digital Magnetic Stirrer & Ceramic Hotplate
# -----------------------------------------------------------------------------
def build_magnetic_stirrer(mats):
    clean_scene()

    # Die-Cast Aluminum Lower Chassis with Sloped Control Bezel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.045))
    body = bpy.context.active_object
    body.name = "Stirrer_Chassis"
    body.scale = (0.24, 0.28, 0.09)
    body.data.materials.append(mats["chassis_dark"])

    # Anti-Spill Fluid Perimeter Gutter Rim
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.04, 0.092))
    rim = bpy.context.active_object
    rim.name = "Stirrer_PlateRim"
    rim.scale = (0.21, 0.21, 0.015)
    rim.data.materials.append(mats["chassis_light"])

    # Pure White Solid Ceramic Heating Plate Top
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.04, 0.102))
    plate = bpy.context.active_object
    plate.name = "Stirrer_CeramicPlate"
    plate.scale = (0.19, 0.19, 0.012)
    plate.data.materials.append(mats["ceramic_white"])

    # PTFE Magnetic Stirring Flea (Pivot-Ring Bar)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.035, location=(0, 0.04, 0.113))
    stir_bar = bpy.context.active_object
    stir_bar.name = "Stirrer_MagneticBar"
    stir_bar.rotation_euler = (0, math.radians(90), math.radians(35))
    stir_bar.data.materials.append(mats["ptfe_white"])

    # Dual Digital LED Displays (Temperature °C in Amber, Stirrer RPM in Cyan)
    bpy.ops.mesh.primitive_plane_add(size=0.065, location=(-0.05, -0.095, 0.075))
    temp_disp = bpy.context.active_object
    temp_disp.name = "Stirrer_TempDisplay"
    temp_disp.scale = (1.0, 0.45, 1.0)
    temp_disp.rotation_euler = (math.radians(35), 0, 0)
    temp_disp.data.materials.append(mats["accent_amber"])

    bpy.ops.mesh.primitive_plane_add(size=0.065, location=(0.05, -0.095, 0.075))
    rpm_disp = bpy.context.active_object
    rpm_disp.name = "Stirrer_RPMDisplay"
    rpm_disp.scale = (1.0, 0.45, 1.0)
    rpm_disp.rotation_euler = (math.radians(35), 0, 0)
    rpm_disp.data.materials.append(mats["display_screen"])

    # Knurled Optical Encoder Rotary Control Dials
    for dx, label in [(-0.05, "TempKnob"), (0.05, "SpeedKnob")]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.020, depth=0.018, location=(dx, -0.125, 0.055))
        knob = bpy.context.active_object
        knob.name = f"Stirrer_{label}"
        knob.rotation_euler = (math.radians(35), 0, 0)
        knob.data.materials.append(mats["stainless"])

    # External PT1000 Temperature Sensor Support Boss & Rod
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.35, location=(0.095, 0.12, 0.22))
    probe_rod = bpy.context.active_object
    probe_rod.name = "Stirrer_ProbeSupportRod"
    probe_rod.data.materials.append(mats["stainless"])

    # PT1000 Stainless Steel Probe Arm & Tip
    bpy.ops.mesh.primitive_cylinder_add(radius=0.003, depth=0.15, location=(0.03, 0.08, 0.22))
    probe = bpy.context.active_object
    probe.name = "Stirrer_PT1000SensorProbe"
    probe.data.materials.append(mats["stainless"])

    export_glb(OUTPUT_DIR / "SM_MagneticStirrer_Hotplate.glb")


# -----------------------------------------------------------------------------
# 12. Aerodynamic Fume Hood Enclosure (Ducted Class II)
# -----------------------------------------------------------------------------
def build_fume_hood(mats):
    clean_scene()

    # Outer Hood Structural Cabinet
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.90))
    cabinet = bpy.context.active_object
    cabinet.name = "FumeHood_OuterCabinet"
    cabinet.scale = (1.20, 0.85, 1.50)
    cabinet.data.materials.append(mats["chassis_light"])

    # Solid Epoxy Resin Worktop Floor (Dished with spill containment)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.02, 0.22))
    worktop = bpy.context.active_object
    worktop.name = "FumeHood_Worktop"
    worktop.scale = (1.14, 0.78, 0.04)
    worktop.data.materials.append(mats["epoxy_black"])

    # Aerodynamic Front Airfoil Sill
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.14, location=(0, -0.40, 0.23))
    airfoil = bpy.context.active_object
    airfoil.name = "FumeHood_AirfoilSill"
    airfoil.rotation_euler = (0, math.radians(90), 0)
    airfoil.data.materials.append(mats["stainless"])

    # Interior Rear Exhaust Baffle Plates (3-Tier Air Slots)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.38, 0.90))
    baffle = bpy.context.active_object
    baffle.name = "FumeHood_ExhaustBaffle"
    baffle.scale = (1.12, 0.03, 1.25)
    baffle.data.materials.append(mats["chassis_dark"])

    # Top Cylindrical Exhaust Duct Collar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.25, location=(0, 0.15, 1.75))
    duct = bpy.context.active_object
    duct.name = "FumeHood_ExhaustDuct"
    duct.data.materials.append(mats["stainless"])

    # Vertical Sliding Tempered Glass Sash
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.40, 0.95))
    sash = bpy.context.active_object
    sash.name = "FumeHood_GlassSash"
    sash.scale = (1.12, 0.015, 0.85)
    sash.data.materials.append(mats["acrylic_clear"])

    # Sash Full-Width Extruded Aluminum Grip Handle
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.41, 0.53))
    sash_handle = bpy.context.active_object
    sash_handle.name = "FumeHood_SashHandle"
    sash_handle.scale = (1.12, 0.035, 0.025)
    sash_handle.data.materials.append(mats["stainless"])

    # Ceiling Vapor-Proof LED Task Luminaire Light
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.05, 1.58))
    light = bpy.context.active_object
    light.name = "FumeHood_TaskLuminaire"
    light.scale = (0.90, 0.14, 0.03)
    light.data.materials.append(mats["display_screen"])

    # Utility Service Fixtures on Side Stanchions (Argon, Vacuum, Chilled Water)
    for fy, color_key, label in [(-0.15, "accent_cyan", "ArgonValve"), (0.0, "accent_amber", "VacuumValve"), (0.15, "stainless", "WaterTap")]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.04, location=(-0.55, fy, 0.35))
        turret = bpy.context.active_object
        turret.name = f"FumeHood_{label}"
        turret.rotation_euler = (0, 0, math.radians(90))
        turret.data.materials.append(mats[color_key])

    # Airflow Face Velocity Monitor (Digital FPM/Safety Status)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.58, -0.40, 0.75))
    monitor = bpy.context.active_object
    monitor.name = "FumeHood_VelocityMonitor"
    monitor.scale = (0.03, 0.08, 0.12)
    monitor.data.materials.append(mats["display_screen"])

    export_glb(OUTPUT_DIR / "SM_FumeHood_Ducted.glb")


# -----------------------------------------------------------------------------
# 13. Laboratory Micropipette Set & Tip Box Carousel
# -----------------------------------------------------------------------------
def build_micropipette_set(mats):
    clean_scene()

    # Curved Acrylic Desktop Pipette Carousel Stand
    bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.025, location=(0, 0, 0.012))
    base = bpy.context.active_object
    base.name = "PipetteStand_Base"
    base.data.materials.append(mats["acrylic_clear"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.32, location=(0, 0, 0.17))
    shaft = bpy.context.active_object
    shaft.name = "PipetteStand_CentralShaft"
    shaft.data.materials.append(mats["stainless"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.015, location=(0, 0, 0.31))
    hanger = bpy.context.active_object
    hanger.name = "PipetteStand_HangerHead"
    hanger.data.materials.append(mats["acrylic_clear"])

    # 3 Ergonomic Air-Displacement Micropipettes (P1000 Blue, P200 Yellow, P20 Grey)
    pipette_specs = [
        (-0.065, "P1000", mats["accent_cyan"]),
        (0.0, "P200", mats["accent_amber"]),
        (0.065, "P20", mats["chassis_dark"])
    ]

    for px, model, col_mat in pipette_specs:
        # Pipette Handle Body
        bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.16, location=(px, -0.02, 0.23))
        body = bpy.context.active_object
        body.name = f"Pipette_{model}_Handle"
        body.data.materials.append(mats["chassis_light"])

        # Ergonomic Finger Rest Hook
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, -0.035, 0.28))
        hook = bpy.context.active_object
        hook.name = f"Pipette_{model}_Hook"
        hook.scale = (0.018, 0.020, 0.012)
        hook.data.materials.append(mats["chassis_dark"])

        # Color-Coded Plunger Push Button
        bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=0.025, location=(px, -0.02, 0.32))
        btn = bpy.context.active_object
        btn.name = f"Pipette_{model}_Plunger"
        btn.data.materials.append(col_mat)

        # 3-Digit Microliter Volume Counter Window
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, -0.006, 0.24))
        vol = bpy.context.active_object
        vol.name = f"Pipette_{model}_VolumeDisplay"
        vol.scale = (0.012, 0.004, 0.035)
        vol.data.materials.append(mats["display_screen"])

        # Tapered PVDF Shaft with Tip Ejector Collar
        bpy.ops.mesh.primitive_cone_add(radius1=0.008, radius2=0.0025, depth=0.09, location=(px, -0.02, 0.105))
        tip_cone = bpy.context.active_object
        tip_cone.name = f"Pipette_{model}_Shaft"
        tip_cone.rotation_euler = (math.radians(180), 0, 0)
        tip_cone.data.materials.append(mats["ptfe_white"])

        # Stainless Steel Ejector Arm
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0018, depth=0.08, location=(px, -0.028, 0.115))
        ejector = bpy.context.active_object
        ejector.name = f"Pipette_{model}_EjectorArm"
        ejector.data.materials.append(mats["stainless"])

    # Polypropylene Pipette Tip Box (96-Well Rack)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.14, 0.10, 0.035))
    box = bpy.context.active_object
    box.name = "TipBox_Housing"
    box.scale = (0.12, 0.085, 0.05)
    box.data.materials.append(mats["chassis_light"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.14, 0.10, 0.065))
    lid = bpy.context.active_object
    lid.name = "TipBox_TransparentLid"
    lid.scale = (0.122, 0.087, 0.025)
    lid.data.materials.append(mats["acrylic_clear"])

    # Perforated Tip Plate Deck
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.14, 0.10, 0.055))
    deck = bpy.context.active_object
    deck.name = "TipBox_TipDeck"
    deck.scale = (0.11, 0.075, 0.006)
    deck.data.materials.append(mats["accent_cyan"])

    export_glb(OUTPUT_DIR / "SM_Micropipette_Set.glb")


# -----------------------------------------------------------------------------
# Main Execution Pipeline
# -----------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Athanor Ascension — Blender 5.x Procedural Apparatus Generator")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 60)

    mats = setup_materials()

    generators = [
        ("Rotary Evaporator", build_rotovap),
        ("Schlenk Line", build_schlenk_line),
        ("Soxhlet Extractor", build_soxhlet_extractor),
        ("HPLC Chromatography System", build_hplc_system),
        ("Benchtop Microcentrifuge", build_centrifuge),
        ("UV-Vis Spectrophotometer", build_uv_vis),
        ("Inert Atmosphere Glovebox", build_glovebox),
        ("Precision Analytical Balance", build_analytical_balance),
        ("Separatory Funnel 500mL", build_separatory_funnel),
        ("NMR Spectrometer 500MHz", build_nmr_spectrometer),
        ("Magnetic Stirrer Hotplate", build_magnetic_stirrer),
        ("Ducted Class II Fume Hood", build_fume_hood),
        ("Micropipette Set & Carousel", build_micropipette_set),
    ]

    for title, gen_func in generators:
        print(f"\n[GENERATING] {title}...")
        gen_func(mats)

    print("\n" + "=" * 60)
    print("SUCCESS: All 13 Laboratory Apparatus GLB models generated!")
    print("=" * 60)


if __name__ == "__main__":
    main()
