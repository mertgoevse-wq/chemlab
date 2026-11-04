# Athanor Ascension — Fusor Workshop
# Interactive build checklist + live discharge model. The learning loop is
# build -> understand why -> energise -> read the diagnose. Failures are named
# after the real phenomenon (Paschen window, arcing, dose limit).

extends Control

const BG: Color = Color(0.03, 0.042, 0.05, 1.0)
const PANEL: Color = Color(0.055, 0.07, 0.082, 1.0)
const GRID: Color = Color(0.18, 0.26, 0.28, 0.5)
const TEXT: Color = Color(0.82, 0.88, 0.9)
const DIM: Color = Color(0.5, 0.59, 0.63)
const CYAN: Color = Color(0.3, 0.85, 0.9)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.36, 0.32)
const VIOLET: Color = Color(0.66, 0.5, 1.0)

var _built: Dictionary = {}
var _voltage_kv: float = 28.0
var _current_ma: float = 8.0
var _pressure_mtorr: float = 6.0
var _distance_m: float = 1.5
var _last_result: Dictionary = {}
var _time: float = 0.0
var _log: RichTextLabel
var _readout: RichTextLabel
var _why_panel: RichTextLabel
var _v_label: Label
var _i_label: Label
var _p_label: Label
var _d_label: Label


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build_ui()
	_refresh()


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _build_ui() -> void:
	var title := Label.new()
	title.text = "FUSOR WORKSHOP  ·  PLASMA & CIRCUITS"
	title.position = Vector2(24.0, 16.0)
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Inertial-electrostatic confinement · build it, understand it, then energise it"
	subtitle.position = Vector2(24.0, 42.0)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var back := Button.new()
	back.text = "← Return to Athanor"
	back.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	back.offset_left = -220.0
	back.offset_right = -20.0
	back.offset_top = 14.0
	back.offset_bottom = 44.0
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/main_menu/main_menu.tscn"))
	add_child(back)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(24.0, 78.0)
	scroll.custom_minimum_size = Vector2(440, 600)
	add_child(scroll)
	var steps := VBoxContainer.new()
	steps.custom_minimum_size = Vector2(420, 0)
	steps.add_theme_constant_override("separation", 6)
	scroll.add_child(steps)

	steps.add_child(_section("BUILD CHECKLIST"))
	for step in FusorPhysics.BUILD_STEPS:
		var check := CheckButton.new()
		check.text = str(step.get("title", ""))
		check.add_theme_font_size_override("font_size", 12)
		check.toggled.connect(func(pressed):
			_built[str(step.get("id", ""))] = pressed
			_why_panel.text = "[b]%s[/b]\n%s\n[color=#%s]Why: %s[/color]" % [
				str(step.get("title", "")), str(step.get("detail", "")), AMBER.to_html(false), str(step.get("why", ""))
			]
			_refresh())
		check.mouse_entered.connect(func():
			_why_panel.text = "[b]%s[/b]\n%s\n[color=#%s]Why: %s[/color]" % [
				str(step.get("title", "")), str(step.get("detail", "")), AMBER.to_html(false), str(step.get("why", ""))
			])
		steps.add_child(check)

	steps.add_child(_section("OPERATING POINT"))
	_v_label = _small("Cathode voltage · 28.0 kV")
	steps.add_child(_v_label)
	steps.add_child(_slider(2.0, 40.0, 28.0, _on_voltage_changed))

	_i_label = _small("Discharge current · 8.0 mA")
	steps.add_child(_i_label)
	steps.add_child(_slider(0.2, 30.0, 8.0, _on_current_changed))

	_p_label = _small("Chamber pressure · 6.0 mTorr")
	steps.add_child(_p_label)
	steps.add_child(_slider(0.1, 30.0, 6.0, _on_pressure_changed))

	_d_label = _small("Operator distance · 1.50 m")
	steps.add_child(_d_label)
	steps.add_child(_slider(0.5, 5.0, 1.5, _on_distance_changed))

	var run := Button.new()
	run.text = "⚡ Energise"
	run.custom_minimum_size = Vector2(0, 36)
	run.pressed.connect(_on_energise)
	steps.add_child(run)

	_why_panel = RichTextLabel.new()
	_why_panel.bbcode_enabled = true
	_why_panel.fit_content = true
	_why_panel.position = Vector2(490.0, 628.0)
	_why_panel.custom_minimum_size = Vector2(720, 62)
	_why_panel.add_theme_font_size_override("normal_font_size", 11)
	add_child(_why_panel)

	_readout = RichTextLabel.new()
	_readout.bbcode_enabled = true
	_readout.fit_content = true
	_readout.position = Vector2(500.0, 84.0)
	_readout.custom_minimum_size = Vector2(300, 320)
	_readout.add_theme_font_size_override("normal_font_size", 12)
	add_child(_readout)

	_log = RichTextLabel.new()
	_log.bbcode_enabled = true
	_log.fit_content = true
	_log.position = Vector2(830.0, 84.0)
	_log.custom_minimum_size = Vector2(390, 320)
	_log.add_theme_font_size_override("normal_font_size", 11)
	add_child(_log)
	_log.text = "[color=#7f8c9b]Diagnostics appear here after a run.[/color]"


