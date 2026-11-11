# Athanor Ascension — Organic Synthesis Terminal
# Playable aspirin protocol from design/gdd/synthesis-protocols.md.
#
# Four stages: weigh & charge -> reflux -> quench/recrystallise -> analytical
# assay. The evaluation is offline, deterministic and stoichiometric; the player
# can fail by missing catalyst, overheating, skipping the hood or rushing the
# reflux, and each failure teaches the actual constraint.
extends Control

const Chem = preload("res://scripts/labs/synthesis_chemistry.gd")
const Catalog = preload("res://scripts/labs/synthesis_catalog.gd")
const SCENE_HUB: String = "res://scenes/laboratories/lab_hub.tscn"

const BG: Color = Color(0.028, 0.038, 0.05, 1.0)
const PANEL: Color = Color(0.052, 0.068, 0.085, 0.97)
const PANEL_SOFT: Color = Color(0.045, 0.058, 0.073, 0.92)
const TEXT: Color = Color(0.83, 0.89, 0.92)
const DIM: Color = Color(0.52, 0.61, 0.67)
const CYAN: Color = Color(0.26, 0.85, 0.93)
const AMBER: Color = Color(1.0, 0.71, 0.29)
const RED: Color = Color(1.0, 0.41, 0.37)
const GREEN: Color = Color(0.42, 0.86, 0.67)
const GLASS: Color = Color(0.68, 0.82, 0.88, 0.22)

var _protocol: Dictionary = {}
var _stage: int = 1
var _mass_g: float = 13.8
var _anhydride_ml: float = 14.2
var _catalyst_drops: int = 5
var _stir_rpm: float = 450.0
var _temp_c: float = 70.0
var _reflux_min: float = 20.0
var _hood: bool = true
var _ice_c: float = 2.0
var _water_ml: float = 30.0
var _ethanol_ml: float = 15.0
var _seeded: bool = true
var _ppe: Dictionary = {"goggles": false, "gloves": false, "coat": false}

var _reflux_done: bool = false
var _submitted: bool = false
var _last_result: Dictionary = {}
var _batch_count: int = 0
var _time: float = 0.0

var _controls: VBoxContainer
var _report: RichTextLabel
var _status: Label
var _next_btn: Button
var _title_label: Label
var _subtitle_label: Label
var _briefing: RichTextLabel
var _category_opt: OptionButton
var _protocol_opt: OptionButton
var _protocol_list_cache: Array[Dictionary] = []

var _sandbox_mode: bool = true
var _sop_guide_active: bool = true
var _sop_modal: PanelContainer
var _sop_modal_text: RichTextLabel
var _btn_sop_toggle: Button
var _btn_auto_charge: Button
var _btn_sop_modal: Button
var _sandbox_badge: Label


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build_ui()
	_populate_categories()
	_set_stage(1)
	set_process(true)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _params() -> Dictionary:
	return {
		"protocol": _protocol,
		"protocol_id": str(_protocol.get("id", "aspirin")),
		"salicylic_mass_g": _mass_g,
		"anhydride_ml": _anhydride_ml,
		"reagent_a_mass": _mass_g,
		"reagent_b_amount": _anhydride_ml,
		"catalyst_drops": _catalyst_drops,
		"stir_rpm": _stir_rpm,
		"reflux_temp_c": _temp_c,
		"reflux_min": _reflux_min,
		"fume_hood": _hood,
		"ice_bath_c": _ice_c,
		"quench_water_ml": _water_ml,
		"recryst_ethanol_ml": _ethanol_ml,
		"seed_crystal": _seeded,
		"ppe": _ppe_ok()
	}


func _ppe_ok() -> bool:
	return bool(_ppe.get("goggles", false)) and bool(_ppe.get("gloves", false)) and bool(_ppe.get("coat", false))


# =============================================================================
# PROTOCOL CATALOG BINDINGS
# =============================================================================

func _populate_categories() -> void:
	if _category_opt == null:
		return
	_category_opt.clear()
	var cats: Array[String] = Catalog.get_categories()
	for i in range(cats.size()):
		_category_opt.add_item(cats[i], i)
	if not cats.is_empty():
		_populate_protocols_for_category(cats[0], "aspirin")
	else:
		_select_protocol("aspirin")


func _populate_protocols_for_category(cat_name: String, default_proto_id: String = "") -> void:
	if _protocol_opt == null:
		return
	_protocol_opt.clear()
	_protocol_list_cache = Catalog.get_protocols_in_category(cat_name)
	var select_idx: int = 0
	for i in range(_protocol_list_cache.size()):
		var p: Dictionary = _protocol_list_cache[i]
		_protocol_opt.add_item(str(p.get("name", "Unknown")), i)
		if not default_proto_id.is_empty() and str(p.get("id", "")) == default_proto_id:
			select_idx = i
	if not _protocol_list_cache.is_empty():
		_protocol_opt.selected = select_idx
		_select_protocol(str(_protocol_list_cache[select_idx].get("id", "aspirin")))


func _on_category_selected(idx: int) -> void:
	var cat_name: String = _category_opt.get_item_text(idx)
	_populate_protocols_for_category(cat_name)


func _on_protocol_selected(idx: int) -> void:
	if idx >= 0 and idx < _protocol_list_cache.size():
		var p: Dictionary = _protocol_list_cache[idx]
		_select_protocol(str(p.get("id", "")))


func _select_protocol(proto_id: String) -> void:
	_protocol = Catalog.get_protocol(proto_id)
	if _protocol.is_empty():
		_protocol = Catalog.get_protocol("aspirin")

	if _title_label != null:
		_title_label.text = "ORGANIC SYNTHESIS  ·  %s" % str(_protocol.get("name", "ACETYLSALICYLIC ACID")).to_upper()
	if _subtitle_label != null:
		var rA_name: String = str(_protocol.get("reagent_a", {}).get("name", "Reagent A"))
		var rB_name: String = str(_protocol.get("reagent_b", {}).get("name", "Reagent B"))
		var cat_name: String = str(_protocol.get("catalyst", {}).get("name", "H₂SO₄"))
		_subtitle_label.text = "%s + %s  ·  %s  ·  MW %.2f g/mol" % [rA_name, rB_name, cat_name, float(_protocol.get("mw", 180.16))]

	_submitted = false
	_last_result = {}
	_reflux_done = false

	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var reflux_info: Dictionary = _protocol.get("reflux", {})
	var workup_info: Dictionary = _protocol.get("workup", {})

	_mass_g = float(rA.get("default", 13.8))
	_anhydride_ml = float(rB.get("default", 14.2))
	_catalyst_drops = int(_protocol.get("catalyst", {}).get("default_drops", 5))
	_stir_rpm = float(reflux_info.get("stir_rpm", 450.0))
	_temp_c = float(reflux_info.get("default_temp", 70.0))
	_reflux_min = float(reflux_info.get("default_min", 20.0))
	_hood = true
	_ice_c = float(workup_info.get("ice_temp_c", 2.0))
	_water_ml = float(workup_info.get("quench_water_ml", 30.0))
	_ethanol_ml = float(workup_info.get("recryst_solvent_ml", 15.0))
	_seeded = bool(workup_info.get("seed_crystal", true))

	_update_briefing()
	_set_stage(1)
	if _status != null:
		_status.text = "Protocol loaded: %s (%s). Don PPE, weigh %s, then charge the flask." % [
			str(_protocol.get("name", "")), str(_protocol.get("category", "")), str(rA.get("name", "reagent"))
		]


