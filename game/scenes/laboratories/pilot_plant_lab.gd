# Athanor Ascension — Industrial Pilot Plant
# Continuous flow reactors, distillation columns, process control, scale-up, GMP.
# Failures: thermal runaway, pressure relief, toxic release, runaway reaction.

extends Control

const BG: Color = Color(0.04, 0.04, 0.05, 1.0)
const PANEL: Color = Color(0.07, 0.07, 0.09, 0.95)
const TEXT: Color = Color(0.85, 0.9, 0.95)
const DIM: Color = Color(0.55, 0.6, 0.65)
const CYAN: Color = Color(0.5, 0.85, 1.0)
const AMBER: Color = Color(1.0, 0.75, 0.3)
const RED: Color = Color(1.0, 0.35, 0.35)
const GREEN: Color = Color(0.5, 0.85, 0.5)

var _process: String = "cstr"
var _feed_rate: float = 100.0  # L/h
var _reactor_temp_c: float = 80.0
var _cooling_duty: float = 0.0  # kW
var _pressure_bar: float = 2.0
var _conversion: float = 0.0
var _runaway_risk: bool = false
var _relief_valve_open: bool = false
var _toxic_release: bool = false
var _gmp_compliant: bool = true

var _log: RichTextLabel
var _readout: RichTextLabel
var _why_panel: RichTextLabel

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build_ui()
	_refresh_all()

func _build_ui() -> void:
	var title := Label.new()
	title.text = "PILOT PLANT  ·  CONTINUOUS FLOW • SCALE-UP • GMP"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "CSTR · distillation · process control · runaway · pressure relief · toxic release"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var proc := _panel("Reactor operation", Vector2(24, 68), Vector2(560, 300))
	_anchor_dropdown(proc, "Unit operation", ["cstr", "distillation", "crystallization", "filtration"], _process, func(v): _process = v)
	_anchor_slider(proc, "Feed rate L/h", 10.0, 500.0, _feed_rate, func(v): _feed_rate = v)
	_anchor_slider(proc, "Reactor temp °C", 20.0, 200.0, _reactor_temp_c, func(v): _reactor_temp_c = v)
	_anchor_slider(proc, "Cooling duty kW", 0.0, 500.0, _cooling_duty, func(v): _cooling_duty = v)
	_anchor_slider(proc, "Pressure bar", 0.5, 10.0, _pressure_bar, func(v): _pressure_bar = v)
	_anchor_checkbox(proc, "GMP compliant", _gmp_compliant, func(v): _gmp_compliant = v)
	var run_btn := Button.new()
	run_btn.text = "Run material balance"
	run_btn.position = Vector2(14, 300 - 28)
	run_btn.size = Vector2(160, 26)
	run_btn.pressed.connect(func(): _run_balance())
	proc.add_child(run_btn)

	var safe := _panel("Safety systems", Vector2(608, 68), Vector2(560, 300))
	_anchor_checkbox(safe, "Thermal runaway scenario", _runaway_risk, func(v): _runaway_risk = v)
	_anchor_checkbox(safe, "Pressure relief valve open", _relief_valve_open, func(v): _relief_valve_open = v)
	_anchor_checkbox(safe, "Toxic release scenario", _toxic_release, func(v): _toxic_release = v)
	var safe_btn := Button.new()
	safe_btn.text = "Evaluate safety"
	safe_btn.position = Vector2(14, 300 - 28)
	safe_btn.size = Vector2(160, 26)
	safe_btn.pressed.connect(func(): _evaluate_safety())
	safe.add_child(safe_btn)

	_log := RichTextLabel.new()
	_log.position = Vector2(608, 388)
	_log.size = Vector2(560, 220)
	_log.add_theme_color_override("font_color", TEXT)
	add_child(_log)

	_readout := RichTextLabel.new()
	_readout.position = Vector2(1192, 68)
	_readout.size = Vector2(420, 540)
	_readout.add_theme_color_override("font_color", TEXT)
	add_child(_readout)

	_why_panel := RichTextLabel.new()
	_why_panel.position = Vector2(1192, 620)
	_why_panel.size = Vector2(420, 120)
	_why_panel.add_theme_color_override("font_color", AMBER)
	add_child(_why_panel)

func _panel(title: String, pos: Vector2, size: Vector2) -> PanelContainer:
	var p := PanelContainer.new()
	p.position = pos
	p.size = size
	var t := Label.new()
	t.text = title
	t.position = Vector2(10, 8)
	t.add_theme_font_size_override("font_size", 13)
	t.add_theme_color_override("font_color", CYAN)
	p.add_child(t)
	add_child(p)
	return p

func _anchor_dropdown(parent: Control, label: String, options: Array, current: String, on_changed: Callable) -> void:
	var lbl := Label.new()
	lbl.text = label
	lbl.position = Vector2(14, _cursor(parent))
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", DIM)
	parent.add_child(lbl)

	var opt := OptionButton.new()
	opt.position = Vector2(14, _cursor(parent) + 16)
	opt.size = Vector2(200, 24)
	for o in options:
		opt.add_item(o)
	opt.select(options.find(current))
	opt.item_selected.connect(func(idx): on_changed(opt.get_item_text(idx)))
	parent.add_child(opt)

