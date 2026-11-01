# ChemLab 3D Simulation HUD Controller (Godot 4.x Engine)
# Extends Node3D / CanvasLayer for immersive VR & Desktop scientific simulation.
# Controls:
# 1. 3D Spatial Overlay (Reagent Tags, Temperature Readouts, pH Spectrum Bar)
# 2. Holographic Virtual Hands with 3 interaction states:
#    - READY (Green): Hand open, tracking active, ready to pinch
#    - HOVER (Yellow): Near glassware (< 50mm proximity lock)
#    - HELD  (Blue): Glassware firmly gripped, kinematic parented
# 3. Top Bar HUD (Quest Objectives, Safety Alert Status, Story/Sandbox Mode Toggle)
# 4. Audio-Visual Feedback (Level-Up fanfare, Quest Complete arpeggio, Shockwaves)

extends CanvasLayer
class_name ChemLabHUD

# Enums
enum InteractionState { READY, HOVER, HELD }
enum SafetyStatus { OPTIMAL, CAUTION, HAZARD_ALERT }
enum GameMode { STORY, SANDBOX }

# Colors according to ChemLab Design System
const COLOR_GREEN_READY = Color(0.0, 1.0, 0.35, 1.0)
const COLOR_YELLOW_HOVER = Color(1.0, 0.85, 0.0, 1.0)
const COLOR_BLUE_HELD = Color(0.0, 0.55, 1.0, 1.0)

const COLOR_SAFETY_OPTIMAL = Color(0.10, 0.95, 0.35, 1.0)
const COLOR_SAFETY_CAUTION = Color(1.0, 0.65, 0.05, 1.0)
const COLOR_SAFETY_HAZARD = Color(1.0, 0.15, 0.15, 1.0)

# Signals
signal game_mode_changed(new_mode: GameMode)
signal quest_completed(quest_id: String, xp_awarded: int)
signal level_up_achieved(new_level: int, rank_title: String)
signal hand_interaction_state_changed(hand: String, new_state: InteractionState)

# Node references
@export var quest_title_label: Label
@export var quest_step_label: Label
@export var quest_progress_bar: ProgressBar

@export var safety_badge: PanelContainer
@export var safety_label: Label
@export var safety_detail_label: Label

@export var mode_toggle_btn: Button
@export var mode_label: Label

@export var sfx_player_chime: AudioStreamPlayer
@export var sfx_player_fanfare: AudioStreamPlayer
@export var sfx_player_haptic: AudioStreamPlayer

@export var celebration_banner: Control
@export var celebration_particles: GPUParticles3D

# Internal State
var current_mode: GameMode = GameMode.STORY
var current_safety: SafetyStatus = SafetyStatus.OPTIMAL
var left_hand_state: InteractionState = InteractionState.READY
var right_hand_state: InteractionState = InteractionState.READY

# Audio Stream Preloads
var sound_quest_complete: AudioStream
var sound_level_up: AudioStream
var sound_pinch_ready: AudioStream
var sound_pinch_hover: AudioStream
var sound_pinch_grip: AudioStream
var sound_safety_alert: AudioStream

func _ready() -> void:
	load_audio_assets()
	set_game_mode(GameMode.STORY)
	set_safety_status(SafetyStatus.OPTIMAL, "PPE Active: Nitrile Gloves | Eye Shield | Fume Sash: 25 cm")
	set_quest_objective(
		"Belousov-Zhabotinsky Oscillation",
		"Heat 50 mL Malonic Acid Solution to 45.0 °C on magnetic stirrer.",
		2, 4, 65.0
	)
	if celebration_banner:
		celebration_banner.visible = false

func load_audio_assets() -> void:
	# Load synthesized 44.1kHz WAV assets from audio/ directory
	sound_quest_complete = load_audio_file("res://audio/sfx_quest_complete.wav")
	sound_level_up = load_audio_file("res://audio/sfx_level_up.wav")
	sound_pinch_ready = load_audio_file("res://audio/sfx_pinch_ready.wav")
	sound_pinch_hover = load_audio_file("res://audio/sfx_pinch_hover.wav")
	sound_pinch_grip = load_audio_file("res://audio/sfx_pinch_grip.wav")
	sound_safety_alert = load_audio_file("res://audio/sfx_safety_alert.wav")

func load_audio_file(path: String) -> AudioStream:
	if ResourceLoader.exists(path):
		return load(path)
	return null

# =============================================================================
# 1. Spatial 3D Overlay Controls
# =============================================================================

func update_reagent_tag(tag_node: Node3D, chemical_name: String, formula: String, concentration: float, temp_c: float) -> void:
	if not tag_node:
		return
	var label = tag_node.get_node_or_null("Label3D_Title") as Label3D
	if label:
		label.text = "%s (%s)" % [formula, chemical_name]
	var sub_label = tag_node.get_node_or_null("Label3D_Details") as Label3D
	if sub_label:
		sub_label.text = "Conc: %.2f M | Temp: %.1f °C" % [concentration, temp_c]

func update_heated_flask_temperature(hud_node: Node3D, current_temp: float, target_temp: float, is_heating: bool) -> void:
	if not hud_node:
		return
	var temp_label = hud_node.get_node_or_null("Label3D_Temp") as Label3D
	if temp_label:
		temp_label.text = "%.1f °C" % current_temp
		if current_temp > 95.0:
			temp_label.modulate = COLOR_SAFETY_HAZARD
		else:
			temp_label.modulate = Color(1.0, 0.65, 0.05, 1.0)

	var status_label = hud_node.get_node_or_null("Label3D_Status") as Label3D
	if status_label:
		status_label.text = "SET: %.1f °C | %s" % [target_temp, "HEATING ▲" if is_heating else "STABLE"]

