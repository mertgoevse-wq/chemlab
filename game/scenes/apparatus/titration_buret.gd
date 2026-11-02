# Titration Buret (Godot 4 Engine)
# High-precision volumetric titration apparatus with retort stand, clamp,
# 50.00 mL precision glass buret tube, rotatable PTFE stopcock, and discrete droplet emitter.
#
# Features:
# 1. Retort stand with heavy cast iron base, chrome rod, and buret clamp
# 2. 50.00 mL graduated glass buret tube with physical meniscus level tracking
# 3. Stopcock Valve state machine: CLOSED, DROPWISE (1 drop / 0.8s = 0.05 mL), STREAM (continuous)
# 4. GPUParticles3D discrete droplet emitter at needle tip
# 5. RayCast3D receiving vessel detection with stoichiometric titrant transfer (0.1 M NaOH)
# 6. Automatic pH curve calculation, phenolphthalein endpoint transition, and QuestManager integration

extends StaticBody3D
class_name TitrationBuret

# =============================================================================
# ENUMS & SIGNALS
# =============================================================================
enum ValveState {
	CLOSED,    # Stopcock closed (0 mL/s)
	DROPWISE,  # Analytical titration mode: 1 drop every 0.8s (0.05 mL/drop = 0.0625 mL/s)
	STREAM     # Continuous flush/drain mode: ~2.5 mL/s
}

signal valve_state_changed(new_state: ValveState)
signal drop_dispensed(volume_ml: float, titrant_reagent: String, moles_titrant: float)
signal volume_changed(remaining_ml: float, delivered_ml: float)
signal buret_emptied()
signal endpoint_reached(receiving_vessel: Node, current_ph: float)
signal receiving_flask_placed(flask: Node)
signal receiving_flask_removed(flask: Node)

# =============================================================================
# CONSTANTS & SPECIFICATIONS
# =============================================================================
const GROUP_INTERACTIVE_APPARATUS: String = "interactive_apparatus"

const MAX_CAPACITY_ML: float = 50.00
const DROP_VOLUME_ML: float = 0.05         # 0.05 mL per analytical drop (20 drops/mL)
const DROP_INTERVAL_S: float = 0.80        # 1 drop every 0.8 seconds in DROPWISE mode
const STREAM_FLOW_RATE_ML_S: float = 2.50  # 2.50 mL/s in continuous stream mode

# Physical tube dimensions for visual meniscus scaling
const TUBE_CALIBRATED_HEIGHT: float = 0.50 # Height of calibrated liquid column in meters
const TUBE_BOTTOM_Y: float = 0.26          # Y position corresponding to 50.00 mL reading (Empty)
const TUBE_TOP_Y: float = 0.76             # Y position corresponding to 0.00 mL reading (Full)

# Default Titrant Chemistry (Standard Analytical 0.1 M NaOH)
const DEFAULT_TITRANT_ID: String = "naoh"
const DEFAULT_TITRANT_NAME: String = "0.1 M Sodium Hydroxide (NaOH)"
const DEFAULT_TITRANT_MOLARITY: float = 0.10   # mol/L
const DEFAULT_TITRANT_MW: float = 39.997       # g/mol
const DEFAULT_TITRANT_DENSITY: float = 1.040   # g/mL
const DEFAULT_TITRANT_PH: float = 13.00

# Endpoint detection (Phenolphthalein indicator transition: pH 8.2 - 10.0, faint pink endpoint ~8.5)
const ENDPOINT_MIN_PH: float = 8.2
const ENDPOINT_TARGET_PH: float = 8.5

# =============================================================================
# NODE REFERENCES
# =============================================================================
@onready var stopcock_valve: MeshInstance3D = $StopcockValve
@onready var drop_emitter: GPUParticles3D = $DropEmitter
@onready var drop_target_ray: RayCast3D = $DropTargetRay
@onready var liquid_column: MeshInstance3D = $BuretAssembly/LiquidColumn
@onready var meniscus_marker: Marker3D = get_node_or_null("BuretAssembly/MeniscusMarker")
@onready var flask_snap_point: Marker3D = get_node_or_null("ReceivingFlaskPoint")
@onready var readout_label: Label3D = get_node_or_null("GraduationReadout")

@onready var audio_drip: AudioStreamPlayer3D = get_node_or_null("AudioDrip")
@onready var audio_valve: AudioStreamPlayer3D = get_node_or_null("AudioValve")

# =============================================================================
# EXPORTED / CONFIGURABLE PROPERTIES
# =============================================================================
@export var current_volume_ml: float = MAX_CAPACITY_ML
@export var delivered_volume_ml: float = 0.00
@export var titrant_reagent: String = DEFAULT_TITRANT_ID
@export var titrant_molarity: float = DEFAULT_TITRANT_MOLARITY
@export var current_valve_state: ValveState = ValveState.CLOSED

