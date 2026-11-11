# Athanor Ascension — Test Apparatus Suite & Interactive Practicum
# Headless verification of all 8 laboratory instruments and practicum UI
# Run: tools/bin/godot --headless --path game --script res://tests/test_apparatus_and_practicum.gd

extends SceneTree

const Suite = preload("res://scripts/labs/apparatus_suite.gd")

func _init() -> void:
	print("--- Running Test Apparatus Suite & Interactive Practicum ---")
	var failures: int = 0

	failures += _test_rotary_evaporator()
	failures += _test_schlenk_line()
	failures += _test_analytical_balance()
	failures += _test_hplc_system()
	failures += _test_soxhlet_extractor()
	failures += _test_uvvis_spectrophotometer()
	failures += _test_glovebox()
	failures += _test_centrifuge()
	failures += _test_practicum_ui()

	if failures == 0:
		print("SUCCESS: All apparatus suite tests passed (0 failures).")
		quit(0)
	else:
		printerr("FAILED: %d apparatus tests failed." % failures)
		quit(1)

func _assert(condition: bool, msg: String) -> int:
	if not condition:
		printerr("  [FAIL] %s" % msg)
		return 1
	print("  [PASS] %s" % msg)
	return 0

func _test_rotary_evaporator() -> int:
	print("\nTesting Rotary Evaporator (Rotovap)...")
	var f: int = 0
	var rotovap = Suite.RotovapController.new()

	rotovap.secure_keck_clip(true)
	f += _assert(rotovap.keck_clip_secured, "Keck clip is secured")

	rotovap.rotation_target_rpm = 120.0
	rotovap.rotation_rpm = 120.0
	rotovap.bath_target_c = 45.0
	rotovap.bath_temp_c = 45.0
	rotovap.vacuum_target_mbar = 50.0
	rotovap.vacuum_mbar = 50.0
	rotovap.set_stopcock(true)
	rotovap.toggle_bath_lift(true)
	rotovap.state = Suite.RotovapController.State.DISTILLING

	# Advance 5 seconds of thermodynamics
	for i in range(50):
		rotovap.update(0.1)

	var st = rotovap.get_status()
	f += _assert(float(st.get("rotation_rpm", 0.0)) > 100.0, "Rotation accelerated towards target RPM")
	f += _assert(float(st.get("vacuum_mbar", 1013.0)) < 700.0, "Vacuum pulled below atmospheric pressure")
	f += _assert(float(st.get("distillation_rate_ml_min", 0.0)) > 0.0, "Active distillation rate registered")
	f += _assert(float(st.get("collected_distillate_ml", 0.0)) > 0.0, "Distillate volume collected in receiving flask")
	return f

func _test_schlenk_line() -> int:
	print("\nTesting Schlenk Line (Inert Gas / High Vacuum)...")
	var f: int = 0
	var schlenk = Suite.SchlenkLineController.new()

	schlenk.fill_cold_trap(true)
	f += _assert(schlenk.cold_trap_filled_ln2, "Cold trap filled with LN2 (-196°C)")

	# Evacuate Port 0
	var res_vac = schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.VACUUM)
	f += _assert(bool(res_vac.get("success", false)), "Port 0 turned to VACUUM")

	# Inert refill Port 0 (Cycle 1)
	schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.INERT_GAS)
	# Cycles 2 & 3
	schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.VACUUM)
	schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.INERT_GAS)
	schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.VACUUM)
	schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.INERT_GAS)

	var st = schlenk.get_status()
	f += _assert(int(st.get("port_0_purge_cycles", 0)) >= 3, "3x evacuate-refill cycles recorded")
	f += _assert(bool(st.get("port_0_purged", false)), "Port 0 atmosphere marked inert (< 1 ppm O2)")
	return f

func _test_analytical_balance() -> int:
	print("\nTesting Analytical Balance & Metrology...")
	var f: int = 0
	var bal = Suite.AnalyticalBalanceController.new()

	bal.set_draft_shield(true)
	bal.tare()
	var st_zero = bal.get_reading()
	f += _assert(float(st_zero.get("displayed_mass_g", 1.0)) == 0.0, "Balance tared to 0.0000 g")

	bal.place_mass(0.2500)
	var st = bal.get_reading()
	f += _assert(abs(float(st.get("displayed_mass_g", 0.0)) - 0.2500) < 0.001, "Measured mass matches added sample aliquot (0.2500 g)")
	f += _assert(bool(st.get("is_stable", false)), "Reading is stable with closed draft shield")
	return f

