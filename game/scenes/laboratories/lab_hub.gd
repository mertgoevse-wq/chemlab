# Athanor Ascension - Laboratory Hub
# Central hub connecting all 15 laboratory archetypes

extends Node3D

class_name LabHub

@export var auto_load_labs: bool = true

# Lab archetypes from labs.json
var labs: Array[Dictionary] = []
var _current_lab: String = ""
var _player: Node3D

# Lab positions in hub (circular arrangement)
var _lab_positions: Dictionary = {}

func _ready() -> void:
	_load_labs_data()
	_generate_hub_layout()
	_setup_player()

	if auto_load_labs:
		_preload_lab_scenes()

func _load_labs_data() -> void:
	var file = FileAccess.open("res://data/labs/labs.json", FileAccess.READ)
	if file:
		var json_str = file.get_as_text()
		file.close()
		var parsed = JSON.parse_string(json_str)
		if parsed:
			labs = parsed.labs

func _generate_hub_layout() -> void:
	# Arrange 15 labs in a circular hub with central atrium
	var center = Vector3(0, 0, 0)
	var radius = 30.0
	var lab_count = labs.size()

	for i in range(lab_count):
		var lab = labs[i]
		var angle = (float(i) / maxf(float(lab_count), 1.0)) * TAU - PI/2  # Start at top
		var pos = Vector3(cos(angle) * radius, 0, sin(angle) * radius)
		_lab_positions[lab.id] = pos

		# Create lab entrance marker
		_create_lab_entrance(lab, pos, angle)

	# Central atrium
	_create_central_atrium()

func _create_lab_entrance(lab: Dictionary, pos: Vector3, angle: float) -> void:
	var entrance = Node3D.new()
	entrance.name = "Entrance_%s" % lab.id
	entrance.position = pos
	entrance.rotation.y = angle + PI  # Face center

	# Entrance arch
	var arch = MeshInstance3D.new()
	arch.mesh = CylinderMesh.new()
	(arch.mesh as CylinderMesh).height = 4.0
	(arch.mesh as CylinderMesh).radius = 2.5
	arch.position = Vector3(0, 2, 0)
	entrance.add_child(arch)

	# Lab name sign
	var sign = Label3D.new()
	sign.text = lab.name
	sign.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sign.position = Vector3(0, 5, 3)
	sign.rotation.y = PI
	entrance.add_child(sign)

	# Status indicator
	var status_light = OmniLight3D.new()
	status_light.light_color = _get_lab_status_color(lab.id)
	status_light.position = Vector3(0, 4, 0)
	status_light.light_energy = 2.0
	entrance.add_child(status_light)

	# Interaction area
	var area = Area3D.new()
	area.name = "InteractionArea"
	var collision = CollisionShape3D.new()
	collision.shape = CylinderShape3D.new()
	(collision.shape as CylinderShape3D).radius = 3.0
	(collision.shape as CylinderShape3D).height = 5.0
	area.add_child(collision)
	area.body_entered.connect(func(_body): _on_player_approach(lab.id))
	entrance.add_child(area)

	add_child(entrance)

func _get_lab_status_color(lab_id: String) -> Color:
	# Green = unlocked, Yellow = available, Red = locked
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.save_data.statistics.labs_unlocked.has(lab_id):
		return Color(0.2, 0.8, 0.2)  # Green
	return Color(1.0, 0.8, 0.0)  # Yellow (available)

