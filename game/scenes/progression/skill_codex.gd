# Athanor Ascension — Skill Codex
#
# The progression screen the GDDs already specified but the build never had:
# four tracks, the real XP curve, and every milestone's apparatus, reagent and
# ability unlocks read straight from data/progression/skills.json. Nothing here
# is hand-authored per track; adding a milestone to the JSON adds it here.
extends Control

const HUB_SCENE: String = "res://scenes/laboratories/lab_hub.tscn"
const PRACTICUM_SCENE: String = "res://scenes/laboratories/titration_practicum.tscn"

const BG := Color(0.026, 0.037, 0.048, 1.0)
const PANEL := Color(0.052, 0.068, 0.084, 0.96)
const TEXT := Color(0.84, 0.90, 0.93)
const DIM := Color(0.50, 0.60, 0.66)
const CYAN := Color(0.25, 0.85, 0.92)
const AMBER := Color(1.0, 0.72, 0.28)
const GREEN := Color(0.40, 0.85, 0.65)
const GRID := Color(0.16, 0.24, 0.28, 0.7)

var _track_ids: Array[String] = []
var _selected: int = 0

var _track_name: Label
var _track_meta: Label
var _level_label: Label
var _rank_label: Label
var _xp_line: Label
var _bar: ProgressBar
var _milestones: RichTextLabel
var _ledger: RichTextLabel
var _track_list: ItemList
var _encourage: Label


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_collect_tracks()
	_build_ui()
	_refresh_all()
	var skills := _skills()
	if skills != null and skills.has_signal("xp_gained"):
		skills.xp_gained.connect(_on_xp_gained)


func _skills() -> Node:
	return get_node_or_null("/root/SkillManager")


func _collect_tracks() -> void:
	_track_ids.clear()
	var skills := _skills()
	if skills == null:
		return
	var tracks: Dictionary = skills.get_tracks()
	for id in ["chemistry", "biology", "forensics", "engineering"]:
		if tracks.has(id):
			_track_ids.append(id)
	for id in tracks.keys():
		if not _track_ids.has(str(id)):
			_track_ids.append(str(id))


