"""
Module 4: Chemistry Laboratory Apparatus, Glassware, Bunsen Burner, Magnetic Stirrer, and Reagents
Constructs high-detail chemical equipment placed upon the lab benches and inside the fume hood.
"""

import math

import bpy


def build_apparatus():
    print(">>> Building Chemistry Apparatus, Glassware & Reagents...")

    # Collection
    col_name = "04_Apparatus_Chemicals"
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

    # 1. High-Quality Photorealistic Materials
    # Borosilicate Glass
    mat_glass = bpy.data.materials.get("Mat_Borosilicate_Glass") or bpy.data.materials.new(
        name="Mat_Borosilicate_Glass"
    )
    mat_glass.use_nodes = True
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.98, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.02
        bsdf.inputs["IOR"].default_value = 1.474  # True IOR of Pyrex / Borosilicate Glass
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 1.0

    # Amber Glass (for light-sensitive chemical storage)
    mat_amber = bpy.data.materials.get("Mat_Amber_Glass") or bpy.data.materials.new(
        name="Mat_Amber_Glass"
    )
    mat_amber.use_nodes = True
    bsdf = mat_amber.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.45, 0.22, 0.04, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["IOR"].default_value = 1.52
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.85
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.85

    # Chemical Liquid 1: Copper Sulfate Solution (Vibrant Cyan)
    mat_liq_blue = bpy.data.materials.get("Mat_Liquid_CopperSulfate") or bpy.data.materials.new(
        name="Mat_Liquid_CopperSulfate"
    )
    mat_liq_blue.use_nodes = True
    bsdf = mat_liq_blue.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.65, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.02
        bsdf.inputs["IOR"].default_value = 1.34
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.95
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.95

    # Chemical Liquid 2: Fluorescein / Nickel Solution (Electric Green)
    mat_liq_green = bpy.data.materials.get("Mat_Liquid_NickelGreen") or bpy.data.materials.new(
        name="Mat_Liquid_NickelGreen"
    )
    mat_liq_green.use_nodes = True
    bsdf = mat_liq_green.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.92, 0.25, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.02
        bsdf.inputs["IOR"].default_value = 1.34
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.95
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.95

    # Chemical Liquid 3: Potassium Permanganate (Deep Purple)
    mat_liq_purple = bpy.data.materials.get("Mat_Liquid_Permanganate") or bpy.data.materials.new(
        name="Mat_Liquid_Permanganate"
    )
    mat_liq_purple.use_nodes = True
    bsdf = mat_liq_purple.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.55, 0.05, 0.65, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.02
        bsdf.inputs["IOR"].default_value = 1.35
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.90
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.90

    # Chemical Liquid 4: Clear Water Solution
    mat_liq_water = bpy.data.materials.get("Mat_Liquid_Water") or bpy.data.materials.new(
        name="Mat_Liquid_Water"
    )
    mat_liq_water.use_nodes = True
    bsdf = mat_liq_water.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.96, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.01
        bsdf.inputs["IOR"].default_value = 1.333
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.98
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.98

    # Bunsen Flame Core (Inner Intense Blue/Cyan Emission)
    mat_flame_inner = bpy.data.materials.get("Mat_Flame_InnerCone") or bpy.data.materials.new(
        name="Mat_Flame_InnerCone"
    )
    mat_flame_inner.use_nodes = True
    bsdf = mat_flame_inner.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.1, 0.8, 1.0, 1.0)
        bsdf.inputs["Emission Color"].default_value = (0.1, 0.85, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 18.0

    # Bunsen Flame Outer (Warm Blue/Violet Sheath)
    mat_flame_outer = bpy.data.materials.get("Mat_Flame_OuterCone") or bpy.data.materials.new(
        name="Mat_Flame_OuterCone"
    )
    mat_flame_outer.use_nodes = True
    bsdf = mat_flame_outer.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.3, 0.95, 1.0)
        bsdf.inputs["Emission Color"].default_value = (0.15, 0.35, 0.95, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 8.0

    # Brass Collar & Metals
    mat_brass = bpy.data.materials.get("Mat_Brass_Polished") or bpy.data.materials.new(
        name="Mat_Brass_Polished"
    )
    mat_brass.use_nodes = True
    bsdf = mat_brass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.78, 0.32, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.95
        bsdf.inputs["Roughness"].default_value = 0.22

    # Rubber Tubing (Gas Hose)
    mat_rubber = bpy.data.materials.get("Mat_Rubber_Orange") or bpy.data.materials.new(
        name="Mat_Rubber_Orange"
    )
    mat_rubber.use_nodes = True
    bsdf = mat_rubber.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.38, 0.08, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.6

    # Ceramic Hotplate Surface
    mat_ceramic_white = bpy.data.materials.get("Mat_Ceramic_White") or bpy.data.materials.new(
        name="Mat_Ceramic_White"
    )
    mat_ceramic_white.use_nodes = True
    bsdf = mat_ceramic_white.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.15

    # Instrument Body (Lab Blue/Gray)
    mat_instrument = bpy.data.materials.get("Mat_Instrument_Body") or bpy.data.materials.new(
        name="Mat_Instrument_Body"
    )
    mat_instrument.use_nodes = True
    bsdf = mat_instrument.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.25, 0.35, 0.45, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3

    # Reusable Metal & Dark
    mat_metal = bpy.data.materials.get("Mat_Steel_Brushed")
    mat_dark = bpy.data.materials.get("Mat_Baseboard")
    mat_chrome = bpy.data.materials.get("Mat_Chrome_Polished")

    BENCH_TOP_Z = 0.90  # Height of the island bench worktops

    # =========================================================================
    # 2. Erlenmeyer Flasks (Conical Glassware with Colorful Chemical Solutions)
    # =========================================================================
    def create_erlenmeyer(x, y, scale_factor=1.0, mat_solution=mat_liq_blue, name="Flask"):
        z_base = BENCH_TOP_Z
        # Conical body
        r_bottom = 0.08 * scale_factor
        r_mid = 0.03 * scale_factor
        h_cone = 0.13 * scale_factor
        bpy.ops.mesh.primitive_cone_add(
            radius1=r_bottom, radius2=r_mid, depth=h_cone, location=(x, y, z_base + h_cone / 2)
        )
        body = bpy.context.active_object
        body.name = f"{name}_Glass_Cone"
        body.data.materials.append(mat_glass)
        link_obj(body)

        # Neck
        h_neck = 0.07 * scale_factor
        r_neck = 0.025 * scale_factor
        bpy.ops.mesh.primitive_cylinder_add(
            radius=r_neck, depth=h_neck, location=(x, y, z_base + h_cone + h_neck / 2)
        )
        neck = bpy.context.active_object
        neck.name = f"{name}_Glass_Neck"
        neck.data.materials.append(mat_glass)
        link_obj(neck)

        # Flat rim collar
        bpy.ops.mesh.primitive_torus_add(
            major_radius=r_neck,
            minor_radius=0.004 * scale_factor,
            location=(x, y, z_base + h_cone + h_neck),
        )
        rim = bpy.context.active_object
        rim.name = f"{name}_Glass_Rim"
        rim.data.materials.append(mat_glass)
        link_obj(rim)

        # Liquid volume inside
        h_liq = h_cone * 0.55
        r_liq_top = r_bottom - (r_bottom - r_mid) * 0.55
        bpy.ops.mesh.primitive_cone_add(
            radius1=r_bottom - 0.005,
            radius2=r_liq_top,
            depth=h_liq,
            location=(x, y, z_base + h_liq / 2 + 0.005),
        )
        liq = bpy.context.active_object
        liq.name = f"{name}_Solution"
        liq.data.materials.append(mat_solution)
        link_obj(liq)

    # Place Flasks on Island Bench A (x=-1.3)
    create_erlenmeyer(
        -1.3, -0.4, scale_factor=1.0, mat_solution=mat_liq_blue, name="Erlenmeyer_500ml_Blue"
    )
    create_erlenmeyer(
        -1.15, -0.6, scale_factor=0.8, mat_solution=mat_liq_green, name="Erlenmeyer_250ml_Green"
    )
    create_erlenmeyer(
        -1.45, -0.65, scale_factor=0.75, mat_solution=mat_liq_purple, name="Erlenmeyer_250ml_Purple"
    )

    # =========================================================================
    # 3. Chemical Beakers (Cylindrical Glassware with Spouts)
    # =========================================================================
    def create_beaker(
        x, y, radius=0.05, height=0.12, mat_sol=mat_liq_water, fill_ratio=0.6, name="Beaker"
    ):
        z_base = BENCH_TOP_Z
        # Glass Wall
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius, depth=height, location=(x, y, z_base + height / 2)
        )
        beaker = bpy.context.active_object
        beaker.name = f"{name}_Glass"
        beaker.data.materials.append(mat_glass)
        link_obj(beaker)

        # Liquid inside
        if fill_ratio > 0.0:
            h_fill = height * fill_ratio
            bpy.ops.mesh.primitive_cylinder_add(
                radius=radius - 0.004, depth=h_fill, location=(x, y, z_base + h_fill / 2 + 0.004)
            )
            sol = bpy.context.active_object
            sol.name = f"{name}_Liquid"
            sol.data.materials.append(mat_sol)
            link_obj(sol)

    # Place Beakers on Island Bench A
    create_beaker(
        -1.3,
        0.4,
        radius=0.055,
        height=0.13,
        mat_sol=mat_liq_green,
        fill_ratio=0.65,
        name="Beaker_400ml_Green",
    )
    create_beaker(
        -1.15,
        0.55,
        radius=0.04,
        height=0.09,
        mat_sol=mat_liq_blue,
        fill_ratio=0.45,
        name="Beaker_150ml_Blue",
    )

    # =========================================================================
    # 4. Graduated Measuring Cylinder
    # =========================================================================
    CYL_X = -1.45
    CYL_Y = 0.55
    # Hexagonal Anti-Roll Base
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6, radius=0.04, depth=0.015, location=(CYL_X, CYL_Y, BENCH_TOP_Z + 0.0075)
    )
    cyl_base = bpy.context.active_object
    cyl_base.name = "GradCylinder_HexBase"
    cyl_base.data.materials.append(mat_glass)
    link_obj(cyl_base)

    # Tall Glass Column
    CYL_H = 0.22
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.018, depth=CYL_H, location=(CYL_X, CYL_Y, BENCH_TOP_Z + 0.015 + CYL_H / 2)
    )
    cyl_col = bpy.context.active_object
    cyl_col.name = "GradCylinder_GlassColumn"
    cyl_col.data.materials.append(mat_glass)
    link_obj(cyl_col)

    # Liquid Meniscus inside Cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.015, depth=0.14, location=(CYL_X, CYL_Y, BENCH_TOP_Z + 0.015 + 0.07)
    )
    cyl_liq = bpy.context.active_object
    cyl_liq.name = "GradCylinder_Liquid"
    cyl_liq.data.materials.append(mat_liq_blue)
    link_obj(cyl_liq)

    # =========================================================================
    # 5. Precision Test Tube Rack with 8 Analytical Color Gradient Tubes
    # =========================================================================
    RACK_X = -1.3
    RACK_Y = -1.1
    RACK_W = 0.12
    RACK_L = 0.36
    RACK_H = 0.14

    # Rack Base & Top Plates (Clean Acrylic / White Polypropylene)
    for rz in [BENCH_TOP_Z + 0.015, BENCH_TOP_Z + RACK_H]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(RACK_X, RACK_Y, rz))
        r_plate = bpy.context.active_object
        r_plate.name = f"TestTubeRack_Plate_{int(rz * 100)}"
        r_plate.scale = (RACK_W, RACK_L, 0.012)
        r_plate.data.materials.append(mat_ceramic_white)
        link_obj(r_plate)

    # Rack End Pillars
    for py_off in [-RACK_L / 2 + 0.015, RACK_L / 2 - 0.015]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(RACK_X, RACK_Y + py_off, BENCH_TOP_Z + RACK_H / 2)
        )
        r_post = bpy.context.active_object
        r_post.name = f"TestTubeRack_Post_{py_off}"
        r_post.scale = (RACK_W, 0.015, RACK_H)
        r_post.data.materials.append(mat_ceramic_white)
        link_obj(r_post)

    # 8 Test Tubes with Color Gradient
    gradient_colors = [
        (0.95, 0.15, 0.15),  # pH 1 Acidic Red
        (0.95, 0.55, 0.10),  # pH 4 Orange
        (0.95, 0.85, 0.05),  # pH 6 Yellow
        (0.15, 0.90, 0.25),  # pH 7 Neutral Green
        (0.05, 0.65, 0.95),  # pH 9 Alkaline Cyan
        (0.15, 0.25, 0.95),  # pH 11 Deep Blue
        (0.65, 0.05, 0.85),  # pH 14 Violet
        (0.92, 0.96, 1.00),  # Pure Distilled H2O
    ]

    TUBE_R = 0.010
    TUBE_H = 0.15
    for t_idx, rgb in enumerate(gradient_colors):
        tx = RACK_X
        ty = RACK_Y - RACK_L / 2 + 0.045 + t_idx * 0.038
        tz = BENCH_TOP_Z + 0.02 + TUBE_H / 2

        # Glass Tube
        bpy.ops.mesh.primitive_cylinder_add(radius=TUBE_R, depth=TUBE_H, location=(tx, ty, tz))
        tube = bpy.context.active_object
        tube.name = f"TestTube_Glass_{t_idx}"
        tube.data.materials.append(mat_glass)
        link_obj(tube)

        # Rounded Glass Bottom
        bpy.ops.mesh.primitive_uv_sphere_add(radius=TUBE_R, location=(tx, ty, tz - TUBE_H / 2))
        t_bot = bpy.context.active_object
        t_bot.name = f"TestTube_Bottom_{t_idx}"
        t_bot.data.materials.append(mat_glass)
        link_obj(t_bot)

        # Solution inside
        mat_sol_tube = bpy.data.materials.new(name=f"Mat_TestTube_Sol_{t_idx}")
        mat_sol_tube.use_nodes = True
        bsdf = mat_sol_tube.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.02
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = 0.92
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = 0.92

        h_fill = TUBE_H * 0.6
        bpy.ops.mesh.primitive_cylinder_add(
            radius=TUBE_R - 0.002, depth=h_fill, location=(tx, ty, tz - TUBE_H / 2 + h_fill / 2)
        )
        t_liq = bpy.context.active_object
        t_liq.name = f"TestTube_Liquid_{t_idx}"
        t_liq.data.materials.append(mat_sol_tube)
        link_obj(t_liq)

    # =========================================================================
    # 6. Bunsen Burner, Real Glowing Flame, Tripod & Wire Gauze
    # =========================================================================
    BUNSEN_X = 1.3
    BUNSEN_Y = -0.5
    BUNSEN_BASE_Z = BENCH_TOP_Z

    # Heavy Round Cast Iron Base
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.065, depth=0.02, location=(BUNSEN_X, BUNSEN_Y, BUNSEN_BASE_Z + 0.01)
    )
    b_base = bpy.context.active_object
    b_base.name = "Bunsen_Base"
    b_base.data.materials.append(mat_dark)
    link_obj(b_base)

    # Gas Inlet Nipple (Projecting sideways towards utility turret)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.008, depth=0.05, location=(BUNSEN_X + 0.065, BUNSEN_Y, BUNSEN_BASE_Z + 0.02)
    )
    b_nipple = bpy.context.active_object
    b_nipple.name = "Bunsen_GasNipple"
    b_nipple.rotation_euler = (0, math.radians(90), 0)
    b_nipple.data.materials.append(mat_brass)
    link_obj(b_nipple)

    # Rubber Gas Tubing (curved hose connecting to table tap)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.007, depth=0.45, location=(BUNSEN_X + 0.18, BUNSEN_Y - 0.05, BUNSEN_BASE_Z + 0.03)
    )
    b_hose = bpy.context.active_object
    b_hose.name = "Bunsen_GasHose"
    b_hose.rotation_euler = (0, math.radians(80), math.radians(15))
    b_hose.data.materials.append(mat_rubber)
    link_obj(b_hose)

    # Knurled Air Collar (Rotatable brass sleeve with air holes)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.018, depth=0.025, location=(BUNSEN_X, BUNSEN_Y, BUNSEN_BASE_Z + 0.035)
    )
    b_collar = bpy.context.active_object
    b_collar.name = "Bunsen_AirCollar"
    b_collar.data.materials.append(mat_brass)
    link_obj(b_collar)

    # Vertical Chimney / Flame Tube
    CHIMNEY_H = 0.14
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.012,
        depth=CHIMNEY_H,
        location=(BUNSEN_X, BUNSEN_Y, BUNSEN_BASE_Z + 0.02 + CHIMNEY_H / 2),
    )
    b_chimney = bpy.context.active_object
    b_chimney.name = "Bunsen_Chimney"
    b_chimney.data.materials.append(mat_chrome)
    link_obj(b_chimney)

    # REALISTIC BUNSEN FLAME (Glowing Dual Cone)
    FLAME_BASE_Z = BUNSEN_BASE_Z + 0.02 + CHIMNEY_H

    # Inner Cone (Small, intense cyan blue cone: T ~ 1500°C)
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.012,
        radius2=0.001,
        depth=0.055,
        location=(BUNSEN_X, BUNSEN_Y, FLAME_BASE_Z + 0.0275),
    )
    flame_in = bpy.context.active_object
    flame_in.name = "Bunsen_Flame_InnerCone"
    flame_in.data.materials.append(mat_flame_inner)
    link_obj(flame_in)

    # Outer Cone (Taller sheath flame)
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.015, radius2=0.002, depth=0.12, location=(BUNSEN_X, BUNSEN_Y, FLAME_BASE_Z + 0.06)
    )
    flame_out = bpy.context.active_object
    flame_out.name = "Bunsen_Flame_OuterCone"
    flame_out.data.materials.append(mat_flame_outer)
    link_obj(flame_out)

    # Point Light for Flame Glow in Blender Viewport
    bpy.ops.object.light_add(
        type="POINT", radius=0.05, location=(BUNSEN_X, BUNSEN_Y, FLAME_BASE_Z + 0.06)
    )
    flame_light = bpy.context.active_object
    flame_light.name = "Bunsen_Flame_PointLight"
    flame_light.data.energy = 45.0
    flame_light.data.color = (0.2, 0.65, 1.0)  # Blue flame emission
    link_obj(flame_light)

    # Tripod Stand over the Bunsen Burner
    TRIPOD_H = 0.22
    TRIPOD_R = 0.09
    # Ring
    bpy.ops.mesh.primitive_torus_add(
        major_radius=TRIPOD_R,
        minor_radius=0.008,
        location=(BUNSEN_X, BUNSEN_Y, BENCH_TOP_Z + TRIPOD_H),
    )
    tri_ring = bpy.context.active_object
    tri_ring.name = "Tripod_Ring"
    tri_ring.data.materials.append(mat_dark)
    link_obj(tri_ring)

    # 3 Tripod Legs
    for leg_deg in [0, 120, 240]:
        rad = math.radians(leg_deg)
        lx = BUNSEN_X + math.cos(rad) * TRIPOD_R
        ly = BUNSEN_Y + math.sin(rad) * TRIPOD_R
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.006, depth=TRIPOD_H, location=(lx, ly, BENCH_TOP_Z + TRIPOD_H / 2)
        )
        tri_leg = bpy.context.active_object
        tri_leg.name = f"Tripod_Leg_{leg_deg}"
        tri_leg.data.materials.append(mat_dark)
        link_obj(tri_leg)

    # Ceramic Wire Gauze Mat on Tripod
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(BUNSEN_X, BUNSEN_Y, BENCH_TOP_Z + TRIPOD_H + 0.006)
    )
    gauze = bpy.context.active_object
    gauze.name = "Tripod_WireGauze"
    gauze.scale = (0.16, 0.16, 0.004)
    gauze.data.materials.append(mat_ceramic_white)
    link_obj(gauze)

    # Heated Beaker sitting on top of the gauze
    create_beaker(
        BUNSEN_X,
        BUNSEN_Y,
        radius=0.05,
        height=0.11,
        mat_sol=mat_liq_blue,
        fill_ratio=0.55,
        name="Beaker_Heated",
    )

    # =========================================================================
    # 7. Digital Magnetic Stirrer & Hotplate
    # =========================================================================
    STIR_X = 1.3
    STIR_Y = 0.5
    STIR_W = 0.22
    STIR_L = 0.28
    STIR_H = 0.085

    # Main Housing (Medical Slate/Blue)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(STIR_X, STIR_Y, BENCH_TOP_Z + STIR_H / 2))
    stir_body = bpy.context.active_object
    stir_body.name = "MagStirrer_Housing"
    stir_body.scale = (STIR_W, STIR_L, STIR_H)
    stir_body.data.materials.append(mat_instrument)
    link_obj(stir_body)

    # White Ceramic Top Plate
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(STIR_X, STIR_Y + 0.03, BENCH_TOP_Z + STIR_H + 0.005)
    )
    stir_plate = bpy.context.active_object
    stir_plate.name = "MagStirrer_TopPlate"
    stir_plate.scale = (STIR_W - 0.02, STIR_W - 0.02, 0.01)
    stir_plate.data.materials.append(mat_ceramic_white)
    link_obj(stir_plate)

    # Digital 7-Segment Display Panel (Red LED Readout: "350 RPM | 85°C")
    mat_led_red = bpy.data.materials.get("Mat_LED_Red_Display") or bpy.data.materials.new(
        name="Mat_LED_Red_Display"
    )
    mat_led_red.use_nodes = True
    bsdf = mat_led_red.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.05, 0.05, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.1, 0.1, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0

    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(STIR_X, STIR_Y - STIR_L / 2 + 0.06, BENCH_TOP_Z + STIR_H + 0.002)
    )
    disp = bpy.context.active_object
    disp.name = "MagStirrer_Display"
    disp.scale = (0.12, 0.035, 0.003)
    disp.data.materials.append(mat_led_red)
    link_obj(disp)

    # Twin Rotary Knobs (Speed & Heat)
    for k_idx, kx in enumerate([-0.05, 0.05]):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.015,
            depth=0.02,
            location=(STIR_X + kx, STIR_Y - STIR_L / 2 + 0.02, BENCH_TOP_Z + STIR_H / 2),
        )
        knob = bpy.context.active_object
        knob.name = f"MagStirrer_Knob_{k_idx}"
        knob.rotation_euler = (math.radians(90), 0, 0)
        knob.data.materials.append(mat_dark)
        link_obj(knob)

    # Beaker with active stirring on the magnetic hotplate
    create_beaker(
        STIR_X,
        STIR_Y + 0.03,
        radius=0.048,
        height=0.10,
        mat_sol=mat_liq_green,
        fill_ratio=0.50,
        name="Beaker_Stirring",
    )

    # Teflon Magnetic Stir Bar (White PTFE pill inside beaker)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.004, depth=0.025, location=(STIR_X, STIR_Y + 0.03, BENCH_TOP_Z + STIR_H + 0.015)
    )
    stir_bar = bpy.context.active_object
    stir_bar.name = "Teflon_Magnetic_StirBar"
    stir_bar.rotation_euler = (0, math.radians(90), math.radians(35))
    stir_bar.data.materials.append(mat_ceramic_white)
    link_obj(stir_bar)

    # =========================================================================
    # 8. Chemical Reagent Bottles on the Central Shelves
    # =========================================================================
    # Shelf 1 Height: BENCH_TOP_Z + 0.35 + 0.015 = 1.265m
    SHELF_Z = BENCH_TOP_Z + 0.365

    # White Plastic Cap Material
    mat_cap = bpy.data.materials.get("Mat_Cap_White") or bpy.data.materials.new(
        name="Mat_Cap_White"
    )
    mat_cap.use_nodes = True
    bsdf = mat_cap.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.94, 0.96, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35

    # Paper Label Material
    mat_label = bpy.data.materials.get("Mat_Bottle_Label") or bpy.data.materials.new(
        name="Mat_Bottle_Label"
    )
    mat_label.use_nodes = True
    bsdf = mat_label.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.96, 0.96, 0.92, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.7

    bottle_configs = [
        # Bench A Shelf (x=-1.6)
        (-1.6, -1.0, mat_amber, "Bottle_Amber_HCl"),
        (-1.6, -0.7, mat_amber, "Bottle_Amber_HNO3"),
        (-1.6, -0.4, mat_glass, "Bottle_Clear_Ethanol"),
        (-1.6, 0.4, mat_amber, "Bottle_Amber_H2SO4"),
        (-1.6, 0.7, mat_glass, "Bottle_Clear_Acetone"),
        (-1.6, 1.0, mat_glass, "Bottle_Clear_NaOH"),
        # Bench B Shelf (x=1.6)
        (1.6, -1.0, mat_amber, "Bottle_Amber_Methanol"),
        (1.6, -0.7, mat_glass, "Bottle_Clear_Isopropanol"),
        (1.6, -0.4, mat_amber, "Bottle_Amber_Toluene"),
        (1.6, 0.4, mat_glass, "Bottle_Clear_DistWater"),
        (1.6, 0.7, mat_amber, "Bottle_Amber_Ether"),
        (1.6, 1.0, mat_glass, "Bottle_Clear_AceticAcid"),
    ]

    for bx, by, mat_b, b_name in bottle_configs:
        B_R = 0.038
        B_H = 0.13
        # Cylindrical Body
        bpy.ops.mesh.primitive_cylinder_add(
            radius=B_R, depth=B_H, location=(bx, by, SHELF_Z + B_H / 2)
        )
        b_obj = bpy.context.active_object
        b_obj.name = f"{b_name}_Body"
        b_obj.data.materials.append(mat_b)
        link_obj(b_obj)

        # Neck
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.016, depth=0.03, location=(bx, by, SHELF_Z + B_H + 0.015)
        )
        b_neck = bpy.context.active_object
        b_neck.name = f"{b_name}_Neck"
        b_neck.data.materials.append(mat_b)
        link_obj(b_neck)

        # Screw Cap
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.018, depth=0.02, location=(bx, by, SHELF_Z + B_H + 0.03)
        )
        b_cap = bpy.context.active_object
        b_cap.name = f"{b_name}_Cap"
        b_cap.data.materials.append(mat_cap)
        link_obj(b_cap)

        # Front Chemical Label Placard
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(bx + B_R + 0.001, by, SHELF_Z + B_H / 2)
        )
        b_lbl = bpy.context.active_object
        b_lbl.name = f"{b_name}_Label"
        b_lbl.scale = (0.002, 0.045, 0.065)
        b_lbl.data.materials.append(mat_label)
        link_obj(b_lbl)

    # =========================================================================
    # 9. LDPE Squeeze Wash Bottles (Laboratory Wash Bottles with Curved Straws)
    # =========================================================================
    wash_configs = [
        (-1.45, 1.1, (0.05, 0.45, 0.95), "WashBottle_DI_Water"),  # Blue Cap
        (1.45, -1.1, (0.95, 0.15, 0.15), "WashBottle_Acetone"),  # Red Cap
    ]
    for wx, wy, cap_rgb, w_name in wash_configs:
        W_R = 0.042
        W_H = 0.16
        # Bottle Body (Translucent Plastic)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=W_R, depth=W_H, location=(wx, wy, BENCH_TOP_Z + W_H / 2)
        )
        w_body = bpy.context.active_object
        w_body.name = f"{w_name}_Body"
        w_body.data.materials.append(mat_ceramic_white)
        link_obj(w_body)

        # Color-coded Cap
        mat_cap_color = bpy.data.materials.new(name=f"Mat_{w_name}_Cap")
        mat_cap_color.use_nodes = True
        bsdf = mat_cap_color.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*cap_rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.35

        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.022, depth=0.03, location=(wx, wy, BENCH_TOP_Z + W_H + 0.015)
        )
        w_cap = bpy.context.active_object
        w_cap.name = f"{w_name}_Cap"
        w_cap.data.materials.append(mat_cap_color)
        link_obj(w_cap)

        # Curved Dispensing Nozzle Straw
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.005, depth=0.10, location=(wx + 0.02, wy, BENCH_TOP_Z + W_H + 0.06)
        )
        w_straw = bpy.context.active_object
        w_straw.name = f"{w_name}_Straw"
        w_straw.rotation_euler = (0, math.radians(25), 0)
        w_straw.data.materials.append(mat_ceramic_white)
        link_obj(w_straw)

    # =========================================================================
    # 10. Active Synthesis Setup inside the Fume Hood
    # =========================================================================
    HOOD_BENCH_Z = 0.90
    HOOD_X = -2.2
    HOOD_Y = 3.35

    # Lab Scissor Jack (Aluminium lift stand)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(HOOD_X, HOOD_Y - 0.1, HOOD_BENCH_Z + 0.06))
    jack = bpy.context.active_object
    jack.name = "FumeHood_LabJack"
    jack.scale = (0.18, 0.18, 0.12)
    jack.data.materials.append(mat_metal)
    link_obj(jack)

    # 1000ml Large Boiling Flask with Stirring Purple Reaction Solution
    create_erlenmeyer(
        HOOD_X,
        HOOD_Y - 0.1,
        scale_factor=1.35,
        mat_solution=mat_liq_purple,
        name="FumeHood_ReactionFlask",
    )

    print(">>> Chemistry Apparatus, Glassware & Reagents constructed successfully!")


build_apparatus()
