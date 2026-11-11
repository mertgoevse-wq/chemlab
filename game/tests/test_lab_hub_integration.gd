# Athanor Ascension — Test Lab Hub & 3D Terminal Integration
# Headless verification of LabHub scene architecture, Practicum Kiosk,
# Pneumatic Transit Station, and AI Advisor Kiosk.
# Run: tools/bin/godot --headless --path game --script res://tests/test_lab_hub_integration.gd

extends SceneTree

const HUB_PATH := "res://scenes/laboratories/lab_hub.tscn"

func _init() -> void:
	_run.call_deferred()

func _run() -> void:
	print("--- Running Test Lab Hub & 3D Terminal Integration ---")
	var failures: int = 0

	var packed := load(HUB_PATH)
	failures += _assert(packed != null, "LabHub scene loaded successfully")

	var instance: Node3D = packed.instantiate()
	failures += _assert(instance != null, "LabHub scene instantiated successfully")

	root.add_child(instance)
	await process_frame

	# Verify Architectural Rotunda Floor
	var floor_node := instance.get_node_or_null("RotundaFloor")
	failures += _assert(floor_node != null, "Rotunda floor mesh present in hub")

	# Verify Practicum Kiosk
	var practicum_kiosk := instance.get_node_or_null("PracticumKiosk")
	failures += _assert(practicum_kiosk != null, "Practicum Kiosk 3D node present in atrium")

	# Verify Pneumatic Transit Station
	var transit_station := instance.get_node_or_null("PneumaticTransitStation")
	failures += _assert(transit_station != null, "Pneumatic Transit Station 3D node present in atrium")

	# Verify AI Advisor Kiosk
	var ai_advisor := instance.get_node_or_null("AIAdvisorKiosk")
	failures += _assert(ai_advisor != null, "AI Advisor Kiosk 3D node present in atrium")

	# Verify Interaction HUD
	var hud := instance.get_node_or_null("InteractionHUD")
	failures += _assert(hud != null, "Interaction HUD overlay present")

	# Advance 1 frame of processing
	instance._process(0.016)

	instance.queue_free()

	if failures == 0:
		print("SUCCESS: All Lab Hub & 3D Terminal tests passed (0 failures).")
		quit(0)
	else:
		printerr("FAILED: %d Lab Hub tests failed." % failures)
		quit(1)

func _assert(condition: bool, msg: String) -> int:
	if not condition:
		printerr("  [FAIL] %s" % msg)
		return 1
	print("  [PASS] %s" % msg)
	return 0
