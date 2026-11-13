# Athanor Ascension - Laboratory Hub
# Central rotunda connecting all 15 laboratory archetypes,
# physical 3D Apparatus Practicum Kiosk, Pneumatic Transit Fast Travel Station,
# and Local AI Research Advisor Terminal.

extends Node3D

class_name LabHub

const FLOOR_EPOXY_ALBEDO: String = "res://assets/textures/floor_epoxy_albedo.png"
const FLOOR_EPOXY_NORMAL: String = "res://assets/textures/floor_epoxy_normal.png"
const STEEL_BRUSHED_ALBEDO: String = "res://assets/textures/steel_brushed_albedo.png"
const STEEL_BRUSHED_NORMAL: String = "res://assets/textures/steel_brushed_normal.png"

@export var auto_load_labs: bool = true

# Lab archetypes from labs.json
var labs: Array[Dictionary] = []
var _current_lab: String = ""
var _player: Node3D

# Lab positions in hub (circular arrangement)
var _lab_positions: Dictionary = {}

# Active interaction state
var _active_interaction_type: String = ""
var _interaction_hud: Control

# Shared PBR Materials (Optimized for Intel Iris Xe Compatibility renderer)
var _mat_floor: StandardMaterial3D
var _mat_pillar: StandardMaterial3D
var _mat_arch: StandardMaterial3D
var _mat_cyan_glow: StandardMaterial3D
var _mat_amber_glow: StandardMaterial3D
var _mat_green_glow: StandardMaterial3D
var _mat_terminal: StandardMaterial3D
var _mat_glass: StandardMaterial3D


func _ready() -> void:
	_init_shared_materials()
	_load_labs_data()
	_create_hub_architecture()
	_generate_hub_layout()
	_create_practicum_kiosk()
	_create_pneumatic_transit_station()
	_create_ai_advisor_kiosk()
	_create_photorealistic_bench_kiosk()
	_create_interaction_hud()
	_setup_player()

	if auto_load_labs:
		_preload_lab_scenes()


func _init_shared_materials() -> void:
	_mat_floor = StandardMaterial3D.new()
	_mat_floor.albedo_color = Color(0.06, 0.07, 0.09)
	_mat_floor.metallic = 0.25
	_mat_floor.roughness = 0.35

	_mat_pillar = StandardMaterial3D.new()
	_mat_pillar.albedo_color = Color(0.12, 0.14, 0.17)
	_mat_pillar.metallic = 0.65
	_mat_pillar.roughness = 0.25

	_mat_arch = StandardMaterial3D.new()
	_mat_arch.albedo_color = Color(0.09, 0.11, 0.14)
	_mat_arch.metallic = 0.4
	_mat_arch.roughness = 0.45

	_mat_cyan_glow = StandardMaterial3D.new()
	_mat_cyan_glow.albedo_color = Color(0.2, 0.85, 0.95)
	_mat_cyan_glow.emission_enabled = true
	_mat_cyan_glow.emission = Color(0.2, 0.85, 0.95)
	_mat_cyan_glow.emission_energy_multiplier = 2.2

	_mat_amber_glow = StandardMaterial3D.new()
	_mat_amber_glow.albedo_color = Color(1.0, 0.72, 0.25)
	_mat_amber_glow.emission_enabled = true
	_mat_amber_glow.emission = Color(1.0, 0.72, 0.25)
	_mat_amber_glow.emission_energy_multiplier = 2.0

	_mat_green_glow = StandardMaterial3D.new()
	_mat_green_glow.albedo_color = Color(0.25, 0.92, 0.55)
	_mat_green_glow.emission_enabled = true
	_mat_green_glow.emission = Color(0.25, 0.92, 0.55)
	_mat_green_glow.emission_energy_multiplier = 2.0

	_mat_terminal = StandardMaterial3D.new()
	_mat_terminal.albedo_color = Color(0.03, 0.05, 0.08)
	_mat_terminal.metallic = 0.85
	_mat_terminal.roughness = 0.2

	_mat_glass = StandardMaterial3D.new()
	_mat_glass.albedo_color = Color(0.75, 0.92, 0.98, 0.35)
	_mat_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_glass.roughness = 0.05
	_mat_glass.metallic = 0.1

	_apply_generated_textures()


