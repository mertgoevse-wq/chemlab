# Athanor Ascension — Webcam Input & Gesture Telemetry Verification Test
# Run: tools/bin/godot --headless --path game --script res://tests/test_webcam_input_manager.gd
extends SceneTree

const InputManagerScript = preload("res://scripts/input/input_manager.gd")

var _passed: int = 0
var _failed: int = 0


func _init() -> void:
	print("\n>>> [InputManager] Verifying Webcam Telemetry and Apparatus Manipulation")
	_run_tests()


func _run_tests() -> void:
	var im: Node = root.get_node_or_null("InputManager")
	var created_instance: bool = false
	if im == null:
		im = InputManagerScript.new()
		root.add_child(im)
		created_instance = true

	# Mock dummy apparatus
	var dummy_flask = Node3D.new()
	dummy_flask.name = "TestFlask"
	root.add_child(dummy_flask)

	# 1. Test Hover tracking
	im.apparatus_hovered.emit(dummy_flask)
	_check("Hovered apparatus registered", im.currently_hovered_apparatus == dummy_flask, true)

	# 2. Test PINCH gesture grab
	var test_state := {
		"grab_emitted": false,
		"grabbed_app": null,
		"tilt_emitted": false,
		"recorded_tilt": 0.0,
		"pour_emitted": false,
		"recorded_pour_rate": 0.0,
		"release_emitted": false
	}

	im.apparatus_grabbed.connect(func(app):
		test_state["grab_emitted"] = true
		test_state["grabbed_app"] = app
	)

	im._on_gesture_received({
		"gesture": "PINCH",
		"confidence": 0.95,
		"pinch_distance": 0.02,
		"tilt_degrees": 12.0
	})

	_check("PINCH emitted apparatus_grabbed", test_state["grab_emitted"], true)
	_check("Grabbed correct apparatus", test_state["grabbed_app"] == dummy_flask, true)
	_check("is_holding_apparatus flag set", im.is_holding_apparatus, true)

	# 3. Test Tilt angle update
	im.tilt_angle_updated.connect(func(deg):
		test_state["tilt_emitted"] = true
		test_state["recorded_tilt"] = deg
	)

	im._on_gesture_received({
		"gesture": "PINCH_DRAG",
		"confidence": 0.92,
		"tilt_degrees": 48.5,
		"pour_rate": 0.65
	})

	_check("tilt_angle_updated emitted", test_state["tilt_emitted"], true)
	_check_close("tilt angle accurate", test_state["recorded_tilt"], 48.5, 0.1)

	# 4. Test Pour emission
	im.apparatus_poured.connect(func(rate):
		test_state["pour_emitted"] = true
		test_state["recorded_pour_rate"] = rate
	)

	im._on_gesture_received({
		"gesture": "PINCH_DRAG",
		"confidence": 0.88,
		"pour_rate": 0.75,
		"tilt_degrees": 55.0
	})

	_check("apparatus_poured emitted", test_state["pour_emitted"], true)
	_check_close("pour rate accurate", test_state["recorded_pour_rate"], 0.75, 0.05)

	# 5. Test RELEASE gesture
	im.apparatus_released.connect(func(_app):
		test_state["release_emitted"] = true
	)

	im._on_gesture_received({
		"gesture": "RELEASE",
		"confidence": 0.90
	})

	_check("RELEASE emitted apparatus_released", test_state["release_emitted"], true)
	_check("is_holding_apparatus reset", im.is_holding_apparatus, false)

	# 6. Test Unhover
	im.apparatus_unhovered.emit(dummy_flask)
	_check("Unhover cleared apparatus", im.currently_hovered_apparatus == null, true)

	# Cleanup
	dummy_flask.queue_free()
	if created_instance:
		im.queue_free()

	print("\n>>> RESULTS: %d passed, %d failed" % [_passed, _failed])
	if _failed == 0:
		print("PASS  InputManager webcam gesture verification")
		quit(0)
	else:
		printerr("FAIL  InputManager webcam gesture verification")
		quit(1)


func _check(label: String, actual: Variant, expected: Variant) -> void:
	if actual == expected:
		_passed += 1
		print("  ✓ " + label)
	else:
		_failed += 1
		printerr("  ✗ %s (expected %s, got %s)" % [label, str(expected), str(actual)])


func _check_close(label: String, actual: float, expected: float, tol: float = 0.01) -> void:
	if absf(actual - expected) <= tol:
		_passed += 1
		print("  ✓ " + label)
	else:
		_failed += 1
		printerr("  ✗ %s (expected %.3f, got %.3f)" % [label, expected, actual])
