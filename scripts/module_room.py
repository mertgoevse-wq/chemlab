"""
Module 1: Room Architecture, Floor, Walls, Ceiling, and Lighting
Constructs the clinical laboratory room framework.
"""

import math

import bpy


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def build_room():
    print(">>> Building Lab Architecture...")

    clean_scene()

    # Create / Get Collection
    col_name = "01_Architecture"
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
    # Floor: Polished Epoxy Resin
    mat_floor = bpy.data.materials.get("Mat_Floor_Epoxy") or bpy.data.materials.new(
        name="Mat_Floor_Epoxy"
    )
    mat_floor.use_nodes = True
    bsdf = mat_floor.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.79, 0.83, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.16
        bsdf.inputs["Metallic"].default_value = 0.05

    # Walls: Cleanroom White with Satin finish
    mat_wall = bpy.data.materials.get("Mat_Wall_Cleanroom") or bpy.data.materials.new(
        name="Mat_Wall_Cleanroom"
    )
    mat_wall.use_nodes = True
    bsdf = mat_wall.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.94, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45

    # Safety Accent Stripe: Lab Cyan/Blue
    mat_stripe = bpy.data.materials.get("Mat_Safety_Cyan") or bpy.data.materials.new(
        name="Mat_Safety_Cyan"
    )
    mat_stripe.use_nodes = True
    bsdf = mat_stripe.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.55, 0.75, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.25

    # Baseboard: Dark Charcoal Gray
    mat_baseboard = bpy.data.materials.get("Mat_Baseboard") or bpy.data.materials.new(
        name="Mat_Baseboard"
    )
    mat_baseboard.use_nodes = True
    bsdf = mat_baseboard.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.16, 0.18, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3

    # Ceiling Tiles
    mat_ceiling = bpy.data.materials.get("Mat_Ceiling_Acoustic") or bpy.data.materials.new(
        name="Mat_Ceiling_Acoustic"
    )
    mat_ceiling.use_nodes = True
    bsdf = mat_ceiling.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.88, 0.89, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85

    # LED Panel Emission: 5000K daylight white
    mat_led = bpy.data.materials.get("Mat_LED_Panel") or bpy.data.materials.new(
        name="Mat_LED_Panel"
    )
    mat_led.use_nodes = True
    bsdf = mat_led.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 0.98, 0.95, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.98, 0.95, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 4.5

    # Door Frame & Stainless Steel
    mat_metal = bpy.data.materials.get("Mat_Steel_Brushed") or bpy.data.materials.new(
        name="Mat_Steel_Brushed"
    )
    mat_metal.use_nodes = True
    bsdf = mat_metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.8, 0.82, 0.84, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.92
        bsdf.inputs["Roughness"].default_value = 0.25

    # Glass
    mat_glass = bpy.data.materials.get("Mat_Safety_Glass") or bpy.data.materials.new(
        name="Mat_Safety_Glass"
    )
    mat_glass.use_nodes = True
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.98, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.04
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 1.0
        bsdf.inputs["IOR"].default_value = 1.45

    ROOM_X = 10.0
    ROOM_Y = 8.0
    ROOM_Z = 3.4

    # 2. Floor Plane
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor_Epoxy"
    floor.scale = (ROOM_X, ROOM_Y, 1.0)
    floor.data.materials.append(mat_floor)
    link_obj(floor)

    # 3. Baseboards along walls
    baseboard_configs = [
        ((0, -ROOM_Y / 2, 0.06), (ROOM_X, 0.04, 0.12), "Baseboard_South"),
        ((0, ROOM_Y / 2, 0.06), (ROOM_X, 0.04, 0.12), "Baseboard_North"),
        ((-ROOM_X / 2, 0, 0.06), (0.04, ROOM_Y, 0.12), "Baseboard_West"),
        ((ROOM_X / 2, 0, 0.06), (0.04, ROOM_Y, 0.12), "Baseboard_East"),
    ]
    for loc, scl, name in baseboard_configs:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        bb = bpy.context.active_object
        bb.name = name
        bb.scale = scl
        bb.data.materials.append(mat_baseboard)
        link_obj(bb)

    # 4. Back Wall (North)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, ROOM_Y / 2, ROOM_Z / 2))
    w_north = bpy.context.active_object
    w_north.name = "Wall_North"
    w_north.scale = (ROOM_X, 0.15, ROOM_Z)
    w_north.data.materials.append(mat_wall)
    link_obj(w_north)

    # Safety Stripe on North Wall (at height 1.2m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, ROOM_Y / 2 - 0.08, 1.2))
    stripe_n = bpy.context.active_object
    stripe_n.name = "Stripe_North"
    stripe_n.scale = (ROOM_X, 0.02, 0.15)
    stripe_n.data.materials.append(mat_stripe)
    link_obj(stripe_n)

    # 5. Side Wall (West)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-ROOM_X / 2, 0, ROOM_Z / 2))
    w_west = bpy.context.active_object
    w_west.name = "Wall_West"
    w_west.scale = (0.15, ROOM_Y, ROOM_Z)
    w_west.data.materials.append(mat_wall)
    link_obj(w_west)

    # Safety Stripe on West Wall
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-ROOM_X / 2 + 0.08, 0, 1.2))
    stripe_w = bpy.context.active_object
    stripe_w.name = "Stripe_West"
    stripe_w.scale = (0.02, ROOM_Y, 0.15)
    stripe_w.data.materials.append(mat_stripe)
    link_obj(stripe_w)

    # 6. Side Wall (East)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ROOM_X / 2, 1.0, ROOM_Z / 2))
    w_east_top = bpy.context.active_object
    w_east_top.name = "Wall_East"
    w_east_top.scale = (0.15, ROOM_Y, ROOM_Z)
    w_east_top.data.materials.append(mat_wall)
    link_obj(w_east_top)

    # 7. Laboratory Door (on East wall at y=-2.0)
    # Door frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ROOM_X / 2 - 0.04, -2.0, 1.15))
    door_frame = bpy.context.active_object
    door_frame.name = "Door_Frame"
    door_frame.scale = (0.18, 1.15, 2.3)
    door_frame.data.materials.append(mat_metal)
    link_obj(door_frame)

    # Door panel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ROOM_X / 2 - 0.04, -2.0, 1.1))
    door_panel = bpy.context.active_object
    door_panel.name = "Door_Panel"
    door_panel.scale = (0.08, 1.0, 2.15)
    door_panel.data.materials.append(mat_wall)
    link_obj(door_panel)

    # Door Window
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ROOM_X / 2 - 0.04, -2.0, 1.45))
    door_win = bpy.context.active_object
    door_win.name = "Door_Window"
    door_win.scale = (0.09, 0.35, 0.75)
    door_win.data.materials.append(mat_glass)
    link_obj(door_win)

    # Door Handle
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.015, depth=0.25, location=(ROOM_X / 2 - 0.12, -1.6, 1.05)
    )
    handle = bpy.context.active_object
    handle.name = "Door_Handle"
    handle.rotation_euler = (0, math.radians(90), 0)
    handle.data.materials.append(mat_metal)
    link_obj(handle)

    # 8. Ceiling Plane
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, ROOM_Z))
    ceiling = bpy.context.active_object
    ceiling.name = "Ceiling_Acoustic"
    ceiling.scale = (ROOM_X, ROOM_Y, 1.0)
    ceiling.data.materials.append(mat_ceiling)
    link_obj(ceiling)

    # 9. Recessed LED Troffer Lights & Area Lamps (2x3 Grid)
    light_xs = [-2.5, 0.0, 2.5]
    light_ys = [-1.5, 1.5]

    for i, lx in enumerate(light_xs):
        for j, ly in enumerate(light_ys):
            # Panel Mesh
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx, ly, ROOM_Z - 0.02))
            panel = bpy.context.active_object
            panel.name = f"LED_Panel_{i}_{j}"
            panel.scale = (1.2, 0.6, 0.04)
            panel.data.materials.append(mat_led)
            link_obj(panel)

            # Area Light underneath panel
            bpy.ops.object.light_add(type="AREA", radius=0.5, location=(lx, ly, ROOM_Z - 0.08))
            light = bpy.context.active_object
            light.name = f"Lamp_Area_{i}_{j}"
            light.data.energy = 220.0
            light.data.size = 1.2
            light.data.size_y = 0.6
            light.data.color = (0.96, 0.98, 1.0)
            link_obj(light)

    # 10. Main Perspective Camera
    cam_data = bpy.data.cameras.new("Cam_Lab_Overview")
    cam_data.lens = 28.0
    cam_obj = bpy.data.objects.new("Cam_Lab_Overview", cam_data)
    cam_obj.location = (5.5, -4.8, 2.9)
    cam_obj.rotation_euler = (math.radians(65), 0, math.radians(45))
    col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Set viewport to material preview
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"

    print(">>> Lab Architecture constructed successfully!")


build_room()