func _apply_generated_textures() -> void:
	# PBR maps baked in Blender (tools/blender/build_lab_textures.py).
	# Guarded so the hub still renders on a checkout without generated assets.
	if ResourceLoader.exists(FLOOR_EPOXY_ALBEDO):
		_mat_floor.albedo_texture = load(FLOOR_EPOXY_ALBEDO)
		_mat_floor.uv1_scale = Vector3(8.0, 8.0, 1.0)
		if ResourceLoader.exists(FLOOR_EPOXY_NORMAL):
			_mat_floor.normal_enabled = true
			_mat_floor.normal_texture = load(FLOOR_EPOXY_NORMAL)
			_mat_floor.normal_scale = 0.55

	if ResourceLoader.exists(STEEL_BRUSHED_ALBEDO):
		var steel: Texture2D = load(STEEL_BRUSHED_ALBEDO)
		var steel_normal: Texture2D = null
		if ResourceLoader.exists(STEEL_BRUSHED_NORMAL):
			steel_normal = load(STEEL_BRUSHED_NORMAL)
		for material in [_mat_pillar, _mat_arch]:
			material.albedo_texture = steel
			material.uv1_scale = Vector3(2.0, 2.0, 1.0)
			if steel_normal != null:
				material.normal_enabled = true
				material.normal_texture = steel_normal
				material.normal_scale = 0.75


func _create_hub_architecture() -> void:
	# 1. Main rotunda floor slab
	var floor_mesh := CylinderMesh.new()
	floor_mesh.top_radius = 35.0
	floor_mesh.bottom_radius = 35.0
	floor_mesh.height = 0.6
	var floor_inst := MeshInstance3D.new()
	floor_inst.name = "RotundaFloor"
	floor_inst.mesh = floor_mesh
	floor_inst.material_override = _mat_floor
	floor_inst.position = Vector3(0.0, -0.3, 0.0)
	add_child(floor_inst)

	# 2. Glowing concentric navigation rings
	for r in [10.0, 20.0, 30.0]:
		var ring := MeshInstance3D.new()
		var ring_mesh := TorusMesh.new()
		ring_mesh.inner_radius = r - 0.08
		ring_mesh.outer_radius = r + 0.08
		ring.mesh = ring_mesh
		ring.material_override = _mat_cyan_glow
		ring.position = Vector3(0.0, 0.02, 0.0)
		add_child(ring)

	# 3. Ambient dome lighting
	var dome_light := DirectionalLight3D.new()
	dome_light.light_color = Color(0.85, 0.92, 1.0)
	dome_light.light_energy = 0.65
	dome_light.rotation = Vector3(-PI / 3.0, PI / 4.0, 0.0)
	add_child(dome_light)

	var atrium_omni := OmniLight3D.new()
	atrium_omni.position = Vector3(0.0, 14.0, 0.0)
	atrium_omni.light_color = Color(0.4, 0.85, 1.0)
	atrium_omni.light_energy = 2.5
	atrium_omni.omni_range = 45.0
	add_child(atrium_omni)


func _load_labs_data() -> void:
	var file = FileAccess.open("res://data/labs/labs.json", FileAccess.READ)
	if file:
		var json_str = file.get_as_text()
		file.close()
		var parsed = JSON.parse_string(json_str)
		if parsed and parsed is Dictionary and parsed.has("labs"):
			labs.clear()
			labs.assign(parsed.labs)


func _generate_hub_layout() -> void:
	var radius = 30.0
	var lab_count = labs.size()

	for i in range(lab_count):
		var lab = labs[i]
		var angle = (float(i) / maxf(float(lab_count), 1.0)) * TAU - PI / 2.0
		var pos = Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
		_lab_positions[lab.id] = pos
		_create_lab_entrance(lab, pos, angle)

	_create_central_atrium()


