# Athanor Ascension — Titration Practicum
#
# A real volumetric titration: hold the stopcock, watch the equilibrium pH move,
# stop at the first persistent phenolphthalein pink. The curve is solved from
# charge balance (see scripts/labs/titration_chemistry.gd), not from a lookup
# table. Scoring compares the volume at which you stopped to the true indicator
# endpoint, so the lesson is precision near equivalence, not clicking fast.
extends Control

const CHEM := preload("res://scripts/labs/titration_chemistry.gd")
const HUB_SCENE: String = "res://scenes/laboratories/lab_hub.tscn"
const CODEX_SCENE: String = "res://scenes/progression/skill_codex.tscn"

const BG := Color(0.026, 0.037, 0.048, 1.0)
const PANEL := Color(0.052, 0.068, 0.084, 0.96)
const TEXT := Color(0.84, 0.90, 0.93)
const DIM := Color(0.50, 0.60, 0.66)
const CYAN := Color(0.25, 0.85, 0.92)
const AMBER := Color(1.0, 0.72, 0.28)
const RED := Color(1.0, 0.40, 0.36)
const GREEN := Color(0.40, 0.85, 0.65)
const GRID := Color(0.16, 0.24, 0.28, 0.7)

const BURETTE_MAX_ML := 50.0
const MAX_TITRANT_ML := 55.0
const BEAKER_MAX_ML := 80.0

var _acid_index: int = 0
var _acid_molarity: float = 0.100
var _acid_ml: float = 25.0
var _ka: float = CHEM.STRONG_KA
var _base_molarity: float = 0.100
var _base_ml: float = 0.0
var _ph: float = 1.0
var _flowing: bool = false
var _flow_rate: float = 0.0
var _endpoint_ml: float = -1.0
var _submitted: bool = false
var _runs: int = 0
var _drop_phase: float = 0.0
var _last_result: Dictionary = {}

var _volume_label: Label
var _ph_label: Label
var _hint_label: Label
var _result: RichTextLabel
var _flow_button: Button
var _submit_button: Button
var _acid_option: OptionButton
var _codex_button: Button
var _toast: Label
var _toast_time: float = 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build_ui()
	_reset_run()


