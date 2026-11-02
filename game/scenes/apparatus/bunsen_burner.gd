# ChemLab 3D Laboratory Simulation (Godot 4 Engine)
# Apparatus: Precision Bunsen Burner with Rotatable Air Collar & Dual-Cone Flame Physics
# Implements realistic thermodynamic convective heat transfer (dT/dt = (Q_flame - Q_loss) / (m * Cp))
# and acoustic boiling / sizzling state triggers.

class_name BunsenBurner
extends StaticBody3D

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

enum FlameState {
	OFF = 0,
	SAFETY_YELLOW = 1,
	HEATING_BLUE = 2
}

const HEAT_CAPACITY_WATER_J_KG_K: float = 4184.0  # J / (kg * K)
const DENSITY_WATER_KG_L: float = 1.0             # kg / L
const HEAT_OF_VAPORIZATION_J_KG: float = 2260000.0 # Latent heat of vaporization (J/kg)

# Standard laboratory flame color temperatures & lighting
const COLOR_SAFETY_FLAME = Color(1.0, 0.68, 0.18, 1.0) # Warm luminous amber/orange (~1000 K visual)
const COLOR_HEATING_FLAME = Color(0.25, 0.65, 1.0, 1.0) # Non-luminous cyan/blue (~1800 K visual)

# =============================================================================
# SIGNALS
# =============================================================================

signal flame_state_changed(new_state: FlameState)
signal collar_adjusted(opening_ratio: float)
signal vessel_entered_heating_zone(vessel: Node)
signal vessel_exited_heating_zone(vessel: Node)
signal vessel_temperature_updated(vessel: Node, temperature_c: float)
signal vessel_boiling_started(vessel: Node, temperature_c: float)
signal gas_valve_toggled(is_open: bool)

# =============================================================================
# EXPORTED PARAMETERS
# =============================================================================

@export_group("State & Controls")
@export var current_state: FlameState = FlameState.OFF
@export var gas_valve_open: bool = true
@export_range(0.0, 1.0, 0.01) var collar_opening: float = 0.0 # 0.0 = Closed (Yellow), 1.0 = Open (Blue)

@export_group("Thermal Properties")
@export var power_safety_yellow_watts: float = 350.0  # ~350 W luminous gentle flame
@export var power_heating_blue_watts: float = 1450.0   # ~1450 W roaring non-luminous high heat
@export var heat_transfer_efficiency: float = 0.68     # Coupling factor from flame cone to vessel base
@export var ambient_temperature_c: float = 21.0       # Ambient room temperature in Celsius
@export var convective_loss_coefficient: float = 1.25  # W / K heat dissipation to room air

@export_group("Audio Feedback")
@export var enable_audio: bool = true
@export var flame_volume_db: float = -6.0
@export var boil_volume_db: float = -3.0

# =============================================================================
# NODE REFERENCES
# =============================================================================

@onready var flame_mesh: MeshInstance3D = get_node_or_null("FlameMesh")
@onready var flame_light: OmniLight3D = get_node_or_null("FlameLight")
@onready var heating_zone: Area3D = get_node_or_null("HeatingZone")
@onready var collar_mesh: MeshInstance3D = get_node_or_null("KnurledCollar")
@onready var audio_flame: AudioStreamPlayer3D = get_node_or_null("FlameAudio")
@onready var audio_boil: AudioStreamPlayer3D = get_node_or_null("BoilAudio")
@onready var audio_sizzle: AudioStreamPlayer3D = get_node_or_null("SizzleAudio")

# Internal tracking of vessels within the cylindrical heating column
var _tracked_vessels: Array[Node] = []
var _vessel_boiling_map: Dictionary = {} # vessel -> bool
var _flame_flicker_noise: float = 0.0
var _flame_shader_material: ShaderMaterial = null

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	add_to_group("interactive_apparatus")
	add_to_group("apparatus")
	add_to_group("interactable")
	set_meta("is_apparatus", true)
	set_meta("apparatus_type", "bunsen_burner")

	_ensure_components()
	_setup_heating_zone_signals()
	_update_visuals_and_lighting()

	# Synchronize state machine with initial parameters
	if gas_valve_open and current_state != FlameState.OFF:
		set_flame_state(current_state)
	else:
		set_flame_state(FlameState.OFF)