func _create_lab_entrance(lab: Dictionary, pos: Vector3, angle: float) -> void:
	var entrance = Node3D.new()
	entrance.name = "Entrance_%s" % lab.id
	entrance.position = pos
	entrance.rotation.y = angle + PI

	var arch = MeshInstance3D.new()
	var arch_mesh = CylinderMesh.new()
	arch_mesh.height = 4.5
	arch_mesh.top_radius = 2.6
	arch_mesh.bottom_radius = 2.6
	arch.mesh = arch_mesh
	arch.material_override = _mat_arch
	arch.position = Vector3(0, 2.25, 0)
	entrance.add_child(arch)

	var sign = Label3D.new()
	sign.text = "%s\n[%s]" % [str(lab.get("name", "Lab")), str(lab.get("archetype", "Sector")).to_upper()]
	sign.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sign.position = Vector3(0, 5.2, 3.0)
	sign.rotation.y = PI
	sign.modulate = Color(0.9, 0.95, 1.0)
	sign.font_size = 28
	sign.outline_size = 4
	sign.outline_modulate = Color(0.0, 0.0, 0.0, 0.8)
	entrance.add_child(sign)

	var status_light = OmniLight3D.new()
	status_light.light_color = _get_lab_status_color(lab.id)
	status_light.position = Vector3(0, 4.2, 0)
	status_light.light_energy = 2.2
	status_light.omni_range = 8.0
	entrance.add_child(status_light)

	var area = Area3D.new()
	area.name = "InteractionArea"
	var collision = CollisionShape3D.new()
	collision.shape = CylinderShape3D.new()
	(collision.shape as CylinderShape3D).radius = 3.2
	(collision.shape as CylinderShape3D).height = 5.0
	area.add_child(collision)
	area.body_entered.connect(func(_body): _on_player_approach(lab.id))
	entrance.add_child(area)

	add_child(entrance)


func _get_lab_status_color(lab_id: String) -> Color:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.save_data.statistics.labs_unlocked.has(lab_id):
		return Color(0.25, 0.92, 0.55)  # Green
	return Color(1.0, 0.75, 0.2)  # Amber


func _create_central_atrium() -> void:
	var atrium = Node3D.new()
	atrium.name = "CentralAtrium"
	atrium.position = Vector3.ZERO

	# Central structural pillar
	var pillar = MeshInstance3D.new()
	var pillar_mesh = CylinderMesh.new()
	pillar_mesh.height = 24.0
	pillar_mesh.top_radius = 3.2
	pillar_mesh.bottom_radius = 3.2
	pillar.mesh = pillar_mesh
	pillar.material_override = _mat_pillar
	pillar.position = Vector3(0, 12, 0)
	atrium.add_child(pillar)

	# Holographic directory billboard
	var directory = Label3D.new()
	directory.name = "DirectoryLabel"
	directory.text = "ATHANOR ASCENSION · LABORATORY ARCHIVE\n" + _generate_directory_text()
	directory.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	directory.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	directory.position = Vector3(0, 13.5, 0)
	directory.rotation.y = PI
	directory.font_size = 22
	directory.modulate = Color(0.3, 0.92, 1.0)
	directory.outline_size = 4
	atrium.add_child(directory)

	add_child(atrium)
	_create_suit_lockers()
	_create_central_elevator()


func _generate_directory_text() -> String:
	var text = ""
	for lab in labs:
		var status = "🟢" if _is_lab_unlocked(lab.id) else "🟡"
		text += "%s %s (%s)\n" % [status, lab.name, lab.archetype]
	return text


func _is_lab_unlocked(lab_id: String) -> bool:
	var save_manager = get_node_or_null("/root/SaveManager")
	return save_manager and save_manager.save_data.statistics.labs_unlocked.has(lab_id)


# =============================================================================
# 3D PRACTICUM TERMINAL KIOSK (8 Instruments)
# =============================================================================