func _update_briefing() -> void:
	if _briefing == null:
		return
	var proto_name: String = str(_protocol.get("name", "Acetylsalicylic acid"))
	var desc: String = str(_protocol.get("description", "Aspirin synthesis via O-acylation."))
	var cat: String = str(_protocol.get("category", "Industrial APIs"))
	var lit_ref: String = str(_protocol.get("literature_reference", "Vogel / Standard Chemical Literature"))
	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var reflux_info: Dictionary = _protocol.get("reflux", {})
	var anal_info: Dictionary = _protocol.get("analytical", {})
	var workup_info: Dictionary = _protocol.get("workup", {})

	var text := "[font_size=15][b]PROTOCOL SPECIFICATION[/b][/font_size]\n"
	text += "[color=#85949f]%s · %s[/color]\n\n" % [cat, proto_name]
	if not lit_ref.is_empty():
		text += "[b]Literature Reference[/b]\n[color=#6ddbaa]%s[/color]\n\n" % lit_ref
	text += "[b]Overview[/b]\n%s\n\n" % desc
	text += "[b]Reagent A (Precursor)[/b]\n"
	text += "• %s (MW %.2f g/mol, %s)\n" % [str(rA.get("name", "")), float(rA.get("mw", 0.0)), str(rA.get("unit", "g"))]
	text += "[b]Reagent B[/b]\n"
	text += "• %s (MW %.2f g/mol, %s)\n\n" % [str(rB.get("name", "")), float(rB.get("mw", 0.0)), str(rB.get("unit", "mL"))]
	text += "[b]Target Specifications[/b]\n"
	text += "• Product MW: %.2f g/mol\n" % float(_protocol.get("mw", 0.0))
	text += "• Literature MP: %.1f °C\n" % float(anal_info.get("mp_pure", 0.0))
	text += "• Purity Gate: ≥ %.1f %%\n" % float(anal_info.get("purity_pass", 95.0))
	text += "• Yield Contract: ≥ %.1f g\n\n" % float(anal_info.get("yield_pass_g", 10.0))
	text += "[b]Validated Window[/b]\n"
	text += "• Reflux: %.0f–%.0f °C for %.0f min\n" % [
		float(reflux_info.get("temp_optimal_low", 65.0)),
		float(reflux_info.get("temp_optimal_high", 75.0)),
		float(reflux_info.get("optimal_min", 20.0))
	]
	text += "• Degradation threshold: > %.0f °C\n" % float(reflux_info.get("temp_degrade", 85.0))

	if _sop_guide_active:
		text += "\n[b][color=#ffb45c]STEP-BY-STEP SOP GUIDE[/color][/b]\n"
		text += "1. Charge %.1f %s of %s + %.1f %s of %s + %d drops catalyst.\n" % [
			float(rA.get("default", 10.0)), str(rA.get("unit", "g")), str(rA.get("name", "reagent")),
			float(rB.get("default", 10.0)), str(rB.get("unit", "mL")), str(rB.get("name", "reagent")),
			int(_protocol.get("catalyst", {}).get("default", 5))
		]
		text += "2. Set mantle to %.0f °C, run reflux for %.0f min with fume hood ON.\n" % [
			float(reflux_info.get("default_temp", 70.0)), float(reflux_info.get("default_min", 20.0))
		]
		text += "3. Quench on %.0f °C ice bath with %.0f mL water; recrystallize from %.0f mL %s with seed crystal.\n" % [
			float(workup_info.get("ice_c", 2.0)), float(workup_info.get("water_ml", 30.0)),
			float(workup_info.get("ethanol_ml", 15.0)), str(workup_info.get("solvent", "solvent"))
		]
		text += "4. Dry product and verify MP (%.1f °C) & purity (≥ %.1f%%).\n" % [
			float(anal_info.get("mp_pure", 0.0)), float(anal_info.get("purity_pass", 95.0))
		]

	var steps: Array = _protocol.get("steps", [])
	if not steps.is_empty():
		text += "\n[b]Literature Multi-Step Pathway[/b]\n"
		for s in steps:
			if s is Dictionary:
				text += "• Step %s: %s\n" % [str(s.get("step_number", "")), str(s.get("name", ""))]

	text += "\n[b]Safety gate[/b]\n"
	text += "Fume hood on, sash low. Goggles, nitrile gloves and lab coat are required before the first reagent is opened.\n\n"
	text += "[i]The assay does not reward luck. It reports what your conditions actually produced.[/i]"
	_briefing.text = text


# =============================================================================
# UI CONSTRUCTION
# =============================================================================

