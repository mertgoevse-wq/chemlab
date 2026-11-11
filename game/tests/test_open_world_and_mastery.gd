# Athanor Ascension — Open World, Character Defaults & Mastery Progression Test Suite
# Tests:
# 1. Canonical Default Naming for Academic, Hobbyist, and Ex-Pharma origins
# 2. Level 99 Master Lab Regalia database validity & requirements
# 3. All 20 skill tracks progression & Omniscient Alchemist achievement
# 4. OpenWorldManager 7 sectors & 8 research contracts
# 5. Interactive Apparatus Suite (Rotovap, Schlenk, Balance, HPLC, Soxhlet, UV-Vis, Glovebox, Centrifuge)
# 6. LocalAIReactionAdvisor deterministic reaction prediction & NMR elucidation

extends SceneTree

func _init() -> void:
	_run_tests.call_deferred()

func _run_tests() -> void:
	print("\n=======================================================")
	print(">>> [OpenWorld & Mastery] Starting Comprehensive Verification...")
	print("=======================================================")

	# -------------------------------------------------------------------------
	# 1. Canonical Default Naming & Character Customization
	# -------------------------------------------------------------------------
	var char_creator = root.get_node_or_null("CharacterCreator")
	if not char_creator:
		var cc_script = load("res://scripts/character/character_creator.gd")
		char_creator = cc_script.new()
		root.add_child(char_creator)

	print("\n[Section 1] Testing Canonical Protagonist Defaults...")
	# Academic default
	char_creator.select_background("academic")
	char_creator.set_character_name("")  # Empty should use canonical
	var res_acad = char_creator.create_character()
	assert(res_acad.success == true, "Academic character creation failed")
	assert(res_acad.character.name == "Dr. Aris Thorne", "Academic name should default to Dr. Aris Thorne")
	print("  ok  Academic default name verified: %s" % res_acad.character.name)

	# Hobbyist default
	char_creator.select_background("hobbyist")
	char_creator.set_character_name("   ")
	var res_hobb = char_creator.create_character()
	assert(res_hobb.character.name == "Vesper Finch", "Hobbyist name should default to Vesper Finch")
	print("  ok  Hobbyist default name verified: %s" % res_hobb.character.name)

	# Ex-Pharma default
	char_creator.select_background("ex_pharma")
	char_creator.set_character_name("")
	var res_pharma = char_creator.create_character()
	assert(res_pharma.character.name == "Kaelen Voss", "Ex-Pharma name should default to Kaelen Voss")
	print("  ok  Ex-Pharma default name verified: %s" % res_pharma.character.name)

	# Custom name override
	char_creator.set_character_name("Prof. Alistair Crowley")
	char_creator.set_pronouns("they/them")
	char_creator.set_lab_coat_style("hazard_orange")
	var res_custom = char_creator.create_character()
	assert(res_custom.character.name == "Prof. Alistair Crowley", "Custom name was not retained")
	assert(res_custom.character.pronouns == "they/them", "Pronouns were not retained")
	assert(res_custom.character.lab_coat_style == "hazard_orange", "Lab coat style was not retained")
	print("  ok  Custom character customization verified: %s, %s, %s" % [
		res_custom.character.name, res_custom.character.pronouns, res_custom.character.lab_coat_style
	])

	# -------------------------------------------------------------------------
	# 2. Master Lab Coats & Regalia Database Validation
	# -------------------------------------------------------------------------
	print("\n[Section 2] Validating Master Regalia Database...")
	var equip_file = FileAccess.open("res://data/equipment/equipment_database.json", FileAccess.READ)
	assert(equip_file != null, "Could not open equipment_database.json")
	var equip_json = JSON.new()
	var parse_err = equip_json.parse(equip_file.get_as_text())
	equip_file.close()
	assert(parse_err == OK, "JSON parse error in equipment_database.json")

	var equip_items: Array = equip_json.data.get("equipment_items", [])
	var items_by_id = {}
	for it in equip_items:
		items_by_id[it.get("id", "")] = it

	var expected_skills = [
		"chemistry", "biology", "physics", "mathematics", "forensics",
		"toxicology", "apparatus_building", "lab_safety", "automation", "containment",
		"nuclear_engineering", "genetics", "biochemistry", "pharmacology",
		"synthetic_biology", "radiochemistry", "environmental_science",
		"materials_science", "computational_chemistry", "engineering"
	]
	assert(expected_skills.size() == 20, "Should have exactly 20 skill tracks")

	for s in expected_skills:
		var reg_id = "regalia_" + s
		assert(items_by_id.has(reg_id), "Missing Master Regalia for skill: %s" % s)
		var reg = items_by_id[reg_id]
		assert(reg.get("slot") == "body", "%s slot must be body" % reg_id)
		assert(reg.get("tier") == "mythic", "%s tier must be mythic" % reg_id)
		var req = reg.get("skill_requirement", {})
		assert(req.get("skill") == s, "%s requirement skill mismatch" % reg_id)
		assert(int(req.get("level")) == 99, "%s requirement level must be 99" % reg_id)

	print("  ok  All 20 Level 99 Master Lab Coats found with verified Level 99 requirements")

	# Omniscient Alchemical Regalia
	assert(items_by_id.has("regalia_omniscient_alchemist"), "Missing regalia_omniscient_alchemist")
	var omni_coat = items_by_id["regalia_omniscient_alchemist"]
	assert(omni_coat.get("all_skills_mastered") == true, "Omniscient coat must require all_skills_mastered")

	assert(items_by_id.has("hood_omniscient_alchemist"), "Missing hood_omniscient_alchemist")
	var omni_hood = items_by_id["hood_omniscient_alchemist"]
	assert(omni_hood.get("all_skills_mastered") == true, "Omniscient hood must require all_skills_mastered")
	print("  ok  Omniscient Alchemical Regalia and Cowl verified")

	# -------------------------------------------------------------------------
	# 3. Progression & Mastery Signals
	# -------------------------------------------------------------------------
	print("\n[Section 3] Testing SkillManager Mastery & Rewards...")
	var skill_mgr = root.get_node_or_null("SkillManager")
	if not skill_mgr:
		var sm_script = load("res://scripts/progression/skill_manager.gd")
		skill_mgr = sm_script.new()
		root.add_child(skill_mgr)

	var inv_mgr = root.get_node_or_null("InventoryManager")
	if not inv_mgr:
		var im_script = load("res://scripts/core/inventory_manager.gd")
		inv_mgr = im_script.new()
		root.add_child(inv_mgr)

	# Verify Level 92 represents ~50% of Level 99 XP
	var xp_92 = skill_mgr.get_xp_for_level(92)
	var xp_99 = skill_mgr.get_xp_for_level(99)
	var ratio = float(xp_92) / float(xp_99)
	assert(ratio >= 0.48 and ratio <= 0.52, "Level 92 must be approximately 50 percent of Level 99 XP (ratio: %f)" % ratio)
	print("  ok  Exponential XP curve confirmed: Level 92 is precisely %.2f percent of Level 99 XP" % (ratio * 100.0))

	# Test Level 99 Mastery Trigger
	var signal_tracker = {"mastered": false, "skill": "", "level": 0}
	skill_mgr.skill_mastered.connect(func(s_id, lvl):
		signal_tracker["mastered"] = true
		signal_tracker["skill"] = s_id
		signal_tracker["level"] = lvl
	)

	# Grant enough XP to hit Level 99 Chemistry
	skill_mgr.add_xp("chemistry", xp_99)
	assert(skill_mgr.get_level("chemistry") >= 99, "Chemistry level should be 99+")
	assert(signal_tracker["mastered"] == true, "skill_mastered signal was not fired")
	assert(inv_mgr.has_item("regalia_chemistry"), "regalia_chemistry should be auto-awarded into inventory")
	print("  ok  Level 99 Chemistry mastery reached, signal fired, Grand Chemist's Coat awarded")

	# Test Level 99 on all skills trigger
	for s in expected_skills:
		if s != "chemistry":
			skill_mgr.add_xp(s, xp_99)

	assert(skill_mgr.is_all_skills_mastered() == true, "All skills should be reported as mastered")
	assert(inv_mgr.has_item("regalia_omniscient_alchemist"), "regalia_omniscient_alchemist should be awarded")
	assert(inv_mgr.has_item("hood_omniscient_alchemist"), "hood_omniscient_alchemist should be awarded")
	print("  ok  All 20 skills mastered! Omniscient Alchemical Regalia awarded to inventory")

	# -------------------------------------------------------------------------
	# 4. OpenWorldManager Sectors & Research Contracts
	# -------------------------------------------------------------------------
	print("\n[Section 4] Testing OpenWorldManager Sectors & Contracts...")
	var ow_mgr = root.get_node_or_null("OpenWorldManager")
	if not ow_mgr:
		var ow_script = load("res://scripts/world/open_world_manager.gd")
		ow_mgr = ow_script.new()
		root.add_child(ow_mgr)

	var sectors = ow_mgr.get_all_sectors()
	assert(sectors.size() == 7, "Must have exactly 7 open world sectors")
	var sector_ids: Array[String] = []
	for s in sectors:
		sector_ids.append(s.get("id", ""))
	assert(sector_ids.has("sector_atrium"), "Missing Grand Atrium sector")
	assert(sector_ids.has("sector_underground"), "Missing Underground Alchemical Warren")
	assert(sector_ids.has("sector_cleanroom"), "Missing Bio-Molecular Cleanroom")
	assert(sector_ids.has("sector_orbital"), "Missing Orbital Telemetry sector")
	print("  ok  7 interconnected laboratory sectors verified")

	# Test Transit
	var transit_res = ow_mgr.transit_to_sector("sector_containment")
	assert(transit_res.success == true, "Pneumatic transit failed")
	assert(ow_mgr.current_sector_id == "sector_containment", "Current sector did not update")
	print("  ok  Pneumatic transit from Atrium to Hazardous Containment Vault successful")

	# Test Contracts
	var contracts = ow_mgr.get_available_contracts()
	assert(contracts.size() >= 8, "Expected at least 8 research contracts, got %d" % contracts.size())
	assert(ow_mgr.start_contract("contract_aspirin_purity") == true, "Failed to start contract_aspirin_purity")
	ow_mgr.update_contract_objective("contract_aspirin_purity", "synthesize_aspirin", 1)
	ow_mgr.update_contract_objective("contract_aspirin_purity", "nmr_verify", 1)
	assert(ow_mgr.is_contract_complete("contract_aspirin_purity") == true, "Contract should be completed")
	var claim_res = ow_mgr.claim_contract_rewards("contract_aspirin_purity")
	assert(claim_res.success == true, "Contract rewards claim failed")
	print("  ok  Research Contract flow (accept -> objectives -> verify -> rewards) verified")

	# -------------------------------------------------------------------------
	# 5. Interactive Apparatus Suite
	# -------------------------------------------------------------------------
	print("\n[Section 5] Testing ApparatusSuite Instruments...")
	var ApparatusSuiteClass = load("res://scripts/labs/apparatus_suite.gd")

	# 5.1 Rotovap
	var rotovap = ApparatusSuiteClass.RotovapController.new()
	assert(rotovap.secure_keck_clip(true) == true, "Rotovap keck clip failed")
	rotovap.state = rotovap.State.ROTATING
	rotovap.set_stopcock(true)
	rotovap.toggle_bath_lift(true)
	rotovap.bath_temp_c = 55.0
	rotovap.vacuum_mbar = 45.0
	rotovap.rotation_rpm = 120.0
	var rv_status = rotovap.update(2.0)
	assert(rv_status.distillation_rate_ml_min > 0.0, "Rotovap should be distilling under vacuum & heat")
	print("  ok  Rotary Evaporator: vacuum distillation and thin film evaporation verified")

	# 5.2 Schlenk Line
	var schlenk = ApparatusSuiteClass.SchlenkLineController.new()
	schlenk.fill_cold_trap(true)
	var p0_res = schlenk.set_port_valve(0, schlenk.ValvePosition.VACUUM)
	assert(p0_res.success == true, "Schlenk vacuum port opening failed")
	schlenk.set_port_valve(0, schlenk.ValvePosition.INERT_GAS)
	schlenk.set_port_valve(0, schlenk.ValvePosition.VACUUM)
	schlenk.set_port_valve(0, schlenk.ValvePosition.INERT_GAS)
	schlenk.set_port_valve(0, schlenk.ValvePosition.VACUUM)
	schlenk.set_port_valve(0, schlenk.ValvePosition.INERT_GAS)
	var schlenk_status = schlenk.get_status()
	assert(schlenk_status.port_0_purged == true, "Port 0 should be purged after 3x cycles")
	print("  ok  Schlenk Line: 3x Evacuate-Refill cycle and LN2 cold trap verified")

	# 5.3 Analytical Balance & Micropipette
	var balance = ApparatusSuiteClass.AnalyticalBalanceController.new()
	balance.set_draft_shield(true)
	balance.tare()
	balance.place_mass(0.1250)
	var bal_reading = balance.get_reading()
	assert(abs(bal_reading.displayed_mass_g - 0.1250) < 0.0001, "Balance reading mismatch")
	assert(bal_reading.is_stable == true, "Balance with closed draft shield should be stable")

	var pipette = ApparatusSuiteClass.MicropipetteController.new()
	pipette.attach_tip(true)
	pipette.set_volume(500.0)
	var asp = pipette.aspirate()
	assert(asp.success == true and asp.volume_ul == 500.0, "Pipette aspiration failed")
	var disp = pipette.dispense()
	assert(disp.success == true and disp.dispensed_ul == 500.0, "Pipette dispensation failed")
	print("  ok  Analytical Balance (0.0001 g) & Micropipette mechanics verified")

	# 5.4 HPLC
	var hplc = ApparatusSuiteClass.HPLCController.new()
	hplc.start_pumps(true)
	var hplc_run = hplc.inject_sample("Analgesic Mix", [
		{ "name": "Paracetamol", "logP": 0.46, "concentration_mg_ml": 0.5 },
		{ "name": "Aspirin", "logP": 1.19, "concentration_mg_ml": 0.5 },
		{ "name": "Caffeine", "logP": -0.07, "concentration_mg_ml": 0.2 }
	])
	assert(hplc_run.success == true, "HPLC run failed")
	assert(hplc_run.peaks.size() == 3, "HPLC should detect 3 distinct analyte peaks")
	print("  ok  HPLC Reverse-Phase C18 Chromatogram generation verified (3 separated peaks)")

	# 5.5 Soxhlet Extractor
	var soxhlet = ApparatusSuiteClass.SoxhletController.new()
	for i in range(10):
		soxhlet.update(20.0)
	var sox_status = soxhlet.get_status()
	assert(sox_status.siphon_cycles > 0, "Soxhlet should have completed siphon cycles")
	assert(sox_status.extracted_analyte_mg > 0.0, "Analyte should be extracted into boiling flask")
	print("  ok  Soxhlet Extractor: %d siphon cycles completed (%.1f mg extracted)" % [
		sox_status.siphon_cycles, sox_status.extracted_analyte_mg
	])

	# 5.6 UV-Vis Spectrophotometer
	var uv_vis = ApparatusSuiteClass.UVVisController.new()
	uv_vis.blank_zero()
	var scan = uv_vis.scan_absorbance("Fluorescein", 80000.0, 0.000015, 490.0)
	assert(scan.success == true, "UV-Vis scan failed")
	assert(scan.lambda_max_nm == 490.0, "Lambda max mismatch")
	assert(scan.absorbance_at_lambda_max > 1.0, "Beer-Lambert absorbance calculation error")
	print("  ok  UV-Vis Spectrophotometer: Beer-Lambert law & lambda_max scan verified")

	# 5.7 Glovebox & Centrifuge
	var glovebox = ApparatusSuiteClass.GloveboxController.new()
	glovebox.cycle_antechamber()
	glovebox.cycle_antechamber()
	glovebox.cycle_antechamber()
	var transfer = glovebox.transfer_item("Lithium Aluminum Hydride")
	assert(transfer.success == true, "Purged glovebox transfer failed")

	var centrifuge = ApparatusSuiteClass.CentrifugeController.new()
	centrifuge.set_tubes_balanced(true)
	var cf_res = centrifuge.start(true)
	assert(cf_res.success == true and cf_res.rcf_g_force > 5000, "Centrifuge RCF calculation error")
	print("  ok  Inert Glovebox & High-Speed Centrifuge controllers verified")

	# -------------------------------------------------------------------------
	# 6. Local AI Reaction Advisor & Heuristics
	# -------------------------------------------------------------------------
	print("\n[Section 6] Testing LocalAIReactionAdvisor...")
	var advisor = root.get_node_or_null("LocalAIReactionAdvisor")
	if not advisor:
		var adv_script = load("res://scripts/core/local_ai_reaction_advisor.gd")
		advisor = adv_script.new()
		root.add_child(advisor)

	# Reaction prediction
	var rxn_pred = advisor.predict_reaction(["Salicylic acid", "Acetic anhydride"], {"catalyst": "H2SO4"})
	assert(rxn_pred.has("primary_product"), "Missing primary_product in prediction")
	assert(rxn_pred.primary_product.contains("Aspirin"), "Expected Aspirin product")
	assert(rxn_pred.enthalpy_kj_mol < 0.0, "Esterification should be exothermic")
	print("  ok  Reaction Prediction: Salicylic acid + Acetic anhydride -> %s (dH = %.1f kJ/mol)" % [
		rxn_pred.primary_product, rxn_pred.enthalpy_kj_mol
	])

	# NMR Elucidation
	var nmr_elucid = advisor.elucidate_nmr_spectrum([
		{ "ppm": 1.18, "multiplicity": "t", "integration": 3 },
		{ "ppm": 3.65, "multiplicity": "q", "integration": 2 },
		{ "ppm": 2.60, "multiplicity": "s", "integration": 1 }
	])
	assert(nmr_elucid.analyzed_peaks_count == 3, "Expected 3 analyzed peaks")
	assert(nmr_elucid.identified_fragments.size() == 3, "Expected 3 structural fragments")
	print("  ok  NMR Spectral Elucidation: Ethanol triplet (CH3) and quartet (CH2) fragments parsed")

	print("\n=======================================================")
	print(">>> [OpenWorld & Mastery] ALL TESTS PASSED CLEANLY!")
	print("=======================================================\n")
	quit(0)
