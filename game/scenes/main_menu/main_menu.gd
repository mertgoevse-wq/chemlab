# Athanor Ascension - Main Menu
# Unified 3-Mode Startup Architecture:
# 1. Career / Story Mode (10 Acts, 3 Backgrounds: Academic, Hobbyist, Ex-Pharma)
# 2. Pure Sandbox Mode (Immediate unlock of all 15 labs & literature catalogs)
# 3. Training & Certification Practicum (Analytical Titration & Safety Drills)

extends Control

class_name MainMenu

# UI Node References
var _nav_menu: VBoxContainer
var _btn_sandbox: Button
var _btn_campaign: Button
var _btn_practicum: Button
var _btn_settings: Button
var _btn_credits: Button
var _btn_exit: Button

var _settings_modal: Control
var _credits_modal: Control
var _campaign_modal: PanelContainer
var _fade_overlay: ColorRect

var _sfx_click: AudioStreamPlayer
var _sfx_hover: AudioStreamPlayer

# Settings Controls
var _opt_graphics: OptionButton
var _opt_input: OptionButton
var _slider_master: HSlider
var _slider_sfx: HSlider
var _slider_ambience: HSlider
var _lbl_master_val: Label
var _lbl_sfx_val: Label
var _lbl_ambience_val: Label
var _btn_settings_close: Button
var _btn_credits_close: Button

# Campaign Creation State
var _character_creator: CharacterCreator
var _selected_bg_id: String = "academic"
var _selected_spec_id: String = "organic_synthesis"
var _name_line_edit: LineEdit
var _bg_desc_label: Label
var _spec_desc_label: Label
var _bg_buttons: Array[Button] = []
var _spec_buttons: Array[Button] = []

func _ready() -> void:
	_character_creator = get_node_or_null("/root/CharacterCreator")
	_cache_ui_nodes()
	_setup_buttons()
	_setup_settings_modal()
	_setup_credits_modal()
	_build_campaign_modal()
	_fade_in_screen()

func _cache_ui_nodes() -> void:
	# Navigation Menu & Primary Buttons
	_nav_menu = get_node_or_null("UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu")
	if _nav_menu:
		_btn_sandbox = _nav_menu.get_node_or_null("BtnSandbox")
		_btn_campaign = _nav_menu.get_node_or_null("BtnCampaign")
		_btn_settings = _nav_menu.get_node_or_null("BtnSettings")
		_btn_credits = _nav_menu.get_node_or_null("BtnCredits")
		_btn_exit = _nav_menu.get_node_or_null("BtnExit")

	# Modals & Overlays
	_settings_modal = get_node_or_null("UI/SettingsModal")
	_credits_modal = get_node_or_null("UI/CreditsModal")
	_fade_overlay = get_node_or_null("UI/FadeOverlay")

	# Audio
	_sfx_click = get_node_or_null("Audio/SFXClick")
	_sfx_hover = get_node_or_null("Audio/SFXHover")

	# Settings controls
	if _settings_modal:
		_opt_graphics = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/OptGraphicsPreset")
		_opt_input = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/OptInputMode")
		_slider_master = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxMaster/SliderMaster")
		_lbl_master_val = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxMaster/LblMasterVal")
		_slider_sfx = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxSFX/SliderSFX")
		_lbl_sfx_val = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxSFX/LblSFXVal")
		_slider_ambience = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxAmbience/SliderAmbience")
		_lbl_ambience_val = _settings_modal.get_node_or_null("MarginContainer/VBox/SettingsGrid/HBoxAmbience/LblAmbienceVal")
		_btn_settings_close = _settings_modal.get_node_or_null("MarginContainer/VBox/BtnSettingsClose")

	if _credits_modal:
		_btn_credits_close = _credits_modal.get_node_or_null("MarginContainer/VBox/BtnCreditsClose")

