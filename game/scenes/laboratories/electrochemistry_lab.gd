# Athanor Ascension — Electrochemistry Laboratory
# Interactive build + live discharge model: galvanic cells, electrolysis,
# Faraday's laws, and corrosion. Failures are named after real phenomena
# (Nernst equation, hydrogen evolution, pitting corrosion).
#
# Learning loop: build -> understand why -> energise -> diagnose.

extends Control

const BG: Color = Color(0.03, 0.035, 0.045, 1.0)
const PANEL: Color = Color(0.055, 0.065, 0.075, 0.95)
const TEXT: Color = Color(0.82, 0.88, 0.92)
const DIM: Color = Color(0.5, 0.58, 0.64)
const CYAN: Color = Color(0.4, 0.85, 0.95)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.36, 0.32)
const GREEN: Color = Color(0.42, 0.86, 0.67)

# Standard electrode potentials (V vs SHE, 25 °C)
const E_STD: Dictionary = {
	"Zn": -0.763,
	"Cu": 0.340,
	"Ag": 0.7996,
	"Fe": -0.440,
	"Pb": -0.126,
	"Ni": -0.257,
	"Sn": -0.136,
	"H2": 0.000,
}

const F: float = 96485.33212   # Faraday constant C/mol
const R: float = 8.314462618  # gas constant J/(mol·K)
const T: float = 298.15       # K

var _anode_material: String = "Zn"
var _cathode_material: String = "Cu"
var _anode_conc_m: float = 1.0
var _cathode_conc_m: float = 1.0
var _load_ohm: float = 10.0
var _internal_r_ohm: float = 0.5
var _temperature_c: float = 25.0

var _electrolysis_on: bool = false
var _electrolysis_current_a: float = 0.5
var _electrolysis_time_s: float = 0.0
var _electrolysis_target: String = "Cu2+"

var _corrosion_on: bool = false
var _corrosion_metal: String = "Fe"
var _corrosion_env: String = "seawater"
var _corrosion_chloride_m: float = 0.6

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
	title.text = "ELECTROCHEMISTRY  ·  GALVANIC CELLS • ELECTROLYSIS • CORROSION"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Nernst equation · Faraday's laws · mixed-potential corrosion · real numbers, no CGI"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	# ---- Galvanic cell panel ----
	var galv := _panel("Galvanic Cell (Voltaic)", Vector2(24, 68), Vector2(560, 300))
	_anchor_dropdown(galv, "Anode material", ["Zn", "Cu", "Ag", "Fe", "Pb", "Ni", "Sn"], _anode_material, func(v): _anode_material = v)
	_anchor_dropdown(galv, "Cathode material", ["Cu", "Ag", "Zn", "Fe", "Pb", "Ni", "Sn"], _cathode_material, func(v): _cathode_material = v)
	_anchor_slider(galv, "Anode [ion] M", 0.01, 10.0, _anode_conc_m, func(v): _anode_conc_m = v)
	_anchor_slider(galv, "Cathode [ion] M", 0.01, 10.0, _cathode_conc_m, func(v): _cathode_conc_m = v)
	_anchor_slider(galv, "Load resistance Ω", 0.1, 100.0, _load_ohm, func(v): _load_ohm = v)
	_anchor_slider(galv, "Temperature °C", 0.0, 100.0, _temperature_c, func(v): _temperature_c = v)

	var galvanic_btn := Button.new()
	galvanic_btn.text = "Recalculate cell"
	galvanic_btn.position = Vector2(34, 300 - 28)
	galvanic_btn.size = Vector2(150, 26)
	galvanic_btn.pressed.connect(func(): _refresh_all())
	galv.add_child(galvanic_btn)

	# ---- Electrolysis panel ----
	var elec := _panel("Electrolysis (Faraday)", Vector2(608, 68), Vector2(560, 300))
	_anchor_dropdown(elec, "Target species", ["Cu2+", "H2O", "NaCl"], _electrolysis_target, func(v): _electrolysis_target = v)
	_anchor_slider(elec, "Current A", 0.01, 5.0, _electrolysis_current_a, func(v): _electrolysis_current_a = v)
	_anchor_slider(elec, "Time s", 1.0, 3600.0, _electrolysis_time_s, func(v): _electrolysis_time_s = v)
	var elec_btn := Button.new()
	elec_btn.text = "Run electrolysis"
	elec_btn.position = Vector2(34, 300 - 28)
	elec_btn.size = Vector2(150, 26)
	elec_btn.pressed.connect(func(): _run_electrolysis())
	elec.add_child(elec_btn)

	# ---- Corrosion panel ----
	var corr := _panel("Corrosion (mixed potential)", Vector2(24, 388), Vector2(560, 220))
	_anchor_dropdown(corr, "Metal", ["Fe", "Zn", "Cu", "Ag", "Pb", "Ni"], _corrosion_metal, func(v): _corrosion_metal = v)
	_anchor_dropdown(corr, "Environment", ["seawater", "acidic", "atmospheric"], _corrosion_env, func(v): _corrosion_env = v)
	_anchor_slider(corr, "Chloride mol/L", 0.0, 1.0, _corrosion_chloride_m, func(v): _corrosion_chloride_m = v)
	var corr_btn := Button.new()
	corr_btn.text = "Analyze corrosion"
	corr_btn.position = Vector2(34, 220 - 28)
	corr_btn.size = Vector2(150, 26)
	corr_btn.pressed.connect(func(): _analyze_corrosion())
	corr.add_child(corr_btn)

	# ---- Log/readout ----
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
	lbl.position = Vector2(14, _panel_cursor(parent))
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", DIM)
	parent.add_child(lbl)

	var opt := OptionButton.new()
	opt.position = Vector2(14, _panel_cursor(parent) + 16)
	opt.size = Vector2(200, 24)
	for o in options:
		opt.add_item(o)
	opt.select(options.find(current))
	opt.item_selected.connect(func(idx): on_changed(opt.get_item_text(idx)))
	parent.add_child(opt)

