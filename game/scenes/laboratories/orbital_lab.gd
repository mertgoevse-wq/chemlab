# Athanor Ascension — Orbital Microgravity Laboratory
# Protein crystallization, fluid dynamics, combustion, materials science in microgravity.
# Failures: microgravity convection loss, radiation dose, launch loads, orbital debris.

extends Control

const BG: Color = Color(0.02, 0.03, 0.06, 1.0)
const PANEL: Color = Color(0.06, 0.07, 0.09, 0.95)
const TEXT: Color = Color(0.8, 0.9, 1.0)
const DIM: Color = Color(0.5, 0.6, 0.7)
const CYAN: Color = Color(0.4, 0.8, 1.0)
const AMBER: Color = Color(1.0, 0.75, 0.3)
const RED: Color = Color(1.0, 0.35, 0.35)
const GREEN: Color = Color(0.5, 0.85, 0.5)

var _experiment: String = "protein_crystallization"
var _g_level: float = 0.0  # g, microgravity ~0
var _temperature_c: float = 22.0
var _radiation_mSv_h: float = 0.5
var _mission_duration_h: float = 72.0
var _crystal_quality: float = 0.0
var _convection: bool = false  # convection active = not microgravity
var _debris_risk: bool = false

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
	title.text = "ORBITAL MICROGRAVITY  ·  CRYSTALS • FLUIDS • RADIATION"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Protein crystallization · buoyancy-driven convection · radiation dose"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var exp := _panel("Experiment", Vector2(24, 68), Vector2(560, 280))
	_anchor_dropdown(exp, "Experiment", ["protein_crystallization", "fluid_dynamics", "combustion", "materials_science"], _experiment, func(v): _experiment = v)
	_anchor_slider(exp, "Gravity level g", 0.0, 2.0, _g_level, func(v): _g_level = v)
	_anchor_slider(exp, "Temperature °C", 15.0, 35.0, _temperature_c, func(v): _temperature_c = v)
	_anchor_slider(exp, "Mission duration h", 1.0, 720.0, _mission_duration_h, func(v): _mission_duration_h = v)
	var run_btn := Button.new()
	run_btn.text = "Run experiment"
	run_btn.position = Vector2(14, 280 - 28)
	run_btn.size = Vector2(150, 26)
	run_btn.pressed.connect(func(): _run_experiment())
	exp.add_child(run_btn)

	var env := _panel("Orbital environment", Vector2(608, 68), Vector2(560, 280))
	_anchor_slider(env, "Radiation mSv/h", 0.1, 5.0, _radiation_mSv_h, func(v): _radiation_mSv_h = v)
	_anchor_checkbox(env, "Convection active (1 g)", _convection, func(v): _convection = v)
	_anchor_checkbox(env, "Orbital debris risk", _debris_risk, func(v): _debris_risk = v)
	var env_btn := Button.new()
	env_btn.text = "Assess environment"
	env_btn.position = Vector2(14, 280 - 28)
	env_btn.size = Vector2(180, 26)
	env_btn.pressed.connect(func(): _assess_environment())
	env.add_child(env_btn)

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
	cb.size = Vector2(220, 24)
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
	_run_experiment()

func _run_experiment() -> void:
	# Microgravity: no buoyancy-driven convection → diffusion-only growth → larger crystals
	var is_microg = _g_level < 0.01
	var base_quality = 0.5
	if _experiment == "protein_crystallization":
		base_quality = 0.6
	elif _experiment == "fluid_dynamics":
		base_quality = 0.4
	elif _experiment == "combustion":
		base_quality = 0.3
	else:
		base_quality = 0.5

	# Microgravity improves crystal quality (diffusion-limited growth)
	var quality = base_quality
	if is_microg:
		quality *= 1.5
	if _temperature_c > 30.0 or _temperature_c < 15.0:
		quality *= 0.8
	quality = clampf(quality, 0.0, 1.0)
	_crystal_quality = quality

	var txt: PackedStringArray = []
	txt.append("[center][b]Orbital experiment result[/b][/center]")
	txt.append("")
	txt.append("Experiment: %s" % _experiment)
	txt.append("Gravity: %0.2f g (%s)" % [_g_level, (is_microg and "microgravity" or "Earth-normal")])
	txt.append("Temperature: %0.1f °C" % _temperature_c)
	txt.append("Duration: %0.0f h" % _mission_duration_h)
	txt.append("")
	txt.append("Crystal quality: %0.0f%%" % (quality * 100))
	txt.append("Convection: %s" % (_convection and "active (buoyancy-driven)" or "suppressed (diffusion-only)"))
	txt.append("")
	txt.append("In microgravity: no sedimentation, diffusion-limited growth → larger, better-ordered crystals.")

	_readout.text = "\n".join(txt)

	var why: PackedStringArray = []
	why.append("[b]Why:[/b] On Earth, buoyancy-driven convection disturbs crystal growth.")
	why.append("In orbit, diffusion dominates → larger, better-ordered protein crystals.")
	why.append("Radiation accumulates over mission duration — dose limits apply.")
	_why_panel.text = "\n".join(why)

	var level = "green" if quality > 0.7 else ( "amber" if quality > 0.4 else "red")
	_log.append_text("[color=%s]→[/color] Experiment: %s, quality %0.0f%%, gravity %0.2f g\n" % [level, _experiment, quality * 100, _g_level])

func _assess_environment() -> void:
	var dose = _radiation_mSv_h * _mission_duration_h
	var txt: PackedStringArray = []
	txt.append("[center][b]Orbital environment[/b][/center]")
	txt.append("")
	txt.append("Radiation: %0.2f mSv/h" % _radiation_mSv_h)
	txt.append("Cumulative dose (%0.0f h): %0.1f mSv" % [_mission_duration_h, dose])
	txt.append("Convection: %s" % (_convection and "active" or "suppressed"))
	txt.append("Debris risk: %s" % (_debris_risk and "elevated" or "nominal"))
	txt.append("")
	txt.append("NASA career limit: ~1000 mSv (varies by age/sex)")
	txt.append("ISS typical: ~0.5–1 mSv/day")

	_readout.text = "\n".join(txt)

	var why: PackedStringArray = []
	why.append("[b]Why:[/b] Orbital radiation (GCR, SPEs) accumulates over time.")
	why.append("Microgravity removes convection → phenomena only observable in orbit.")
	why.append("Debris: impact risk to module and experiments.")
	_why_panel.text = "\n".join(why)

	var level = "green" if dose < 100 else ( "amber" if dose < 500 else "red")
	_log.append_text("[color=%s]→[/color] Environment: dose %0.1f mSv over mission, debris %s\n" % [level, dose, (_debris_risk and "elevated" or "nominal")])
