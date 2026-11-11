extends SceneTree

func _init() -> void:
	print("--- BEGIN PLAYER CONTROLLER VALIDATION ---")

	# 1. Load the scene
	var scene_res = load("res://scenes/player/player_controller.tscn")
	if not scene_res:
		push_error("FAILED to load res://scenes/player/player_controller.tscn")
		quit(1)
		return
	print("Loaded scene resource successfully: ", scene_res)

	# 2. Instantiate the player
	var player = scene_res.instantiate()
	if not player:
		push_error("FAILED to instantiate Player scene")
		quit(1)
		return
	print("Instantiated player node successfully: ", player.name, " (Type: ", player.get_class(), ")")

	# 3. Add to root tree to trigger _ready()
	root.add_child(player)
	print("Added player to tree. Checking child nodes:")

	var col_shape = player.get_node_or_null("CollisionShape3D")
	assert(col_shape != null, "CollisionShape3D must exist")
	assert(col_shape.shape is CapsuleShape3D, "Shape must be CapsuleShape3D")
	var capsule = col_shape.shape as CapsuleShape3D
	assert(is_equal_approx(capsule.height, 1.8), "Height must be 1.8m")
	assert(is_equal_approx(capsule.radius, 0.35), "Radius must be 0.35m")
	print("  * CapsuleShape3D verified: height=1.8m, radius=0.35m")

	var head = player.get_node_or_null("Head")
	assert(head != null, "Head must exist")
	assert(is_equal_approx(head.position.y, 1.65), "Head must be at y=1.65m")
	print("  * Head verified: at y=1.65m")

	var camera = head.get_node_or_null("Camera3D")
	assert(camera != null, "Camera3D must exist")
	assert(is_equal_approx(camera.fov, 75.0), "FOV must be 75")
	assert(is_equal_approx(camera.near, 0.05), "Near must be 0.05")
	assert(is_equal_approx(camera.far, 100.0), "Far must be 100.0")
	print("  * Camera3D verified: FOV=75, Near=0.05, Far=100.0")

	var ray = head.get_node_or_null("InteractionRay")
	assert(ray != null, "InteractionRay must exist")
	assert(ray.target_position == Vector3(0, 0, -2.5), "Target position must be (0, 0, -2.5)")
	assert(ray.collide_with_areas == true, "Must collide with areas")
	assert(ray.collide_with_bodies == true, "Must collide with bodies")
	print("  * InteractionRay verified: target=(0,0,-2.5), areas=true, bodies=true")

	var socket = head.get_node_or_null("HeldItemSocket")
	assert(socket != null, "HeldItemSocket must exist")
	assert(socket.position.is_equal_approx(Vector3(0.25, -0.2, -0.65)), "Socket position must be (0.25, -0.2, -0.65)")
	print("  * HeldItemSocket verified: transform at Vector3(0.25, -0.2, -0.65)")

	var hud = player.get_node_or_null("HUD")
	assert(hud != null, "HUD must exist")

	var crosshair = hud.get_node_or_null("Crosshair")
	assert(crosshair != null, "Crosshair must exist")
	print("  * HUD Crosshair verified")

	var prompt = hud.get_node_or_null("InteractionPrompt")
	assert(prompt != null, "InteractionPrompt must exist")
	var app_label = prompt.get_node_or_null("VBoxContainer/ApparatusLabel")
	var hints_label = prompt.get_node_or_null("VBoxContainer/ActionHintsLabel")
	assert(app_label != null, "ApparatusLabel must exist")
	assert(hints_label != null, "ActionHintsLabel must exist")
	print("  * HUD Interaction Prompt Panel verified: ", hints_label.text)

	var spatial_anchor = hud.get_node_or_null("SpatialHUDAnchor")
	assert(spatial_anchor != null, "SpatialHUDAnchor must exist")
	print("  * Spatial HUD Anchor verified")

	# 4. Test Locomotion & Physics Simulation
	player._physics_process(0.0166)
	print("  * Physics process executed successfully. Velocity: ", player.velocity)

	# 5. Test Pickup and Carry system
	var test_apparatus = RigidBody3D.new()
	test_apparatus.name = "ErlenmeyerFlask"
	test_apparatus.add_to_group("interactive_apparatus")
	root.add_child(test_apparatus)

	player.pickup_apparatus(test_apparatus)
	assert(player.carried_item == test_apparatus, "Apparatus must be carried")
	assert(test_apparatus.get_parent() == socket, "Apparatus must be parented to HeldItemSocket")
	print("  * Pickup verified: carried item parented to HeldItemSocket")

	# Test pour tilt
	player.is_pouring = true
	player.target_pour_angle = 60.0
	player._process_carried_item(0.5)
	assert(player.current_pour_angle > 0.0, "Pour tilt must advance")
	print("  * Pour tilt verified: current_pour_angle=", player.current_pour_angle)

	# Test swirl
	player.is_swirling = true
	player._process_carried_item(0.1)
	assert(player.swirl_timer > 0.0, "Swirl timer must advance")
	print("  * Swirl verified: swirl_timer=", player.swirl_timer)

	# Test drop
	player.drop_carried_apparatus(false)
	assert(player.carried_item == null, "Apparatus must be dropped")
	print("  * Drop verified: carried item cleared")
	test_apparatus.queue_free()

	# 6. Test Mouse Capture toggle
	player._setup_mouse_capture(false)
	assert(player.is_mouse_captured == false, "Mouse should be uncaptured")
	player._setup_mouse_capture(true)
	assert(player.is_mouse_captured == true, "Mouse should be captured")
	print("  * Mouse capture toggle verified")

	# 7. Test External InputManager Gesture Integration
	var im: Node = root.get_node_or_null("InputManager")
	if im == null:
		var InputManagerScript = load("res://scripts/input/input_manager.gd")
		if InputManagerScript:
			im = InputManagerScript.new()
			im.name = "InputManager"
			root.add_child(im)

	if im != null:
		player.set_input_manager(im)

		var test_beaker = RigidBody3D.new()
		test_beaker.name = "TestBeaker"
		test_beaker.add_to_group("interactive_apparatus")
		root.add_child(test_beaker)

		# Test grab via signal
		im.apparatus_grabbed.emit(test_beaker)
		assert(player.carried_item == test_beaker, "Apparatus must be carried via apparatus_grabbed signal")
		print("  * Signal apparatus_grabbed verified")

		# Test tilt via signal
		im.tilt_angle_updated.emit(45.0)
		assert(player.manual_tilt_angle == 45.0, "manual_tilt_angle must match signal")
		assert(player.is_pouring == true, "is_pouring must be true when tilt exceeds threshold")
		print("  * Signal tilt_angle_updated verified")

		# Test swirl via signal
		var prev_swirl = player.swirl_timer
		im.apparatus_swirled.emit(120.0)
		assert(player.is_swirling == true, "is_swirling must be true on apparatus_swirled")
		assert(player.swirl_timer > prev_swirl, "swirl_timer must advance on apparatus_swirled")
		print("  * Signal apparatus_swirled verified")

		# Test release via signal
		im.apparatus_released.emit(test_beaker)
		assert(player.carried_item == null, "Apparatus must be dropped via apparatus_released signal")
		print("  * Signal apparatus_released verified")

		test_beaker.queue_free()

	player.queue_free()
	print("--- ALL PLAYER CONTROLLER VALIDATION TESTS PASSED ---")
	quit(0)