func _ensure_components() -> void:
	# Ensure FlameMesh has valid ShaderMaterial
	if flame_mesh and flame_mesh.material_override is ShaderMaterial:
		_flame_shader_material = flame_mesh.material_override as ShaderMaterial
	elif flame_mesh and flame_mesh.get_active_material(0) is ShaderMaterial:
		_flame_shader_material = flame_mesh.get_active_material(0) as ShaderMaterial

	# Setup audio streams if players exist
	_setup_audio_players()


func _setup_audio_players() -> void:
	if not audio_flame:
		audio_flame = AudioStreamPlayer3D.new()
		audio_flame.name = "FlameAudio"
		audio_flame.unit_size = 3.0
		audio_flame.max_distance = 15.0
		audio_flame.volume_db = flame_volume_db
		add_child(audio_flame)

	if not audio_boil:
		audio_boil = AudioStreamPlayer3D.new()
		audio_boil.name = "BoilAudio"
		audio_boil.unit_size = 2.5
		audio_boil.max_distance = 12.0
		audio_boil.volume_db = boil_volume_db
		add_child(audio_boil)

	if not audio_sizzle:
		audio_sizzle = AudioStreamPlayer3D.new()
		audio_sizzle.name = "SizzleAudio"
		audio_sizzle.unit_size = 2.0
		audio_sizzle.max_distance = 10.0
		audio_sizzle.volume_db = -8.0
		add_child(audio_sizzle)

	# Load audio assets
	if ResourceLoader.exists("res://audio/sfx_flame_roaring.wav"):
		audio_flame.stream = load("res://audio/sfx_flame_roaring.wav")
	if ResourceLoader.exists("res://audio/sfx_boiling_bubble.wav"):
		audio_boil.stream = load("res://audio/sfx_boiling_bubble.wav")
	if ResourceLoader.exists("res://audio/sfx_sizzle.wav"):
		audio_sizzle.stream = load("res://audio/sfx_sizzle.wav")


func _setup_heating_zone_signals() -> void:
	if not heating_zone:
		heating_zone = get_node_or_null("HeatingZone")
	if heating_zone:
		if not heating_zone.body_entered.is_connected(_on_heating_zone_body_entered):
			heating_zone.body_entered.connect(_on_heating_zone_body_entered)
		if not heating_zone.body_exited.is_connected(_on_heating_zone_body_exited):
			heating_zone.body_exited.connect(_on_heating_zone_body_exited)
		if not heating_zone.area_entered.is_connected(_on_heating_zone_area_entered):
			heating_zone.area_entered.connect(_on_heating_zone_area_entered)
		if not heating_zone.area_exited.is_connected(_on_heating_zone_area_exited):
			heating_zone.area_exited.connect(_on_heating_zone_area_exited)


func _physics_process(delta: float) -> void:
	# 1. Update lighting flicker
	_process_flame_lighting(delta)

	# 2. Continuous thermodynamic simulation for all vessels in the heating column
	_process_thermal_convection(delta)


# =============================================================================
# THERMODYNAMIC CONVECTIVE HEATING SIMULATION
# Equation: dT/dt = (Q_flame - Q_loss) / (m * Cp)
# =============================================================================

