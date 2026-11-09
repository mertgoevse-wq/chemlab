# ChemLab 3D Laboratory Simulation (Godot 4 Engine)
# Apparatus: NMR Sample Tube
# A pickupable sample tube for NMR spectrometer analysis

extends RigidBody3D
class_name NMRSampleTube

# =============================================================================
# SIGNALS
# =============================================================================

signal picked_up(player: Node)
signal dropped(player: Node)
signal inserted_into_nmr(nmr: Node)
signal removed_from_nmr(nmr: Node)

# =============================================================================
# EXPORTED PARAMETERS
# =============================================================================

@export_group("Sample Properties")
@export var sample_type: String = "nmr_sample"
@export var compound_name: String = "Ethanol"
@export var concentration_mM: float = 50.0
@export var solvent: String = "CDCl3"
@export var volume_ml: float = 0.6

@export_group("Physics Settings")
@export var pickup_mass: float = 0.05
@export var pickup_linear_damp: float = 0.1
@export var pickup_angular_damp: float = 0.1

# =============================================================================
# NODE REFERENCES
# =============================================================================

@onready var tube_mesh: MeshInstance3D = get_node_or_null("TubeMesh")
@onready var liquid_mesh: MeshInstance3D = get_node_or_null("LiquidMesh")
@onready var collision_shape: CollisionShape3D = get_node_or_null("CollisionShape3D")
@onready var meta_node: Node3D = get_node_or_null("Meta")

# =============================================================================
# RUNTIME STATE
# =============================================================================

var _is_held: bool = false
var _holder: Node = null
var _original_layer: int = 1
var _original_mask: int = 1
var _is_in_nmr: bool = false
var _current_nmr: Node = null

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	add_to_group("interactive_apparatus")
	add_to_group("apparatus")
	add_to_group("interactable")
	add_to_group("sample_tube")
	set_meta("is_apparatus", true)
	set_meta("apparatus_type", "nmr_sample_tube")
	set_meta("apparatus_name", "NMR Sample Tube")

	# Initialize physics properties for pickup
	mass = pickup_mass
	linear_damp = pickup_linear_damp
	angular_damp = pickup_angular_damp

	# Setup collision for pickup detection
	if collision_shape:
		collision_shape.disabled = false

	# Sync meta data
	_sync_meta_to_properties()

	print(">>> [NMRSampleTube] Initialized: %s (%s mM in %s)" % [compound_name, concentration_mM, solvent])


func _sync_meta_to_properties() -> void:
	if meta_node:
		compound_name = meta_node.get_meta("compound_name", compound_name)
		concentration_mM = meta_node.get_meta("concentration_mM", concentration_mM)
		solvent = meta_node.get_meta("solvent", solvent)
		volume_ml = meta_node.get_meta("volume_ml", volume_ml)
		sample_type = meta_node.get_meta("sample_type", sample_type)

		# Update meta node with current values
		meta_node.set_meta("compound_name", compound_name)
		meta_node.set_meta("concentration_mM", concentration_mM)
		meta_node.set_meta("solvent", solvent)
		meta_node.set_meta("volume_ml", volume_ml)
		meta_node.set_meta("sample_type", sample_type)


# =============================================================================
# PICKUP / DROP SYSTEM
# =============================================================================

func pickup(player: Node) -> bool:
	if _is_held:
		return false

	_is_held = true
	_holder = player

	# Save original collision settings
	if is CollisionObject3D:
		_original_layer = collision_layer
		_original_mask = collision_mask
		collision_layer = 0
		collision_mask = 0

	# Freeze physics while held
	freeze = true
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO

	# Emit signal
	picked_up.emit(player)

	# Notify InputManager
	var im = get_node_or_null("/root/InputManager")
	if im and im.has_method("grab_apparatus"):
		im.grab_apparatus(self)

	print(">>> [NMRSampleTube] Picked up by player: %s" % compound_name)
	return true


