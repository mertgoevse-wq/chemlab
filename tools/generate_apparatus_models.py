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

import sys
import math
from pathlib import Path
import bpy

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "game" / "assets" / "apparatus"
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
    }


def export_glb(filepath):
    """Exports all scene objects into an optimized binary GLTF (.glb) file."""
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
    ]

    for title, gen_func in generators:
        print(f"\n[GENERATING] {title}...")
        gen_func(mats)

    print("\n" + "=" * 60)
    print("SUCCESS: All 8 Laboratory Apparatus GLB models generated!")
    print("=" * 60)


if __name__ == "__main__":
    main()