func _process_thermal_convection(delta: float) -> void:
	# Determine effective flame power output
	var q_flame_gross: float = 0.0
	match current_state:
		FlameState.OFF:
			q_flame_gross = 0.0
		FlameState.SAFETY_YELLOW:
			q_flame_gross = power_safety_yellow_watts
		FlameState.HEATING_BLUE:
			q_flame_gross = power_heating_blue_watts

	var q_flame_net: float = q_flame_gross * heat_transfer_efficiency
	var any_vessel_boiling: bool = false

	# Iterate over all vessels positioned above the flame
	for i in range(_tracked_vessels.size() - 1, -1, -1):
		var vessel = _tracked_vessels[i]
		if not is_instance_valid(vessel):
			_tracked_vessels.remove_at(i)
			continue

		var vessel_data = _extract_vessel_state(vessel)
		var current_temp: float = vessel_data["temp"]
		var volume_ml: float = vessel_data["volume"]
		var boiling_point: float = vessel_data["boiling_point"]

		# Mass in kg (water equivalent or density adjusted)
		var mass_kg: float = maxf(0.015, (volume_ml / 1000.0) * DENSITY_WATER_KG_L)
		var cp: float = HEAT_CAPACITY_WATER_J_KG_K

		# Heat loss to ambient air: Q_loss = h * A * (T - T_amb)
		var delta_t_ambient = current_temp - ambient_temperature_c
		var q_loss: float = maxf(0.0, convective_loss_coefficient * delta_t_ambient)

		var new_temp: float = current_temp

		if current_state != FlameState.OFF and volume_ml > 0.5:
			# Heating phase: dT = ((Q_in - Q_loss) / (m * Cp)) * dt
			var net_heat_rate_watts: float = q_flame_net - q_loss
			var dt_rate = net_heat_rate_watts / (mass_kg * cp)
			new_temp += dt_rate * delta

			# Boiling threshold transition
			if new_temp >= boiling_point:
				new_temp = boiling_point # Latent heat buffer
				any_vessel_boiling = true

				if not _vessel_boiling_map.get(vessel, false):
					_vessel_boiling_map[vessel] = true
					vessel_boiling_started.emit(vessel, new_temp)
					_trigger_boiling_audio(true)
			else:
				if _vessel_boiling_map.get(vessel, false):
					_vessel_boiling_map[vessel] = false

		else:
			# Cooling phase towards ambient temperature
			if current_temp > ambient_temperature_c:
				var cool_rate = (q_loss / (mass_kg * cp))
				new_temp = maxf(ambient_temperature_c, current_temp - cool_rate * delta)

			if _vessel_boiling_map.get(vessel, false):
				_vessel_boiling_map[vessel] = false

		# Write back updated temperature to vessel
		_apply_vessel_temperature(vessel, new_temp, delta)
		vessel_temperature_updated.emit(vessel, new_temp)

	# Manage boiling acoustic feedback
	if any_vessel_boiling:
		_maintain_boiling_audio()
	else:
		_fade_boiling_audio(delta)


func _get_simulation_bridge() -> Node:
	if is_inside_tree() and get_tree() and get_tree().root and get_tree().root.has_node("SimulationBridge"):
		return get_tree().root.get_node("SimulationBridge")
	return null


func _extract_vessel_state(vessel: Node) -> Dictionary:
	var temp: float = ambient_temperature_c
	var vol: float = 100.0
	var bp: float = 100.0

	# 1. Direct property inspection
	if "temperature_c" in vessel:
		temp = float(vessel.temperature_c)
	elif "temperature" in vessel:
		temp = float(vessel.temperature)

	if "volume_ml" in vessel:
		vol = float(vessel.volume_ml)
	elif "current_volume_ml" in vessel:
		vol = float(vessel.current_volume_ml)
	elif "liquid_volume" in vessel:
		vol = float(vessel.liquid_volume)

	if "boiling_point_c" in vessel:
		bp = float(vessel.boiling_point_c)
	elif "boiling_point" in vessel:
		bp = float(vessel.boiling_point)

	# 2. Check SimulationBridge registry if vessel has ID
	var bridge = _get_simulation_bridge()
	if bridge and "active_vessels" in bridge:
		var v_id = str(vessel.get("vessel_id") if "vessel_id" in vessel else vessel.name)
		if bridge.active_vessels.has(v_id):
			var reg_data = bridge.active_vessels[v_id]
			if reg_data.has("temperature_c"):
				temp = float(reg_data["temperature_c"])
			if reg_data.has("volume_ml"):
				vol = float(reg_data["volume_ml"])

	return {"temp": temp, "volume": vol, "boiling_point": bp}


func _apply_vessel_temperature(vessel: Node, new_temp: float, delta: float) -> void:
	if "temperature_c" in vessel:
		vessel.temperature_c = new_temp
	elif "temperature" in vessel:
		vessel.temperature = new_temp

	if vessel.has_method("apply_heat"):
		var watts = (power_heating_blue_watts if current_state == FlameState.HEATING_BLUE else power_safety_yellow_watts) * heat_transfer_efficiency
		vessel.call("apply_heat", watts, delta)

	# Update SimulationBridge if registered
	var bridge = _get_simulation_bridge()
	if bridge and "active_vessels" in bridge:
		var v_id = str(vessel.get("vessel_id") if "vessel_id" in vessel else vessel.name)
		if bridge.active_vessels.has(v_id):
			bridge.active_vessels[v_id]["temperature_c"] = new_temp


