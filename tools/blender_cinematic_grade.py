"""ChemLab cinematic night grade — headless Blender authoring pass.

Usage:
    blender -b chemlab.blend --python tools/blender_cinematic_grade.py

Produces:
    chemlab_cinematic.blend                (authoring copy; chemlab.blend stays authoritative)
    docs/screenshots/cine_establish.png    (wide)
    docs/screenshots/cine_bench.png        (working bench, shallow DOF)
    docs/screenshots/cine_hood.png         (fume hood task light)

Why materials first: the source scene is authored in near-white values (walls
0.92, floor 0.75, ceiling 0.88). Under any bright rig that reads as a white
box. A night look needs albedo separation plus practicals that actually fall
off, so this pass regrades surfaces before it relights.
"""

import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "docs", "screenshots")
os.makedirs(SHOTS, exist_ok=True)

scene = bpy.context.scene


# ---------------------------------------------------------------- material kit
def principled(mat):
    return next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def set_surface(mat_name, base=None, roughness=None, metallic=None, emission=None):
    """Set the PBR surface of an existing material without rebuilding its graph."""
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        return False
    bsdf = principled(mat)
    if not bsdf:
        return False
    if base is not None:
        bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    if roughness is not None:
        bsdf.inputs["Roughness"].default_value = roughness
    if metallic is not None:
        bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        color, strength = emission
        if bsdf.inputs.get("Emission Color"):
            bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
            bsdf.inputs["Emission Strength"].default_value = strength
    return True


def add_grain(mat_name, scale=9.0, strength=0.18):
    """Break up flat albedo with low-frequency noise so surfaces are not plastic."""
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = principled(mat)
    if not bsdf or bsdf.inputs["Base Color"].is_linked:
        return
    base_color = bsdf.inputs["Base Color"].default_value[:]

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-900, 0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-700, 0)
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-480, 0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.72
    dark = tuple(max(0.0, c * (1.0 - strength)) for c in base_color[:3])
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color[:3], 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


# Night palette: separate surfaces in value and temperature or the camera reads
# one continuous white mass. Values are linear (not sRGB), so these are dark.
GRADES = [
    # name, base color, roughness, metallic, grain tag
    ("Mat_Wall_Cleanroom", (0.30, 0.305, 0.315), 0.72, 0.0, None),
    ("Mat_Ceiling_Acoustic", (0.085, 0.09, 0.10), 0.92, 0.0, None),
    ("Mat_Floor_Epoxy", (0.038, 0.044, 0.052), 0.16, 0.05, "floor"),
    ("Mat_Baseboard", (0.045, 0.05, 0.058), 0.35, 0.0, None),
    ("Mat_Cabinet_Laminate", (0.115, 0.125, 0.145), 0.38, 0.0, "cabinet"),
    ("Mat_Countertop_Ceramic", (0.055, 0.062, 0.072), 0.20, 0.08, "counter"),
    ("Mat_Shelf_Resin", (0.11, 0.12, 0.135), 0.30, 0.0, None),
    ("Mat_FumeHood_Body", (0.30, 0.315, 0.335), 0.34, 0.0, None),
    ("Mat_FumeHood_Interior", (0.42, 0.44, 0.46), 0.18, 0.0, None),
    # metals keep their metalness; only the albedo gets out of chalk-white
    ("Mat_Steel_Brushed", (0.62, 0.645, 0.67), 0.28, 0.92, None),
    ("Mat_Steel_Frame", (0.55, 0.575, 0.60), 0.33, 0.55, None),
    ("Mat_Chrome_Polished", (0.80, 0.815, 0.83), 0.10, 1.0, None),
    ("Mat_Stainless_Sink", (0.55, 0.575, 0.60), 0.20, 0.95, None),
]

# Walls and ceiling stay clean: any visible albedo noise at this scale reads
# as damp concrete, not as a cleanroom. Only the floor and casework get grain.
GRAIN = {
    "floor": (6.0, 0.08),
    "cabinet": (18.0, 0.04),
    "counter": (12.0, 0.04),
}

for name, base, rough, metal, tag in GRADES:
    if set_surface(name, base=base, roughness=rough, metallic=metal) and tag:
        add_grain(name, *GRAIN.get(tag, (12.0, 0.04)))


def set_transmission(mat_name, amount=0.95, ior=1.45):
    mat = bpy.data.materials.get(mat_name)
    bsdf = principled(mat) if mat else None
    if not bsdf:
        return
    for key in ("Transmission Weight", "Transmission"):
        if bsdf.inputs.get(key):
            bsdf.inputs[key].default_value = amount
            break
    if bsdf.inputs.get("IOR"):
        bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Roughness"].default_value = 0.04


