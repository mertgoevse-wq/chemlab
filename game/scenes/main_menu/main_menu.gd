# ChemLab 3D Scientific Main Menu Controller (Godot 4.x Engine)
# Extends Control for modern cleanroom dark UI with 3D animated molecular backdrop.
# Provides seamless scene transitions, Iris Xe hardware profile scaling,
# audio mixing, dual-input configuration, and gamepad/keyboard navigation.

class_name MainMenu
extends Control

# =============================================================================
# SIGNALS & CONSTANTS
# =============================================================================

signal laboratory_launch_requested(lab_scene_path: String)
signal settings_saved(settings_dictionary: Dictionary)

const SCENE_ANALYTICAL_LAB: String = "res://scenes/laboratories/analytical_lab.tscn"
const SCENE_SANDBOX_LAB: String = "res://scenes/laboratories/analytical_lab.tscn"

# Color tokens from ChemLab Design System
const COLOR_CYAN_ACCENT: Color = Color(0.0, 0.898, 1.0, 1.0) # #00E5FF
const COLOR_AMBER_ALERT: Color = Color(1.0, 0.702, 0.0, 1.0) # #FFB300
const COLOR_DEEP_SLATE: Color = Color(0.043, 0.059, 0.098, 1.0) # #0B0F19

# =============================================================================
# NODE REFERENCES
# =============================================================================

# Navigation Menu Buttons
@onready var btn_sandbox: Button = $UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu/BtnSandbox
@onready var btn_campaign: Button = $UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu/BtnCampaign
@onready var btn_settings: Button = $UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu/BtnSettings
@onready var btn_credits: Button = $UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu/BtnCredits
@onready var btn_exit: Button = $UI/MarginContainer/HBoxContainer/MenuContainer/NavMenu/BtnExit

# Modal Dialogs
@onready var settings_panel: PanelContainer = $UI/SettingsModal
@onready var btn_settings_close: Button = $UI/SettingsModal/MarginContainer/VBox/BtnSettingsClose
@onready var credits_panel: PanelContainer = $UI/CreditsModal
@onready var btn_credits_close: Button = $UI/CreditsModal/MarginContainer/VBox/BtnCreditsClose

# Settings Controls
@onready var opt_graphics_preset: OptionButton = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/OptGraphicsPreset
@onready var opt_input_mode: OptionButton = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/OptInputMode
@onready var slider_master: HSlider = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxMaster/SliderMaster
@onready var lbl_master_val: Label = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxMaster/LblMasterVal
@onready var slider_sfx: HSlider = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxSFX/SliderSFX
@onready var lbl_sfx_val: Label = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxSFX/LblSFXVal
@onready var slider_ambience: HSlider = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxAmbience/SliderAmbience
@onready var lbl_ambience_val: Label = $UI/SettingsModal/MarginContainer/VBox/SettingsGrid/HBoxAmbience/LblAmbienceVal

# Animated 3D Scene Elements
@onready var molecular_cluster: Node3D = $BackgroundViewport/SubViewport/World3D/MolecularCluster
@onready var backdrop_camera: Camera3D = $BackgroundViewport/SubViewport/World3D/Camera3D

# Audio Players
@onready var sfx_click: AudioStreamPlayer = $Audio/SFXClick
@onready var sfx_hover: AudioStreamPlayer = $Audio/SFXHover

# Screen Shutter / Fade Overlay
@onready var fade_overlay: ColorRect = $UI/FadeOverlay

# =============================================================================
# STATE VARIABLES
# =============================================================================

var _rotation_speed_y: float = 0.22
var _rotation_speed_x: float = 0.08
var _is_transitioning: bool = false
var _active_graphics_preset: String = "balanced"
var _active_input_mode: String = "desktop"

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	# Configure fade overlay
	fade_overlay.visible = true
	fade_overlay.modulate = Color(1.0, 1.0, 1.0, 1.0)

	# Connect all button signals
	_connect_signals()

	# Populate option buttons
	_populate_settings_options()

	# Load and apply settings
	_load_persisted_settings()

	# Setup keyboard / gamepad focus
	btn_sandbox.grab_focus()

	# Start entry fade-in
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(fade_overlay, "modulate:a", 0.0, 0.6)
	tween.tween_callback(func(): fade_overlay.visible = false)


func _process(delta: float) -> void:
	# Continuous slow rotation of 3D background molecular mesh
	if molecular_cluster:
		molecular_cluster.rotate_y(_rotation_speed_y * delta)
		molecular_cluster.rotate_x(_rotation_speed_x * delta)


