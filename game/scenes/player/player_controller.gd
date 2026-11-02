# ChemLab First-Person Player Controller (Godot 4)
# Full 3D locomotion, mouse look, raycast interaction, pickup, carrying, pour tilt, swirl and HUD delegation.

extends CharacterBody3D
class_name PlayerController

# =============================================================================
# SIGNALS
# =============================================================================
signal apparatus_hovered(apparatus: Node)
signal apparatus_unhovered(apparatus: Node)
signal apparatus_picked_up(apparatus: Node)
signal apparatus_dropped(apparatus: Node)
signal mouse_capture_changed(is_captured: bool)

# =============================================================================
# CONSTANTS & DEFAULTS
# =============================================================================
const DEFAULT_WALK_SPEED: float = 3.0
const DEFAULT_SPRINT_MULTIPLIER: float = 1.6
const DEFAULT_JUMP_IMPULSE: float = 4.5
const DEFAULT_GRAVITY: float = 9.8
const ACCELERATION: float = 12.0
const DECELERATION: float = 16.0
const AIR_ACCEL_MODIFIER: float = 0.35

const DEFAULT_MOUSE_SENSITIVITY: float = 0.002
const MIN_PITCH_DEG: float = -85.0
const MAX_PITCH_DEG: float = 85.0

const DEFAULT_MAX_POUR_ANGLE: float = 80.0
const POUR_TILT_SPEED: float = 120.0 # degrees per second
const POUR_THRESHOLD_ANGLE: float = 35.0
const CARRY_LERP_SPEED: float = 18.0
const SWIRL_ANGULAR_VELOCITY: float = 16.0 # radians / sec

# =============================================================================
# EXPORTED VARIABLES
# =============================================================================
@export_group("Locomotion")
@export var walk_speed: float = DEFAULT_WALK_SPEED
@export var sprint_multiplier: float = DEFAULT_SPRINT_MULTIPLIER
@export var jump_impulse: float = DEFAULT_JUMP_IMPULSE
@export var gravity: float = DEFAULT_GRAVITY
@export var mouse_sensitivity: float = DEFAULT_MOUSE_SENSITIVITY

@export_group("Carrying & Interaction")
@export var max_pour_angle: float = DEFAULT_MAX_POUR_ANGLE
@export var carry_lerp_speed: float = CARRY_LERP_SPEED
@export var interaction_range: float = 2.5

# =============================================================================
# NODE REFERENCES
# =============================================================================
@onready var collision_shape: CollisionShape3D = $CollisionShape3D
@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var interaction_ray: RayCast3D = $Head/InteractionRay
@onready var held_item_socket: Marker3D = $Head/HeldItemSocket

@onready var hud: CanvasLayer = $HUD
@onready var crosshair: Control = $HUD/Crosshair
@onready var prompt_panel: PanelContainer = $HUD/InteractionPrompt
@onready var apparatus_label: Label = $HUD/InteractionPrompt/VBoxContainer/ApparatusLabel
@onready var action_hints_label: Label = $HUD/InteractionPrompt/VBoxContainer/ActionHintsLabel
@onready var spatial_hud_anchor: Control = $HUD/SpatialHUDAnchor

# =============================================================================
# RUNTIME STATE
# =============================================================================
var is_mouse_captured: bool = true
var hovered_apparatus: Node = null

# Held Item State
var carried_item: Node = null
var carried_item_original_parent: Node = null
var carried_item_layer: int = 1
var carried_item_mask: int = 1
var carried_item_freeze: bool = false
var carried_item_freeze_mode: RigidBody3D.FreezeMode = RigidBody3D.FREEZE_MODE_STATIC

# Pour & Swirl Dynamics
var is_pouring: bool = false
var is_swirling: bool = false
var manual_tilt_angle: float = 0.0
var current_pour_angle: float = 0.0
var target_pour_angle: float = 0.0
var swirl_timer: float = 0.0

# Cached InputManager singleton
var _cached_input_manager: Node = null

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	_ensure_references()
	_setup_mouse_capture(true)
	_setup_interaction_ray()
	_connect_input_manager_signals()

	if prompt_panel:
		prompt_panel.visible = false
	if spatial_hud_anchor:
		spatial_hud_anchor.visible = false