func _panel_cursor(parent: Control) -> float:
	# crude cursor: count children * 40
	return (parent.get_child_count() - 1) * 42

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

func _refresh_all() -> void:
	var temp_k = _temperature_c + 273.15
	var e_anode = _nernst(_anode_material, _anode_conc_m, temp_k)
	var e_cathode = _nernst(_cathode_material, _cathode_conc_m, temp_k)
	var e_cell = e_cathode - e_anode
	var i = e_cell / (_internal_r_ohm + _load_ohm)
	var p = i * i * _load_ohm

	var txt = []
	txt.push("[center][b]Galvanic cell: %s → %s[/b][/center]" % [_anode_material, _cathode_material])
	txt.push("")
	txt.push("E°cell = %0.3f V" % (E_STD[_cathode_material] - E_STD[_anode_material]))
	txt.push("E_anode (Nernst) = %0.3f V" % e_anode)
	txt.push("E_cathode (Nernst) = %0.3f V" % e_cathode)
	txt.push("E_cell = %0.3f V" % e_cell)
	txt.push("I = %0.4f A  (R_int = %0.2f Ω, R_load = %0.2f Ω)" % [i, _internal_r_ohm, _load_ohm])
	txt.push("P = %0.3f W" % p)
	txt.push("")
	txt.push("Nernst: E = E° − (RT/nF)·ln(Q), n = 2, T = %0.1f °C" % _temperature_c)
	txt.push("Zn2+ + 2e− → Zn   E° = −0.763 V")
	txt.push("Cu2+ + 2e− → Cu   E° = +0.340 V")

	_readout.text = txt.join("\n")

	# Why panel
	var why = []
	why.push("[b]Why:[/b] The cell voltage falls as concentrations diverge from standard (Q ≠ 1).")
	why.push("Higher load resistance → lower current, higher voltage; max power at R_load = R_int.")
	why.push("If E_cell < 0, the spontaneous direction is reversed (electrolytic).")
	_why_panel.text = why.join("\n")

	if e_cell > 1.5:
		_log.append_text("[color=green]✓[/color] Strong galvanic cell: %0.3f V, %0.2f A\n" % [e_cell, i])
	elif e_cell > 0:
		_log.append_text("[color=yellow]⚠[/color] Weak cell: %0.3f V\n" % e_cell)
	else:
		_log.append_text("[color=red]✗[/color] Non-spontaneous: %0.3f V — would run electrolytic\n" % e_cell)

func _nernst(metal: String, conc: float, temp_k: float) -> float:
	# M2+ + 2e- -> M, n = 2, E = E° - (RT/2F)*ln(1/[M2+])
	var e0 = E_STD.has(metal) and E_STD[metal] or 0.0
	if conc <= 0:
		conc = 0.001
	var q = 1.0 / conc
	var e = e0 - (R * temp_k / (2.0 * F)) * log(q)
	return e

