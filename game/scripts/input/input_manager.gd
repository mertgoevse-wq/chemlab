# ChemLab Dual-Input Unified Abstraction Layer (Godot 4 Engine)
# Autoload Singleton: InputManager
# Unifies Hardware Mouse/Keyboard & Webcam Hand-Tracking (MediaPipe via TCP/UDP)
# Implements 1-Euro Filter, Schmitt Trigger Hysteresis for PINCH, POUR, SWIRL gestures.

extends Node

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

enum InputMode {
	HARDWARE_DESKTOP,
	WEBCAM_TRACKER,
	HYBRID
}

enum Handedness {
	RIGHT,
	LEFT
}

enum InteractionState {
	IDLE,
	HOVER,
	GRABBED,
	POURING,
	SWIRLING
}

# MediaPipe 21 Landmark Indices
const LM_WRIST = 0
const LM_THUMB_CMC = 1
const LM_THUMB_MCP = 2
const LM_THUMB_IP = 3
const LM_THUMB_TIP = 4
const LM_INDEX_MCP = 5
const LM_INDEX_PIP = 6
const LM_INDEX_DIP = 7
const LM_INDEX_TIP = 8
const LM_MIDDLE_MCP = 9
const LM_MIDDLE_PIP = 10
const LM_MIDDLE_DIP = 11
const LM_MIDDLE_TIP = 12
const LM_RING_MCP = 13
const LM_RING_PIP = 14
const LM_RING_DIP = 15
const LM_RING_TIP = 16
const LM_PINKY_MCP = 17
const LM_PINKY_PIP = 18
const LM_PINKY_DIP = 19
const LM_PINKY_TIP = 20

# Gesture Thresholds with Schmitt Trigger Hysteresis
const PINCH_ENTER_DIST: float = 0.045     # meters (< 0.045m enters PINCH)
const PINCH_EXIT_DIST: float = 0.065      # meters (> 0.065m exits PINCH)
const POUR_ANGLE_THRESHOLD: float = 38.0  # degrees (> 38° triggers POUR)
const POUR_EXIT_ANGLE: float = 34.0       # degrees (< 34° exits POUR)
const SWIRL_MIN_RPM: float = 40.0         # RPM to trigger SWIRL
const SWIRL_EXIT_RPM: float = 20.0        # RPM to exit SWIRL

# 1-Euro Filter Default Parameters
const ONE_EURO_FC_MIN: float = 1.0        # Min cutoff frequency (Hz)
const ONE_EURO_BETA: float = 0.007        # Velocity adaptation parameter
const ONE_EURO_D_CUTOFF: float = 1.0      # Derivative cutoff frequency (Hz)

# Default Network Settings
const DEFAULT_TRACKER_HOST: String = "127.0.0.1"
const DEFAULT_TRACKER_PORT: int = 8768
const RECONNECT_INTERVAL: float = 2.0

# =============================================================================
# SIGNALS
# =============================================================================

signal apparatus_grabbed(apparatus: Variant)
signal apparatus_released(apparatus: Variant)
signal apparatus_poured(rate: float)
signal apparatus_swirled(rpm: float)
signal apparatus_hovered(apparatus: Variant)
signal apparatus_unhovered(apparatus: Variant)

signal input_mode_changed(mode: InputMode)
signal tracker_connection_changed(connected: bool)
signal landmarks_received(raw: Array, smoothed: Array, handedness: Handedness)
signal gesture_state_changed(gesture: String, is_active: bool, details: Dictionary)
signal tilt_angle_updated(angle_deg: float)
signal balance_tare_requested()

# =============================================================================
# INNER CLASSES: 1-EURO ADAPTIVE FILTER (CHI 2012)
# =============================================================================