func _anchor_checkbox(parent: Control, label: String, cur: bool, on_changed: Callable) -> void:
	var cb := CheckButton.new()
	cb.text = label
	cb.position = Vector2(14, _cursor(parent))
	cb.size = Vector2(220, 24)
	cb.pressed = cur
	cb.toggled.connect(func(v): on_changed(v))
	parent.add_child(cb)

func _anchor_slider(parent: Control, label: String, min_v: float, max_v: float, cur: float, on_changed: Callable) -> void:
	var lbl := Label.new()
	lbl.text = label
	lbl.position = Vector2(14, _cursor(parent))
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", DIM)
	parent.add_child(lbl)

	var sld := HSlider.new()
	sld.position = Vector2(14, _cursor(parent) + 16)
	sld.size = Vector2(200, 24)
	sld.min = min_v
	sld.max = max_v
	sld.value = cur
	sld.value_changed.connect(func(v): on_changed(v))
	parent.add_child(sld)

func _cursor(parent: Control) -> float:
	return (parent.get_child_count() - 1) * 40

func _run_balance() -> void:
	# CSTR material balance: X = k*tau/(1+k*tau), tau = V/Q
	# Assume first-order A->B, k = 0.05 min^-1 at 80C, V = 500 L
	var v_reactor_l = 500.0
	var k_min = 0.05 * exp((_reactor_temp_c - 80.0) / 15.0)  # rough Arrhenius scaling
	var tau_min = v_reactor_l / _feed_rate * 60.0  # L / (L/h) * 60 = min
	var k_tau = k_min * tau_min
	var conversion = k_tau / (1.0 + k_tau)
	var product_kg_h = _feed_rate * conversion * 0.9  # kg/h approx

	_conversion = conversion

	var txt = []
	txt.push("[center][b]Material balance[/b][/center]")
	txt.push("")
	txt.push("Operation: %s" % _process)
	txt.push("Feed rate: %0.1f L/h" % _feed_rate)
	txt.push("Reactor volume: %0.0f L" % v_reactor_l)
	txt.push("Residence time: %0.1f min" % tau_min)
	txt.push("Rate constant k: %0.4f min⁻¹" % k_min)
	txt.push("")
	txt.push("Conversion: %0.1f%%" % (conversion * 100))
	txt.push("Product rate: %0.1f kg/h" % product_kg_h)
	txt.push("GMP compliant: %s" % (_gmp_compliant and "yes" or "no"))

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] CSTR: X = k·τ/(1+k·τ). Longer residence or faster kinetics → higher conversion.")
	why.push("Scale-up: keep τ and k constant; geometry changes heat transfer (surface/volume ratio).")
	why.push("GMP: documented SOPs, batch records, validated cleaning.")
	_why_panel.text = why.join("\n")

	var level = "green" if _gmp_compliant and conversion > 0.5 else "amber"
	_log.append_text("[color=%s]→[/color] Balance: X=%0.1f%%, product %0.1f kg/h, GMP=%s\n" % [level, conversion*100, product_kg_h, (_gmp_compliant and "yes" or "no")])

func _evaluate_safety() -> void:
	var txt = []
	txt.push("[center][b]Safety evaluation[/b][/center]")
	txt.push("")
	txt.push("Reactor temp: %0.0f °C" % _reactor_temp_c)
	txt.push("Pressure: %0.1f bar" % _pressure_bar)
	txt.push("Cooling duty: %0.0f kW" % _cooling_duty)
	txt.push("")
	txt.push("Thermal runaway scenario: %s" % (_runaway_risk and "ACTIVE" or "no"))
	txt.push("Pressure relief valve: %s" % (_relief_valve_open and "OPEN" or "closed"))
	txt.push("Toxic release: %s" % (_toxic_release and "ACTIVE" or "no"))
	txt.push("")
	if _runaway_risk:
		txt.push("CRITICAL: Thermal runaway detected — emergency cooling + quench required.")
	if _pressure_bar > 6.0 and not _relief_valve_open:
		txt.push("WARNING: Overpressure — relief valve must open.")
	if _toxic_release:
		txt.push("CRITICAL: Toxic release — evacuate, scrubber on.")

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] Runaway: heat generation > heat removal → exponential T rise.")
	why.push("Pressure relief: protect vessel at MAEP. Toxic release: scrubber, evacuation, PPE.")
	_why_panel.text = why.join("\n")

	var level = "green"
	if _runaway_risk or _toxic_release:
		level = "red"
	elif _pressure_bar > 6.0 or _reactor_temp_c > 150.0:
		level = "amber"
	_log.append_text("[color=%s]→[/color] Safety: temp %0.0f°C, pressure %0.1f bar, runaway=%s\n" % [level, _reactor_temp_c, _pressure_bar, (_runaway_risk and "YES" or "no")])

func exp(x: float) -> float:
	var result = 1.0
	var term = 1.0
	for i in range(1, 25):
		term *= x / i
		result += term
	return result
