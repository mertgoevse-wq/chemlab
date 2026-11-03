"""
Blender 3D Bridge for Chemical Safety & Hazard Simulation
Connects physics simulation state to Blender 3D scene objects (from module_fume_safety.py
and module_apparatus.py), generating animations, LED state updates, airflow draft curves,
stopper projectile trajectories, and spill/effervescence visual effects.
"""


try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False



class BlenderSafetyVisualizer:
    """
    Translates chemical safety simulation events into Blender 3D keyframe animations,
    curve geometry, material shaders, and particle dynamics.
    """

    BENCH_H: float = 0.90
    HOOD_X: float = -2.2
    HOOD_Y: float = 3.35

    @classmethod
    def apply_sash_animation(cls, start_frame: int, end_frame: int, target_height_m: float) -> str:
        """
        Generates Python script for Blender to animate sash movement and update LED alarm status.
        """
        code = f"""
import bpy

sash_glass = bpy.data.objects.get("FumeHood_SashGlass")
sash_handle = bpy.data.objects.get("FumeHood_SashHandle")
led_obj = bpy.data.objects.get("FumeHood_Status_LED")

target_h = {target_height_m}
glass_z = 0.90 + target_h + 0.85 / 2.0
handle_z = 0.90 + target_h

if sash_glass and sash_handle:
    # Keyframe initial
    sash_glass.keyframe_insert(data_path="location", frame={start_frame})
    sash_handle.keyframe_insert(data_path="location", frame={start_frame})

    # Animate to target
    sash_glass.location.z = glass_z
    sash_handle.location.z = handle_z
    sash_glass.keyframe_insert(data_path="location", frame={end_frame})
    sash_handle.keyframe_insert(data_path="location", frame={end_frame})

# Update Status LED color based on safety line (0.45m)
mat_led = bpy.data.materials.get("Mat_LED_Green")
if mat_led and mat_led.use_nodes:
    bsdf = mat_led.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if target_h > 0.45:
            # Alarm Red
            bsdf.inputs['Base Color'].default_value = (0.95, 0.05, 0.05, 1.0)
            bsdf.inputs['Emission Color'].default_value = (1.0, 0.05, 0.05, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 12.0
        else:
            # Safe Green
            bsdf.inputs['Base Color'].default_value = (0.05, 0.95, 0.2, 1.0)
            bsdf.inputs['Emission Color'].default_value = (0.1, 1.0, 0.2, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 6.0
"""
        return code

    @classmethod
    def generate_draft_airflow_curves_code(cls, streamlines: list[list[tuple[float, float, float]]]) -> str:
        """
        Generates Blender Python code to render 3D aerodynamic airflow streamlines as beveled curves
        with glowing blue-white cyan emission shaders.
        """
        lines_data = repr(streamlines)
        code = f"""
import bpy

streamlines = {lines_data}

col_name = "03_Safety_Equipment"
col = bpy.data.collections.get(col_name) or bpy.context.scene.collection

# Remove previous draft curves if any
for obj in list(bpy.data.objects):
    if obj.name.startswith("Airflow_Streamline_"):
        bpy.data.objects.remove(obj, do_unlink=True)

mat_flow = bpy.data.materials.get("Mat_Airflow_Streamline")
if not mat_flow:
    mat_flow = bpy.data.materials.new(name="Mat_Airflow_Streamline")
    mat_flow.use_nodes = True
    bsdf = mat_flow.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.2, 0.8, 1.0, 0.5)
        bsdf.inputs['Emission Color'].default_value = (0.3, 0.85, 1.0, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 3.5

for idx, pts in enumerate(streamlines):
    curve_data = bpy.data.curves.new(name=f"Airflow_Curve_{{idx}}", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.005  # 5mm smooth tube
    curve_data.bevel_resolution = 4

    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(pts) - 1)
    for p_idx, (x, y, z) in enumerate(pts):
        polyline.points[p_idx].co = (x, y, z, 1.0)

    c_obj = bpy.data.objects.new(f"Airflow_Streamline_{{idx}}", curve_data)
    c_obj.data.materials.append(mat_flow)
    col.objects.link(c_obj)
"""
        return code

    @classmethod
    def animate_stopper_pop_code(cls, vessel_name: str, trajectory: list[tuple[float, float, float]], start_frame: int = 1) -> str:
        """
        Generates Blender Python code to keyframe a stopper popping out and arcing across the lab.
        """
        traj_data = repr(trajectory)
        code = f"""
import bpy

stopper = bpy.data.objects.get("{vessel_name}_Stopper") or bpy.data.objects.get("Stopper")
traj = {traj_data}

if stopper and traj:
    base_loc = list(stopper.location)
    for frame_idx, (dx, dy, dz) in enumerate(traj):
        f = {start_frame} + frame_idx * 2
        stopper.location = (base_loc[0] + dx, base_loc[1] + dy, base_loc[2] + dz)
        stopper.keyframe_insert(data_path="location", frame=f)
"""
        return code

    @classmethod
    def render_spill_puddle_code(cls, spill_id: str, x: float, y: float, z: float, radius: float, ph: float) -> str:
        """
        Generates Blender code to render chemical spill puddle on bench/floor,
        colored according to universal pH indicator:
        pH 0-2: Intense Red
        pH 3-5: Orange/Yellow
        pH 6-8: Neutral Green
        pH 9-11: Deep Blue/Violet
        """
        # Universal indicator RGB color mapping
        if ph < 3.0:
            color = (0.9, 0.05, 0.05, 0.85)  # Acid Red
        elif ph < 6.0:
            color = (0.95, 0.7, 0.05, 0.85)  # Orange/Yellow
        elif ph <= 8.5:
            color = (0.1, 0.85, 0.2, 0.85)   # Safe Neutral Green
        else:
            color = (0.1, 0.2, 0.95, 0.85)   # Basic Blue

        code = f"""
import bpy

puddle_name = "Spill_Puddle_{spill_id}"
old_puddle = bpy.data.objects.get(puddle_name)
if old_puddle:
    bpy.data.objects.remove(old_puddle, do_unlink=True)

# Cylinder disc puddle
bpy.ops.mesh.primitive_cylinder_add(radius={radius}, depth=0.005, location=({x}, {y}, {z} + 0.0025))
puddle = bpy.context.active_object
puddle.name = puddle_name

mat_puddle = bpy.data.materials.new(name=f"Mat_Spill_{ph}")
mat_puddle.use_nodes = True
bsdf = mat_puddle.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = {color}
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.33
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.90

puddle.data.materials.append(mat_puddle)
"""
        return code
