# Athanor Ascension — Radiochemistry Hot Cell
# Radioisotope production, shielding, dose monitoring, remote manipulators.
# Failures: shielding breach, contamination, criticality, dose limit exceeded.

extends Control

const BG: Color = Color(0.04, 0.02, 0.02, 1.0)
const PANEL: Color = Color(0.07, 0.04, 0.04, 0.95)
const TEXT: Color = Color(0.9, 0.8, 0.8)
const DIM: Color = Color(0.6, 0.5, 0.5)
const CYAN: Color = Color(0.6, 0.9, 1.0)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.3, 0.3)
const GREEN: Color = Color(0.6, 0.9, 0.6)

# Isotope data: half-life (h), dose rate factor (mSv/h per MBq at 1 cm), gamma energy (MeV)
const ISOTOPES: Dictionary = {
	"F-18": {"half_life_h": 1.83, "dose_factor": 0.00057, "gamma": 0.511},
	"Tc-99m": {"half_life_h": 6.01, "dose_factor": 0.00078, "gamma": 0.140},
	"I-131": {"half_life_h": 192.0, "dose_factor": 0.0023, "gamma": 0.364},
	"Mo-99": {"half_life_h": 65.94, "dose_factor": 0.0012, "gamma": 0.740},
	"Co-60": {"half_life_h": 1321.0, "dose_factor": 0.0036, "gamma": 1.25},
}

var _isotope: String = "F-18"
var _activity_mbq: float = 100.0
var _elapsed_h: float = 0.0
var _shield_cm: float = 5.0  # lead equivalent
var _distance_cm: float = 30.0
var _dose_rate_usv_h: float = 0.0
var _cumulative_dose_usv: float = 0.0
var _shielding_breach: bool = false
var _contamination: bool = false

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
	title.text = "RADIOCHEMISTRY HOT CELL  ·  ISOTOPES • SHIELDING • DOSE"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Radioisotope production · inverse-square law · shielding · real dose limits"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var iso := _panel("Isotope & activity", Vector2(24, 68), Vector2(560, 260))
	_anchor_dropdown(iso, "Isotope", ["F-18", "Tc-99m", "I-131", "Mo-99", "Co-60"], _isotope, func(v): _isotope = v)
	_anchor_slider(iso, "Activity MBq", 1.0, 1000.0, _activity_mbq, func(v): _activity_mbq = v)
	_anchor_slider(iso, "Decay time h", 0.0, 72.0, _elapsed_h, func(v): _elapsed_h = v)

	var sh := _panel("Shielding & distance", Vector2(24, 348), Vector2(560, 260))
	_anchor_slider(sh, "Lead shield cm", 0.0, 20.0, _shield_cm, func(v): _shield_cm = v)
	_anchor_slider(sh, "Distance cm", 10.0, 200.0, _distance_cm, func(v): _distance_cm = v)
	_anchor_checkbox(sh, "Shielding breach", _shielding_breach, func(v): _shielding_breach = v)
	_anchor_checkbox(sh, "Contamination", _contamination, func(v): _contamination = v)

	var calc_btn := Button.new()
	calc_btn.text = "Calculate dose"
	calc_btn.position = Vector2(24, 628 - 28)
	calc_btn.size = Vector2(150, 26)
	calc_btn.pressed.connect(func(): _calc_dose())
	add_child(calc_btn)

	_log := RichTextLabel.new()
	_log.position = Vector2(608, 68)
	_log.size = Vector2(560, 300)
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
	cb.size = Vector2(200, 24)
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

func _calc_dose() -> void:
	var iso = ISOTOPES[_isotope]
	var half_life = iso["half_life_h"]
	var activity_now = _activity_mbq * pow(0.5, _elapsed_h / half_life)

	# Dose rate: Gamma constant ~ dose_factor * activity / r^2 (r in m), attenuation through shield
	var r_m = _distance_cm / 100.0
	var unshielded = iso["dose_factor"] * activity_now / (r_m * r_m)  # mSv/h approx
	# Lead attenuation: I = I0 * exp(-mu * x), mu ~ 1.23 /cm for typical gamma at Pb
	var attenuation = exp(-1.23 * _shield_cm)
	var dose_rate = unshielded * attenuation
	if _shielding_breach:
		dose_rate *= 10.0
	if _contamination:
		dose_rate *= 2.0

	var cum = dose_rate * (_elapsed_h / 24.0)  # rough cumulative for a work day

	_dose_rate_usv_h = dose_rate * 1000.0  # to µSv/h
	_cumulative_dose_usv = cum * 1000.0

	var txt = []
	txt.push("[center][b]Dose assessment[/b][/center]")
	txt.push("")
	txt.push("Isotope: %s (T½ = %0.2f h)" % [_isotope, half_life])
	txt.push("Activity now: %0.1f MBq (decayed for %0.1f h)" % [activity_now, _elapsed_h])
	txt.push("Distance: %0.1f m" % r_m)
	txt.push("Lead shield: %0.1f cm (attenuation %0.0f%%)" % [_shield_cm, (1.0 - attenuation) * 100])
	txt.push("")
	txt.push("Dose rate: %0.1f µSv/h" % (_dose_rate_usv_h))
	txt.push("Cumulative (8 h day): %0.1f µSv" % _cumulative_dose_usv)
	txt.push("")
	txt.push("Annual limit (worker): 20,000 µSv")
	txt.push("Public limit: 1,000 µSv/year")

	_readout.text = txt.join("\n")

	var why = []
	why.push("[b]Why:[/b] Dose falls with 1/r² and shield attenuation (exponential in Pb).")
	why.push("Contamination and shielding breaches multiply dose.")
	why.push("Keep time short, distance large, shielding thick — ALARA.")
	_why_panel.text = why.join("\n")

	var level = "green"
	if _dose_rate_usv_h > 100:
		level = "red"
	elif _dose_rate_usv_h > 20:
		level = "amber"
	_log.append_text("[color=%s]→[/color] Dose: %0.1f µSv/h at %0.1f m, %0.1f cm Pb\n" % [level, _dose_rate_usv_h, r_m, _shield_cm])

func _pitting_risk() -> bool:
	# placeholder for compatibility with UI pattern
	return false

func exp(x: float) -> float:
	var result = 1.0
	var term = 1.0
	for i in range(1, 25):
		term *= x / i
		result += term
	return result
