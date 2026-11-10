# Athanor Ascension — Cell Culture Laboratory
# Aseptic technique, contamination risk, bioreactor growth curves.
# Failures: aseptic breach, mycoplasma, wrong temperature/pH, overcrowding.

extends Control

const BG: Color = Color(0.03, 0.035, 0.045, 1.0)
const PANEL: Color = Color(0.055, 0.065, 0.075, 0.95)
const TEXT: Color = Color(0.82, 0.88, 0.92)
const DIM: Color = Color(0.5, 0.58, 0.64)
const CYAN: Color = Color(0.4, 0.85, 0.95)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.36, 0.32)
const GREEN: Color = Color(0.42, 0.86, 0.67)

var _aseptic: bool = true
var _biosafety_cabinet: bool = true
var _co2_incubator: bool = true
var _temperature_c: float = 37.0
var _co2_percent: float = 5.0
var _ph: float = 7.4
var _cell_density_ml: float = 1.0e5
var _contamination: bool = false
var _mycoplasma: bool = false
var _time_h: float = 0.0
var _growth_rate_h: float = 0.03  # per hour

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
	title.text = "CELL CULTURE  ·  ASEPTIC TECHNIQUE • BIOREACTOR • CONTAMINATION"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Mammalian cell culture · growth curves · aseptic breaks teach real constraints"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var cult := _panel("Culture conditions", Vector2(24, 68), Vector2(560, 300))
	_anchor_checkbox(cult, "Aseptic technique", _aseptic, func(v): _aseptic = v)
	_anchor_checkbox(cult, "Biosafety cabinet class II", _biosafety_cabinet, func(v): _biosafety_cabinet = v)
	_anchor_checkbox(cult, "CO₂ incubator (37 °C, 5% CO₂)", _co2_incubator, func(v): _co2_incubator = v)
	_anchor_slider(cult, "Temperature °C", 20.0, 45.0, _temperature_c, func(v): _temperature_c = v)
	_anchor_slider(cult, "CO₂ %", 0.0, 10.0, _co2_percent, func(v): _co2_percent = v)
	_anchor_slider(cult, "pH", 6.5, 8.0, _ph, func(v): _ph = v)
	_anchor_slider(cult, "Initial density cells/mL", 1.0e4, 1.0e6, _cell_density_ml, func(v): _cell_density_ml = v)
	var cult_btn := Button.new()
	cult_btn.text = "Simulate 48 h culture"
	cult_btn.position = Vector2(14, 300 - 28)
	cult_btn.size = Vector2(200, 26)
	cult_btn.pressed.connect(func(): _simulate_culture())
	cult.add_child(cult_btn)

	var cont := _panel("Contamination controls", Vector2(608, 68), Vector2(560, 220))
	_anchor_checkbox(cont, "Simulate contamination event", _contamination, func(v): _contamination = v)
	_anchor_checkbox(cont, "Mycoplasma check", _mycoplasma, func(v): _mycoplasma = v)
	var cont_btn := Button.new()
	cont_btn.text = "Run contamination test"
	cont_btn.position = Vector2(14, 220 - 28)
	cont_btn.size = Vector2(200, 26)
	cont_btn.pressed.connect(func(): _test_contamination())
	cont.add_child(cont_btn)

	_log := RichTextLabel.new()
	_log.position = Vector2(608, 308)
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

func _anchor_checkbox(parent: Control, label: String, cur: bool, on_changed: Callable) -> void:
	var cb := CheckButton.new()
	cb.text = label
	cb.position = Vector2(14, _panel_cursor(parent))
	cb.size = Vector2(220, 24)
	cb.pressed = cur
	cb.toggled.connect(func(v): on_changed(v))
	parent.add_child(cb)

func _anchor_slider(parent: Control, label: String, min_v: float, max_v: float, cur: float, on_changed: Callable) -> void:
	var lbl := Label.new()
	lbl.text = label
	lbl.position = Vector2(14, _panel_cursor(parent))
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", DIM)
	parent.add_child(lbl)

	var sld := HSlider.new()
	sld.position = Vector2(14, _panel_cursor(parent) + 16)
	sld.size = Vector2(200, 24)
	sld.min = min_v
	sld.max = max_v
	sld.value = cur
	sld.value_changed.connect(func(v): on_changed(v))
	parent.add_child(sld)

