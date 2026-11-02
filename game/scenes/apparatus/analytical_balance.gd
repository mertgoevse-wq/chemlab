# Analytical Balance (Godot 4 Engine)
# Precision 4-decimal-place laboratory analytical balance (0.0001 g resolution)
# Features:
# 1. Cast aluminum chassis with stainless steel weighing pan
# 2. 3-sided sliding glass draft shields (Left, Right, Top)
# 3. Dynamic air draft turbulence simulation (+/- 0.0003 g when doors are open)
# 4. Stoichiometric mass computation: m = sum(n_i * M_w,i) + V * rho
# 5. Electronic Tare functionality with VFD green/cyan fluorescent vacuum display
# 6. Automatic QuestManager and PlayerController integration

extends StaticBody3D
class_name AnalyticalBalance

# =============================================================================
# SIGNALS
# =============================================================================
signal mass_changed(raw_mass: float, net_mass: float, displayed_mass: float)
signal tared(offset_mass: float)
signal door_state_changed(door_name: String, is_open: bool)
signal stability_changed(is_stable: bool)
signal vessel_placed(vessel: Node)
signal vessel_removed(vessel: Node)

# =============================================================================
# CONSTANTS & REAGENT DATABASE
# =============================================================================
const GROUP_INTERACTIVE_APPARATUS: String = "interactive_apparatus"

# Molecular weights (M_w in g/mol) and densities (rho in g/mL)
const REAGENT_PROPERTIES: Dictionary = {
	"water": {"mw": 18.015, "density": 1.000},
	"h2o": {"mw": 18.015, "density": 1.000},
	"distilled_water": {"mw": 18.015, "density": 1.000},
	"hcl": {"mw": 36.460, "density": 1.020},
	"hcl_0.1m": {"mw": 36.460, "density": 1.020},
	"naoh": {"mw": 39.997, "density": 1.040},
	"naoh_0.1m": {"mw": 39.997, "density": 1.040},
	"phenolphthalein": {"mw": 318.32, "density": 1.277},
	"phenolphthalein_indicator": {"mw": 318.32, "density": 1.277},
	"universal_indicator": {"mw": 100.0, "density": 1.000},
	"hydrogen_peroxide": {"mw": 34.014, "density": 1.110},
	"h2o2": {"mw": 34.014, "density": 1.110},
	"potassium_iodide": {"mw": 166.00, "density": 1.120},
	"ki": {"mw": 166.00, "density": 1.120},
	"malonic_acid": {"mw": 104.06, "density": 1.620},
	"potassium_iodate": {"mw": 214.00, "density": 3.890},
	"kio3": {"mw": 214.00, "density": 3.890},
	"dish_soap": {"mw": 250.00, "density": 1.030},
	"nacl": {"mw": 58.44, "density": 2.160},
	"sodium_chloride": {"mw": 58.44, "density": 2.160}
}

const DEFAULT_MW: float = 50.0
const DEFAULT_DENSITY: float = 1.0
const DRAFT_FLUCTUATION_AMPLITUDE: float = 0.0003  # +/- 0.0003 g air draft disturbance
const DOOR_SLIDE_DISTANCE: float = 0.14          # meters to slide when opened
const DOOR_SLIDE_DURATION: float = 0.35          # seconds for door animation

# =============================================================================
# NODE REFERENCES
# =============================================================================
@onready var weighing_pan_area: Area3D = $WeighingPanArea
@onready var digital_display: Label3D = $DigitalDisplay
@onready var tare_button: MeshInstance3D = $TareButton
@onready var weighing_pan: MeshInstance3D = $WeighingPan

# 3 Draft Shield Doors
@onready var door_left: Node3D = $DraftShield/DoorLeft
@onready var door_right: Node3D = $DraftShield/DoorRight
@onready var door_top: Node3D = $DraftShield/DoorTop

# Audio players
@onready var audio_beep: AudioStreamPlayer3D = get_node_or_null("AudioBeep")
@onready var audio_door: AudioStreamPlayer3D = get_node_or_null("AudioDoor")

# =============================================================================
# STATE VARIABLES
# =============================================================================
@export var tare_offset_g: float = 0.0
@export var current_vessel: Node = null

# Door positions and open/closed states
var is_door_left_open: bool = false
var is_door_right_open: bool = false
var is_door_top_open: bool = false

var door_left_closed_pos: Vector3 = Vector3.ZERO
var door_right_closed_pos: Vector3 = Vector3.ZERO
var door_top_closed_pos: Vector3 = Vector3.ZERO

# Masses
var raw_mass_g: float = 0.0
var net_mass_g: float = 0.0
var displayed_mass_g: float = 0.0

# Draft fluctuation
var draft_noise_time: float = 0.0
var current_draft_offset_g: float = 0.0
var is_reading_stable: bool = true

