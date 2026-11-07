# Athanor Ascension - Input Manager
# Autoload: InputManager
# Handles: Keyboard/mouse, webcam gestures, Joy-Con, GameSir Nova Lite, radial wheel

extends Node

class_name InputManager

signal input_method_changed(method: String)
signal gesture_detected(gesture: String, data: Dictionary)
signal radial_wheel_toggled(enabled: bool)
signal quick_slot_activated(slot_index: int)

# Input state
var current_method: String = "keyboard_mouse"  # keyboard_mouse, webcam, joycon, gamesir
var webcam_tracking_active: bool = false
var joycon_connected: bool = false
var gamesir_connected: bool = false
var radial_wheel_active: bool = false
var last_gesture: String = ""

# Webcam tracking (via IPC from Python)
var _hand_tracker_ipc: String = "127.0.0.1:8766"  # Python hand tracker port

func _ready() -> void:
	_load_settings()
	_detect_controllers()

func _load_settings() -> void:
	var config = ConfigFile.new()
	if config.load("user://input_settings.cfg") == OK:
		current_method = config.get_value("input", "method", "keyboard_mouse")
		webcam_tracking_active = config.get_value("input", "webcam_tracking", false)
	input_method_changed.emit(current_method)

func _save_settings() -> void:
	var config = ConfigFile.new()
	config.set_value("input", "method", current_method)
	config.set_value("input", "webcam_tracking", webcam_tracking_active)
	config.save("user://input_settings.cfg")

func _detect_controllers() -> void:
	# Check for Joy-Con (via SDL2 gamecontrollerdb)
	var joycon_count = Input.get_connected_joypads().size()
	joycon_connected = joycon_count > 0

	# Check for GameSir Nova Lite (presents as standard gamepad)
	# Would need specific VID/PID detection
	gamesir_connected = false  # Placeholder

# =============================================================================
# INPUT METHOD MANAGEMENT
# =============================================================================

func set_input_method(method: String) -> void:
	if method in ["keyboard_mouse", "webcam", "joycon", "gamesir"]:
		current_method = method
		input_method_changed.emit(method)
		_save_settings()

		# Start/stop webcam tracking
		if method == "webcam":
			start_webcam_tracking()
		else:
			stop_webcam_tracking()

func get_input_method() -> String:
	return current_method

# =============================================================================
# WEBCAM HAND TRACKING
# =============================================================================

func start_webcam_tracking() -> void:
	if webcam_tracking_active:
		return

	webcam_tracking_active = true
	# Connect to Python hand tracker via IPC
	# Would start the hand_tracker.py process
	print("Starting webcam hand tracking...")

	# Start IPC client to receive gesture data
	_start_hand_tracker_ipc()

func stop_webcam_tracking() -> void:
	if not webcam_tracking_active:
		return

	webcam_tracking_active = false
	_stop_hand_tracker_ipc()
	print("Stopped webcam hand tracking.")

func _start_hand_tracker_ipc() -> void:
	# Connect to hand_tracker.py on port 8766
	# Would use StreamPeerTCP or WebSocket
	pass

func _stop_hand_tracker_ipc() -> void:
	pass

func _on_gesture_received(gesture_data: Dictionary) -> void:
	var gesture = gesture_data.get("gesture", "")
	var confidence = gesture_data.get("confidence", 0.0)

	if confidence < 0.5:
		return

	last_gesture = gesture
	gesture_detected.emit(gesture, gesture_data)

	# Map gestures to game actions
	_map_gesture_to_action(gesture, gesture_data)

func _map_gesture_to_action(gesture: String, data: Dictionary) -> void:
	var inv_manager = get_node_or_null("/root/InventoryManager")
	var sim_bridge = get_node_or_null("/root/SimulationBridge")

	match gesture:
		"PINCH":
			# Pick up small apparatus
			print("Gesture: PINCH - Pick up")
		"PINCH_DRAG":
			# Pour (tilt-governed)
			var pour_rate = data.get("pour_rate", 0.0)
			var tilt = data.get("tilt_degrees", 0.0)
			if sim_bridge:
				# Would trigger pour action
				pass
		"GRAB":
			# Move vessel
			var grab_strength = data.get("grab_strength", 0.0)
		"SWIPE":
			# Turn knob
			var swipe_x = data.get("swipe_delta_x", 0.0)
			var swipe_y = data.get("swipe_delta_y", 0.0)
		"POINT":
			# Raycast select
			var world_pos = data.get("world_position_3d", Vector3.ZERO)
		"FIST":
			# Firm lock on vessel
			pass

# =============================================================================
# JOY-CON SUPPORT
# =============================================================================

func is_joycon_connected() -> bool:
	return joycon_connected

