# Athanor Ascension — Aetherkin Companion 3D Entity (Godot 4 Engine)
# Real-time physical representation of laboratory companions in 3D space.
# Handles following the player, sniffing apparatus for hazardous leaks/purity,
# scavenging dangerous containment zones, and displaying elemental visual feedback.

class_name CompanionEntity
extends CharacterBody3D

# =============================================================================
# SIGNALS
# =============================================================================

signal sniff_started(apparatus: Node)
signal sniff_completed(apparatus: Node, diagnostic_data: Dictionary)
signal scavenge_started(zone: Node)
signal scavenge_completed(zone: Node, recovered_items: Array)
signal ability_executed(ability_id: String)

# =============================================================================
# PROPERTIES & RUNTIME STATE
# =============================================================================

@export var species_id: String = "cinderling"
@export var companion_name: String = "Cinderling"
@export var move_speed: float = 3.5
@export var follow_distance: float = 1.6
@export var stop_distance: float = 1.0

var companion_instance_id: String = ""
var target_player: Node3D = null
var current_task: String = "idle" # "idle", "follow", "sniff", "scavenge"
var target_destination: Vector3 = Vector3.ZERO
var task_target_node: Node = null
var task_timer: float = 0.0

# Procedural Visual Nodes
var visual_root: Node3D
var body_mesh: MeshInstance3D
var eye_left: MeshInstance3D
var eye_right: MeshInstance3D
var aura_light: OmniLight3D
var base_material: StandardMaterial3D

func _ready() -> void:
	add_to_group("companions")
	add_to_group("aetherkin")
	_build_procedural_visuals()
	_apply_species_visual_traits()


func _physics_process(delta: float) -> void:
	match current_task:
		"follow":
			_process_follow(delta)
		"sniff":
			_process_sniff(delta)
		"scavenge":
			_process_scavenge(delta)
		"idle":
			_process_idle(delta)

	move_and_slide()


# =============================================================================
# PROCEDURAL VISUAL ASSEMBLY (Intel Iris Xe 60 FPS Compliant)
# =============================================================================

func _build_procedural_visuals() -> void:
	visual_root = Node3D.new()
	visual_root.name = "VisualRoot"
	add_child(visual_root)

	# Main Body Mesh
	body_mesh = MeshInstance3D.new()
	body_mesh.name = "BodyMesh"
	var sphere = SphereMesh.new()
	sphere.radius = 0.22
	sphere.height = 0.44
	body_mesh.mesh = sphere
	visual_root.add_child(body_mesh)

	# Dynamic PBR Material
	base_material = StandardMaterial3D.new()
	base_material.roughness = 0.35
	base_material.metallic = 0.1
	body_mesh.set_surface_override_material(0, base_material)

	# Sensory Eyes / Optical Nodes
	var eye_mesh = SphereMesh.new()
	eye_mesh.radius = 0.04
	eye_mesh.height = 0.08

	var eye_mat = StandardMaterial3D.new()
	eye_mat.albedo_color = Color(0.1, 0.1, 0.1)
	eye_mat.emission_enabled = true
	eye_mat.emission = Color(0.0, 1.0, 0.8)
	eye_mat.emission_energy_multiplier = 2.5

	eye_left = MeshInstance3D.new()
	eye_left.name = "EyeLeft"
	eye_left.mesh = eye_mesh
	eye_left.position = Vector3(0.09, 0.08, -0.18)
	eye_left.set_surface_override_material(0, eye_mat)
	visual_root.add_child(eye_left)

	eye_right = MeshInstance3D.new()
	eye_right.name = "EyeRight"
	eye_right.mesh = eye_mesh
	eye_right.position = Vector3(-0.09, 0.08, -0.18)
	eye_right.set_surface_override_material(0, eye_mat)
	visual_root.add_child(eye_right)

	# Elemental Aura Light
	aura_light = OmniLight3D.new()
	aura_light.name = "AuraLight"
	aura_light.omni_range = 3.0
	aura_light.light_energy = 0.8
	add_child(aura_light)

	# Collision Shape for Lab Interaction
	var col = CollisionShape3D.new()
	col.name = "CollisionShape"
	var col_shape = SphereShape3D.new()
	col_shape.radius = 0.25
	col.shape = col_shape
	add_child(col)


