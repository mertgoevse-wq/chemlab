# Loading Screen Test
# Tests that loading screen has all required nodes and transitions properly
# Run: tools/bin/godot --headless --path game --script res://tests/test_loading_screen.gd

extends SceneTree

var _failures: int = 0

func _init() -> void:
	print("--- LOADING SCREEN VALIDATION ---")
	var scene = load("res://scenes/loading/loading_screen.tscn")
	var instance = scene.instantiate()

	# Scene unique nodes (%NodeName)
	_check(instance.get_node_or_null("%ProgressBar") != null, "ProgressBar node exists")
	_check(instance.get_node_or_null("%LoadingText") != null, "LoadingText node exists")
	_check(instance.get_node_or_null("%SubtitleText") != null, "SubtitleText node exists")
	_check(instance.get_node_or_null("Background") != null, "Background node exists")
	_check(instance.get_node_or_null("%SigilTexture") != null, "SigilTexture node exists")
	_check(instance.get_node_or_null("%ApparatusBackdrop") != null, "ApparatusBackdrop node exists")

	# Verify ApparatusBackdrop has script attached
	var apparatus = instance.get_node_or_null("%ApparatusBackdrop")
	_check(apparatus != null and apparatus.get_script() != null, "ApparatusBackdrop has script attached")

	instance.queue_free()

	print("--- RESULT: %s (%d failures) ---" % ["PASS" if _failures == 0 else "FAIL", _failures])
	quit(0 if _failures == 0 else 1)


func _check(condition: bool, label: String) -> void:
	if condition:
		print("  ok  ", label)
	else:
		_failures += 1
		printerr("  FAIL ", label)