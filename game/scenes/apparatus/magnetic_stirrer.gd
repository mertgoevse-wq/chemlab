# ChemLab 3D Laboratory Simulation (Godot 4 Engine)
# Apparatus: Digital Magnetic Stirrer & Hotplate
# Features:
# 1. Closed-loop PID temperature regulation (0 to 350 °C) with ceramic plate thermal inertia.
# 2. Variable speed magnetic drive (0 to 1500 RPM) with fluid vortex generation.
# 3. Noyes-Whitney dissolution & reaction mixing kinetics acceleration (dC/dt = (D*A/h)*(Cs - C)).
# 4. Dual 7-segment digital displays for Temperature and RPM readouts.
# 5. Interactive rotary dials with Left Click drag & Mouse Wheel bindings.

class_name MagneticStirrer
extends StaticBody3D

# =============================================================================
# SIGNALS
# =============================================================================

signal power_toggled(is_powered: bool)
signal target_temperature_changed(temp_c: float)
signal target_rpm_changed(rpm: float)
signal plate_temperature_updated(temp_c: float)
signal actual_rpm_updated(rpm: float)
signal vessel_placed_on_plate(vessel: Node)
signal vessel_removed_from_plate(vessel: Node)
signal vessel_boiling_started(vessel: Node, temp_c: float)

# =============================================================================
# EXPORTED PARAMETERS
# =============================================================================

@export_group("Power & Operational Limits")
@export var is_powered_on: bool = true
@export_range(0.0, 350.0, 1.0) var target_temp_c: float = 0.0
@export_range(0.0, 1500.0, 10.0) var target_rpm: float = 0.0

@export_group("PID Temperature Controller Tuning")
@export var pid_kp: float = 14.5   # Proportional gain
@export var pid_ki: float = 0.065  # Integral gain
@export var pid_kd: float = 3.2    # Derivative gain
@export var max_heater_power_watts: float = 750.0 # Maximum electric heating mantle power

@export_group("Thermal & Physical Constants")
@export var ambient_temperature_c: float = 21.0
@export var plate_heat_capacity_j_k: float = 765.0 # Ceramic top plate thermal mass (~0.85 kg * 900 J/kg*K)
@export var plate_ambient_loss_coefficient: float = 1.65 # W / K convective/radiative heat dissipation
@export var thermal_contact_conductance: float = 12.5 # W / K conduction from ceramic plate to flat glassware base
@export var motor_acceleration_time_s: float = 0.75   # Brushless DC motor inertia response time

@export_group("Acoustic Audio Feedback")
@export var enable_audio: bool = true
@export var motor_base_volume_db: float = -12.0
@export var boil_volume_db: float = -4.0

# =============================================================================
# NODE REFERENCES
# =============================================================================

@onready var temp_display: Label3D = get_node_or_null("TempDisplay")
@onready var rpm_display: Label3D = get_node_or_null("RpmDisplay")
@onready var heating_zone: Area3D = get_node_or_null("TopPlateHeatingZone")
@onready var stir_bar: MeshInstance3D = get_node_or_null("StirBar")
@onready var heat_knob: MeshInstance3D = get_node_or_null("HeatKnob")
@onready var stir_knob: MeshInstance3D = get_node_or_null("StirKnob")
@onready var power_switch: MeshInstance3D = get_node_or_null("PowerSwitch")
@onready var ceramic_plate_mesh: MeshInstance3D = get_node_or_null("CeramicPlate")

@onready var audio_motor: AudioStreamPlayer3D = get_node_or_null("MotorAudio")
@onready var audio_boil: AudioStreamPlayer3D = get_node_or_null("BoilAudio")
@onready var audio_sizzle: AudioStreamPlayer3D = get_node_or_null("SizzleAudio")

# =============================================================================
# RUNTIME SIMULATION STATE
# =============================================================================

var current_plate_temp_c: float = 21.0
var current_rpm: float = 0.0
var stir_bar_angle_rad: float = 0.0

# PID Controller state variables
var _pid_integral: float = 0.0
var _pid_prev_error: float = 0.0
var _heater_duty_cycle: float = 0.0 # 0.0 to 1.0