func _setup_buttons() -> void:
	if not _nav_menu:
		return

	# Configure Mode 1: Career / Story Mode
	if _btn_campaign:
		_btn_campaign.text = "📖 Career & Story Mode (10 Acts · Mentor Guidance)"
		_btn_campaign.pressed.connect(_on_campaign_pressed)
		_hook_button_sounds(_btn_campaign)

	# Configure Mode 2: Pure Sandbox Mode
	if _btn_sandbox:
		_btn_sandbox.text = "🧪 Pure Sandbox Mode (All 15 Labs & Literature Catalogs)"
		_btn_sandbox.pressed.connect(_on_sandbox_pressed)
		_hook_button_sounds(_btn_sandbox)

	# Configure Mode 3: Training & Certification Practicum
	_btn_practicum = _nav_menu.get_node_or_null("BtnPracticum")
	if not _btn_practicum:
		_btn_practicum = Button.new()
		_btn_practicum.name = "BtnPracticum"
		_btn_practicum.custom_minimum_size = Vector2(0, 52)
		_nav_menu.add_child(_btn_practicum)
		_nav_menu.move_child(_btn_practicum, 2)

	_btn_practicum.text = "🎯 Training & Certification (Analytical Titration Drills)"
	_btn_practicum.pressed.connect(_on_practicum_pressed)
	_hook_button_sounds(_btn_practicum)

	# Configure Settings, Credits, Exit
	if _btn_settings:
		_btn_settings.pressed.connect(func(): _show_modal(_settings_modal))
		_hook_button_sounds(_btn_settings)

	if _btn_credits:
		_btn_credits.pressed.connect(func(): _show_modal(_credits_modal))
		_hook_button_sounds(_btn_credits)

	if _btn_exit:
		_btn_exit.pressed.connect(func(): get_tree().quit())
		_hook_button_sounds(_btn_exit)

func _hook_button_sounds(btn: Button) -> void:
	btn.mouse_entered.connect(func(): _play_sfx(_sfx_hover))
	btn.pressed.connect(func(): _play_sfx(_sfx_click))

func _play_sfx(player: AudioStreamPlayer) -> void:
	if player and player.stream:
		player.play()

# =============================================================================
# STARTUP MODE 1: CAREER & STORY MODE
# =============================================================================

func _on_campaign_pressed() -> void:
	if _campaign_modal:
		_show_modal(_campaign_modal)

func _build_campaign_modal() -> void:
	var ui_root = get_node_or_null("UI")
	if not ui_root:
		return

	_campaign_modal = PanelContainer.new()
	_campaign_modal.name = "CampaignModal"
	_campaign_modal.visible = false
	_campaign_modal.set_anchors_preset(PRESET_CENTER)
	_campaign_modal.offset_left = -460.0
	_campaign_modal.offset_top = -320.0
	_campaign_modal.offset_right = 460.0
	_campaign_modal.offset_bottom = 320.0
	ui_root.add_child(_campaign_modal)

	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 28)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_bottom", 24)
	_campaign_modal.add_child(margin)

	var vbox = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 14)
	margin.add_child(vbox)

	# Title & Header
	var title = Label.new()
	title.text = "RESEARCH CAREER & INVESTIGATOR ORIENTATION"
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", Color(0.0, 0.9, 1.0))
	vbox.add_child(title)

	var subtitle = Label.new()
	subtitle.text = "Select your background origin to calibrate starting apparatus, mentor guidance, and laboratory bay."
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", Color(0.7, 0.78, 0.88))
	vbox.add_child(subtitle)

	vbox.add_child(HSeparator.new())

	# Background Selection Buttons
	var bg_label = Label.new()
	bg_label.text = "CHOOSE BACKGROUND ORIGIN:"
	bg_label.add_theme_font_size_override("font_size", 13)
	bg_label.add_theme_color_override("font_color", Color(1.0, 0.7, 0.0))
	vbox.add_child(bg_label)

	var bg_hbox = HBoxContainer.new()
	bg_hbox.add_theme_constant_override("separation", 12)
	vbox.add_child(bg_hbox)

	var backgrounds = [
		{"id": "academic", "name": "Academic", "sub": "State University · Analytical Lab"},
		{"id": "hobbyist", "name": "Hobbyist", "sub": "Basement Lab · Off-Grid Synthesis"},
		{"id": "ex_pharma", "name": "Ex-Pharma", "sub": "Clandestine Facility · Pilot Plant"}
	]

	_bg_buttons.clear()
	for bg_info in backgrounds:
		var btn = Button.new()
		btn.text = "%s\n%s" % [bg_info.name, bg_info.sub]
		btn.custom_minimum_size = Vector2(260, 56)
		btn.toggle_mode = true
		btn.button_pressed = (bg_info.id == _selected_bg_id)
		btn.pressed.connect(_on_background_button_pressed.bind(bg_info.id))
		_hook_button_sounds(btn)
		bg_hbox.add_child(btn)
		_bg_buttons.append(btn)

	_bg_desc_label = Label.new()
	_bg_desc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bg_desc_label.add_theme_font_size_override("font_size", 12)
	_bg_desc_label.add_theme_color_override("font_color", Color(0.85, 0.9, 0.95))
	vbox.add_child(_bg_desc_label)
	_update_bg_description(_selected_bg_id)

	vbox.add_child(HSeparator.new())

	# Specialization Selection
	var spec_label = Label.new()
	spec_label.text = "CHOOSE FIELD SPECIALIZATION:"
	spec_label.add_theme_font_size_override("font_size", 13)
	spec_label.add_theme_color_override("font_color", Color(1.0, 0.7, 0.0))
	vbox.add_child(spec_label)

	var spec_hbox = HBoxContainer.new()
	spec_hbox.add_theme_constant_override("separation", 8)
	vbox.add_child(spec_hbox)

	var specializations = [
		{"id": "organic_synthesis", "name": "Organic Synthesis"},
		{"id": "analytical_chemistry", "name": "Analytical Chem"},
		{"id": "chemical_engineering", "name": "Process Pilot"},
		{"id": "radiochemistry", "name": "Radiochem"},
		{"id": "bio_molecular", "name": "Bio-Genomics"}
	]

	_spec_buttons.clear()
	for spec_info in specializations:
		var btn = Button.new()
		btn.text = spec_info.name
		btn.custom_minimum_size = Vector2(155, 38)
		btn.toggle_mode = true
		btn.button_pressed = (spec_info.id == _selected_spec_id)
		btn.pressed.connect(_on_spec_button_pressed.bind(spec_info.id))
		_hook_button_sounds(btn)
		spec_hbox.add_child(btn)
		_spec_buttons.append(btn)

	# Name LineEdit
	var name_hbox = HBoxContainer.new()
	name_hbox.add_theme_constant_override("separation", 16)
	vbox.add_child(name_hbox)

	var name_lbl = Label.new()
	name_lbl.text = "Investigator Name:"
	name_hbox.add_child(name_lbl)

	_name_line_edit = LineEdit.new()
	_name_line_edit.text = "Dr. Valerius Athanor"
	_name_line_edit.custom_minimum_size = Vector2(320, 36)
	name_hbox.add_child(_name_line_edit)

	# Footer Actions
	var action_hbox = HBoxContainer.new()
	action_hbox.add_theme_constant_override("separation", 16)
	action_hbox.alignment = BoxContainer.ALIGNMENT_END
	vbox.add_child(action_hbox)

	var cancel_btn = Button.new()
	cancel_btn.text = "Cancel"
	cancel_btn.custom_minimum_size = Vector2(130, 44)
	cancel_btn.pressed.connect(func(): _campaign_modal.visible = false)
	_hook_button_sounds(cancel_btn)
	action_hbox.add_child(cancel_btn)

	var launch_btn = Button.new()
	launch_btn.text = "🚀 Initiate Research Journey"
	launch_btn.custom_minimum_size = Vector2(240, 44)
	launch_btn.pressed.connect(_launch_campaign_journey)
	_hook_button_sounds(launch_btn)
	action_hbox.add_child(launch_btn)