func _apply_species_visual_traits() -> void:
	match species_id:
		"cinderling":
			base_material.albedo_color = Color(0.95, 0.45, 0.15)
			base_material.emission_enabled = true
			base_material.emission = Color(1.0, 0.3, 0.05)
			base_material.emission_energy_multiplier = 1.8
			aura_light.light_color = Color(1.0, 0.5, 0.1)
		"lab_rat", "instrumented_rat":
			base_material.albedo_color = Color(0.75, 0.72, 0.7)
			base_material.emission_enabled = false
			aura_light.light_color = Color(0.0, 0.8, 1.0)
			aura_light.light_energy = 0.4
		"wall_gecko":
			base_material.albedo_color = Color(0.3, 0.75, 0.4)
			base_material.emission_enabled = true
			base_material.emission = Color(0.2, 0.9, 0.4)
			base_material.emission_energy_multiplier = 1.0
			aura_light.light_color = Color(0.3, 1.0, 0.5)
		"brinejack":
			base_material.albedo_color = Color(0.2, 0.6, 0.9, 0.85)
			base_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			base_material.emission_enabled = true
			base_material.emission = Color(0.3, 0.7, 1.0)
			base_material.emission_energy_multiplier = 1.5
			aura_light.light_color = Color(0.2, 0.7, 1.0)
		_:
			base_material.albedo_color = Color(0.8, 0.6, 0.9)
			aura_light.light_color = Color(0.7, 0.5, 1.0)


# =============================================================================
# BEHAVIORS & AI PROCESSES
# =============================================================================

func set_target_player(player: Node3D) -> void:
	target_player = player
	current_task = "follow"


func _process_follow(delta: float) -> void:
	if target_player == null:
		velocity = Vector3.ZERO
		return

	var target_pos = target_player.global_position if (is_inside_tree() and target_player.is_inside_tree()) else target_player.position
	var current_pos = global_position if is_inside_tree() else position
	var dist_vec = target_pos - current_pos
	dist_vec.y = 0.0 # Keep on floor plane
	var dist = dist_vec.length()

	if dist > follow_distance:
		var dir = dist_vec.normalized()
		velocity.x = dir.x * move_speed
		velocity.z = dir.z * move_speed
		# Rotate towards movement direction
		var target_angle = atan2(-dir.x, -dir.z)
		rotation.y = lerp_angle(rotation.y, target_angle, 8.0 * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, 10.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 10.0 * delta)

	# Gentle breathing hover animation
	if visual_root:
		visual_root.position.y = sin(Time.get_ticks_msec() * 0.005) * 0.04


func _process_idle(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, 10.0 * delta)
	velocity.z = move_toward(velocity.z, 0.0, 10.0 * delta)
	if visual_root:
		visual_root.position.y = sin(Time.get_ticks_msec() * 0.003) * 0.03


func _process_sniff(delta: float) -> void:
	if task_target_node == null:
		current_task = "follow"
		return

	var target_pos = task_target_node.global_position if (is_inside_tree() and task_target_node.is_inside_tree()) else task_target_node.position
	var current_pos = global_position if is_inside_tree() else position
	var dist_vec = target_pos - current_pos
	dist_vec.y = 0.0
	var dist = dist_vec.length()

	if dist > 0.8:
		var dir = dist_vec.normalized()
		velocity.x = dir.x * move_speed
		velocity.z = dir.z * move_speed
		rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), 10.0 * delta)
	else:
		velocity = Vector3.ZERO
		task_timer += delta

		# Sniff head-bobbing sensory vibration
		if visual_root:
			visual_root.position.y = sin(task_timer * 20.0) * 0.06

		if task_timer >= 1.2:
			# Complete Sniff analysis
			var diagnostic = _perform_chemical_sniff_analysis(task_target_node)
			sniff_completed.emit(task_target_node, diagnostic)
			task_timer = 0.0
			task_target_node = null
			current_task = "follow"