# =============================================================================
# LIFECYCLE
# =============================================================================
func _ready() -> void:
	add_to_group(GROUP_INTERACTIVE_APPARATUS)

	# Store initial closed door positions
	if door_left:
		door_left_closed_pos = door_left.position
	if door_right:
		door_right_closed_pos = door_right.position
	if door_top:
		door_top_closed_pos = door_top.position

	# Connect WeighingPanArea signals
	if weighing_pan_area:
		weighing_pan_area.body_entered.connect(_on_weighing_pan_area_body_entered)
		weighing_pan_area.body_exited.connect(_on_weighing_pan_area_body_exited)
		weighing_pan_area.area_entered.connect(_on_weighing_pan_area_entered)
		weighing_pan_area.area_exited.connect(_on_weighing_pan_area_exited)

	# Initial tare and display refresh
	_update_mass_reading(0.0)
	_update_display()


func _physics_process(delta: float) -> void:
	draft_noise_time += delta
	_update_mass_reading(delta)
	_update_display()


# =============================================================================
# WEIGHING CALCULATION LOGIC
# =============================================================================
# Measures tare mass of empty vessel + mass of all dissolved/liquid contents:
# m = sum(n_i * M_w,i) + V * rho
func calculate_vessel_mass(vessel: Node) -> float:
	if vessel == null or not is_instance_valid(vessel):
		return 0.0

	# 1. Direct mass method if implemented
	if vessel.has_method("get_total_mass"):
		return float(vessel.get_total_mass())

	# 2. Direct property if implemented
	if "total_mass_g" in vessel:
		return float(vessel.get("total_mass_g"))
	if "mass_g" in vessel:
		return float(vessel.get("mass_g"))

	# 3. Stoichiometric computation: m = dry_mass + dissolved_solutes + solvent
	var dry_mass: float = 0.0
	if "empty_mass_g" in vessel:
		dry_mass = float(vessel.get("empty_mass_g"))
	elif "tare_mass" in vessel:
		dry_mass = float(vessel.get("tare_mass"))
	elif "dry_mass_g" in vessel:
		dry_mass = float(vessel.get("dry_mass_g"))
	else:
		# Sensible default based on vessel name
		var v_name = vessel.name.to_lower()
		if "flask" in v_name or "erlenmeyer" in v_name:
			dry_mass = 125.0000  # Standard 250 mL Pyrex Erlenmeyer
		elif "beaker" in v_name:
			dry_mass = 105.0000  # Standard 250 mL Pyrex Beaker
		elif "tube" in v_name:
			dry_mass = 18.5000   # Test tube
		else:
			dry_mass = 50.0000   # Generic glassware

	var contents_mass: float = 0.0

	# Check for LiquidMixture or liquid contents dictionary
	var mixture = null
	if "liquid_mixture" in vessel and vessel.get("liquid_mixture") != null:
		mixture = vessel.get("liquid_mixture")
	elif "contents" in vessel and vessel.get("contents") != null:
		mixture = vessel.get("contents")

	if mixture != null:
		contents_mass = _calculate_mixture_mass(mixture)
	else:
		# Check for direct volume and reagents properties
		var volume_ml: float = 0.0
		if "volume_ml" in vessel:
			volume_ml = float(vessel.get("volume_ml"))
		elif "current_volume_ml" in vessel:
			volume_ml = float(vessel.get("current_volume_ml"))

		var reagent_dict: Dictionary = {}
		if "reagent_moles" in vessel:
			reagent_dict = vessel.get("reagent_moles")
		elif "reagents" in vessel:
			var r = vessel.get("reagents")
			if r is Dictionary:
				reagent_dict = r

		contents_mass = _calculate_stoichiometric_mass(volume_ml, reagent_dict)

	return dry_mass + contents_mass


func _calculate_mixture_mass(mixture) -> float:
	var vol_ml: float = 0.0
	var moles_dict: Dictionary = {}

	if mixture is Dictionary:
		if mixture.has("volume_ml") and mixture.has("reagent_moles"):
			vol_ml = float(mixture.get("volume_ml", 0.0))
			moles_dict = mixture.get("reagent_moles", {})
		else:
			# Format as used by ErlenmeyerFlask: { species_id: {"moles": float, "volume_ml": float, ...} }
			for key in mixture.keys():
				var item = mixture[key]
				if item is Dictionary:
					vol_ml += float(item.get("volume_ml", 0.0))
					moles_dict[key] = float(item.get("moles", 0.0))
				elif item is float or item is int:
					moles_dict[key] = float(item)
	else:
		if "volume_ml" in mixture:
			vol_ml = float(mixture.get("volume_ml"))
		if "reagent_moles" in mixture:
			moles_dict = mixture.get("reagent_moles")

	return _calculate_stoichiometric_mass(vol_ml, moles_dict)


