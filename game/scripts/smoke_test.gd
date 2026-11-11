# ChemLab: Origins — Headless Engine Smoke Test Harness
# Path: res://scripts/smoke_test.gd
# Validates scene compilation, apparatus instantiation, and scientific stoichiometry.

extends SceneTree

const SCENES_TO_VALIDATE: Array[String] = [
	"res://scenes/loading/loading_screen.tscn",
	"res://scenes/main_menu/main_menu.tscn",
	"res://scenes/genomics/genome_browser.tscn",
	"res://scenes/laboratories/accelerator_lab.tscn",
	"res://scenes/laboratories/fusor_lab.tscn",
	"res://scenes/laboratories/lab_hub.tscn",
	"res://scenes/laboratories/titration_practicum.tscn",
	"res://scenes/laboratories/synthesis_lab.tscn",
	"res://scenes/laboratories/electrochemistry_lab.tscn",
	"res://scenes/laboratories/cell_culture_lab.tscn",
	"res://scenes/laboratories/radiochemistry_lab.tscn",
	"res://scenes/laboratories/materials_lab.tscn",
	"res://scenes/laboratories/cleanroom_lab.tscn",
	"res://scenes/laboratories/pilot_plant.tscn",
	"res://scenes/laboratories/forensic_lab.tscn",
	"res://scenes/laboratories/orbital_lab.tscn",
	"res://scenes/laboratories/cryogenic_lab.tscn",
	"res://scenes/laboratories/teaching_lab.tscn",
	"res://scenes/laboratories/genomics_lab.tscn",
	"res://scenes/progression/skill_codex.tscn",
	"res://scenes/laboratories/analytical_lab.tscn",
	"res://scenes/player/player.tscn",
	"res://scenes/player/player_controller.tscn",
	"res://scenes/apparatus/analytical_balance.tscn",
	"res://scenes/apparatus/magnetic_stirrer.tscn",
	"res://scenes/apparatus/titration_buret.tscn",
	"res://scenes/apparatus/bunsen_burner.tscn",
	"res://scenes/apparatus/erlenmeyer_flask.tscn",
	"res://scenes/apparatus/beaker.tscn",
	"res://scenes/quests/quest_overlay.tscn"
]

func _init() -> void:
	print("\n=======================================================")
	print(">>> [ChemLab Smoke Test] Starting Headless Verification...")
	print("=======================================================")

	var total_passed: int = 0
	var total_failed: int = 0

	# 1. Validate All Scenes
	for scene_path in SCENES_TO_VALIDATE:
		print("Checking scene: %s ..." % scene_path)
		if not ResourceLoader.exists(scene_path):
			printerr("FAIL: Scene file does not exist: %s" % scene_path)
			total_failed += 1
			continue

		var res = load(scene_path)
		if not res or not (res is PackedScene):
			printerr("FAIL: Could not load PackedScene: %s" % scene_path)
			total_failed += 1
			continue

		var instance = res.instantiate()
		if not instance:
			printerr("FAIL: Could not instantiate scene: %s" % scene_path)
			total_failed += 1
			continue
		# A scene whose root script failed to parse still instantiates as a bare
		# Control. Without this check the suite happily passes an empty room.
		if instance.get_script() == null:
			printerr("FAIL: root script missing or failed to load: %s" % scene_path)
			total_failed += 1
			instance.free()
			continue

		print("  -> Instantiated successfully: %s (%s)" % [instance.name, instance.get_class()])
		total_passed += 1
		instance.free()

	# 2. Validate Scientific Stoichiometric Acid-Base Neutralization
	print("\nChecking Scientific Stoichiometry (HCl + NaOH Neutralization)...")
	var rxn_eval_script = load("res://scripts/chemistry/reaction_evaluator.gd")
	if rxn_eval_script:
		var evaluator = rxn_eval_script.new()
		var hcl_moles = 0.0025  # 25 mL of 0.1 M HCl
		var naoh_moles = 0.0025 # 25 mL of 0.1 M NaOH
		var limiting = minf(hcl_moles, naoh_moles)
		var q_joules = limiting * absf(evaluator.DELTA_H_NEUTRALIZATION_KJ_MOL) * 1000.0
		var total_mass_g = 50.0  # 50 mL total volume
		var delta_t = q_joules / (total_mass_g * evaluator.WATER_CP_J_G_K)

		print("  -> Delta H: %.2f kJ/mol" % evaluator.DELTA_H_NEUTRALIZATION_KJ_MOL)
		print("  -> Calculated Neutralization Heat: %.2f Joules" % q_joules)
		print("  -> Adiabatic Temperature Rise: +%.3f °C" % delta_t)

		# Expect ~0.682 °C temperature increase for 25 mL 0.1M + 25 mL 0.1M
		if absf(delta_t - 0.682) < 0.02:
			print("  -> PASS: Enthalpy balance matches theoretical NIST value (+0.682 °C).")
			total_passed += 1
		else:
			printerr("  -> FAIL: Enthalpy calculation unexpected: %f" % delta_t)
			total_failed += 1

	print("\n=======================================================")
	print(">>> [ChemLab Smoke Test] Summary: %d Passed, %d Failed" % [total_passed, total_failed])
	print("=======================================================")

	if total_failed == 0:
		print(">>> ALL SMOKE TESTS PASSED! Exiting cleanly with code 0.\n")
		quit(0)
	else:
		printerr(">>> FAILURES DETECTED! Exiting with code 1.\n")
		quit(1)