func _process_scavenge(delta: float) -> void:
	if task_target_node == null:
		current_task = "follow"
		return

	var target_pos = task_target_node.global_position if (is_inside_tree() and task_target_node.is_inside_tree()) else task_target_node.position
	var current_pos = global_position if is_inside_tree() else position
	var dist_vec = target_pos - current_pos
	dist_vec.y = 0.0
	var dist = dist_vec.length()

	if dist > 0.6:
		var dir = dist_vec.normalized()
		velocity.x = dir.x * (move_speed * 1.3)
		velocity.z = dir.z * (move_speed * 1.3)
		rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), 12.0 * delta)
	else:
		velocity = Vector3.ZERO
		task_timer += delta
		if task_timer >= 1.5:
			# Complete scavenge
			var recovered = _perform_scavenge_loot(task_target_node)
			scavenge_completed.emit(task_target_node, recovered)
			task_timer = 0.0
			task_target_node = null
			current_task = "follow"


# =============================================================================
# ACTIVE LAB COMMANDS
# =============================================================================

func command_sniff(apparatus: Node) -> void:
	"""Command companion to approach and sniff apparatus for chemical composition & vapor leaks."""
	if apparatus == null:
		return
	task_target_node = apparatus
	task_timer = 0.0
	current_task = "sniff"
	sniff_started.emit(apparatus)


func command_scavenge(zone: Node) -> void:
	"""Command companion to dart into hazardous containment and scavenge dropped reagents."""
	if zone == null:
		return
	task_target_node = zone
	task_timer = 0.0
	current_task = "scavenge"
	scavenge_started.emit(zone)


func _perform_chemical_sniff_analysis(target: Node) -> Dictionary:
	var result = {
		"compound_name": "Ambient Air",
		"purity_pct": 99.5,
		"temperature_c": 22.0,
		"hazard_level": "SAFE",
		"ppm_leak": 0.0,
		"detected_anomalies": []
	}

	if target.has_method("get_sample_data"):
		var data = target.get_sample_data()
		result["compound_name"] = data.get("compound_name", "Unknown")
		result["concentration_mM"] = data.get("concentration_mM", 50.0)
		result["solvent"] = data.get("solvent", "CDCl3")
		result["purity_pct"] = 99.2
		result["ppm_leak"] = 0.02
	elif target.has_meta("compound_name"):
		result["compound_name"] = str(target.get_meta("compound_name"))
		result["purity_pct"] = 98.0
	else:
		result["compound_name"] = target.name

	# Species-specific diagnostic insights
	match species_id:
		"cinderling":
			result["thermal_stability"] = "High (Reaction well-buffered against exothermic surge)"
		"lab_rat", "instrumented_rat":
			result["ppm_leak"] = 0.005
			result["toxicity_alert"] = "Negative: Inhalation index well below OSHA PEL"
		"wall_gecko":
			result["particulate_count"] = "ISO Class 5 certified air cleanliness"

	return result


func _perform_scavenge_loot(target: Node) -> Array:
	var items = []
	if target.is_in_group("waste_drum") or target.name.to_lower().contains("waste"):
		items.append({"item_id": "salvaged_palladium_catalyst", "quantity": 1})
	elif target.is_in_group("fume_hood") or target.name.to_lower().contains("hood"):
		items.append({"item_id": "chiral_ligand_aliquot", "quantity": 2})
	else:
		items.append({"item_id": "reagent_sample_vial", "quantity": 1})
	return items
