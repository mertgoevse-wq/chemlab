"""
ChemLab Automated Asset Exporter (Blender 5.2 to Godot 4).
Exports laboratory apparatus and cleanroom geometry from chemlab.blend
to game/assets/ using glTF 2.0 (.glb) with Draco compression.

Run via Blender headless mode:
    blender -b chemlab.blend --python tools/export_assets_to_godot.py
"""

import sys
from pathlib import Path

try:
    import bpy
except ImportError:
    print("Error: This script must be executed inside Blender's Python runtime.")
    sys.exit(1)

REPO_ROOT = Path(r"C:\Users\Win11 Pro\Desktop\chemlab")
APPARATUS_OUT = REPO_ROOT / "game" / "assets" / "apparatus"
APPARATUS_OUT.mkdir(parents=True, exist_ok=True)

# Apparatus export group mapping (logical grouping of objects to export as individual .glb)
ASSET_GROUPS = {
    "SM_Beaker_150ml": ["Beaker_150ml_Blue_Glass", "Beaker_150ml_Blue_Liquid"],
    "SM_Beaker_400ml": ["Beaker_400ml_Green_Glass", "Beaker_400ml_Green_Liquid"],
    "SM_Beaker_Heated": ["Beaker_Heated_Glass", "Beaker_Heated_Liquid"],
    "SM_Beaker_Stirring": ["Beaker_Stirring_Glass", "Beaker_Stirring_Liquid"],
    "SM_Bottle_Amber_HCl": [
        "Bottle_Amber_HCl_Body",
        "Bottle_Amber_HCl_Cap",
        "Bottle_Amber_HCl_Label",
        "Bottle_Amber_HCl_Neck",
    ],
    "SM_Bottle_Amber_H2SO4": [
        "Bottle_Amber_H2SO4_Body",
        "Bottle_Amber_H2SO4_Cap",
        "Bottle_Amber_H2SO4_Label",
        "Bottle_Amber_H2SO4_Neck",
    ],
}


def export_asset_group(asset_name: str, object_names: list[str]) -> bool:
    """Selects target objects, centers origin if needed, and exports to .glb."""
    # Deselect all
    bpy.ops.object.select_all(action="DESELECT")

    found_objects = []
    for name in object_names:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.select_set(True)
            found_objects.append(obj)

    if not found_objects:
        print(f"[SKIP] No objects found for {asset_name}")
        return False

    bpy.context.view_layer.objects.active = found_objects[0]
    output_path = APPARATUS_OUT / f"{asset_name}.glb"

    print(
        f"[EXPORT] Exporting {asset_name} ({len(found_objects)} objects) -> {output_path.name}..."
    )

    try:
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_materials="EXPORT",
            export_vertex_color="NONE",
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10,
            export_draco_texcoord_quantization=12,
            export_lights=False,
            export_cameras=False,
        )
        print(f"[SUCCESS] Exported {output_path.name} ({output_path.stat().st_size} bytes)")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed exporting {asset_name}: {exc}")
        return False


def main() -> None:
    print("=== ChemLab Asset Pipeline Exporter (Blender 5.2 -> Godot 4) ===")
    total = len(ASSET_GROUPS)
    success_count = 0

    for asset_name, obj_names in ASSET_GROUPS.items():
        if export_asset_group(asset_name, obj_names):
            success_count += 1

    print(f"=== Export Complete: {success_count}/{total} asset packages generated ===")


if __name__ == "__main__":
    main()