func _on_voltage_changed(value: float) -> void:
	_voltage_kv = value
	_refresh()


func _on_current_changed(value: float) -> void:
	_current_ma = value
	_refresh()


func _on_pressure_changed(value: float) -> void:
	_pressure_mtorr = value
	_refresh()


func _on_distance_changed(value: float) -> void:
	_distance_m = value
	_refresh()


func _section(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 10)
	label.add_theme_color_override("font_color", DIM)
	return label


func _small(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 11)
	label.add_theme_color_override("font_color", TEXT)
	return label


func _slider(min_v: float, max_v: float, value: float, handler: Callable) -> HSlider:
	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.step = 0.1
	slider.value = value
	slider.custom_minimum_size = Vector2(400, 20)
	slider.value_changed.connect(handler)
	return slider


func _refresh() -> void:
	_v_label.text = "Cathode voltage · %.1f kV" % _voltage_kv
	_i_label.text = "Discharge current · %.1f mA" % _current_ma
	_p_label.text = "Chamber pressure · %.1f mTorr" % _pressure_mtorr
	_d_label.text = "Operator distance · %.2f m" % _distance_m

	var breakdown := FusorPhysics.paschen_breakdown_v(_pressure_mtorr, 4.0)
	var mfp := FusorPhysics.mean_free_path_m(_pressure_mtorr)
	var yield_per_s := FusorPhysics.neutron_yield_per_s(_voltage_kv, _current_ma, _pressure_mtorr)
	var dose := FusorPhysics.dose_rate_usv_h(yield_per_s, _distance_m)
	var gain := FusorPhysics.energy_gain_q(_voltage_kv, _current_ma, _pressure_mtorr)
	var window := FusorPhysics.pressure_window_ok(_pressure_mtorr)

	_readout.text = "[b][color=#%s]VACUUM & DISCHARGE[/color][/b]\n" % CYAN.to_html(false) + \
		"Paschen breakdown (4 cm gap)  %s V\n" % _f(breakdown) + \
		"mean free path               %s m\n" % _sci(mfp) + \
		"pressure window               %s\n" % ("inside 0.5–20 mTorr" if window else "[color=#ff5c52]outside[/color]") + \
		"\n[b][color=#%s]FUSION[/color][/b]\n" % VIOLET.to_html(false) + \
		"neutron yield      %s n/s\n" % _sci(yield_per_s) + \
		"fusion power       %s W\n" % _sci(FusorPhysics.fusion_power_w(yield_per_s)) + \
		"input power        %s W\n" % _f(FusorPhysics.input_power_w(_voltage_kv, _current_ma)) + \
		"energy gain Q      %s\n" % _sci(gain) + \
		"\n[b][color=#%s]RADIATION AT OPERATOR[/color][/b]\n" % AMBER.to_html(false) + \
		"dose rate      %.2f µSv/h\n" % dose + \
		"annual budget  %.2f%% of 20 mSv (1 h run)\n" % (FusorPhysics.annual_dose_fraction(dose, 1.0) * 100.0) + \
		"[color=#7f8c9b]D-D neutron energy 2.45 MeV. Yield scaling is empirical, not first-principles.[/color]"


func _on_energise() -> void:
	var build_complete := _built.size() >= FusorPhysics.BUILD_STEPS.size() and not _built.values().has(false)
	var result := FusorPhysics.simulate_run(_voltage_kv, _current_ma, _pressure_mtorr, _distance_m, build_complete)
	_last_result = result

	if not build_complete:
		var missing: Array[String] = []
		for step in FusorPhysics.BUILD_STEPS:
			if not bool(_built.get(str(step.get("id", "")), false)):
				missing.append(str(step.get("title", "")))
		_log.text = "[color=#ffb84a]Interlock: build incomplete.[/color]\nMissing: %s\n[color=#7f8c9b]The checklist is not decoration: each item is an actual failure mode.[/color]" % ", ".join(missing)
		return

	if bool(result.get("ok", false)):
		_log.text = "[b][color=#%s]STABLE DISCHARGE[/color][/b]\n%s\n\nDose at operator: %.2f µSv/h\nQ = %s\n\n[color=#7f8c9b]%s[/color]" % [
			CYAN.to_html(false), str(result.get("message", "")), float(result.get("dose_usv_h", 0.0)),
			_sci(float(result.get("q", 0.0))), "A fusor is a neutron source, not a power plant. Q stays far below 1."
		]
	else:
		_log.text = "[b][color=#ff5c52]RUN FAILED · %s[/color][/b]\n%s\n\n[color=#7f8c9b]Diagnose, adjust one variable, run again. That is the actual experimental method.[/color]" % [
			str(result.get("failure", "unknown")).replace("_", " ").to_upper(), str(result.get("message", ""))
		]


