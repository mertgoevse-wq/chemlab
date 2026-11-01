"""
Headless Blender Scene Verification Test
Executed in Blender background mode:
blender.exe -b chemlab.blend -P tests/headless_blender_test.py
"""

import os
import sys

try:
    import bpy
except ImportError:
    try:
        import pytest

        pytestmark = pytest.mark.skip(
            reason="headless_blender_test.py must be executed within Blender (bpy)"
        )
    except ImportError:
        pass
    print("FATAL: headless_blender_test.py must be executed within Blender (bpy).", file=sys.stderr)
    if "pytest" not in sys.modules:
        sys.exit(1)


def run_headless_tests():
    print("=" * 60)
    print("ChemLab Headless Scene Verification Test")
    print("=" * 60)

    failures = []
    warnings = []

    # 1. Scene existence
    scene = bpy.context.scene
    if not scene:
        failures.append("No active scene found in .blend file.")
        print("FAIL: No active scene.")
        sys.exit(1)

    print(f"[PASS] Active Scene: {scene.name}")

    # 2. Render Engine Check
    engine = scene.render.engine
    print(f"[*] Configured Render Engine: {engine}")
    valid_engines = ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"]
    if engine not in valid_engines:
        failures.append(f"Invalid render engine: {engine}. Expected one of {valid_engines}")
    else:
        print(f"[PASS] Render engine {engine} is supported.")

    # 3. Collection Structure Check
    required_collections = [
        ("01_Architecture", ["01_Architecture"]),
        ("02_Furniture", ["02_Furniture"]),
        ("03_Safety", ["03_Fume_Safety", "03_Safety_Equipment"]),
        ("04_Apparatus", ["04_Apparatus_Chemicals"]),
        ("05_Cameras_Lighting", ["05_Lighting_Cameras", "05_Cameras"]),
    ]

    scene_collection_names = [c.name for c in bpy.data.collections]
    print(f"[*] Available Collections: {scene_collection_names}")

    for group_name, allowed_names in required_collections:
        match = any(name in scene_collection_names for name in allowed_names)
        if not match:
            warnings.append(
                f"Required collection group '{group_name}' (expected: {allowed_names}) is missing."
            )
        else:
            print(f"[PASS] Required collection group present: {group_name}")

    # 4. Camera & Lighting Checks
    cameras = [obj for obj in scene.objects if obj.type == "CAMERA"]
    lights = [obj for obj in scene.objects if obj.type == "LIGHT"]

    if not cameras:
        failures.append("Scene contains no camera objects.")
    else:
        print(f"[PASS] Cameras detected: {len(cameras)} ({', '.join(c.name for c in cameras[:3])})")

    if not lights:
        warnings.append(
            "Scene contains no dedicated light objects (environment lighting may be active)."
        )
    else:
        print(f"[PASS] Light sources detected: {len(lights)}")

    # 5. Missing Data / Broken Links Check
    missing_files = [
        lib.filepath for lib in bpy.data.libraries if getattr(lib, "is_missing", False)
    ]
    if missing_files:
        failures.append(f"External library data missing from .blend file: {missing_files}")

    broken_images = []
    for img in bpy.data.images:
        if img.source == "FILE" and img.filepath:
            abs_path = bpy.path.abspath(img.filepath)
            if not os.path.exists(abs_path) and not img.packed_file:
                broken_images.append(img.name)

    if broken_images:
        failures.append(f"Missing external image files: {broken_images}")
    else:
        print("[PASS] All texture and datablock references are intact.")

    print("-" * 60)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        print("VERIFICATION RESULT: FAILED")
        sys.exit(1)

    print("VERIFICATION RESULT: PASSED")
    sys.exit(0)


if __name__ == "__main__":
    run_headless_tests()