func _build_ui() -> void:
	_title_label = Label.new()
	_title_label.text = "ORGANIC SYNTHESIS  ·  ACETYLSALICYLIC ACID"
	_title_label.position = Vector2(22.0, 8.0)
	_title_label.add_theme_font_size_override("font_size", 17)
	_title_label.add_theme_color_override("font_color", TEXT)
	add_child(_title_label)

	_subtitle_label = Label.new()
	_subtitle_label.text = "Salicylic acid + acetic anhydride  ·  H₂SO₄ catalysed  ·  offline stoichiometry"
	_subtitle_label.position = Vector2(22.0, 34.0)
	_subtitle_label.add_theme_font_size_override("font_size", 11)
	_subtitle_label.add_theme_color_override("font_color", DIM)
	add_child(_subtitle_label)

	# Row 1 action controls
	var top_actions := HBoxContainer.new()
	top_actions.position = Vector2(440.0, 6.0)
	top_actions.custom_minimum_size = Vector2(820.0, 28.0)
	top_actions.add_theme_constant_override("separation", 10)
	add_child(top_actions)

	_sandbox_badge = Label.new()
	_sandbox_badge.text = "🧪 SANDBOX MODE · ALL ROUTES & PRECURSORS UNLOCKED"
	_sandbox_badge.add_theme_font_size_override("font_size", 10)
	_sandbox_badge.add_theme_color_override("font_color", GREEN)
	top_actions.add_child(_sandbox_badge)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_actions.add_child(spacer)

	_btn_sop_toggle = Button.new()
	_btn_sop_toggle.text = "📘 SOP Guide: ON"
	_btn_sop_toggle.custom_minimum_size = Vector2(125.0, 26.0)
	_btn_sop_toggle.pressed.connect(_toggle_sop_guide)
	top_actions.add_child(_btn_sop_toggle)

	_btn_sop_modal = Button.new()
	_btn_sop_modal.text = "🔬 Literature SOP"
	_btn_sop_modal.custom_minimum_size = Vector2(130.0, 26.0)
	_btn_sop_modal.pressed.connect(_show_sop_modal)
	top_actions.add_child(_btn_sop_modal)

	var back := Button.new()
	back.text = "← Lab network"
	back.custom_minimum_size = Vector2(115.0, 26.0)
	back.pressed.connect(func(): get_tree().change_scene_to_file(SCENE_HUB))
	top_actions.add_child(back)

	# Row 2 selector and auto-charge controls
	var selector_box := HBoxContainer.new()
	selector_box.position = Vector2(440.0, 36.0)
	selector_box.custom_minimum_size = Vector2(820.0, 28.0)
	selector_box.add_theme_constant_override("separation", 8)
	add_child(selector_box)

	var cat_lbl := Label.new()
	cat_lbl.text = "Category:"
	cat_lbl.add_theme_font_size_override("font_size", 11)
	cat_lbl.add_theme_color_override("font_color", CYAN)
	selector_box.add_child(cat_lbl)

	_category_opt = OptionButton.new()
	_category_opt.custom_minimum_size = Vector2(165.0, 26.0)
	_category_opt.item_selected.connect(_on_category_selected)
	selector_box.add_child(_category_opt)

	var proto_lbl := Label.new()
	proto_lbl.text = "Route:"
	proto_lbl.add_theme_font_size_override("font_size", 11)
	proto_lbl.add_theme_color_override("font_color", CYAN)
	selector_box.add_child(proto_lbl)

	_protocol_opt = OptionButton.new()
	_protocol_opt.custom_minimum_size = Vector2(230.0, 26.0)
	_protocol_opt.item_selected.connect(_on_protocol_selected)
	selector_box.add_child(_protocol_opt)

	var spacer2 := Control.new()
	spacer2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	selector_box.add_child(spacer2)

	_btn_auto_charge = Button.new()
	_btn_auto_charge.text = "⚡ Auto-Charge Optimal Aliquots"
	_btn_auto_charge.custom_minimum_size = Vector2(215.0, 26.0)
	_btn_auto_charge.pressed.connect(auto_charge_literature_aliquots)
	selector_box.add_child(_btn_auto_charge)

	_briefing = RichTextLabel.new()
	_briefing.bbcode_enabled = true
	_briefing.position = Vector2(20.0, 70.0)
	_briefing.custom_minimum_size = Vector2(300.0, 610.0)
	_briefing.size = Vector2(300.0, 610.0)
	_briefing.add_theme_font_size_override("normal_font_size", 11)
	_briefing.add_theme_font_size_override("bold_font_size", 12)
	_briefing.scroll_active = true
	add_child(_briefing)

	_controls = VBoxContainer.new()
	_controls.position = Vector2(0.0, 0.0)
	_controls.custom_minimum_size = Vector2(500.0, 0.0)
	_controls.add_theme_constant_override("separation", 4)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(338.0, 450.0)
	scroll.custom_minimum_size = Vector2(522.0, 234.0)
	scroll.size = Vector2(522.0, 234.0)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.add_child(_controls)
	add_child(scroll)

	_report = RichTextLabel.new()
	_report.bbcode_enabled = true
	_report.position = Vector2(874.0, 70.0)
	_report.custom_minimum_size = Vector2(386.0, 614.0)
	_report.size = Vector2(386.0, 614.0)
	_report.add_theme_font_size_override("normal_font_size", 11)
	_report.add_theme_font_size_override("bold_font_size", 12)
	_report.scroll_active = true
	add_child(_report)

	_status = Label.new()
	_status.position = Vector2(22.0, 692.0)
	_status.custom_minimum_size = Vector2(1230.0, 20.0)
	_status.add_theme_font_size_override("font_size", 11)
	_status.add_theme_color_override("font_color", DIM)
	_status.text = "Stage 1 — don PPE, then weigh the acid and charge the flask."
	add_child(_status)


func _clear_controls() -> void:
	for child in _controls.get_children():
		child.queue_free()


func _add_intro(title: String, body: String) -> void:
	var label := RichTextLabel.new()
	label.bbcode_enabled = true
	label.fit_content = true
	label.custom_minimum_size = Vector2(500.0, 0.0)
	label.add_theme_font_size_override("normal_font_size", 11)
	label.text = "[b][color=#%s]%s[/color][/b]\n[color=#85949f]%s[/color]" % [CYAN.to_html(false), title, body]
	_controls.add_child(label)


func _add_sop_hint(hint: String) -> void:
	if not _sop_guide_active:
		return
	var label := RichTextLabel.new()
	label.bbcode_enabled = true
	label.fit_content = true
	label.custom_minimum_size = Vector2(500.0, 0.0)
	label.add_theme_font_size_override("normal_font_size", 10)
	label.text = "[color=#6ddbaa]📖 [b]Literature SOP Guide[/b]:[/color] %s" % hint
	_controls.add_child(label)


func _add_slider(title: String, unit: String, min_v: float, max_v: float, step: float,
		value: float, decimals: int, callback: Callable) -> void:
	# One compact row: label | slider | live value. Keeping every control on a
	# single line leaves room for the PPE gate and the stage navigation at 720p.
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)

	var name_label := Label.new()
	name_label.text = title
	name_label.custom_minimum_size = Vector2(142.0, 0.0)
	name_label.add_theme_font_size_override("font_size", 11)
	name_label.add_theme_color_override("font_color", TEXT)
	row.add_child(name_label)

	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.step = step
	slider.value = value
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size = Vector2(238.0, 18.0)
	row.add_child(slider)

	var value_label := Label.new()
	value_label.text = _format_value(value, unit, decimals)
	value_label.custom_minimum_size = Vector2(74.0, 0.0)
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value_label.add_theme_font_size_override("font_size", 11)
	value_label.add_theme_color_override("font_color", AMBER)
	row.add_child(value_label)

	slider.value_changed.connect(func(v: float):
		callback.call(v)
		value_label.text = _format_value(v, unit, decimals)
		_refresh_live()
	)
	_controls.add_child(row)


func _add_check(title: String, pressed: bool, callback: Callable) -> CheckButton:
	var check := CheckButton.new()
	check.text = title
	check.button_pressed = pressed
	check.add_theme_font_size_override("font_size", 11)
	check.toggled.connect(callback)
	_controls.add_child(check)
	return check


func _format_value(value: float, unit: String, decimals: int) -> String:
	return ("%." + str(decimals) + "f %s") % [value, unit]


func _make_ppe_check(text: String, pressed: bool, callback: Callable) -> CheckButton:
	var check := CheckButton.new()
	check.text = text
	check.button_pressed = pressed
	check.add_theme_font_size_override("font_size", 11)
	check.toggled.connect(callback)
	return check


func _add_nav(allow_next: bool, next_text: String = "Continue →") -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	var prev := Button.new()
	prev.text = "← Previous stage"
	prev.custom_minimum_size = Vector2(168.0, 30.0)
	prev.disabled = _stage <= 1
	prev.pressed.connect(_on_previous)
	row.add_child(prev)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)
	if _stage < 4:
		_next_btn = Button.new()
		_next_btn.text = next_text
		_next_btn.custom_minimum_size = Vector2(156.0, 30.0)
		_next_btn.disabled = not allow_next
		_next_btn.pressed.connect(_on_next)
		row.add_child(_next_btn)
	_controls.add_child(row)


func _set_stage(stage: int) -> void:
	_stage = clampi(stage, 1, 4)
	_clear_controls()
	match _stage:
		1:
			_build_stage_one()
		2:
			_build_stage_two()
		3:
			_build_stage_three()
		4:
			_build_stage_four()
	_refresh_live()
	queue_redraw()


