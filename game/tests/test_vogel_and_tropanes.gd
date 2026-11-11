# Athanor Ascension — Test Vogel, Tropane Alkaloids & Expanded Syntheses
# Headless verification of Vogel's Practical Organic Chemistry, Tropane Alkaloids,
# and extended PiHKAL/TiHKAL catalog entries.
# Run: tools/bin/godot --headless --path game --script res://tests/test_vogel_and_tropanes.gd

extends SceneTree

const Catalog = preload("res://scripts/labs/synthesis_catalog.gd")
const Chem = preload("res://scripts/labs/synthesis_chemistry.gd")

func _init() -> void:
	print("--- Running Test Vogel, Tropane Alkaloids & Expanded Syntheses ---")
	var failures: int = 0

	failures += _test_catalog_categories()
	failures += _test_tropane_alkaloid_entries()
	failures += _test_vogel_classical_entries()
	failures += _test_natural_product_entries()
	failures += _test_expanded_pihkal_tihkal()
	failures += _test_synthesis_chemistry_evaluation()

	if failures == 0:
		print("SUCCESS: All Vogel, Tropane & Expanded Synthesis tests passed (0 failures).")
		quit(0)
	else:
		printerr("FAILED: %d synthesis catalog tests failed." % failures)
		quit(1)

func _assert(condition: bool, msg: String) -> int:
	if not condition:
		printerr("  [FAIL] %s" % msg)
		return 1
	print("  [PASS] %s" % msg)
	return 0

func _test_catalog_categories() -> int:
	print("\nTesting Catalog Categories...")
	var f: int = 0
	var cats := Catalog.get_categories()
	f += _assert(cats.has("Industrial APIs"), "Has Industrial APIs category")
	f += _assert(cats.has("Tropane Alkaloids & Classic Syntheses"), "Has Tropane Alkaloids category")
	f += _assert(cats.has("Classical Organic & Dyes (Vogel)"), "Has Classical Organic & Dyes category")
	f += _assert(cats.has("Natural Product Isolation & Extractions"), "Has Natural Products category")
	f += _assert(cats.has("PiHKAL Phenethylamines"), "Has PiHKAL category")
	f += _assert(cats.has("TiHKAL Tryptamines"), "Has TiHKAL category")
	return f

func _test_tropane_alkaloid_entries() -> int:
	print("\nTesting Tropane Alkaloid Syntheses...")
	var f: int = 0
	var tropinone := Catalog.get_protocol("robinson_tropinone")
	f += _assert(not tropinone.is_empty(), "Robinson Tropinone protocol loaded")
	f += _assert(str(tropinone.get("name", "")) == "Tropinone", "Name is Tropinone")
	f += _assert(float(tropinone.get("mw", 0.0)) > 139.0, "Molecular weight is ~139.19 g/mol")

	var atropine := Catalog.get_protocol("atropine_total_synthesis")
	f += _assert(not atropine.is_empty(), "Atropine protocol loaded")
	f += _assert(str(atropine.get("name", "")).contains("Atropine"), "Name contains Atropine (got '%s')" % str(atropine.get("name", "")))

	var scopolamine := Catalog.get_protocol("scopolamine_datura_isolation")
	f += _assert(not scopolamine.is_empty(), "Scopolamine protocol loaded")
	f += _assert(str(scopolamine.get("name", "")).contains("Scopolamine"), "Name contains Scopolamine (got '%s')" % str(scopolamine.get("name", "")))
	return f

func _test_vogel_classical_entries() -> int:
	print("\nTesting Vogel Classical Organic Syntheses...")
	var f: int = 0
	var grignard := Catalog.get_protocol("triphenylmethanol_grignard")
	f += _assert(not grignard.is_empty(), "Triphenylmethanol Grignard protocol loaded")
	f += _assert(str(grignard.get("name", "")) == "Triphenylmethanol", "Name is Triphenylmethanol")

	var diels_alder := Catalog.get_protocol("anthracene_diels_alder")
	f += _assert(not diels_alder.is_empty(), "Anthracene Diels-Alder protocol loaded")

	var fischer_indole := Catalog.get_protocol("fischer_tetrahydrocarbazole")
	f += _assert(not fischer_indole.is_empty(), "Tetrahydrocarbazole Fischer Indole protocol loaded")

	var sandmeyer := Catalog.get_protocol("sandmeyer_chlorobenzene")
	f += _assert(not sandmeyer.is_empty(), "Sandmeyer Chlorobenzene protocol loaded")

	var cannizzaro := Catalog.get_protocol("cannizzaro_benzaldehyde")
	f += _assert(not cannizzaro.is_empty(), "Cannizzaro Benzaldehyde protocol loaded")
	return f

