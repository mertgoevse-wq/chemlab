# Athanor Ascension — Laboratory Network Hub
# The working entry point into the world: a data-driven index of every laboratory
# archetype and suit in game/data/labs/labs.json. Laboratories that already have a
# playable terminal launch it; blueprint-only labs say so instead of pretending.
#
# This replaces the old "drop the player into an empty 3D room" flow.

extends Control

const LABS_PATH: String = "res://data/labs/labs.json"
const SCENE_GENOME: String = "res://scenes/genomics/genome_browser.tscn"
const SCENE_ACCELERATOR: String = "res://scenes/laboratories/accelerator_lab.tscn"
const SCENE_FUSOR: String = "res://scenes/laboratories/fusor_lab.tscn"
const SCENE_BENCH_3D: String = "res://scenes/laboratories/analytical_lab.tscn"
const SCENE_TITRATION: String = "res://scenes/laboratories/titration_practicum.tscn"
const SCENE_CODEX: String = "res://scenes/progression/skill_codex.tscn"
const SCENE_MENU: String = "res://scenes/main_menu/main_menu.tscn"

const PLAYABLE: Dictionary = {
	"genomics_lab": SCENE_GENOME,
	"accelerator": SCENE_ACCELERATOR,
	"fusor_workshop": SCENE_FUSOR,
	"analytical_lab": SCENE_BENCH_3D
}

const BG: Color = Color(0.026, 0.037, 0.048, 1.0)
const PANEL: Color = Color(0.052, 0.068, 0.084, 0.96)
const TEXT: Color = Color(0.83, 0.89, 0.92)
const DIM: Color = Color(0.5, 0.6, 0.66)
const CYAN: Color = Color(0.25, 0.85, 0.92)
const AMBER: Color = Color(1.0, 0.71, 0.28)
const RED: Color = Color(1.0, 0.4, 0.36)
const GREEN: Color = Color(0.4, 0.85, 0.65)

var _data: Dictionary = {}
var _labs: Array = []
var _suits: Array = []
var _selected_lab: int = 0
var _selected_suit: int = 0

var _lab_list: ItemList
var _detail: RichTextLabel
var _suit_info: RichTextLabel
var _suit_opt: OptionButton
var _enter_btn: Button
var _status: Label


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_load_data()
	_build_ui()
	if not _labs.is_empty():
		# Open on the first playable room, not on a blueprint the player
		# cannot enter — the hub's first impression should be an open door.
		var start_index := 0
		for i in range(_labs.size()):
			if PLAYABLE.has(str((_labs[i] as Dictionary).get("id", ""))):
				start_index = i
				break
		_lab_list.select(start_index)
		_on_lab_selected(start_index)


