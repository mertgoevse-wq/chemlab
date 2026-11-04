# Athanor Ascension — aspirin synthesis model tests
# Verifies the GDD numbers, not just that the script runs.
extends SceneTree

const Chem = preload("res://scripts/labs/synthesis_chemistry.gd")


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var failures: Array[String] = []

	var good: Dictionary = Chem.evaluate({
		"salicylic_mass_g": 13.8,
		"anhydride_ml": 14.2,
		"catalyst_drops": 5,
		"stir_rpm": 450.0,
		"reflux_temp_c": 70.0,
		"reflux_min": 20.0,
		"fume_hood": true,
		"ice_bath_c": 2.0,
		"quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0,
		"seed_crystal": true,
		"ppe": true
	})

	if not bool(good.get("ok", false)):
		failures.append("valid batch was rejected")
	if absf(float(good.get("theoretical_g", 0.0)) - 18.0) > 0.05:
		failures.append("theoretical yield %.3f g != 18.0 g" % float(good.get("theoretical_g", 0.0)))
	if absf(float(good.get("equivalents", 0.0)) - 1.506) > 0.02:
		failures.append("equivalents %.3f != 1.506" % float(good.get("equivalents", 0.0)))
	if float(good.get("purity", 0.0)) < 97.0:
		failures.append("optimal purity %.1f %% < 97 %%" % float(good.get("purity", 0.0)))
	if float(good.get("yield_g", 0.0)) < 14.0:
		failures.append("optimal yield %.2f g < 14 g" % float(good.get("yield_g", 0.0)))
	if absf(float(good.get("melting_point_c", 0.0)) - 135.5) > 1.0:
		failures.append("optimal melting point %.2f C drifted from 135.5" % float(good.get("melting_point_c", 0.0)))
	if int(good.get("stars", 0)) != 3:
		failures.append("optimal batch did not earn 3 stars (%d)" % int(good.get("stars", 0)))
	if not bool(good.get("safety_pass", false)):
		failures.append("optimal batch failed the safety gate")

	var no_catalyst: Dictionary = Chem.evaluate({
		"salicylic_mass_g": 13.8, "anhydride_ml": 14.2, "catalyst_drops": 0,
		"stir_rpm": 450.0, "reflux_temp_c": 70.0, "reflux_min": 20.0,
		"fume_hood": true, "ice_bath_c": 2.0, "quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0, "seed_crystal": true, "ppe": true
	})
	if float(no_catalyst.get("purity", 100.0)) >= 80.0:
		failures.append("missing catalyst still yielded %.1f %% purity" % float(no_catalyst.get("purity", 0.0)))
	if not (no_catalyst.get("flags", []) as Array).has("MISSING_CATALYST"):
		failures.append("missing catalyst flag not reported")

	var no_hood: Dictionary = Chem.evaluate({
		"salicylic_mass_g": 13.8, "anhydride_ml": 14.2, "catalyst_drops": 5,
		"stir_rpm": 450.0, "reflux_temp_c": 70.0, "reflux_min": 20.0,
		"fume_hood": false, "ice_bath_c": 2.0, "quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0, "seed_crystal": true, "ppe": true
	})
	if bool(no_hood.get("safety_pass", true)):
		failures.append("open-bench batch passed the safety gate")

	var overheated: Dictionary = Chem.evaluate({
		"salicylic_mass_g": 13.8, "anhydride_ml": 14.2, "catalyst_drops": 5,
		"stir_rpm": 450.0, "reflux_temp_c": 105.0, "reflux_min": 20.0,
		"fume_hood": true, "ice_bath_c": 2.0, "quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0, "seed_crystal": true, "ppe": true
	})
	if float(overheated.get("purity", 100.0)) >= float(good.get("purity", 0.0)):
		failures.append("overheating did not reduce purity")
	if not (overheated.get("flags", []) as Array).has("TARRING"):
		failures.append("tarring flag missing above 85 C")

	var limiting: Dictionary = Chem.evaluate({
		"salicylic_mass_g": 13.8, "anhydride_ml": 7.0, "catalyst_drops": 5,
		"stir_rpm": 450.0, "reflux_temp_c": 70.0, "reflux_min": 20.0,
		"fume_hood": true, "ice_bath_c": 2.0, "quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0, "seed_crystal": true, "ppe": true
	})
	if str(limiting.get("limiting_reagent", "")) != "acetic anhydride":
		failures.append("7 mL anhydride should be limiting")
	if float(limiting.get("theoretical_g", 0.0)) >= 18.0:
		failures.append("limiting anhydride did not cap theoretical yield")

	print("good: theoretical=%.3f eq=%.3f purity=%.1f yield=%.2f mp=%.2f stars=%d" % [
		float(good.get("theoretical_g", 0.0)), float(good.get("equivalents", 0.0)),
		float(good.get("purity", 0.0)), float(good.get("yield_g", 0.0)),
		float(good.get("melting_point_c", 0.0)), int(good.get("stars", 0))
	])
	print("no_catalyst purity=%.1f | no_hood safety=%s | overheat purity=%.1f" % [
		float(no_catalyst.get("purity", 0.0)), str(no_hood.get("safety_pass", true)),
		float(overheated.get("purity", 0.0))
	])

	if failures.is_empty():
		print("PASS  synthesis chemistry model")
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL  %s" % failure)
		quit(1)