func _ensure_references() -> void:
	if head == null: head = get_node_or_null("Head")
	if camera == null and head != null: camera = head.get_node_or_null("Camera3D")
	if interaction_ray == null and head != null: interaction_ray = head.get_node_or_null("InteractionRay")
	if held_item_socket == null and head != null: held_item_socket = head.get_node_or_null("HeldItemSocket")
	if hud == null: hud = get_node_or_null("HUD")
	if crosshair == null and hud != null: crosshair = hud.get_node_or_null("Crosshair")
	if prompt_panel == null and hud != null: prompt_panel = hud.get_node_or_null("InteractionPrompt")
	if apparatus_label == null and prompt_panel != null: apparatus_label = prompt_panel.get_node_or_null("VBoxContainer/ApparatusLabel")
	if action_hints_label == null and prompt_panel != null: action_hints_label = prompt_panel.get_node_or_null("VBoxContainer/ActionHintsLabel")
	if spatial_hud_anchor == null and hud != null: spatial_hud_anchor = hud.get_node_or_null("SpatialHUDAnchor")


func _physics_process(delta: float) -> void:
	if not is_inside_tree():
		return
	_ensure_references()
	_process_locomotion(delta)
	_process_interaction_detection()
	_process_carried_item(delta)
	_update_hud_display()


func _unhandled_input(event: InputEvent) -> void:
	# 1. Escape toggles mouse capture (captured for gameplay, visible for UI/menu)
	if event.is_action_pressed("pause_menu") or (event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE):
		_setup_mouse_capture(not is_mouse_captured)
		get_viewport().set_input_as_handled()
		return

	# Re-capture mouse on click if currently free
	if not is_mouse_captured and event is InputEventMouseButton and event.pressed:
		_setup_mouse_capture(true)
		get_viewport().set_input_as_handled()
		return

	if not is_mouse_captured:
		return

	# 2. Mouse Look (Horizontal rotation on Player, Vertical pitch clamping [-85°, +85°] on Head)
	if event is InputEventMouseMotion:
		_process_mouse_look(event as InputEventMouseMotion)
		return

	# 3. Action Inputs
	_process_action_inputs(event)

# =============================================================================
# MOUSE LOOK & CAPTURE
# =============================================================================

func _setup_mouse_capture(captured: bool) -> void:
	is_mouse_captured = captured
	if captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	else:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	mouse_capture_changed.emit(captured)


func _process_mouse_look(motion: InputEventMouseMotion) -> void:
	# Horizontal rotation applies directly to Player body around Y
	rotate_y(-motion.relative.x * mouse_sensitivity)

	# Vertical rotation applies to Head around X, clamped between [-85°, +85°]
	var new_pitch = head.rotation.x - motion.relative.y * mouse_sensitivity
	head.rotation.x = clampf(new_pitch, deg_to_rad(MIN_PITCH_DEG), deg_to_rad(MAX_PITCH_DEG))

# =============================================================================
# LOCOMOTION
# =============================================================================

