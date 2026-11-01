"""
Module 6: ChemLab Heads-Up Display (HUD) & 3D Spatial User Interface System
Constructs a comprehensive, non-intrusive 3D spatial user interface in Blender 5.2:
1. 3D Spatial Overlay:
   - Floating holographic reagent tags (CuSO4, NiCl2, KMnO4, Heated Reaction)
   - Temperature digital readouts on heated flasks & magnetic stirrer hotplate
   - 3D spatial pH color spectrum bar (pH 0-14) with dynamic indicator needle & molarity readout
2. Holographic Virtual Hands:
   - High-fidelity articulated hand geometry with semi-transparent Fresnel glow
   - Color-coded fingertip interaction dots (Green = ready to pinch, Yellow = hovering, Blue = firmly held)
3. Camera-Anchored Top Bar HUD:
   - Current Quest objective with progress bar & step tracker
   - Safety alert status module (PPE check, fume sash flow rate, hazard detector)
   - Active game mode toggle (Story Mode vs. Sandbox Mode)
4. Audio-Visual Feedback System:
   - Level-up & Quest completion celebratory holographic shockwave rings
   - 3D Level-Up trophy banner & golden/cyan orbital energy particles
   - Audio feedback cue mapping for synthesized stereo WAV sound assets
"""

import math

import bpy


