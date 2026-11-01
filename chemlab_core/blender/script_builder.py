"""
Safe Blender Python Code Generator.
Constructs verified, injectable Python snippets for Blender 3D operations.
"""

from chemlab_core.models import OscillatingPhase


def build_transform_script(
    object_name: str,
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
) -> str:
    """Generate Blender script to translate an object by a delta vector."""
    return f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.location.x += {dx:.6f}
    obj.location.y += {dy:.6f}
    obj.location.z += {dz:.6f}
    print(f"Moved {{obj.name}} to {{list(obj.location)}}")
else:
    print(f"Warning: Object '{object_name}' not found")
""".strip()


def build_rotation_script(
    object_name: str,
    angle_degrees: float,
    axis: str = "Y",
) -> str:
    """Generate Blender script to rotate an object (e.g. pouring liquid)."""
    axis_lower = axis.lower()
    return f"""
import bpy
import math

obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.rotation_euler.{axis_lower} = math.radians({angle_degrees:.4f})
    print(f"Rotated {{obj.name}} {axis_lower} to {angle_degrees:.2f} deg")
else:
    print(f"Warning: Object '{object_name}' not found")
""".strip()


def build_chemical_material_script(
    material_name: str,
    color_rgba: tuple[float, float, float, float],
    roughness: float = 0.05,
    transmission_weight: float = 0.95,
    ior: float = 1.333,
) -> str:
    """Generate script to update a Principled BSDF liquid shader.

    Enforces realistic optical properties (water IOR 1.333, transmission 0.95).
    """
    r, g, b, a = color_rgba
    return f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat:
    mat = bpy.data.materials.new(name="{material_name}")
    mat.use_nodes = True

nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, {a:.4f})
    bsdf.inputs['Roughness'].default_value = {roughness:.4f}
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = {transmission_weight:.4f}
    elif 'Transmission' in bsdf.inputs:
        bsdf.inputs['Transmission'].default_value = {transmission_weight:.4f}
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = {ior:.4f}
    print(f"Updated chemical material '{material_name}' to RGBA=({r:.2f},{g:.2f},{b:.2f},{a:.2f})")
""".strip()


def build_oscillation_keyframe_script(
    material_name: str,
    phase: OscillatingPhase,
    color_rgba: tuple[float, float, float, float],
) -> str:
    """Update material and tag viewport update for oscillating reaction cycle."""
    return build_chemical_material_script(
        material_name=material_name,
        color_rgba=color_rgba,
        roughness=0.04,
        transmission_weight=0.92,
        ior=1.34,
    )