func _build_stage_one() -> void:
	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var rA_name: String = str(rA.get("name", "Salicylic acid"))
	var rB_name: String = str(rB.get("name", "Acetic anhydride"))
	var rA_unit: String = str(rA.get("unit", "g"))
	var rB_unit: String = str(rB.get("unit", "mL"))
	var rA_min: float = float(rA.get("min", 1.0))
	var rA_max: float = float(rA.get("max", 50.0))
	var rB_min: float = float(rB.get("min", 1.0))
	var rB_max: float = float(rB.get("max", 50.0))
	var cat_name: String = str(_protocol.get("catalyst", {}).get("name", "H₂SO₄ catalyst"))
	var cat_opt: int = int(_protocol.get("catalyst", {}).get("default", 5))

	_add_intro("STAGE 1 / 4 — WEIGH & CHARGE", "Tare the balance, weigh %s, then charge %s and catalyst into the dry flask." % [rA_name, rB_name])
	_add_sop_hint("Charge [b]%.1f %s[/b] of %s + [b]%.1f %s[/b] of %s with [b]%d drops[/b] %s. Don complete PPE to unlock the flask." % [
		float(rA.get("default", 10.0)), rA_unit, rA_name, float(rB.get("default", 10.0)), rB_unit, rB_name, cat_opt, cat_name
	])
	_add_slider(rA_name, rA_unit, rA_min, rA_max, 0.1, _mass_g, 1, func(v): _mass_g = v)
	_add_slider(rB_name, rB_unit, rB_min, rB_max, 0.1, _anhydride_ml, 1, func(v): _anhydride_ml = v)
	_add_slider(cat_name, "drops", 0.0, 10.0, 1.0, float(_catalyst_drops), 0, func(v): _catalyst_drops = int(v))
	_add_slider("Stirrer", "rpm", 0.0, 1200.0, 50.0, _stir_rpm, 0, func(v): _stir_rpm = v)

	var ppe_row := HBoxContainer.new()
	ppe_row.add_theme_constant_override("separation", 6)
	ppe_row.add_child(_make_ppe_check("Goggles", bool(_ppe["goggles"]), _on_goggles))
	ppe_row.add_child(_make_ppe_check("Gloves", bool(_ppe["gloves"]), _on_gloves))
	ppe_row.add_child(_make_ppe_check("Lab coat", bool(_ppe["coat"]), _on_coat))
	_controls.add_child(ppe_row)
	_add_nav(_ppe_ok(), "Begin reflux →")


func _build_stage_two() -> void:
	var reflux_info: Dictionary = _protocol.get("reflux", {})
	var t_low: float = float(reflux_info.get("temp_optimal_low", 65.0))
	var t_high: float = float(reflux_info.get("temp_optimal_high", 75.0))
	var opt_min: float = float(reflux_info.get("optimal_min", 20.0))

	_add_intro("STAGE 2 / 4 — REFLUX", "Bring the mantle to %.0f–%.0f °C and hold reflux for %.0f minutes. The condenser must stay cold; vapour leaving the top is lost reagent." % [t_low, t_high, opt_min])
	_add_sop_hint("Set mantle to [b]%.0f °C[/b] (optimal %.0f–%.0f °C) and run reflux for [b]%.0f min[/b]. Ensure fume hood is ON to capture vapors." % [
		float(reflux_info.get("default_temp", 70.0)), t_low, t_high, opt_min
	])
	_add_slider("Mantle temperature", "°C", 30.0, 140.0, 1.0, _temp_c, 0, func(v): _temp_c = v)
	_add_slider("Reflux time", "min", 2.0, maxf(60.0, opt_min * 2.0), 1.0, _reflux_min, 0, func(v): _reflux_min = v)
	_add_check("Fume hood running / sash low", _hood, _on_hood)

	var run := Button.new()
	run.text = "Run reflux" if not _reflux_done else "Reflux complete ✓"
	run.disabled = _reflux_done
	run.custom_minimum_size = Vector2(220.0, 32.0)
	run.pressed.connect(_on_run_reflux)
	_controls.add_child(run)
	if _reflux_done:
		var note := Label.new()
		note.text = "Acylation finished. Cool the flask before quenching."
		note.add_theme_font_size_override("font_size", 10)
		note.add_theme_color_override("font_color", GREEN)
		_controls.add_child(note)
	_add_nav(_reflux_done, "Quench & crystallise →")


func _build_stage_three() -> void:
	var workup_info: Dictionary = _protocol.get("workup", {})
	var solv_name: String = str(workup_info.get("solvent", "ethanol"))
	var ice_opt: float = float(workup_info.get("ice_c", 2.0))
	var water_opt: float = float(workup_info.get("water_ml", 30.0))
	var eth_opt: float = float(workup_info.get("ethanol_ml", 15.0))

	_add_intro("STAGE 3 / 4 — QUENCH & CRYSTALLISE", "Pour the cooled mixture onto ice water to hydrolyse excess unreacted reagent. Filter, then recrystallise from %s and dry." % solv_name)
	_add_sop_hint("Chill ice bath to [b]%.0f °C[/b], quench excess reagent with [b]%.0f mL[/b] water. Dissolve in [b]%.0f mL[/b] hot %s and add seed crystal." % [
		ice_opt, water_opt, eth_opt, solv_name
	])
	_add_slider("Ice bath", "°C", -10.0, 25.0, 1.0, _ice_c, 0, func(v): _ice_c = v)
	_add_slider("Quench water", "mL", 0.0, 80.0, 1.0, _water_ml, 0, func(v): _water_ml = v)
	_add_slider("Recrystallisation " + solv_name, "mL", 0.0, 50.0, 1.0, _ethanol_ml, 0, func(v): _ethanol_ml = v)
	_add_check("Add seed crystal", _seeded, _on_seed)
	_add_nav(true, "Go to assay →")


func _build_stage_four() -> void:
	var anal_info: Dictionary = _protocol.get("analytical", {})
	_add_intro("STAGE 4 / 4 — ANALYTICAL ASSAY", "TLC, melting point and gravimetric purity decide whether the batch meets the contract. Submit the dried product.")
	_add_sop_hint("Literature assay targets: MP [b]%.1f °C[/b] · TLC Rf [b]%.2f[/b] · Purity ≥ [b]%.1f%%[/b] · Yield ≥ [b]%.1f g[/b]." % [
		float(anal_info.get("mp_pure", 0.0)), float(anal_info.get("tlc_rf", 0.40)),
		float(anal_info.get("purity_pass", 95.0)), float(anal_info.get("yield_pass_g", 10.0))
	])
	if not _submitted:
		var submit := Button.new()
		submit.text = "Submit batch to analytical"
		submit.custom_minimum_size = Vector2(260.0, 34.0)
		submit.pressed.connect(_on_submit)
		_controls.add_child(submit)
		var note := Label.new()
		note.text = "The assay is computed from the conditions you actually ran."
		note.add_theme_font_size_override("font_size", 10)
		note.add_theme_color_override("font_color", DIM)
		_controls.add_child(note)
	else:
		var again := Button.new()
		again.text = "Start a new batch"
		again.custom_minimum_size = Vector2(200.0, 32.0)
		again.pressed.connect(_on_new_batch)
		_controls.add_child(again)
	_add_nav(false)


func _on_goggles(pressed: bool) -> void:
	_ppe["goggles"] = pressed
	_refresh_ppe()


func _on_gloves(pressed: bool) -> void:
	_ppe["gloves"] = pressed
	_refresh_ppe()


func _on_coat(pressed: bool) -> void:
	_ppe["coat"] = pressed
	_refresh_ppe()


func _refresh_ppe() -> void:
	if _stage != 1:
		return
	# Rebuild so the Continue button reflects the PPE gate immediately.
	_set_stage(1)
	_status.text = "PPE complete. Weigh the acid and continue." if _ppe_ok() else "PPE incomplete — the flask stays closed."


func _on_hood(pressed: bool) -> void:
	_hood = pressed
	_refresh_live()


func _on_seed(pressed: bool) -> void:
	_seeded = pressed