# Placed receiving flask underneath
@export var placed_receiving_flask: Node = null

# =============================================================================
# STATE VARIABLES
# =============================================================================
var drop_timer: float = 0.0
var stream_accumulator: float = 0.0
var initial_column_pos: Vector3 = Vector3.ZERO
var initial_column_scale: Vector3 = Vector3.ONE
var is_endpoint_announced: bool = false

# =============================================================================
# LIFECYCLE
# =============================================================================
func _ready() -> void:
	add_to_group(GROUP_INTERACTIVE_APPARATUS)

	if liquid_column:
		initial_column_pos = liquid_column.position
		initial_column_scale = liquid_column.scale

	if drop_emitter:
		drop_emitter.emitting = false

	if drop_target_ray:
		drop_target_ray.enabled = true
		drop_target_ray.collide_with_areas = true
		drop_target_ray.collide_with_bodies = true

	_update_valve_visual(false)
	_update_meniscus_display()


func _physics_process(delta: float) -> void:
	match current_valve_state:
		ValveState.CLOSED:
			drop_timer = 0.0
			stream_accumulator = 0.0
			if drop_emitter and drop_emitter.emitting:
				drop_emitter.emitting = false

		ValveState.DROPWISE:
			if current_volume_ml <= 0.0:
				set_valve_state(ValveState.CLOSED)
				buret_emptied.emit()
				return

			drop_timer += delta
			if drop_timer >= DROP_INTERVAL_S:
				drop_timer -= DROP_INTERVAL_S
				_dispense_discrete_drop(DROP_VOLUME_ML)

		ValveState.STREAM:
			if current_volume_ml <= 0.0:
				set_valve_state(ValveState.CLOSED)
				buret_emptied.emit()
				return

			if drop_emitter and not drop_emitter.emitting:
				drop_emitter.emitting = true

			var flow_amount = STREAM_FLOW_RATE_ML_S * delta
			flow_amount = minf(flow_amount, current_volume_ml)
			_dispense_continuous_stream(flow_amount)


# =============================================================================
# VALVE STATE MACHINE
# =============================================================================
func set_valve_state(new_state: ValveState) -> void:
	if current_valve_state == new_state:
		return

	current_valve_state = new_state
	drop_timer = 0.0
	stream_accumulator = 0.0

	_update_valve_visual(true)

	if audio_valve:
		audio_valve.play()

	valve_state_changed.emit(current_valve_state)


func cycle_valve_state() -> void:
	match current_valve_state:
		ValveState.CLOSED:
			set_valve_state(ValveState.DROPWISE)
		ValveState.DROPWISE:
			set_valve_state(ValveState.STREAM)
		ValveState.STREAM:
			set_valve_state(ValveState.CLOSED)


func _update_valve_visual(animated: bool = true) -> void:
	if not stopcock_valve:
		return

	# Rotation angle around Z-axis:
	# CLOSED: 0 deg (handle perpendicular across horizontal barrel)
	# DROPWISE: 45 deg (half-open metering angle)
	# STREAM: 90 deg (fully parallel with vertical buret tube)
	var target_angle_deg: float = 0.0
	match current_valve_state:
		ValveState.CLOSED:
			target_angle_deg = 0.0
		ValveState.DROPWISE:
			target_angle_deg = 45.0
		ValveState.STREAM:
			target_angle_deg = 90.0

	var target_rot = Vector3(0, 0, deg_to_rad(target_angle_deg))

	if animated:
		var tween = create_tween()
		tween.set_trans(Tween.TRANS_BACK)
		tween.set_ease(Tween.EASE_OUT)
		tween.tween_property(stopcock_valve, "rotation", target_rot, 0.22)
	else:
		stopcock_valve.rotation = target_rot


# =============================================================================
# VOLUME DRAINAGE & MENISCUS TRACKING
# =============================================================================
func _update_meniscus_display() -> void:
	var fill_ratio = clampf(current_volume_ml / MAX_CAPACITY_ML, 0.0, 1.0)
	var reading_ml = MAX_CAPACITY_ML - current_volume_ml

	# Update liquid cylinder mesh height and vertical position
	if liquid_column:
		liquid_column.visible = (fill_ratio > 0.001)
		liquid_column.scale = Vector3(
			initial_column_scale.x,
			initial_column_scale.y * fill_ratio,
			initial_column_scale.z
		)
		# Liquid column bottom stays at TUBE_BOTTOM_Y (0.26m)
		var column_height = TUBE_CALIBRATED_HEIGHT * fill_ratio
		liquid_column.position = Vector3(
			0,
			TUBE_BOTTOM_Y + (column_height * 0.5),
			0
		)

	# Update Meniscus marker
	if meniscus_marker:
		meniscus_marker.position = Vector3(
			0,
			TUBE_BOTTOM_Y + (TUBE_CALIBRATED_HEIGHT * fill_ratio),
			0
		)

	# Update 3D Graduation readout label
	if readout_label:
		readout_label.text = "Buret: %5.2f mL\nDelivered: %5.2f mL" % [reading_ml, delivered_volume_ml]