func _unhandled_input(event: InputEvent) -> void:
	# Handle UI Cancel (Escape / Gamepad B) to close modal panels
	if event.is_action_pressed("ui_cancel"):
		if settings_panel and settings_panel.visible:
			_on_btn_settings_close_pressed()
			get_viewport().set_input_as_handled()
		elif credits_panel and credits_panel.visible:
			_on_btn_credits_close_pressed()
			get_viewport().set_input_as_handled()

# =============================================================================
# SIGNAL SETUP & CONNECTIONS
# =============================================================================

func _connect_signals() -> void:
	# Primary navigation buttons
	btn_sandbox.pressed.connect(_on_btn_sandbox_pressed)
	btn_campaign.pressed.connect(_on_btn_campaign_pressed)
	btn_settings.pressed.connect(_on_btn_settings_pressed)
	btn_credits.pressed.connect(_on_btn_credits_pressed)
	btn_exit.pressed.connect(_on_btn_exit_pressed)

	# Dialog close buttons
	btn_settings_close.pressed.connect(_on_btn_settings_close_pressed)
	btn_credits_close.pressed.connect(_on_btn_credits_close_pressed)

	# Hover & Focus audio cues for all interactive buttons
	var buttons: Array[Button] = [
		btn_sandbox, btn_campaign, btn_settings, btn_credits, btn_exit,
		btn_settings_close, btn_credits_close
	]
	for btn in buttons:
		btn.mouse_entered.connect(_play_hover_sfx)
		btn.focus_entered.connect(_play_hover_sfx)

	# Settings controls
	opt_graphics_preset.item_selected.connect(_on_graphics_preset_selected)
	opt_input_mode.item_selected.connect(_on_input_mode_selected)
	slider_master.value_changed.connect(_on_master_slider_changed)
	slider_sfx.value_changed.connect(_on_sfx_slider_changed)
	slider_ambience.value_changed.connect(_on_ambience_slider_changed)


func _populate_settings_options() -> void:
	# Graphics Presets
	opt_graphics_preset.clear()
	opt_graphics_preset.add_item("Low (Performance Focus · 0.67x Scale)", 0)
	opt_graphics_preset.add_item("Balanced (Iris Xe 60 FPS Target · 0.77x Scale)", 1)
	opt_graphics_preset.add_item("High (Desktop GPU / Native 1.0x Scale)", 2)

	# Input Modes
	opt_input_mode.clear()
	opt_input_mode.add_item("Mouse & Keyboard (Precision Desktop Controls)", 0)
	opt_input_mode.add_item("Webcam Hand Tracking (MediaPipe Touchless Vision)", 1)

# =============================================================================
# PERSISTENCE & HARDWARE PROFILING
# =============================================================================

func _load_persisted_settings() -> void:
	var save_mgr = _get_save_manager()

	# Default values
	var preset: String = "balanced"
	var input_mode: String = "desktop"
	var master_vol: float = 1.0
	var sfx_vol: float = 1.0
	var ambience_vol: float = 0.8

	if save_mgr != null:
		preset = str(save_mgr.get_setting("graphics_preset", "balanced"))
		input_mode = str(save_mgr.get_setting("input_mode", "desktop"))
		master_vol = float(save_mgr.get_setting("master_volume", 1.0))
		sfx_vol = float(save_mgr.get_setting("sfx_volume", 1.0))
		ambience_vol = float(save_mgr.get_setting("ambience_volume", 0.8))

	# Apply to Graphics OptionButton
	match preset.to_lower():
		"low":
			opt_graphics_preset.selected = 0
		"high":
			opt_graphics_preset.selected = 2
		_:
			opt_graphics_preset.selected = 1
			preset = "balanced"

	apply_graphics_preset(preset)

	# Apply to Input OptionButton
	if input_mode == "webcam_tracker":
		opt_input_mode.selected = 1
	else:
		opt_input_mode.selected = 0
		input_mode = "desktop"

	apply_input_mode(input_mode)

	# Apply to Volume Sliders
	slider_master.value = master_vol
	_update_volume_label(lbl_master_val, master_vol)
	_apply_audio_volume("Master", master_vol)

	slider_sfx.value = sfx_vol
	_update_volume_label(lbl_sfx_val, sfx_vol)
	_apply_audio_volume("SFX", sfx_vol)

	slider_ambience.value = ambience_vol
	_update_volume_label(lbl_ambience_val, ambience_vol)
	_apply_audio_volume("Ambience", ambience_vol)


