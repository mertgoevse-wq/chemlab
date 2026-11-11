# Athanor Ascension — Synthesis Catalog & Multi-Protocol Chemistry Tests
# Verifies catalog loading of Industrial APIs, PiHKAL and TiHKAL,
# and verifies deterministic stoichiometric evaluation across different reaction types.
extends SceneTree

const Chem = preload("res://scripts/labs/synthesis_chemistry.gd")
const Catalog = preload("res://scripts/labs/synthesis_catalog.gd")


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var failures: Array[String] = []

	# 1. Verify Categories
	var categories: Array[String] = Catalog.get_categories()
	if not categories.has("Industrial APIs"):
		failures.append("Missing category 'Industrial APIs'")
	if not categories.has("PiHKAL Phenethylamines"):
		failures.append("Missing category 'PiHKAL Phenethylamines'")
	if not categories.has("TiHKAL Tryptamines"):
		failures.append("Missing category 'TiHKAL Tryptamines'")

	# 2. Verify Industrial Protocols
	var industrial: Array[Dictionary] = Catalog.get_protocols_in_category("Industrial APIs")
	if industrial.size() < 5:
		failures.append("Expected >= 5 industrial protocols, found %d" % industrial.size())

	# 3. Test Paracetamol Evaluation (Industrial API)
	var para_proto: Dictionary = Catalog.get_protocol("paracetamol")
	if para_proto.is_empty() or str(para_proto.get("id", "")) != "paracetamol":
		failures.append("Paracetamol protocol failed to load")
	else:
		var para_res: Dictionary = Chem.evaluate({
			"protocol": para_proto,
			"reagent_a_mass": 10.9, # 4-aminophenol (MW 109.13 -> ~0.10 mol)
			"reagent_b_amount": 10.2, # Acetic anhydride (MW 102.09, density 1.082 -> ~0.108 mol)
			"catalyst_drops": 5,
			"reflux_temp_c": 100.0,
			"reflux_min": 25.0,
			"stir_rpm": 500.0,
			"fume_hood": true,
			"ice_bath_c": 2.0,
			"quench_water_ml": 25.0,
			"recryst_ethanol_ml": 15.0,
			"seed_crystal": true,
			"ppe": true
		})
		if not bool(para_res.get("ok", false)):
			failures.append("Paracetamol evaluation failed: %s" % str(para_res.get("error", "")))
		if float(para_res.get("purity", 0.0)) < 95.0:
			failures.append("Paracetamol purity %.1f %% < 95.0 %%" % float(para_res.get("purity", 0.0)))
		if float(para_res.get("yield_g", 0.0)) < 10.0:
			failures.append("Paracetamol yield %.2f g < 10.0 g" % float(para_res.get("yield_g", 0.0)))
		print("Paracetamol evaluation: purity=%.1f%% yield=%.2fg stars=%d" % [
			float(para_res.get("purity", 0.0)),
			float(para_res.get("yield_g", 0.0)),
			int(para_res.get("stars", 0))
		])

	# 4. Test PiHKAL Phenethylamine Protocol (e.g. Mescaline or 2C-B)
	var pihkal_list: Array[Dictionary] = Catalog.get_protocols_in_category("PiHKAL Phenethylamines")
	if pihkal_list.is_empty():
		failures.append("PiHKAL protocol list is empty")
	else:
		var p_sample: Dictionary = pihkal_list[0]
		var p_res: Dictionary = Chem.evaluate({
			"protocol": p_sample,
			"reagent_a_mass": float(p_sample["reagent_a"]["default"]),
			"reagent_b_amount": float(p_sample["reagent_b"]["default"]),
			"catalyst_drops": 5,
			"reflux_temp_c": float(p_sample["reflux"]["default_temp"]),
			"reflux_min": float(p_sample["reflux"]["default_min"]),
			"stir_rpm": 450.0,
			"fume_hood": true,
			"ice_bath_c": 2.0,
			"quench_water_ml": 30.0,
			"recryst_ethanol_ml": 15.0,
			"seed_crystal": true,
			"ppe": true
		})
		if not bool(p_res.get("ok", false)):
			failures.append("PiHKAL %s evaluation failed" % str(p_sample.get("name", "")))
		print("PiHKAL sample (%s): purity=%.1f%% yield=%.2fg" % [
			str(p_sample.get("name", "")),
			float(p_res.get("purity", 0.0)),
			float(p_res.get("yield_g", 0.0))
		])

	# 5. Test TiHKAL Tryptamine Protocol
	var tihkal_list: Array[Dictionary] = Catalog.get_protocols_in_category("TiHKAL Tryptamines")
	if tihkal_list.is_empty():
		failures.append("TiHKAL protocol list is empty")
	else:
		var t_sample: Dictionary = tihkal_list[0]
		var t_res: Dictionary = Chem.evaluate({
			"protocol": t_sample,
			"reagent_a_mass": float(t_sample["reagent_a"]["default"]),
			"reagent_b_amount": float(t_sample["reagent_b"]["default"]),
			"catalyst_drops": 5,
			"reflux_temp_c": float(t_sample["reflux"]["default_temp"]),
			"reflux_min": float(t_sample["reflux"]["default_min"]),
			"stir_rpm": 450.0,
			"fume_hood": true,
			"ice_bath_c": 2.0,
			"quench_water_ml": 30.0,
			"recryst_ethanol_ml": 15.0,
			"seed_crystal": true,
			"ppe": true
		})
		if not bool(t_res.get("ok", false)):
			failures.append("TiHKAL %s evaluation failed" % str(t_sample.get("name", "")))
		print("TiHKAL sample (%s): purity=%.1f%% yield=%.2fg" % [
			str(t_sample.get("name", "")),
			float(t_res.get("purity", 0.0)),
			float(t_res.get("yield_g", 0.0))
		])

	if failures.is_empty():
		print("PASS  synthesis catalog and multi-protocol evaluation")
		quit(0)
	else:
		for f in failures:
			printerr("FAIL: ", f)
		quit(1)
