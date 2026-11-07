# Athanor Ascension - Player Controller
# Handles: Movement, interaction, webcam gestures, Joy-Con, GameSir, radial wheel

extends CharacterBody3D

class_name PlayerController

@export var move_speed: float = 3.0
@export var sprint_speed: float = 6.0
@export var jump_velocity: float = 4.5
@export var gravity: float = 9.8
@export var mouse_sensitivity: float = 0.002
@export var camera_distance: float = 2.5

# Components
var _camera: Camera3D
var _camera_pivot: Node3D
var _collision_shape: CollisionShape3D

# State
var _current_speed: float = 3.0
var _is_sprinting: bool = false
var _target_velocity: Vector3 = Vector3.ZERO
var _camera_rotation: Vector2 = Vector2.ZERO
var _interaction_target: Node3D = null
var _last_gesture: String = ""

# Input manager reference
var _input_manager: InputManager

func _ready() -> void:
	_cache_nodes()
	_setup_camera()
	_setup_input()
	_input_manager = get_node_or_null("/root/InputManager")

func _cache_nodes() -> void:
	_camera = %Camera3D
	_camera_pivot = %CameraPivot
	_collision_shape = %CollisionShape3D

func _setup_camera() -> void:
	_camera_pivot.add_child(_camera)
	_camera.position = Vector3(0, 1.6, camera_distance)
	_camera.look_at(Vector3(0, 1.6, 0))
	_input_manager.set_input_method("keyboard_mouse")

func _setup_input() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta: float) -> void:
	_handle_movement(delta)
	_apply_gravity(delta)
	move_and_slide()

func _process(delta: float) -> void:
	_handle_camera(delta)
	_check_interaction()
	_process_gestures()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_camera_rotation.x -= event.relative.y * mouse_sensitivity
		_camera_rotation.y -= event.relative.x * mouse_sensitivity
		_camera_rotation.x = clamp(_camera_rotation.x, -PI/2 + 0.1, PI/2 - 0.1)

	if event is InputEventKey:
		if event.pressed and not event.echo:
			match event.keycode:
				KEY_ESCAPE:
					Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
				KEY_TAB:
					var inv_manager = get_node_or_null("/root/InventoryManager")
					if inv_manager:
						inv_manager.toggle_radial_wheel()
				KEY_F1:
					_set_input_method("keyboard_mouse")
				KEY_F2:
					_set_input_method("webcam")
				KEY_F3:
					_set_input_method("joycon")
				KEY_F4:
					_set_input_method("gamesir")

func _set_input_method(method: String) -> void:
	var input_manager = get_node_or_null("/root/InputManager")
	if input_manager:
		input_manager.set_input_method(method)

func _handle_movement(delta: float) -> void:
	var input_dir = Vector3.ZERO

	if Input.is_action_pressed("move_forward"):
		input_dir.z -= 1
	if Input.is_action_pressed("move_back"):
		input_dir.z += 1
	if Input.is_action_pressed("move_left"):
		input_dir.x -= 1
	if Input.is_action_pressed("move_right"):
		input_dir.x += 1

	input_dir = input_dir.normalized() if input_dir.length() > 0 else Vector3.ZERO

	# Sprint
	_is_sprinting = Input.is_action_pressed("sprint") and input_dir.length() > 0
	_current_speed = sprint_speed if _is_sprinting else move_speed

	# Calculate target velocity relative to camera
	var basis = global_transform.basis
	var forward = -basis.z.normalized()
	forward.y = 0
	forward = forward.normalized()
	var right = basis.x.normalized()

	var move_dir = (forward * input_dir.z + right * input_dir.x).normalized()
	_target_velocity.x = move_dir.x * _current_speed
	_target_velocity.z = move_dir.z * _current_speed

	# Apply to velocity
	velocity.x = lerp(velocity.x, _target_velocity.x, 0.1)
	velocity.z = lerp(velocity.z, _target_velocity.z, 0.1)

	# Jump
	if is_on_floor() and Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity

