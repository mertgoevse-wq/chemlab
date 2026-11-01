"""
Render Multi-Perspective Previews for ChemLab HUD & UI System
Saves persistent state to chemlab.blend and generates crisp preview renders:
- preview_hud_player.png: Full first-person immersive VR/Desktop simulation view
- preview_hud_spatial_detail.png: Detailed focus on 3D spatial overlay (tags, pH bar, thermal HUD)
- preview_hands_detail.png: Macro focus on holographic hands and color-coded interaction states
"""

import math
import os
import sys

import bpy

PROJECT_PATH = r"C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend"
OUTPUT_DIR = r"C:\Users\Win11 Pro\Desktop\chemlab"

# Ensure module_ui_hud is loaded
sys.path.append(r"C:\Users\Win11 Pro\Desktop\chemlab\scripts")
import module_ui_hud


def setup_additional_cameras():
    col = bpy.data.collections.get("06_UI_HUD_Spatial") or bpy.context.scene.collection

    # 1. Spatial Detail Camera (Focus on Floating Reagent Tags & pH Bar)
    cam_spatial_name = "Cam_HUD_Spatial_Detail"
    cam_spatial_obj = bpy.data.objects.get(cam_spatial_name)
    if not cam_spatial_obj:
        c_data = bpy.data.cameras.new(cam_spatial_name)
        c_data.lens = 45.0
        cam_spatial_obj = bpy.data.objects.new(cam_spatial_name, c_data)
        col.objects.link(cam_spatial_obj)
    cam_spatial_obj.location = (-1.05, -1.35, 1.35)
    cam_spatial_obj.rotation_euler = (math.radians(78), 0, math.radians(12))

    # 2. Holographic Hands Detail Camera (Macro focus on fingertip dots: green, yellow, blue)
    cam_hands_name = "Cam_Hands_Detail"
    cam_hands_obj = bpy.data.objects.get(cam_hands_name)
    if not cam_hands_obj:
        c_data = bpy.data.cameras.new(cam_hands_name)
        c_data.lens = 55.0
        cam_hands_obj = bpy.data.objects.new(cam_hands_name, c_data)
        col.objects.link(cam_hands_obj)
    cam_hands_obj.location = (-0.90, -1.15, 1.25)
    cam_hands_obj.rotation_euler = (math.radians(65), 0, math.radians(18))

    return cam_spatial_obj, cam_hands_obj


def render_and_save():
    print(">>> Generating and Persisting ChemLab HUD & UI System...")
    module_ui_hud.build_hud_ui()
    cam_spatial, cam_hands = setup_additional_cameras()

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    renders = [
        ("Cam_Player_HUD_View", os.path.join(OUTPUT_DIR, "preview_hud_player.png")),
        ("Cam_HUD_Spatial_Detail", os.path.join(OUTPUT_DIR, "preview_hud_spatial_detail.png")),
        ("Cam_Hands_Detail", os.path.join(OUTPUT_DIR, "preview_hands_detail.png")),
    ]

    for cam_name, out_path in renders:
        cam_obj = bpy.data.objects.get(cam_name)
        if cam_obj:
            print(f"[*] Rendering view: {cam_name} -> {out_path}")
            scene.camera = cam_obj
            scene.render.filepath = out_path
            bpy.ops.render.render(write_still=True)
            print(f"[PASS] Rendered: {out_path}")

    # Save to chemlab.blend
    print(f"[*] Persisting scene to {PROJECT_PATH}...")
    bpy.ops.wm.save_as_mainfile(filepath=PROJECT_PATH)
    print("[PASS] chemlab.blend successfully updated!")


if __name__ == "__main__":
    render_and_save()
