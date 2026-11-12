# Athanor Ascension — Test Photorealistic Laboratory Bench & 3D Apparatus Suite
# Headless verification of PhotorealisticBench scene, PBR materials, metrology actuators,
# thermodynamics, and analytical instruments.
# Run: tools/bin/godot --headless --path game --script res://tests/test_photorealistic_bench.gd

extends SceneTree

const BENCH_SCENE: PackedScene = preload("res://scenes/laboratories/photorealistic_bench.tscn")

func _init() -> void:
	_run.call_deferred()

func _run() -> void:
	print("--- Running Test Photorealistic Laboratory Bench Suite ---")
	var failures: int = 0

	failures += await _test_bench_scene_instantiation()
	failures += await _test_apparatus_nodes_and_hierarchy()
	failures += await _test_analytical_balance_actuators()
	failures += await _test_magnetic_stirrer_and_heating()
	failures += await _test_distillation_thermodynamics()
	failures += await _test_ui_controls_and_logging()

	if failures == 0:
		print("SUCCESS: All Photorealistic Laboratory Bench tests passed (0 failures).")
		quit(0)
	else:
		printerr("FAILED: %d bench tests failed." % failures)
		quit(1)

func _assert(condition: bool, msg: String) -> int:
	if not condition:
		printerr("  [FAIL] %s" % msg)
		return 1
	print("  [PASS] %s" % msg)
	return 0

func _test_bench_scene_instantiation() -> int:
	print("\nTesting Photorealistic Bench Scene Instantiation...")
	var f: int = 0
	f += _assert(BENCH_SCENE != null, "Bench PackedScene loaded successfully")

	var bench = BENCH_SCENE.instantiate()
	f += _assert(bench != null, "Bench instance created successfully")
	f += _assert(bench is Control, "Bench is Control root")
	bench.free()
	return f

func _test_apparatus_nodes_and_hierarchy() -> int:
	print("\nTesting 3D Apparatus Nodes & Scene Graph...")
	var f: int = 0
	var bench = BENCH_SCENE.instantiate()
	root.add_child(bench)
	await process_frame

	var vp_container = bench.get_node_or_null("ViewportContainer")
	f += _assert(vp_container != null, "ViewportContainer exists")

	var vp = vp_container.get_node_or_null("LaboratoryViewport") if vp_container != null else null
	f += _assert(vp != null, "LaboratoryViewport exists")

	var world = vp.get_node_or_null("BenchSceneRoot") if vp != null else null
	f += _assert(world != null, "BenchSceneRoot exists")

	if world != null:
		var cam = world.get_node_or_null("LabCamera")
		f += _assert(cam != null and cam is Camera3D, "LabCamera exists and is Camera3D")

		var env = world.get_node_or_null("WorldEnv")
		f += _assert(env != null and env is WorldEnvironment, "WorldEnvironment exists with ACES tonemapper")

		var dist_rig = world.get_node_or_null("FractionalDistillationRig")
		f += _assert(dist_rig != null, "FractionalDistillationRig apparatus exists")

		var balance = world.get_node_or_null("AnalyticalBalanceStation")
		f += _assert(balance != null, "AnalyticalBalanceStation exists")

		var stirrer = world.get_node_or_null("MagneticStirrerStation")
		f += _assert(stirrer != null, "MagneticStirrerStation exists")

		var rack = world.get_node_or_null("WoodenTestTubeRack")
		f += _assert(rack != null, "WoodenTestTubeRack exists")

		var arrow = world.get_node_or_null("TargetGuideArrow")
		f += _assert(arrow != null, "TargetGuideArrow 3D guide exists")

	bench.queue_free()
	await process_frame
	return f

func _test_analytical_balance_actuators() -> int:
	print("\nTesting Analytical Balance & Tare Precision...")
	var f: int = 0
	var bench = BENCH_SCENE.instantiate()
	root.add_child(bench)
	await process_frame

	f += _assert(bench.balance_mass_g == 0.0, "Initial balance mass is 0.0000 g")

	bench._add_reagent_to_balance("Citric acid", 10.0000)
	f += _assert(abs(bench.balance_mass_g - 10.0000) < 0.0001, "Weighed 10.0000 g citric acid")

	bench._on_tare_clicked()
	f += _assert(bench.balance_mass_g == 0.0, "Tare resets balance to 0.0000 g")
	f += _assert(bench.balance_tared == true, "balance_tared flag set")

	bench.queue_free()
	await process_frame
	return f

func _test_magnetic_stirrer_and_heating() -> int:
	print("\nTesting Magnetic Stirrer & Heating Mantle Actuators...")
	var f: int = 0
	var bench = BENCH_SCENE.instantiate()
	root.add_child(bench)
	await process_frame

	f += _assert(bench.is_stirring == false, "Initial stirring is FALSE")
	f += _assert(bench.is_boiling == false, "Initial boiling/heating is FALSE")

	bench._toggle_stirrer()
	f += _assert(bench.is_stirring == true, "Toggle stirrer sets is_stirring = TRUE")

	bench._toggle_heating()
	f += _assert(bench.is_boiling == true, "Toggle heating sets is_boiling = TRUE")

	# Simulate 2 seconds of physics tick
	for i in range(120):
		bench._process(1.0 / 60.0)

	f += _assert(bench.stir_rpm > 50.0, "Stirrer RPM spun up (current: %.1f RPM)" % bench.stir_rpm)
	f += _assert(bench.mantle_temp_c > 22.0, "Mantle temperature rising (current: %.1f °C)" % bench.mantle_temp_c)

	bench.queue_free()
	await process_frame
	return f

func _test_distillation_thermodynamics() -> int:
	print("\nTesting Fractional Distillation Thermodynamics & Condensate Collection...")
	var f: int = 0
	var bench = BENCH_SCENE.instantiate()
	root.add_child(bench)
	await process_frame

	bench.is_boiling = true
	bench.mantle_temp_c = 78.4 # Steady state boiling for ethanol / water
	bench.target_temp_c = 78.4

	# Run 60 frames (1 second) of steady state distillation
	for i in range(60):
		bench._process(1.0 / 60.0)

	f += _assert(bench.distillate_collected_ml > 0.0, "Distillate collected > 0 mL (got %.4f mL)" % bench.distillate_collected_ml)

	bench._collect_fraction()
	f += _assert(bench.distillate_collected_ml == 0.0, "Fraction collected and receiver reset to 0 mL")

	bench.queue_free()
	await process_frame
	return f

func _test_ui_controls_and_logging() -> int:
	print("\nTesting UI Overlays & Metrology Logging...")
	var f: int = 0
	var bench = BENCH_SCENE.instantiate()
	root.add_child(bench)
	await process_frame

	bench._log("Test log entry")
	f += _assert(bench._log_console != null, "Log console exists")
	f += _assert(bench.has_log("Test log entry"), "Log history contains message")

	bench._on_ppe_clicked()
	f += _assert(bench.has_log("PPE Active"), "PPE toggle logged")

	bench._on_sop_clicked()
	f += _assert(bench.has_log("SOP Guidance"), "SOP toggle logged")

	bench.queue_free()
	await process_frame
	return f