func _on_run_reflux() -> void:
	if not _ppe_ok():
		_status.text = "The safety gate is still closed. Return to stage 1 and don PPE."
		_status.add_theme_color_override("font_color", RED)
		return
	_reflux_done = true
	if not _hood:
		_status.text = "Reflux finished — but the hood was off. Expect exposure and a safety failure at assay."
		_status.add_theme_color_override("font_color", AMBER)
	elif _temp_c > 85.0:
		_status.text = "Reflux finished at %.0f °C. The batch is discoloured; tar is forming." % _temp_c
		_status.add_theme_color_override("font_color", AMBER)
	else:
		_status.text = "Reflux finished at %.0f °C after %.0f min. Cool before quenching." % [_temp_c, _reflux_min]
		_status.add_theme_color_override("font_color", GREEN)
	_set_stage(2)


func _on_next() -> void:
	if _stage == 1:
		if not _ppe_ok():
			_status.text = "Cannot open the reagents without goggles, gloves and a lab coat."
			_status.add_theme_color_override("font_color", RED)
			return
		_set_stage(2)
		_status.text = "Stage 2 — set the mantle and run the reflux."
	elif _stage == 2:
		if not _reflux_done:
			_status.text = "Run the reflux before moving on; the acylation has not happened yet."
			_status.add_theme_color_override("font_color", RED)
			return
		_set_stage(3)
		_status.text = "Stage 3 — quench on ice, filter, recrystallise."
	elif _stage == 3:
		_set_stage(4)
		_status.text = "Stage 4 — submit the dried product for assay."


func _on_previous() -> void:
	if _stage > 1:
		_set_stage(_stage - 1)
		_status.text = "Returned to stage %d. Conditions are preserved." % _stage


func _on_submit() -> void:
	submit_batch()
	var result := _last_result
	if not bool(result.get("ok", false)):
		_status.text = str(result.get("error", "The batch could not be evaluated."))
		_status.add_theme_color_override("font_color", RED)
		return
	var stars := int(result.get("stars", 0))
	_status.text = "%s  ·  %.1f %% purity  ·  %.1f g isolated  ·  MP %.1f °C  ·  %d XP chemistry" % [
		str(result.get("grade", "")), float(result.get("purity", 0.0)), float(result.get("yield_g", 0.0)),
		float(result.get("melting_point_c", 0.0)), int(result.get("xp_awarded", 0))
	]
	_status.add_theme_color_override("font_color", GREEN if stars >= 2 else AMBER if stars == 1 else RED)


func submit_batch() -> Dictionary:
	if _submitted:
		return {"ok": false, "error": "This batch has already been submitted."}
	var result: Dictionary = Chem.evaluate(_params())
	_last_result = result
	if not bool(result.get("ok", false)):
		return result
	_submitted = true
	_batch_count += 1
	var cap: float = clampf(1.0 - 0.25 * float(maxi(0, _batch_count - 1)), 0.35, 1.0)
	var xp: int = int(round(float(result.get("xp_chemistry", 0)) * cap))
	var xp_eng: int = int(round(float(result.get("xp_engineering", 0)) * cap))
	result["xp_awarded"] = xp
	result["xp_engineering_awarded"] = xp_eng
	result["xp_multiplier"] = cap

	var skills := get_node_or_null("/root/SkillManager")
	if skills != null:
		var proto_name: String = str(_protocol.get("name", "Aspirin"))
		skills.add_xp("chemistry", xp, "%s synthesis" % proto_name)
		if xp_eng > 0:
			skills.add_xp("engineering", xp_eng, "Reflux rig operation")

	var vitals := get_node_or_null("/root/PlayerVitals")
	if vitals != null:
		if not _hood:
			if vitals.has_method("add_chemical_exposure"):
				vitals.add_chemical_exposure("organic_vapour", 120.0, 2.0)
			if vitals.has_method("apply_hazard_damage"):
				vitals.apply_hazard_damage(4.0, "chemical_burn", "open-bench organic vapour")
		if _temp_c > 100.0:
			if vitals.has_method("apply_hazard_damage"):
				vitals.apply_hazard_damage(5.0, "thermal_burn", "reflux runaway")

	_save_record(result)
	_set_stage(4)
	return result


func _save_record(result: Dictionary) -> void:
	var save_manager := get_node_or_null("/root/SaveManager")
	if save_manager == null:
		return
	var data: Dictionary = save_manager.get("save_data")
	var record: Dictionary = data.get("synthesis", {})
	if record.is_empty():
		record = {"runs": 0, "best_purity": 0.0, "best_yield_g": 0.0, "best_score": 0.0}
	record["runs"] = int(record.get("runs", 0)) + 1
	record["best_purity"] = maxf(float(record.get("best_purity", 0.0)), float(result.get("purity", 0.0)))
	record["best_yield_g"] = maxf(float(record.get("best_yield_g", 0.0)), float(result.get("yield_g", 0.0)))
	record["best_score"] = maxf(float(record.get("best_score", 0.0)), float(result.get("score", 0.0)))
	record["last"] = {
		"purity": float(result.get("purity", 0.0)),
		"yield_g": float(result.get("yield_g", 0.0)),
		"grade": str(result.get("grade", "")),
		"stars": int(result.get("stars", 0))
	}
	data["synthesis"] = record
	if save_manager.has_method("save_game"):
		save_manager.save_game()


func _on_new_batch() -> void:
	_select_protocol(str(_protocol.get("id", "aspirin")))
	_status.text = "New batch. PPE is retained; reagents reset to the protocol defaults."
	_status.add_theme_color_override("font_color", DIM)


# =============================================================================
# SANDBOX MODE: LITERATURE PRECURSORS & STEP-BY-STEP SOP GUIDES
# =============================================================================

func auto_charge_literature_aliquots() -> void:
	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var reflux_info: Dictionary = _protocol.get("reflux", {})
	var workup_info: Dictionary = _protocol.get("workup", {})

	_mass_g = float(rA.get("default", 10.0))
	_anhydride_ml = float(rB.get("default", 10.0))
	_catalyst_drops = int(_protocol.get("catalyst", {}).get("default", 5))
	_stir_rpm = float(reflux_info.get("stir_rpm", 450.0))
	_temp_c = float(reflux_info.get("default_temp", 70.0))
	_reflux_min = float(reflux_info.get("default_min", 20.0))
	_hood = true
	_ice_c = float(workup_info.get("ice_c", 2.0))
	_water_ml = float(workup_info.get("water_ml", 30.0))
	_ethanol_ml = float(workup_info.get("ethanol_ml", 15.0))
	_seeded = true
	_ppe = {"goggles": true, "gloves": true, "coat": true}

	_set_stage(_stage)
	if _status != null:
		_status.text = "✓ Optimal literature aliquots charged for %s: 100%% stoichiometric precision." % str(_protocol.get("name", ""))
		_status.add_theme_color_override("font_color", GREEN)


func _toggle_sop_guide() -> void:
	_sop_guide_active = not _sop_guide_active
	if _btn_sop_toggle != null:
		_btn_sop_toggle.text = "📘 SOP Guide: ON" if _sop_guide_active else "📘 SOP Guide: OFF"
	_update_briefing()
	_set_stage(_stage)


func _show_sop_modal() -> void:
	if _sop_modal == null:
		_build_sop_modal()
	_update_sop_modal_text()
	_sop_modal.visible = true


