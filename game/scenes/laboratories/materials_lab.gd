# Athanor Ascension — Materials & Metallurgy Laboratory
# Sintering, annealing, XRD, SEM, thin films, battery materials, catalysts.
# Failures: wrong temperature profile, contamination, vacuum leaks.

extends Control

const BG: Color = Color(0.03, 0.035, 0.045, 1.0)
const PANEL: Color = Color(0.055, 0.065, 0.075, 0.95)
const TEXT: Color = Color(0.82, 0.88, 0.92)
const DIM: Color = Color(0.5, 0.58, 0.64)
const CYAN: Color = Color(0.4, 0.85, 0.95)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.36, 0.32)
const GREEN: Color = Color(0.42, 0.86, 0.67)

var _process: String = "sintering"
var _temperature_c: float = 800.0
var _time_h: float = 2.0
var _atmosphere: String = "air"
var _vacuum_mbar: float = 1000.0
var _contamination: bool = false
var _grain_size_um: float = 0.0
var _phase_purity: float = 0.0
var _hardness_hv: float = 0.0

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
	title.text = "MATERIALS & METALLURGY  ·  SINTERING • ANNEALING • XRD • SEM"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Heat treatments · microstructure · phase purity · hardness"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var proc := _panel("Process parameters", Vector2(24, 68), Vector2(560, 280))
	_anchor_dropdown(proc, "Process", ["sintering", "annealing", "calcination"], _process, func(v): _process = v)
	_anchor_slider(proc, "Temperature °C", 200.0, 1600.0, _temperature_c, func(v): _temperature_c = v)
	_anchor_slider(proc, "Time h", 0.5, 24.0, _time_h, func(v): _time_h = v)
	_anchor_dropdown(proc, "Atmosphere", ["air", "argon", "nitrogen", "vacuum", "hydrogen"], _atmosphere, func(v): _atmosphere = v)
	_anchor_checkbox(proc, "Contamination", _contamination, func(v): _contamination = v)

	var run_btn := Button.new()
	run_btn.text = "Run heat treatment"
	run_btn.position = Vector2(24, 280 - 28)
	run_btn.size = Vector2(180, 26)
	run_btn.pressed.connect(func(): _run_treatment())
	proc.add_child(run_btn)

	var vac := _panel("Vacuum & analysis", Vector2(608, 68), Vector2(560, 280))
	_anchor_slider(vac, "Pressure mbar", 1e-6, 1000.0, _vacuum_mbar, func(v): _vacuum_mbar = v)
	var analyze_btn := Button.new()
	analyze_btn.text = "Analyze microstructure"
	analyze_btn.position = Vector2(14, 280 - 28)
	analyze_btn.size = Vector2(180, 26)
	analyze_btn.pressed.connect(func(): _analyze_microstructure())
	vac.add_child(analyze_btn)

	_log = RichTextLabel.new()
	_log.position = Vector2(608, 368)
	_log.size = Vector2(560, 220)
	_log.add_theme_color_override("font_color", TEXT)
	add_child(_log)

	_readout = RichTextLabel.new()
	_readout.position = Vector2(1192, 68)
	_readout.size = Vector2(420, 540)
	_readout.add_theme_color_override("font_color", TEXT)
	add_child(_readout)

	_why_panel = RichTextLabel.new()
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
	opt.item_selected.connect(func(idx): on_changed.call(opt.get_item_text(idx)))
	parent.add_child(opt)

func _anchor_checkbox(parent: Control, label: String, cur: bool, on_changed: Callable) -> void:
	var cb := CheckButton.new()
	cb.text = label
	cb.position = Vector2(14, _cursor(parent))
	cb.size = Vector2(200, 24)
	cb.button_pressed = cur
	cb.toggled.connect(func(v): on_changed.call(v))
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
	sld.min_value = min_v
	sld.max_value = max_v
	sld.value = cur
	sld.value_changed.connect(func(v): on_changed.call(v))
	parent.add_child(sld)