# =============================================================================
# DISPENSING LOGIC & REACTION/TITRATION ENGINE
# =============================================================================
func _dispense_discrete_drop(volume_ml: float) -> void:
	var actual_vol = minf(volume_ml, current_volume_ml)
	if actual_vol <= 0.0:
		return

	current_volume_ml -= actual_vol
	delivered_volume_ml += actual_vol

	if drop_emitter:
		drop_emitter.restart()
		drop_emitter.emitting = true

	if audio_drip:
		audio_drip.play()

	_transfer_titrant_to_vessel(actual_vol)
	_update_meniscus_display()

	var moles = titrant_molarity * (actual_vol / 1000.0)
	drop_dispensed.emit(actual_vol, titrant_reagent, moles)
	volume_changed.emit(current_volume_ml, delivered_volume_ml)


func _dispense_continuous_stream(volume_ml: float) -> void:
	var actual_vol = minf(volume_ml, current_volume_ml)
	if actual_vol <= 0.0:
		return

	current_volume_ml -= actual_vol
	delivered_volume_ml += actual_vol

	stream_accumulator += actual_vol
	if stream_accumulator >= 0.10:
		_transfer_titrant_to_vessel(stream_accumulator)
		var moles = titrant_molarity * (stream_accumulator / 1000.0)
		drop_dispensed.emit(stream_accumulator, titrant_reagent, moles)
		stream_accumulator = 0.0

	_update_meniscus_display()
	volume_changed.emit(current_volume_ml, delivered_volume_ml)


func _transfer_titrant_to_vessel(volume_ml: float) -> void:
	var target_vessel = _find_receiving_vessel()
	if target_vessel == null:
		return

	var moles = titrant_molarity * (volume_ml / 1000.0)

	if target_vessel.has_method("receive_liquid"):
		target_vessel.receive_liquid(
			titrant_reagent,
			volume_ml,
			moles,
			titrant_molarity,
			Color(0.95, 0.98, 1.0, 0.8),
			DEFAULT_TITRANT_PH
		)
	elif target_vessel.has_method("add_reagent"):
		target_vessel.add_reagent(titrant_reagent, moles, volume_ml)
	elif target_vessel.has_method("add_drop"):
		target_vessel.add_drop(titrant_reagent, volume_ml)
	else:
		_apply_direct_reagent_addition(target_vessel, volume_ml, moles)

	_update_titration_endpoint_curve(target_vessel)


func _apply_direct_reagent_addition(vessel: Node, volume_ml: float, moles: float) -> void:
	if "volume_ml" in vessel:
		var current_v = float(vessel.get("volume_ml"))
		vessel.set("volume_ml", current_v + volume_ml)

	if "reagent_moles" in vessel:
		var r_moles = vessel.get("reagent_moles")
		if r_moles is Dictionary:
			r_moles[titrant_reagent] = float(r_moles.get(titrant_reagent, 0.0)) + moles