func drop(apply_impulse: bool = true) -> void:
	if not _is_held:
		return

	var holder = _holder
	_is_held = false
	_holder = null

	# Restore collision
	if is CollisionObject3D:
		collision_layer = _original_layer
		collision_mask = _original_mask

	# Restore physics
	freeze = false
	freeze_mode = RigidBody3D.FREEZE_MODE_NONE

	if apply_impulse:
		# Gentle toss forward
		var toss_dir = -global_transform.basis.z
		linear_velocity = Vector3(0, 0.5, 0) + toss_dir * 2.0
		angular_velocity = Vector3(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * 1.5

	# Notify InputManager
	var im = get_node_or_null("/root/InputManager")
	if im and im.has_method("release_apparatus"):
		im.release_apparatus()

	dropped.emit(holder)
	print(">>> [NMRSampleTube] Dropped: %s" % compound_name)


func place_on_surface(target_surface: Node, world_position: Vector3, surface_normal: Vector3) -> void:
	if not _is_held:
		return

	_is_held = false
	var holder = _holder
	_holder = null

	# Restore collision
	if is CollisionObject3D:
		collision_layer = 1
		collision_mask = 1

	# Restore physics
	freeze = false
	freeze_mode = RigidBody3D.FREEZE_MODE_NONE
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO

	# Position on surface
	global_position = world_position + surface_normal * 0.02
	global_rotation = Basis.IDENTITY

	dropped.emit(holder)
	print(">>> [NMRSampleTube] Placed on surface: %s" % compound_name)


# =============================================================================
# NMR INTEGRATION
# =============================================================================

func _on_body_entered(body: Node3D) -> void:
	# Check if entering NMR bore
	if body.has_meta("apparatus_type") and body.get_meta("apparatus_type") == "nmr_spectrometer":
		if not _is_held and not _is_in_nmr:
			_insert_into_nmr(body)


func _on_body_exited(body: Node3D) -> void:
	if body == _current_nmr:
		_remove_from_nmr()


var _is_in_nmr: bool = false
var _current_nmr: Node = null


func _insert_into_nmr(nmr: Node) -> void:
	if _is_in_nmr or _is_held:
		return

	_is_in_nmr = true
	_current_nmr = nmr

	# Position in NMR bore
	if nmr.has_node("SampleTubeSlot"):
		var slot = nmr.get_node("SampleTubeSlot")
		global_position = slot.global_position
		global_rotation = slot.global_rotation

	# Freeze in place
	freeze = true
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO

	# Disable collision while in NMR
	collision_layer = 0
	collision_mask = 0

	# Notify NMR
	if nmr.has_method("_on_sample_inserted"):
		nmr._on_sample_inserted(self)

	inserted_into_nmr.emit(nmr)
	print(">>> [NMRSampleTube] Inserted into NMR: %s" % compound_name)


func _remove_from_nmr() -> void:
	if not _is_in_nmr:
		return

	var nmr = _current_nmr
	_is_in_nmr = false
	_current_nmr = null

	# Restore physics
	freeze = false
	freeze_mode = RigidBody3D.FREEZE_MODE_NONE
	collision_layer = 1
	collision_mask = 1

	# Notify NMR
	if nmr and nmr.has_method("_on_sample_removed"):
		nmr._on_sample_removed(self)

	removed_from_nmr.emit(nmr)
	print(">>> [NMRSampleTube] Removed from NMR: %s" % compound_name)


# =============================================================================
# INTERACTION API
# =============================================================================

func get_interaction_info() -> Dictionary:
	return {
		"name": "NMR Sample Tube (%s)" % compound_name,
		"can_pickup": true,
		"prompt": "[E] Take Sample Tube (%s)" % compound_name,
		"hints": "Sample: %s (%0.1f mM in %s)\n[E] Take | [E] Insert into NMR" % [compound_name, concentration_mM, solvent],
	}


func on_picked_up(player: Node) -> void:
	pickup(player)


func on_dropped(player: Node) -> void:
	drop(true)


func interact(player: Node) -> void:
	if _is_held:
		drop(true)
	else:
		pickup(player)


# =============================================================================
# SAMPLE DATA ACCESS
# =============================================================================

func get_sample_data() -> Dictionary:
	return {
		"sample_type": sample_type,
		"compound_name": compound_name,
		"concentration_mM": concentration_mM,
		"solvent": solvent,
		"volume_ml": volume_ml,
		"temperature_c": 25.0,
	}


func get_sample_id() -> String:
	return "SAMPLE_%s_%s" % [compound_name.to_upper(), Time.get_unix_time_from_system()]


# =============================================================================
# SAVE/LOAD SUPPORT
# =============================================================================

func get_save_data() -> Dictionary:
	return {
		"compound_name": compound_name,
		"concentration_mM": concentration_mM,
		"solvent": solvent,
		"volume_ml": volume_ml,
		"sample_type": sample_type,
		"global_position": global_position,
		"global_rotation": global_rotation,
		"is_held": _is_held,
		"is_in_nmr": _is_in_nmr,
	}


func load_save_data(data: Dictionary) -> void:
	compound_name = data.get("compound_name", "Ethanol")
	concentration_mM = data.get("concentration_mM", 50.0)
	solvent = data.get("solvent", "CDCl3")
	volume_ml = data.get("volume_ml", 0.6)
	sample_type = data.get("sample_type", "nmr_sample")

	if data.has("global_position"):
		global_position = data.global_position
	if data.has("global_rotation"):
		global_rotation = data.global_rotation

	# Restore held state would be handled by player system

	_sync_meta_to_properties()
	print(">>> [NMRSampleTube] Save data loaded: %s" % compound_name)