# =============================================================================
# STATE MACHINE & INTERACTIVE CONTROLS
# =============================================================================

func toggle_flame() -> void:
	if not gas_valve_open:
		extinguish()
		return

	if current_state == FlameState.OFF:
		# Ignites according to current collar setting
		if collar_opening < 0.25:
			set_flame_state(FlameState.SAFETY_YELLOW)
		else:
			set_flame_state(FlameState.HEATING_BLUE)
	else:
		extinguish()


func ignite() -> void:
	if not gas_valve_open:
		return
	if collar_opening < 0.25:
		set_flame_state(FlameState.SAFETY_YELLOW)
	else:
		set_flame_state(FlameState.HEATING_BLUE)


func extinguish() -> void:
	set_flame_state(FlameState.OFF)


func set_gas_valve(open: bool) -> void:
	gas_valve_open = open
	gas_valve_toggled.emit(open)
	if not open and current_state != FlameState.OFF:
		extinguish()


func adjust_collar(delta_val: float) -> void:
	set_collar_opening(collar_opening + delta_val)


func set_collar_opening(opening: float) -> void:
	collar_opening = clampf(opening, 0.0, 1.0)
	collar_adjusted.emit(collar_opening)

	# Visually rotate knurled collar around Y axis
	if collar_mesh:
		collar_mesh.rotation.y = collar_opening * (PI * 0.5)

	# Auto-transition flame state based on air intake if burner is lit
	if current_state != FlameState.OFF:
		if collar_opening >= 0.25 and current_state != FlameState.HEATING_BLUE:
			set_flame_state(FlameState.HEATING_BLUE)
		elif collar_opening < 0.25 and current_state != FlameState.SAFETY_YELLOW:
			set_flame_state(FlameState.SAFETY_YELLOW)


func set_flame_state(new_state: FlameState) -> void:
	current_state = new_state
	_update_visuals_and_lighting()
	_update_flame_audio()
	flame_state_changed.emit(new_state)


# =============================================================================
# VISUALS, SHADER & LIGHTING UPDATES
# =============================================================================

func _update_visuals_and_lighting() -> void:
	# 1. Update Flame Shader
	if _flame_shader_material:
		_flame_shader_material.set_shader_parameter("flame_state", int(current_state))
		match current_state:
			FlameState.OFF:
				_flame_shader_material.set_shader_parameter("flame_intensity", 0.0)
			FlameState.SAFETY_YELLOW:
				_flame_shader_material.set_shader_parameter("flame_intensity", 1.0)
				_flame_shader_material.set_shader_parameter("flame_height_scale", 1.25)
			FlameState.HEATING_BLUE:
				_flame_shader_material.set_shader_parameter("flame_intensity", 1.4)
				_flame_shader_material.set_shader_parameter("flame_height_scale", 1.0)

	if flame_mesh:
		flame_mesh.visible = (current_state != FlameState.OFF)

	# 2. Update OmniLight3D
	if flame_light:
		match current_state:
			FlameState.OFF:
				flame_light.visible = false
				flame_light.light_energy = 0.0
			FlameState.SAFETY_YELLOW:
				flame_light.visible = true
				flame_light.light_color = COLOR_SAFETY_FLAME
				flame_light.light_energy = 0.95
				flame_light.omni_range = 1.2
			FlameState.HEATING_BLUE:
				flame_light.visible = true
				flame_light.light_color = COLOR_HEATING_FLAME
				flame_light.light_energy = 1.6
				flame_light.omni_range = 1.6


func _process_flame_lighting(delta: float) -> void:
	if not flame_light or current_state == FlameState.OFF:
		return

	# High-frequency organic flame flicker
	_flame_flicker_noise += delta * 15.0
	var flicker = sin(_flame_flicker_noise) * 0.12 + cos(_flame_flicker_noise * 1.7) * 0.08
	var base_energy = 0.95 if current_state == FlameState.SAFETY_YELLOW else 1.6
	flame_light.light_energy = maxf(0.1, base_energy + flicker)