func update_ph_cursor(ph_bar_node: Node3D, current_ph: float) -> void:
	if not ph_bar_node:
		return
	var needle = ph_bar_node.get_node_or_null("Needle") as Node3D
	if needle:
		# Map pH 0-14 to local X coordinate [-0.19 to +0.19]
		var clamped_ph = clampf(current_ph, 0.0, 14.0)
		var normalized_x = ((clamped_ph / 14.0) - 0.5) * 0.38
		needle.position.x = normalized_x

	var value_label = ph_bar_node.get_node_or_null("Label3D_Value") as Label3D
	if value_label:
		var state_str = "NEUTRAL"
		if current_ph < 6.5:
			state_str = "ACIDIC"
		elif current_ph > 7.5:
			state_str = "ALKALINE"
		value_label.text = "pH %.2f [%s]" % [current_ph, state_str]

# =============================================================================
# 2. Hand Feedback & Interaction States
# =============================================================================

func set_hand_state(is_right_hand: bool, state: InteractionState, target_object: Node3D = null) -> void:
	var hand_name = "Right" if is_right_hand else "Left"
	if is_right_hand:
		right_hand_state = state
	else:
		left_hand_state = state

	var color = COLOR_GREEN_READY
	var sfx: AudioStream = sound_pinch_ready

	match state:
		InteractionState.READY:
			color = COLOR_GREEN_READY
			sfx = sound_pinch_ready
		InteractionState.HOVER:
			color = COLOR_YELLOW_HOVER
			sfx = sound_pinch_hover
		InteractionState.HELD:
			color = COLOR_BLUE_HELD
			sfx = sound_pinch_grip

	if sfx and sfx_player_haptic:
		sfx_player_haptic.stream = sfx
		sfx_player_haptic.play()

	hand_interaction_state_changed.emit(hand_name, state)

# =============================================================================
# 3. Top Bar HUD Controls
# =============================================================================

func set_quest_objective(quest_title: String, step_desc: String, current_step: int, total_steps: int, progress_pct: float) -> void:
	if quest_title_label:
		quest_title_label.text = "QUEST: %s" % quest_title
	if quest_step_label:
		quest_step_label.text = "Step %d/%d: %s" % [current_step, total_steps, step_desc]
	if quest_progress_bar:
		quest_progress_bar.value = progress_pct

func set_safety_status(status: SafetyStatus, details: String) -> void:
	current_safety = status
	var color = COLOR_SAFETY_OPTIMAL
	var text = "SAFETY: OPTIMAL"

	match status:
		SafetyStatus.OPTIMAL:
			color = COLOR_SAFETY_OPTIMAL
			text = "SAFETY: OPTIMAL"
		SafetyStatus.CAUTION:
			color = COLOR_SAFETY_CAUTION
			text = "SAFETY: CAUTION"
		SafetyStatus.HAZARD_ALERT:
			color = COLOR_SAFETY_HAZARD
			text = "⚠ HAZARD ALERT"
			if sound_safety_alert and sfx_player_haptic:
				sfx_player_haptic.stream = sound_safety_alert
				sfx_player_haptic.play()

	if safety_label:
		safety_label.text = text
		safety_label.modulate = color
	if safety_detail_label:
		safety_detail_label.text = details

func set_game_mode(mode: GameMode) -> void:
	current_mode = mode
	if mode_label:
		if mode == GameMode.STORY:
			mode_label.text = "[STORY MODE]  Sandbox"
			mode_label.modulate = Color(0.0, 0.82, 1.0, 1.0)
		else:
			mode_label.text = "Story  [SANDBOX MODE]"
			mode_label.modulate = Color(1.0, 0.65, 0.05, 1.0)
	game_mode_changed.emit(mode)

func toggle_game_mode() -> void:
	if current_mode == GameMode.STORY:
		set_game_mode(GameMode.SANDBOX)
	else:
		set_game_mode(GameMode.STORY)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_focus_next"): # TAB key
		toggle_game_mode()

# =============================================================================
# 4. Audio-Visual Feedback for Level-Up and Quest Completion
# =============================================================================

func trigger_quest_completion(quest_title: String, xp_reward: int) -> void:
	# Audio: Shimmering C-major crystalline arpeggio
	if sound_quest_complete and sfx_player_chime:
		sfx_player_chime.stream = sound_quest_complete
		sfx_player_chime.play()

	# Visual: Expand celebratory particles and show trophy plate
	if celebration_particles:
		celebration_particles.restart()
		celebration_particles.emitting = true

	if celebration_banner:
		celebration_banner.visible = true
		var tween = create_tween().set_parallel(true)
		celebration_banner.modulate = Color(1, 1, 1, 0)
		celebration_banner.scale = Vector2(0.8, 0.8)
		tween.tween_property(celebration_banner, "modulate:a", 1.0, 0.35)
		tween.tween_property(celebration_banner, "scale", Vector2(1.0, 1.0), 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	quest_completed.emit(quest_title, xp_reward)

func trigger_level_up(new_level: int, rank_title: String) -> void:
	# Audio: Triumphant synth fanfare with sub-bass impact
	if sound_level_up and sfx_player_fanfare:
		sfx_player_fanfare.stream = sound_level_up
		sfx_player_fanfare.play()

	level_up_achieved.emit(new_level, rank_title)
