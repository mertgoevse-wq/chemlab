# ChemLab Quest HUD Overlay Controller (Godot 4 Engine)
# Attached to game/scenes/quests/quest_overlay.tscn
# Renders active quest objectives, dynamic checklist ticks, OSHA safety alerts, and fanfare celebration.

extends CanvasLayer
class_name QuestOverlay

# Node references
@export var quest_card_panel: PanelContainer
@export var quest_title_label: Label
@export var quest_tier_label: Label
@export var objectives_container: VBoxContainer

@export var safety_meter_bar: ProgressBar
@export var safety_score_label: Label
@export var safety_grade_label: Label

@export var warning_banner_panel: PanelContainer
@export var warning_title_label: Label
@export var warning_msg_label: Label
@export var warning_osha_label: Label

@export var celebration_modal: Control
@export var celebration_title_label: Label
@export var celebration_xp_label: Label
@export var celebration_stars_label: Label
@export var celebration_continue_btn: Button

# Audio Stream Players
@export var sfx_tick: AudioStreamPlayer
@export var sfx_warning: AudioStreamPlayer
@export var sfx_fanfare: AudioStreamPlayer

# Styling colors
const COLOR_COMPLETED = Color(0.2, 0.9, 0.4, 1.0)
const COLOR_ACTIVE = Color(1.0, 1.0, 1.0, 1.0)
const COLOR_PENDING = Color(0.6, 0.65, 0.7, 0.6)
const COLOR_HAZARD = Color(1.0, 0.2, 0.2, 1.0)
const COLOR_CAUTION = Color(1.0, 0.75, 0.1, 1.0)
const COLOR_OPTIMAL = Color(0.1, 0.85, 0.45, 1.0)

var warning_timer: SceneTreeTimer = null

func _ready() -> void:
	if warning_banner_panel:
		warning_banner_panel.visible = false
	if celebration_modal:
		celebration_modal.visible = false

	if celebration_continue_btn:
		celebration_continue_btn.pressed.connect(_on_continue_pressed)

	_connect_to_quest_manager()
	_refresh_hud_display()


func _connect_to_quest_manager() -> void:
	var qm = _get_quest_manager()
	if not qm:
		return

	qm.quest_started.connect(_on_quest_started)
	qm.objective_progressed.connect(_on_objective_progressed)
	qm.objective_completed.connect(_on_objective_completed)
	qm.quest_completed.connect(_on_quest_completed)
	qm.safety_score_updated.connect(_on_safety_score_updated)
	qm.safety_warning_triggered.connect(_on_safety_warning_triggered)
	qm.fanfare_celebration_started.connect(_on_fanfare_celebration_started)


func _get_quest_manager() -> Node:
	if Engine.has_singleton("QuestManager"):
		return Engine.get_singleton("QuestManager")
	var root = get_tree().root if get_tree() else null
	if root and root.has_node("QuestManager"):
		return root.get_node("QuestManager")
	return null

# =============================================================================
# HUD RENDERING & REFRESH
# =============================================================================

func _refresh_hud_display() -> void:
	var qm = _get_quest_manager()
	if not qm:
		return

	var q = qm.get_active_quest()
	if q.is_empty():
		return

	if quest_title_label:
		quest_title_label.text = str(q.get("title", "Laboratory Quest"))
	if quest_tier_label:
		quest_tier_label.text = "Tier %d: %s" % [int(q.get("tier", 1)), str(q.get("category", "General"))]

	_render_objectives_list(q.get("objectives", []))
	_update_safety_meter(qm.current_safety_score)


func _render_objectives_list(objectives: Array) -> void:
	if not objectives_container:
		return

	# Clear existing objective row widgets
	for child in objectives_container.get_children():
		child.queue_free()

	for i in range(objectives.size()):
		var obj = objectives[i] as Dictionary
		var row = _create_objective_row(i, obj)
		objectives_container.add_child(row)