func _cursor(parent: Control) -> float:
	return (parent.get_child_count() - 1) * 40

func _refresh_all() -> void:
	_run_treatment()

func _run_treatment() -> void:
	# Sintering/annealing model: grain growth d^n - d0^n = k*t*exp(-Q/RT)
	var t_k = _temperature_c + 273.15
	var q_j = 200000.0  # activation energy J/mol
	var r = 8.314
	var k = 1e-5  # m^n/s pre-exponential
	var n = 2.0  # grain growth exponent
	var d0_um = 1.0  # initial grain size um
	var rate = k * _time_h * 3600.0 * exp(-q_j / (r * t_k))
	var d_um = pow(pow(d0_um, n) + rate, 1.0 / n)

	# Phase purity depends on atmosphere and contamination
	var purity = 1.0
	if _contamination:
		purity *= 0.7
	if _atmosphere == "air" and _process in ["annealing", "sintering"]:
		purity *= 0.85  # oxidation
	if _temperature_c > 1200.0 and _atmosphere != "vacuum" and _atmosphere != "argon":
		purity *= 0.9

	_grain_size_um = d_um
	_phase_purity = purity
	_hardness_hv = 100.0 + 50.0 * (1.0 - _grain_size_um / 50.0)  # Hall-Petch-ish
	_hardness_hv = clampf(_hardness_hv, 10.0, 500.0)

	var txt: PackedStringArray = []
	txt.append("[center][b]Heat treatment result[/b][/center]")
	txt.append("")
	txt.append("Process: %s" % _process)
	txt.append("T = %0.0f °C, t = %0.1f h, atmosphere = %s" % [_temperature_c, _time_h, _atmosphere])
	txt.append("")
	txt.append("Grain size: %0.2f µm" % _grain_size_um)
	txt.append("Phase purity: %0.0f%%" % (_phase_purity * 100))
	txt.append("Hardness: %0.1f HV" % _hardness_hv)
	txt.append("")
	txt.append("Grain growth: dⁿ − d₀ⁿ = k·t·exp(−Q/RT)")

	_readout.text = "\n".join(txt)

	var why: PackedStringArray = []
	why.append("[b]Why:[/b] Higher T and longer t → grain growth (Hall–Petch: finer grains = harder).")
	why.append("Wrong atmosphere → oxidation/impurities → lower phase purity.")
	why.append("Contamination → second phases, inclusions.")
	_why_panel.text = "\n".join(why)

	var level = "green" if _phase_purity > 0.9 and not _contamination else "amber"
	_log.append_text("[color=%s]→[/color] Treatment: %s, grain %0.2f µm, purity %0.0f%%\n" % [level, _process, _grain_size_um, _phase_purity * 100])

func _analyze_microstructure() -> void:
	var txt: PackedStringArray = []
	txt.append("[center][b]Microstructure analysis[/b][/center]")
	txt.append("")
	txt.append("Vacuum: %0.2e mbar" % _vacuum_mbar)
	txt.append("Grain size: %0.2f µm" % _grain_size_um)
	txt.append("Phase purity: %0.0f%%" % (_phase_purity * 100))
	txt.append("")
	if _vacuum_mbar > 1.0 and _process == "sintering":
		txt.append("WARNING: Pressure too high for clean sintering — oxidation likely.")
	elif _vacuum_mbar < 1e-3:
		txt.append("UHV reached — clean surface, good for thin films.")
	else:
		txt.append("Pressure adequate for bulk heat treatment.")
	txt.append("")
	txt.append("XRD would show: %s" % (_phase_purity > 0.95 and "single phase" or "mixed phases + impurities"))

	_readout.text = "\n".join(txt)
	_log.append_text("[color=cyan]→[/color] Microstructure: %0.2f µm grains, %0.0f%% purity, %0.2e mbar\n" % [_grain_size_um, _phase_purity * 100, _vacuum_mbar])

func exp(x: float) -> float:
	var result = 1.0
	var term = 1.0
	for i in range(1, 25):
		term *= x / i
		result += term
	return result
