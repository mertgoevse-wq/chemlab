# Athanor Ascension — Cryogenic & Vacuum Laboratory
# Liquid helium, dilution refrigerators, superconductivity, quantum computing, UHV.
# Failures: cryogenic burns, asphyxiation, pressure vessels, quench.

extends Control

const BG: Color = Color(0.02, 0.04, 0.08, 1.0)
const PANEL: Color = Color(0.06, 0.08, 0.12, 0.95)
const TEXT: Color = Color(0.8, 0.95, 1.0)
const DIM: Color = Color(0.5, 0.6, 0.7)
const CYAN: Color = Color(0.4, 0.9, 1.0)
const AMBER: Color = Color(1.0, 0.75, 0.3)
const RED: Color = Color(1.0, 0.35, 0.35)
const GREEN: Color = Color(0.5, 0.85, 0.5)

var _system: String = "dilution_refrigerator"
var _base_temp_mk: float = 10.0  # millikelvin
var _liquid_helium_l: float = 50.0
var _pressure_mbar: float = 1e-6  # UHV
var _quench_risk: bool = false
var _oxygen_monitor: bool = true
var _asphyxiation_risk: bool = false
var _cooling_power_w: float = 1.0  # at base temp

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
	title.text = "CRYOGENIC & VACUUM  ·  DILUTION FRIDGE • UHV • SUPERCONDUCTIVITY"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Liquid helium · dilution refrigerator · UHV · quench protection"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var sys := _panel("Cryogenic system", Vector2(24, 68), Vector2(560, 300))
	_anchor_dropdown(sys, "System", ["dilution_refrigerator", "liquid_helium", "uhv_chamber", "superconducting_magnet"], _system, func(v): _system = v)
	_anchor_slider(sys, "Base temperature mK", 1.0, 100.0, _base_temp_mk, func(v): _base_temp_mk = v)
	_anchor_slider(sys, "Liquid helium L", 1.0, 200.0, _liquid_helium_l, func(v): _liquid_helium_l = v)
	_anchor_slider(sys, "Cooling power µW", 0.1, 100.0, _cooling_power_w * 1e6, func(v): _cooling_power_w = v / 1e6)
	var sys_btn := Button.new()
	sys_btn.text = "Calculate hold time"
	sys_btn.position = Vector2(14, 300 - 28)
	sys_btn.size = Vector2(160, 26)
	sys_btn.pressed.connect(func(): _calc_hold_time())
	sys.add_child(sys_btn)

	var vac := _panel("Vacuum & safety", Vector2(608, 68), Vector2(560, 280))
	_anchor_slider(vac, "Pressure mbar", 1e-10, 1.0, _pressure_mbar, func(v): _pressure_mbar = v)
	_anchor_checkbox(vac, "Quench risk", _quench_risk, func(v): _quench_risk = v)
	_anchor_checkbox(vac, "Oxygen monitor active", _oxygen_monitor, func(v): _oxygen_monitor = v)
	_anchor_checkbox(vac, "Asphyxiation risk", _asphyxiation_risk, func(v): _asphyxiation_risk = v)
	var vac_btn := Button.new()
	vac_btn.text = "Evaluate safety"
	vac_btn.position = Vector2(14, 280 - 28)
	vac_btn.size = Vector2(160, 26)
	vac_btn.pressed.connect(func(): _evaluate_safety())
	vac.add_child(vac_btn)

	_log := RichTextLabel.new()
	_log.position = Vector2(608, 368)
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

func _calc_hold_time() -> void:
	# Hold time = liquid inventory / boil-off rate. Boil-off depends on cooling power & temp.
	var boil_off_w = _cooling_power_w + 2.0  # parasitic + cooling
	var inventory_j = _liquid_helium_l * 1000.0 * 4.6  # J (density ~0.125 kg/L, L_vap ~ 20 kJ/kg → ~2.5 kJ/L, use 4.6 for safety margin)
	var hold_s = inventory_j / boil_off_w
	var hold_h = hold_s / 3600.0

	var txt = []
	txt.push("[center][b]Cryogenic system[/b][/center]")
	txt.push("")
	txt.push("System: %s" % _system)
	txt.push("Base temperature: %0.1f mK" % _base_temp_mk)
	txt.push("Liquid helium: %0.1f L" % _liquid_helium_l)
	txt.push("Cooling power: %0.1f µW at base temp" % (_cooling_power_w * 1e6))
	txt.push("")
	txt.push("Estimated boil-off: %0.2f W" % boil_off_w)
	txt.push("Hold time: %0.1f h (%0.1f days)" % [hold_h, hold_h / 24.0])

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] Hold time = inventory / boil-off rate. Lower base temp → higher boil-off.")
	why.push("Liquid helium boil-off cools the cold head; dilution fridge needs continuous He-3/He-4 circulation.")
	why.push("UHV (≤1e-6 mbar) needed for surface science, quantum devices.")
	_why_panel.text = why.join("\n")

	var level = "green" if hold_h > 24 else ( "amber" if hold_h > 4 else "red")
	_log.append_text("[color=%s]→[/color] Cryo: %s, base %0.1f mK, hold %0.1f h\n" % [level, _system, _base_temp_mk, hold_h])

func _evaluate_safety() -> void:
	var txt = []
	txt.push("[center][b]Cryogenic safety[/b][/center]")
	txt.push("")
	txt.push("Pressure: %0.2e mbar" % _pressure_mbar)
	txt.push("Quench risk: %s" % (_quench_risk and "ELEVATED" or "nominal"))
	txt.push("Oxygen monitor: %s" % (_oxygen_monitor and "active" or "OFF"))
	txt.push("Asphyxiation risk: %s" % (_asphyxiation_risk and "yes" or "no"))
	txt.push("")
	if _quench_risk:
		txt.push("CRITICAL: Quench — rapid He boil-off, pressure rise, possible asphyxiation.")
	if _pressure_mbar > 1e-3:
		txt.push("WARNING: Not UHV — surface contamination likely.")
	if not _oxygen_monitor:
		txt.push("WARNING: No O2 monitor — He boil-off can displace oxygen.")
	if _asphyxiation_risk:
		txt.push("CRITICAL: Asphyxiation — evacuate, ventilate.")

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] He boil-off displaces oxygen → asphyxiation in confined spaces.")
	why.push("Quench: superconducting magnet loses superconductivity, massive He release.")
	why.push("UHV: required to avoid surface contamination and mean free path issues.")
	_why_panel.text = why.join("\n")

	var level = "green"
	if _quench_risk or _asphyxiation_risk:
		level = "red"
	elif _pressure_mbar > 1e-3 or not _oxygen_monitor:
		level = "amber"
	_log.append_text("[color=%s]→[/color] Safety: pressure %0.2e mbar, quench=%s, asphyxiation=%s\n" % [level, _pressure_mbar, (_quench_risk and "YES" or "no"), (_asphyxiation_risk and "YES" or "no")])