func _process_locomotion(delta: float) -> void:
	# Apply gravity when in air
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0

	# Jump impulse
	if is_on_floor() and (Input.is_action_just_pressed("jump") or (Input.is_key_pressed(KEY_SPACE) and is_mouse_captured)):
		velocity.y = jump_impulse

	# Vector input: WASD
	var input_vector = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	if input_vector == Vector2.ZERO and is_mouse_captured:
		var raw_x: float = 0.0
		var raw_y: float = 0.0
		if Input.is_key_pressed(KEY_D): raw_x += 1.0
		if Input.is_key_pressed(KEY_A): raw_x -= 1.0
		if Input.is_key_pressed(KEY_S): raw_y += 1.0
		if Input.is_key_pressed(KEY_W): raw_y -= 1.0
		input_vector = Vector2(raw_x, raw_y).normalized()

	# Compute 3D direction relative to player body orientation
	var wish_dir = (transform.basis * Vector3(input_vector.x, 0, input_vector.y)).normalized()

	# Sprint multiplier
	var is_sprinting = (Input.is_action_pressed("sprint") or Input.is_key_pressed(KEY_SHIFT)) and input_vector.y < 0.1
	var target_speed = walk_speed * (sprint_multiplier if is_sprinting else 1.0)

	# Slight speed moderation if carrying heavy glassware
	if carried_item != null:
		target_speed *= 0.88

	# Smooth horizontal acceleration/deceleration lerp
	var target_h_vel = wish_dir * target_speed
	var current_h_vel = Vector3(velocity.x, 0, velocity.z)
	var accel_factor = ACCELERATION if wish_dir.length_squared() > 0.001 else DECELERATION
	if not is_on_floor():
		accel_factor *= AIR_ACCEL_MODIFIER

	current_h_vel = current_h_vel.lerp(target_h_vel, accel_factor * delta)
	velocity.x = current_h_vel.x
	velocity.z = current_h_vel.z

	move_and_slide()

# =============================================================================
# RAYCAST & INTERACTION DETECTION
# =============================================================================

func _setup_interaction_ray() -> void:
	if interaction_ray:
		interaction_ray.target_position = Vector3(0, 0, -interaction_range)
		interaction_ray.collide_with_areas = true
		interaction_ray.collide_with_bodies = true
		interaction_ray.enabled = true


func _process_interaction_detection() -> void:
	if not interaction_ray:
		return

	interaction_ray.force_raycast_update()
	var detected_target: Node = null

	if interaction_ray.is_colliding():
		var collider = interaction_ray.get_collider()
		if collider is Node:
			detected_target = _resolve_interactive_apparatus(collider as Node)

	if detected_target != hovered_apparatus:
		if hovered_apparatus != null:
			apparatus_unhovered.emit(hovered_apparatus)
			_notify_input_manager_hover(hovered_apparatus, false)
		hovered_apparatus = detected_target
		if hovered_apparatus != null:
			apparatus_hovered.emit(hovered_apparatus)
			_notify_input_manager_hover(hovered_apparatus, true)


func _resolve_interactive_apparatus(node: Node) -> Node:
	var curr: Node = node
	while curr != null and curr != self:
		if curr.is_in_group("interactive_apparatus") or curr.has_method("get_interaction_info"):
			return curr
		if curr.is_in_group("apparatus") or curr.is_in_group("interactable"):
			return curr
		curr = curr.get_parent()
	return null

# =============================================================================
# PICKUP, CARRYING, POUR & SWIRL SYSTEM
# =============================================================================

func pickup_apparatus(target: Node) -> void:
	if target == null or carried_item != null:
		return

	# Verification via get_interaction_info if available
	if target.has_method("get_interaction_info"):
		var info = target.get_interaction_info()
		if info is Dictionary and not bool(info.get("can_pickup", true)):
			return

	carried_item = target
	carried_item_original_parent = target.get_parent()

	# Save and adjust collision masks to prevent colliding with player's capsule
	if target is CollisionObject3D:
		var col = target as CollisionObject3D
		carried_item_layer = col.collision_layer
		carried_item_mask = col.collision_mask
		col.collision_layer = 0
		col.collision_mask = 0

	# Kinematic freeze for physics bodies
	if target is RigidBody3D:
		var rb = target as RigidBody3D
		carried_item_freeze = rb.freeze
		carried_item_freeze_mode = rb.freeze_mode
		rb.freeze = true
		rb.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
		rb.linear_velocity = Vector3.ZERO
		rb.angular_velocity = Vector3.ZERO

	_ensure_references()
	# Reparent or add to HeldItemSocket
	if target.get_parent() != null:
		var keep_transform = target.is_inside_tree() and held_item_socket.is_inside_tree()
		target.reparent(held_item_socket, keep_transform)
	else:
		held_item_socket.add_child(target)

	# Reset states
	current_pour_angle = 0.0
	target_pour_angle = 0.0
	manual_tilt_angle = 0.0
	is_pouring = false
	is_swirling = false
	swirl_timer = 0.0

	# Forward lifecycle callback to apparatus
	if target.has_method("on_picked_up"):
		target.on_picked_up(self)

	# Inform InputManager singleton
	var im = _get_input_manager()
	if im and im.has_method("grab_apparatus"):
		im.grab_apparatus(target)

	apparatus_picked_up.emit(target)


