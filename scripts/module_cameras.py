"""
Module 5: Camera Setup, Rendering Settings & Viewport Optimization
Sets up multiple cinematic camera perspectives and optimal viewport display settings.
"""

import math

import bpy


def setup_cameras_and_render():
    print(">>> Setting up Cinematic Cameras & Render Settings...")

    col_name = "05_Cameras"
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

    # 1. Camera 1: Cinematic Workbench Detail (Focus on flasks & flame)
    cam_bench_obj = bpy.data.objects.get("Cam_Workbench_Detail")
    if not cam_bench_obj:
        cam_bench_data = bpy.data.cameras.new("Cam_Workbench_Detail")
        cam_bench_data.lens = 50.0  # 50mm portrait lens
        cam_bench_obj = bpy.data.objects.new("Cam_Workbench_Detail", cam_bench_data)
        link_obj(cam_bench_obj)
    cam_bench_obj.location = (-0.1, -1.8, 1.45)
    cam_bench_obj.rotation_euler = (math.radians(72), 0, math.radians(20))

    # 2. Camera 2: Fume Hood & Safety Focus
    cam_hood_obj = bpy.data.objects.get("Cam_FumeHood_View")
    if not cam_hood_obj:
        cam_hood_data = bpy.data.cameras.new("Cam_FumeHood_View")
        cam_hood_data.lens = 35.0
        cam_hood_obj = bpy.data.objects.new("Cam_FumeHood_View", cam_hood_data)
        link_obj(cam_hood_obj)
    cam_hood_obj.location = (-0.5, 0.8, 1.6)
    cam_hood_obj.rotation_euler = (math.radians(78), 0, math.radians(-35))

    # Set active camera to Overview (primary for desktop app display)
    overview_cam = bpy.data.objects.get("Cam_Lab_Overview")
    if overview_cam:
        bpy.context.scene.camera = overview_cam

    # Configure Render Settings for Blender 5.2 Eevee (faster, reliable)
    scene = bpy.context.scene
    try:
        # Try Eevee Next first, fall back to Cycles if not available
        if "BLENDER_EEVEE_NEXT" in [
            e.identifier for e in bpy.types.RenderEngine.bl_rna.properties["engine"].enum_items
        ]:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        else:
            scene.render.engine = "CYCLES"
    except Exception:
        scene.render.engine = "CYCLES"

    # Eevee settings optimized for this lab scene
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_bloom = False
    scene.eevee.use_gtao = True
    scene.eevee.motion_blur_fraction = 0.0

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    # Ensure all 3D viewports in the desktop GUI are set to Material Preview with scene lighting
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True

    print(">>> Camera setup complete — viewports in Material Preview mode.")
    print(">>> Render ready via Blender UI: Render → Render Image (F12)")
    print(">>> Or export via: File → Export → GLTF (.glb) for scene sharing.")


setup_cameras_and_render()