class OneEuroFilter1D:
	var min_cutoff: float = 1.0
	var beta: float = 0.007
	var d_cutoff: float = 1.0

	var x_prev: float = 0.0
	var dx_prev: float = 0.0
	var t_prev: float = -1.0
	var initialized: bool = false

	func _init(p_fc_min: float = 1.0, p_beta: float = 0.007, p_d_cutoff: float = 1.0) -> void:
		min_cutoff = p_fc_min
		beta = p_beta
		d_cutoff = p_d_cutoff

	static func smoothing_factor(dt: float, cutoff: float) -> float:
		var r = 2.0 * PI * cutoff * dt
		return r / (r + 1.0)

	static func exponential_smoothing(alpha: float, x: float, x_old: float) -> float:
		return alpha * x + (1.0 - alpha) * x_old

	func filter(t: float, x: float) -> float:
		if not initialized or t_prev < 0.0:
			x_prev = x
			dx_prev = 0.0
			t_prev = t
			initialized = true
			return x

		var dt = t - t_prev
		if dt <= 1e-6:
			return x_prev

		# 1. Discrete signal derivative (velocity)
		var dx = (x - x_prev) / dt

		# 2. Filter derivative using fixed cutoff
		var a_d = smoothing_factor(dt, d_cutoff)
		var hat_dx = exponential_smoothing(a_d, dx, dx_prev)

		# 3. Dynamic adaptive cutoff frequency
		var cutoff = min_cutoff + beta * absf(hat_dx)

		# 4. Filter current signal using dynamic cutoff
		var a = smoothing_factor(dt, cutoff)
		var hat_x = exponential_smoothing(a, x, x_prev)

		# 5. Store state
		x_prev = hat_x
		dx_prev = hat_dx
		t_prev = t

		return hat_x

	func reset() -> void:
		initialized = false
		t_prev = -1.0


class OneEuroFilter3D:
	var fx: OneEuroFilter1D
	var fy: OneEuroFilter1D
	var fz: OneEuroFilter1D

	func _init(fc_min: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0) -> void:
		fx = OneEuroFilter1D.new(fc_min, beta, d_cutoff)
		fy = OneEuroFilter1D.new(fc_min, beta, d_cutoff)
		fz = OneEuroFilter1D.new(fc_min, beta, d_cutoff)

	func filter(t: float, v: Vector3) -> Vector3:
		return Vector3(
			fx.filter(t, v.x),
			fy.filter(t, v.y),
			fz.filter(t, v.z)
		)

	func reset() -> void:
		fx.reset()
		fy.reset()
		fz.reset()

# =============================================================================
# EXPORTED & RUNTIME VARIABLES
# =============================================================================

@export var current_input_mode: InputMode = InputMode.HYBRID
@export var tracker_host: String = DEFAULT_TRACKER_HOST
@export var tracker_port: int = DEFAULT_TRACKER_PORT
@export var ray_length: float = 100.0
@export var mouse_tilt_sensitivity: float = 4.0 # Degrees per wheel tick
@export var debug_logging: bool = false

# Network Sockets
var tcp_client: StreamPeerTCP = StreamPeerTCP.new()
var udp_server: PacketPeerUDP = PacketPeerUDP.new()
var tcp_connected: bool = false
var tcp_rx_buffer: String = ""
var reconnect_timer: float = 0.0

# 21 Landmark Filters for MediaPipe Hands
var landmark_filters: Array[OneEuroFilter3D] = []
var raw_landmarks: Array[Vector3] = []
var smoothed_landmarks: Array[Vector3] = []
var active_handedness: Handedness = Handedness.RIGHT

# Cursor Filter for smooth 2D/3D screen interaction
var cursor_filter: OneEuroFilter3D = OneEuroFilter3D.new(ONE_EURO_FC_MIN, ONE_EURO_BETA, ONE_EURO_D_CUTOFF)
var smoothed_cursor_3d: Vector3 = Vector3.ZERO
var smoothed_cursor_screen: Vector2 = Vector2.ZERO

# Gesture Detection State Machines with Hysteresis
var is_pinching: bool = false
var pinch_distance: float = 1.0

var is_pouring: bool = false
var current_tilt_degrees: float = 0.0
var pour_rate: float = 0.0

var is_swirling: bool = false
var current_swirl_rpm: float = 0.0

# Swirl Trajectory Circular Buffer
# Elements: { "pos": Vector2, "time": float }
var swirl_history: Array[Dictionary] = []
const SWIRL_WINDOW_SECONDS: float = 1.0

# Object Interaction State
var hovered_apparatus: Variant = null
var grabbed_apparatus: Variant = null
var current_state: InteractionState = InteractionState.IDLE

# Keyboard tilt accumulator (Hardware mode)
var hardware_tilt_degrees: float = 0.0

# Timing
var last_frame_time: float = 0.0

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	# Initialize 21 1-Euro landmark filters
	landmark_filters.clear()
	raw_landmarks.resize(21)
	smoothed_landmarks.resize(21)
	for i in range(21):
		landmark_filters.append(OneEuroFilter3D.new(ONE_EURO_FC_MIN, ONE_EURO_BETA, ONE_EURO_D_CUTOFF))
		raw_landmarks[i] = Vector3.ZERO
		smoothed_landmarks[i] = Vector3.ZERO

	# Initialize UDP listener for datagram tracker broadcast
	var udp_err = udp_server.bind(tracker_port, tracker_host)
	if udp_err == OK:
		_log("UDP listener bound to %s:%d" % [tracker_host, tracker_port])
	else:
		_log("UDP bind failed with code %d; TCP will be primary." % udp_err)

	# Initial TCP connection attempt
	_attempt_tcp_connection()
	_log("InputManager initialized in mode: %s" % InputMode.keys()[current_input_mode])


