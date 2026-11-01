"""
Module 2: Laboratory Furniture, Workstations, Island Benches, and Sink Station
Constructs high-end ergonomic laboratory benches and washing facilities.
"""

import math

import bpy


def build_furniture():
    print(">>> Building Lab Furniture & Workstations...")

    # Collection
    col_name = "02_Furniture"
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
    # Ceramic/Epoxy Countertop (Chemical Resistant Charcoal)
    mat_top = bpy.data.materials.get("Mat_Countertop_Ceramic") or bpy.data.materials.new(
        name="Mat_Countertop_Ceramic"
    )
    mat_top.use_nodes = True
    bsdf = mat_top.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.12, 0.13, 0.15, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.22
        bsdf.inputs["Metallic"].default_value = 0.08

    # Steel Frame: Clean Medical Gray / White
    mat_frame = bpy.data.materials.get("Mat_Steel_Frame") or bpy.data.materials.new(
        name="Mat_Steel_Frame"
    )
    mat_frame.use_nodes = True
    bsdf = mat_frame.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.88, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
        bsdf.inputs["Metallic"].default_value = 0.3

    # Cabinets: White Laminate with Lab Cyan Accents
    mat_cabinet = bpy.data.materials.get("Mat_Cabinet_Laminate") or bpy.data.materials.new(
        name="Mat_Cabinet_Laminate"
    )
    mat_cabinet.use_nodes = True
    bsdf = mat_cabinet.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.4

    # Handles / Metal Chrome
    mat_chrome = bpy.data.materials.get("Mat_Chrome_Polished") or bpy.data.materials.new(
        name="Mat_Chrome_Polished"
    )
    mat_chrome.use_nodes = True
    bsdf = mat_chrome.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.96, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.98
        bsdf.inputs["Roughness"].default_value = 0.12

    # Stainless Steel Sink
    mat_sink = bpy.data.materials.get("Mat_Stainless_Sink") or bpy.data.materials.new(
        name="Mat_Stainless_Sink"
    )
    mat_sink.use_nodes = True
    bsdf = mat_sink.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.80, 0.82, 0.85, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.95
        bsdf.inputs["Roughness"].default_value = 0.18

    # Service Tap Colors: Gas (Yellow), Vacuum (Gray), DI Water (Cyan)
    mat_tap_gas = bpy.data.materials.get("Mat_Tap_Gas") or bpy.data.materials.new(
        name="Mat_Tap_Gas"
    )
    mat_tap_gas.use_nodes = True
    bsdf = mat_tap_gas.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.75, 0.05, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3

    # Reagent Shelf Glass/Acrylic
    mat_shelf = bpy.data.materials.get("Mat_Shelf_Resin") or bpy.data.materials.new(
        name="Mat_Shelf_Resin"
    )
    mat_shelf.use_nodes = True
    bsdf = mat_shelf.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.88, 0.92, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.2

    # Helper function to create an island lab bench
    def create_island_bench(center_x, center_y, bench_id):
        LENGTH = 3.4
        WIDTH = 1.3
        HEIGHT = 0.90
        TOP_THICKNESS = 0.045

        # 1. Countertop
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(center_x, center_y, HEIGHT - TOP_THICKNESS / 2)
        )
        top = bpy.context.active_object
        top.name = f"Bench_{bench_id}_Worktop"
        top.scale = (WIDTH, LENGTH, TOP_THICKNESS)
        top.data.materials.append(mat_top)
        link_obj(top)

        # 2. Steel Legs & Frame (4 corners)
        leg_offset_x = WIDTH / 2 - 0.06
        leg_offset_y = LENGTH / 2 - 0.06
        leg_positions = [
            (center_x - leg_offset_x, center_y - leg_offset_y),
            (center_x + leg_offset_x, center_y - leg_offset_y),
            (center_x - leg_offset_x, center_y + leg_offset_y),
            (center_x + leg_offset_x, center_y + leg_offset_y),
        ]
        for idx, (lx, ly) in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cube_add(
                size=1.0, location=(lx, ly, (HEIGHT - TOP_THICKNESS) / 2)
            )
            leg = bpy.context.active_object
            leg.name = f"Bench_{bench_id}_Leg_{idx}"
            leg.scale = (0.05, 0.05, HEIGHT - TOP_THICKNESS)
            leg.data.materials.append(mat_frame)
            link_obj(leg)

        # 3. Under-counter Cabinet Blocks (2 units per bench)
        cab_ys = [center_y - 0.75, center_y + 0.75]
        for c_idx, cy in enumerate(cab_ys):
            cab_height = 0.74
            cab_width = WIDTH - 0.14
            cab_len = 0.95
            bpy.ops.mesh.primitive_cube_add(
                size=1.0, location=(center_x, cy, cab_height / 2 + 0.08)
            )
            cab = bpy.context.active_object
            cab.name = f"Bench_{bench_id}_Cabinet_{c_idx}"
            cab.scale = (cab_width, cab_len, cab_height)
            cab.data.materials.append(mat_cabinet)
            link_obj(cab)

            # Drawer pull handles on both accessible sides (East and West)
            for side in [-1, 1]:
                for h_level in [0.25, 0.45, 0.65]:
                    hx = center_x + side * (cab_width / 2 + 0.02)
                    hy = cy
                    hz = 0.08 + h_level
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz))
                    handle = bpy.context.active_object
                    handle.name = f"Bench_{bench_id}_Handle_{c_idx}_{side}_{int(h_level * 100)}"
                    handle.scale = (0.015, 0.18, 0.02)
                    handle.data.materials.append(mat_chrome)
                    link_obj(handle)

        # 4. Central Reagent Shelf Bridge (Above Table Center)
        # Vertical Support Stanchions (2 upright posts)
        post_y_offsets = [-LENGTH / 2 + 0.25, LENGTH / 2 - 0.25]
        POST_HEIGHT = 0.75
        for p_idx, py in enumerate(post_y_offsets):
            bpy.ops.mesh.primitive_cube_add(
                size=1.0, location=(center_x, center_y + py, HEIGHT + POST_HEIGHT / 2)
            )
            post = bpy.context.active_object
            post.name = f"Bench_{bench_id}_Post_{p_idx}"
            post.scale = (0.05, 0.05, POST_HEIGHT)
            post.data.materials.append(mat_frame)
            link_obj(post)

        # 2 Tier Shelves
        for s_idx, s_h in enumerate([0.35, 0.65]):
            shelf_z = HEIGHT + s_h
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y, shelf_z))
            shelf = bpy.context.active_object
            shelf.name = f"Bench_{bench_id}_Shelf_{s_idx}"
            shelf.scale = (0.35, LENGTH - 0.4, 0.025)
            shelf.data.materials.append(mat_shelf)
            link_obj(shelf)

            # Safety Retainer Guardrails (keeps chemical bottles from slipping off)
            for rail_side in [-1, 1]:
                rx = center_x + rail_side * 0.18
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=0.006, depth=LENGTH - 0.4, location=(rx, center_y, shelf_z + 0.035)
                )
                rail = bpy.context.active_object
                rail.name = f"Bench_{bench_id}_Rail_{s_idx}_{rail_side}"
                rail.rotation_euler = (math.radians(90), 0, 0)
                rail.data.materials.append(mat_chrome)
                link_obj(rail)

        # 5. Service Spine / Utility Turrets (Gas & Electric outlets on tabletop center)
        for tap_idx, ty in enumerate([-0.6, 0.6]):
            # Base Turret
            bpy.ops.mesh.primitive_cube_add(
                size=1.0, location=(center_x, center_y + ty, HEIGHT + 0.07)
            )
            turret = bpy.context.active_object
            turret.name = f"Bench_{bench_id}_UtilityTurret_{tap_idx}"
            turret.scale = (0.12, 0.12, 0.14)
            turret.data.materials.append(mat_frame)
            link_obj(turret)

            # Dual Gas Taps (pointed sideways)
            for g_side in [-1, 1]:
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=0.012,
                    depth=0.08,
                    location=(center_x + g_side * 0.08, center_y + ty, HEIGHT + 0.10),
                )
                tap = bpy.context.active_object
                tap.name = f"Bench_{bench_id}_GasTap_{tap_idx}_{g_side}"
                tap.rotation_euler = (0, math.radians(90), 0)
                tap.data.materials.append(mat_tap_gas)
                link_obj(tap)

    # Build the two central island benches
    create_island_bench(-1.6, 0.0, "Island_A")
    create_island_bench(1.6, 0.0, "Island_B")

    # 2. Side Perimeter Workstation (West Wall, for balances & instruments)
    PERIM_X = -4.2
    PERIM_Y = 1.6
    PERIM_LEN = 3.2
    PERIM_W = 0.8
    PERIM_H = 0.90
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(PERIM_X, PERIM_Y, PERIM_H - 0.025))
    perim_top = bpy.context.active_object
    perim_top.name = "Perimeter_Bench_Top"
    perim_top.scale = (PERIM_W, PERIM_LEN, 0.05)
    perim_top.data.materials.append(mat_top)
    link_obj(perim_top)

    # Perimeter Bench Cabinets
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(PERIM_X, PERIM_Y, (PERIM_H - 0.05) / 2))
    perim_cab = bpy.context.active_object
    perim_cab.name = "Perimeter_Bench_Cabinet"
    perim_cab.scale = (PERIM_W - 0.05, PERIM_LEN - 0.1, PERIM_H - 0.05)
    perim_cab.data.materials.append(mat_cabinet)
    link_obj(perim_cab)

    # 3. Wet Lab Chemical Sink Station (West Wall, southern end)
    SINK_X = -4.2
    SINK_Y = -1.8
    SINK_LEN = 2.0
    SINK_W = 0.85
    SINK_H = 0.90

    # Sink Counter Unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(SINK_X, SINK_Y, SINK_H - 0.025))
    sink_counter = bpy.context.active_object
    sink_counter.name = "Sink_Countertop"
    sink_counter.scale = (SINK_W, SINK_LEN, 0.05)
    sink_counter.data.materials.append(mat_top)
    link_obj(sink_counter)

    # Dual Basins (Indented stainless steel basins)
    for b_idx, by_off in enumerate([-0.4, 0.4]):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(SINK_X + 0.02, SINK_Y + by_off, SINK_H - 0.12)
        )
        basin = bpy.context.active_object
        basin.name = f"Sink_Basin_{b_idx}"
        basin.scale = (0.50, 0.55, 0.28)
        basin.data.materials.append(mat_sink)
        link_obj(basin)

        # Basin Rim
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(SINK_X + 0.02, SINK_Y + by_off, SINK_H + 0.01)
        )
        rim = bpy.context.active_object
        rim.name = f"Sink_Rim_{b_idx}"
        rim.scale = (0.56, 0.61, 0.02)
        rim.data.materials.append(mat_sink)
        link_obj(rim)

    # Gooseneck Mixer Faucet (Arched lab tap)
    faucet_x = SINK_X - 0.22
    faucet_y = SINK_Y
    # Vertical Base Pillar
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.02, depth=0.35, location=(faucet_x, faucet_y, SINK_H + 0.18)
    )
    tap_pillar = bpy.context.active_object
    tap_pillar.name = "Faucet_Pillar"
    tap_pillar.data.materials.append(mat_chrome)
    link_obj(tap_pillar)

    # Arched Gooseneck Spout
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.015, depth=0.22, location=(faucet_x + 0.08, faucet_y, SINK_H + 0.38)
    )
    tap_neck = bpy.context.active_object
    tap_neck.name = "Faucet_Gooseneck"
    tap_neck.rotation_euler = (0, math.radians(45), 0)
    tap_neck.data.materials.append(mat_chrome)
    link_obj(tap_neck)

    # Downward Aerator Nozzle
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.012, depth=0.10, location=(faucet_x + 0.16, faucet_y, SINK_H + 0.35)
    )
    tap_nozzle = bpy.context.active_object
    tap_nozzle.name = "Faucet_Nozzle"
    tap_nozzle.data.materials.append(mat_chrome)
    link_obj(tap_nozzle)

    # Wall-Mounted Drying Pegboard (above the sink on the west wall)
    BOARD_X = -4.90
    BOARD_Y = SINK_Y
    BOARD_Z = 1.85
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(BOARD_X, BOARD_Y, BOARD_Z))
    pegboard = bpy.context.active_object
    pegboard.name = "Sink_Pegboard_Backing"
    pegboard.scale = (0.04, 1.4, 0.9)
    pegboard.data.materials.append(mat_cabinet)
    link_obj(pegboard)

    # Pegboard Pins for drying glassware (grid of tilted pins)
    pin_mat = bpy.data.materials.get("Mat_Peg_Plastic") or bpy.data.materials.new(
        name="Mat_Peg_Plastic"
    )
    pin_mat.use_nodes = True
    bsdf = pin_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.4, 0.8, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3

    for px_idx, pz in enumerate([1.55, 1.75, 1.95, 2.15]):
        for py_idx, py in enumerate([-0.5, -0.25, 0.0, 0.25, 0.5]):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.008, depth=0.14, location=(BOARD_X + 0.06, BOARD_Y + py, pz)
            )
            pin = bpy.context.active_object
            pin.name = f"Peg_Pin_{px_idx}_{py_idx}"
            pin.rotation_euler = (0, math.radians(-30), 0)  # Tilted upwards to hold flasks
            pin.data.materials.append(pin_mat)
            link_obj(pin)

    # Sink Cabinet under unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(SINK_X, SINK_Y, (SINK_H - 0.05) / 2))
    sink_cab = bpy.context.active_object
    sink_cab.name = "Sink_Base_Cabinet"
    sink_cab.scale = (SINK_W - 0.05, SINK_LEN - 0.05, SINK_H - 0.05)
    sink_cab.data.materials.append(mat_cabinet)
    link_obj(sink_cab)

    print(">>> Lab Furniture & Workstations constructed successfully!")


build_furniture()
