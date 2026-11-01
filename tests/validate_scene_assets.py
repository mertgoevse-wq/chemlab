"""
ChemLab Scene Asset & Hardware Budget Validator
Runs inside Blender to validate mesh topology, transform hygiene,
material assignments, and hardware budget constraints for Intel Iris Xe.
"""

import os
import sys

try:
    import bpy
except ImportError:
    try:
        import pytest

        pytestmark = pytest.mark.skip(
            reason="validate_scene_assets.py must be executed within Blender (bpy)"
        )
    except ImportError:
        pass
    print("FATAL: validate_scene_assets.py must be executed within Blender (bpy).", file=sys.stderr)
    if "pytest" not in sys.modules:
        sys.exit(1)

# Iris Xe Budget Limits
MAX_TOTAL_TRIANGLES = 250000
MAX_OBJECT_TRIANGLES = 35000
MAX_MATERIALS_PER_OBJECT = 4


def validate_assets():
    print("=" * 60)
    print("ChemLab Scene Asset & Hardware Budget Audit (Intel Iris Xe)")
    print("=" * 60)

    total_triangles = 0
    total_vertices = 0
    total_meshes = 0

    unapplied_scale_objs = []
    missing_material_objs = []
    over_budget_objs = []
    generic_named_objs = []

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    total_meshes = len(mesh_objects)

    print(f"[*] Scanning {total_meshes} mesh objects in scene...")

    for obj in mesh_objects:
        # 1. Transform Validation (Scale should be 1.0, 1.0, 1.0)
        s = obj.scale
        if abs(s.x - 1.0) > 0.01 or abs(s.y - 1.0) > 0.01 or abs(s.z - 1.0) > 0.01:
            unapplied_scale_objs.append(f"{obj.name} (Scale: {s.x:.2f}, {s.y:.2f}, {s.z:.2f})")

        # 2. Geometry & Triangle Counting
        mesh = obj.data
        tri_count = 0
        vert_count = len(mesh.vertices)
        total_vertices += vert_count

        # Calculate polygon/triangle count
        for poly in mesh.polygons:
            if len(poly.vertices) == 3:
                tri_count += 1
            elif len(poly.vertices) == 4:
                tri_count += 2
            else:
                tri_count += len(poly.vertices) - 2

        total_triangles += tri_count

        if tri_count > MAX_OBJECT_TRIANGLES:
            over_budget_objs.append(f"{obj.name}: {tri_count} tris (limit: {MAX_OBJECT_TRIANGLES})")

        # 3. Material Assignment Check
        if len(obj.material_slots) == 0:
            missing_material_objs.append(obj.name)
        else:
            has_assigned_material = any(slot.material is not None for slot in obj.material_slots)
            if not has_assigned_material:
                missing_material_objs.append(obj.name)

        # 4. Naming Hygiene (avoid generic Cube.001 etc in production)
        if obj.name.startswith(("Cube.", "Cylinder.", "Sphere.", "Plane.")):
            generic_named_objs.append(obj.name)

    print(f"[*] Total Scene Mesh Count: {total_meshes}")
    print(f"[*] Total Vertices: {total_vertices:,}")
    print(f"[*] Total Triangles: {total_triangles:,} / {MAX_TOTAL_TRIANGLES:,} limit")

    budget_passed = total_triangles <= MAX_TOTAL_TRIANGLES
    if budget_passed:
        print(
            f"[PASS] Triangle budget compliant ({total_triangles / MAX_TOTAL_TRIANGLES * 100:.1f}% used)."
        )
    else:
        print(
            f"[FAIL] Exceeded maximum triangle budget by {total_triangles - MAX_TOTAL_TRIANGLES:,} tris!"
        )

    # 5. Borosilicate Glass Material Audit
    glass_mats = [m for m in bpy.data.materials if "glass" in m.name.lower()]
    print(f"[*] Glass Materials Detected: {[m.name for m in glass_mats]}")
    for gm in glass_mats:
        if gm.use_nodes and gm.node_tree:
            bsdf = gm.node_tree.nodes.get("Principled BSDF")
            if bsdf and "IOR" in bsdf.inputs:
                ior = bsdf.inputs["IOR"].default_value
                if abs(ior - 1.474) < 0.05:
                    print(f"[PASS] {gm.name} conforms to Borosilicate IOR ({ior:.3f})")
                else:
                    print(f"[WARN] {gm.name} IOR is {ior:.3f} (Standard Borosilicate is 1.474)")

    # Summary
    issues = 0
    if not budget_passed:
        issues += 1
    if unapplied_scale_objs:
        print(f"\n[WARN] Unapplied Object Scale ({len(unapplied_scale_objs)}):")
        for u in unapplied_scale_objs[:10]:
            print(f"  - {u}")
        if len(unapplied_scale_objs) > 10:
            print(f"  ... and {len(unapplied_scale_objs) - 10} more.")

    if missing_material_objs:
        print(f"\n[WARN] Objects Missing Materials ({len(missing_material_objs)}):")
        for m in missing_material_objs[:10]:
            print(f"  - {m}")

    if over_budget_objs:
        print("\n[FAIL] Individual Objects Exceeding Budget:")
        for o in over_budget_objs:
            print(f"  - {o}")
        issues += 1

    print("\n" + "=" * 60)
    if issues > 0:
        print(f"ASSET VALIDATION AUDIT: FAILED ({issues} critical issues)")
        sys.exit(1)
    else:
        print("ASSET VALIDATION AUDIT: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    validate_assets()