func _create_practicum_kiosk() -> void:
	var kiosk := Node3D.new()
	kiosk.name = "PracticumKiosk"
	kiosk.position = Vector3(8.0, 0.0, 4.0)

	# Pedestal Base
	var base := MeshInstance3D.new()
	var base_mesh := BoxMesh.new()
	base_mesh.size = Vector3(1.6, 1.1, 1.2)
	base.mesh = base_mesh
	base.material_override = _mat_terminal
	base.position = Vector3(0.0, 0.55, 0.0)
	kiosk.add_child(base)

	# Angled Holographic Monitor Console
	var screen := MeshInstance3D.new()
	var screen_mesh := BoxMesh.new()
	screen_mesh.size = Vector3(1.4, 0.8, 0.06)
	screen.mesh = screen_mesh
	screen.material_override = _mat_cyan_glow
	screen.position = Vector3(0.0, 1.25, 0.2)
	screen.rotation.x = -PI / 5.0
	kiosk.add_child(screen)

	# 3D Sign
	var sign := Label3D.new()
	sign.text = "APPARATUS PRACTICUM · SOP SUITE\n[E] Open 8 Advanced Instruments"
	sign.position = Vector3(0.0, 2.1, 0.2)
	sign.rotation.y = PI
	sign.font_size = 22
	sign.modulate = Color(0.3, 0.92, 1.0)
	sign.outline_size = 4
	kiosk.add_child(sign)

	# Interaction Area
	var area := Area3D.new()
	area.name = "Area"
	var col := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 2.4
	col.shape = sphere
	area.add_child(col)
	area.position = Vector3(0.0, 1.0, 0.0)
	area.body_entered.connect(func(_b): _set_interaction_prompt("practicum", true))
	area.body_exited.connect(func(_b): _set_interaction_prompt("practicum", false))
	kiosk.add_child(area)

	add_child(kiosk)


# =============================================================================
# PNEUMATIC TRANSIT FAST TRAVEL STATION (7 Sectors)
# =============================================================================

func _create_pneumatic_transit_station() -> void:
	var station := Node3D.new()
	station.name = "PneumaticTransitStation"
	station.position = Vector3(-8.0, 0.0, 4.0)

	# Transparent Pneumatic Glass Tube
	var tube := MeshInstance3D.new()
	var tube_mesh := CylinderMesh.new()
	tube_mesh.top_radius = 1.2
	tube_mesh.bottom_radius = 1.2
	tube_mesh.height = 6.0
	tube.mesh = tube_mesh
	tube.material_override = _mat_glass
	tube.position = Vector3(0.0, 3.0, 0.0)
	station.add_child(tube)

	# Neon Compression Rings
	for y_offset in [1.5, 3.0, 4.5]:
		var ring := MeshInstance3D.new()
		var ring_mesh := TorusMesh.new()
		ring_mesh.inner_radius = 1.22
		ring_mesh.outer_radius = 1.34
		ring.mesh = ring_mesh
		ring.material_override = _mat_green_glow
		ring.position = Vector3(0.0, y_offset, 0.0)
		station.add_child(ring)

	# Transport Capsule inside tube
	var capsule := MeshInstance3D.new()
	var cap_mesh := CapsuleMesh.new()
	cap_mesh.radius = 0.85
	cap_mesh.height = 2.2
	capsule.mesh = cap_mesh
	capsule.material_override = _mat_terminal
	capsule.position = Vector3(0.0, 1.6, 0.0)
	station.add_child(capsule)

	# 3D Sign
	var sign := Label3D.new()
	sign.text = "PNEUMATIC TRANSIT NETWORK\n[E] Fast Travel to 7 Sectors"
	sign.position = Vector3(0.0, 4.2, 1.4)
	sign.rotation.y = PI
	sign.font_size = 22
	sign.modulate = Color(0.35, 0.95, 0.65)
	sign.outline_size = 4
	station.add_child(sign)

	# Interaction Area
	var area := Area3D.new()
	area.name = "Area"
	var col := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 2.4
	col.shape = sphere
	area.add_child(col)
	area.position = Vector3(0.0, 1.0, 0.0)
	area.body_entered.connect(func(_b): _set_interaction_prompt("transit", true))
	area.body_exited.connect(func(_b): _set_interaction_prompt("transit", false))
	station.add_child(area)

	add_child(station)