func _build_ui() -> void:
	var title := Label.new()
	title.text = "VOLUMETRIC ANALYSIS  ·  ACID–BASE TITRATION"
	title.position = Vector2(26, 16)
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var sub := Label.new()
	sub.text = "0.100 M NaOH titrant · phenolphthalein · equilibrium solved each frame"
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

	var acid_label := Label.new()
	acid_label.text = "ANALYTE  (25.00 mL aliquot)"
	acid_label.position = Vector2(26, 86)
	acid_label.add_theme_font_size_override("font_size", 10)
	acid_label.add_theme_color_override("font_color", DIM)
	add_child(acid_label)

	_acid_option = OptionButton.new()
	_acid_option.position = Vector2(26, 106)
	_acid_option.custom_minimum_size = Vector2(292, 34)
	_acid_option.add_item("Hydrochloric acid HCl · strong · pH(eq) 7.0")
	_acid_option.add_item("Acetic acid CH₃COOH · weak · pH(eq) 8.7")
	_acid_option.item_selected.connect(_on_acid_selected)
	add_child(_acid_option)

	var vol_caption := Label.new()
	vol_caption.text = "TITRANT DELIVERED"
	vol_caption.position = Vector2(26, 160)
	vol_caption.add_theme_font_size_override("font_size", 10)
	vol_caption.add_theme_color_override("font_color", DIM)
	add_child(vol_caption)

	_volume_label = Label.new()
	_volume_label.position = Vector2(24, 176)
	_volume_label.add_theme_font_size_override("font_size", 38)
	_volume_label.add_theme_color_override("font_color", TEXT)
	add_child(_volume_label)

	_ph_label = Label.new()
	_ph_label.position = Vector2(26, 226)
	_ph_label.add_theme_font_size_override("font_size", 12)
	add_child(_ph_label)

	_flow_button = Button.new()
	_flow_button.text = "Hold to open stopcock"
	_flow_button.position = Vector2(26, 264)
	_flow_button.custom_minimum_size = Vector2(292, 54)
	_flow_button.button_down.connect(_on_flow_down)
	_flow_button.button_up.connect(_on_flow_up)
	add_child(_flow_button)

	var drop := Button.new()
	drop.text = "+ 1 drop (0.05 mL)"
	drop.position = Vector2(26, 326)
	drop.custom_minimum_size = Vector2(140, 36)
	drop.pressed.connect(func() -> void: _add_volume(0.05))
	add_child(drop)

	var half := Button.new()
	half.text = "+ 0.50 mL"
	half.position = Vector2(178, 326)
	half.custom_minimum_size = Vector2(140, 36)
	half.pressed.connect(func() -> void: _add_volume(0.50))
	add_child(half)

	_submit_button = Button.new()
	_submit_button.text = "■  Stop & submit for assay"
	_submit_button.position = Vector2(26, 376)
	_submit_button.custom_minimum_size = Vector2(292, 40)
	_submit_button.pressed.connect(_on_submit)
	add_child(_submit_button)

	var reset := Button.new()
	reset.text = "↺ Fresh aliquot"
	reset.position = Vector2(26, 424)
	reset.custom_minimum_size = Vector2(292, 34)
	reset.pressed.connect(_on_reset)
	add_child(reset)

	_codex_button = Button.new()
	_codex_button.text = "◇ Skill codex & unlocks"
	_codex_button.position = Vector2(26, 466)
	_codex_button.custom_minimum_size = Vector2(292, 34)
	_codex_button.pressed.connect(func() -> void: get_tree().change_scene_to_file(CODEX_SCENE))
	add_child(_codex_button)

	_hint_label = Label.new()
	_hint_label.position = Vector2(26, 512)
	_hint_label.custom_minimum_size = Vector2(292, 20)
	_hint_label.add_theme_font_size_override("font_size", 11)
	add_child(_hint_label)

	_result = RichTextLabel.new()
	_result.bbcode_enabled = true
	_result.position = Vector2(26, 540)
	_result.custom_minimum_size = Vector2(292, 164)
	_result.add_theme_font_size_override("normal_font_size", 11)
	_result.text = "[color=#7f8c9b]The assay report appears here after you submit a persistent endpoint.[/color]"
	add_child(_result)

	_toast = Label.new()
	_toast.position = Vector2(350, 660)
	_toast.custom_minimum_size = Vector2(500, 24)
	_toast.add_theme_font_size_override("font_size", 13)
	_toast.add_theme_color_override("font_color", GREEN)
	_toast.modulate.a = 0.0
	add_child(_toast)

	_refresh_labels()


func _process(delta: float) -> void:
	if _flowing and not _submitted:
		_flow_rate = minf(_flow_rate + delta * 2.4, 3.2)
		_add_volume(_flow_rate * delta)
		_drop_phase = fmod(_drop_phase + delta * 9.0, 1.0)
	if _toast_time > 0.0:
		_toast_time = maxf(_toast_time - delta, 0.0)
		_toast.modulate.a = clampf(_toast_time / 0.6, 0.0, 1.0)
	queue_redraw()


# =============================================================================
# SIMULATION
# =============================================================================

func _reset_run() -> void:
	_base_ml = 0.0
	_endpoint_ml = -1.0
	_submitted = false
	_flowing = false
	_flow_rate = 0.0
	_last_result = {}
	_ph = CHEM.ph_at(_acid_molarity, _acid_ml, _base_molarity, 0.0, _ka)
	if _result != null:
		_result.text = "[color=#7f8c9b]The assay report appears here after you submit a persistent endpoint.[/color]"
	if _flow_button != null:
		_flow_button.text = "Hold to open stopcock"
	_flow_rate = 0.0
	_refresh_labels()