func _process(delta: float) -> void:
	var now = Time.get_ticks_msec() / 1000.0
	last_frame_time = now

	# 1. Manage Network Hand-Tracking Receiver
	_poll_tracker_network(delta, now)

	# 2. Hardware Raycast & Cursor Updates
	if current_input_mode != InputMode.WEBCAM_TRACKER or not tcp_connected:
		_process_hardware_targeting()

	# 3. Process Swirl Trajectory Buffer Decay
	_prune_swirl_history(now)

	# 4. Pour State Update & Dispatch
	_update_pour_state()


func _unhandled_input(event: InputEvent) -> void:
	# Hardware Mouse & Keyboard processing
	if current_input_mode == InputMode.WEBCAM_TRACKER and tcp_connected:
		return

	# Action map integration (from project.godot)
	if event.is_action_pressed("interact"):
		if grabbed_apparatus != null:
			release_apparatus()
		elif hovered_apparatus != null:
			grab_apparatus(hovered_apparatus)
	elif event.is_action_pressed("drop_item"):
		if grabbed_apparatus != null:
			release_apparatus()
	elif event.is_action_pressed("pour"):
		_adjust_hardware_tilt(15.0)
	elif event.is_action_pressed("swirl"):
		_apply_swirl_impulse(120.0)

	# Mouse Button Press: Grab & Release
	if event is InputEventMouseButton:
		var mb = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				if hovered_apparatus != null and grabbed_apparatus == null:
					grab_apparatus(hovered_apparatus)
			else:
				if grabbed_apparatus != null:
					release_apparatus()

		# Mouse Wheel Pour-Tilt Simulation
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_adjust_hardware_tilt(mouse_tilt_sensitivity)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_adjust_hardware_tilt(-mouse_tilt_sensitivity)

	# Keyboard Hotkeys
	elif event is InputEventKey and event.pressed and not event.echo:
		var key = event as InputEventKey
		match key.keycode:
			KEY_SPACE, KEY_E:
				# Toggle Grab/Release
				if grabbed_apparatus != null:
					release_apparatus()
				elif hovered_apparatus != null:
					grab_apparatus(hovered_apparatus)

			KEY_T:
				# Tare analytical balance
				balance_tare_requested.emit()
				_log("Tare balance requested via hotkey [T]")

			KEY_R:
				# Manual swirl impulse
				_apply_swirl_impulse(120.0)

			KEY_Q:
				# Tilt pour counter-clockwise
				_adjust_hardware_tilt(10.0)

			KEY_Z:
				# Tilt pour clockwise
				_adjust_hardware_tilt(-10.0)

			KEY_TAB:
				# Cycle input mode
				cycle_input_mode()

			KEY_F1:
				# Force reconnect tracker
				_attempt_tcp_connection()

# =============================================================================
# NETWORK RECEIVER: CHEMLAB-TRACKER DAEMON (STREAMPEER_TCP / UDP)
# =============================================================================

func _attempt_tcp_connection() -> void:
	var current_st = tcp_client.get_status()
	if current_st == StreamPeerTCP.STATUS_CONNECTED or current_st == StreamPeerTCP.STATUS_CONNECTING:
		return
	if current_st != StreamPeerTCP.STATUS_NONE:
		tcp_client.disconnect_from_host()

	var err = tcp_client.connect_to_host(tracker_host, tracker_port)
	if err == OK:
		_log("Attempting TCP connection to chemlab-tracker on %s:%d..." % [tracker_host, tracker_port])
	else:
		_log("TCP connection failed to initiate: %d" % err)