func apply_graphics_preset(preset: String) -> void:
	_active_graphics_preset = preset.to_lower()
	var vp: Viewport = get_viewport()
	var vp_rid: RID = vp.get_viewport_rid()
	var supports_screen_space_aa: bool = RenderingServer.get_rendering_device() != null

	match _active_graphics_preset:
		"low":
			# Maximum frame rate for low-spec or battery saver mode
			vp.scaling_3d_scale = 0.67
			vp.msaa_3d = Viewport.MSAA_DISABLED
			vp.use_debanding = false
			RenderingServer.viewport_set_msaa_3d(vp_rid, RenderingServer.VIEWPORT_MSAA_DISABLED)
			RenderingServer.viewport_set_use_debanding(vp_rid, false)
			if supports_screen_space_aa:
				vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
				RenderingServer.viewport_set_screen_space_aa(vp_rid, RenderingServer.VIEWPORT_SCREEN_SPACE_AA_DISABLED)

		"balanced":
			# Hardware-tuned for Intel Core i5-1245U / Intel Iris Xe 80 EUs (60 FPS Target)
			# 0.77x resolution scaling (approx 60% pixels, CAS/XeSS equivalent upsample)
			vp.scaling_3d_scale = 0.77
			vp.msaa_3d = Viewport.MSAA_2X
			vp.use_debanding = true
			RenderingServer.viewport_set_msaa_3d(vp_rid, RenderingServer.VIEWPORT_MSAA_2X)
			RenderingServer.viewport_set_use_debanding(vp_rid, true)
			if supports_screen_space_aa:
				vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
				RenderingServer.viewport_set_screen_space_aa(vp_rid, RenderingServer.VIEWPORT_SCREEN_SPACE_AA_FXAA)

		"high":
			# Native 1080p rendering with full MSAA 4x for discrete GPUs
			vp.scaling_3d_scale = 1.0
			vp.msaa_3d = Viewport.MSAA_4X
			vp.use_debanding = true
			RenderingServer.viewport_set_msaa_3d(vp_rid, RenderingServer.VIEWPORT_MSAA_4X)
			RenderingServer.viewport_set_use_debanding(vp_rid, true)
			if supports_screen_space_aa:
				vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
				RenderingServer.viewport_set_screen_space_aa(vp_rid, RenderingServer.VIEWPORT_SCREEN_SPACE_AA_FXAA)

	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.set_setting("graphics_preset", _active_graphics_preset)


func apply_input_mode(mode_name: String) -> void:
	_active_input_mode = mode_name
	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.set_setting("input_mode", _active_input_mode)

	# Forward to InputManager autoload if present
	if has_node("/root/InputManager"):
		var input_mgr = get_node("/root/InputManager")
		var target_mode = input_mgr.InputMode.WEBCAM_TRACKER if mode_name == "webcam_tracker" else input_mgr.InputMode.HARDWARE_DESKTOP
		if input_mgr.has_method("set_input_mode"):
			input_mgr.set_input_mode(target_mode)
		elif "current_input_mode" in input_mgr:
			input_mgr.current_input_mode = target_mode


func _apply_audio_volume(bus_name: String, linear_value: float) -> void:
	var bus_index := AudioServer.get_bus_index(bus_name)
	if bus_index >= 0:
		if linear_value <= 0.001:
			AudioServer.set_bus_mute(bus_index, true)
		else:
			AudioServer.set_bus_mute(bus_index, false)
			AudioServer.set_bus_volume_db(bus_index, linear_to_db(linear_value))


func _update_volume_label(label: Label, linear_value: float) -> void:
	if label:
		label.text = "%d%%" % int(round(linear_value * 100.0))


func _get_save_manager() -> Object:
	if Engine.has_singleton("SaveManager"):
		return Engine.get_singleton("SaveManager")
	elif has_node("/root/SaveManager"):
		return get_node("/root/SaveManager")
	return null

# =============================================================================
# SCENE TRANSITIONS
# =============================================================================

