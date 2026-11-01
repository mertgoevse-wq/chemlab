#!/usr/bin/env python3
"""
ChemLab HUD & UI Scene Builder
Complements the main laboratory with non-intrusive 3D spatial overlays:
- Floating Reagent Tags
- Temperature Readouts on heated flasks
- pH Color Bar
- Holographic Virtual Hands
- Top Bar (Quest, Safety, Game Mode)
- Level-Up & Quest Completion AV feedback hooks

Integrated into chemlab.blend via Blender 5.2 Python API.
Usage: run inside Blender text editor / scripting workspace with chemlab.blend open.
"""

import math

import bpy

HUD_COLLECTION = "00_HUD_UI"

PALETTE = {
    "reagent_tag_bg": (0.07, 0.09, 0.14, 1.0),
    "reagent_tag_border": (0.0, 0.82, 1.0, 1.0),
    "temp_bg": (0.10, 0.04, 0.02, 1.0),
    "temp_text": (1.0, 0.45, 0.10, 1.0),
    "ph_red": (0.90, 0.10, 0.10, 1.0),
    "ph_orange": (1.0, 0.55, 0.05, 1.0),
    "ph_yellow": (0.95, 0.90, 0.10, 1.0),
    "ph_green": (0.15, 0.90, 0.25, 1.0),
    "ph_cyan": (0.05, 0.65, 0.95, 1.0),
    "ph_blue": (0.15, 0.25, 0.95, 1.0),
    "ph_violet": (0.65, 0.05, 0.85, 1.0),
    "hand_ready": (0.15, 0.95, 0.20, 0.85),  # Green
    "hand_hover": (1.0, 0.78, 0.08, 0.85),  # Yellow
    "hand_hold": (0.08, 0.55, 1.0, 0.85),  # Blue
    "topbar_bg": (0.05, 0.07, 0.10, 0.92),
    "topbar_text": (0.98, 0.99, 1.0, 1.0),
    "topbar_alert": (0.95, 0.20, 0.20, 1.0),
    "topbar_story": (0.10, 0.60, 1.0, 1.0),
    "topbar_sandbox": (0.20, 0.85, 0.45, 1.0),
}

FONT_ID = None


def get_font():
    global FONT_ID
    if FONT_ID is None:
        try:
            FONT_ID = bpy.data.fonts[0]
        except Exception:
            FONT_ID = bpy.data.fonts.new("UI_Font")
    return FONT_ID


def ensure_collection():
    col = bpy.data.collections.get(HUD_COLLECTION)
    if not col:
        col = bpy.data.collections.new(HUD_COLLECTION)
        bpy.context.scene.collection.children.link(col)

    def link_obj(obj):
        if obj.name not in col.objects:
            col.objects.link(obj)
        for c in list(obj.users_collection):
            if c != col:
                c.objects.unlink(obj)

    return col, link_obj