func _f(value: float) -> String:
	return "%.2f" % value


func _sci(value: float) -> String:
	if value == 0.0 or is_inf(value):
		return "—"
	var exponent := int(floor(log(value) / log(10.0)))
	var mantissa := value / pow(10.0, exponent)
	return "%.2f e%d" % [mantissa, exponent]


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 64), Vector2(size.x, 64), GRID, 1.0)

	# Chamber drawing.
	var chamber_center := Vector2(1020.0, 560.0)
	var radius := 56.0
	draw_circle(chamber_center, radius, Color(0.06, 0.09, 0.1, 0.9))
	draw_arc(chamber_center, radius, 0, TAU, 64, Color(0.5, 0.75, 0.8, 0.7), 2.0)
	draw_arc(chamber_center, radius - 6.0, 0, TAU, 64, Color(0.3, 0.5, 0.55, 0.4), 1.0)

	# Inner cathode grid.
	var grid_r := 26.0
	draw_arc(chamber_center, grid_r, 0, TAU, 40, Color(0.75, 0.82, 0.85, 0.55), 1.0)
	draw_arc(chamber_center, grid_r * 0.62, 0, TAU, 40, Color(0.75, 0.82, 0.85, 0.4), 1.0)
	for i in range(8):
		var angle := TAU * float(i) / 8.0
		draw_line(chamber_center + Vector2(cos(angle), sin(angle)) * grid_r * 0.6,
			chamber_center + Vector2(cos(angle), sin(angle)) * grid_r, Color(0.7, 0.8, 0.84, 0.3), 1.0)

	# Glow intensity scales with pressure and voltage.
	var glow_strength := 0.0
	if FusorPhysics.pressure_window_ok(_pressure_mtorr):
		glow_strength = clampf((_voltage_kv - 6.0) / 34.0, 0.0, 1.0) * 0.8
	var glow_color := Color(0.5, 0.4, 1.0, 0.16 + glow_strength * 0.3)
	draw_circle(chamber_center, grid_r * 1.6, glow_color)
	draw_circle(chamber_center, grid_r * 0.55, Color(1.0, 0.95, 1.0, glow_strength * 0.5))

	# Star filaments.
	for i in range(10):
		var angle := TAU * float(i) / 10.0 + sin(_time * 0.4 + i) * 0.04
		var start := chamber_center + Vector2(cos(angle), sin(angle)) * grid_r
		var end := chamber_center + Vector2(cos(angle), sin(angle)) * (radius - 12.0)
		draw_line(start, end, Color(0.55, 0.6, 1.0, 0.12 + glow_strength * 0.25), 1.0)

	# HV feedthrough and supply.
	draw_line(chamber_center + Vector2(0, -radius), chamber_center + Vector2(0, -radius - 54.0), Color(0.7, 0.74, 0.78, 0.7), 3.0)
	draw_rect(Rect2(chamber_center + Vector2(-34, -radius - 86.0), Vector2(68, 32)), Color(0.1, 0.13, 0.15), true)
	draw_rect(Rect2(chamber_center + Vector2(-34, -radius - 86.0), Vector2(68, 32)), GRID, false, 1.0)
	draw_string(ThemeDB.fallback_font, chamber_center + Vector2(-30, -radius - 64.0), "HV",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 11, AMBER)

	# Pump line.
	draw_line(chamber_center + Vector2(-radius, 30), chamber_center + Vector2(-radius - 58, 30), Color(0.55, 0.7, 0.74, 0.6), 4.0)
	draw_rect(Rect2(chamber_center + Vector2(-radius - 96, 12), Vector2(40, 36)), Color(0.1, 0.14, 0.16), true)
	draw_rect(Rect2(chamber_center + Vector2(-radius - 96, 12), Vector2(40, 36)), GRID, false, 1.0)
	draw_string(ThemeDB.fallback_font, chamber_center + Vector2(-radius - 92, 66), "PUMP",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Deat probe.
	draw_line(chamber_center + Vector2(radius, 0), Vector2(1150.0, 560.0), Color(0.55, 0.75, 0.7, 0.5), 2.0)
	draw_circle(Vector2(1156.0, 560.0), 7.0, Color(0.2, 0.3, 0.28))
	draw_string(ThemeDB.fallback_font, Vector2(1138, 586), "D2", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Radiation rings when yield is high.
	if bool(_last_result.get("ok", false)):
		var y := float(_last_result.get("neutron_yield_per_s", 0.0))
		if y > 1.0e5:
			var pulse := 0.5 + 0.5 * sin(_time * 1.8)
			draw_arc(chamber_center, radius + 16.0 + pulse * 10.0, 0, TAU, 64, Color(1.0, 0.65, 0.2, 0.2 * (1.0 - pulse)), 2.0)

	draw_string(ThemeDB.fallback_font, Vector2(24, 700), "FUSOR SCHEMATIC · inner grid cathode · D-D fusion",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)