func _poll_tracker_network(delta: float, current_time: float) -> void:
	# Poll TCP Client
	tcp_client.poll()
	var status = tcp_client.get_status()

	if status == StreamPeerTCP.STATUS_CONNECTED:
		if not tcp_connected:
			tcp_connected = true
			reconnect_timer = 0.0
			tracker_connection_changed.emit(true)
			_log("Successfully connected to chemlab-tracker daemon.")

		var bytes_avail = tcp_client.get_available_bytes()
		if bytes_avail > 0:
			var raw_data = tcp_client.get_utf8_string(bytes_avail)
			tcp_rx_buffer += raw_data
			_parse_stream_buffer(current_time)

	elif status == StreamPeerTCP.STATUS_ERROR or status == StreamPeerTCP.STATUS_NONE:
		if tcp_connected:
			tcp_connected = false
			tracker_connection_changed.emit(false)
			_log("Disconnected from chemlab-tracker daemon.")

		# Reconnection logic
		reconnect_timer += delta
		if reconnect_timer >= RECONNECT_INTERVAL:
			reconnect_timer = 0.0
			_attempt_tcp_connection()

	# Also poll UDP packets as parallel transport fallback
	while udp_server.get_available_packet_count() > 0:
		var packet = udp_server.get_packet()
		var packet_str = packet.get_string_from_utf8()
		if packet_str.length() > 0:
			_process_json_payload(packet_str, current_time)


func _parse_stream_buffer(current_time: float) -> void:
	# Split by newline delimiters
	var newline_pos = tcp_rx_buffer.find("\n")
	while newline_pos != -1:
		var line = tcp_rx_buffer.substr(0, newline_pos).strip_edges()
		tcp_rx_buffer = tcp_rx_buffer.substr(newline_pos + 1)
		if line.length() > 0:
			_process_json_payload(line, current_time)
		newline_pos = tcp_rx_buffer.find("\n")

	# Prevent buffer bloat if malformed data arrives
	if tcp_rx_buffer.length() > 65536:
		tcp_rx_buffer = ""


func _process_json_payload(json_str: String, current_time: float) -> void:
	var json = JSON.new()
	var err = json.parse(json_str)
	if err != OK:
		return

	var data = json.data
	if not (data is Dictionary):
		return

	var dict = data as Dictionary

	# Parse Handedness
	if dict.has("handedness"):
		var h_str = str(dict["handedness"]).to_lower()
		active_handedness = Handedness.LEFT if h_str.begins_with("left") else Handedness.RIGHT

	# Parse 21 Landmarks
	if dict.has("landmarks") and dict["landmarks"] is Array:
		var lms_array = dict["landmarks"] as Array
		if lms_array.size() >= 21:
			for i in range(21):
				var item = lms_array[i]
				var lm_vec = Vector3.ZERO
				if item is Dictionary:
					lm_vec = Vector3(
						float(item.get("x", 0.0)),
						float(item.get("y", 0.0)),
						float(item.get("z", 0.0))
					)
				elif item is Array and item.size() >= 3:
					lm_vec = Vector3(float(item[0]), float(item[1]), float(item[2]))

				raw_landmarks[i] = lm_vec
				# Apply 1-Euro adaptive low-pass filter
				smoothed_landmarks[i] = landmark_filters[i].filter(current_time, lm_vec)

			landmarks_received.emit(raw_landmarks, smoothed_landmarks, active_handedness)
			_evaluate_hand_gestures(current_time)

# =============================================================================
# GESTURE EVALUATION & SCHMITT TRIGGER HYSTERESIS
# =============================================================================

func _evaluate_hand_gestures(current_time: float) -> void:
	var thumb_tip = smoothed_landmarks[LM_THUMB_TIP]
	var index_tip = smoothed_landmarks[LM_INDEX_TIP]
	var wrist = smoothed_landmarks[LM_WRIST]
	var index_mcp = smoothed_landmarks[LM_INDEX_MCP]
	var pinky_mcp = smoothed_landmarks[LM_PINKY_MCP]

	# -------------------------------------------------------------------------
	# 1. PINCH Gesture (Schmitt Trigger: < 0.045m enters, > 0.065m exits)
	# -------------------------------------------------------------------------
	pinch_distance = thumb_tip.distance_to(index_tip)

	if not is_pinching:
		if pinch_distance < PINCH_ENTER_DIST:
			is_pinching = true
			gesture_state_changed.emit("PINCH", true, {"distance": pinch_distance})
			_on_pinch_entered()
	else:
		if pinch_distance > PINCH_EXIT_DIST:
			is_pinching = false
			gesture_state_changed.emit("PINCH", false, {"distance": pinch_distance})
			_on_pinch_exited()

	# Interaction Cursor centroid (Midpoint thumb & index)
	var interaction_point = (thumb_tip + index_tip) * 0.5
	smoothed_cursor_3d = cursor_filter.filter(current_time, interaction_point)

	# -------------------------------------------------------------------------
	# 2. POUR Gesture (Wrist tilt > 38°)
	# Vector from pinky MCP to index MCP represents hand knuckle plane
	# -------------------------------------------------------------------------
	var dx_knuckle = index_mcp.x - pinky_mcp.x
	var dy_knuckle = index_mcp.y - pinky_mcp.y
	var dz_knuckle = index_mcp.z - pinky_mcp.z

	var tilt_rad = atan2(dy_knuckle + dz_knuckle * 0.5, absf(dx_knuckle) + 1e-5)
	current_tilt_degrees = rad_to_deg(tilt_rad)
	tilt_angle_updated.emit(current_tilt_degrees)

	# -------------------------------------------------------------------------
	# 3. SWIRL Gesture (Circular Trajectory in 2D Projection)
	# -------------------------------------------------------------------------
	var proj_2d = Vector2(interaction_point.x, interaction_point.y)
	swirl_history.append({"pos": proj_2d, "time": current_time})
	_evaluate_swirl_trajectory(current_time)