# =============================================================================
# LOCAL AI RESEARCH ADVISOR & PREDICTOR KIOSK
# =============================================================================

func _create_ai_advisor_kiosk() -> void:
	var kiosk := Node3D.new()
	kiosk.name = "AIAdvisorKiosk"
	kiosk.position = Vector3(0.0, 0.0, 8.0)

	# Monolith Column
	var col_inst := MeshInstance3D.new()
	var col_mesh := BoxMesh.new()
	col_mesh.size = Vector3(1.4, 2.2, 0.8)
	col_inst.mesh = col_mesh
	col_inst.material_override = _mat_terminal
	col_inst.position = Vector3(0.0, 1.1, 0.0)
	kiosk.add_child(col_inst)

	# Neural Core Glowing Sphere
	var orb := MeshInstance3D.new()
	var orb_mesh := SphereMesh.new()
	orb_mesh.radius = 0.35
	orb_mesh.height = 0.7
	orb.mesh = orb_mesh
	orb.material_override = _mat_amber_glow
	orb.position = Vector3(0.0, 2.4, 0.0)
	kiosk.add_child(orb)

	# 3D Sign
	var sign := Label3D.new()
	sign.text = "LOCAL AI RESEARCH ADVISOR\n[E] Real-Time Reaction Predictor & Kinetics"
	sign.position = Vector3(0.0, 3.1, 0.0)
	sign.rotation.y = PI
	sign.font_size = 22
	sign.modulate = Color(1.0, 0.78, 0.32)
	sign.outline_size = 4
	kiosk.add_child(sign)

	# Interaction Area
	var area := Area3D.new()
	area.name = "Area"
	var col := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 2.4
	col.shape = sphere
	area.add_child(col)
	area.position = Vector3(0.0, 1.0, 0.0)
	area.body_entered.connect(func(_b): _set_interaction_prompt("ai_advisor", true))
	area.body_exited.connect(func(_b): _set_interaction_prompt("ai_advisor", false))
	kiosk.add_child(area)

	add_child(kiosk)


# =============================================================================
# PHOTOREALISTIC BENCH KIOSK (Fractional Distillation & Precision Metrology)
# =============================================================================

func _create_photorealistic_bench_kiosk() -> void:
	var kiosk := Node3D.new()
	kiosk.name = "PhotorealisticBenchKiosk"
	kiosk.position = Vector3(0.0, 0.0, -8.5)

	# Obsidian Pedestal Base
	var base := MeshInstance3D.new()
	var base_mesh := BoxMesh.new()
	base_mesh.size = Vector3(2.2, 1.1, 1.4)
	base.mesh = base_mesh
	base.material_override = _mat_terminal
	base.position = Vector3(0.0, 0.55, 0.0)
	kiosk.add_child(base)

	# Glowing Cyan Glass Display Terminal
	var screen := MeshInstance3D.new()
	var screen_mesh := BoxMesh.new()
	screen_mesh.size = Vector3(1.8, 1.0, 0.08)
	screen.mesh = screen_mesh
	screen.material_override = _mat_cyan_glow
	screen.position = Vector3(0.0, 1.35, -0.2)
	screen.rotation.x = PI / 5.0
	kiosk.add_child(screen)

	# 3D Sign
	var sign := Label3D.new()
	sign.text = "PHOTOREALISTIC SYNTHESIS BENCH\n[E] Enter High-Fidelity 3D Laboratory (PiHKAL / TiHKAL / Vogel)"
	sign.position = Vector3(0.0, 2.2, -0.2)
	sign.rotation.y = 0.0
	sign.font_size = 20
	sign.modulate = Color(0.3, 0.92, 1.0)
	sign.outline_size = 4
	kiosk.add_child(sign)

	# Interaction Area
	var area := Area3D.new()
	area.name = "Area"
	var col := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 2.6
	col.shape = sphere
	area.add_child(col)
	area.position = Vector3(0.0, 1.0, 0.0)
	area.body_entered.connect(func(_b): _set_interaction_prompt("photorealistic_bench", true))
	area.body_exited.connect(func(_b): _set_interaction_prompt("photorealistic_bench", false))
	kiosk.add_child(area)

	add_child(kiosk)