func _create_central_atrium() -> void:
	var atrium = Node3D.new()
	atrium.name = "CentralAtrium"
	atrium.position = Vector3(0, 0, 0)

	# Central pillar
	var pillar = MeshInstance3D.new()
	pillar.mesh = CylinderMesh.new()
	(pillar.mesh as CylinderMesh).height = 20.0
	(pillar.mesh as CylinderMesh).radius = 3.0
	pillar.position = Vector3(0, 10, 0)
	add_child(pillar)

	# Holographic directory
	var directory = Label3D.new()
	directory.text = "LABORATORY NETWORK\n\n" + _generate_directory_text()
	directory.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	directory.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	directory.position = Vector3(0, 12, 0)
	directory.rotation.y = PI
	add_child(directory)

	# Suit lockers around pillar
	_create_suit_lockers()

	# Central elevator to upper levels
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

		# Locker mesh
		var mesh = MeshInstance3D.new()
		mesh.mesh = BoxMesh.new()
		(mesh.mesh as BoxMesh).size = Vector3(2.0, 2.5, 1.0)
		mesh.position = Vector3(0, 1.25, 1.5)
		locker.add_child(mesh)

		# Suit label
		var label = Label3D.new()
		label.text = suit_id.replace("_", " ").capitalize()
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.position = Vector3(0, 2.8, 2.0)
		label.rotation.y = PI
		locker.add_child(label)

		# Interaction
		var area = Area3D.new()
		var collision = CollisionShape3D.new()
		collision.shape = BoxShape3D.new()
		(collision.shape as BoxShape3D).size = Vector3(3.0, 3.0, 2.0)
		area.add_child(collision)
		area.body_entered.connect(func(_body): _on_suit_interact(suit_id))
		locker.add_child(area)

		add_child(locker)

func _create_central_elevator() -> void:
	var elevator = Node3D.new()
	elevator.name = "CentralElevator"
	elevator.position = Vector3(0, 0, -8)

	# Elevator shaft
	var shaft = MeshInstance3D.new()
	shaft.mesh = CylinderMesh.new()
	(shaft.mesh as CylinderMesh).height = 50.0
	(shaft.mesh as CylinderMesh).radius = 3.0
	shaft.position = Vector3(0, 25, 0)
	add_child(shaft)

	# Elevator platform
	var platform = MeshInstance3D.new()
	platform.mesh = CylinderMesh.new()
	(platform.mesh as CylinderMesh).height = 0.5
	(platform.mesh as CylinderMesh).radius = 2.8
	platform.position = Vector3(0, 1.0, 0)
	platform.name = "ElevatorPlatform"
	add_child(platform)

	# Call button
	var button = Area3D.new()
	button.name = "ElevatorCall"
	var collision = CollisionShape3D.new()
	collision.shape = SphereShape3D.new()
	(collision.shape as SphereShape3D).radius = 0.5
	button.add_child(collision)
	button.position = Vector3(0, 1.5, 3.5)
	button.connect("body_entered", _on_elevator_called)
	add_child(button)

func _on_suit_interact(suit_id: String) -> void:
	# Open suit selection UI
	print("Suit interaction: %s" % suit_id)
	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager:
		inv_manager.open_radial_wheel("equipment")

func _on_player_approach(lab_id: String) -> void:
	print("Player approached lab entrance: %s" % lab_id)
	for lab in labs:
		if lab.get("id", "") == lab_id:
			var scene_path = lab.get("scene_path", "")
			if scene_path != "":
				get_tree().change_scene_to_file(scene_path)
			break

func _on_elevator_called(body: Node3D) -> void:
	# Animate elevator to upper levels
	print("Elevator called - access to upper levels (Genomics, Accelerator, Fusor, Orbital)")
	# Would animate platform and change scene

func _setup_player() -> void:
	# Player spawns at hub entrance
	_player = get_node_or_null("../Player")
	if _player:
		_player.position = Vector3(0, 1, -35)  # Hub entrance

func _preload_lab_scenes() -> void:
	# Preload all lab scenes for instant transition
	for lab in labs:
		if lab.has("scene_path"):
			ResourceLoader.load_threaded_request(lab.scene_path)

func _process(delta: float) -> void:
	# Rotate directory
	var directory = get_node_or_null("CentralAtrium/Label3D")
	if directory:
		directory.rotation.y = (directory.rotation.y + 0.1 * delta) % TAU

	# Pulse suit locker lights
	for child in get_children():
		if child.name.begins_with("Locker_"):
			var light = child.get_node_or_null("OmniLight3D")
			if light:
				light.light_energy = 1.0 + sin(Time.get_ticks_msec() / 500.0) * 0.3