func _create_objective_row(idx: int, obj: Dictionary) -> Control:
	var hbox = HBoxContainer.new()
	hbox.name = "ObjectiveRow_%d" % idx
	hbox.custom_minimum_size = Vector2(0, 32)
	hbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# 1. Checklist Tick Box / Checkmark
	var check_label = Label.new()
	check_label.name = "CheckMark"
	check_label.custom_minimum_size = Vector2(24, 0)
	var is_done = bool(obj.get("is_completed", false))
	var is_active = bool(obj.get("is_active", false))

	if is_done:
		check_label.text = "[✓]"
		check_label.modulate = COLOR_COMPLETED
	elif is_active:
		check_label.text = "[▶]"
		check_label.modulate = COLOR_CAUTION
	else:
		check_label.text = "[ ]"
		check_label.modulate = COLOR_PENDING
	hbox.add_child(check_label)

	# 2. Objective Description & Progress Container
	var vbox = VBoxContainer.new()
	vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var title_lbl = Label.new()
	title_lbl.name = "TitleLabel"
	title_lbl.text = str(obj.get("description", ""))
	title_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	if is_done:
		title_lbl.modulate = COLOR_COMPLETED
	elif is_active:
		title_lbl.modulate = COLOR_ACTIVE
	else:
		title_lbl.modulate = COLOR_PENDING
	vbox.add_child(title_lbl)

	# Fractional progress bar if target > 1.0 (e.g., 25.0 mL or 3 drops)
	var target = float(obj.get("target", 1.0))
	var current = float(obj.get("current", 0.0))
	var unit = str(obj.get("unit", ""))

	if target > 1.0:
		var prog_bar = ProgressBar.new()
		prog_bar.name = "ProgressBar"
		prog_bar.min_value = 0.0
		prog_bar.max_value = target
		prog_bar.value = current
		prog_bar.custom_minimum_size = Vector2(0, 8)
		prog_bar.show_percentage = false
		vbox.add_child(prog_bar)

		var val_lbl = Label.new()
		val_lbl.name = "ValueLabel"
		val_lbl.text = "%.1f / %.1f %s" % [current, target, unit]
		val_lbl.modulate = Color(0.7, 0.8, 0.9, 0.8)
		val_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		vbox.add_child(val_lbl)

	hbox.add_child(vbox)
	return hbox


func _update_safety_meter(score: float) -> void:
	if safety_meter_bar:
		safety_meter_bar.value = score

	if safety_score_label:
		safety_score_label.text = "%.0f%%" % score

	var color = COLOR_OPTIMAL
	var grade_text = "OSHA COMPLIANT"

	if score >= 85.0:
		color = COLOR_OPTIMAL
		grade_text = "OSHA COMPLIANT"
	elif score >= 65.0:
		color = COLOR_CAUTION
		grade_text = "SAFETY CAUTION"
	else:
		color = COLOR_HAZARD
		grade_text = "OSHA HAZARD ALERT"

	if safety_grade_label:
		safety_grade_label.text = grade_text
		safety_grade_label.modulate = color
	if safety_score_label:
		safety_score_label.modulate = color

# =============================================================================
# EVENT LISTENERS
# =============================================================================

func _on_quest_started(_qid: String, _qdata: Dictionary) -> void:
	_refresh_hud_display()


func _on_objective_progressed(_qid: String, _idx: int, _curr: float, _target: float, _done: bool) -> void:
	_refresh_hud_display()


func _on_objective_completed(_qid: String, _idx: int, _obj_data: Dictionary) -> void:
	_refresh_hud_display()
	if sfx_tick:
		sfx_tick.play()


func _on_safety_score_updated(new_score: float, _delta: float, _reason: String) -> void:
	_update_safety_meter(new_score)


func _on_safety_warning_triggered(severity: String, title: String, message: String, osha_code: String) -> void:
	if not warning_banner_panel:
		return

	if warning_title_label:
		warning_title_label.text = "⚠ %s [%s]" % [title, osha_code]
	if warning_msg_label:
		warning_msg_label.text = message
	if warning_osha_label:
		warning_osha_label.text = "Standard Ref: %s" % osha_code

	var color = COLOR_HAZARD if severity == "CRITICAL" else COLOR_CAUTION
	warning_banner_panel.modulate = color
	warning_banner_panel.visible = true

	if sfx_warning:
		sfx_warning.play()

	# Auto-hide after 5.0 seconds
	if warning_timer:
		warning_timer.timeout.disconnect(_on_warning_timeout)
	warning_timer = get_tree().create_timer(5.0)
	warning_timer.timeout.connect(_on_warning_timeout)


func _on_warning_timeout() -> void:
	if warning_banner_panel:
		var tween = create_tween()
		tween.tween_property(warning_banner_panel, "modulate:a", 0.0, 0.4)
		tween.tween_callback(func():
			warning_banner_panel.visible = false
			warning_banner_panel.modulate.a = 1.0
		)


func _on_fanfare_celebration_started(title: String, xp: int, stars: int) -> void:
	if not celebration_modal:
		return

	if celebration_title_label:
		celebration_title_label.text = "QUEST COMPLETE!\n%s" % title
	if celebration_xp_label:
		celebration_xp_label.text = "+%d XP" % xp
	if celebration_stars_label:
		var star_str = ""
		for s in range(stars):
			star_str += "★ "
		celebration_stars_label.text = star_str.strip_edges()

	celebration_modal.visible = true
	celebration_modal.scale = Vector2(0.8, 0.8)
	celebration_modal.modulate.a = 0.0

	var tween = create_tween().set_parallel(true)
	tween.tween_property(celebration_modal, "scale", Vector2.ONE, 0.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(celebration_modal, "modulate:a", 1.0, 0.3)

	if sfx_fanfare:
		sfx_fanfare.play()


func _on_quest_completed(_qid: String, _title: String, _xp: int, _score: float) -> void:
	_refresh_hud_display()


func _on_continue_pressed() -> void:
	if celebration_modal:
		celebration_modal.visible = false