# =============================================================================
# INTERACTION HUD & INPUT HANDLING
# =============================================================================

func _create_interaction_hud() -> void:
	_interaction_hud = Control.new()
	_interaction_hud.name = "InteractionHUD"
	_interaction_hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	_interaction_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var prompt_panel := PanelContainer.new()
	prompt_panel.name = "PromptPanel"
	prompt_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	prompt_panel.position = Vector2(-220.0, -80.0)
	prompt_panel.custom_minimum_size = Vector2(440.0, 50.0)
	prompt_panel.visible = false

	var prompt_label := Label.new()
	prompt_label.name = "PromptLabel"
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	prompt_label.add_theme_font_size_override("font_size", 16)
	prompt_label.add_theme_color_override("font_color", Color(0.2, 0.9, 1.0))
	prompt_panel.add_child(prompt_label)

	_interaction_hud.add_child(prompt_panel)
	add_child(_interaction_hud)


func _set_interaction_prompt(type: String, active: bool) -> void:
	if not _interaction_hud:
		return
	var panel = _interaction_hud.get_node_or_null("PromptPanel")
	var label = panel.get_node_or_null("PromptLabel") if panel else null
	if not panel or not label:
		return

	if active:
		_active_interaction_type = type
		panel.visible = true
		match type:
			"practicum":
				label.text = "Press [E] to Open Laboratory Apparatus Practicum"
			"transit":
				label.text = "Press [E] to Access Pneumatic Transit Network (Fast Travel)"
			"ai_advisor":
				label.text = "Press [E] to Consult Local AI Research Advisor"
			"photorealistic_bench":
				label.text = "Press [E] to Enter Photorealistic Synthesis Bench"
			_:
				label.text = "Press [E] to Interact"
	else:
		if _active_interaction_type == type:
			_active_interaction_type = ""
			panel.visible = false


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact") or (event is InputEventKey and event.pressed and event.keycode == KEY_E):
		if not _active_interaction_type.is_empty():
			_execute_active_interaction()


func _execute_active_interaction() -> void:
	match _active_interaction_type:
		"photorealistic_bench":
			print("Launching Photorealistic Synthesis Bench...")
			get_tree().change_scene_to_file("res://scenes/laboratories/photorealistic_bench.tscn")
		"practicum":
			print("Launching Apparatus Practicum scene...")
			get_tree().change_scene_to_file("res://scenes/laboratories/apparatus_practicum.tscn")
		"transit":
			print("Opening Pneumatic Transit Selector...")
			var owm = get_node_or_null("/root/OpenWorldManager")
			if owm:
				# Default cycle to next unlocked sector
				var cur_sec = owm.get_current_sector()
				var next_sec = "sector_underground" if cur_sec.get("id", "") == "sector_atrium" else "sector_atrium"
				owm.fast_travel_to_sector(next_sec)
		"ai_advisor":
			print("Opening AI Research Advisor status...")
			# Show advisor message in HUD
			var panel = _interaction_hud.get_node_or_null("PromptPanel")
			var label = panel.get_node_or_null("PromptLabel") if panel else null
			if label:
				label.text = "AI Advisor: Deterministic reaction engine active (100% offline ready)."


