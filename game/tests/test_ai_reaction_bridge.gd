# Athanor Ascension — Test AI Reaction Bridge Integration
# Headless verification of AI reagent computation via SimulationBridge with offline fallback
# Run: tools/bin/godot --headless --path game --script res://tests/test_ai_reaction_bridge.gd

extends SceneTree

func _init() -> void:
	_run.call_deferred()

func _run() -> void:
	print("--- Running Test AI Reaction Bridge Integration ---")
	var failures: int = 0

	var bridge = root.get_node_or_null("SimulationBridge")
	if bridge == null:
		var bridge_script = load("res://scripts/chemistry/simulation_bridge.gd")
		bridge = bridge_script.new()
		root.add_child(bridge)
		await process_frame

	failures += _test_offline_ai_reaction_fallback(bridge)
	failures += _test_local_ai_endpoint_configuration(bridge)
	failures += _test_get_ai_providers(bridge)

	if failures == 0:
		print("SUCCESS: All AI reaction bridge tests passed (0 failures).")
		quit(0)
	else:
		printerr("FAILED: %d AI reaction bridge tests failed." % failures)
		quit(1)

func _assert(condition: bool, msg: String) -> int:
	if not condition:
		printerr("  [FAIL] %s" % msg)
		return 1
	print("  [PASS] %s" % msg)
	return 0

func _test_offline_ai_reaction_fallback(bridge: Node) -> int:
	print("\nTesting offline AI reaction fallback prediction...")
	var f: int = 0

	# Force embedded fallback to test deterministic local prediction
	bridge.force_embedded_fallback()

	var result = bridge.compute_ai_reaction(
		["salicylic_acid", "acetic_anhydride"],
		65.0,
		["h2so4"],
		"aspirin"
	)

	f += _assert(bool(result.get("success", false)), "AI reaction computation returned success")
	f += _assert(bool(result.get("fallback_used", false)), "Offline fallback appropriately flagged")

	var pred = result.get("prediction", {})
	f += _assert(pred.has("reaction_name"), "Prediction contains reaction_name")
	f += _assert("aspirin" in str(pred.get("reaction_name", "")).to_lower() or "aspirin" in str(pred.get("products", {})).to_lower(), "Reaction predicts aspirin synthesis")
	f += _assert(float(pred.get("enthalpy_kj_mol", 0.0)) < 0.0, "Reaction is exothermic (ΔH < 0)")
	f += _assert(float(pred.get("rate_constant_k", 0.0)) > 0.0, "Rate constant k > 0")
	return f

func _test_local_ai_endpoint_configuration(bridge: Node) -> int:
	print("\nTesting local AI endpoint registration...")
	var f: int = 0

	var recorded: Array = []
	var callback = func(resp: Dictionary):
		recorded.append(resp)

	bridge.configure_local_ai_endpoint("http://127.0.0.1:11434/v1", "llama3.2", 1, callback)
	var recorded_resp: Dictionary = recorded[0] if not recorded.is_empty() else {}
	f += _assert(recorded_resp.has("provider") or recorded_resp.has("status"), "Configured local AI callback executed")
	return f

func _test_get_ai_providers(bridge: Node) -> int:
	print("\nTesting get AI providers list...")
	var f: int = 0

	var recorded: Array = []
	var callback = func(resp: Dictionary):
		recorded.append(resp)

	bridge.get_ai_providers(callback)
	var recorded_resp: Dictionary = recorded[0] if not recorded.is_empty() else {}
	f += _assert(recorded_resp.has("providers") or recorded_resp.has("provider_order"), "AI providers list received")
	return f