func _calculate_stoichiometric_mass(volume_ml: float, reagent_moles: Dictionary) -> float:
	# 1. Dissolved solutes mass: sum(n_i * M_w,i)
	var solutes_mass_g: float = 0.0
	for reagent_id in reagent_moles.keys():
		var moles = float(reagent_moles[reagent_id])
		var id_clean = str(reagent_id).to_lower().strip_edges()
		var mw = DEFAULT_MW
		if REAGENT_PROPERTIES.has(id_clean):
			mw = float(REAGENT_PROPERTIES[id_clean]["mw"])
		solutes_mass_g += moles * mw

	# 2. Solvent volume mass: V * rho
	var solvent_density: float = DEFAULT_DENSITY
	var solvent_mass_g: float = volume_ml * solvent_density

	return solutes_mass_g + solvent_mass_g


func _update_mass_reading(delta: float) -> void:
	raw_mass_g = calculate_vessel_mass(current_vessel)
	net_mass_g = raw_mass_g - tare_offset_g

	# Draft shield logic:
	# Opening glass doors introduces air draft fluctuations (+/- 0.0003 g)
	# Closing all doors stabilizes the reading!
	var any_door_open = is_any_door_open()

	if any_door_open:
		is_reading_stable = false
		# Multi-frequency turbulent sinusoidal draft flutter (+/- 0.0003 g)
		var flutter = (
			sin(draft_noise_time * 3.8) * 0.00015
			+ cos(draft_noise_time * 7.4) * 0.00010
			+ sin(draft_noise_time * 13.1) * 0.00005
		)
		current_draft_offset_g = lerpf(current_draft_offset_g, flutter, clampf(delta * 8.0, 0.0, 1.0))
	else:
		# Rapidly settle when sealed
		current_draft_offset_g = lerpf(current_draft_offset_g, 0.0, clampf(delta * 12.0, 0.0, 1.0))
		if absf(current_draft_offset_g) < 0.00002:
			current_draft_offset_g = 0.0
			is_reading_stable = true

	displayed_mass_g = net_mass_g + current_draft_offset_g

	mass_changed.emit(raw_mass_g, net_mass_g, displayed_mass_g)
	stability_changed.emit(is_reading_stable)


func _update_display() -> void:
	if not digital_display:
		return

	# Format display string with high precision: e.g. "   0.0000 g" or " 125.4312 g"
	var sign_str = ""
	var abs_mass = absf(displayed_mass_g)
	if displayed_mass_g < -0.00005:
		sign_str = "-"
	elif displayed_mass_g > 0.00005:
		sign_str = " "
	else:
		sign_str = " "
		abs_mass = 0.0

	# Stability indicator badge: [S] or space
	var stab_char = "*" if is_reading_stable else "~"

	digital_display.text = "%s%s%8.4f g" % [stab_char, sign_str, abs_mass]

	# VFD Fluorescent Vacuum Display Colors:
	# Stable: Pristine bright Cyan/Mint (Color(0.05, 1.0, 0.85))
	# Unstable: Slightly flickering lighter Cyan (Color(0.2, 0.9, 0.95))
	if is_reading_stable:
		digital_display.modulate = Color(0.08, 1.0, 0.82, 1.0)
	else:
		var flick = 0.92 + 0.08 * sin(draft_noise_time * 24.0)
		digital_display.modulate = Color(0.15 * flick, 0.88 * flick, 0.98 * flick, 1.0)


# =============================================================================
# TARE FUNCTIONALITY
# =============================================================================
# Stores offset mass and resets display to 0.0000 g
func tare() -> void:
	tare_offset_g = raw_mass_g
	_update_mass_reading(0.0)
	_update_display()

	if audio_beep:
		audio_beep.play()

	tared.emit(tare_offset_g)

	# QuestManager integration check
	if has_node("/root/QuestManager"):
		var qm = get_node("/root/QuestManager")
		qm.set("balance_tared", true)
		if qm.has_method("complete_objective_by_id"):
			qm.complete_objective_by_id("place_flask_tare")
		elif qm.has_method("advance_objective"):
			qm.advance_objective("place_flask_tare", 1.0)


# =============================================================================
# DRAFT SHIELD DOOR CONTROLS
# =============================================================================
func is_any_door_open() -> bool:
	return is_door_left_open or is_door_right_open or is_door_top_open


func are_all_doors_closed() -> bool:
	return not is_any_door_open()


func toggle_door(door_name: String) -> void:
	match door_name.to_lower():
		"left":
			set_door_state("left", not is_door_left_open)
		"right":
			set_door_state("right", not is_door_right_open)
		"top":
			set_door_state("top", not is_door_top_open)
		_:
			# Default toggle all doors or toggle first open/closed
			if is_any_door_open():
				close_all_doors()
			else:
				open_all_doors()