func get_joycon_mapping() -> Dictionary:
	# Joy-Con L/R mapping for lab operations
	return {
		"left_stick": "movement",
		"right_stick": "camera",
		"l_button": "pipette_aspirate",
		"zl_button": "pipette_dispense",
		"r_button": "pour_tilt",
		"zr_button": "burner_control",
		"dpad_up": "quick_select_1",
		"dpad_right": "quick_select_2",
		"dpad_down": "quick_select_3",
		"dpad_left": "quick_select_4",
		"plus_button": "menu",
		"minus_button": "radial_wheel",
		"left_stick_click": "sprint",
		"right_stick_click": "interact",
		"gyro": "pour_tilt_fine",
		"hd_rumble": "reaction_feedback"
	}

func _process_joycon_input(delta: float) -> void:
	if not joycon_connected or current_method != "joycon":
		return

	# Process gyro for pour tilt
	# Process HD rumble for reaction feedback
	pass

# =============================================================================
# GAMESIR NOVA LITE SUPPORT
# =============================================================================

func is_gamesir_connected() -> bool:
	return gamesir_connected

func get_gamesir_mapping() -> Dictionary:
	return {
		"left_stick": "movement",
		"right_stick": "camera",
		"l1": "pipette_aspirate",
		"l2": "pipette_dispense_analog",
		"r1": "pour_tilt",
		"r2": "burner_control_analog",
		"dpad": "quick_slots",
		"start": "menu",
		"select": "radial_wheel",
		"left_stick_click": "sprint",
		"right_stick_click": "interact"
	}

# =============================================================================
# RADIAL WHEEL (Assassin's Creed Style)
# =============================================================================

func toggle_radial_wheel() -> void:
	radial_wheel_active = not radial_wheel_active
	radial_wheel_toggled.emit(radial_wheel_active)

	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager:
		if radial_wheel_active:
			inv_manager.open_radial_wheel("tools")
		else:
			inv_manager.close_radial_wheel()

func is_radial_wheel_active() -> bool:
	return radial_wheel_active

func get_radial_wheel_items() -> Array[Dictionary]:
	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager:
		return inv_manager.get_radial_wheel_items("tools")
	return []

# =============================================================================
# QUICK SLOTS
# =============================================================================

func activate_quick_slot(index: int) -> void:
	if index >= 0 and index < 8:
		quick_slot_activated.emit(index)

		var inv_manager = get_node_or_null("/root/InventoryManager")
		if inv_manager:
			var item_id = inv_manager.get_quick_slot(index)
			if item_id != "":
				_use_quick_slot_item(item_id)

func _use_quick_slot_item(item_id: String) -> void:
	# Consume/use item from quick slot
	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager:
		inv_manager.remove_item(item_id, 1)
		# Apply item effect
		print("Used quick slot item: %s" % item_id)

# =============================================================================
# KEYBOARD/MOUSE (Default)
# =============================================================================

func _unhandled_input(event: InputEvent) -> void:
	if current_method != "keyboard_mouse":
		return

	# Pour action (mouse button 5 / F key)
	if event.is_action_pressed("pour"):
		gesture_detected.emit("POUR", { "source": "keyboard" })

	# Swirl action (mouse button 2 / R key)
	if event.is_action_pressed("swirl"):
		gesture_detected.emit("SWIRL", { "source": "keyboard" })

	# Radial wheel (Left Shift / Tab)
	if event.is_action_pressed("radial_wheel"):
		toggle_radial_wheel()

	# Quick slots (1-8 keys)
	for i in range(8):
		if event.is_action_pressed("quick_slot_%d" % (i + 1)):
			activate_quick_slot(i)

# =============================================================================
# CALIBRATION
# =============================================================================

func start_calibration() -> void:
	# Would open calibration wizard for webcam tracking
	print("Starting input calibration...")

func calibrate_webcam() -> Dictionary:
	# Returns calibration data
	return {
		"hand_size": 1.0,
		"camera_position": Vector3(0, 0, 0),
		"pinch_threshold": 0.045,
		"grab_threshold": 0.16
	}

# =============================================================================
# SETTINGS
# =============================================================================

func set_webcam_tracking(enabled: bool) -> void:
	webcam_tracking_active = enabled
	_save_settings()
	if enabled:
		start_webcam_tracking()
	else:
		stop_webcam_tracking()

func get_webcam_tracking() -> bool:
	return webcam_tracking_active

func to_dict() -> Dictionary:
	return {
		"method": current_method,
		"webcam_tracking": webcam_tracking_active
	}

func from_dict(data: Dictionary) -> void:
	current_method = data.get("method", "keyboard_mouse")
	webcam_tracking_active = data.get("webcam_tracking", false)
	_save_settings()