func _on_background_button_pressed(bg_id: String) -> void:
	_selected_bg_id = bg_id
	for i in range(_bg_buttons.size()):
		var btn = _bg_buttons[i]
		btn.button_pressed = (btn.text.begins_with("Academic") and bg_id == "academic") or \
							(btn.text.begins_with("Hobbyist") and bg_id == "hobbyist") or \
							(btn.text.begins_with("Ex-Pharma") and bg_id == "ex_pharma")
	_update_bg_description(bg_id)

func _update_bg_description(bg_id: String) -> void:
	match bg_id:
		"academic":
			_bg_desc_label.text = "Academic: Rigorous institutional training under Prof. Sterling. Starts at the State University Analytical Laboratory with analytical balances, high-precision titrators, and spectrophotometers."
		"hobbyist":
			_bg_desc_label.text = "Hobbyist: Unorthodox self-taught researcher. Operates from an improvised basement facility with customized borosilicate glassware, DIY magnetic stirrers, and esoteric alchemical texts."
		"ex_pharma":
			_bg_desc_label.text = "Ex-Pharma: Senior industrial synthesis specialist. Escaped corporate surveillance with high-yield pilot notebooks (including multi-step PiHKAL/TiHKAL pathways). Starts in a Clandestine Pilot Facility."

func _on_spec_button_pressed(spec_id: String) -> void:
	_selected_spec_id = spec_id
	for btn in _spec_buttons:
		btn.button_pressed = (btn.text.to_lower().contains(spec_id.replace("_", " ").substr(0, 5)))

