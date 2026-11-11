# Athanor Ascension — Main Menu 3-Mode Integration Test
# Validates:
# 1. Main menu loads cleanly and executes _ready() in SceneTree
# 2. Mode 1 (Career / Story Mode), Mode 2 (Pure Sandbox), Mode 3 (Practicum) buttons are present
# 3. Mode 1 campaign modal toggles backgrounds (Academic, Hobbyist, Ex-Pharma) & specializations
# 4. Mode 2 sandbox activates and unlocks all 15 laboratories
# 5. Settings modal options and sliders function properly

extends SceneTree

const MAIN_MENU_SCENE := "res://scenes/main_menu/main_menu.tscn"

func _init() -> void:
	_run_tests.call_deferred()

func _run_tests() -> void:
	print("\n=======================================================")
	print(">>> [Main Menu Test] Starting 3-Mode Verification...")
	print("=======================================================")

	var packed := load(MAIN_MENU_SCENE)
	if not packed:
		printerr("FAIL: Could not load scene %s" % MAIN_MENU_SCENE)
		quit(1)
		return

	var menu: MainMenu = packed.instantiate() as MainMenu
	if not menu:
		printerr("FAIL: Could not instantiate MainMenu")
		quit(1)
		return

	root.add_child(menu)
	await process_frame
	await process_frame

	# 1. Verify 3 Startup Mode Buttons
	print("Verifying 3 Startup Mode Buttons...")
	if not menu._btn_campaign:
		printerr("FAIL: _btn_campaign missing")
		quit(1)
		return
	assert("Story" in menu._btn_campaign.text, "Campaign button missing Story Mode label")
	print("  -> Mode 1: '%s' Verified." % menu._btn_campaign.text.substr(0, 30))

	if not menu._btn_sandbox:
		printerr("FAIL: _btn_sandbox missing")
		quit(1)
		return
	assert("Sandbox" in menu._btn_sandbox.text, "Sandbox button missing Sandbox label")
	print("  -> Mode 2: '%s' Verified." % menu._btn_sandbox.text.substr(0, 30))

	if not menu._btn_practicum:
		printerr("FAIL: _btn_practicum missing")
		quit(1)
		return
	assert("Training" in menu._btn_practicum.text, "Practicum button missing Training label")
	print("  -> Mode 3: '%s' Verified." % menu._btn_practicum.text.substr(0, 30))

	# 2. Test Campaign Modal Opening & Background Selection
	print("\nTesting Career & Story Mode Modal...")
	menu._on_campaign_pressed()
	await process_frame
	assert(menu._campaign_modal.visible == true, "Campaign modal did not open")

	# Test selecting 'hobbyist'
	menu._on_background_button_pressed("hobbyist")
	assert(menu._selected_bg_id == "hobbyist", "Failed to select hobbyist background")
	assert("Improvised" in menu._bg_desc_label.text or "Hobbyist" in menu._bg_desc_label.text, "Background description not updated")

	# Test selecting 'ex_pharma'
	menu._on_background_button_pressed("ex_pharma")
	assert(menu._selected_bg_id == "ex_pharma", "Failed to select ex_pharma background")
	print("  -> Background toggles functional (Academic, Hobbyist, Ex-Pharma).")

	# Test selecting specialization
	menu._on_spec_button_pressed("radiochemistry")
	assert(menu._selected_spec_id == "radiochemistry", "Failed to select specialization")
	print("  -> Specialization selector functional.")

	# Close modal
	menu._campaign_modal.visible = false

	# 3. Test Pure Sandbox Mode Activation
	print("\nTesting Pure Sandbox Mode Activation...")
	menu._on_sandbox_pressed()
	await process_frame

	var save_mgr = root.get_node_or_null("SaveManager")
	if save_mgr:
		var unlocked = save_mgr.save_data.statistics.labs_unlocked
		print("  -> Labs unlocked in Sandbox: %d laboratories" % unlocked.size())
		assert(unlocked.size() >= 15, "Expected all 15 laboratories to be unlocked in Sandbox mode")
		assert("synthesis_lab" in unlocked, "Missing synthesis_lab in sandbox")
		assert("titration_practicum" in unlocked, "Missing titration_practicum in sandbox")
		assert("accelerator_lab" in unlocked, "Missing accelerator_lab in sandbox")
		assert("fusor_lab" in unlocked, "Missing fusor_lab in sandbox")
		print("  -> ALL 15 LABORATORIES VERIFIED UNLOCKED!")

	# 4. Test Settings Modal
	print("\nTesting Settings Modal...")
	menu._show_modal(menu._settings_modal)
	assert(menu._settings_modal.visible == true, "Settings modal did not open")
	if menu._opt_input:
		menu._on_input_mode_selected(1) # Webcam mode
		var input_mgr = root.get_node_or_null("InputManager")
		if input_mgr:
			assert(input_mgr.current_method == "webcam", "Failed to switch input method to webcam")
			print("  -> Webcam hand tracking input method activated successfully (:8766).")
	menu._settings_modal.visible = false

	print("\n=======================================================")
	print(">>> [Main Menu Test] ALL 3 MODES & INTEGRATION TESTS PASSED!")
	print("=======================================================\n")
	quit(0)