# Vessel tracking on top ceramic plate
var _tracked_vessels: Array[Node] = []
var _vessel_boiling_map: Dictionary = {}

# Interaction dragging tracking
enum DraggedKnob { NONE, HEAT, STIR }
var _active_drag_knob: DraggedKnob = DraggedKnob.NONE
var _last_drag_mouse_pos: Vector2 = Vector2.ZERO

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	add_to_group("interactive_apparatus")
	add_to_group("apparatus")
	add_to_group("interactable")
	set_meta("is_apparatus", true)
	set_meta("apparatus_type", "magnetic_stirrer")

	current_plate_temp_c = ambient_temperature_c
	_setup_audio_players()
	_setup_heating_zone()
	_update_knob_rotations()
	_update_displays()


func _setup_audio_players() -> void:
	if not audio_motor:
		audio_motor = AudioStreamPlayer3D.new()
		audio_motor.name = "MotorAudio"
		audio_motor.unit_size = 2.0
		audio_motor.max_distance = 10.0
		audio_motor.volume_db = -30.0
		add_child(audio_motor)

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

	if ResourceLoader.exists("res://audio/sfx_flame_roaring.wav"):
		audio_motor.stream = load("res://audio/sfx_flame_roaring.wav")
	if ResourceLoader.exists("res://audio/sfx_boiling_bubble.wav"):
		audio_boil.stream = load("res://audio/sfx_boiling_bubble.wav")
	if ResourceLoader.exists("res://audio/sfx_sizzle.wav"):
		audio_sizzle.stream = load("res://audio/sfx_sizzle.wav")


func _setup_heating_zone() -> void:
	if not heating_zone:
		heating_zone = get_node_or_null("TopPlateHeatingZone")
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
	# 1. Simulate motor rotation & stir bar
	_process_stir_motor(delta)

	# 2. Simulate closed-loop PID heat regulation & conductive heat transfer
	_process_pid_thermodynamics(delta)

	# 3. Apply fluid vortex & Noyes-Whitney dissolution acceleration to overlying liquid
	_process_overlying_vessels(delta)

	# 4. Refresh 7-segment digital displays
	_update_displays()


# =============================================================================
# 1. MOTOR DYNAMICS & STIR BAR ROTATION
# =============================================================================

func _process_stir_motor(delta: float) -> void:
	var target = target_rpm if is_powered_on else 0.0

	# Smooth motor inertia acceleration
	if motor_acceleration_time_s > 0.001:
		var rate = 1500.0 / motor_acceleration_time_s
		current_rpm = move_toward(current_rpm, target, rate * delta)
	else:
		current_rpm = target

	actual_rpm_updated.emit(current_rpm)

	# Rotate Stir Bar around Y axis
	if current_rpm > 1.0:
		var ang_vel_rad_s = (current_rpm / 60.0) * (2.0 * PI)
		stir_bar_angle_rad += ang_vel_rad_s * delta
		if stir_bar:
			stir_bar.rotation.y = stir_bar_angle_rad
			# Micro-jitter rattle at high RPM (> 1100 RPM)
			if current_rpm > 1100.0:
				var jitter_amp = (current_rpm - 1100.0) / 400.0 * 0.0006
				stir_bar.position.x = sin(stir_bar_angle_rad * 3.0) * jitter_amp
				stir_bar.position.z = cos(stir_bar_angle_rad * 3.0) * jitter_amp
			else:
				stir_bar.position.x = 0.0
				stir_bar.position.z = 0.0

	# Update motor acoustic hum
	if enable_audio and audio_motor:
		if current_rpm > 15.0:
			if not audio_motor.playing:
				audio_motor.play()
			var normalized_rpm = current_rpm / 1500.0
			audio_motor.pitch_scale = 0.5 + normalized_rpm * 1.5
			audio_motor.volume_db = motor_base_volume_db + normalized_rpm * 10.0
		else:
			if audio_motor.playing:
				audio_motor.stop()


# =============================================================================
# 2. CLOSED-LOOP PID TEMPERATURE REGULATION
# =============================================================================

