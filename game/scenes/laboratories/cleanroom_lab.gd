# Athanor Ascension — Cleanroom Fabrication Laboratory
# Photolithography, etching, deposition, MEMS, ISO Class 5.
# Failures: particle contamination, wrong dose, humidity, gowning breach.

extends Control

const BG: Color = Color(0.95, 0.97, 1.0, 1.0)
const PANEL: Color = Color(1.0, 1.0, 1.0, 0.9)
const TEXT: Color = Color(0.1, 0.15, 0.2)
const DIM: Color = Color(0.5, 0.55, 0.6)
const CYAN: Color = Color(0.1, 0.6, 0.8)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.36, 0.32)
const GREEN: Color = Color(0.2, 0.7, 0.3)

var _process: String = "photolithography"
var _iso_class: int = 5
var _gowning_complete: bool = true
var _humidity_rh: float = 45.0
var _temp_c: float = 21.0
var _particle_count: float = 100.0  # per m3
var _dose_mj_cm2: float = 25.0
var _resist_thickness_um: float = 1.5
var _defect_density: float = 0.0
var _yield_pct: float = 0.0

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
	title.text = "CLEANROOM FABRICATION  ·  LITHOGRAPHY • ETCH • DEPOSITION • ISO"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Photolithography · particle control · yield · ISO Class 5"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var proc := _panel("Process", Vector2(24, 68), Vector2(560, 300))
	_anchor_dropdown(proc, "Process step", ["photolithography", "etching", "deposition", "metrology"], _process, func(v): _process = v)
	_anchor_dropdown(proc, "ISO class", ["1", "5", "7", "8"], str(_iso_class), func(v): _iso_class = int(v))
	_anchor_checkbox(proc, "Full gowning (bunny suit)", _gowning_complete, func(v): _gowning_complete = v)
	_anchor_slider(proc, "Humidity %RH", 30.0, 60.0, _humidity_rh, func(v): _humidity_rh = v)
	_anchor_slider(proc, "Temperature °C", 18.0, 26.0, _temp_c, func(v): _temp_c = v)
	_anchor_slider(proc, "Dose mJ/cm²", 5.0, 100.0, _dose_mj_cm2, func(v): _dose_mj_cm2 = v)
	var proc_btn := Button.new()
	proc_btn.text = "Run process step"
	proc_btn.position = Vector2(14, 300 - 28)
	proc_btn.size = Vector2(160, 26)
	proc_btn.pressed.connect(func(): _run_process())
	proc.add_child(proc_btn)

	var env := _panel("Environment", Vector2(608, 68), Vector2(560, 260))
	_anchor_slider(env, "Particles per m³ (≥0.5 µm)", 1.0, 10000.0, _particle_count, func(v): _particle_count = v)
	var env_btn := Button.new()
	env_btn.text = "Measure environment"
	env_btn.position = Vector2(14, 260 - 28)
	env_btn.size = Vector2(180, 26)
	env_btn.pressed.connect(func(): _measure_environment())
	env.add_child(env_btn)

	_log := RichTextLabel.new()
	_log.position = Vector2(608, 348)
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

func _run_process() -> void:
	# Yield model: defects scale with particles, humidity deviation, missing gowning
	var iso_factor = {
		"1": 0.01,
		"5": 0.1,
		"7": 1.0,
		"8": 10.0,
	}[str(_iso_class)] or 1.0
	var particle_defects = _particle_count / 1000.0 * iso_factor
	var humidity_dev = abs(_humidity_rh - 45.0) / 15.0
	var temp_dev = abs(_temp_c - 21.0) / 5.0
	var gowning_penalty = 0.0 if _gowning_complete else 0.5

	var defect_density = particle_defects * (1.0 + humidity_dev + temp_dev + gowning_penalty)
	_defect_density = defect_density  # defects/cm²
	# Yield: Poisson, die area ~ 1 cm², yield = exp(-defects * area)
	var yield_pct = exp(-defect_density * 1.0) * 100.0
	_yield_pct = clamp(yield_pct, 0.0, 100.0)

	var txt = []
	txt.push("[center][b]Process step: %s[/b][/center]" % _process)
	txt.push("")
	txt.push("ISO class: %d" % _iso_class)
	txt.push("Gowning: %s" % (_gowning_complete and "complete" or "INCOMPLETE"))
	txt.push("Humidity: %0.1f%% RH (target 45%%)" % _humidity_rh)
	txt.push("Temperature: %0.1f °C (target 21°C)" % _temp_c)
	txt.push("Dose: %0.1f mJ/cm²" % _dose_mj_cm2)
	txt.push("")
	txt.push("Defect density: %0.2f defects/cm²" % _defect_density)
	txt.push("Yield: %0.1f%%" % _yield_pct)
	txt.push("")
	txt.push("Yield = exp(−defects × area), Poisson model")

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] Particles on the wafer → defects → lower yield.")
	why.push("Humidity/temperature off-spec → resist issues, condensation.")
	why.push("Incomplete gowning → human-borne particles.")
	_why_panel.text = why.join("\n")

	var level = "green" if _yield_pct > 90 else ( "amber" if _yield_pct > 70 else "red")
	_log.append_text("[color=%s]→[/color] Process: %s, defects %0.2f/cm², yield %0.1f%%\n" % [level, _process, _defect_density, _yield_pct])

func _measure_environment() -> void:
	var txt = []
	txt.push("[center][b]Environment measurement[/b][/center]")
	txt.push("")
	txt.push("Particles ≥0.5 µm: %0.0f per m³" % _particle_count)
	txt.push("ISO class %d limit: %s" % [_iso_class, _iso_limit(_iso_class)])
	txt.push("Humidity: %0.1f%% RH" % _humidity_rh)
	txt.push("Temperature: %0.1f °C" % _temp_c)
	txt.push("")
	if _particle_count > _iso_limit(_iso_class):
		txt.push("RESULT: Out of specification — cleanroom not at class.")
	else:
		txt.push("RESULT: Within ISO class limits.")

	_readout.text = txt.join("\n")
	_log.append_text("[color=%s]→[/color] Environment: %0.0f particles/m³, ISO %d\n" % [( _particle_count > _iso_limit(_iso_class) and "red" or "green"), _particle_count, _iso_class])

func _iso_limit(cls: int) -> float:
	var limits = {"1": 10.0, "5": 3520.0, "7": 352000.0, "8": 3520000.0}
	return limits[str(cls)] or 3520.0

func clamp(v: float, lo: float, hi: float) -> float:
	return max(lo, min(hi, v))

func exp(x: float) -> float:
	var result = 1.0
	var term = 1.0
	for i in range(1, 25):
		term *= x / i
		result += term
	return result
