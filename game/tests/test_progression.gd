# Athanor Ascension — progression and titration verification
# Run: tools/bin/godot --headless --path game --script res://tests/test_progression.gd
extends SceneTree

const SKILL_SCRIPT := "res://scripts/progression/skill_manager.gd"
const CHEM := preload("res://scripts/labs/titration_chemistry.gd")

var _passed: int = 0
var _failed: int = 0


func _init() -> void:
	print("\n>>> [Progression] verifying XP curve, milestones and titration equilibrium")
	var manager = load(SKILL_SCRIPT).new()
	manager._load_tracks()
	manager._build_curve()

	_check("curve level 2 = 83 XP", manager.xp_to_reach_level(2), 83)
	_check("curve level 5 = 388 XP", manager.xp_to_reach_level(5), 388)
	_check("curve level 10 = 1154 XP", manager.xp_to_reach_level(10), 1154)
	_check("curve level 50 = 101333 XP", manager.xp_to_reach_level(50), 101333)
	_check("curve level 99 = 13034431 XP", manager.xp_to_reach_level(99), 13034431)
	_check("level_for_xp(1153) = 9", manager.level_for_xp(1153), 9)
	_check("level_for_xp(1154) = 10", manager.level_for_xp(1154), 10)

	var award: Dictionary = manager.add_xp("chemistry", 1154, "test")
	_check("award level_after = 10", int(award.get("level_after", 0)), 10)
	_check("milestone at level 10 unlocked", (award.get("milestones", []) as Array).size(), 1)
	_check("chemistry level = 10", manager.get_level("chemistry"), 10)
	_check("apparatus unlocked at level 10 > 0", manager.get_unlocked_apparatus("chemistry").size() > 0, true)
	_check("unknown skill rejected", bool(manager.add_xp("alchemy", 100).get("ok", true)), false)

	# Strong acid: pH 1.0 at 0 mL, 7.0 at equivalence.
	_check_close("HCl initial pH", CHEM.ph_at(0.1, 25.0, 0.1, 0.0, CHEM.STRONG_KA), 1.0, 0.02)
	_check_close("HCl pH at equivalence", CHEM.ph_at(0.1, 25.0, 0.1, 25.0, CHEM.STRONG_KA), 7.0, 0.05)
	# 0.01 mmol excess H+ in 49.9 mL -> 2.0e-4 M -> pH 3.70.
	_check_close("HCl pH at 24.9 mL", CHEM.ph_at(0.1, 25.0, 0.1, 24.9, CHEM.STRONG_KA), 3.70, 0.03)

	# Weak acid: buffer region, basic equivalence, later pH 8.2 endpoint.
	_check_close("acetic initial pH", CHEM.ph_at(0.1, 25.0, 0.1, 0.0, 1.8e-5), 2.87, 0.03)
	_check_close("acetic half-equivalence pH = pKa", CHEM.ph_at(0.1, 25.0, 0.1, 12.5, 1.8e-5), 4.74, 0.05)
	_check_close("acetic pH at equivalence", CHEM.ph_at_equivalence(0.1, 25.0, 0.1, 1.8e-5), 8.72, 0.06)
	var acetic_endpoint: float = CHEM.endpoint_ml(0.1, 25.0, 0.1, 1.8e-5, 8.2)
	_check("acetic endpoint near equivalence", acetic_endpoint > 24.9 and acetic_endpoint < 25.2, true)
	var hcl_endpoint: float = CHEM.endpoint_ml(0.1, 25.0, 0.1, CHEM.STRONG_KA, 8.2)
	_check("HCl endpoint just past equivalence", hcl_endpoint >= 25.0 and hcl_endpoint < 25.02, true)
	_check("indicator colourless at pH 4", CHEM.indicator_state(4.0), "colourless")
	_check("indicator pink at pH 9", CHEM.indicator_state(9.0), "persistent pink")
	_check("indicator magenta at pH 11", CHEM.indicator_state(11.0), "magenta overshoot")

	print("\n>>> [Progression] %d passed, %d failed" % [_passed, _failed])
	quit(0 if _failed == 0 else 1)


func _check(label: String, actual: Variant, expected: Variant) -> void:
	if actual == expected:
		print("PASS  %s" % label)
		_passed += 1
	else:
		printerr("FAIL  %s: got %s, expected %s" % [label, str(actual), str(expected)])
		_failed += 1


func _check_close(label: String, actual: float, expected: float, tolerance: float) -> void:
	if absf(actual - expected) <= tolerance:
		print("PASS  %s (%.4f)" % [label, actual])
		_passed += 1
	else:
		printerr("FAIL  %s: got %.4f, expected %.4f ± %.4f" % [label, actual, expected, tolerance])
		_failed += 1