func _apply_gravity(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = 0

func _handle_camera(delta: float) -> void:
	# Rotate camera pivot
	_camera_pivot.rotation.y = lerp(_camera_pivot.rotation.y, _camera_rotation.y, 0.1)
	_camera.rotation.x = lerp(_camera.rotation.x, _camera_rotation.x, 0.1)

	# Camera collision (prevent clipping through walls)
	var from = _camera_pivot.global_position
	var to = _camera.global_position
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(from, to, 1)
	var result = space_state.intersect_ray(query)
	if result:
		_camera.global_position = result.position

func _check_interaction() -> void:
	# Raycast for interaction
	var from = _camera.global_position
	var to = from + _camera.global_transform.basis.z * -3.0
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(from, to, 1)
	var result = space_state.intersect_ray(query)

	if result:
		var collider = result.collider
		if collider and collider.has_method("interact"):
			_interaction_target = collider
			_show_interaction_prompt(collider)
		else:
			_hide_interaction_prompt()
	else:
		_hide_interaction_prompt()

	# Interaction input
	if Input.is_action_just_pressed("interact") and _interaction_target:
		_interaction_target.interact()

func _show_interaction_prompt(target: Node3D) -> void:
	# Would show UI prompt
	pass

func _hide_interaction_prompt() -> void:
	# Would hide UI prompt
	pass

func _process_gestures() -> void:
	var input_manager = get_node_or_null("/root/InputManager")
	if not input_manager:
		return

	var method = input_manager.get_input_method()

	if method == "webcam":
		# Gestures handled via signal from InputManager
		pass
	elif method == "joycon":
		_process_joycon_input()
	elif method == "gamesir":
		_process_gamesir_input()

func _process_joycon_input() -> void:
	# Gyro for pour tilt
	# HD rumble for reaction feedback
	pass

func _process_gamesir_input() -> void:
	# GameSir Nova Lite analog triggers for precise pour/burner control
	pass

func _on_gesture_detected(gesture: String, data: Dictionary) -> void:
	_last_gesture = gesture
	_process_gesture_action(gesture, data)

func _process_gesture_action(gesture: String, data: Dictionary) -> void:
	var sim_bridge = get_node_or_null("/root/SimulationBridge")
	var inv_manager = get_node_or_null("/root/InventoryManager")

	match gesture:
		"PINCH":
			# Pick up apparatus
			_try_pickup_apparatus()
		"PINCH_DRAG":
			# Pour
			var pour_rate = data.get("pour_rate", 0.0)
			var tilt = data.get("tilt_degrees", 0.0)
			_try_pour(pour_rate, tilt)
		"GRAB":
			# Move vessel
			_try_grab_vessel()
		"SWIPE":
			# Turn knob
			_try_turn_knob(data.get("swipe_delta_x", 0.0))
		"POINT":
			# Raycast select
			_try_select_target(data.get("world_position_3d", Vector3.ZERO))
		"FIST":
			# Firm lock
			_try_firm_hold()

func _try_pickup_apparatus() -> void:
	if _interaction_target and _interaction_target.has_method("pickup"):
		_interaction_target.pickup()

func _try_pour(pour_rate: float, tilt: float) -> void:
	if _interaction_target and _interaction_target.has_method("pour"):
		_interaction_target.pour(pour_rate, tilt)

func _try_grab_vessel() -> void:
	if _interaction_target and _interaction_target.has_method("grab"):
		_interaction_target.grab()

func _try_turn_knob(delta_x: float) -> void:
	if _interaction_target and _interaction_target.has_method("turn_knob"):
		_interaction_target.turn_knob(delta_x)

func _try_select_target(pos: Vector3) -> void:
	# Raycast from camera to world position
	var from = _camera.global_position
	var to = from + (_camera.global_transform.basis.z * -10.0)
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(from, to, 1)
	var result = space_state.intersect_ray(query)

	if result and result.collider:
		_interaction_target = result.collider

func _try_firm_hold() -> void:
	if _interaction_target and _interaction_target.has_method("lock"):
		_interaction_target.lock()

# Quick slot activation
func _unhandled_key_input(event: InputEventKey) -> void:
	if event.pressed and not event.echo:
		for i in range(8):
			if event.keycode == KEY_1 + i:
				var inv_manager = get_node_or_null("/root/InventoryManager")
				if inv_manager:
					inv_manager.activate_quick_slot(i)
				break