func _build_ui() -> void:
	var title := Label.new()
	title.text = "SKILL CODEX  ·  DISCIPLINE LEDGER"
	title.position = Vector2(26, 16)
	title.add_theme_font_size_override("font_size", 21)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var sub := Label.new()
	sub.text = "%d Disciplines · Complete exponential progression (Lv. 1–120) · Unlocks read from skills.json" % _track_ids.size()
	sub.position = Vector2(26, 44)
	sub.add_theme_font_size_override("font_size", 11)
	sub.add_theme_color_override("font_color", DIM)
	add_child(sub)

	var back := Button.new()
	back.text = "← Lab network"
	back.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	back.offset_left = -176.0
	back.offset_right = -22.0
	back.offset_top = 14.0
	back.offset_bottom = 44.0
	back.pressed.connect(func() -> void: get_tree().change_scene_to_file(HUB_SCENE))
	add_child(back)

	var list_label := Label.new()
	list_label.text = "TRACKS"
	list_label.position = Vector2(26, 82)
	list_label.add_theme_font_size_override("font_size", 10)
	list_label.add_theme_color_override("font_color", DIM)
	add_child(list_label)

	_track_list = ItemList.new()
	_track_list.position = Vector2(26, 102)
	_track_list.custom_minimum_size = Vector2(262, 474)
	_track_list.add_theme_font_size_override("font_size", 12)
	_track_list.item_selected.connect(_on_track_selected)
	add_child(_track_list)

	var practice := Button.new()
	practice.text = "🧪  Titration practicum"
	practice.position = Vector2(26, 590)
	practice.custom_minimum_size = Vector2(262, 38)
	practice.pressed.connect(func() -> void: get_tree().change_scene_to_file(PRACTICUM_SCENE))
	add_child(practice)

	var practice_hint := Label.new()
	practice_hint.text = "Real equilibrium curve · awards Chemistry XP"
	practice_hint.position = Vector2(26, 632)
	practice_hint.add_theme_font_size_override("font_size", 10)
	practice_hint.add_theme_color_override("font_color", DIM)
	add_child(practice_hint)

	_encourage = Label.new()
	_encourage.position = Vector2(26, 662)
	_encourage.custom_minimum_size = Vector2(262, 40)
	_encourage.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_encourage.add_theme_font_size_override("font_size", 10)
	_encourage.add_theme_color_override("font_color", AMBER)
	add_child(_encourage)

	_track_name = Label.new()
	_track_name.position = Vector2(312, 82)
	_track_name.custom_minimum_size = Vector2(520, 34)
	_track_name.add_theme_font_size_override("font_size", 24)
	_track_name.add_theme_color_override("font_color", TEXT)
	add_child(_track_name)

	_track_meta = Label.new()
	_track_meta.position = Vector2(312, 116)
	_track_meta.custom_minimum_size = Vector2(520, 40)
	_track_meta.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_track_meta.add_theme_font_size_override("font_size", 11)
	_track_meta.add_theme_color_override("font_color", DIM)
	add_child(_track_meta)

	_level_label = Label.new()
	_level_label.position = Vector2(312, 166)
	_level_label.add_theme_font_size_override("font_size", 38)
	_level_label.add_theme_color_override("font_color", CYAN)
	add_child(_level_label)

	_rank_label = Label.new()
	_rank_label.position = Vector2(418, 178)
	_rank_label.custom_minimum_size = Vector2(400, 24)
	_rank_label.add_theme_font_size_override("font_size", 13)
	_rank_label.add_theme_color_override("font_color", AMBER)
	add_child(_rank_label)

	_bar = ProgressBar.new()
	_bar.position = Vector2(312, 222)
	_bar.custom_minimum_size = Vector2(516, 14)
	_bar.show_percentage = false
	_bar.max_value = 1.0
	_bar.step = 0.001
	add_child(_bar)

	_xp_line = Label.new()
	_xp_line.position = Vector2(312, 242)
	_xp_line.custom_minimum_size = Vector2(520, 18)
	_xp_line.add_theme_font_size_override("font_size", 10)
	_xp_line.add_theme_color_override("font_color", DIM)
	add_child(_xp_line)

	var ms_label := Label.new()
	ms_label.text = "MILESTONE LADDER"
	ms_label.position = Vector2(312, 272)
	ms_label.add_theme_font_size_override("font_size", 10)
	ms_label.add_theme_color_override("font_color", DIM)
	add_child(ms_label)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(312, 292)
	scroll.custom_minimum_size = Vector2(520, 396)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)

	_milestones = RichTextLabel.new()
	_milestones.bbcode_enabled = true
	_milestones.fit_content = true
	_milestones.custom_minimum_size = Vector2(500, 0)
	_milestones.add_theme_font_size_override("normal_font_size", 11)
	_milestones.add_theme_font_size_override("bold_font_size", 13)
	scroll.add_child(_milestones)

	var ledger_label := Label.new()
	ledger_label.text = "UNLOCK LEDGER"
	ledger_label.position = Vector2(858, 82)
	ledger_label.add_theme_font_size_override("font_size", 10)
	ledger_label.add_theme_color_override("font_color", DIM)
	add_child(ledger_label)

	var ledger_scroll := ScrollContainer.new()
	ledger_scroll.position = Vector2(858, 102)
	ledger_scroll.custom_minimum_size = Vector2(392, 540)
	ledger_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(ledger_scroll)

	_ledger = RichTextLabel.new()
	_ledger.bbcode_enabled = true
	_ledger.fit_content = true
	_ledger.custom_minimum_size = Vector2(372, 0)
	_ledger.add_theme_font_size_override("normal_font_size", 11)
	ledger_scroll.add_child(_ledger)


func _refresh_all() -> void:
	var skills := _skills()
	if skills == null:
		return
	_track_list.clear()
	for id in _track_ids:
		var track: Dictionary = skills.get_track(id)
		var level: int = skills.get_level(id)
		var display := str(track.get("display_name", id)).split(":")[0]
		_track_list.add_item("%s  ·  Lv %d" % [display, level])
	if not _track_ids.is_empty():
		_track_list.select(clampi(_selected, 0, _track_ids.size() - 1))
		_refresh_track(_selected)


func _on_track_selected(index: int) -> void:
	_selected = index
	_refresh_track(index)