func _add_volume(ml: float) -> void:
	if _submitted or ml <= 0.0:
		return
	var before_ph := _ph
	var before_ml := _base_ml
	_base_ml = minf(_base_ml + ml, MAX_TITRANT_ML)
	_ph = CHEM.ph_at(_acid_molarity, _acid_ml, _base_molarity, _base_ml, _ka)
	if _endpoint_ml < 0.0 and before_ph < CHEM.PHENOLPHTHALEIN_PH and _ph >= CHEM.PHENOLPHTHALEIN_PH:
		# Across the equivalence cliff a whole frame can jump several pH units,
		# so linear pH interpolation reports nonsense. Bisect the equilibrium
		# curve on volume instead: the endpoint stays exact at any flow rate.
		var lo := before_ml
		var hi := _base_ml
		for _i in range(50):
			var mid := (lo + hi) * 0.5
			if CHEM.ph_at(_acid_molarity, _acid_ml, _base_molarity, mid, _ka) >= CHEM.PHENOLPHTHALEIN_PH:
				hi = mid
			else:
				lo = mid
		_endpoint_ml = (lo + hi) * 0.5
		_flash_toast("Persistent pink at %.3f mL — release the stopcock." % _endpoint_ml)
	if _base_ml >= MAX_TITRANT_ML:
		_flowing = false
		_flow_rate = 0.0
		_flow_button.text = "Burette empty — fresh aliquot"
	_refresh_labels()


func _on_flow_down() -> void:
	if _submitted:
		return
	_flowing = true
	_flow_rate = 0.15
	_flow_button.text = "Stopcock OPEN — release to stop"


func _on_flow_up() -> void:
	_flowing = false
	_flow_rate = 0.0
	if not _submitted:
		_flow_button.text = "Hold to open stopcock"


func _on_submit() -> void:
	if _endpoint_ml < 0.0:
		_result.text = "[color=#ffb84a][b]No endpoint.[/b][/color]\nThe solution never held a pink tint. Phenolphthalein only reports pH ≥ 8.2; add titrant and watch for the first persistent colour."
		return

	_submitted = true
	_flowing = false
	_flow_rate = 0.0
	_flow_button.text = "Assay submitted"
	_submit_button.disabled = true

	var equivalence := CHEM.equivalence_ml(_acid_molarity, _acid_ml, _base_molarity)
	var target := CHEM.endpoint_ml(_acid_molarity, _acid_ml, _base_molarity, _ka, CHEM.PHENOLPHTHALEIN_PH)
	var eq_ph := CHEM.ph_at_equivalence(_acid_molarity, _acid_ml, _base_molarity, _ka)
	var error_ml := absf(_endpoint_ml - target)
	var accuracy := clampf(1.0 - error_ml / 0.60, 0.0, 1.0)
	var base_xp := int(round(40.0 + 80.0 * accuracy))
	var multiplier := 1.0 if _runs < 3 else 0.25
	var xp := maxi(1, int(round(float(base_xp) * multiplier)))
	_runs += 1

	var stars := 1
	if error_ml <= 0.08:
		stars = 3
	elif error_ml <= 0.25:
		stars = 2

	var award: Dictionary = {}
	var skill_manager := get_node_or_null("/root/SkillManager")
	if skill_manager != null:
		award = skill_manager.add_xp("chemistry", xp, "Titration endpoint (%s)" % _acid_name())
	var new_level := int(award.get("level_after", 0))

	var grade := "EXEMPLARY" if stars == 3 else ("COMPETENT" if stars == 2 else "ACCEPTABLE")
	var grade_color := GREEN if stars == 3 else (AMBER if stars == 2 else DIM)
	var level_line := ""
	if new_level > 0:
		level_line = "\n[color=#3ddc97]+%d Chemistry XP[/color] · level %d" % [xp, new_level]
		var unlocked: Array = award.get("milestones", [])
		for milestone in unlocked:
			level_line += "\n[color=#ffb84a]◆ Milestone: %s[/color]" % str(milestone.get("title", ""))

	_result.text = "[b][color=#%s]%s[/color][/b]  %s\n\nEndpoint found      %.3f mL\nTrue 8.2 mL point   %.3f mL\nEquivalence         %.3f mL\nError               %.3f mL\n\npH at equivalence   %.2f\n[color=#7f8c9b]%s[/color]%s" % [
		grade_color.to_html(false),
		grade,
		"★".repeat(stars) + "☆".repeat(3 - stars),
		_endpoint_ml,
		target,
		equivalence,
		error_ml,
		eq_ph,
		_teaching_line(eq_ph),
		level_line
	]
	_last_result = {
		"endpoint_ml": _endpoint_ml,
		"target_ml": target,
		"equivalence_ml": equivalence,
		"error_ml": error_ml,
		"xp": xp,
		"stars": stars
	}
	_flash_toast("%s · +%d Chemistry XP" % [grade, xp])
	_refresh_labels()