func _process_pid_thermodynamics(delta: float) -> void:
	var setpoint = target_temp_c if is_powered_on else ambient_temperature_c

	# Error: e(t) = Setpoint - Process Variable
	var error = setpoint - current_plate_temp_c

	# Anti-windup Integral accumulation
	if is_powered_on and target_temp_c > ambient_temperature_c:
		_pid_integral = clampf(_pid_integral + error * delta, -60.0, 60.0)
	else:
		_pid_integral = 0.0

	# Derivative calculation
	var derivative = (error - _pid_prev_error) / maxf(1e-4, delta)
	_pid_prev_error = error

	# PID Output Calculation
	if is_powered_on and target_temp_c > ambient_temperature_c:
		var raw_output = (pid_kp * error) + (pid_ki * _pid_integral) + (pid_kd * derivative)
		_heater_duty_cycle = clampf(raw_output / 100.0, 0.0, 1.0)
	else:
		_heater_duty_cycle = 0.0

	# Electric heating power delivered to plate
	var p_heater_watts = _heater_duty_cycle * max_heater_power_watts

	# Convective & radiative heat loss from ceramic top plate to room air
	var delta_t_ambient = current_plate_temp_c - ambient_temperature_c
	var q_plate_loss_watts = maxf(0.0, plate_ambient_loss_coefficient * delta_t_ambient)

	# Conductive heat transfer from plate to all placed vessels
	var q_total_conduct_watts = 0.0
	for vessel in _tracked_vessels:
		if is_instance_valid(vessel):
			var v_temp = _get_vessel_temp(vessel)
			var delta_t_contact = current_plate_temp_c - v_temp
			if delta_t_contact > 0.0:
				q_total_conduct_watts += thermal_contact_conductance * delta_t_contact

	# Ceramic Plate Thermal Balance: dT/dt = (P_heater - Q_loss - Q_conduct) / (m * Cp)
	var net_plate_power = p_heater_watts - q_plate_loss_watts - q_total_conduct_watts
	var plate_dt = (net_plate_power / plate_heat_capacity_j_k) * delta
	current_plate_temp_c = maxf(ambient_temperature_c, current_plate_temp_c + plate_dt)

	plate_temperature_updated.emit(current_plate_temp_c)


# =============================================================================
# 3. OVERLYING VESSEL DYNAMICS: HEAT, VORTEX & NOYES-WHITNEY ACCELERATION
# =============================================================================

func _process_overlying_vessels(delta: float) -> void:
	var any_boiling: bool = false

	# Calculate Noyes-Whitney reaction mixing & dissolution acceleration factor:
	# Rate Multiplier = 1.0 + alpha * sqrt(RPM / 100)
	var mixing_mult: float = 1.0
	var vortex_intensity: float = 0.0
	var vortex_depth_mm: float = 0.0

	if current_rpm > 5.0:
		mixing_mult = 1.0 + 0.85 * sqrt(current_rpm / 100.0)
		vortex_intensity = clampf(pow(current_rpm / 1500.0, 2.0), 0.0, 1.0)
		vortex_depth_mm = vortex_intensity * 35.0 # Up to 35mm conical depression

	for i in range(_tracked_vessels.size() - 1, -1, -1):
		var vessel = _tracked_vessels[i]
		if not is_instance_valid(vessel):
			_tracked_vessels.remove_at(i)
			continue

		var v_temp = _get_vessel_temp(vessel)
		var v_vol = _get_vessel_volume(vessel)
		var boiling_point = _get_vessel_boiling_point(vessel)

		var mass_kg: float = maxf(0.015, (v_vol / 1000.0) * 1.0)
		var cp: float = 4184.0 # J / (kg * K)

		# Heat conduction from plate to vessel
		var delta_t_plate = current_plate_temp_c - v_temp
		var q_in = thermal_contact_conductance * delta_t_plate
		var q_loss = 1.25 * (v_temp - ambient_temperature_c)

		var new_v_temp = v_temp + ((q_in - q_loss) / (mass_kg * cp)) * delta
		new_v_temp = maxf(ambient_temperature_c, new_v_temp)

		# Boiling state
		if new_v_temp >= boiling_point:
			new_v_temp = boiling_point
			any_boiling = true
			if not _vessel_boiling_map.get(vessel, false):
				_vessel_boiling_map[vessel] = true
				vessel_boiling_started.emit(vessel, new_v_temp)
		else:
			if _vessel_boiling_map.get(vessel, false):
				_vessel_boiling_map[vessel] = false

		_set_vessel_temp(vessel, new_v_temp, delta)

		# Apply Vortex & Noyes-Whitney mixing rates to vessel
		_apply_stirring_kinetics(vessel, current_rpm, vortex_depth_mm, mixing_mult, delta)

	# Manage boiling audio
	if any_boiling:
		if audio_boil and not audio_boil.playing:
			audio_boil.play()
		if audio_sizzle and not audio_sizzle.playing:
			audio_sizzle.play()
	else:
		if audio_boil and audio_boil.playing:
			audio_boil.volume_db = lerpf(audio_boil.volume_db, -40.0, delta * 3.0)
			if audio_boil.volume_db <= -35.0:
				audio_boil.stop()
				audio_boil.volume_db = boil_volume_db
		if audio_sizzle and audio_sizzle.playing:
			audio_sizzle.volume_db = lerpf(audio_sizzle.volume_db, -40.0, delta * 3.0)
			if audio_sizzle.volume_db <= -35.0:
				audio_sizzle.stop()
				audio_sizzle.volume_db = -8.0