func transition_to_laboratory(scene_path: String) -> void:
	if _is_transitioning:
		return
	_is_transitioning = true

	_play_click_sfx()
	laboratory_launch_requested.emit(scene_path)

	# Disable navigation buttons to prevent duplicate triggers
	btn_sandbox.disabled = true
	btn_campaign.disabled = true
	btn_settings.disabled = true
	btn_credits.disabled = true
	btn_exit.disabled = true

	# Smooth scene fade out
	fade_overlay.visible = true
	fade_overlay.modulate = Color(1.0, 1.0, 1.0, 0.0)

	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(fade_overlay, "modulate:a", 1.0, 0.45)
	tween.tween_callback(func():
		if ResourceLoader.exists(scene_path):
			get_tree().change_scene_to_file(scene_path)
		else:
			push_warning("MainMenu: Scene '%s' is not yet present on disk. Returning to menu." % scene_path)
			# Fallback fade-in if scene is not yet generated
			var return_tween := create_tween()
			return_tween.tween_property(fade_overlay, "modulate:a", 0.0, 0.35)
			return_tween.tween_callback(func():
				fade_overlay.visible = false
				btn_sandbox.disabled = false
				btn_campaign.disabled = false
				btn_settings.disabled = false
				btn_credits.disabled = false
				btn_exit.disabled = false
				_is_transitioning = false
				btn_sandbox.grab_focus()
			)
	)

# =============================================================================
# BUTTON SIGNAL HANDLERS
# =============================================================================

func _on_btn_sandbox_pressed() -> void:
	transition_to_laboratory(SCENE_SANDBOX_LAB)


func _on_btn_campaign_pressed() -> void:
	transition_to_laboratory(SCENE_ANALYTICAL_LAB)


func _on_btn_settings_pressed() -> void:
	_play_click_sfx()
	credits_panel.visible = false
	settings_panel.visible = true
	settings_panel.modulate = Color(1.0, 1.0, 1.0, 0.0)

	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(settings_panel, "modulate:a", 1.0, 0.25)
	btn_settings_close.grab_focus()


func _on_btn_settings_close_pressed() -> void:
	_play_click_sfx()
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_IN)
	tween.tween_property(settings_panel, "modulate:a", 0.0, 0.18)
	tween.tween_callback(func():
		settings_panel.visible = false
		btn_settings.grab_focus()
	)


func _on_btn_credits_pressed() -> void:
	_play_click_sfx()
	settings_panel.visible = false
	credits_panel.visible = true
	credits_panel.modulate = Color(1.0, 1.0, 1.0, 0.0)

	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(credits_panel, "modulate:a", 1.0, 0.25)
	btn_credits_close.grab_focus()


func _on_btn_credits_close_pressed() -> void:
	_play_click_sfx()
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC)
	tween.set_ease(Tween.EASE_IN)
	tween.tween_property(credits_panel, "modulate:a", 0.0, 0.18)
	tween.tween_callback(func():
		credits_panel.visible = false
		btn_credits.grab_focus()
	)


func _on_btn_exit_pressed() -> void:
	_play_click_sfx()
	# Save state before quitting
	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.save_game()

	# Smooth fade out before quit
	fade_overlay.visible = true
	var tween := create_tween()
	tween.tween_property(fade_overlay, "modulate:a", 1.0, 0.3)
	tween.tween_callback(func(): get_tree().quit())

# =============================================================================
# SETTINGS EVENT HANDLERS
# =============================================================================

func _on_graphics_preset_selected(index: int) -> void:
	_play_click_sfx()
	match index:
		0:
			apply_graphics_preset("low")
		2:
			apply_graphics_preset("high")
		_:
			apply_graphics_preset("balanced")


func _on_input_mode_selected(index: int) -> void:
	_play_click_sfx()
	if index == 1:
		apply_input_mode("webcam_tracker")
	else:
		apply_input_mode("desktop")


func _on_master_slider_changed(value: float) -> void:
	_update_volume_label(lbl_master_val, value)
	_apply_audio_volume("Master", value)
	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.set_setting("master_volume", value)


func _on_sfx_slider_changed(value: float) -> void:
	_update_volume_label(lbl_sfx_val, value)
	_apply_audio_volume("SFX", value)
	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.set_setting("sfx_volume", value)


func _on_ambience_slider_changed(value: float) -> void:
	_update_volume_label(lbl_ambience_val, value)
	_apply_audio_volume("Ambience", value)
	var save_mgr = _get_save_manager()
	if save_mgr != null:
		save_mgr.set_setting("ambience_volume", value)

# =============================================================================
# AUDIO FEEDBACK HELPERS
# =============================================================================

func _play_click_sfx() -> void:
	if sfx_click and sfx_click.stream:
		sfx_click.play()


func _play_hover_sfx() -> void:
	if sfx_hover and sfx_hover.stream and not _is_transitioning:
		sfx_hover.play()