func _build_sop_modal() -> void:
	_sop_modal = PanelContainer.new()
	_sop_modal.name = "SOPModal"
	_sop_modal.visible = false
	_sop_modal.set_anchors_preset(Control.PRESET_CENTER)
	_sop_modal.offset_left = -460.0
	_sop_modal.offset_top = -280.0
	_sop_modal.offset_right = 460.0
	_sop_modal.offset_bottom = 280.0
	add_child(_sop_modal)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_bottom", 16)
	_sop_modal.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 10)
	margin.add_child(vbox)

	var header_hbox := HBoxContainer.new()
	vbox.add_child(header_hbox)

	var title := Label.new()
	title.text = "LITERATURE STANDARD OPERATING PROCEDURE (SOP)"
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", CYAN)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_hbox.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕ Close"
	close_btn.custom_minimum_size = Vector2(80, 28)
	close_btn.pressed.connect(func(): _sop_modal.visible = false)
	header_hbox.add_child(close_btn)

	vbox.add_child(HSeparator.new())

	_sop_modal_text = RichTextLabel.new()
	_sop_modal_text.bbcode_enabled = true
	_sop_modal_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_sop_modal_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_sop_modal_text.add_theme_font_size_override("normal_font_size", 11)
	_sop_modal_text.add_theme_font_size_override("bold_font_size", 12)
	_sop_modal_text.scroll_active = true
	vbox.add_child(_sop_modal_text)


func _update_sop_modal_text() -> void:
	if _sop_modal_text == null:
		return
	var proto_name: String = str(_protocol.get("name", "Unknown Protocol"))
	var chem_name: String = str(_protocol.get("chemical_name", proto_name))
	var cat: String = str(_protocol.get("category", "Synthesis"))
	var cas: String = str(_protocol.get("cas", "N/A"))
	var formula: String = str(_protocol.get("formula", ""))
	var mw: float = float(_protocol.get("mw", 0.0))
	var lit_ref: String = str(_protocol.get("literature_reference", "Vogel's Practical Organic Chemistry"))
	var desc: String = str(_protocol.get("description", ""))
	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var reflux_info: Dictionary = _protocol.get("reflux", {})
	var workup_info: Dictionary = _protocol.get("workup", {})
	var anal_info: Dictionary = _protocol.get("analytical", {})

	var text := "[b][font_size=15]%s[/font_size][/b]\n" % proto_name.to_upper()
	text += "[color=#85949f]IUPAC: %s  ·  Category: %s[/color]\n" % [chem_name, cat]
	text += "[color=#ffb45c]Formula: %s  ·  MW: %.2f g/mol  ·  CAS: %s[/color]\n\n" % [formula, mw, cas]

	text += "[b]Literature Reference[/b]\n[color=#6ddbaa]%s[/color]\n\n" % lit_ref
	text += "[b]Reaction Description & Chemical Mechanism[/b]\n%s\n\n" % desc

	text += "[b]Precursors & Reagents (Edukte)[/b]\n"
	text += "• %s (MW %.2f g/mol): %.1f %s (limiting precursor)\n" % [
		str(rA.get("name", "")), float(rA.get("mw", 0.0)), float(rA.get("default", 10.0)), str(rA.get("unit", "g"))
	]
	text += "• %s (MW %.2f g/mol): %.1f %s\n" % [
		str(rB.get("name", "")), float(rB.get("mw", 0.0)), float(rB.get("default", 10.0)), str(rB.get("unit", "mL"))
	]
	text += "• Catalyst / Buffer: %s (%d drops)\n\n" % [
		str(_protocol.get("catalyst", {}).get("name", "Catalyst")), int(_protocol.get("catalyst", {}).get("default", 5))
	]

	text += "[b]Thermal & Kinetic Parameters[/b]\n"
	text += "• Optimal Reflux: %.0f–%.0f °C (Target %.0f °C) for %.0f min\n" % [
		float(reflux_info.get("temp_optimal_low", 65.0)), float(reflux_info.get("temp_optimal_high", 75.0)),
		float(reflux_info.get("default_temp", 70.0)), float(reflux_info.get("default_min", 20.0))
	]
	text += "• Thermal Degradation Limit: > %.0f °C\n\n" % float(reflux_info.get("temp_degrade", 85.0))

	text += "[b]Workup, Hydrolysis & Recrystallization[/b]\n"
	text += "• Quench: %.0f mL ice water at %.0f °C\n" % [
		float(workup_info.get("water_ml", 30.0)), float(workup_info.get("ice_c", 2.0))
	]
	text += "• Recrystallization: %.0f mL boiling %s with seed crystal\n\n" % [
		float(workup_info.get("ethanol_ml", 15.0)), str(workup_info.get("solvent", "solvent"))
	]

	text += "[b]Analytical Quality Gates[/b]\n"
	text += "• Melting Point: %.1f °C (± %.1f °C)\n" % [
		float(anal_info.get("mp_pure", 0.0)), float(anal_info.get("mp_tolerance", 2.5))
	]
	text += "• TLC Rf: %.2f\n" % float(anal_info.get("tlc_rf", 0.40))
	text += "• Purity Contract: ≥ %.1f %%\n" % float(anal_info.get("purity_pass", 95.0))
	text += "• Yield Contract: ≥ %.1f g\n" % float(anal_info.get("yield_pass_g", 10.0))

	var steps: Array = _protocol.get("steps", [])
	if not steps.is_empty():
		text += "\n[b]Literature Multi-Step Synthetic Stages[/b]\n"
		for s in steps:
			if s is Dictionary:
				text += "• [b]Step %s[/b]: %s\n" % [str(s.get("step_number", "")), str(s.get("name", ""))]
				var s_reag: Array = s.get("reagents", [])
				for r in s_reag:
					if r is Dictionary:
						text += "    - %s: %s %s\n" % [str(r.get("name", "")), str(r.get("amount", "")), str(r.get("unit", ""))]

	_sop_modal_text.text = text


# =============================================================================
# LIVE REPORT
# =============================================================================