func _on_pinch_entered() -> void:
	_log("PINCH Entered (dist: %.4f m)" % pinch_distance)
	if hovered_apparatus != null and grabbed_apparatus == null:
		grab_apparatus(hovered_apparatus)


func _on_pinch_exited() -> void:
	_log("PINCH Exited (dist: %.4f m)" % pinch_distance)
	if grabbed_apparatus != null:
		release_apparatus()


func _evaluate_swirl_trajectory(current_time: float) -> void:
	if swirl_history.size() < 10:
		return

	# Calculate centroid of recent 2D trajectory points
	var sum_pos = Vector2.ZERO
	for pt in swirl_history:
		sum_pos += pt["pos"]
	var centroid = sum_pos / float(swirl_history.size())

	# Measure cumulative angular displacement around centroid
	var total_angle: float = 0.0
	var prev_angle: float = 0.0
	var valid_steps: int = 0
	var avg_radius: float = 0.0

	for i in range(swirl_history.size()):
		var p = swirl_history[i]["pos"] - centroid
		var r = p.length()
		avg_radius += r
		var angle = atan2(p.y, p.x)
		if i > 0:
			var diff = wrapf(angle - prev_angle, -PI, PI)
			total_angle += diff
			valid_steps += 1
		prev_angle = angle

	avg_radius /= float(swirl_history.size())

	# Radius must be larger than noise threshold (> 15mm)
	if avg_radius < 0.015:
		_set_swirling(false, 0.0)
		return

	var dt = current_time - swirl_history[0]["time"]
	if dt <= 0.1:
		return

	# Angular velocity in radians per second -> RPM
	var angular_velocity = absf(total_angle) / dt
	var calculated_rpm = (angular_velocity / (2.0 * PI)) * 60.0

	# Hysteresis for swirl state
	if not is_swirling:
		if calculated_rpm >= SWIRL_MIN_RPM and absf(total_angle) >= PI:
			_set_swirling(true, calculated_rpm)
	else:
		if calculated_rpm <= SWIRL_EXIT_RPM:
			_set_swirling(false, calculated_rpm)
		else:
			current_swirl_rpm = calculated_rpm
			apparatus_swirled.emit(current_swirl_rpm)


func _set_swirling(active: bool, rpm: float) -> void:
	if is_swirling != active:
		is_swirling = active
		current_swirl_rpm = rpm
		gesture_state_changed.emit("SWIRL", active, {"rpm": rpm})
		if active:
			apparatus_swirled.emit(rpm)
			_log("SWIRL Gesture Active: %.1f RPM" % rpm)


func _prune_swirl_history(current_time: float) -> void:
	while swirl_history.size() > 0 and (current_time - swirl_history[0]["time"]) > SWIRL_WINDOW_SECONDS:
		swirl_history.pop_front()

# =============================================================================
# POUR DYNAMICS
# =============================================================================

func _update_pour_state() -> void:
	var effective_tilt = absf(current_tilt_degrees)
	if current_input_mode != InputMode.WEBCAM_TRACKER or not tcp_connected:
		effective_tilt = absf(hardware_tilt_degrees)

	# Schmitt Trigger for POUR
	if not is_pouring:
		if effective_tilt > POUR_ANGLE_THRESHOLD and grabbed_apparatus != null:
			is_pouring = true
			pour_rate = clampf((effective_tilt - POUR_ANGLE_THRESHOLD) / 35.0, 0.0, 1.0)
			apparatus_poured.emit(pour_rate)
			gesture_state_changed.emit("POUR", true, {"rate": pour_rate, "tilt": effective_tilt})
	else:
		if effective_tilt < POUR_EXIT_ANGLE or grabbed_apparatus == null:
			is_pouring = false
			pour_rate = 0.0
			apparatus_poured.emit(0.0)
			gesture_state_changed.emit("POUR", false, {"rate": 0.0, "tilt": effective_tilt})
		else:
			pour_rate = clampf((effective_tilt - POUR_ANGLE_THRESHOLD) / 35.0, 0.0, 1.0)
			apparatus_poured.emit(pour_rate)