func _create_suit_lockers() -> void:
	var suits = ["teaching", "analytical", "organic_synthesis", "electrochemistry",
	             "genomics", "cell_culture", "radiochemistry", "accelerator",
	             "fusor", "materials", "cleanroom", "pilot_plant", "forensic", "orbital", "cryogenic"]

	for i in range(suits.size()):
		var suit_id = suits[i]
		var angle = (float(i) / maxf(float(suits.size()), 1.0)) * TAU
		var radius = 8.0
		var pos = Vector3(cos(angle) * radius, 0, sin(angle) * radius)

		var locker = Node3D.new()
		locker.name = "Locker_%s" % suit_id
		locker.position = pos
		locker.rotation.y = angle + PI

		var mesh = MeshInstance3D.new()
		mesh.mesh = BoxMesh.new()
		(mesh.mesh as BoxMesh).size = Vector3(1.8, 2.4, 0.8)
		mesh.material_override = _mat_terminal
		mesh.position = Vector3(0, 1.2, 0.0)
		locker.add_child(mesh)

		var label = Label3D.new()
		label.text = suit_id.replace("_", " ").capitalize()
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.position = Vector3(0, 2.6, 0.5)
		label.rotation.y = PI
		label.font_size = 20
		label.modulate = Color(0.85, 0.95, 1.0)
		locker.add_child(label)

		var area = Area3D.new()
		var collision = CollisionShape3D.new()
		collision.shape = BoxShape3D.new()
		(collision.shape as BoxShape3D).size = Vector3(2.5, 2.8, 1.8)
		area.add_child(collision)
		area.body_entered.connect(func(_body): _on_suit_interact(suit_id))
		locker.add_child(area)

		add_child(locker)


func _create_central_elevator() -> void:
	var elevator = Node3D.new()
	elevator.name = "CentralElevator"
	elevator.position = Vector3(0, 0, -8)

	var shaft = MeshInstance3D.new()
	var shaft_mesh = CylinderMesh.new()
	shaft_mesh.height = 36.0
	shaft_mesh.top_radius = 2.8
	shaft_mesh.bottom_radius = 2.8
	shaft.mesh = shaft_mesh
	shaft.material_override = _mat_pillar
	shaft.position = Vector3(0, 18, 0)
	add_child(shaft)

	var platform = MeshInstance3D.new()
	var platform_mesh = CylinderMesh.new()
	platform_mesh.height = 0.5
	platform_mesh.top_radius = 2.6
	platform_mesh.bottom_radius = 2.6
	platform.mesh = platform_mesh
	platform.material_override = _mat_terminal
	platform.position = Vector3(0, 0.5, 0)
	platform.name = "ElevatorPlatform"
	add_child(platform)

	var button = Area3D.new()
	button.name = "ElevatorCall"
	var collision = CollisionShape3D.new()
	collision.shape = SphereShape3D.new()
	(collision.shape as SphereShape3D).radius = 0.6
	button.add_child(collision)
	button.position = Vector3(0, 1.2, 3.2)
	button.connect("body_entered", _on_elevator_called)
	add_child(button)


func _on_suit_interact(suit_id: String) -> void:
	print("Suit interaction: %s" % suit_id)
	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager and inv_manager.has_method("open_radial_wheel"):
		inv_manager.open_radial_wheel("equipment")


func _on_player_approach(lab_id: String) -> void:
	print("Player approached lab entrance: %s" % lab_id)
	for lab in labs:
		if lab.get("id", "") == lab_id:
			var scene_path = lab.get("scene_path", "")
			if scene_path != "" and ResourceLoader.exists(scene_path):
				get_tree().change_scene_to_file(scene_path)
			break


func _on_elevator_called(_body: Node3D) -> void:
	print("Elevator called - access to upper levels (Genomics, Accelerator, Fusor, Orbital)")


func _setup_player() -> void:
	_player = get_node_or_null("../Player")
	if _player:
		_player.position = Vector3(0, 1, -30)


func _preload_lab_scenes() -> void:
	if DisplayServer.get_name() == "headless":
		return
	for lab in labs:
		if lab.has("scene_path"):
			var p = str(lab.scene_path)
			if ResourceLoader.exists(p):
				ResourceLoader.load_threaded_request(p)


func _process(delta: float) -> void:
	var directory = get_node_or_null("CentralAtrium/DirectoryLabel")
	if directory:
		directory.rotation.y = (directory.rotation.y + 0.1 * delta)

	# Animate AI neural orb floating oscillation
	var orb = get_node_or_null("AIAdvisorKiosk/MeshInstance3D2")
	if orb:
		orb.position.y = 2.4 + sin(Time.get_ticks_msec() / 400.0) * 0.08
