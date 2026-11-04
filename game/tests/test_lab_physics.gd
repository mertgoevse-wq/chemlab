# Athanor Ascension — Physics lab headless test
# Run: tools/bin/godot --headless --path game --script res://tests/test_lab_physics.gd

extends SceneTree

const AP = preload("res://scripts/labs/accelerator_physics.gd")
const FP = preload("res://scripts/labs/fusor_physics.gd")

var _failures: int = 0


func _init() -> void:
	print("--- LAB PHYSICS VALIDATION ---")

	var gamma := AP.kinetic_to_gamma(250.0, "proton")
	_check(absf(gamma - 1.26648) < 0.001, "250 MeV proton gamma ~1.2665")
	var beta := AP.beta_from_kinetic(250.0, "proton")
	_check(absf(beta - 0.6136) < 0.002, "250 MeV proton beta ~0.614")
	_check(AP.beta_from_kinetic(7000.0, "proton") > 0.99, "7 GeV proton is ultra-relativistic")

	var rigidity := AP.magnetic_rigidity_t_m(250.0, "proton")
	_check(absf(rigidity - 2.432) < 0.03, "250 MeV proton rigidity ~2.43 T*m")
	var field := AP.required_field_t(250.0, "proton", 1.2)
	_check(absf(field - rigidity / 1.2) < 1e-9, "field = rigidity / radius")

	_check(AP.beam_power_w(250.0, 10.0) > 2400.0 and AP.beam_power_w(250.0, 10.0) < 2600.0,
		"10 uA at 250 MeV is ~2.5 kW")

	var threshold := AP.reaction_threshold_mev("p_li7")
	_check(absf(threshold - 1.88) < 0.1, "p+Li7 threshold ~1.88 MeV")
	_check(AP.reaction_threshold_mev("dt") == 0.0, "D-T is exothermic, zero threshold")

	# 250 MeV protons are below the Cherenkov threshold in water (beta 0.61 < 1/1.333).
	var cherenkov := AP.cherenkov_angle_deg(250.0, "proton", "water")
	_check(cherenkov == 0.0, "250 MeV proton is below Cherenkov threshold in water")
	var cherenkov_high := AP.cherenkov_angle_deg(7000.0, "proton", "water")
	_check(cherenkov_high > 35.0 and cherenkov_high < 46.0, "7 GeV proton Cherenkov angle in water ~41 deg")
	_check(AP.cherenkov_angle_deg(0.1, "proton", "water") == 0.0, "sub-threshold beam has no Cherenkov cone")

	var activity := AP.activation_bq(1.0e22, 0.05, 1.0e12, 53.22 * 86400.0, 600.0)
	_check(activity > 0.0, "activation is positive")

	var breakdown := FP.paschen_breakdown_v(6.0, 4.0)
	_check(breakdown > 1500.0 and breakdown < 2500.0, "air Paschen at 6 mTorr, 4 cm ~2 kV")
	_check(FP.pressure_window_ok(6.0), "6 mTorr is inside the fusor window")
	_check(not FP.pressure_window_ok(30.0), "30 mTorr is outside the window")
	_check(FP.mean_free_path_m(6.0) > FP.mean_free_path_m(20.0), "mean free path falls with pressure")

	var yield_rate := FP.neutron_yield_per_s(28.0, 8.0, 6.0)
	_check(yield_rate > 1.0e4, "28 kV / 8 mA fusor yields >1e4 n/s")

	var build_ok: Dictionary = {}
	for step in FP.BUILD_STEPS:
		build_ok[str(step.get("id", ""))] = true

	var run_ok := FP.simulate_run(28.0, 8.0, 6.0, 1.5, true)
	_check(bool(run_ok.get("ok", false)), "complete build + valid operating point runs")
	_check(float(run_ok.get("dose_usv_h", 0.0)) > 0.0, "dose rate computed")

	var run_low_v := FP.simulate_run(5.0, 8.0, 6.0, 1.5, true)
	_check(not bool(run_low_v.get("ok", true)), "low voltage run fails honestly")

	var run_arc := FP.simulate_run(28.0, 8.0, 25.0, 1.5, true)
	_check(str(run_arc.get("failure", "")) == "no_vacuum", "bad pressure reports no_vacuum")

	var run_incomplete := FP.simulate_run(28.0, 8.0, 6.0, 1.5, false)
	_check(str(run_incomplete.get("failure", "")) == "incomplete_build", "incomplete build is blocked")

	print("--- RESULT: %s (%d failures) ---" % ["PASS" if _failures == 0 else "FAIL", _failures])
	quit(0 if _failures == 0 else 1)


func _check(condition: bool, label: String) -> void:
	if condition:
		print("  ok  ", label)
	else:
		_failures += 1
		printerr("  FAIL ", label)