func _launch_campaign_journey() -> void:
	if _character_creator:
		_character_creator.select_background(_selected_bg_id)
		_character_creator.select_specialization(_selected_spec_id)
		var char_name = _name_line_edit.text.strip_edges()
		if char_name == "":
			char_name = "Dr. Valerius Athanor"
		_character_creator.set_character_name(char_name)

		var res = _character_creator.create_character()
		if res.get("success", false):
			_character_creator.apply_character_to_game(res.character)

	# Determine starting lab based on background
	var target_scene = "res://scenes/laboratories/lab_hub.tscn"
	match _selected_bg_id:
		"academic":
			target_scene = "res://scenes/laboratories/analytical_lab.tscn"
		"hobbyist":
			target_scene = "res://scenes/laboratories/synthesis_lab.tscn"
		"ex_pharma":
			target_scene = "res://scenes/laboratories/synthesis_lab.tscn"

	_transition_to_scene(target_scene)

# =============================================================================
# STARTUP MODE 2: PURE SANDBOX MODE
# =============================================================================

func _on_sandbox_pressed() -> void:
	var save_mgr = get_node_or_null("/root/SaveManager")
	if save_mgr and save_mgr.has_method("unlock_all_sandbox"):
		save_mgr.unlock_all_sandbox()

	# Transition to central Lab Hub with full equipment & catalogs
	_transition_to_scene("res://scenes/laboratories/lab_hub.tscn")

# =============================================================================
# STARTUP MODE 3: TRAINING & CERTIFICATION PRACTICUM
# =============================================================================

func _on_practicum_pressed() -> void:
	# Transition directly to Analytical Titration Practicum
	_transition_to_scene("res://scenes/laboratories/titration_practicum.tscn")

# =============================================================================
# MODALS & SCENE TRANSITIONS
# =============================================================================

func _show_modal(modal: Control) -> void:
	if modal:
		modal.visible = true

func _transition_to_scene(scene_path: String) -> void:
	if _fade_overlay:
		_fade_overlay.visible = true
		var tween = create_tween()
		tween.tween_property(_fade_overlay, "color:a", 1.0, 0.4)
		await tween.finished

	get_tree().change_scene_to_file(scene_path)

func _fade_in_screen() -> void:
	if _fade_overlay:
		_fade_overlay.visible = true
		_fade_overlay.color = Color(0.043, 0.059, 0.098, 1.0)
		var tween = create_tween()
		tween.tween_property(_fade_overlay, "color:a", 0.0, 0.5)
		await tween.finished
		_fade_overlay.visible = false

# =============================================================================
# SETTINGS & CREDITS
# =============================================================================

func _setup_settings_modal() -> void:
	if not _settings_modal:
		return

	if _opt_graphics:
		_opt_graphics.clear()
		_opt_graphics.add_item("Iris Xe Integrated (Compatibility GLES3 · 60 FPS Budget)")
		_opt_graphics.add_item("Balanced (Enhanced Bloom & Depth of Field)")
		_opt_graphics.add_item("High Fidelity (Full Volumetrics & Shaders)")
		_opt_graphics.select(0)

	if _opt_input:
		_opt_input.clear()
		_opt_input.add_item("Keyboard & Mouse (Classic Lab Precision)")
		_opt_input.add_item("Webcam Hand Tracking (MediaPipe 1-Euro Filter :8766)")
		_opt_input.add_item("Joy-Con Dual Motion Sensors")
		_opt_input.add_item("GameSir Nova Lite Controller")
		_opt_input.select(0)
		_opt_input.item_selected.connect(_on_input_mode_selected)

	# Audio Sliders
	if _slider_master:
		_slider_master.value_changed.connect(func(v): _on_volume_changed("Master", v, _lbl_master_val))
	if _slider_sfx:
		_slider_sfx.value_changed.connect(func(v): _on_volume_changed("UI", v, _lbl_sfx_val))
	if _slider_ambience:
		_slider_ambience.value_changed.connect(func(v): _on_volume_changed("Ambience", v, _lbl_ambience_val))

	if _btn_settings_close:
		_btn_settings_close.pressed.connect(func(): _settings_modal.visible = false)
		_hook_button_sounds(_btn_settings_close)

func _on_input_mode_selected(index: int) -> void:
	var input_mgr = get_node_or_null("/root/InputManager")
	if not input_mgr:
		return
	match index:
		0: input_mgr.set_input_method("keyboard_mouse")
		1: input_mgr.set_input_method("webcam")
		2: input_mgr.set_input_method("joycon")
		3: input_mgr.set_input_method("gamesir")

func _on_volume_changed(bus_name: String, value: float, label: Label) -> void:
	if label:
		label.text = "%d%%" % int(value * 100)
	var bus_idx = AudioServer.get_bus_index(bus_name)
	if bus_idx >= 0:
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(maxf(value, 0.0001)))

func _setup_credits_modal() -> void:
	if _btn_credits_close:
		_btn_credits_close.pressed.connect(func(): _credits_modal.visible = false)
		_hook_button_sounds(_btn_credits_close)