func _test_natural_product_entries() -> int:
	print("\nTesting Natural Product Extractions...")
	var f: int = 0
	var belladonna := Catalog.get_protocol("belladonna_alkaloid_extraction")
	f += _assert(not belladonna.is_empty(), "Belladonna Tropane Extraction loaded")

	var harmala := Catalog.get_protocol("manske_harmala_extraction")
	f += _assert(not harmala.is_empty(), "Harmine & Harmaline Extraction loaded")

	var quinine := Catalog.get_protocol("quinine_cinchona_extraction")
	f += _assert(not quinine.is_empty(), "Cinchona Bark Quinine Extraction loaded")
	return f

func _test_expanded_pihkal_tihkal() -> int:
	print("\nTesting Expanded PiHKAL & TiHKAL Catalogs...")
	var f: int = 0
	var pihkal_prots := Catalog.get_protocols_in_category("PiHKAL Phenethylamines")
	f += _assert(pihkal_prots.size() >= 20, "PiHKAL catalog has >= 20 compounds (found %d)" % pihkal_prots.size())

	var two_c_c := Catalog.get_protocol("2c-c")
	f += _assert(not two_c_c.is_empty(), "2C-C protocol loaded")

	var doi := Catalog.get_protocol("doi")
	f += _assert(not doi.is_empty(), "DOI protocol loaded")

	var tihkal_prots := Catalog.get_protocols_in_category("TiHKAL Tryptamines")
	f += _assert(tihkal_prots.size() >= 15, "TiHKAL catalog has >= 15 compounds (found %d)" % tihkal_prots.size())

	var four_ho_met := Catalog.get_protocol("4-ho-met")
	f += _assert(not four_ho_met.is_empty(), "4-HO-MET protocol loaded")

	var ibogaine := Catalog.get_protocol("ibogaine")
	f += _assert(not ibogaine.is_empty(), "Ibogaine protocol loaded")
	return f

func _test_synthesis_chemistry_evaluation() -> int:
	print("\nTesting Chemistry Evaluation of New Protocol (Robinson Tropinone)...")
	var f: int = 0
	var tropinone := Catalog.get_protocol("robinson_tropinone")
	var rA: Dictionary = tropinone.get("reagent_a", {})
	var rB: Dictionary = tropinone.get("reagent_b", {})
	var reflux: Dictionary = tropinone.get("reflux", {})

	var params := {
		"protocol": tropinone,
		"protocol_id": "robinson_tropinone",
		"reagent_a_mass": float(rA.get("default", 13.2)),
		"reagent_b_amount": float(rB.get("default", 50.0)),
		"catalyst_drops": 5,
		"stir_rpm": 450.0,
		"reflux_temp_c": float(reflux.get("default_temp", 75.0)),
		"reflux_min": float(reflux.get("default_min", 25.0)),
		"fume_hood": true,
		"ice_bath_c": 2.0,
		"quench_water_ml": 30.0,
		"recryst_ethanol_ml": 15.0,
		"seed_crystal": true,
		"ppe": true
	}

	var eval_res: Dictionary = Chem.evaluate(params)
	f += _assert(bool(eval_res.get("ok", false)), "Batch evaluation succeeded for Robinson Tropinone")
	f += _assert(float(eval_res.get("purity", 0.0)) > 90.0, "Purity > 90%% (got %.2f)" % float(eval_res.get("purity", 0.0)))
	f += _assert(float(eval_res.get("yield_g", 0.0)) > 0.0, "Non-zero product yield (got %.2f g)" % float(eval_res.get("yield_g", 0.0)))
	return f