func _load_data() -> void:
	if not FileAccess.file_exists(LABS_PATH):
		push_error("LabHub: %s missing" % LABS_PATH)
		return
	var file := FileAccess.open(LABS_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("LabHub: invalid labs.json")
		return
	_data = parsed
	_labs = _data.get("labs", [])
	_suits = _data.get("suits", [])


func _build_ui() -> void:
	var title := Label.new()
	title.text = "ATHANOR ASCENSION  ·  LABORATORY NETWORK"
	title.position = Vector2(26.0, 18.0)
	title.add_theme_font_size_override("font_size", 21)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var sub := Label.new()
	sub.text = "%d laboratory archetypes · %d suits · 4 live terminals + practicum" % [_labs.size(), _suits.size()]
	sub.position = Vector2(26.0, 46.0)
	sub.add_theme_font_size_override("font_size", 11)
	sub.add_theme_color_override("font_color", DIM)
	add_child(sub)

	var back := Button.new()
	back.text = "← Main menu"
	back.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	back.offset_left = -180.0
	back.offset_right = -22.0
	back.offset_top = 16.0
	back.offset_bottom = 46.0
	back.pressed.connect(func(): get_tree().change_scene_to_file(SCENE_MENU))
	add_child(back)

	_lab_list = ItemList.new()
	_lab_list.position = Vector2(26.0, 78.0)
	_lab_list.custom_minimum_size = Vector2(336.0, 600.0)
	_lab_list.add_theme_font_size_override("font_size", 12)
	_lab_list.item_selected.connect(_on_lab_selected)
	add_child(_lab_list)
	for i in range(_labs.size()):
		var lab: Dictionary = _labs[i]
		var tag := "LIVE" if PLAYABLE.has(str(lab.get("id", ""))) else "BLUEPRINT"
		_lab_list.add_item("%s  [%s]" % [str(lab.get("name", "")), tag])

	_detail = RichTextLabel.new()
	_detail.bbcode_enabled = true
	_detail.position = Vector2(382.0, 78.0)
	_detail.custom_minimum_size = Vector2(516.0, 520.0)
	_detail.add_theme_font_size_override("normal_font_size", 12)
	_detail.add_theme_font_size_override("bold_font_size", 14)
	add_child(_detail)

	_enter_btn = Button.new()
	_enter_btn.text = "▶ Enter laboratory"
	_enter_btn.position = Vector2(382.0, 606.0)
	_enter_btn.custom_minimum_size = Vector2(244.0, 40.0)
	_enter_btn.pressed.connect(_on_enter)
	add_child(_enter_btn)

	# The 3D analytical bench is still PARTIAL; routing players into an empty
	# room was the bug this hub replaced. Ship the working practicum instead of
	# a button that drops the player into unfinished geometry.
	var titration := Button.new()
	titration.text = "🧪 Titration practicum"
	titration.position = Vector2(636.0, 606.0)
	titration.custom_minimum_size = Vector2(200.0, 40.0)
	titration.pressed.connect(func(): get_tree().change_scene_to_file(SCENE_TITRATION))
	add_child(titration)

	var codex := Button.new()
	codex.text = "◇ Skill codex & unlocks"
	codex.position = Vector2(382.0, 652.0)
	codex.custom_minimum_size = Vector2(454.0, 30.0)
	codex.pressed.connect(func(): get_tree().change_scene_to_file(SCENE_CODEX))
	add_child(codex)

	var right_top := 78.0
	var suit_label := Label.new()
	suit_label.text = "LABORATORY SUITS"
	suit_label.position = Vector2(922.0, right_top)
	suit_label.add_theme_font_size_override("font_size", 10)
	suit_label.add_theme_color_override("font_color", DIM)
	add_child(suit_label)

	_suit_opt = OptionButton.new()
	_suit_opt.position = Vector2(922.0, right_top + 20.0)
	_suit_opt.custom_minimum_size = Vector2(330.0, 34.0)
	for suit in _suits:
		_suit_opt.add_item(str(suit.get("name", suit.get("id", "?"))))
	_suit_opt.item_selected.connect(_on_suit_selected)
	add_child(_suit_opt)

	_suit_info = RichTextLabel.new()
	_suit_info.bbcode_enabled = true
	_suit_info.position = Vector2(922.0, right_top + 66.0)
	_suit_info.custom_minimum_size = Vector2(330.0, 330.0)
	_suit_info.add_theme_font_size_override("normal_font_size", 11)
	add_child(_suit_info)

	var equip := Button.new()
	equip.text = "Wear suit for next session"
	equip.position = Vector2(922.0, right_top + 402.0)
	equip.custom_minimum_size = Vector2(330.0, 36.0)
	equip.pressed.connect(_on_equip_suit)
	add_child(equip)

	_status = Label.new()
	_status.position = Vector2(26.0, 690.0)
	_status.add_theme_font_size_override("font_size", 11)
	_status.add_theme_color_override("font_color", DIM)
	_status.text = "Select a laboratory. Live terminals are real, blueprint entries are specified but not yet fitted out."
	add_child(_status)

	if not _suits.is_empty():
		_on_suit_selected(0)


func _on_lab_selected(index: int) -> void:
	if index < 0 or index >= _labs.size():
		return
	_selected_lab = index
	var lab: Dictionary = _labs[index]
	var hazards: Array = lab.get("hazards", [])
	var equipment: Array = lab.get("equipment", [])
	var playable := PLAYABLE.has(str(lab.get("id", "")))
	var status_color := GREEN if playable else AMBER
	var status_text := "LIVE TERMINAL" if playable else "BLUEPRINT · SPECIFIED, NOT YET FITTED OUT"

	_detail.text = "[font_size=24][b]%s[/b][/font_size]\n[color=#8b9aa4]%s · Tier %d · %s[/color]\n\n[color=#%s]%s[/color]\n\n[b]Containment[/b]  %s\n[b]Cleanroom[/b]   %s\n\n[b]Hazards[/b]\n• %s\n\n[b]Equipment[/b]\n• %s\n\n[i]%s[/i]" % [
		str(lab.get("name", "")),
		str(lab.get("category", "")).replace("_", " ").capitalize(),
		int(lab.get("tier", 1)),
		str(lab.get("containment", "")),
		status_color.to_html(false),
		status_text,
		str(lab.get("containment", "")),
		str(lab.get("cleanroom", "")),
		"\n• ".join(_string_array(hazards)),
		"\n• ".join(_string_array(equipment)),
		str(lab.get("notes", ""))
	]
	_enter_btn.disabled = not playable
	_enter_btn.text = "▶ Enter laboratory" if playable else "Blueprint — see roadmap"


func _on_enter() -> void:
	var lab: Dictionary = _labs[_selected_lab]
	var lab_id := str(lab.get("id", ""))
	if not PLAYABLE.has(lab_id):
		_status.text = "%s has no playable terminal yet. Its specification is in docs/ROADMAP.md." % str(lab.get("name", ""))
		return
	_status.text = "Entering %s…" % str(lab.get("name", ""))
	get_tree().change_scene_to_file(str(PLAYABLE[lab_id]))


func _on_suit_selected(index: int) -> void:
	if index < 0 or index >= _suits.size():
		return
	_selected_suit = index
	var suit: Dictionary = _suits[index]
	var p: Dictionary = suit.get("protection", {})
	var pen: Dictionary = suit.get("penalty", {})
	_suit_info.text = "[b]%s[/b]\n[color=#8b9aa4]Tier %d · %s[/color]\n\n[b]Protection[/b]\n%s\n\n[b]Penalty[/b]\n%s\n\n[i]%s[/i]" % [
		str(suit.get("name", "")),
		int(suit.get("tier", 1)),
		"Unlocked" if str(suit.get("unlock", "")) == "start" else "Unlock: %s" % str(suit.get("unlock", "")),
		_bars(p, GREEN),
		_bars(pen, RED),
		str(suit.get("notes", ""))
	]


func _on_equip_suit() -> void:
	if _suits.is_empty():
		return
	var suit: Dictionary = _suits[_selected_suit]
	var p: Dictionary = suit.get("protection", {})
	var total := 0.0
	for key in p.keys():
		total += float(p[key])
	var average := total / maxf(float(p.size()), 1.0)
	var vitals := get_node_or_null("/root/PlayerVitals")
	if vitals != null and vitals.has_method("set_hazard_protection"):
		vitals.set_hazard_protection(clampf(1.0 - average * 0.85, 0.08, 1.0))
	_status.text = "Equipped %s. Protection applied to the next accident; mobility penalty is narrative for now." % str(suit.get("name", ""))
	_status.add_theme_color_override("font_color", GREEN)


func _bars(values: Dictionary, color: Color) -> String:
	var lines: Array[String] = []
	var keys := values.keys()
	keys.sort()
	for key in keys:
		var value := clampf(float(values[key]), 0.0, 1.0)
		var filled := int(round(value * 10.0))
		lines.append("%s  %s%s  %d%%" % [str(key).capitalize(), "█".repeat(filled), "·".repeat(10 - filled), int(value * 100.0)])
	return "\n".join(lines)


func _string_array(values: Array) -> Array[String]:
	var out: Array[String] = []
	for value in values:
		out.append(str(value))
	return out


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 66), Vector2(size.x, 66), Color(0.16, 0.24, 0.28, 0.7), 1.0)
	draw_rect(Rect2(12, 70, 358, 616), PANEL, true)
	draw_rect(Rect2(370, 70, 540, 600), Color(0.045, 0.06, 0.074, 0.8), true)
	draw_rect(Rect2(910, 70, 356, 600), PANEL, true)
	# Subtle vertical accent.
	draw_rect(Rect2(370, 70, 2, 600), Color(CYAN.r, CYAN.g, CYAN.b, 0.4), true)
