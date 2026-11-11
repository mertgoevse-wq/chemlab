# Athanor Ascension — NMR Spectrometer Integration Test
# Validates:
# 1. AnalyticalLab scene loads with NMRSpectrometer and NMRSampleTube
# 2. Player pickup and hold mechanics for NMRSampleTube
# 3. NMR spectrometer bore insertion and state transition
# 4. 1H NMR chemical shift spectrum generation and peak simulation
# 5. Display screen emission material update
# 6. Save/load state persistence for NMR apparatus and sample queue
# 7. Sample removal and cleanup

extends SceneTree

const LAB_SCENE := "res://scenes/laboratories/analytical_lab.tscn"

func _init() -> void:
	_run_tests.call_deferred()

func _run_tests() -> void:
	print("\n=======================================================")
	print(">>> [NMR Test] Starting NMR Spectrometer Verification...")
	print("=======================================================")

	var packed := load(LAB_SCENE)
	if packed == null:
		printerr("FAIL: Cannot load analytical lab scene: %s" % LAB_SCENE)
		quit(1)
		return

	var lab = packed.instantiate()
	root.add_child(lab)
	await process_frame
	await process_frame

	var nmr = lab.get_node_or_null("ApparatusInstances/NMRSpectrometer")
	assert(nmr != null, "FAIL: NMRSpectrometer not found in AnalyticalLab")
	print("  ok  NMRSpectrometer node found")

	var tube = lab.get_node_or_null("ApparatusInstances/NMRSampleTube")
	assert(tube != null, "FAIL: NMRSampleTube not found in AnalyticalLab")
	print("  ok  NMRSampleTube node found")

	var player = lab.get_node_or_null("Player")
	assert(player != null, "FAIL: Player not found in AnalyticalLab")
	print("  ok  Player node found")

	# 1. Initial State Check
	assert(nmr.is_powered_on == true, "FAIL: NMR should be powered on by default")
	assert(nmr.current_sample == null, "FAIL: NMR should have no sample initially")
	assert(tube._is_held == false, "FAIL: Tube should not be held initially")
	print("  ok  NMR initial power and bore state verified")

	# 2. Player Pickup NMR Sample Tube
	var pickup_ok = tube.pickup(player)
	assert(pickup_ok == true, "FAIL: Tube pickup failed")
	assert(tube._is_held == true, "FAIL: Tube _is_held should be true")
	assert(tube.freeze == true, "FAIL: Tube physics should be frozen while held")
	print("  ok  NMRSampleTube pickup by player verified")

	# 3. Sample Tube Data
	var sample_data = tube.get_sample_data()
	assert(sample_data.has("compound_name"), "FAIL: Sample missing compound_name")
	assert(sample_data.has("concentration_mM"), "FAIL: Sample missing concentration_mM")
	assert(sample_data.has("solvent"), "FAIL: Sample missing solvent")
	assert(sample_data["compound_name"] == "Ethanol", "FAIL: Default sample should be Ethanol")
	print("  ok  Sample metadata verified: %s (%s mM in %s)" % [sample_data["compound_name"], sample_data["concentration_mM"], sample_data["solvent"]])

	# 4. Insertion into NMR Bore
	# When held by player, placing into NMR
	tube.drop(false)
	nmr._insert_sample(tube)
	assert(nmr.current_sample == tube, "FAIL: Sample tube not inserted into NMR")
	assert(nmr.sample_queue.size() >= 1, "FAIL: Sample queue should contain inserted sample")
	print("  ok  Sample successfully inserted into NMR bore slot")

	# 5. Spectrum Acquisition & Simulation
	# Process FID to spectrum
	var sample_info = nmr.sample_queue[0]
	nmr._process_fid_to_spectrum(sample_info)

	var spectrum = nmr.current_spectrum_data
	assert(spectrum.has("x_ppm"), "FAIL: Spectrum missing x_ppm")
	assert(spectrum.has("y_intensity"), "FAIL: Spectrum missing y_intensity")
	assert(spectrum.has("peaks"), "FAIL: Spectrum missing peaks")
	assert(spectrum["x_ppm"].size() == spectrum["y_intensity"].size(), "FAIL: x and y size mismatch")
	assert(spectrum["x_ppm"].size() > 50, "FAIL: Spectrum resolution insufficient")
	print("  ok  NMR FID processed to frequency spectrum (%d data points)" % spectrum["x_ppm"].size())

	# Verify Ethanol 1H peaks: CH3 (~1.18 ppm), CH2 (~3.65 ppm), OH (~2.60 ppm)
	var peaks = spectrum["peaks"]
	var found_ch3 = false
	var found_ch2 = false
	var found_oh = false
	for p in peaks:
		var ppm = float(p.get("ppm", 0.0))
		if abs(ppm - 1.18) < 0.2:
			found_ch3 = true
		elif abs(ppm - 3.65) < 0.2:
			found_ch2 = true
		elif abs(ppm - 2.60) < 0.3:
			found_oh = true

	assert(found_ch3, "FAIL: Ethanol CH3 peak near 1.18 ppm missing")
	assert(found_ch2, "FAIL: Ethanol CH2 peak near 3.65 ppm missing")
	assert(found_oh, "FAIL: Ethanol OH peak near 2.60 ppm missing")
	print("  ok  Chemical shift assignments verified: CH3 (1.18 ppm), CH2 (3.65 ppm), OH (2.60 ppm)")

	# 6. Display Screen Material State
	if nmr.screen_material != null:
		assert(nmr.screen_material.emission_enabled == true, "FAIL: Display screen emission should be active")
		print("  ok  Display screen emission material active")

	# 7. Save / Load State Persistence
	var save_data = nmr.get_save_data()
	assert(save_data.has("is_powered_on"), "FAIL: Save data missing is_powered_on")
	assert(save_data.has("has_sample"), "FAIL: Save data missing has_sample")
	assert(save_data["has_sample"] == true, "FAIL: Save data should report has_sample true")
	assert(save_data.has("current_spectrum"), "FAIL: Save data missing current_spectrum")

	# Test restoring state
	nmr.load_save_data(save_data)
	assert(nmr.is_powered_on == true, "FAIL: Powered state not restored")
	assert(nmr.current_spectrum_data.has("peaks"), "FAIL: Spectrum not restored")
	print("  ok  Apparatus save/load serialization round-trip verified")

	# 8. Sample Removal
	nmr._try_remove_sample(player)
	assert(nmr.current_sample == null, "FAIL: Sample should be removed from NMR")
	print("  ok  Sample successfully ejected and bore cleared")

	print("=======================================================")
	print(">>> [NMR Test] ALL NMR TESTS PASSED CLEANLY!")
	print("=======================================================\n")
	quit(0)