# Safety glass has to transmit, or the sash reads as a black panel.
set_transmission("Mat_Safety_Glass", 0.96, 1.47)
set_transmission("Mat_Borosilicate_Glass", 0.94, 1.47)

# Practical emitters: ceiling panels drop to standby so the rig reads as night,
# while the hood keeps a real task light (the fume hood is the hero prop).
set_surface("Mat_LED_Panel", emission=((0.60, 0.68, 0.82), 0.35))
set_surface("Mat_Hood_Light", emission=((1.0, 0.90, 0.74), 5.0))
set_surface("Mat_Borosilicate_Glass", base=(0.72, 0.78, 0.82), roughness=0.03, metallic=0.0)

# --------------------------------------------------------------- render setup
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"

eevee = scene.eevee
for attr, value in (
    ("taa_render_samples", 64),
    ("use_raytracing", True),
    ("use_shadows", True),
    ("shadow_ray_count", 2),
    ("shadow_step_count", 8),
    ("use_volumetric_lights", True),
    ("volumetric_samples", 48),
):
    if hasattr(eevee, attr):
        try:
            setattr(eevee, attr, value)
        except (TypeError, ValueError):
            pass

# Film grade: AgX preserves highlight roll-off on glass and stainless.
scene.view_settings.view_transform = "AgX"
for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
    try:
        scene.view_settings.look = look
        break
    except (TypeError, ValueError):
        continue
scene.view_settings.exposure = 0.55
scene.view_settings.gamma = 1.0