func _panel_cursor(parent: Control) -> float:
	return (parent.get_child_count() - 1) * 40

func _refresh_all() -> void:
	# Growth: dN/dt = mu*N, mu depends on temp/pH/CO2
	var mu_opt = 0.03  # /h at 37°C, 5% CO2, pH 7.4
	var temp_factor = 1.0 - abs(_temperature_c - 37.0) / 15.0
	var co2_factor = 1.0 - abs(_co2_percent - 5.0) / 5.0
	var ph_factor = 1.0 - abs(_ph - 7.4) / 1.0
	temp_factor = clamp(temp_factor, 0.0, 1.0)
	co2_factor = clamp(co2_factor, 0.0, 1.0)
	ph_factor = clamp(ph_factor, 0.0, 1.0)
	var mu = mu_opt * temp_factor * co2_factor * ph_factor
	if not _co2_incubator or not _biosafety_cabinet:
		mu *= 0.3  # poor conditions

	var t = 48.0
	var n_final = _cell_density_ml * exp(mu * t)

	var txt = []
	txt.push("[center][b]Culture after 48 h[/b][/center]")
	txt.push("")
	txt.push("µ = %0.4f /h (optimum %0.4f)" % [mu, mu_opt])
	txt.push("Temperature factor: %0.2f" % temp_factor)
	txt.push("CO₂ factor: %0.2f" % co2_factor)
	txt.push("pH factor: %0.2f" % ph_factor)
	txt.push("")
	txt.push("N₀ = %0.1e cells/mL" % _cell_density_ml)
	txt.push("N(48h) = %0.1e cells/mL" % n_final)
	txt.push("")
	txt.push("Conditions: %s" % [(_aseptic and _biosafety_cabinet and _co2_incubator) and "aseptic" or "COMPROMISED"])

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] Mammalian cells need 37 °C, 5 % CO₂, pH 7.4.")
	why.push("Deviations slow growth; contamination can overgrow the culture.")
	why.push("Always work in a biosafety cabinet with aseptic technique.")
	_why_panel.text = why.join("\n")

	if not _aseptic or not _biosafety_cabinet:
		_log.append_text("[color=red]✗[/color] Aseptic break — culture at risk of contamination\n")
	elif mu < 0.01:
		_log.append_text("[color=yellow]⚠[/color] Suboptimal conditions — slow growth\n")
	else:
		_log.append_text("[color=green]✓[/color] Healthy culture, µ = %0.4f /h\n" % mu)

func _simulate_culture() -> void:
	_refresh_all()
	_log.append_text("[color=cyan]→[/color] Simulated 48 h culture at %0.1f °C, %0.1f%% CO₂, pH %0.2f\n" % [_temperature_c, _co2_percent, _ph])

func _test_contamination() -> void:
	var risk = 0.0
	if not _aseptic:
		risk += 0.6
	if not _biosafety_cabinet:
		risk += 0.3
	if _mycoplasma:
		risk += 0.4
	if _contamination:
		risk += 0.5
	risk = clamp(risk, 0.0, 1.0)

	var txt = []
	txt.push("[center][b]Contamination test[/b][/center]")
	txt.push("")
	txt.push("Contamination risk: %0.0f%%" % (risk * 100.0))
	txt.push("Aseptic: %s" % (_aseptic and "yes" or "no"))
	txt.push("BSC: %s" % (_biosafety_cabinet and "yes" or "no"))
	txt.push("Mycoplasma: %s" % (_mycoplasma and "yes" or "no"))
	txt.push("")
	if risk > 0.5:
		txt.push("RESULT: Contamination detected — culture lost.")
	elif risk > 0.2:
		txt.push("RESULT: Warning — low-level contamination possible.")
	else:
		txt.push("RESULT: Culture clean.")

	_readout.text = txt.join("\n")
	_why_panel.text = "[b]Why:[/b] Contamination risk rises with aseptic breaks, missing BSC, and mycoplasma."
	_log.append_text("[color=%s]→[/color] Contamination test: risk %0.0f%%\n" % [(risk > 0.5 and "red" or (risk > 0.2 and "yellow" or "green")), risk * 100.0])

func clamp(v: float, lo: float, hi: float) -> float:
	return max(lo, min(hi, v))

func exp(x: float) -> float:
	# simple series for e^x
	var result = 1.0
	var term = 1.0
	for i in range(1, 20):
		term *= x / i
		result += term
	return result