def mat_emissive(name, color, strength=3.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    # Clear default BSDF if present
    for node in nodes:
        nodes.remove(node)
    bsdf = nodes.new("ShaderNodeBsdfDiffuse")  # fallback
    emit = nodes.new("ShaderNodeEmission")
    out = nodes.new("ShaderNodeOutputMaterial")
    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = strength
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def mat_plastic(name, color, roughness=0.35):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Transmission Weight"].default_value = 0.0
    return mat


def clear_hud(collection, link_obj):
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def create_text(
    name,
    text_str,
    location,
    rotation=(0, 0, 0),
    scale=0.02,
    color=(1, 1, 1, 1),
    strength=3.0,
    align="CENTER",
):
    bpy.ops.object.text_add(location=location)
    txt = bpy.context.active_object
    txt.name = name
    txt.data.body = text_str
    txt.data.size = scale
    txt.data.extrude = 0.001
    txt.data.align_x = align
    txt.data.align_y = "CENTER"
    txt.rotation_euler = rotation
    mat = mat_emissive(name + "_Mat", color, strength)
    if txt.data.materials:
        txt.data.materials[0] = mat
    else:
        txt.data.materials.append(mat)
    return txt


def create_cube(name, location, scale, rotation=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = rotation
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def create_cylinder(name, location, radius, depth, rotation=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def create_sphere(name, location, radius, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def build_reagent_tag(
    name, location, label_text, chemical_formula, tag_color=(0.0, 0.82, 1.0, 1.0)
):
    """Floating billboard-style reagent tag hovering above glassware."""
    mat_bg = mat_emissive(name + "_TagBG", PALETTE["reagent_tag_bg"], strength=1.8)
    mat_border = mat_emissive(name + "_TagBorder", tag_color, strength=2.5)

    # Base plane / sign backing
    create_cube(name + "_BG", location, scale=(0.08, 0.002, 0.04), mat=mat_bg)
    # Border glow rim
    create_cube(
        name + "_Border",
        location,
        scale=(0.085, 0.0025, 0.045),
        rotation=(0, 0, math.radians(2)),
        mat=mat_border,
    )

    # Label text
    y_off = 0.0
    create_text(
        name + "_Label",
        label_text,
        location=(location[0], location[1] + 0.003, location[2] + y_off),
        rotation=(math.radians(90), 0, 0),
        scale=0.018,
        color=(1, 1, 1, 1),
        strength=4.0,
        align="CENTER",
    )
    create_text(
        name + "_Formula",
        chemical_formula,
        location=(location[0], location[1] + 0.003, location[2] + y_off - 0.025),
        rotation=(math.radians(90), 0, 0),
        scale=0.014,
        color=(tag_color[0], tag_color[1], tag_color[2], 1.0),
        strength=2.0,
        align="CENTER",
    )
    print(f"[HUD] Reagent tag built: {name}")


def build_temperature_readout(name, location, temp_value, unit="°C"):
    """Digital red LED temperature overlay sitting atop heated flasks / hotplates."""
    mat_bg = mat_emissive(name + "_TempBG", PALETTE["temp_bg"], strength=2.0)
    create_cube(name + "_BG", location, scale=(0.07, 0.002, 0.03), mat=mat_bg)

    reading = f"{temp_value:.0f} {unit}"
    create_text(
        name + "_Readout",
        reading,
        location=(location[0], location[1] + 0.003, location[2] + 0.01),
        rotation=(math.radians(90), 0, 0),
        scale=0.020,
        color=PALETTE["temp_text"],
        strength=5.0,
        align="CENTER",
    )
    print(f"[HUD] Temperature readout built: {name} ({reading})")


def build_ph_color_bar(name, location, scale=(0.45, 0.05, 0.02)):
    """pH color spectrum bar anchored near reagent shelf, labelled 1–14."""
    colors = [
        PALETTE["ph_red"],
        PALETTE["ph_orange"],
        PALETTE["ph_yellow"],
        PALETTE["ph_green"],
        PALETTE["ph_cyan"],
        PALETTE["ph_blue"],
        PALETTE["ph_violet"],
    ]

    mat_bg = mat_emissive(name + "_BarBG", (0.04, 0.06, 0.10, 1.0), strength=1.5)
    bar = create_cube(name + "_BG", location, scale=scale, mat=mat_bg)

    n_seg = len(colors)
    seg_w = scale[0] / n_seg
    for i, c in enumerate(colors):
        sx = location[0] - scale[0] / 2 + seg_w * i + seg_w / 2
        sy = location[1] + 0.002
        sz = location[2] + scale[2] / 2
        mat_seg = mat_emissive(name + f"_Seg{i}", c, strength=2.2)
        create_cube(
            name + f"_Seg{i}",
            (sx, sy, sz),
            scale=(seg_w * 0.98, scale[1] * 0.6, scale[2] * 0.9),
            mat=mat_seg,
        )

    # Endpoint labels: 1 (red) left, 7 green center, 14 violet right
    create_text(
        name + "_Lbl_1",
        "1",
        location=(location[0] - scale[0] / 2 - 0.02, location[1] + 0.003, location[2]),
        rotation=(math.radians(90), 0, 0),
        scale=0.016,
        color=(1, 0.2, 0.2, 1),
        strength=3.0,
    )
    create_text(
        name + "_Lbl_7",
        "7",
        location=(location[0], location[1] + 0.003, location[2]),
        rotation=(math.radians(90), 0, 0),
        scale=0.016,
        color=(0.15, 0.9, 0.25, 1),
        strength=3.0,
    )
    create_text(
        name + "_Lbl_14",
        "14",
        location=(location[0] + scale[0] / 2 + 0.02, location[1] + 0.003, location[2]),
        rotation=(math.radians(90), 0, 0),
        scale=0.016,
        color=(0.65, 0.05, 0.85, 1),
        strength=3.0,
    )
    print(f"[HUD] pH color bar built: {name}")


def build_holographic_hand(name, location, state="ready"):
    """
    Transparent holographic virtual hand with color-coded fingertip interaction dots.
    states: 'ready' = green, 'hover' = yellow, 'hold' = blue
    """
    hand_color = {
        "ready": PALETTE["hand_ready"],
        "hover": PALETTE["hand_hover"],
        "hold": PALETTE["hand_hold"],
    }.get(state, PALETTE["hand_ready"])

    mat_hand = mat_emissive(name + "_HandMat", (0.12, 0.16, 0.24, 0.35), strength=1.2)
    mat_dot = mat_emissive(name + "_DotMat", hand_color, strength=4.0)

    # Palm base - transparent rounded block
    create_cube(name + "_Palm", location, scale=(0.08, 0.01, 0.12), mat=mat_hand)

    # Five fingertips extending from palm
    finger_offsets = [
        (-0.03, 0.02, 0.065),  # thumb
        (-0.015, 0.02, 0.085),  # index
        (0.0, 0.02, 0.085),  # middle
        (0.015, 0.02, 0.085),  # ring
        (0.03, 0.02, 0.065),  # pinky
    ]
    for i, off in enumerate(finger_offsets):
        fin_loc = (location[0] + off[0], location[1] + off[1], location[2] + off[2])
        create_sphere(name + f"_Finger{i}", fin_loc, radius=0.008, mat=mat_dot)

    print(f"[HUD] Holographic hand built: {name} (state={state})")


def build_top_bar(
    name, location, quest_text="Ziel: Salzsäure & Natron mischen", safety_state="safe", mode="story"
):
    """
    Top HUD bar: Quest objective, Safety alert status, Game mode toggle.
    Anchored as a horizontal slab at the top of the view frame.
    """
    mat_bg = mat_emissive(name + "_BG", PALETTE["topbar_bg"], strength=2.0)
    create_cube(name + "_BG", location, scale=(1.35, 0.002, 0.12), mat=mat_bg)

    # Quest objective text (left)
    create_text(
        name + "_Quest",
        quest_text,
        location=(location[0] - 0.45, location[1] + 0.003, location[2] + 0.035),
        rotation=(math.radians(90), 0, 0),
        scale=0.018,
        color=PALETTE["topbar_text"],
        strength=4.0,
    )

    # Safety alert (center)
    if safety_state == "alert":
        alert_color = PALETTE["topbar_alert"]
        alert_text = "⚠ SICHERHEITS-WARNUNG"
    else:
        alert_color = PALETTE["ph_green"]
        alert_text = "SICHER"
    create_text(
        name + "_Safety",
        alert_text,
        location=(location[0], location[1] + 0.003, location[2] + 0.035),
        rotation=(math.radians(90), 0, 0),
        scale=0.018,
        color=alert_color,
        strength=4.0,
    )

    # Game mode toggle (right)
    mode_color = PALETTE["topbar_story"] if mode == "story" else PALETTE["topbar_sandbox"]
    mode_text = "MODUS: STORY" if mode == "story" else "MODUS: SANDBOX"
    create_text(
        name + "_Mode",
        mode_text,
        location=(location[0] + 0.45, location[1] + 0.003, location[2] + 0.035),
        rotation=(math.radians(90), 0, 0),
        scale=0.018,
        color=mode_color,
        strength=4.0,
    )

    print(f"[HUD] Top bar built: {name} (safety={safety_state}, mode={mode})")


def build_av_feedback_node(name, location, tag="complete"):
    """
    Light-based node placeholder for Audio-Visual feedback on level-up / quest completion.
    Acts as a visual trigger anchor (emissive pulse light) where gameplay code can hook
    particle/sound systems in Godot / game engine builds.
    """
    color = {
        "complete": (0.10, 0.85, 0.45, 1.0),
        "levelup": (0.10, 0.60, 1.0, 1.0),
    }.get(tag, (1.0, 1.0, 1.0, 1.0))
    mat = mat_emissive(name + "_Mat", color, strength=6.0)
    create_sphere(name + "_Trigger", location, radius=0.15, mat=mat)
    print(f"[HUD] AV feedback node built: {name} (tag={tag})")


def build_full_hud():
    col, link_obj = ensure_collection()
    clear_hud(col, link_obj)

    # 1. Floating reagent tags above key glassware
    build_reagent_tag(
        "Tag_CuSO4",
        (-1.3, 0.72, 1.35),
        "Kupfersulfatlösung",
        "CuSO₄ · 0.25 M",
        tag_color=(0.05, 0.65, 0.95, 1.0),
    )
    build_reagent_tag(
        "Tag_Green",
        (-1.15, 0.98, 1.10),
        "Nickelgrün-Lösung",
        "NiSO₄ · 0.12 M",
        tag_color=(0.15, 0.92, 0.25, 1.0),
    )
    build_reagent_tag(
        "Tag_Permanganate",
        (-1.45, 0.80, 1.15),
        "Kaliumpermanganat",
        "KMnO₄ · 0.05 M",
        tag_color=(0.55, 0.05, 0.65, 1.0),
    )
    build_reagent_tag(
        "Tag_HeatedBeaker",
        (1.3, 0.05, 1.30),
        "Erhitzte Lösung",
        "H₂O · 85 °C",
        tag_color=(0.95, 0.45, 0.10, 1.0),
    )

    # 2. Temperature readout on heated beaker / hotplate
    build_temperature_readout("Temp_Hotplate", (1.3, 0.35, 1.08), temp_value=85)
    build_temperature_readout(
        "Temp_Stirrer", (1.3, 0.78, 1.04), temp_value=340
    )  # RPM readout on stirrer

    # 3. pH color bar anchored near test tube rack / reagent shelf
    build_ph_color_bar("PH_Bar_Shelf", (-1.3, -1.45, 1.10), scale=(0.40, 0.05, 0.02))

    # 4. Holographic virtual hands (mirror states)
    build_holographic_hand("Hand_Left_Ready", (-0.55, 0.55, 1.10), state="ready")
    build_holographic_hand("Hand_Right_Hover", (0.55, 0.55, 1.10), state="hover")
    build_holographic_hand("Hand_Both_Hold", (0.0, 0.65, 1.05), state="hold")

    # 5. Top bar at top-center of scene
    build_top_bar(
        "TopBar_Main",
        (0.0, 1.35, 2.15),
        quest_text="Quest: Salzsäure + Natron → Reaktionsbeobachtung",
        safety_state="safe",
        mode="story",
    )

    # 6. AV feedback placeholders
    build_av_feedback_node("FX_QuestComplete", (0.0, 0.0, 2.4), tag="complete")
    build_av_feedback_node("FX_LevelUp", (0.0, 0.0, 2.6), tag="levelup")

    print("[HUD] Full HUD scene assembled in collection:", HUD_COLLECTION)


if __name__ == "__main__":
    build_full_hud()