func _teaching_line(eq_ph: float) -> String:
	if _acid_index == 0:
		return "Strong acid: equivalence is neutral (pH %.2f), so the first pink appears only after equivalence. One extra drop is enough to overshoot — this is why dropwise control matters." % eq_ph
	return "Weak acid: at equivalence the solution is basic (pH %.2f) because acetate hydrolyses. Phenolphthalein's 8.2 transition lands on that equivalence pH, which is why it is the correct indicator here — not methyl orange." % eq_ph


func _on_reset() -> void:
	_submit_button.disabled = false
	_reset_run()
	_flash_toast("Fresh 25.00 mL aliquot prepared.")


func _on_acid_selected(index: int) -> void:
	_acid_index = index
	_ka = CHEM.STRONG_KA if index == 0 else 1.8e-5
	_submit_button.disabled = false
	_reset_run()


func _acid_name() -> String:
	return "HCl" if _acid_index == 0 else "acetic acid"


func _refresh_labels() -> void:
	_volume_label.text = "%.2f mL" % _base_ml
	var state := CHEM.indicator_state(_ph)
	var state_color := DIM if _ph < CHEM.PHENOLPHTHALEIN_PH else (AMBER if _ph < 10.0 else RED)
	_ph_label.text = "pH %.2f  ·  indicator %s" % [_ph, state]
	_ph_label.add_theme_color_override("font_color", state_color)
	if _endpoint_ml < 0.0 and not _submitted:
		_hint_label.text = "Colourless. Add titrant slowly near 24 mL."
		_hint_label.add_theme_color_override("font_color", DIM)
	elif not _submitted:
		_hint_label.text = "Endpoint held. Submit to assay %.3f mL." % _endpoint_ml
		_hint_label.add_theme_color_override("font_color", GREEN)
	else:
		_hint_label.text = "Assay complete. Reset for a fresh aliquot."
		_hint_label.add_theme_color_override("font_color", CYAN)


func _flash_toast(message: String) -> void:
	_toast.text = message
	_toast_time = 3.2
	_toast.modulate.a = 1.0


# =============================================================================
# RENDERING
# =============================================================================

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 70), Vector2(size.x, 70), GRID, 1.0)
	draw_rect(Rect2(12, 78, 320, 632), PANEL, true)
	draw_rect(Rect2(344, 78, 500, 632), Color(0.045, 0.06, 0.074, 0.82), true)
	draw_rect(Rect2(856, 78, 412, 632), PANEL, true)
	draw_rect(Rect2(344, 78, 2, 632), Color(CYAN.r, CYAN.g, CYAN.b, 0.35), true)

	_draw_burette_and_beaker()
	_draw_curve()
	_draw_teaching()