func _adjust_hardware_tilt(delta_deg: float) -> void:
	hardware_tilt_degrees = clampf(hardware_tilt_degrees + delta_deg, 0.0, 120.0)
	current_tilt_degrees = hardware_tilt_degrees
	tilt_angle_updated.emit(current_tilt_degrees)

# =============================================================================
# HARDWARE RAYCAST & TARGETING
# =============================================================================

func _process_hardware_targeting() -> void:
	var viewport = get_viewport()
	if not viewport:
		return

	var camera = viewport.get_camera_3d()
	if not camera:
		return

	var mouse_pos = viewport.get_mouse_position()
	smoothed_cursor_screen = mouse_pos

	var from = camera.project_ray_origin(mouse_pos)
	var to = from + camera.project_ray_normal(mouse_pos) * ray_length

	var space_state = camera.get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(from, to)
	query.collide_with_areas = true
	query.collide_with_bodies = true

	var result = space_state.intersect_ray(query)
	if result and result.has("collider"):
		var collider = result["collider"]
		var apparatus = _resolve_apparatus_root(collider)
		if apparatus != hovered_apparatus:
			if hovered_apparatus != null:
				apparatus_unhovered.emit(hovered_apparatus)
			hovered_apparatus = apparatus
			if hovered_apparatus != null:
				apparatus_hovered.emit(hovered_apparatus)
	else:
		if hovered_apparatus != null:
			apparatus_unhovered.emit(hovered_apparatus)
			hovered_apparatus = null


func _resolve_apparatus_root(node: Node) -> Variant:
	# Walks upward until finding node in "apparatus" or "interactable" group
	var curr: Node = node
	while curr != null:
		if curr.is_in_group("apparatus") or curr.is_in_group("interactable") or curr.has_meta("is_apparatus"):
			return curr
		curr = curr.get_parent()
	return node # Fallback to hit collider

# =============================================================================
# PUBLIC INTERACTION API
# =============================================================================

func grab_apparatus(apparatus: Variant) -> void:
	if apparatus == null or grabbed_apparatus == apparatus:
		return
	grabbed_apparatus = apparatus
	current_state = InteractionState.GRABBED
	apparatus_grabbed.emit(apparatus)
	_log("Apparatus grabbed: %s" % str(apparatus))


func release_apparatus() -> void:
	if grabbed_apparatus == null:
		return
	var app = grabbed_apparatus
	grabbed_apparatus = null
	current_state = InteractionState.IDLE
	is_pouring = false
	pour_rate = 0.0
	hardware_tilt_degrees = 0.0
	apparatus_poured.emit(0.0)
	apparatus_released.emit(app)
	_log("Apparatus released: %s" % str(app))


func cycle_input_mode() -> void:
	var next_mode = (int(current_input_mode) + 1) % 3
	set_input_mode(next_mode as InputMode)


func set_input_mode(new_mode: InputMode) -> void:
	current_input_mode = new_mode
	input_mode_changed.emit(new_mode)
	_log("Input Mode switched to: %s" % InputMode.keys()[new_mode])


func is_hand_tracking_active() -> bool:
	return tcp_connected or udp_server.get_available_packet_count() > 0


func get_landmark(idx: int, smoothed: bool = true) -> Vector3:
	if idx < 0 or idx >= 21:
		return Vector3.ZERO
	return smoothed_landmarks[idx] if smoothed else raw_landmarks[idx]


func get_cursor_3d() -> Vector3:
	return smoothed_cursor_3d


func get_active_apparatus() -> Variant:
	return grabbed_apparatus


func get_hovered_apparatus() -> Variant:
	return hovered_apparatus


func _apply_swirl_impulse(rpm: float) -> void:
	current_swirl_rpm = rpm
	apparatus_swirled.emit(rpm)
	_log("Manual swirl impulse applied: %.1f RPM" % rpm)


func _log(msg: String) -> void:
	if debug_logging:
		print("[InputManager] %s" % msg)