func _refresh_track(index: int) -> void:
	var skills := _skills()
	if skills == null or index < 0 or index >= _track_ids.size():
		return
	var id := _track_ids[index]
	var track: Dictionary = skills.get_track(id)
	var level: int = skills.get_level(id)
	var xp: int = skills.get_xp(id)
	var progress: float = skills.get_progress(id)
	var span: Dictionary = skills.get_level_span(id)
	var colour := Color.from_string(str(track.get("color_hex", "#25d9eb")), CYAN)

	_track_name.text = str(track.get("display_name", id))
	_track_name.add_theme_color_override("font_color", colour)
	_track_meta.text = str(track.get("description", ""))
	_level_label.text = "LV %d" % level
	_level_label.add_theme_color_override("font_color", colour)
	_rank_label.text = str(skills.get_rank_title(level))
	_bar.value = progress
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.10, 0.13, 0.15, 1.0)
	bg.set_corner_radius_all(2)
	var fill := StyleBoxFlat.new()
	fill.bg_color = colour
	fill.set_corner_radius_all(2)
	_bar.add_theme_stylebox_override("background", bg)
	_bar.add_theme_stylebox_override("fill", fill)
	_xp_line.text = "%s XP  ·  %d / %d into level %d  ·  %.1f%%" % [_format_int(xp), int(span.get("into", 0)), int(span.get("span", 0)), level, progress * 100.0]

	var milestones: Array = skills.get_milestones(id)
	var body := ""
	for milestone in milestones:
		var ms_level := int(milestone.get("level", 1))
		var unlocked := level >= ms_level
		var marker := "[color=#3ddc97]◆[/color]" if unlocked else "[color=#42525b]◇[/color]"
		var title_colour := "#dfe8ec" if unlocked else "#6c7d86"
		body += "%s  [color=%s][b]Lv %d · %s[/b][/color]\n" % [marker, title_colour, ms_level, str(milestone.get("title", ""))]
		body += "     [color=#8b9aa4]%s[/color]\n" % str(milestone.get("description", ""))
		var apparatus: Array = milestone.get("unlocked_apparatus", [])
		var abilities: Array = milestone.get("unlocked_abilities", [])
		if not apparatus.is_empty():
			body += "     [color=#5fb8c4]Apparatus[/color]  %s\n" % ", ".join(_prefix(apparatus, 3))
		if not abilities.is_empty():
			body += "     [color=#c9a24a]Ability[/color]    %s\n" % ", ".join(_prefix(abilities, 2))
		body += "\n"
	_milestones.text = body

	var next_milestone: Dictionary = skills.get_next_milestone(id)
	var ledger := "[b]Unlocked at your current level[/b]\n\n"
	ledger += "[color=#5fb8c4]APPARATUS · %d[/color]\n%s\n\n" % [skills.get_unlocked_apparatus(id).size(), _bullet(skills.get_unlocked_apparatus(id), 8)]
	ledger += "[color=#3ddc97]REAGENTS · %d[/color]\n%s\n\n" % [skills.get_unlocked_reagents(id).size(), _bullet(skills.get_unlocked_reagents(id), 8)]
	ledger += "[color=#c9a24a]ABILITIES · %d[/color]\n%s\n\n" % [skills.get_unlocked_abilities(id).size(), _bullet(skills.get_unlocked_abilities(id), 8)]
	if not next_milestone.is_empty():
		ledger += "[b]Next gate[/b]\n[color=#ffb84a]Lv %d · %s[/color]\n%s" % [
			int(next_milestone.get("level", 1)),
			str(next_milestone.get("title", "")),
			str(next_milestone.get("description", ""))
		]
	else:
		ledger += "[color=#3ddc97]Track mastered. Every listed unlock is available.[/color]"
	_ledger.text = ledger

	if not next_milestone.is_empty():
		var remaining := int(next_milestone.get("level", 1)) - level
		_encourage.text = "%d level%s to “%s”. Real bench work earns XP." % [
			remaining, "" if remaining == 1 else "s", str(next_milestone.get("title", ""))
		]
	else:
		_encourage.text = "Track complete. Use the practicum to keep your technique sharp."


func _on_xp_gained(_skill_id: String, _amount: int, _total: int, _level: int, _reason: String) -> void:
	_refresh_all()


func _prefix(values: Array, count: int) -> Array[String]:
	var out: Array[String] = []
	for i in range(mini(count, values.size())):
		out.append(str(values[i]))
	if values.size() > count:
		out.append("+%d more" % (values.size() - count))
	return out


func _bullet(values: Array, count: int) -> String:
	if values.is_empty():
		return "[color=#4a5a63]None yet.[/color]"
	var lines: Array[String] = []
	for i in range(mini(count, values.size())):
		lines.append("· %s" % str(values[i]))
	if values.size() > count:
		lines.append("· +%d more" % (values.size() - count))
	return "\n".join(lines)


func _format_int(value: int) -> String:
	var text := str(value)
	var out := ""
	var count := 0
	for i in range(text.length() - 1, -1, -1):
		out = text[i] + out
		count += 1
		if count % 3 == 0 and i > 0:
			out = "," + out
	return out


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 70), Vector2(size.x, 70), GRID, 1.0)
	draw_rect(Rect2(12, 74, 290, 628), PANEL, true)
	draw_rect(Rect2(302, 74, 540, 628), Color(0.045, 0.06, 0.074, 0.82), true)
	draw_rect(Rect2(302, 74, 2, 628), Color(CYAN.r, CYAN.g, CYAN.b, 0.35), true)
	draw_rect(Rect2(848, 74, 420, 628), PANEL, true)
