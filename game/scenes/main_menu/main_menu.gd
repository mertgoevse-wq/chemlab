# Athanor Ascension - Main Menu
# Research terminals, settings, character creation, input presets

extends Control

class_name MainMenu

var _current_screen: String = "main"
var _selected_save_slot: int = 1
var _character_creator: CharacterCreator

# UI elements
var _main_container: VBoxContainer
var _continue_button: Button
var _new_game_button: Button
var _load_game_button: Button
var _settings_button: Button
var _credits_button: Button
var _quit_button: Button

var _save_slot_container: GridContainer
var _save_slots: Array[Button] = []

var _character_creation_container: Control
var _background_buttons: Array[Button] = []
var _specialization_buttons: Array[Button] = []

var _settings_container: Control

func _ready() -> void:
	_cache_nodes()
	_connect_signals()
	_load_save_previews()
	_show_screen("main")

	# Play ambient music
	_play_ambient_music()

func _cache_nodes() -> void:
	_main_container = %MainContainer
	_continue_button = %ContinueButton
	_new_game_button = %NewGameButton
	_load_game_button = %LoadGameButton
	_settings_button = %SettingsButton
	_credits_button = %CreditsButton
	_quit_button = %QuitButton

	_save_slot_container = %SaveSlotContainer
	_character_creation_container = %CharacterCreationContainer
	_settings_container = %SettingsContainer

	# Get CharacterCreator autoload
	_character_creator = get_node_or_null("/root/CharacterCreator")

func _connect_signals() -> void:
	_continue_button.pressed.connect(func(): _continue_game())
	_new_game_button.pressed.connect(func(): _show_screen("character_creation"))
	_load_game_button.pressed.connect(func(): _show_screen("load_game"))
	_settings_button.pressed.connect(func(): _show_screen("settings"))
	_credits_button.pressed.connect(func(): _show_screen("credits"))
	_quit_button.pressed.connect(func(): get_tree().quit())

func _load_save_previews() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if not save_manager:
		return

	# Clear existing
	for btn in _save_slots:
		btn.queue_free()
	_save_slots.clear()

	# Create save slot buttons
	var saves = save_manager.get_all_saves()
	for i, save_info in saves:
		if i >= 10:  # Max 10 slots
			break

		var btn = Button.new()
		btn.name = "SaveSlot_%d" % (i + 1)

		if save_info.empty:
			btn.text = "Slot %d\n[Empty]" % (i + 1)
			btn.disabled = true
		else:
			btn.text = "Slot %d\n%s\n%s\n%s" % [
				i + 1,
				save_info.character_name,
				save_info.background,
				save_info.playtime_formatted
			]
			btn.disabled = false
			btn.pressed.connect(func(slot=i+1): _load_save_slot(slot).bind(i + 1))

		btn.custom_minimum_size = Vector2(200, 100)
		_save_slot_container.add_child(btn)
		_save_slots.append(btn)

func _show_screen(screen: String) -> void:
	_current_screen = screen

	_main_container.visible = (screen == "main")
	_save_slot_container.visible = (screen == "load_game")
	_character_creation_container.visible = (screen == "character_creation")
	_settings_container.visible = (screen == "settings")

	if screen == "credits":
		_show_credits()
	elif screen == "character_creation":
		_setup_character_creation()

func _continue_game() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager:
		save_manager.load_game(save_manager.current_slot)
		get_tree().change_scene_to_file("res://scenes/laboratories/lab_hub.tscn")

func _load_save_slot(slot: int) -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.load_game(slot):
		get_tree().change_scene_to_file("res://scenes/laboratories/lab_hub.tscn")

func _setup_character_creation() -> void:
	if not _character_creator:
		return

	# Clear existing buttons
	for btn in _background_buttons:
		btn.queue_free()
	_background_buttons.clear()

	for btn in _specialization_buttons:
		btn.queue_free()
	_specialization_buttons.clear()

	# Background selection
	var backgrounds = _character_creator.get_available_backgrounds()
	for i, bg in backgrounds:
		var btn = Button.new()
		btn.name = "BG_%s" % bg.id
		btn.text = "%s\n%s" % [bg.name, bg.description]
		btn.custom_minimum_size = Vector2(300, 100)
		btn.pressed.connect(func(bg_id=bg.id): _select_background(bg_id).bind(bg.id))
		_character_creation_container.add_child(btn)
		_background_buttons.append(btn)

	# Specialization selection
	var specs = _character_creator.get_available_specializations()
	for i, spec in specs:
		var btn = Button.new()
		btn.name = "Spec_%s" % spec.id
		btn.text = "%s\n%s" % [spec.name, spec.description]
		btn.custom_minimum_size = Vector2(300, 100)
		btn.pressed.connect(func(spec_id=spec.id): _select_specialization(spec_id).bind(spec.id))
		_character_creation_container.add_child(btn)
		_specialization_buttons.append(btn)

	# Name input
	# Would add LineEdit for name

	# Create button
	var create_btn = Button.new()
	create_btn.text = "Begin Journey"
	create_btn.custom_minimum_size = Vector2(200, 50)
	create_btn.pressed.connect(_create_character)
	_character_creation_container.add_child(create_btn)

func _select_background(bg_id: String) -> void:
	_character_creator.select_background(bg_id)
	# Update button visuals
	for btn in _background_buttons:
		btn.button_pressed = (btn.name == "BG_%s" % bg_id)

func _select_specialization(spec_id: String) -> void:
	_character_creator.select_specialization(spec_id)
	for btn in _specialization_buttons:
		btn.button_pressed = (btn.name == "Spec_%s" % spec_id)

func _create_character() -> void:
	var result = _character_creator.create_character()
	if result.success:
		_character_creator.apply_character_to_game(result.character)
		get_tree().change_scene_to_file("res://scenes/loading/loading_screen.tscn")
	else:
		print("Character creation failed: %s" % result.error)

func _show_credits() -> void:
	# Would show credits screen
	print("Credits screen")

func _play_ambient_music() -> void:
	# Would play Flow Music generated ambient track
	pass