func drop_carried_apparatus(apply_impulse: bool = true) -> void:
	if carried_item == null:
		return

	var item = carried_item
	carried_item = null
	is_pouring = false
	is_swirling = false
	current_pour_angle = 0.0
	manual_tilt_angle = 0.0

	# Reparent to original parent or scene root
	var dest_parent: Node = carried_item_original_parent
	if not is_instance_valid(dest_parent) or not dest_parent.is_inside_tree():
		if is_inside_tree():
			var tree = get_tree()
			if tree != null:
				dest_parent = tree.current_scene if tree.current_scene != null else tree.root
		if dest_parent == null:
			dest_parent = get_parent()

	if item.get_parent() != null:
		var keep_transform = item.is_inside_tree() and (dest_parent != null and dest_parent.is_inside_tree())
		item.reparent(dest_parent, keep_transform)
	else:
		if dest_parent != null:
			dest_parent.add_child(item)

	# Restore collision masks
	if item is CollisionObject3D:
		var col = item as CollisionObject3D
		col.collision_layer = carried_item_layer
		col.collision_mask = carried_item_mask

	# Restore rigid body physics with gentle toss impulse
	if item is RigidBody3D:
		var rb = item as RigidBody3D
		rb.freeze = carried_item_freeze
		rb.freeze_mode = carried_item_freeze_mode
		if apply_impulse:
			var toss_dir = -camera.global_transform.basis.z if camera else Vector3(0, 0, -1)
			rb.linear_velocity = velocity + toss_dir * 2.5 + Vector3(0, 0.5, 0)
			rb.angular_velocity = Vector3(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * 1.5

	if item.has_method("on_dropped"):
		item.on_dropped(self)

	var im = _get_input_manager()
	if im and im.has_method("release_apparatus"):
		im.release_apparatus()

	apparatus_dropped.emit(item)


func place_carried_apparatus(target_surface: Node, world_position: Vector3, surface_normal: Vector3) -> void:
	if carried_item == null:
		return

	var item = carried_item
	carried_item = null
	is_pouring = false
	is_swirling = false
	current_pour_angle = 0.0
	manual_tilt_angle = 0.0

	var dest_parent: Node = target_surface if is_instance_valid(target_surface) else null
	if dest_parent == null:
		if is_inside_tree():
			var tree = get_tree()
			if tree != null:
				dest_parent = tree.current_scene if tree.current_scene != null else tree.root
		if dest_parent == null:
			dest_parent = get_parent()

	if item.get_parent() != null:
		var keep_transform = item.is_inside_tree() and (dest_parent != null and dest_parent.is_inside_tree())
		item.reparent(dest_parent, keep_transform)
	else:
		if dest_parent != null:
			dest_parent.add_child(item)
	item.global_position = world_position + surface_normal * 0.02
	# Orient upright
	item.global_basis = Basis.IDENTITY

	if item is CollisionObject3D:
		var col = item as CollisionObject3D
		col.collision_layer = carried_item_layer
		col.collision_mask = carried_item_mask

	if item is RigidBody3D:
		var rb = item as RigidBody3D
		rb.freeze = carried_item_freeze
		rb.freeze_mode = carried_item_freeze_mode
		rb.linear_velocity = Vector3.ZERO
		rb.angular_velocity = Vector3.ZERO

	if item.has_method("on_placed"):
		item.on_placed(target_surface)
	if target_surface and target_surface.has_method("on_apparatus_placed"):
		target_surface.on_apparatus_placed(item)

	var im = _get_input_manager()
	if im and im.has_method("release_apparatus"):
		im.release_apparatus()

	apparatus_dropped.emit(item)


func _process_carried_item(delta: float) -> void:
	if carried_item == null or not is_instance_valid(carried_item):
		return

	# 1. Update Pour Tilt Angle
	var desired_angle = target_pour_angle if is_pouring else manual_tilt_angle
	current_pour_angle = move_toward(current_pour_angle, desired_angle, POUR_TILT_SPEED * delta)

	var pour_rate: float = 0.0
	if current_pour_angle > POUR_THRESHOLD_ANGLE:
		pour_rate = clampf((current_pour_angle - POUR_THRESHOLD_ANGLE) / (max_pour_angle - POUR_THRESHOLD_ANGLE), 0.0, 1.0)

	# Delegate pour to carried apparatus
	if pour_rate > 0.0:
		if carried_item.has_method("pour"):
			carried_item.pour(pour_rate, delta)
		elif carried_item.has_method("on_pour"):
			carried_item.on_pour(pour_rate, delta)

		# If hovering over another apparatus (e.g. beaker under flask), forward liquid transfer
		if hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			if hovered_apparatus.has_method("receive_liquid"):
				hovered_apparatus.receive_liquid(carried_item, pour_rate * delta)
			elif hovered_apparatus.has_method("on_liquid_transferred"):
				hovered_apparatus.on_liquid_transferred(carried_item, pour_rate * delta)

		var im = _get_input_manager()
		if im and im.has_signal("apparatus_poured"):
			im.apparatus_poured.emit(pour_rate)

	# 2. Update Swirl Dynamics
	var swirl_offset = Vector3.ZERO
	var swirl_basis = Basis.IDENTITY

	if is_swirling:
		swirl_timer += delta * SWIRL_ANGULAR_VELOCITY
		var sx = cos(swirl_timer) * 0.02
		var sz = sin(swirl_timer) * 0.02
		var sy = sin(swirl_timer * 2.0) * 0.005
		swirl_offset = Vector3(sx, sy, sz)
		var swirl_axis = Vector3(sin(swirl_timer), 0.0, cos(swirl_timer)).normalized()
		swirl_basis = Basis(swirl_axis, deg_to_rad(12.0))

		if carried_item.has_method("swirl"):
			carried_item.swirl(120.0, delta)
		elif carried_item.has_method("on_swirl"):
			carried_item.on_swirl(120.0, delta)

		var im = _get_input_manager()
		if im and im.has_signal("apparatus_swirled"):
			im.apparatus_swirled.emit(120.0)
	else:
		swirl_timer = 0.0

	# 3. Construct Target Transform in HeldItemSocket Local Space
	# Pour tilt rotates around local X (pitch forward) with slight roll along Z
	var tilt_pitch = deg_to_rad(-current_pour_angle)
	var tilt_roll = deg_to_rad(current_pour_angle * 0.25)
	var pour_basis = Basis().rotated(Vector3.RIGHT, tilt_pitch).rotated(Vector3.FORWARD, tilt_roll)

	var target_local_basis = pour_basis * swirl_basis
	var target_local_pos = swirl_offset

	# 4. Smooth Interpolation to Socket
	carried_item.position = carried_item.position.lerp(target_local_pos, carry_lerp_speed * delta)
	carried_item.basis = carried_item.basis.slerp(target_local_basis, carry_lerp_speed * delta)

# =============================================================================
# ACTION INPUT & INTERACTION DELEGATION
# =============================================================================

func _process_action_inputs(event: InputEvent) -> void:
	# --- [E] Take / Place / Interact ---
	if event.is_action_pressed("interact") or (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_E):
		_handle_interaction_trigger()
		get_viewport().set_input_as_handled()
		return

	# --- [Q] Drop ---
	if event.is_action_pressed("drop_item") or (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_Q):
		if carried_item != null:
			drop_carried_apparatus(true)
			get_viewport().set_input_as_handled()
			return

	# --- Mouse Buttons & Wheel: Pour, Swirl, Primary/Secondary Interact ---
	if event is InputEventMouseButton:
		var mb = event as InputEventMouseButton
		match mb.button_index:
			MOUSE_BUTTON_LEFT:
				_handle_left_click(mb.pressed)
				get_viewport().set_input_as_handled()

			MOUSE_BUTTON_RIGHT:
				_handle_right_click(mb.pressed)
				get_viewport().set_input_as_handled()

			MOUSE_BUTTON_WHEEL_DOWN:
				if carried_item != null and mb.pressed:
					manual_tilt_angle = clampf(manual_tilt_angle + 10.0, 0.0, max_pour_angle)
					get_viewport().set_input_as_handled()

			MOUSE_BUTTON_WHEEL_UP:
				if carried_item != null and mb.pressed:
					manual_tilt_angle = clampf(manual_tilt_angle - 10.0, 0.0, max_pour_angle)
					get_viewport().set_input_as_handled()


func _handle_interaction_trigger() -> void:
	# If carrying an apparatus:
	if carried_item != null:
		# If pointing at another apparatus (delegation or nesting)
		if hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			if hovered_apparatus.has_method("interact_with"):
				hovered_apparatus.interact_with(carried_item, self)
				return
			elif hovered_apparatus.has_method("receive_item"):
				hovered_apparatus.receive_item(carried_item)
				drop_carried_apparatus(false)
				return
			elif hovered_apparatus.has_method("place_item"):
				hovered_apparatus.place_item(carried_item)
				drop_carried_apparatus(false)
				return
			elif carried_item.has_method("use_on"):
				carried_item.use_on(hovered_apparatus)
				return
			elif hovered_apparatus.has_method("interact"):
				hovered_apparatus.interact(self)
				return

		# If pointing at a surface or workbench: place down
		if interaction_ray and interaction_ray.is_colliding():
			var hit_pos = interaction_ray.get_collision_point()
			var hit_norm = interaction_ray.get_collision_normal()
			var hit_collider = interaction_ray.get_collider() as Node
			place_carried_apparatus(hit_collider, hit_pos, hit_norm)
			return

		# Otherwise drop into space
		drop_carried_apparatus(true)
		return

	# If NOT carrying an apparatus:
	if hovered_apparatus != null and is_instance_valid(hovered_apparatus):
		# Check if pickupable
		var is_pickupable = true
		if hovered_apparatus.has_method("get_interaction_info"):
			var info = hovered_apparatus.get_interaction_info()
			if info is Dictionary and not bool(info.get("can_pickup", true)):
				is_pickupable = false

		if is_pickupable and (hovered_apparatus.is_in_group("interactive_apparatus") or hovered_apparatus.is_in_group("apparatus")):
			pickup_apparatus(hovered_apparatus)
			return

		# If not picked up, delegate interaction
		if hovered_apparatus.has_method("interact"):
			hovered_apparatus.interact(self)
		elif hovered_apparatus.has_method("activate"):
			hovered_apparatus.activate()
		elif hovered_apparatus.has_method("toggle"):
			hovered_apparatus.toggle()


func _handle_left_click(is_pressed: bool) -> void:
	if carried_item != null:
		is_pouring = is_pressed
		target_pour_angle = max_pour_angle if is_pressed else 0.0
		if not is_pressed:
			manual_tilt_angle = 0.0

		if is_pressed and hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			if hovered_apparatus.has_method("on_primary_interact_with"):
				hovered_apparatus.on_primary_interact_with(carried_item)
	else:
		# Not carrying: primary click interaction on target
		if is_pressed and hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			if hovered_apparatus.has_method("on_primary_interact"):
				hovered_apparatus.on_primary_interact(self)
			elif hovered_apparatus.has_method("interact"):
				hovered_apparatus.interact(self)


func _handle_right_click(is_pressed: bool) -> void:
	if carried_item != null:
		is_swirling = is_pressed
	else:
		# Not carrying: secondary click on target (e.g. toggle stirrer, swirl beaker on table)
		if is_pressed and hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			if hovered_apparatus.has_method("on_secondary_interact"):
				hovered_apparatus.on_secondary_interact(self)
			elif hovered_apparatus.has_method("swirl"):
				hovered_apparatus.swirl(60.0)
			elif hovered_apparatus.has_method("toggle_stirrer"):
				hovered_apparatus.toggle_stirrer()

# =============================================================================
# HUD UPDATES & SPATIAL ANCHOR
# =============================================================================

func _update_hud_display() -> void:
	# 1. Crosshair Hover State
	if crosshair and crosshair.has_method("set_hover"):
		crosshair.set_hover(hovered_apparatus != null)

	# 2. Interaction Prompt Panel
	if prompt_panel and apparatus_label and action_hints_label:
		if hovered_apparatus != null and is_instance_valid(hovered_apparatus):
			var app_name = hovered_apparatus.name.capitalize()
			var hints = "[E] Take / Place | [Left Click] Interact / Pour | [Right Click] Swirl | [Q] Drop"

			if hovered_apparatus.has_method("get_interaction_info"):
				var info = hovered_apparatus.get_interaction_info()
				if info is Dictionary:
					if info.has("name"):
						app_name = str(info["name"])
					if info.has("prompt"):
						hints = str(info["prompt"])
					elif info.has("hints"):
						hints = str(info["hints"])
				elif info is String and not str(info).is_empty():
					hints = str(info)

			apparatus_label.text = app_name
			action_hints_label.text = hints
			prompt_panel.visible = true

		elif carried_item != null and is_instance_valid(carried_item):
			var item_name = carried_item.name.capitalize() + " (In Hand)"
			apparatus_label.text = item_name
			action_hints_label.text = "[Left Click] Pour | [Right Click] Swirl | [Q] Drop | [E] Place"
			prompt_panel.visible = true
		else:
			prompt_panel.visible = false

	# 3. Spatial HUD Element Anchor
	if spatial_hud_anchor:
		if hovered_apparatus != null and is_instance_valid(hovered_apparatus) and camera:
			var target_pos = hovered_apparatus.global_position
			if not camera.is_position_behind(target_pos):
				var screen_pos = camera.unproject_position(target_pos)
				var dist = camera.global_position.distance_to(target_pos)
				if spatial_hud_anchor.has_method("update_target"):
					spatial_hud_anchor.update_target(screen_pos, dist)
				else:
					spatial_hud_anchor.position = screen_pos
					spatial_hud_anchor.visible = true
			else:
				if spatial_hud_anchor.has_method("clear_target"):
					spatial_hud_anchor.clear_target()
				else:
					spatial_hud_anchor.visible = false
		else:
			if spatial_hud_anchor.has_method("clear_target"):
				spatial_hud_anchor.clear_target()
			else:
				spatial_hud_anchor.visible = false

# =============================================================================
# INPUT MANAGER INTEGRATION
# =============================================================================

func _get_input_manager() -> Node:
	if _cached_input_manager == null and is_inside_tree():
		_cached_input_manager = get_node_or_null("/root/InputManager")
	return _cached_input_manager


func _connect_input_manager_signals() -> void:
	var im = _get_input_manager()
	if not im:
		return

	if im.has_signal("apparatus_grabbed"):
		im.apparatus_grabbed.connect(_on_external_apparatus_grabbed)
	if im.has_signal("apparatus_released"):
		im.apparatus_released.connect(_on_external_apparatus_released)
	if im.has_signal("tilt_angle_updated"):
		im.tilt_angle_updated.connect(_on_external_tilt_updated)


func _notify_input_manager_hover(apparatus: Node, is_hovering: bool) -> void:
	var im = _get_input_manager()
	if not im:
		return
	if is_hovering and im.has_signal("apparatus_hovered"):
		im.apparatus_hovered.emit(apparatus)
	elif not is_hovering and im.has_signal("apparatus_unhovered"):
		im.apparatus_unhovered.emit(apparatus)


func _on_external_apparatus_grabbed(apparatus: Variant) -> void:
	if apparatus is Node and carried_item != apparatus:
		pickup_apparatus(apparatus as Node)


func _on_external_apparatus_released(_apparatus: Variant) -> void:
	if carried_item != null:
		drop_carried_apparatus(true)


func _on_external_tilt_updated(angle_deg: float) -> void:
	if carried_item != null:
		manual_tilt_angle = clampf(angle_deg, 0.0, max_pour_angle)