def build_hud_ui():
    print(">>> Assembling ChemLab HUD & 3D Spatial UI System...")

    # Collection Setup
    col_name = "06_UI_HUD_Spatial"
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

    def apply_scale(obj):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)

    # =========================================================================
    # Materials & Shaders (Scientific High-Contrast Laboratory Tokens)
    # =========================================================================

    def create_emissive_mat(name, color, strength=5.0):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = strength
            bsdf.inputs["Roughness"].default_value = 0.1
        return mat

    def create_frosted_hud_glass(name, tint=(0.04, 0.08, 0.14, 1.0), alpha=0.35):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = tint
            bsdf.inputs["Roughness"].default_value = 0.12
            bsdf.inputs["IOR"].default_value = 1.45
            bsdf.inputs["Alpha"].default_value = alpha
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = 0.75
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = 0.75
        return mat

    # Palette Materials
    mat_hud_dark = create_frosted_hud_glass(
        "Mat_HUD_Backing_Dark", (0.02, 0.04, 0.07, 1.0), alpha=0.45
    )
    mat_hud_glass = create_frosted_hud_glass(
        "Mat_HUD_Glass_Panel", (0.05, 0.12, 0.20, 1.0), alpha=0.30
    )
    mat_glow_cyan = create_emissive_mat("Mat_HUD_Glow_Cyan", (0.0, 0.82, 1.0, 1.0), strength=8.0)
    mat_glow_emerald = create_emissive_mat(
        "Mat_HUD_Glow_Emerald", (0.10, 0.95, 0.35, 1.0), strength=8.0
    )
    mat_glow_purple = create_emissive_mat(
        "Mat_HUD_Glow_Purple", (0.68, 0.15, 0.95, 1.0), strength=8.0
    )
    mat_glow_amber = create_emissive_mat("Mat_HUD_Glow_Amber", (1.0, 0.65, 0.05, 1.0), strength=9.0)
    mat_glow_gold = create_emissive_mat("Mat_HUD_Glow_Gold", (1.0, 0.85, 0.15, 1.0), strength=12.0)
    mat_glow_red = create_emissive_mat("Mat_HUD_Glow_Red", (1.0, 0.15, 0.15, 1.0), strength=10.0)
    mat_text_white = create_emissive_mat("Mat_HUD_Text_White", (0.95, 0.98, 1.0, 1.0), strength=4.0)

    # Hand Hologram Material
    mat_holo_hand = bpy.data.materials.get("Mat_Holo_Hand") or bpy.data.materials.new(
        name="Mat_Holo_Hand"
    )
    mat_holo_hand.use_nodes = True
    bsdf_hand = mat_holo_hand.node_tree.nodes.get("Principled BSDF")
    if bsdf_hand:
        bsdf_hand.inputs["Base Color"].default_value = (0.05, 0.45, 0.85, 1.0)
        bsdf_hand.inputs["Emission Color"].default_value = (0.08, 0.75, 1.0, 1.0)
        bsdf_hand.inputs["Emission Strength"].default_value = 3.5
        bsdf_hand.inputs["Alpha"].default_value = 0.28
        bsdf_hand.inputs["Roughness"].default_value = 0.08
        if "Transmission Weight" in bsdf_hand.inputs:
            bsdf_hand.inputs["Transmission Weight"].default_value = 0.85
        elif "Transmission" in bsdf_hand.inputs:
            bsdf_hand.inputs["Transmission"].default_value = 0.85

    # Interaction Dot Materials
    mat_dot_green = create_emissive_mat("Mat_Dot_Green_Ready", (0.0, 1.0, 0.35, 1.0), strength=14.0)
    mat_dot_yellow = create_emissive_mat(
        "Mat_Dot_Yellow_Hover", (1.0, 0.85, 0.0, 1.0), strength=16.0
    )
    mat_dot_blue = create_emissive_mat("Mat_Dot_Blue_Held", (0.0, 0.55, 1.0, 1.0), strength=20.0)

    # =========================================================================
    # 1. Non-Intrusive 3D Spatial Overlay: Floating Reagent Tags
    # =========================================================================

    def create_floating_reagent_tag(
        name, x, y, z_anchor, title, formula, concentration, mol_wt, mat_accent
    ):
        """Creates a sleek floating spatial plaque connected via a micro-tether to glassware."""
        TAG_W = 0.14
        TAG_H = 0.065
        TAG_D = 0.003
        z_tag = z_anchor + 0.18

        # 1. Tether Pin Line (Vertical luminescent guide to flask mouth)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0008, depth=0.18, location=(x, y, z_anchor + 0.09)
        )
        tether = bpy.context.active_object
        tether.name = f"{name}_Tether"
        tether.data.materials.append(mat_accent)
        apply_scale(tether)
        link_obj(tether)

        # Anchor node dot at flask lip
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035, location=(x, y, z_anchor))
        dot_anchor = bpy.context.active_object
        dot_anchor.name = f"{name}_AnchorDot"
        dot_anchor.data.materials.append(mat_accent)
        apply_scale(dot_anchor)
        link_obj(dot_anchor)

        # 2. Frosted Glass Backing Plate
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z_tag))
        plate = bpy.context.active_object
        plate.name = f"{name}_Backing"
        plate.scale = (TAG_W, TAG_D, TAG_H)
        plate.data.materials.append(mat_hud_glass)
        apply_scale(plate)
        link_obj(plate)

        # 3. Glowing Border Bezel Frame
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z_tag))
        frame = bpy.context.active_object
        frame.name = f"{name}_Bezel"
        frame.scale = (TAG_W + 0.004, TAG_D * 0.7, TAG_H + 0.004)
        frame.data.materials.append(mat_accent)
        apply_scale(frame)
        link_obj(frame)

        # Accent Top Tab
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(x, y - 0.002, z_tag + TAG_H / 2 + 0.004)
        )
        tab = bpy.context.active_object
        tab.name = f"{name}_AccentTab"
        tab.scale = (TAG_W * 0.45, TAG_D * 1.2, 0.003)
        tab.data.materials.append(mat_accent)
        apply_scale(tab)
        link_obj(tab)

        # 4. Text - Title
        bpy.ops.object.text_add(location=(x - TAG_W / 2 + 0.012, y - TAG_D - 0.002, z_tag + 0.010))
        txt_title = bpy.context.active_object
        txt_title.name = f"{name}_Txt_Title"
        txt_title.data.body = title
        txt_title.data.size = 0.015
        txt_title.data.extrude = 0.0006
        txt_title.rotation_euler = (math.radians(90), 0, 0)
        txt_title.data.materials.append(mat_text_white)
        link_obj(txt_title)

        # Text - Subtitle / Formula & Details
        bpy.ops.object.text_add(location=(x - TAG_W / 2 + 0.012, y - TAG_D - 0.002, z_tag - 0.018))
        txt_sub = bpy.context.active_object
        txt_sub.name = f"{name}_Txt_Details"
        txt_sub.data.body = f"{formula} | {concentration}\n{mol_wt}"
        txt_sub.data.size = 0.009
        txt_sub.data.extrude = 0.0004
        txt_sub.rotation_euler = (math.radians(90), 0, 0)
        txt_sub.data.materials.append(mat_accent)
        link_obj(txt_sub)

    # Spawn Floating Reagent Tags on Island Bench A Glassware
    # 1. Copper Sulfate (CuSO4 500ml Flask at x=-1.3, y=-0.4, rim z=1.10)
    create_floating_reagent_tag(
        name="Tag_CuSO4_Blue",
        x=-1.30,
        y=-0.40,
        z_anchor=1.11,
        title="CuSO4 · 5H2O",
        formula="Copper(II) Sulfate",
        concentration="0.25 M (aq)",
        mol_wt="249.68 g/mol",
        mat_accent=mat_glow_cyan,
    )

    # 2. Nickel Chloride (NiCl2 250ml Flask at x=-1.15, y=-0.6, rim z=1.06)
    create_floating_reagent_tag(
        name="Tag_NiCl2_Green",
        x=-1.15,
        y=-0.60,
        z_anchor=1.07,
        title="NiCl2 (aq)",
        formula="Nickel(II) Chloride",
        concentration="0.10 M | pH 6.2",
        mol_wt="129.60 g/mol",
        mat_accent=mat_glow_emerald,
    )

    # 3. Potassium Permanganate (KMnO4 250ml Flask at x=-1.45, y=-0.65, rim z=1.05)
    create_floating_reagent_tag(
        name="Tag_KMnO4_Purple",
        x=-1.45,
        y=-0.65,
        z_anchor=1.06,
        title="KMnO4 (aq)",
        formula="Potassium Permanganate",
        concentration="0.05 M | Oxidizer",
        mol_wt="158.03 g/mol",
        mat_accent=mat_glow_purple,
    )

    # =========================================================================
    # 2. Temperature Digital Readouts on Heated Flasks
    # =========================================================================

    def create_temperature_readout_hud(name, x, y, z_flask, current_temp, target_temp, status_str):
        """Builds a floating digital HUD readout directly above a heated reaction vessel."""
        # Floating Bracket Frame
        z_hud = z_flask + 0.16
        BRK_W = 0.13
        BRK_H = 0.055

        # Backing Glass
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z_hud))
        bg = bpy.context.active_object
        bg.name = f"{name}_BG"
        bg.scale = (BRK_W, 0.003, BRK_H)
        bg.data.materials.append(mat_hud_dark)
        apply_scale(bg)
        link_obj(bg)

        # Thermal Warning Accent Border
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z_hud))
        border = bpy.context.active_object
        border.name = f"{name}_Border"
        border.scale = (BRK_W + 0.003, 0.0025, BRK_H + 0.003)
        border.data.materials.append(mat_glow_amber)
        apply_scale(border)
        link_obj(border)

        # Main Digital Temperature (Large high-contrast amber/red LED display)
        bpy.ops.object.text_add(location=(x - BRK_W / 2 + 0.010, y - 0.004, z_hud + 0.006))
        txt_temp = bpy.context.active_object
        txt_temp.name = f"{name}_Txt_Temp"
        txt_temp.data.body = f"{current_temp:.1f} °C"
        txt_temp.data.size = 0.018
        txt_temp.data.extrude = 0.0008
        txt_temp.rotation_euler = (math.radians(90), 0, 0)
        txt_temp.data.materials.append(mat_glow_amber)
        link_obj(txt_temp)

        # Sub-status text
        bpy.ops.object.text_add(location=(x - BRK_W / 2 + 0.010, y - 0.004, z_hud - 0.016))
        txt_stat = bpy.context.active_object
        txt_stat.name = f"{name}_Txt_Status"
        txt_stat.data.body = f"SET: {target_temp:.1f} °C | {status_str}"
        txt_stat.data.size = 0.0085
        txt_stat.data.extrude = 0.0004
        txt_stat.rotation_euler = (math.radians(90), 0, 0)
        txt_stat.data.materials.append(mat_text_white)
        link_obj(txt_stat)

        # Thermal Radiation Emission Ring (Glow halo around beaker base)
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.062, minor_radius=0.003, location=(x, y, z_flask - 0.06)
        )
        ring = bpy.context.active_object
        ring.name = f"{name}_ThermalRing"
        ring.data.materials.append(mat_glow_amber)
        apply_scale(ring)
        link_obj(ring)

    # 1. Bunsen Burner Heated Beaker (at x=1.3, y=-0.5, rim z=1.23)
    create_temperature_readout_hud(
        name="TempHUD_Bunsen_Beaker",
        x=1.30,
        y=-0.50,
        z_flask=1.24,
        current_temp=102.4,
        target_temp=100.0,
        status_str="▲ BOILING HAZARD",
    )

    # 2. Magnetic Stirrer Heated Flask (at x=1.3, y=0.5, rim z=1.12)
    create_temperature_readout_hud(
        name="TempHUD_MagStirrer",
        x=1.30,
        y=0.50,
        z_flask=1.12,
        current_temp=85.0,
        target_temp=85.0,
        status_str="STABLE | 450 RPM",
    )

    # =========================================================================
    # 3. 3D Spatial pH Color Bar (Universal Indicator Spectrum)
    # =========================================================================

    def create_spatial_ph_bar(name, x, y, z):
        """Constructs an analytical 3D spatial pH spectrum indicator with cursor needle."""
        BAR_LEN = 0.38
        BAR_H = 0.035
        BAR_D = 0.004

        # Backing Plate
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
        bg = bpy.context.active_object
        bg.name = f"{name}_Backing"
        bg.scale = (BAR_LEN + 0.03, BAR_D, BAR_H + 0.03)
        bg.data.materials.append(mat_hud_dark)
        apply_scale(bg)
        link_obj(bg)

        # Frame
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
        border = bpy.context.active_object
        border.name = f"{name}_Border"
        border.scale = (BAR_LEN + 0.034, BAR_D * 0.8, BAR_H + 0.034)
        border.data.materials.append(mat_glow_cyan)
        apply_scale(border)
        link_obj(border)

        # 14 Spectral Segments
        spectrum_rgbs = [
            (0.92, 0.12, 0.12),  # pH 1 Deep Red
            (0.95, 0.32, 0.10),  # pH 2 Red-Orange
            (0.96, 0.52, 0.08),  # pH 3 Orange
            (0.96, 0.72, 0.05),  # pH 4 Yellow-Orange
            (0.92, 0.88, 0.08),  # pH 5 Yellow
            (0.65, 0.88, 0.12),  # pH 6 Yellow-Green
            (0.12, 0.88, 0.25),  # pH 7 Neutral Green
            (0.08, 0.75, 0.65),  # pH 8 Cyan-Green
            (0.05, 0.65, 0.95),  # pH 9 Cyan
            (0.10, 0.42, 0.95),  # pH 10 Blue
            (0.20, 0.22, 0.95),  # pH 11 Indigo
            (0.52, 0.12, 0.92),  # pH 12 Violet
            (0.72, 0.08, 0.85),  # pH 13 Deep Purple
            (0.55, 0.02, 0.55),  # pH 14 Dark Magenta
        ]

        seg_w = BAR_LEN / 14.0
        for i, rgb in enumerate(spectrum_rgbs):
            seg_x = x - BAR_LEN / 2 + seg_w * i + seg_w / 2
            mat_seg = create_emissive_mat(f"Mat_pH_Seg_{i + 1}", (*rgb, 1.0), strength=3.5)

            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(seg_x, y - 0.002, z))
            seg = bpy.context.active_object
            seg.name = f"{name}_Seg_{i + 1}"
            seg.scale = (seg_w * 0.92, BAR_D * 0.9, BAR_H * 0.75)
            seg.data.materials.append(mat_seg)
            apply_scale(seg)
            link_obj(seg)

        # Title Tag
        bpy.ops.object.text_add(location=(x - BAR_LEN / 2, y - 0.005, z + BAR_H / 2 + 0.006))
        txt_title = bpy.context.active_object
        txt_title.name = f"{name}_Title"
        txt_title.data.body = "UNIVERSAL pH INDICATOR SPECTRUM"
        txt_title.data.size = 0.010
        txt_title.data.extrude = 0.0004
        txt_title.rotation_euler = (math.radians(90), 0, 0)
        txt_title.data.materials.append(mat_glow_cyan)
        link_obj(txt_title)

        # Numeric Scale Labels (pH 1, 7, 14)
        for val, seg_idx in [(1, 0), (7, 6), (14, 13)]:
            lbl_x = x - BAR_LEN / 2 + seg_w * seg_idx + seg_w / 2 - 0.005
            bpy.ops.object.text_add(location=(lbl_x, y - 0.005, z - BAR_H / 2 - 0.015))
            txt_lbl = bpy.context.active_object
            txt_lbl.name = f"{name}_Lbl_{val}"
            txt_lbl.data.body = str(val)
            txt_lbl.data.size = 0.008
            txt_lbl.data.extrude = 0.0003
            txt_lbl.rotation_euler = (math.radians(90), 0, 0)
            txt_lbl.data.materials.append(mat_text_white)
            link_obj(txt_lbl)

        # Dynamic Cursor Needle at pH 2.4 (Acidic Sample)
        cursor_x = x - BAR_LEN / 2 + seg_w * 1.4
        bpy.ops.mesh.primitive_cone_add(
            radius1=0.005,
            radius2=0.0005,
            depth=0.025,
            location=(cursor_x, y - 0.006, z + BAR_H / 2 + 0.012),
        )
        needle = bpy.context.active_object
        needle.name = f"{name}_Needle"
        needle.rotation_euler = (math.radians(180), 0, 0)
        needle.data.materials.append(mat_glow_gold)
        apply_scale(needle)
        link_obj(needle)

        # Readout badge
        bpy.ops.object.text_add(location=(cursor_x - 0.035, y - 0.006, z + BAR_H / 2 + 0.030))
        txt_val = bpy.context.active_object
        txt_val.name = f"{name}_Txt_Value"
        txt_val.data.body = "pH 2.40 [ACIDIC]\n[H+] = 3.98e-3 M"
        txt_val.data.size = 0.0085
        txt_val.data.extrude = 0.0004
        txt_val.rotation_euler = (math.radians(90), 0, 0)
        txt_val.data.materials.append(mat_glow_gold)
        link_obj(txt_val)

    # Spawn Spatial pH Bar above the test tube rack at x=-1.30, y=-1.10, z=1.28
    create_spatial_ph_bar("pH_Spectrum_HUD", x=-1.30, y=-1.10, z=1.28)

    # =========================================================================
    # 4. Transparent Holographic Virtual Hands with Color-Coded Interaction Dots
    # =========================================================================

    def create_holographic_hand(name, base_loc, base_rot, state="ready", is_right=False):
        """
        Constructs an anatomical holographic hand:
        - Articulated palm, metacarpals, and 5 articulated digits.
        - Translucent Fresnel cyan shader.
        - Color-coded interaction dots:
          * Green = ready to pinch
          * Yellow = hovering over interactive glassware
          * Blue = firmly held
        """
        bx, by, bz = base_loc
        rx, ry, rz = base_rot

        hand_empty = bpy.data.objects.new(name, None)
        hand_empty.location = (bx, by, bz)
        hand_empty.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        link_obj(hand_empty)

        # 1. Wrist Emitter Ring
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.028, minor_radius=0.004, location=(0, -0.07, 0)
        )
        wrist = bpy.context.active_object
        wrist.name = f"{name}_WristRing"
        wrist.data.materials.append(mat_glow_cyan)
        apply_scale(wrist)
        wrist.parent = hand_empty
        link_obj(wrist)

        # 2. Main Palm Mesh (Smooth beveled hexagon)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
        palm = bpy.context.active_object
        palm.name = f"{name}_Palm"
        palm.scale = (0.068, 0.075, 0.016)
        palm.data.materials.append(mat_holo_hand)
        apply_scale(palm)
        palm.parent = hand_empty
        link_obj(palm)

        # 3. Digits Setup (Thumb, Index, Middle, Ring, Pinky)
        finger_configs = [
            (
                "Thumb",
                -0.042 if not is_right else 0.042,
                -0.015,
                [0.026, 0.022],
                [25, 30] if not is_right else [-25, 30],
            ),
            ("Index", -0.024 if not is_right else 0.024, 0.040, [0.028, 0.024, 0.020], [8, 15, 20]),
            ("Middle", 0.000, 0.044, [0.032, 0.026, 0.022], [5, 12, 18]),
            ("Ring", 0.022 if not is_right else -0.022, 0.038, [0.028, 0.022, 0.018], [10, 18, 22]),
            (
                "Pinky",
                0.040 if not is_right else -0.040,
                0.028,
                [0.022, 0.018, 0.015],
                [15, 22, 25],
            ),
        ]

        fingertip_positions = []

        for f_name, f_x, f_y, seg_lengths, curl_angles in finger_configs:
            curr_x = f_x
            curr_y = f_y
            curr_z = 0.002
            cur_ang = 0.0

            for s_idx, length in enumerate(seg_lengths):
                cur_ang += math.radians(curl_angles[min(s_idx, len(curl_angles) - 1)])
                seg_r = 0.0055 - s_idx * 0.0008

                # Segment cylinder
                mid_x = curr_x
                mid_y = curr_y + (length / 2.0) * math.cos(cur_ang)
                mid_z = curr_z - (length / 2.0) * math.sin(cur_ang)

                bpy.ops.mesh.primitive_cylinder_add(
                    radius=seg_r, depth=length, location=(mid_x, mid_y, mid_z)
                )
                seg = bpy.context.active_object
                seg.name = f"{name}_{f_name}_Seg_{s_idx}"
                seg.rotation_euler = (cur_ang, 0, 0)
                seg.data.materials.append(mat_holo_hand)
                apply_scale(seg)
                seg.parent = hand_empty
                link_obj(seg)

                # Advance joint
                curr_y += length * math.cos(cur_ang)
                curr_z -= length * math.sin(cur_ang)

            fingertip_positions.append((f_name, (curr_x, curr_y, curr_z)))

        # 4. Color-Coded Interaction Dots on Fingertips
        # States:
        # Green = ready to pinch (#00FF66)
        # Yellow = hovering over interactive glassware (#FFD200)
        # Blue = firmly held (#0088FF)
        dot_mat_map = {"ready": mat_dot_green, "hover": mat_dot_yellow, "hold": mat_dot_blue}
        active_dot_mat = dot_mat_map.get(state, mat_dot_green)

        for tip_name, tip_loc in fingertip_positions:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=tip_loc)
            dot = bpy.context.active_object
            dot.name = f"{name}_{tip_name}_Dot_{state.upper()}"
            dot.data.materials.append(active_dot_mat)
            apply_scale(dot)
            dot.parent = hand_empty
            link_obj(dot)

        # If holding or hovering, add tactile force/halo rings around thumb and index tips
        if state in ("hover", "hold"):
            for ring_tip in ["Thumb", "Index"]:
                t_loc = dict(fingertip_positions)[ring_tip]
                bpy.ops.mesh.primitive_torus_add(
                    major_radius=0.012, minor_radius=0.0015, location=t_loc
                )
                halo = bpy.context.active_object
                halo.name = f"{name}_{ring_tip}_ForceHalo"
                halo.data.materials.append(active_dot_mat)
                apply_scale(halo)
                halo.parent = hand_empty
                link_obj(halo)

    # 1. Left Hand: "READY TO PINCH" (Green Dots)
    # Positioned naturally in front of player, observing bench
    create_holographic_hand(
        name="HoloHand_Left_Ready",
        base_loc=(-0.70, -0.95, 1.18),
        base_rot=(35, 15, 20),
        state="ready",
        is_right=False,
    )

    # 2. Right Hand: "FIRMLY HELD" (Blue Dots)
    # Positioned gripping the 250ml NiCl2 green flask at x=-1.15, y=-0.60
    create_holographic_hand(
        name="HoloHand_Right_Held",
        base_loc=(-1.05, -0.68, 1.10),
        base_rot=(50, -25, -45),
        state="hold",
        is_right=True,
    )

    # 3. Center Target Indicator: "HOVERING OVER GLASSWARE" (Yellow Dots)
    # Proximity cursor near the 500ml blue flask
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.045, minor_radius=0.002, location=(-1.30, -0.40, 1.05)
    )
    prox_ring = bpy.context.active_object
    prox_ring.name = "HUD_Proximity_Target_Yellow"
    prox_ring.data.materials.append(mat_dot_yellow)
    apply_scale(prox_ring)
    link_obj(prox_ring)

    bpy.ops.object.text_add(location=(-1.35, -0.40, 1.15))
    txt_prox = bpy.context.active_object
    txt_prox.name = "Txt_Proximity_Lock"
    txt_prox.data.body = "[PINCH TO GRASP]"
    txt_prox.data.size = 0.011
    txt_prox.data.extrude = 0.0004
    txt_prox.rotation_euler = (math.radians(90), 0, 0)
    txt_prox.data.materials.append(mat_dot_yellow)
    link_obj(txt_prox)

    # =========================================================================
    # 5. Top Bar HUD: Current Quest Objective, Safety Alert Status & Game Mode Toggle
    # =========================================================================

    def create_top_bar_hud():
        """Constructs the spatial Top Bar HUD anchored in the player's upper FOV."""
        # Top Bar is positioned at z=1.85, y=-0.95, x=-0.95 (directly in player view frustum)
        TB_X = -0.90
        TB_Y = -1.10
        TB_Z = 1.68
        TB_W = 0.95
        TB_H = 0.075

        # 1. Main Frosted Backing Bar
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(TB_X, TB_Y, TB_Z))
        bar_bg = bpy.context.active_object
        bar_bg.name = "TopBar_Backing"
        bar_bg.scale = (TB_W, 0.004, TB_H)
        bar_bg.rotation_euler = (math.radians(72), 0, math.radians(20))
        bar_bg.data.materials.append(mat_hud_dark)
        apply_scale(bar_bg)
        link_obj(bar_bg)

        # Glowing Cyber Top Trim Rail
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(TB_X, TB_Y - 0.002, TB_Z + TB_H / 2))
        bar_rail = bpy.context.active_object
        bar_rail.name = "TopBar_TrimRail"
        bar_rail.scale = (TB_W + 0.01, 0.003, 0.004)
        bar_rail.rotation_euler = (math.radians(72), 0, math.radians(20))
        bar_rail.data.materials.append(mat_glow_cyan)
        apply_scale(bar_rail)
        link_obj(bar_rail)

        # 2. Section A (Left): Current Quest Objective
        bpy.ops.object.text_add(location=(TB_X - TB_W / 2 + 0.04, TB_Y - 0.006, TB_Z + 0.015))
        txt_q_title = bpy.context.active_object
        txt_q_title.name = "TopBar_Txt_QuestTitle"
        txt_q_title.data.body = "QUEST: Belousov-Zhabotinsky Oscillation"
        txt_q_title.data.size = 0.014
        txt_q_title.data.extrude = 0.0005
        txt_q_title.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_q_title.data.materials.append(mat_glow_cyan)
        link_obj(txt_q_title)

        bpy.ops.object.text_add(location=(TB_X - TB_W / 2 + 0.04, TB_Y - 0.006, TB_Z - 0.008))
        txt_q_obj = bpy.context.active_object
        txt_q_obj.name = "TopBar_Txt_QuestStep"
        txt_q_obj.data.body = "Step 2/4: Heat 50 mL Malonic Acid Solution to 45.0 °C  [Prog: 65%]"
        txt_q_obj.data.size = 0.0095
        txt_q_obj.data.extrude = 0.0004
        txt_q_obj.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_q_obj.data.materials.append(mat_text_white)
        link_obj(txt_q_obj)

        # 3. Section B (Center): Safety Alert Status
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(TB_X + 0.08, TB_Y - 0.004, TB_Z))
        safety_badge = bpy.context.active_object
        safety_badge.name = "TopBar_SafetyBadge"
        safety_badge.scale = (0.24, 0.003, TB_H * 0.75)
        safety_badge.rotation_euler = (math.radians(72), 0, math.radians(20))
        safety_badge.data.materials.append(mat_glow_emerald)
        apply_scale(safety_badge)
        link_obj(safety_badge)

        bpy.ops.object.text_add(location=(TB_X - 0.03, TB_Y - 0.007, TB_Z + 0.008))
        txt_safe = bpy.context.active_object
        txt_safe.name = "TopBar_Txt_Safety"
        txt_safe.data.body = "SAFETY: OPTIMAL"
        txt_safe.data.size = 0.012
        txt_safe.data.extrude = 0.0005
        txt_safe.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_safe.data.materials.append(mat_text_white)
        link_obj(txt_safe)

        bpy.ops.object.text_add(location=(TB_X - 0.03, TB_Y - 0.007, TB_Z - 0.010))
        txt_safe_sub = bpy.context.active_object
        txt_safe_sub.name = "TopBar_Txt_SafetySub"
        txt_safe_sub.data.body = "PPE: Nitrile + Shield | Sash 25cm"
        txt_safe_sub.data.size = 0.0075
        txt_safe_sub.data.extrude = 0.0003
        txt_safe_sub.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_safe_sub.data.materials.append(mat_hud_dark)
        link_obj(txt_safe_sub)

        # 4. Section C (Right): Active Game Mode Toggle (Story / Sandbox)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(TB_X + TB_W / 2 - 0.12, TB_Y - 0.004, TB_Z)
        )
        toggle_box = bpy.context.active_object
        toggle_box.name = "TopBar_ModeToggle"
        toggle_box.scale = (0.22, 0.003, TB_H * 0.70)
        toggle_box.rotation_euler = (math.radians(72), 0, math.radians(20))
        toggle_box.data.materials.append(mat_glow_cyan)
        apply_scale(toggle_box)
        link_obj(toggle_box)

        bpy.ops.object.text_add(location=(TB_X + TB_W / 2 - 0.22, TB_Y - 0.007, TB_Z + 0.004))
        txt_mode = bpy.context.active_object
        txt_mode.name = "TopBar_Txt_Mode"
        txt_mode.data.body = "[STORY]  SANDBOX"
        txt_mode.data.size = 0.011
        txt_mode.data.extrude = 0.0005
        txt_mode.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_mode.data.materials.append(mat_text_white)
        link_obj(txt_mode)

        bpy.ops.object.text_add(location=(TB_X + TB_W / 2 - 0.22, TB_Y - 0.007, TB_Z - 0.014))
        txt_hint = bpy.context.active_object
        txt_hint.name = "TopBar_Txt_Hotkey"
        txt_hint.data.body = "Press [TAB] to switch"
        txt_hint.data.size = 0.007
        txt_hint.data.extrude = 0.0003
        txt_hint.rotation_euler = (math.radians(72), 0, math.radians(20))
        txt_hint.data.materials.append(mat_hud_dark)
        link_obj(txt_hint)

    create_top_bar_hud()

    # =========================================================================
    # 6. Audio-Visual Feedback on Level-Up and Quest Completion
    # =========================================================================

    def create_celebratory_av_feedback(name, x, y, z):
        """Constructs expanding holographic shockwave rings, trophy banner, and energy particles."""
        # 1. Concentric Holographic Expansion Rings (Shockwave Ripple)
        for r_idx, r_rad in enumerate([0.16, 0.24, 0.32]):
            bpy.ops.mesh.primitive_torus_add(
                major_radius=r_rad, minor_radius=0.0025, location=(x, y, z)
            )
            shockwave = bpy.context.active_object
            shockwave.name = f"{name}_ShockwaveRing_{r_idx}"
            shockwave.data.materials.append(mat_glow_gold if r_idx == 0 else mat_glow_cyan)
            apply_scale(shockwave)
            link_obj(shockwave)

        # 2. Level-Up Floating Holographic Banner
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y - 0.005, z + 0.14))
        trophy_plate = bpy.context.active_object
        trophy_plate.name = f"{name}_TrophyPlate"
        trophy_plate.scale = (0.28, 0.003, 0.075)
        trophy_plate.data.materials.append(mat_hud_dark)
        apply_scale(trophy_plate)
        link_obj(trophy_plate)

        # Golden Accent Ribbon
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y - 0.007, z + 0.14))
        trophy_frame = bpy.context.active_object
        trophy_frame.name = f"{name}_TrophyFrame"
        trophy_frame.scale = (0.284, 0.002, 0.079)
        trophy_frame.data.materials.append(mat_glow_gold)
        apply_scale(trophy_frame)
        link_obj(trophy_frame)

        # Banner Text - LEVEL UP!
        bpy.ops.object.text_add(location=(x - 0.12, y - 0.010, z + 0.155))
        txt_lvl = bpy.context.active_object
        txt_lvl.name = f"{name}_Txt_LevelUp"
        txt_lvl.data.body = "★ QUEST COMPLETE! LEVEL 4 ★"
        txt_lvl.data.size = 0.014
        txt_lvl.data.extrude = 0.0006
        txt_lvl.rotation_euler = (math.radians(90), 0, 0)
        txt_lvl.data.materials.append(mat_glow_gold)
        link_obj(txt_lvl)

        # Subtext - Unlocked Reward & XP
        bpy.ops.object.text_add(location=(x - 0.12, y - 0.010, z + 0.125))
        txt_reward = bpy.context.active_object
        txt_reward.name = f"{name}_Txt_Reward"
        txt_reward.data.body = "+350 XP | Unlocked: Burette & Spectrometer"
        txt_reward.data.size = 0.009
        txt_reward.data.extrude = 0.0004
        txt_reward.rotation_euler = (math.radians(90), 0, 0)
        txt_reward.data.materials.append(mat_text_white)
        link_obj(txt_reward)

        # 3. Orbiting Sparkle / Energy Particle Mesh Motifs
        sparkle_coords = [
            (-0.12, -0.02, 0.08),
            (0.14, 0.01, 0.09),
            (-0.08, 0.02, 0.22),
            (0.10, -0.01, 0.23),
            (0.00, -0.03, -0.06),
        ]
        for s_idx, (sx, sy, sz) in enumerate(sparkle_coords):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=(x + sx, y + sy, z + sz))
            spark = bpy.context.active_object
            spark.name = f"{name}_Sparkle_{s_idx}"
            spark.data.materials.append(mat_glow_gold if s_idx % 2 == 0 else mat_glow_cyan)
            apply_scale(spark)
            link_obj(spark)

    # Spawn celebratory AV feedback around the primary reaction station
    create_celebratory_av_feedback("FX_Celebration", x=-1.15, y=-0.60, z=1.35)

    # =========================================================================
    # 7. Dedicated Player Camera: Cam_Player_HUD_View
    # =========================================================================
    cam_name = "Cam_Player_HUD_View"
    cam_obj = bpy.data.objects.get(cam_name)
    if not cam_obj:
        cam_data = bpy.data.cameras.new(cam_name)
        cam_data.lens = 32.0  # Wide-angle 32mm FOV for immersive first-person simulation view
        cam_obj = bpy.data.objects.new(cam_name, cam_data)
        link_obj(cam_obj)

    # Positioned right in front of the workbench where virtual hands & HUD are visible
    cam_obj.location = (-0.90, -1.55, 1.48)
    cam_obj.rotation_euler = (math.radians(72), 0, math.radians(20))

    # Set as active camera for rendering
    bpy.context.scene.camera = cam_obj

    print("[SUCCESS] ChemLab HUD & 3D Spatial UI System successfully generated!")


if __name__ == "__main__":
    build_hud_ui()