func _draw_burette_and_beaker() -> void:
	var font := ThemeDB.fallback_font
	var tube_x := 594.0
	var tube_top := 106.0
	var tube_bottom := 376.0
	draw_rect(Rect2(tube_x - 15, tube_top, 30, tube_bottom - tube_top), Color(0.10, 0.16, 0.19, 1.0), true)
	draw_rect(Rect2(tube_x - 15, tube_top, 30, tube_bottom - tube_top), Color(0.30, 0.48, 0.54, 0.8), false, 1.4)

	# Titrant column: full at 0 mL delivered, empty at 50 mL.
	var remaining := clampf(1.0 - _base_ml / BURETTE_MAX_ML, 0.0, 1.0)
	var liquid_top := tube_top + (tube_bottom - tube_top) * (1.0 - remaining)
	var titrant_color := Color(0.20, 0.62, 0.72, 0.75)
	draw_rect(Rect2(tube_x - 11, liquid_top, 22, tube_bottom - liquid_top), titrant_color, true)
	draw_line(Vector2(tube_x - 11, liquid_top), Vector2(tube_x + 11, liquid_top), Color(0.75, 0.95, 1.0, 0.9), 1.5)

	# Graduations every 5 mL.
	for ml in range(0, 51, 5):
		var y := tube_top + (tube_bottom - tube_top) * (float(ml) / BURETTE_MAX_ML)
		var length := 10.0 if ml % 10 == 0 else 6.0
		draw_line(Vector2(tube_x + 15, y), Vector2(tube_x + 15 + length, y), Color(0.5, 0.65, 0.7, 0.7), 1.0)
		if ml % 10 == 0:
			draw_string(font, Vector2(tube_x + 30, y + 4), "%d" % ml, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Stopcock and tip.
	draw_rect(Rect2(tube_x - 6, tube_bottom, 12, 16), Color(0.35, 0.42, 0.46), true)
	draw_circle(Vector2(tube_x, tube_bottom + 8), 7.0, Color(0.55, 0.62, 0.66))
	draw_line(Vector2(tube_x, tube_bottom + 16), Vector2(tube_x, tube_bottom + 32), Color(0.55, 0.62, 0.66), 2.0)

	if _flowing and not _submitted:
		var drop_y := tube_bottom + 36 + 22 * _drop_phase
		draw_circle(Vector2(tube_x, drop_y), 3.0, Color(0.55, 0.85, 0.95, 0.9))
		draw_line(Vector2(tube_x, tube_bottom + 32), Vector2(tube_x, drop_y - 4), Color(0.4, 0.75, 0.85, 0.35), 1.0)

	# Beaker.
	var beaker := Rect2(496, 424, 196, 196)
	draw_rect(beaker, Color(0.10, 0.15, 0.18, 0.35), true)
	draw_rect(beaker, Color(0.45, 0.62, 0.68, 0.65), false, 2.0)
	draw_line(beaker.position + Vector2(0, 20), beaker.position + Vector2(26, 20), Color(0.45, 0.62, 0.68, 0.65), 2.0)
	draw_line(beaker.position + Vector2(beaker.size.x, 20), beaker.position + Vector2(beaker.size.x - 26, 20), Color(0.45, 0.62, 0.68, 0.65), 2.0)

	var fill := clampf((_acid_ml + _base_ml) / BEAKER_MAX_ML, 0.0, 1.0)
	var liquid_height := 152.0 * fill
	var liquid := Rect2(beaker.position.x + 3, beaker.end.y - 3 - liquid_height, beaker.size.x - 6, liquid_height)
	draw_rect(liquid, CHEM.color_for_ph(_ph), true)
	if liquid_height > 1.0:
		draw_line(Vector2(liquid.position.x, liquid.position.y), Vector2(liquid.end.x, liquid.position.y), Color(0.85, 0.95, 1.0, 0.55), 1.2)
		draw_line(Vector2(liquid.position.x, liquid.position.y + 2), Vector2(liquid.position.x + 22, liquid.position.y + 2), Color(1, 1, 1, 0.18), 1.0)
		draw_line(Vector2(liquid.end.x - 22, liquid.position.y + 2), Vector2(liquid.end.x, liquid.position.y + 2), Color(1, 1, 1, 0.18), 1.0)

	# Beaker graduations.
	for ml in range(10, 71, 10):
		var y := beaker.end.y - 3 - 152.0 * (float(ml) / BEAKER_MAX_ML)
		draw_line(Vector2(beaker.position.x + 3, y), Vector2(beaker.position.x + 18, y), Color(0.5, 0.65, 0.7, 0.55), 1.0)
		draw_string(font, Vector2(beaker.position.x - 22, y + 4), "%d" % ml, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, DIM)

	draw_string(font, Vector2(496, 404), "25.00 mL aliquot + phenolphthalein", HORIZONTAL_ALIGNMENT_LEFT, 196, 10, DIM)
	draw_string(font, Vector2(496, 646), "%s · 0.100 M · pH %.2f" % [_acid_name().to_upper(), _ph], HORIZONTAL_ALIGNMENT_LEFT, 260, 11, TEXT)

	# Volume callout.
	draw_string(font, Vector2(722, 470), "V =", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, DIM)
	draw_string(font, Vector2(722, 496), "%.2f" % _base_ml, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, TEXT)
	draw_string(font, Vector2(722, 516), "mL NaOH", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)


func _draw_curve() -> void:
	var plot := Rect2(884, 146, 352, 250)
	var font := ThemeDB.fallback_font
	draw_rect(plot, Color(0.035, 0.05, 0.06, 1.0), true)
	draw_rect(plot, GRID, false, 1.0)
	draw_string(font, Vector2(884, 132), "pH  vs  TITRANT VOLUME", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, TEXT)

	for p in range(0, 15, 2):
		var y := plot.end.y - (float(p) / 14.0) * plot.size.y
		draw_line(Vector2(plot.position.x, y), Vector2(plot.end.x, y), Color(0.14, 0.2, 0.24, 0.7), 1.0)
		draw_string(font, Vector2(plot.position.x - 26, y + 4), "%d" % p, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, DIM)
	for v in range(0, 51, 10):
		var x := plot.position.x + (float(v) / 50.0) * plot.size.x
		draw_line(Vector2(x, plot.position.y), Vector2(x, plot.end.y), Color(0.14, 0.2, 0.24, 0.5), 1.0)
		draw_string(font, Vector2(x - 6, plot.end.y + 14), "%d" % v, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, DIM)
	draw_string(font, Vector2(plot.end.x - 40, plot.end.y + 28), "mL", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, DIM)

	# Indicator transition band.
	var y82 := plot.end.y - (CHEM.PHENOLPHTHALEIN_PH / 14.0) * plot.size.y
	draw_line(Vector2(plot.position.x, y82), Vector2(plot.end.x, y82), Color(AMBER.r, AMBER.g, AMBER.b, 0.55), 1.0)
	draw_string(font, Vector2(plot.position.x + 6, y82 - 4), "phenolphthalein 8.2", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, AMBER)

	var points := PackedVector2Array()
	for i in range(0, 121):
		var ml := 50.0 * float(i) / 120.0
		var ph := CHEM.ph_at(_acid_molarity, _acid_ml, _base_molarity, ml, _ka)
		var point := Vector2(
			plot.position.x + (ml / 50.0) * plot.size.x,
			plot.end.y - (ph / 14.0) * plot.size.y
		)
		points.append(point)
	draw_polyline(points, Color(CYAN.r, CYAN.g, CYAN.b, 0.9), 2.0)

	# Equivalence marker (calculable from known concentration, so shown up front).
	var equivalence := CHEM.equivalence_ml(_acid_molarity, _acid_ml, _base_molarity)
	var eq_x := plot.position.x + (equivalence / 50.0) * plot.size.x
	draw_dashed_line(Vector2(eq_x, plot.position.y), Vector2(eq_x, plot.end.y), Color(0.5, 0.6, 0.66, 0.6), 1.0, 5.0)
	draw_string(font, Vector2(eq_x + 4, plot.position.y + 12), "eq", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, DIM)

	var current_x := plot.position.x + (minf(_base_ml, 50.0) / 50.0) * plot.size.x
	var current_y := plot.end.y - (_ph / 14.0) * plot.size.y
	draw_circle(Vector2(current_x, current_y), 4.0, Color.WHITE)
	draw_arc(Vector2(current_x, current_y), 7.0, 0, TAU, 20, CYAN, 1.2)

	if _endpoint_ml >= 0.0:
		var end_x := plot.position.x + (_endpoint_ml / 50.0) * plot.size.x
		draw_line(Vector2(end_x, plot.position.y), Vector2(end_x, plot.end.y), Color(1.0, 0.4, 0.7, 0.8), 1.0)


func _draw_teaching() -> void:
	var font := ThemeDB.fallback_font
	var x := 884.0
	var y := 440.0
	draw_string(font, Vector2(x, y), "READ THE CURVE", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)

	var equivalence := CHEM.equivalence_ml(_acid_molarity, _acid_ml, _base_molarity)
	var eq_ph := CHEM.ph_at_equivalence(_acid_molarity, _acid_ml, _base_molarity, _ka)
	var target := CHEM.endpoint_ml(_acid_molarity, _acid_ml, _base_molarity, _ka)
	var lines: Array[String] = []
	lines.append("Moles analyte      %.3f mmol" % (_acid_molarity * _acid_ml))
	lines.append("Equivalence        %.2f mL" % equivalence)
	lines.append("pH at equivalence  %.2f" % eq_ph)
	lines.append("8.2 endpoint       %.3f mL" % target)
	if _endpoint_ml >= 0.0:
		lines.append("Your endpoint      %.3f mL" % _endpoint_ml)
	var line_y := y + 22.0
	for line in lines:
		draw_string(font, Vector2(x, line_y), line, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, TEXT)
		line_y += 19.0

	var note := "Weak acid buffering keeps pH flat until the equivalence cliff. The steep jump is why one drop can change everything."
	if _acid_index == 0:
		note = "A strong acid has no buffer region: pH climbs slowly, then jumps ~6 units at equivalence. Precision is decided in the last 0.5 mL."
	var wrapped := _wrap(note, 52)
	line_y += 6.0
	for row in wrapped:
		draw_string(font, Vector2(x, line_y), row, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)
		line_y += 15.0

	# Indicator equilibrium: why the colour appears where it does.
	line_y += 20.0
	draw_line(Vector2(x, line_y - 12), Vector2(1236, line_y - 12), GRID, 1.0)
	draw_string(font, Vector2(x, line_y), "INDICATOR EQUILIBRIUM", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, AMBER)
	line_y += 18.0
	var mechanism := "H₂In (colourless) ⇌ In²⁻ (pink) + 2 H⁺. Base removes H⁺, so the equilibrium shifts right and the pink persists."
	for row in _wrap(mechanism, 54):
		draw_string(font, Vector2(x, line_y), row, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, TEXT)
		line_y += 15.0
	line_y += 8.0
	draw_string(font, Vector2(x, line_y), "Transition range 8.2–10.0 · endpoint ≠ equivalence for a strong acid", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)


func _wrap(text: String, width: int) -> Array[String]:
	var out: Array[String] = []
	var words := text.split(" ")
	var line := ""
	for word in words:
		if (line + " " + word).length() > width and line != "":
			out.append(line)
			line = word
		else:
			line = word if line == "" else line + " " + word
	if line != "":
		out.append(line)
	return out