# =============================================================================
# AUDIO SUBSYSTEM
# =============================================================================

func _update_flame_audio() -> void:
	if not enable_audio or not audio_flame:
		return

	match current_state:
		FlameState.OFF:
			if audio_flame.playing:
				audio_flame.stop()
		FlameState.SAFETY_YELLOW:
			audio_flame.pitch_scale = 0.75
			audio_flame.volume_db = flame_volume_db - 4.0
			if not audio_flame.playing:
				audio_flame.play()
		FlameState.HEATING_BLUE:
			audio_flame.pitch_scale = 1.15
			audio_flame.volume_db = flame_volume_db
			if not audio_flame.playing:
				audio_flame.play()


func _trigger_boiling_audio(immediate: bool = false) -> void:
	if not enable_audio:
		return
	if audio_boil and not audio_boil.playing:
		audio_boil.volume_db = boil_volume_db
		audio_boil.play()
	if audio_sizzle and not audio_sizzle.playing:
		audio_sizzle.play()


func _maintain_boiling_audio() -> void:
	if not enable_audio:
		return
	if audio_boil and not audio_boil.playing:
		audio_boil.play()
	if audio_sizzle and not audio_sizzle.playing:
		audio_sizzle.play()


func _fade_boiling_audio(delta: float) -> void:
	if audio_boil and audio_boil.playing:
		audio_boil.volume_db = lerpf(audio_boil.volume_db, -40.0, delta * 3.0)
		if audio_boil.volume_db <= -35.0:
			audio_boil.stop()
			audio_boil.volume_db = boil_volume_db

	if audio_sizzle and audio_sizzle.playing:
		audio_sizzle.volume_db = lerpf(audio_sizzle.volume_db, -40.0, delta * 4.0)
		if audio_sizzle.volume_db <= -35.0:
			audio_sizzle.stop()
			audio_sizzle.volume_db = -8.0


# =============================================================================
# HEATING ZONE PROXIMITY TRIGGERS
# =============================================================================

func _on_heating_zone_body_entered(body: Node) -> void:
	var vessel = _resolve_vessel_node(body)
	if vessel and not _tracked_vessels.has(vessel):
		_tracked_vessels.append(vessel)
		vessel_entered_heating_zone.emit(vessel)


func _on_heating_zone_body_exited(body: Node) -> void:
	var vessel = _resolve_vessel_node(body)
	if vessel and _tracked_vessels.has(vessel):
		_tracked_vessels.erase(vessel)
		_vessel_boiling_map.erase(vessel)
		vessel_exited_heating_zone.emit(vessel)


func _on_heating_zone_area_entered(area: Area3D) -> void:
	var vessel = _resolve_vessel_node(area)
	if vessel and not _tracked_vessels.has(vessel):
		_tracked_vessels.append(vessel)
		vessel_entered_heating_zone.emit(vessel)


func _on_heating_zone_area_exited(area: Area3D) -> void:
	var vessel = _resolve_vessel_node(area)
	if vessel and _tracked_vessels.has(vessel):
		_tracked_vessels.erase(vessel)
		_vessel_boiling_map.erase(vessel)
		vessel_exited_heating_zone.emit(vessel)


func _resolve_vessel_node(node: Node) -> Node:
	var curr: Node = node
	while curr != null:
		if curr.is_in_group("vessel") or curr.is_in_group("glassware") or curr.has_meta("is_vessel") or "temperature_c" in curr or "volume_ml" in curr:
			return curr
		curr = curr.get_parent()
	return node


# =============================================================================
# PLAYER INTERACTION HANDLING
# =============================================================================

func _input_event(_camera: Camera3D, event: InputEvent, _click_position: Vector3, _click_normal: Vector3, _shape_idx: int) -> void:
	if event is InputEventMouseButton and event.pressed:
		var mb = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			# Left click toggles flame
			toggle_flame()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			# Wheel adjusts collar open (towards Blue)
			adjust_collar(0.1)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			# Wheel adjusts collar closed (towards Yellow)
			adjust_collar(-0.1)