func _apply_stirring_kinetics(vessel: Node, rpm: float, vortex_mm: float, mixing_mult: float, delta: float) -> void:
	if "stir_rpm" in vessel:
		vessel.stir_rpm = rpm
	if "vortex_depth" in vessel:
		vessel.vortex_depth = vortex_mm
	if "is_stirring" in vessel:
		vessel.is_stirring = (rpm > 10.0)
	if "mixing_rate_multiplier" in vessel:
		vessel.mixing_rate_multiplier = mixing_mult
	if "dissolution_rate_multiplier" in vessel:
		vessel.dissolution_rate_multiplier = mixing_mult

	# Accelerate turbidity decay (precipitate dissolution / clarification)
	if "turbidity" in vessel and float(vessel.turbidity) > 0.0:
		var decay_speed = 0.02 * mixing_mult * delta
		vessel.turbidity = maxf(0.0, float(vessel.turbidity) - decay_speed)

	# Support dedicated API callback if implemented on vessel
	if vessel.has_method("set_stirring_state"):
		vessel.call("set_stirring_state", rpm, vortex_mm, mixing_mult)


# =============================================================================
# HELPER DATA GETTERS & SETTERS
# =============================================================================

func _get_simulation_bridge() -> Node:
	if is_inside_tree() and get_tree() and get_tree().root and get_tree().root.has_node("SimulationBridge"):
		return get_tree().root.get_node("SimulationBridge")
	return null


func _get_vessel_temp(vessel: Node) -> float:
	if "temperature_c" in vessel:
		return float(vessel.temperature_c)
	if "temperature" in vessel:
		return float(vessel.temperature)
	var bridge = _get_simulation_bridge()
	if bridge and "active_vessels" in bridge:
		var v_id = str(vessel.get("vessel_id") if "vessel_id" in vessel else vessel.name)
		if bridge.active_vessels.has(v_id):
			return float(bridge.active_vessels[v_id].get("temperature_c", ambient_temperature_c))
	return ambient_temperature_c


func _get_vessel_volume(vessel: Node) -> float:
	if "volume_ml" in vessel:
		return float(vessel.volume_ml)
	if "current_volume_ml" in vessel:
		return float(vessel.current_volume_ml)
	return 100.0


func _get_vessel_boiling_point(vessel: Node) -> float:
	if "boiling_point_c" in vessel:
		return float(vessel.boiling_point_c)
	if "boiling_point" in vessel:
		return float(vessel.boiling_point)
	return 100.0