func open_door(door_name: String) -> void:
	set_door_state(door_name, true)


func close_door(door_name: String) -> void:
	set_door_state(door_name, false)


func set_door_state(door_name: String, open: bool) -> void:
	match door_name.to_lower():
		"left":
			if is_door_left_open == open:
				return
			is_door_left_open = open
			_animate_door(door_left, door_left_closed_pos, Vector3(0, 0, -DOOR_SLIDE_DISTANCE), open)
			door_state_changed.emit("left", open)
		"right":
			if is_door_right_open == open:
				return
			is_door_right_open = open
			_animate_door(door_right, door_right_closed_pos, Vector3(0, 0, -DOOR_SLIDE_DISTANCE), open)
			door_state_changed.emit("right", open)
		"top":
			if is_door_top_open == open:
				return
			is_door_top_open = open
			_animate_door(door_top, door_top_closed_pos, Vector3(0, 0, -DOOR_SLIDE_DISTANCE), open)
			door_state_changed.emit("top", open)

	if audio_door:
		audio_door.play()


func open_all_doors() -> void:
	open_door("left")
	open_door("right")
	open_door("top")


func close_all_doors() -> void:
	close_door("left")
	close_door("right")
	close_door("top")


func _animate_door(door_node: Node3D, closed_pos: Vector3, slide_delta: Vector3, open: bool) -> void:
	if not door_node:
		return
	var target_pos = closed_pos + (slide_delta if open else Vector3.ZERO)
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(door_node, "position", target_pos, DOOR_SLIDE_DURATION)


# =============================================================================
# VESSEL PLACEMENT & AREA DETECTION
# =============================================================================
func try_place_item(item: Node) -> bool:
	if item == null or current_vessel != null:
		return false

	# Position item gently on top of the stainless steel weighing pan
	var pan_pos = global_position + Vector3(0, 0.068, 0.02)
	if weighing_pan:
		pan_pos = weighing_pan.global_position + Vector3(0, 0.005, 0)

	if item is Node3D:
		item.global_position = pan_pos
		item.rotation = Vector3.ZERO

	current_vessel = item
	vessel_placed.emit(item)
	_update_mass_reading(0.0)
	_update_display()
	return true


func remove_vessel() -> Node:
	if current_vessel == null:
		return null
	var removed = current_vessel
	current_vessel = null
	vessel_removed.emit(removed)
	_update_mass_reading(0.0)
	_update_display()
	return removed


func _on_weighing_pan_area_body_entered(body: Node3D) -> void:
	if body == self or body.is_ancestor_of(self):
		return
	if current_vessel == null and _is_valid_vessel(body):
		current_vessel = body
		vessel_placed.emit(body)
		_update_mass_reading(0.0)
		_update_display()


func _on_weighing_pan_area_body_exited(body: Node3D) -> void:
	if current_vessel == body:
		current_vessel = null
		vessel_removed.emit(body)
		_update_mass_reading(0.0)
		_update_display()


func _on_weighing_pan_area_entered(area: Area3D) -> void:
	var parent_vessel = area.get_parent()
	if parent_vessel and parent_vessel != self and current_vessel == null and _is_valid_vessel(parent_vessel):
		current_vessel = parent_vessel
		vessel_placed.emit(parent_vessel)
		_update_mass_reading(0.0)
		_update_display()


func _on_weighing_pan_area_exited(area: Area3D) -> void:
	var parent_vessel = area.get_parent()
	if current_vessel == parent_vessel:
		current_vessel = null
		vessel_removed.emit(parent_vessel)
		_update_mass_reading(0.0)
		_update_display()


func _is_valid_vessel(node: Node) -> bool:
	if not node:
		return false
	var n = node.name.to_lower()
	return "flask" in n or "beaker" in n or "tube" in n or "vessel" in n or node.is_in_group("glassware") or node.is_in_group("vessel") or node.has_method("get_total_mass")


# =============================================================================
# PLAYER INTERACTION PROTOCOL (PlayerController Integration)
# =============================================================================
func get_interaction_info() -> Dictionary:
	var prompt = ""
	if current_vessel != null:
		prompt = "[E] Tare Balance | [T] Toggle Doors | [Q] Take %s" % current_vessel.name
	else:
		if is_any_door_open():
			prompt = "[E] Tare Balance | [T] Close Draft Shield | Place Vessel"
		else:
			prompt = "[E] Tare Balance | [T] Open Draft Shield | Place Vessel"

	return {
		"can_pickup": false,
		"can_interact": true,
		"prompt_text": prompt
	}


func interact() -> void:
	# Primary interaction: Tare the balance!
	tare()