func _update_titration_endpoint_curve(vessel: Node) -> void:
	# Standard Acid-Base Titration: 25.0 mL 0.1 M HCl titrated with 0.1 M NaOH
	# Initial acid: 25.0 mL * 0.1 M = 0.00250 mol HCl
	# Equivalence Point: Delivered NaOH = 25.0 mL
	var initial_acid_moles: float = 0.00250
	var added_base_moles: float = titrant_molarity * (delivered_volume_ml / 1000.0)
	var total_volume_l: float = (25.0 + delivered_volume_ml) / 1000.0

	var current_ph: float = 1.0
	var net_moles = initial_acid_moles - added_base_moles

	if net_moles > 1.0e-6:
		var conc_h = net_moles / total_volume_l
		current_ph = clampf(-log(conc_h) / log(10.0), 0.5, 7.0)
	elif net_moles < -1.0e-6:
		var excess_oh = absf(net_moles) / total_volume_l
		var poh = -log(excess_oh) / log(10.0)
		current_ph = clampf(14.0 - poh, 7.0, 13.5)
	else:
		current_ph = 7.00

	if "current_ph" in vessel:
		vessel.set("current_ph", current_ph)
	elif "ph" in vessel:
		vessel.set("ph", current_ph)

	# Phenolphthalein color transition: Colorless -> Persistent Brilliant Magenta/Pink
	if current_ph >= ENDPOINT_MIN_PH:
		var pink_intensity = clampf((current_ph - ENDPOINT_MIN_PH) / 1.5, 0.0, 1.0)
		var pink_color = Color(1.0, 0.25, 0.65, 0.85).lerp(Color(0.95, 0.05, 0.55, 0.95), pink_intensity)
		if vessel.has_method("set_liquid_color"):
			vessel.set_liquid_color(pink_color)
		elif "liquid_color" in vessel:
			vessel.set("liquid_color", pink_color)

		if not is_endpoint_announced and current_ph >= ENDPOINT_TARGET_PH:
			is_endpoint_announced = true
			endpoint_reached.emit(vessel, current_ph)

	# QuestManager integration
	if has_node("/root/QuestManager"):
		var qm = get_node("/root/QuestManager")
		qm.set("current_flask_ph", current_ph)
		if current_ph >= ENDPOINT_TARGET_PH:
			if qm.has_method("complete_objective_by_id"):
				qm.complete_objective_by_id("titrate_naoh")
			elif qm.has_method("advance_objective"):
				qm.advance_objective("titrate_naoh", 10.0)
		else:
			if qm.has_method("advance_objective"):
				qm.advance_objective("titrate_naoh", 0.05)


func _find_receiving_vessel() -> Node:
	if placed_receiving_flask != null and is_instance_valid(placed_receiving_flask):
		return placed_receiving_flask

	if drop_target_ray and drop_target_ray.is_colliding():
		var col = drop_target_ray.get_collider()
		if col:
			return _resolve_vessel_root(col)
	return null


func _resolve_vessel_root(node: Node) -> Node:
	var curr = node
	while curr != null:
		if curr == self:
			return null
		var n = curr.name.to_lower()
		if "flask" in n or "beaker" in n or "vessel" in n or curr.is_in_group("glassware") or curr.is_in_group("vessel"):
			return curr
		if curr.has_method("receive_liquid") or curr.has_method("add_reagent"):
			return curr
		curr = curr.get_parent()
	return node


# =============================================================================
# REFILL & APPARATUS RESET
# =============================================================================
func refill(volume_ml: float = MAX_CAPACITY_ML, reagent: String = DEFAULT_TITRANT_ID, molarity: float = DEFAULT_TITRANT_MOLARITY) -> void:
	current_volume_ml = clampf(volume_ml, 0.0, MAX_CAPACITY_ML)
	delivered_volume_ml = 0.00
	titrant_reagent = reagent
	titrant_molarity = molarity
	is_endpoint_announced = false
	_update_meniscus_display()
	volume_changed.emit(current_volume_ml, delivered_volume_ml)


# =============================================================================
# RECEIVING FLASK PLACEMENT ON RETORT STAND BASE
# =============================================================================
func try_place_item(item: Node) -> bool:
	if item == null or placed_receiving_flask != null:
		return false

	var snap_pos = global_position + Vector3(0, 0.025, 0.06)
	if flask_snap_point:
		snap_pos = flask_snap_point.global_position

	if item is Node3D:
		item.global_position = snap_pos
		item.rotation = Vector3.ZERO

	placed_receiving_flask = item
	receiving_flask_placed.emit(item)
	return true


func remove_vessel() -> Node:
	if placed_receiving_flask == null:
		return null
	var removed = placed_receiving_flask
	placed_receiving_flask = null
	receiving_flask_removed.emit(removed)
	return removed


# =============================================================================
# PLAYER INTERACTION PROTOCOL (PlayerController Integration)
# =============================================================================
func get_interaction_info() -> Dictionary:
	var state_str = ""
	match current_valve_state:
		ValveState.CLOSED:
			state_str = "CLOSED [Click/E -> Dropwise]"
		ValveState.DROPWISE:
			state_str = "DROPWISE [Click/E -> Stream]"
		ValveState.STREAM:
			state_str = "STREAM [Click/E -> Closed]"

	var prompt = "Titration Buret (%5.2f mL) | Valve: %s" % [current_volume_ml, state_str]
	if placed_receiving_flask != null:
		prompt += " | [Q] Take Flask"
	else:
		prompt += " | [E with item] Place Flask"

	return {
		"can_pickup": false,
		"can_interact": true,
		"prompt_text": prompt
	}


func interact() -> void:
	cycle_valve_state()