func _set_vessel_temp(vessel: Node, new_temp: float, delta: float) -> void:
	if "temperature_c" in vessel:
		vessel.temperature_c = new_temp
	elif "temperature" in vessel:
		vessel.temperature = new_temp

	if vessel.has_method("apply_heat"):
		var watts = thermal_contact_conductance * maxf(0.0, current_plate_temp_c - new_temp)
		vessel.call("apply_heat", watts, delta)

	var bridge = _get_simulation_bridge()
	if bridge and "active_vessels" in bridge:
		var v_id = str(vessel.get("vessel_id") if "vessel_id" in vessel else vessel.name)
		if bridge.active_vessels.has(v_id):
			bridge.active_vessels[v_id]["temperature_c"] = new_temp


# =============================================================================
# 4. DIGITAL DISPLAYS & VISUALS
# =============================================================================

func _update_displays() -> void:
	if not is_powered_on:
		if temp_display:
			temp_display.text = "OFF\n--- °C"
			temp_display.modulate = Color(0.35, 0.1, 0.1, 0.4)
		if rpm_display:
			rpm_display.text = "OFF\n--- RPM"
			rpm_display.modulate = Color(0.1, 0.3, 0.15, 0.4)
		return

	# Temperature 7-Segment LED Readout
	if temp_display:
		var heat_glyph = "▲" if _heater_duty_cycle > 0.05 else " "
		temp_display.text = "PV %4.1f°C\nSV %3.0f°C %s" % [current_plate_temp_c, target_temp_c, heat_glyph]
		temp_display.modulate = Color(1.0, 0.18, 0.12, 1.0) # Vivid Red LED

	# RPM 7-Segment LED Readout
	if rpm_display:
		rpm_display.text = "ACT %4.0f\nSET %4.0f" % [current_rpm, target_rpm]
		rpm_display.modulate = Color(0.12, 1.0, 0.35, 1.0) # Vivid Emerald LED

	# Ceramic plate thermal glow at high temperatures (> 120 °C)
	if ceramic_plate_mesh:
		var mat = ceramic_plate_mesh.get_active_material(0) as StandardMaterial3D
		if mat:
			if current_plate_temp_c > 120.0:
				var glow_factor = clampf((current_plate_temp_c - 120.0) / 230.0, 0.0, 1.0)
				mat.emission_enabled = true
				mat.emission = Color(1.0, 0.25, 0.05) * glow_factor * 1.5
			else:
				mat.emission_enabled = false


func _update_knob_rotations() -> void:
	# Map Heat (0-350 °C) to rotation angle [-135° to +135°] (-2.356 to +2.356 rad)
	if heat_knob:
		var t_norm = target_temp_c / 350.0
		heat_knob.rotation.y = lerpf(-deg_to_rad(135.0), deg_to_rad(135.0), t_norm)

	# Map Stir (0-1500 RPM) to rotation angle [-135° to +135°] (-2.356 to +2.356 rad)
	if stir_knob:
		var r_norm = target_rpm / 1500.0
		stir_knob.rotation.y = lerpf(-deg_to_rad(135.0), deg_to_rad(135.0), r_norm)

	if power_switch:
		power_switch.rotation.x = deg_to_rad(15.0) if is_powered_on else deg_to_rad(-15.0)


# =============================================================================
# PUBLIC CONTROL API
# =============================================================================

func toggle_power() -> void:
	set_power(not is_powered_on)


func set_power(on: bool) -> void:
	is_powered_on = on
	power_toggled.emit(on)
	_update_knob_rotations()
	_update_displays()


func set_target_temperature(temp_c: float) -> void:
	target_temp_c = clampf(temp_c, 0.0, 350.0)
	target_temperature_changed.emit(target_temp_c)
	_update_knob_rotations()


func adjust_target_temperature(delta_c: float) -> void:
	set_target_temperature(target_temp_c + delta_c)


func set_target_rpm(rpm: float) -> void:
	target_rpm = clampf(rpm, 0.0, 1500.0)
	target_rpm_changed.emit(target_rpm)
	_update_knob_rotations()


func adjust_target_rpm(delta_rpm: float) -> void:
	set_target_rpm(target_rpm + delta_rpm)


