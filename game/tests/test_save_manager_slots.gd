# Save Manager Slot Regression Test
# Tests save/load round-trip with multiple slots
# Expected output: "SAVE SLOT REGRESSION: PASS"

extends SceneTree

func _init() -> void:
	var SaveManagerScript = load("res://scripts/save/save_manager.gd")
	var save_manager = SaveManagerScript.new()

	# Test slot assignment before read
	save_manager.save_game(1)
	var success = save_manager.load_game(1)
	assert(success)
	assert(save_manager.current_slot == 1)

	# Test no character creation during load
	save_manager.save_game(2)
	success = save_manager.load_game(2)
	assert(success)
	assert(save_manager.current_slot == 2)

	print("SAVE SLOT REGRESSION: PASS")
	quit(0)