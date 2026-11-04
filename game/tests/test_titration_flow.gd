# Athanor Ascension — titration flow integration test
# Drives the real scene: deliver titrant, cross pH 8.2, submit, verify XP.
extends SceneTree

const SCENE_PATH := "res://scenes/laboratories/titration_practicum.tscn"


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var packed := load(SCENE_PATH)
	if packed == null:
		printerr("FAIL: cannot load titration scene")
		quit(1)
		return
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame

	var skills := root.get_node_or_null("SkillManager")
	var before := 0
	if skills != null:
		before = int(skills.get_xp("chemistry"))

	scene._add_volume(25.05)
	await process_frame
	var endpoint_ok: bool = float(scene._endpoint_ml) > 25.0 and float(scene._endpoint_ml) < 25.2
	scene._on_submit()
	await process_frame

	var after := 0
	if skills != null:
		after = int(skills.get_xp("chemistry"))
	var result: Dictionary = scene._last_result
	var stars := int(result.get("stars", 0))
	var xp := int(result.get("xp", 0))

	print("endpoint=%.4f target=%.4f error=%.4f stars=%d xp=%d before=%d after=%d" % [
		float(result.get("endpoint_ml", 0.0)),
		float(result.get("target_ml", 0.0)),
		float(result.get("error_ml", 0.0)),
		stars, xp, before, after
	])

	var ok := endpoint_ok and stars >= 2 and xp > 0 and (skills == null or after == before + xp)
	if ok:
		print("PASS  titration flow awards Chemistry XP")
		quit(0)
	else:
		printerr("FAIL  titration flow (endpoint_ok=%s stars=%d xp=%d delta=%d)" % [str(endpoint_ok), stars, xp, after - before])
		quit(1)