func _refresh_live() -> void:
	if _report == null:
		return
	var rA: Dictionary = _protocol.get("reagent_a", {})
	var rB: Dictionary = _protocol.get("reagent_b", {})
	var rA_name: String = str(rA.get("name", "Salicylic acid"))
	var rB_name: String = str(rB.get("name", "Acetic anhydride"))
	var mw_a: float = float(rA.get("mw", Chem.MW_SALICYLIC))
	var mw_b: float = float(rB.get("mw", Chem.MW_ANHYDRIDE))
	var density_b: float = float(rB.get("density", Chem.DENSITY_ANHYDRIDE))
	var mw_product: float = float(_protocol.get("mw", Chem.MW_ASPIRIN))
	var proto_name: String = str(_protocol.get("name", "Aspirin"))
	var proto_id: String = str(_protocol.get("id", "aspirin")).to_upper()
	var cat_name: String = str(_protocol.get("catalyst", {}).get("name", "H₂SO₄"))
	var solv_name: String = str(_protocol.get("workup", {}).get("solvent", "EtOH"))

	var moles_sal: float = _mass_g / mw_a
	var moles_anh: float = _anhydride_ml * density_b / mw_b
	var equivalents: float = moles_anh / moles_sal if moles_sal > 0.0 else 0.0
	var theoretical: float = minf(moles_sal, moles_anh) * mw_product
	var limiting := rA_name if moles_sal <= moles_anh else rB_name
	var hood_color := GREEN if _hood else RED
	var ppe_color := GREEN if _ppe_ok() else AMBER
	var text := "[font_size=15][b]BATCH RECORD[/b][/font_size]\n"
	text += "[color=#85949f]%s · %s · stage %d / 4[/color]\n\n" % [proto_id, proto_name, _stage]
	text += "[b]STOICHIOMETRY[/b]\n"
	text += "%-16s %.2f g  →  %.1f mmol\n" % [rA_name.left(16), _mass_g, moles_sal * 1000.0]
	text += "%-16s %.1f mL → %.1f mmol\n" % [rB_name.left(16), _anhydride_ml, moles_anh * 1000.0]
	text += "Molar ratio      %.2f eq\n" % equivalents
	text += "Limiting         [color=#ffb45c]%s[/color]\n" % limiting
	text += "Theoretical      %.2f g\n\n" % theoretical
	text += "[b]CONDITIONS[/b]\n"
	text += "Reflux           %.0f °C · %.0f min\n" % [_temp_c, _reflux_min]
	text += "Stirrer          %.0f rpm\n" % _stir_rpm
	text += "Catalyst         %d drops %s\n" % [_catalyst_drops, cat_name]
	text += "Crystallisation  %.0f °C ice · %d mL %s%s\n" % [_ice_c, int(_ethanol_ml), solv_name, " · seeded" if _seeded else ""]
	text += "Fume hood        [color=#%s]%s[/color]\n" % [hood_color.to_html(false), "ON" if _hood else "OFF"]
	text += "PPE              [color=#%s]%s[/color]\n\n" % [ppe_color.to_html(false), "complete" if _ppe_ok() else "incomplete"]

	text += "[b]LIVE HAZARD READ[/b]\n"
	if not _hood:
		text += "[color=#ff6b60]• Open bench. Acetic anhydride vapour is a lachrymator.[/color]\n"
	if _temp_c > 85.0:
		text += "[color=#ff6b60]• Above 85 °C: tar and colour body formation.[/color]\n"
	if _temp_c > 100.0:
		text += "[color=#ff6b60]• Above 100 °C: pyrolysis; the batch is lost.[/color]\n"
	if _catalyst_drops == 0:
		text += "[color=#ffb45c]• No catalyst: most of the acid will survive unreacted.[/color]\n"
	if _catalyst_drops > 6:
		text += "[color=#ffb45c]• Excess acid catalyst chars product and attacks the flask.[/color]\n"
	if _hood and _temp_c <= 85.0 and _catalyst_drops > 0:
		text += "[color=#6ddbaa]• Conditions inside the validated window.[/color]\n"

	if _submitted:
		text += "\n[font_size=14][b]ASSAY RESULT[/b][/font_size]\n"
		text += _format_result()
	else:
		text += "\n[color=#85949f]Assay pending. Complete stages 1–4 and submit the dried product.[/color]\n"
		if _reflux_done:
			text += "[color=#6ddbaa]Reflux recorded.[/color]\n"

	_report.text = text


func _format_result() -> String:
	var result := _last_result
	if not bool(result.get("ok", false)):
		return "[color=#ff6b60]%s[/color]" % str(result.get("error", "invalid batch"))
	var checks: Dictionary = result.get("checks", {})
	var stars := int(result.get("stars", 0))
	var star_text := "★".repeat(stars) + "☆".repeat(3 - stars)
	var grade_color := GREEN if stars >= 2 else AMBER if stars == 1 else RED
	var out := "[color=#%s]%s  %s[/color]\n\n" % [grade_color.to_html(false), star_text, str(result.get("grade", ""))]
	out += "[b]Purity[/b]        %.1f %%  %s\n" % [float(result.get("purity", 0.0)), _check_mark(bool(checks.get("purity", false)))]
	out += "[b]Isolated[/b]      %.2f g  %s\n" % [float(result.get("yield_g", 0.0)), _check_mark(bool(checks.get("yield", false)))]
	out += "[b]Melting point[/b] %.1f °C (%.1f–%.1f)  %s\n" % [
		float(result.get("melting_point_c", 0.0)),
		float(result.get("melting_point_c", 0.0)) - float(result.get("melting_range_c", 0.0)) * 0.5,
		float(result.get("melting_point_c", 0.0)) + float(result.get("melting_range_c", 0.0)) * 0.5,
		_check_mark(bool(checks.get("melting_point", false)))
	]
	out += "[b]TLC[/b]           Rf %.2f (lit. 0.45)  %s\n" % [float(result.get("tlc_rf", 0.0)), _check_mark(bool(checks.get("tlc", false)))]
	out += "[b]Conversion[/b]    %.0f %%\n" % (float(result.get("conversion", 0.0)) * 100.0)
	out += "[b]Theoretical[/b]   %.2f g\n\n" % float(result.get("theoretical_g", 0.0))
	out += "[b]XP[/b]            %d chemistry · %d engineering\n" % [int(result.get("xp_awarded", 0)), int(result.get("xp_engineering_awarded", 0))]
	if float(result.get("xp_multiplier", 1.0)) < 0.999:
		out += "[color=#85949f]Repeat batch: %.0f %% XP. New technique earns the full amount on a fresh route.[/color]\n" % (float(result.get("xp_multiplier", 1.0)) * 100.0)
	var warnings: Array = result.get("warnings", [])
	var shown := 0
	if not warnings.is_empty():
		out += "\n[b]DIAGNOSIS[/b]\n"
		for warning in warnings:
			if shown >= 5:
				break
			out += "[color=#ffb45c]• %s[/color]\n" % str(warning)
			shown += 1
	if bool(result.get("safety_pass", false)):
		out += "\n[color=#6ddbaa]Safety gate passed.[/color]"
	else:
		out += "\n[color=#ff6b60]Safety gate failed — the batch cannot be sold or used for the contract.[/color]"
	return out


func _check_mark(ok: bool) -> String:
	return "[color=#6ddbaa]PASS[/color]" if ok else "[color=#ff6b60]FAIL[/color]"


# =============================================================================
# APPARATUS RENDERING
# =============================================================================

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 64), Vector2(size.x, 64), Color(0.16, 0.24, 0.28, 0.7), 1.0)
	draw_rect(Rect2(16, 70, 308, 614), PANEL, true)
	draw_rect(Rect2(334, 70, 530, 388), PANEL_SOFT, true)
	draw_rect(Rect2(334, 70, 2, 614), Color(CYAN.r, CYAN.g, CYAN.b, 0.38), true)
	draw_rect(Rect2(870, 70, 394, 614), PANEL, true)
	_draw_stepper()
	_draw_apparatus()