func _run_electrolysis() -> void:
	# Faraday: m = M*I*t/(n*F), n_e = I*t/F
	var n_e = _electrolysis_current_a * _electrolysis_time_s / F
	var target = _electrolysis_target
	var molar_mass = {
		"Cu2+": 63.546,
		"H2O": 18.015,
		"NaCl": 58.44,
	}[target] or 63.546
	var n_electrons = {"Cu2+": 2, "H2O": 2, "NaCl": 1}[target] or 2
	var mass_g = molar_mass * n_e / n_electrons
	var extent = n_e / n_electrons

	var txt = []
	txt.push("[center][b]Electrolysis result[/b][/center]")
	txt.push("")
	txt.push("Target: %s" % target)
	txt.push("Current: %0.3f A for %0.1f s" % [_electrolysis_current_a, _electrolysis_time_s])
	txt.push("n(e−) = %0.4f mol" % n_e)
	txt.push("Extent ξ = %0.4f mol" % extent)
	txt.push("Mass deposited: %0.3f g" % mass_g)
	txt.push("")
	txt.push("Faraday: m = M·I·t/(n·F)")
	txt.push("Cu2+ + 2e− → Cu(s)   (n = 2)")

	_readout.text = txt.join("\n")
	_log.append_text("[color=cyan]→[/color] Electrolysis: %0.3f g %s deposited at %0.3f A, %0.1f s\n" % [mass_g, target, _electrolysis_current_a, _electrolysis_time_s])

func _analyze_corrosion() -> void:
	# Mixed potential: simple Tafel bisection
	var e_lo = -2.0
	var e_hi = 2.0
	var f_lo = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_lo)
	var f_hi = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_hi)
	if f_lo * f_hi > 0:
		e_lo, e_hi = -3.0, 3.0
		f_lo = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_lo)
		f_hi = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_hi)
	var e_corr = (e_lo + e_hi) / 2.0
	for _ in range(80):
		var e_mid = (e_lo + e_hi) / 2.0
		var f_mid = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_mid)
		if abs(f_mid) < 1e-15:
			break
		if f_lo * f_mid <= 0:
			e_hi = e_mid
		else:
			e_lo = e_mid
			f_lo = f_mid
	e_corr = (e_lo + e_hi) / 2.0
	var i_corr = abs(_net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_corr)) * 1e6  # µA/cm²
	var cr = (i_corr * 65.38 * 3.27e-3) / (2.0 * 7.14)  # mm/y for Fe

	var txt = []
	txt.push("[center][b]Corrosion analysis: %s in %s[/b][/center]" % [_corrosion_metal, _corrosion_env])
	txt.push("")
	txt.push("E_corr = %0.3f V vs SHE" % e_corr)
	txt.push("i_corr = %0.3f µA/cm²" % i_corr)
	txt.push("Corrosion rate = %0.3f mm/y" % cr)
	txt.push("Chloride: %0.3f mol/L" % _corrosion_chloride_m)
	txt.push("")
	txt.push("CR (mm/y) = i_corr·M·K/(n·ρ), K = 3.27×10⁻³")
	txt.push("Pitting risk: %s" % (_pitting_risk() and "YES" or "no"))

	_readout.text = txt.join("\n")
	_why_panel.text = "[b]Why:[/b] Mixed potential where anodic dissolution = cathodic reduction. Higher [Cl⁻] → lower pitting potential → higher risk."
	_log.append_text("[color=%s]→[/color] Corrosion: %s, E_corr = %0.3f V, CR = %0.3f mm/y\n" % [(_pitting_risk() and "red" or "green"), _corrosion_metal, e_corr, cr])

func _net_curr(metal: String, env: String, chloride: float, e: float) -> float:
	# Simple Tafel: i_a = i0a*10^((E-Eeq_a)/ba), i_c = -i0c*10^((Eeq_c-E)/bc)
	var e_eq_a = -0.76  # Zn/Fe approximate
	var e_eq_c = 0.34   # O2 reduction approximate
	var ba = 0.12
	var bc = 0.12
	var i0a = 1e-6
	var i0c = 1e-5
	if env == "seawater":
		i0c *= 2.0
	if chloride > 0.1:
		i0a *= 1.0 + chloride
	var i_a = i0a * pow(10, (e - e_eq_a) / ba)
	var i_c = -i0c * pow(10, (e_eq_c - e) / bc)
	return i_a + i_c

func _pitting_risk() -> bool:
	var e_lo = -2.0
	var e_hi = 2.0
	var f_lo = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_lo)
	var f_hi = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_hi)
	if f_lo * f_hi > 0:
		return false
	var e_lo2 = e_lo
	var e_hi2 = e_hi
	for _ in range(60):
		var e_mid = (e_lo2 + e_hi2) / 2.0
		var f_mid = _net_curr(_corrosion_metal, _corrosion_env, _corrosion_chloride_m, e_mid)
		if f_lo * f_mid <= 0:
			e_hi2 = e_mid
		else:
			e_lo2 = e_mid
			f_lo = f_mid
	var e_corr = (e_lo2 + e_hi2) / 2.0
	var e_pit = e_corr + 0.3
	return _corrosion_chloride_m > 0.1 and e_pit > e_corr + 0.2
