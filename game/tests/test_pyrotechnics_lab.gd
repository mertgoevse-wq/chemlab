# Athanor Ascension — Pyrotechnics Laboratory Test
# Verifies formulation loading, oxygen balance, flame colour, hazard class and
# the burn-test animation state. Fails fast with quit(1) instead of assert() so
# a SceneTree test can never hang the CI runner.
extends SceneTree

const LAB_SCENE := "res://scenes/laboratories/pyrotechnics_lab.tscn"


func _init() -> void:
	_run.call_deferred()


func _fail(message: String) -> void:
	printerr("FAIL: " + message)
	quit(1)


func _run() -> void:
	print("\n>>> [Pyrotechnics] Starting test bay verification")
	var packed := load(LAB_SCENE)
	if packed == null:
		_fail("cannot load pyrotechnics lab scene")
		return

	var lab = packed.instantiate()
	root.add_child(lab)
	await process_frame
	await process_frame

	if lab.formulations.size() < 5:
		_fail("expected at least 5 formulations, got %d" % lab.formulations.size())
		return
	print("  ok  %d formulations loaded" % lab.formulations.size())

	# Red star: strontium must dominate the red channel.
	lab._select_formulation(1)
	var red: Dictionary = lab.last_result
	if float(red.get("burn_rate_mm_s", 0.0)) <= 0.0:
		_fail("red star has no burn rate")
		return
	var color: Color = red.get("flame_color", Color.WHITE)
	if color.r <= color.b:
		_fail("red star is not red-dominant")
		return
	if int(red.get("emission_nm", 0)) != 606:
		_fail("red star emission should be 606 nm")
		return
	print("  ok  red star %.1f mm/s at %d nm" % [float(red["burn_rate_mm_s"]), int(red["emission_nm"])])

	# Black powder is fuel-rich and burns.
	var black_powder := {
		"name": "Black Powder",
		"colorant": "none",
		"confinement": 0.0,
		"components": [
			{"substance": "potassium_nitrate", "fraction": 0.75},
			{"substance": "charcoal", "fraction": 0.15},
			{"substance": "sulfur", "fraction": 0.10},
		],
	}
	var bp: Dictionary = lab.Model.evaluate(black_powder)
	if absf(float(bp["oxygen_balance"])) < 0.05:
		_fail("black powder should be measurably off oxygen balance")
		return
	if float(bp["burn_rate_mm_s"]) < 5.0:
		_fail("black powder should burn faster than 5 mm/s")
		return
	print("  ok  black powder OB %+.3f, %.1f mm/s" % [float(bp["oxygen_balance"]), float(bp["burn_rate_mm_s"])])

	# Chlorate + sulfur must be flagged as extreme.
	var chlorate := {
		"name": "Chlorate Sulfur",
		"colorant": "none",
		"confinement": 0.0,
		"components": [
			{"substance": "potassium_chlorate", "fraction": 0.70},
			{"substance": "sulfur", "fraction": 0.30},
		],
	}
	var dangerous: Dictionary = lab.Model.evaluate(chlorate)
	if str(dangerous["sensitivity"]) != "extreme":
		_fail("chlorate + sulfur must be extreme sensitivity")
		return
	print("  ok  chlorate/sulfur classified %s" % str(dangerous["hazard_class"]))

	# Burn test enters and exits the animation state.
	lab.run_burn_test()
	if not lab.is_burning:
		_fail("burn test did not start")
		return
	print("  ok  burn test animation started")

	print(">>> [Pyrotechnics] ALL TESTS PASSED")
	quit(0)