func _draw_stepper() -> void:
	var font := ThemeDB.fallback_font
	var labels := ["WEIGH", "REFLUX", "WORKUP", "ASSAY"]
	var start := Vector2(366.0, 90.0)
	for i in range(4):
		var center := Vector2(start.x + float(i) * 118.0, start.y + 8.0)
		if i > 0:
			var prev := Vector2(start.x + float(i - 1) * 118.0, center.y)
			draw_line(prev, center, Color(0.25, 0.36, 0.4, 0.8), 1.5)
		var active: bool = (i + 1) <= _stage
		var current: bool = (i + 1) == _stage
		var color := CYAN if current else (GREEN if active else Color(0.3, 0.38, 0.43))
		draw_circle(center, 9.0 if current else 7.0, Color(color.r, color.g, color.b, 0.22))
		draw_arc(center, 8.0, 0.0, TAU, 24, color, 1.6)
		draw_string(font, center + Vector2(-3.0, 4.0), str(i + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, color)
		draw_string(font, Vector2(center.x - 27.0, center.y + 24.0), labels[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 8, color if active else DIM)


func _draw_apparatus() -> void:
	var font := ThemeDB.fallback_font
	var cx := 599.0
	var body_bottom := 404.0
	var body_top := 288.0
	var body_left := 534.0
	var body_right := 664.0

	# Bench
	draw_rect(Rect2(360, 408, 478, 6), Color(0.16, 0.21, 0.24), true)
	draw_line(Vector2(360, 414), Vector2(838, 414), Color(0.24, 0.31, 0.34, 0.8), 1.0)

	# Heating mantle
	var mantle_glow := clampf((_temp_c - 30.0) / 70.0, 0.0, 1.0)
	draw_arc(Vector2(cx, 397), 80.0, PI + 0.28, TAU - 0.28, 32, Color(0.2, 0.24, 0.27), 12.0)
	draw_arc(Vector2(cx, 397), 80.0, PI + 0.28, TAU - 0.28, 32, Color(0.95, 0.35, 0.16, 0.18 + 0.4 * mantle_glow), 4.0)
	draw_string(font, Vector2(cx - 38.0, 430.0), "HEATING MANTLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Condenser (Dimroth style, schematic)
	var cond_left := cx - 24.0
	var cond_right := cx + 24.0
	var cond_top := 118.0
	var cond_bottom := 214.0
	draw_rect(Rect2(cond_left, cond_top, cond_right - cond_left, cond_bottom - cond_top), Color(GLASS.r, GLASS.g, GLASS.b, 0.13), true)
	draw_rect(Rect2(cond_left, cond_top, cond_right - cond_left, cond_bottom - cond_top), GLASS, false, 1.5)
	var coil := PackedVector2Array()
	for i in range(13):
		var y := cond_top + 8.0 + float(i) * 7.0
		coil.append(Vector2(cond_left + 6.0 if i % 2 == 0 else cond_right - 6.0, y))
	draw_polyline(coil, Color(0.32, 0.76, 0.88, 0.75), 1.4)
	# Cooling hoses
	draw_arc(Vector2(cond_left - 12.0, 150.0), 14.0, -PI * 0.5, PI * 0.5, 14, Color(0.28, 0.55, 0.65, 0.8), 2.0)
	draw_arc(Vector2(cond_right + 12.0, 190.0), 14.0, PI * 0.5, PI * 1.5, 14, Color(0.28, 0.55, 0.65, 0.8), 2.0)
	draw_string(font, Vector2(cond_left - 6.0, 110.0), "CONDENSER", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Flask neck and body
	var flask := PackedVector2Array([
		Vector2(cx - 13.0, 214.0), Vector2(cx - 13.0, 258.0),
		Vector2(cx - 66.0, 380.0), Vector2(cx - 52.0, 404.0),
		Vector2(cx + 52.0, 404.0), Vector2(cx + 66.0, 380.0),
		Vector2(cx + 13.0, 258.0), Vector2(cx + 13.0, 214.0)
	])
	var closed := flask.duplicate()
	closed.append(flask[0])
	draw_colored_polygon(flask, Color(GLASS.r, GLASS.g, GLASS.b, 0.14))
	draw_polyline(closed, Color(0.7, 0.84, 0.9, 0.75), 1.8)

	# Liquid volume: 55 % of the flask body.
	var level_y: float = body_bottom - (body_bottom - body_top) * 0.55
	var liquid_color := Color(0.78, 0.87, 0.88, 0.5)
	if _temp_c > 85.0:
		liquid_color = Color(0.55, 0.36, 0.14, 0.62)
	if _stage >= 3:
		liquid_color = Color(0.66, 0.82, 0.86, 0.38)
	var liquid := PackedVector2Array()
	var steps := 18
	for i in range(steps + 1):
		var y := lerpf(level_y, body_bottom, float(i) / float(steps))
		var half := lerpf(13.0, 66.0, clampf((y - 258.0) / (380.0 - 258.0), 0.0, 1.0))
		if y > 380.0:
			half = lerpf(66.0, 52.0, (y - 380.0) / 24.0)
		liquid.append(Vector2(cx - half, y))
	for i in range(steps + 1):
		var y := lerpf(body_bottom, level_y, float(i) / float(steps))
		var half := lerpf(13.0, 66.0, clampf((y - 258.0) / (380.0 - 258.0), 0.0, 1.0))
		if y > 380.0:
			half = lerpf(66.0, 52.0, (y - 380.0) / 24.0)
		liquid.append(Vector2(cx + half, y))
	draw_colored_polygon(liquid, liquid_color)
	draw_line(Vector2(cx - 46.0, level_y), Vector2(cx + 46.0, level_y), Color(0.86, 0.95, 0.97, 0.65), 1.2)

	# Bubbles while reflux is running
	if _stage >= 2 and _reflux_done and _stage < 3:
		for i in range(7):
			var phase: float = fmod(_time * (0.5 + float(i) * 0.11) + float(i) * 0.37, 1.0)
			var bx: float = cx - 30.0 + float(i) * 10.0 + sin(_time * 2.0 + float(i)) * 4.0
			var by: float = level_y + 6.0 - phase * (level_y - 300.0)
			draw_circle(Vector2(bx, by), 2.2 + float(i % 3), Color(0.9, 0.97, 1.0, 0.35))

	# Crystals after workup
	if _stage >= 3:
		for i in range(9):
			var px: float = cx - 40.0 + float(i % 5) * 19.0
			var py: float = 398.0 - float(i / 5) * 8.0 - 2.0
			var diamond := PackedVector2Array([
				Vector2(px, py - 4.0), Vector2(px + 3.5, py), Vector2(px, py + 4.0), Vector2(px - 3.5, py)
			])
			draw_colored_polygon(diamond, Color(0.9, 0.96, 1.0, 0.72))

	# Thermometer
	draw_line(Vector2(cx + 88.0, 250.0), Vector2(cx + 88.0, 380.0), Color(0.6, 0.7, 0.76, 0.7), 2.0)
	draw_circle(Vector2(cx + 88.0, 384.0), 5.0, Color(0.95, 0.35, 0.3, 0.8))
	draw_string(font, Vector2(cx + 72.0, 238.0), "%.0f °C" % _temp_c, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, AMBER if _temp_c > 85.0 else TEXT)

	# Hood status plate
	var hood_color := GREEN if _hood else RED
	draw_rect(Rect2(748, 78, 100, 24), Color(hood_color.r, hood_color.g, hood_color.b, 0.14), true)
	draw_rect(Rect2(748, 78, 100, 24), Color(hood_color.r, hood_color.g, hood_color.b, 0.6), false, 1.0)
	draw_string(font, Vector2(758, 94), "HOOD %s" % ("ON" if _hood else "OFF"), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, hood_color)

	# Vapour when the hood is off and the flask is hot.
	if not _hood and _temp_c > 60.0:
		for i in range(3):
			var points := PackedVector2Array()
			for j in range(12):
				var t := float(j) / 11.0
				points.append(Vector2(cx - 18.0 + float(i) * 18.0 + sin(t * 6.0 + _time * 2.0 + float(i)) * 6.0, 205.0 - t * 70.0))
			draw_polyline(points, Color(0.85, 0.75, 0.6, 0.22), 1.5)

	draw_string(font, Vector2(360, 442), "250 mL 3-neck flask · Dimroth condenser · oil bath", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)
