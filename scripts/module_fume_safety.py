"""
Module 3: Fume Hood (Digestorium), Flammables Safety Cabinet, Emergency Shower & Eye Wash, and Fire Extinguisher
Constructs primary chemical hazard safety infrastructure.
"""

import math

import bpy


def build_fume_safety():
    print(">>> Building Fume Hood & Safety Equipment...")

    # Collection
    col_name = "03_Safety_Equipment"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    def link_obj(obj):
        if obj.name not in col.objects:
            col.objects.link(obj)
        for c in list(obj.users_collection):
            if c != col:
                c.objects.unlink(obj)

    # 1. Materials
    # Safety Signal Yellow (Flammables Cabinet)
    mat_yellow = bpy.data.materials.get("Mat_Safety_Yellow") or bpy.data.materials.new(
        name="Mat_Safety_Yellow"
    )
    mat_yellow.use_nodes = True
    bsdf = mat_yellow.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.76, 0.05, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
        bsdf.inputs["Metallic"].default_value = 0.1

    # Safety Signal Red (Fire Extinguisher & Hazard Signs)
    mat_red = bpy.data.materials.get("Mat_Safety_Red") or bpy.data.materials.new(
        name="Mat_Safety_Red"
    )
    mat_red.use_nodes = True
    bsdf = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.05, 0.05, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.25

    # Safety Signal Green (Shower & Status LED)
    mat_green_led = bpy.data.materials.get("Mat_LED_Green") or bpy.data.materials.new(
        name="Mat_LED_Green"
    )
    mat_green_led.use_nodes = True
    bsdf = mat_green_led.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.95, 0.2, 1.0)
        bsdf.inputs["Emission Color"].default_value = (0.1, 1.0, 0.2, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 6.0

    # Fume Hood Outer Casing (Off-White Lab Enamel)
    mat_hood_body = bpy.data.materials.get("Mat_FumeHood_Body") or bpy.data.materials.new(
        name="Mat_FumeHood_Body"
    )
    mat_hood_body.use_nodes = True
    bsdf = mat_hood_body.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.88, 0.90, 0.92, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3

    # Fume Hood Interior Basin (Pure White Acid-Proof Ceramic)
    mat_hood_interior = bpy.data.materials.get("Mat_FumeHood_Interior") or bpy.data.materials.new(
        name="Mat_FumeHood_Interior"
    )
    mat_hood_interior.use_nodes = True
    bsdf = mat_hood_interior.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.96, 0.98, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.15

    # Fume Hood Internal Light Bar (High-intensity daylight emission)
    mat_hood_light = bpy.data.materials.get("Mat_Hood_Light") or bpy.data.materials.new(
        name="Mat_Hood_Light"
    )
    mat_hood_light.use_nodes = True
    bsdf = mat_hood_light.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 8.0

    # Reusable Metal & Glass
    mat_metal = bpy.data.materials.get("Mat_Steel_Brushed")
    mat_chrome = bpy.data.materials.get("Mat_Chrome_Polished")
    mat_glass = bpy.data.materials.get("Mat_Safety_Glass")
    mat_dark = bpy.data.materials.get("Mat_Baseboard")

    # =========================================================================
    # 1. Chemical Fume Hood (Digestorium)
    # =========================================================================
    HOOD_X = -2.2
    HOOD_Y = 3.35
    HOOD_W = 1.9
    HOOD_D = 0.95
    HOOD_H = 2.4
    BENCH_H = 0.90

    # Base Cabinet Stand under Fume Hood
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y, BENCH_H / 2))
    hood_base = bpy.context.active_object
    hood_base.name = "FumeHood_Base_Cabinet"
    hood_base.scale = (HOOD_W, HOOD_D, BENCH_H)
    hood_base.data.materials.append(mat_hood_body)
    link_obj(hood_base)

    # Base Cabinet Doors / Handles
    for s in [-0.45, 0.45]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(HOOD_X + s, HOOD_Y - HOOD_D / 2 - 0.015, BENCH_H / 2 + 0.15)
        )
        h_handle = bpy.context.active_object
        h_handle.name = f"FumeHood_Base_Handle_{s}"
        h_handle.scale = (0.02, 0.02, 0.25)
        h_handle.data.materials.append(mat_chrome)
        link_obj(h_handle)

    # Main Upper Enclosure
    UPPER_H = HOOD_H - BENCH_H  # 1.5m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y, BENCH_H + UPPER_H / 2))
    hood_body = bpy.context.active_object
    hood_body.name = "FumeHood_Upper_Body"
    hood_body.scale = (HOOD_W, HOOD_D, UPPER_H)
    hood_body.data.materials.append(mat_hood_body)
    link_obj(hood_body)

    # Interior Work Deck (Inside the chamber)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y - 0.02, BENCH_H + 0.02))
    hood_deck = bpy.context.active_object
    hood_deck.name = "FumeHood_WorkDeck"
    hood_deck.scale = (HOOD_W - 0.15, HOOD_D - 0.12, 0.04)
    hood_deck.data.materials.append(mat_hood_interior)
    link_obj(hood_deck)

    # Aerodynamic Airfoil Spill Lip (Front edge)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.02,
        depth=HOOD_W - 0.15,
        location=(HOOD_X, HOOD_Y - HOOD_D / 2 + 0.03, BENCH_H + 0.04),
    )
    airfoil = bpy.context.active_object
    airfoil.name = "FumeHood_AirFoil"
    airfoil.rotation_euler = (0, math.radians(90), 0)
    airfoil.data.materials.append(mat_metal)
    link_obj(airfoil)

    # Rear Exhaust Baffle Plates (Inside back wall)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(HOOD_X, HOOD_Y + HOOD_D / 2 - 0.08, BENCH_H + UPPER_H / 2)
    )
    baffle = bpy.context.active_object
    baffle.name = "FumeHood_RearBaffle"
    baffle.scale = (HOOD_W - 0.2, 0.02, UPPER_H - 0.2)
    baffle.data.materials.append(mat_hood_interior)
    link_obj(baffle)

    # Sliding Safety Glass Sash Window (Positioned half open at height 0.45m)
    sash_h = 0.85
    sash_z = BENCH_H + 0.50 + sash_h / 2
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y - HOOD_D / 2 + 0.03, sash_z))
    sash_glass = bpy.context.active_object
    sash_glass.name = "FumeHood_SashGlass"
    sash_glass.scale = (HOOD_W - 0.16, 0.015, sash_h)
    sash_glass.data.materials.append(mat_glass)
    link_obj(sash_glass)

    # Sash Window Bottom Handle Bar
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(HOOD_X, HOOD_Y - HOOD_D / 2 + 0.04, BENCH_H + 0.50)
    )
    sash_bar = bpy.context.active_object
    sash_bar.name = "FumeHood_SashHandle"
    sash_bar.scale = (HOOD_W - 0.14, 0.03, 0.03)
    sash_bar.data.materials.append(mat_metal)
    link_obj(sash_bar)

    # Internal Overhead Explosion-Proof Light Fixture
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y, HOOD_H - 0.06))
    hood_lamp_mesh = bpy.context.active_object
    hood_lamp_mesh.name = "FumeHood_Interior_LightPanel"
    hood_lamp_mesh.scale = (HOOD_W - 0.35, 0.25, 0.04)
    hood_lamp_mesh.data.materials.append(mat_hood_light)
    link_obj(hood_lamp_mesh)

    # Blender Spot Light inside the hood casting downward light on experiments
    bpy.ops.object.light_add(type="SPOT", radius=0.2, location=(HOOD_X, HOOD_Y, HOOD_H - 0.1))
    hood_spot = bpy.context.active_object
    hood_spot.name = "FumeHood_SpotLight"
    hood_spot.data.energy = 250.0
    hood_spot.data.spot_size = math.radians(85)
    hood_spot.data.color = (0.95, 0.98, 1.0)
    link_obj(hood_spot)

    # Control Panel (Right pillar of the hood)
    PANEL_X = HOOD_X + HOOD_W / 2 - 0.05
    PANEL_Y = HOOD_Y - HOOD_D / 2 + 0.02
    PANEL_Z = BENCH_H + 0.65

    # Digital Screen / Bezel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(PANEL_X, PANEL_Y, PANEL_Z))
    ctrl_panel = bpy.context.active_object
    ctrl_panel.name = "FumeHood_ControlDisplay"
    ctrl_panel.scale = (0.08, 0.015, 0.20)
    ctrl_panel.data.materials.append(mat_dark)
    link_obj(ctrl_panel)

    # Green Airflow Status LED Indicator
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.012, depth=0.02, location=(PANEL_X, PANEL_Y - 0.012, PANEL_Z + 0.05)
    )
    status_led = bpy.context.active_object
    status_led.name = "FumeHood_Status_LED"
    status_led.rotation_euler = (math.radians(90), 0, 0)
    status_led.data.materials.append(mat_green_led)
    link_obj(status_led)

    # Emergency Purge Button (Red)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.016, depth=0.02, location=(PANEL_X, PANEL_Y - 0.012, PANEL_Z - 0.05)
    )
    purge_btn = bpy.context.active_object
    purge_btn.name = "FumeHood_Purge_Button"
    purge_btn.rotation_euler = (math.radians(90), 0, 0)
    purge_btn.data.materials.append(mat_red)
    link_obj(purge_btn)

    # Exhaust Ductwork to Ceiling
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.18, depth=3.4 - HOOD_H, location=(HOOD_X, HOOD_Y, HOOD_H + (3.4 - HOOD_H) / 2)
    )
    exhaust_duct = bpy.context.active_object
    exhaust_duct.name = "FumeHood_ExhaustDuct"
    exhaust_duct.data.materials.append(mat_metal)
    link_obj(exhaust_duct)

    # =========================================================================
    # 2. Flammables Safety Cabinet (Type 90 Yellow Cabinet)
    # =========================================================================
    CAB_X = 2.4
    CAB_Y = 3.4
    CAB_W = 1.2
    CAB_D = 0.65
    CAB_H = 1.95

    # Main Cabinet Body
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(CAB_X, CAB_Y, CAB_H / 2))
    safety_cab = bpy.context.active_object
    safety_cab.name = "Flammables_Safety_Cabinet"
    safety_cab.scale = (CAB_W, CAB_D, CAB_H)
    safety_cab.data.materials.append(mat_yellow)
    link_obj(safety_cab)

    # Door Split line & Recessed Handles
    for d_side in [-0.28, 0.28]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(CAB_X + d_side, CAB_Y - CAB_D / 2 - 0.01, CAB_H / 2)
        )
        door_handle = bpy.context.active_object
        door_handle.name = f"Flammables_Handle_{d_side}"
        door_handle.scale = (0.04, 0.02, 0.35)
        door_handle.data.materials.append(mat_dark)
        link_obj(door_handle)

    # NFPA Warning Hazard Diamond Sign (Placard on cabinet front)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(CAB_X, CAB_Y - CAB_D / 2 - 0.015, CAB_H - 0.35)
    )
    sign_diamond = bpy.context.active_object
    sign_diamond.name = "Flammables_Hazard_Sign"
    sign_diamond.scale = (0.22, 0.01, 0.22)
    sign_diamond.rotation_euler = (0, 0, math.radians(45))  # Diamond orientation
    sign_diamond.data.materials.append(mat_red)
    link_obj(sign_diamond)

    # =========================================================================
    # 3. Emergency Shower & Eye-Wash Station
    # =========================================================================
    SHOWER_X = 4.3
    SHOWER_Y = -0.5
    SHOWER_Z = 2.5

    # Vertical Supply Pipe from Ceiling
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.025, depth=3.4 - 2.2, location=(SHOWER_X, SHOWER_Y, 2.2 + (3.4 - 2.2) / 2)
    )
    shower_pipe = bpy.context.active_object
    shower_pipe.name = "Emergency_Shower_SupplyPipe"
    shower_pipe.data.materials.append(mat_metal)
    link_obj(shower_pipe)

    # Shower Deluge Head (Conical cone diffuser)
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.18, radius2=0.03, depth=0.12, location=(SHOWER_X, SHOWER_Y, 2.35)
    )
    shower_head = bpy.context.active_object
    shower_head.name = "Emergency_Shower_Head"
    shower_head.data.materials.append(mat_yellow)
    link_obj(shower_head)

    # Triangular Pull Rod for Shower
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.006, depth=0.75, location=(SHOWER_X + 0.12, SHOWER_Y, 2.35 - 0.375)
    )
    pull_rod = bpy.context.active_object
    pull_rod.name = "Emergency_Shower_PullRod"
    pull_rod.data.materials.append(mat_yellow)
    link_obj(pull_rod)

    # Eye Wash Pedestal Unit (Below the shower at height 1.05m)
    EYE_Z = 1.05
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.03, depth=EYE_Z, location=(SHOWER_X, SHOWER_Y, EYE_Z / 2)
    )
    eye_pedestal = bpy.context.active_object
    eye_pedestal.name = "EyeWash_Pedestal"
    eye_pedestal.data.materials.append(mat_metal)
    link_obj(eye_pedestal)

    # Eye Wash Catch Bowl (Stainless steel basin)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.18, depth=0.08, location=(SHOWER_X, SHOWER_Y, EYE_Z + 0.04)
    )
    eye_bowl = bpy.context.active_object
    eye_bowl.name = "EyeWash_Bowl"
    eye_bowl.data.materials.append(mat_metal)
    link_obj(eye_bowl)

    # Dual Aerated Spray Heads
    for s_eye in [-0.06, 0.06]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.015, depth=0.05, location=(SHOWER_X + s_eye, SHOWER_Y, EYE_Z + 0.10)
        )
        spray_nozzle = bpy.context.active_object
        spray_nozzle.name = f"EyeWash_Nozzle_{s_eye}"
        spray_nozzle.data.materials.append(mat_yellow)
        link_obj(spray_nozzle)

    # Push Flag Lever ("PUSH" plate)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(SHOWER_X + 0.18, SHOWER_Y, EYE_Z + 0.08))
    push_plate = bpy.context.active_object
    push_plate.name = "EyeWash_PushPlate"
    push_plate.scale = (0.015, 0.10, 0.10)
    push_plate.data.materials.append(mat_yellow)
    link_obj(push_plate)

    # =========================================================================
    # 4. Wall-Mounted Fire Extinguisher (CO2 / Dry Chemical)
    # =========================================================================
    EXT_X = 4.88  # On the East wall
    EXT_Y = -3.2
    EXT_Z = 1.1

    # Red Pressure Cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.09, depth=0.55, location=(EXT_X - 0.10, EXT_Y, EXT_Z)
    )
    ext_body = bpy.context.active_object
    ext_body.name = "Fire_Extinguisher_Cylinder"
    ext_body.data.materials.append(mat_red)
    link_obj(ext_body)

    # Dome Top & Bottom
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(EXT_X - 0.10, EXT_Y, EXT_Z + 0.275))
    ext_dome = bpy.context.active_object
    ext_dome.name = "Fire_Extinguisher_Dome"
    ext_dome.scale = (1.0, 1.0, 0.5)
    ext_dome.data.materials.append(mat_red)
    link_obj(ext_dome)

    # Valve & Operating Lever
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(EXT_X - 0.10, EXT_Y, EXT_Z + 0.36))
    ext_valve = bpy.context.active_object
    ext_valve.name = "Fire_Extinguisher_Valve"
    ext_valve.scale = (0.05, 0.12, 0.08)
    ext_valve.data.materials.append(mat_dark)
    link_obj(ext_valve)

    # Discharge Hose & Horn
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.015, depth=0.35, location=(EXT_X - 0.12, EXT_Y - 0.09, EXT_Z + 0.15)
    )
    ext_hose = bpy.context.active_object
    ext_hose.name = "Fire_Extinguisher_Hose"
    ext_hose.data.materials.append(mat_dark)
    link_obj(ext_hose)

    # Discharge Horn (Cone)
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.045,
        radius2=0.018,
        depth=0.15,
        location=(EXT_X - 0.12, EXT_Y - 0.09, EXT_Z - 0.08),
    )
    ext_horn = bpy.context.active_object
    ext_horn.name = "Fire_Extinguisher_Horn"
    ext_horn.data.materials.append(mat_dark)
    link_obj(ext_horn)

    # Wall Mounting Bracket
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(EXT_X - 0.02, EXT_Y, EXT_Z))
    ext_bracket = bpy.context.active_object
    ext_bracket.name = "Fire_Extinguisher_Bracket"
    ext_bracket.scale = (0.04, 0.14, 0.30)
    ext_bracket.data.materials.append(mat_metal)
    link_obj(ext_bracket)

    print(">>> Fume Hood & Safety Equipment constructed successfully!")


build_fume_safety()