# =============================================================================
# HEATING ZONE PROXIMITY SIGNALS
# =============================================================================

func _on_heating_zone_body_entered(body: Node) -> void:
	var vessel = _resolve_vessel_node(body)
	if vessel and not _tracked_vessels.has(vessel):
		_tracked_vessels.append(vessel)
		vessel_placed_on_plate.emit(vessel)
		_position_stir_bar_in_vessel(vessel)


func _on_heating_zone_body_exited(body: Node) -> void:
	var vessel = _resolve_vessel_node(body)
	if vessel and _tracked_vessels.has(vessel):
		_tracked_vessels.erase(vessel)
		_vessel_boiling_map.erase(vessel)
		vessel_removed_from_plate.emit(vessel)
		_reset_stir_bar_position()


func _on_heating_zone_area_entered(area: Area3D) -> void:
	var vessel = _resolve_vessel_node(area)
	if vessel and not _tracked_vessels.has(vessel):
		_tracked_vessels.append(vessel)
		vessel_placed_on_plate.emit(vessel)
		_position_stir_bar_in_vessel(vessel)


func _on_heating_zone_area_exited(area: Area3D) -> void:
	var vessel = _resolve_vessel_node(area)
	if vessel and _tracked_vessels.has(vessel):
		_tracked_vessels.erase(vessel)
		_vessel_boiling_map.erase(vessel)
		vessel_removed_from_plate.emit(vessel)
		_reset_stir_bar_position()


func _position_stir_bar_in_vessel(_vessel: Node) -> void:
	if stir_bar:
		# Elevates stir bar slightly into the bottom of glassware
		stir_bar.position.y = 0.046


func _reset_stir_bar_position() -> void:
	if stir_bar:
		# Sits directly flush on ceramic top plate
		stir_bar.position.y = 0.044


func _resolve_vessel_node(node: Node) -> Node:
	var curr: Node = node
	while curr != null:
		if curr.is_in_group("vessel") or curr.is_in_group("glassware") or curr.has_meta("is_vessel") or "temperature_c" in curr or "volume_ml" in curr:
			return curr
		curr = curr.get_parent()
	return node


# =============================================================================
# PLAYER INPUT HANDLING (CLICK & WHEEL INTERACTION)
# =============================================================================

func _input_event(_camera: Camera3D, event: InputEvent, click_position: Vector3, _click_normal: Vector3, _shape_idx: int) -> void:
	var local_pos = to_local(click_position)

	if event is InputEventMouseButton:
		var mb = event as InputEventMouseButton
		if mb.pressed:
			# Differentiate between Heat knob (left side), Stir knob (right side), or Power switch
			if local_pos.z > 0.06:
				if local_pos.x < -0.03: # Heat Knob region
					if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
						adjust_target_temperature(5.0)
					elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
						adjust_target_temperature(-5.0)
					elif mb.button_index == MOUSE_BUTTON_LEFT:
						_active_drag_knob = DraggedKnob.HEAT
						_last_drag_mouse_pos = mb.position
				elif local_pos.x > 0.03: # Stir Knob region
					if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
						adjust_target_rpm(25.0)
					elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
						adjust_target_rpm(-25.0)
					elif mb.button_index == MOUSE_BUTTON_LEFT:
						_active_drag_knob = DraggedKnob.STIR
						_last_drag_mouse_pos = mb.position
				else: # Center / Power switch
					if mb.button_index == MOUSE_BUTTON_LEFT:
						toggle_power()
		else:
			if mb.button_index == MOUSE_BUTTON_LEFT:
				_active_drag_knob = DraggedKnob.NONE

	elif event is InputEventMouseMotion and _active_drag_knob != DraggedKnob.NONE:
		var mm = event as InputEventMouseMotion
		var delta_y = -mm.relative.y # Upward drag increases value
		if _active_drag_knob == DraggedKnob.HEAT:
			adjust_target_temperature(delta_y * 1.5)
		elif _active_drag_knob == DraggedKnob.STIR:
			adjust_target_rpm(delta_y * 8.0)
