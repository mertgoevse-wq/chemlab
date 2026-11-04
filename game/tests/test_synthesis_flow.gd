# Athanor Ascension — synthesis terminal integration test
# Drives the actual scene, submits a valid batch, checks the assay and the XP ledger.
extends SceneTree

const SCENE_PATH := "res://scenes/laboratories/synthesis_lab.tscn"


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var packed := load(SCENE_PATH)
	if packed == null:
		printerr("FAIL: cannot load synthesis scene")
		quit(1)
		return
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame

	# A technically correct run: protocol default charge, 70 C, full reflux,
	# hood on, all PPE, seeded recrystallisation.
	scene._mass_g = 13.8
	scene._anhydride_ml = 14.2
	scene._catalyst_drops = 5
	scene._stir_rpm = 450.0
	scene._temp_c = 70.0
	scene._reflux_min = 20.0
	scene._hood = true
	scene._ice_c = 2.0
	scene._water_ml = 30.0
	scene._ethanol_ml = 15.0
	scene._seeded = true
	scene._ppe = {"goggles": true, "gloves": true, "coat": true}
	scene._reflux_done = true

	var skills := root.get_node_or_null("SkillManager")
	var before := 0
	if skills != null:
		before = int(skills.get_xp("chemistry"))

	var result: Dictionary = scene.submit_batch()
	await process_frame

	var after := 0
	if skills != null:
		after = int(skills.get_xp("chemistry"))

	var stars := int(result.get("stars", 0))
	var xp := int(result.get("xp_awarded", 0))
	var purity := float(result.get("purity", 0.0))
	var yield_g := float(result.get("yield_g", 0.0))
	var safety := bool(result.get("safety_pass", false))
	var submitted := bool(scene._submitted)

	print("purity=%.2f yield=%.2f stars=%d xp=%d before=%d after=%d safety=%s submitted=%s" % [
		purity, yield_g, stars, xp, before, after, str(safety), str(submitted)
	])

	var failures: Array[String] = []
	if not bool(result.get("ok", false)):
		failures.append("batch evaluation failed: %s" % str(result.get("error", "")))
	if purity < 95.0:
		failures.append("purity %.1f < 95" % purity)
	if stars < 2:
		failures.append("stars %d < 2" % stars)
	if xp <= 0:
		failures.append("no chemistry XP awarded")
	if skills != null and after != before + xp:
		failures.append("XP ledger mismatch: %d -> %d, expected +%d" % [before, after, xp])
	if not safety:
		failures.append("safety gate failed on a valid batch")
	if not submitted:
		failures.append("scene did not lock the submitted batch")

	# Double submission must not mint XP.
	var second: Dictionary = scene.submit_batch()
	await process_frame
	var after_second := 0
	if skills != null:
		after_second = int(skills.get_xp("chemistry"))
	if bool(second.get("ok", true)):
		failures.append("second submit was accepted")
	if after_second != after:
		failures.append("second submit changed XP: %d -> %d" % [after, after_second])

	if failures.is_empty():
		print("PASS  synthesis terminal flow awards XP exactly once")
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL  %s" % failure)
		quit(1)