world = scene.world
if world and world.use_nodes:
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.015, 0.022, 0.038, 1.0)
        bg.inputs[1].default_value = 0.30

    # Volumetric haze belongs on the world: a volume cube also renders its
    # opaque surface and swallows the whole shot.
    out = next((n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD"), None)
    if out and not out.inputs["Volume"].is_linked:
        wvol = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        wvol.inputs["Density"].default_value = 0.006
        wvol.inputs["Anisotropy"].default_value = 0.4
        wvol.inputs["Color"].default_value = (0.70, 0.78, 1.0, 1.0)
        world.node_tree.links.new(wvol.outputs["Volume"], out.inputs["Volume"])

# Existing fixtures: night shift.
for ob in bpy.data.objects:
    if ob.type != "LIGHT":
        continue
    key = ob.name.lower()
    if key.startswith("lamp_area"):
        ob.data.energy = 3.0
        ob.data.color = (0.72, 0.80, 1.0)
    elif key.startswith("bunsen"):
        ob.data.energy = 0.0
    elif key.startswith("fumehood"):
        ob.data.energy = 22.0

# Idempotent rig: drop any previous pass before rebuilding.
old = bpy.data.collections.get("07_Cinematic_Night")
if old:
    for ob in list(old.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(old)
cine = bpy.data.collections.new("07_Cinematic_Night")
scene.collection.children.link(cine)


def aim(ob, target):
    direction = Vector(target) - ob.location
    ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, energy, size, color, target, spread=math.radians(120)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.color = color
    data.spread = spread
    ob = bpy.data.objects.new(name, data)
    cine.objects.link(ob)
    ob.location = loc
    aim(ob, target)
    return ob


# Overhead softbox: the only broad source, low enough to sculpt the bench top.
area("Cine_Overhead", (0.0, 0.3, 3.15), 190.0, (2.6, 1.4), (0.95, 0.96, 1.0),
     (0.0, 0.3, 0.9), math.radians(150))
# Warm task light raking across the island from camera-left.
area("Cine_Task_Warm", (-2.9, -1.6, 2.35), 150.0, (1.1, 0.5), (1.0, 0.74, 0.45),
     (-0.2, 0.6, 0.95))
# Cold separation from the far wall; rims the glassware.
area("Cine_Rim_Cool", (2.6, 3.1, 2.5), 180.0, (1.8, 0.6), (0.45, 0.68, 1.0),
     (0.2, 0.4, 1.05))
# Thin strip above the bench to catch beaker rims and the meniscus.
area("Cine_Rim_Strip", (0.4, 1.5, 2.05), 55.0, (2.0, 0.10), (0.80, 0.90, 1.0),
     (0.3, 0.2, 1.0))
# Practical inside the hood, so the sash window shows a lit working volume.
area("Cine_Hood_Inner", (-2.2, 3.30, 2.26), 26.0, (1.3, 0.22), (1.0, 0.86, 0.66),
     (-2.2, 3.30, 0.95), math.radians(140))

def bar(name, center, dims, mat_name="Mat_Steel_Brushed"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = dims
    for col in list(ob.users_collection):
        col.objects.unlink(ob)
    cine.objects.link(ob)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(bpy.data.materials[mat_name])
    return ob


def retrofit_fume_hood():
    """Give the fume hood a real sash window.

    The body is a closed box whose front face hides the interior, so every
    frontal shot could only ever show a blank panel. Turn that face into
    glass and add the steel frame and sash rail a hood actually has.
    """
    body = bpy.data.objects.get("FumeHood_Upper_Body")
    glass = bpy.data.materials.get("Mat_Safety_Glass")
    if not body or not glass:
        return
    me = body.data
    if glass.name not in [m.name for m in me.materials if m]:
        me.materials.append(glass)
    glass_index = [m.name for m in me.materials if m].index(glass.name)

    corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
    x0, y0, z0 = (min(c[i] for c in corners) for i in range(3))
    x1, y1, z1 = (max(c[i] for c in corners) for i in range(3))

    bm = bmesh.new()
    bm.from_mesh(me)
    front_y = min(v.co.y for v in bm.verts)
    cut = [f for f in bm.faces
           if f.normal.y < -0.9 and abs(f.calc_center_median().y - front_y) < 0.01]
    for f in cut:
        f.material_index = glass_index
    bm.to_mesh(me)
    bm.free()
    me.update()

    cx = (x0 + x1) * 0.5
    t = 0.045
    y = y0 - 0.012
    bar("FumeHood_SashFrame_L", (x0 + t, y, (z0 + z1) * 0.5), (t, 0.05, z1 - z0))
    bar("FumeHood_SashFrame_R", (x1 - t, y, (z0 + z1) * 0.5), (t, 0.05, z1 - z0))
    bar("FumeHood_SashFrame_B", (cx, y, z0 + t), (x1 - x0, 0.05, t))
    bar("FumeHood_SashFrame_T", (cx, y, z1 - t), (x1 - x0, 0.05, t))
    bar("FumeHood_SashRail", (cx, y - 0.03, z0 + (z1 - z0) * 0.42), (x1 - x0, 0.06, 0.035))


retrofit_fume_hood()

# Hide interactive dev overlays so beauty frames show the room, not debug aids.
for ob in bpy.data.objects:
    key = ob.name.lower()
    if any(tag in key for tag in ("holo_hand", "hud_", "_dot_", "landmark")):
        ob.hide_render = True


def clearance_warning(loc):
    p = Vector(loc)
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render or ob.name.startswith("Cine_"):
            continue
        if any(abs(v) < 1e-6 for v in ob.dimensions):
            continue
        local = ob.matrix_world.inverted() @ p
        if all(abs(local[i]) <= ob.dimensions[i] * 0.5 for i in range(3)):
            print(f"CINE_WARN camera inside {ob.name} at {tuple(round(v, 2) for v in loc)}")


def shot(name, loc, target, lens, fstop, focus):
    clearance_warning(loc)
    data = bpy.data.cameras.new(f"Cam_{name}")
    cam = bpy.data.objects.new(f"Cam_{name}", data)
    cine.objects.link(cam)
    cam.location = loc
    aim(cam, target)
    data.lens = lens
    data.dof.use_dof = True
    data.dof.focus_distance = focus
    data.dof.aperture_fstop = fstop
    scene.camera = cam
    scene.render.filepath = os.path.join(SHOTS, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"CINE_SHOT {name} -> {scene.render.filepath}")


shot("cine_establish", (4.35, -4.55, 2.30), (-0.35, 0.35, 1.02), 30.0, 5.6, 5.2)
# Bench detail: stand on free floor south of the islands, not inside them.
shot("cine_bench", (2.55, -2.75, 1.48), (-0.15, 0.35, 1.02), 46.0, 2.8, 3.6)
# Hood: centred on the open face, far enough back that the side panel is not
# grazing the lens (a previous pass framed nothing but that panel).
shot("cine_hood", (-3.75, 0.70, 1.72), (-2.15, 3.25, 1.48), 30.0, 4.0, 3.1)

scene.camera = bpy.data.objects["Cam_cine_establish"]
scene.render.filepath = os.path.join(SHOTS, "cine_establish.png")

out = os.path.join(ROOT, "chemlab_cinematic.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
print(f"CINE_SAVED {out}")