func _test_hplc_system() -> int:
	print("\nTesting HPLC Diode Array System...")
	var f: int = 0
	var hplc = Suite.HPLCController.new()

	hplc.start_pumps(true)
	hplc.flow_rate_ml_min = 1.2
	hplc.mobile_phase_b_pct = 50.0

	var inj_res = hplc.inject_sample("Phenethylamine Mix", [
		{"name": "Uracil (t0)", "logP": -1.07, "concentration_mg_ml": 0.5},
		{"name": "2C-B", "logP": 2.85, "concentration_mg_ml": 1.5}
	])

	f += _assert(bool(inj_res.get("success", false)), "Sample injection succeeded")
	var peaks = inj_res.get("peaks", [])
	f += _assert(peaks.size() == 2, "2 chromatographic peaks resolved")
	f += _assert(float(peaks[1].get("retention_time_min", 0.0)) > float(peaks[0].get("retention_time_min", 0.0)), "Higher logP retained longer on C18")
	return f

func _test_soxhlet_extractor() -> int:
	print("\nTesting Soxhlet Continuous Extractor...")
	var f: int = 0
	var sox = Suite.SoxhletController.new()

	sox.heating_mantle_power_pct = 95.0
	sox.condenser_water_flowing = true

	# Advance 80 seconds of continuous extraction (80 * 0.4275 mL/s = 34.2 mL > 25.0 mL threshold)
	for i in range(800):
		sox.update(0.1)

	var st = sox.get_status()
	f += _assert(int(st.get("siphon_cycles", 0)) > 0, "Siphon cycles completed (> 0)")
	f += _assert(float(st.get("extracted_analyte_mg", 0.0)) > 0.0, "Analyte mass extracted into boiling flask")
	f += _assert(float(st.get("recovery_percentage", 0.0)) > 0.0, "Extraction recovery percentage calculated")
	return f

func _test_uvvis_spectrophotometer() -> int:
	print("\nTesting UV-Vis Spectrophotometer & Beer-Lambert...")
	var f: int = 0
	var uv = Suite.UVVisController.new()

	uv.blank_zero()
	f += _assert(uv.is_blanked, "Baseline blanked successfully")

	# Analyte: c = 1.0e-4 M, epsilon = 10,000 L/(mol*cm), path = 1.0 cm -> A = 1.000
	var scan_res = uv.scan_absorbance("Aspirin in Acetonitrile", 10000.0, 0.0001, 278.0)
	f += _assert(bool(scan_res.get("success", false)), "Spectral scan executed")
	var a_max = float(scan_res.get("absorbance_at_lambda_max", 0.0))
	f += _assert(abs(a_max - 1.0) < 0.01, "Beer-Lambert Absorbance matches theoretical A=1.000 (got %.3f)" % a_max)
	return f

func _test_glovebox() -> int:
	print("\nTesting Inert Atmosphere Glovebox...")
	var f: int = 0
	var gb = Suite.GloveboxController.new()

	f += _assert(gb.o2_ppm < 0.1 and gb.h2o_ppm < 0.1, "Glovebox starts at safe inert levels (<0.1 ppm)")

	# Trigger antechamber cycles
	gb.cycle_antechamber()
	gb.cycle_antechamber()
	var res_ante3 = gb.cycle_antechamber()
	f += _assert(bool(res_ante3.get("success", false)), "3x antechamber purge completed")
	f += _assert(gb.antechamber_purged, "Antechamber marked fully purged")

	var transfer_res = gb.transfer_item("tert-Butyllithium Solution")
	f += _assert(bool(transfer_res.get("success", false)), "Pyrophoric reagent safely transferred")
	return f

func _test_centrifuge() -> int:
	print("\nTesting High-Speed Centrifuge...")
	var f: int = 0
	var cent = Suite.CentrifugeController.new()

	cent.set_tubes_balanced(true)
	cent.target_rpm = 10000.0
	var run_res = cent.start(true)

	f += _assert(bool(run_res.get("success", false)), "Centrifuge started with balanced load")
	f += _assert(float(run_res.get("rpm", 0.0)) == 10000.0, "Rotor accelerated to 10,000 RPM")
	f += _assert(float(run_res.get("rcf_g_force", 0.0)) > 5000.0, "Relative Centrifugal Force (RCF) generated > 5,000 x g")
	return f

func _test_practicum_ui() -> int:
	print("\nTesting ApparatusPracticum UI Scene...")
	var f: int = 0
	var scene_res = load("res://scenes/laboratories/apparatus_practicum.tscn")
	f += _assert(scene_res != null, "ApparatusPracticum scene file loaded")

	var instance = scene_res.instantiate()
	f += _assert(instance != null, "ApparatusPracticum instantiated")

	# Add to tree and trigger ready
	root.add_child(instance)
	instance._ready()

	# Test switching through all 8 apparatuses
	for i in range(8):
		instance._switch_apparatus(i)
		instance._process(0.1)

	f += _assert(instance._current_type == 7, "Successfully cycled through all 8 apparatus views in UI")

	instance.queue_free()
	return f
