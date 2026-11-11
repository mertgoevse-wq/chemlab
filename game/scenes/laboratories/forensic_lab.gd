# Athanor Ascension — Forensic Toxicology Laboratory
# SPE extraction, LC-MS/MS screening, confirmatory analysis, chain of custody.
# Failures: missed analyte, matrix effect, contamination, broken chain of custody.

extends Control

const BG: Color = Color(0.05, 0.05, 0.07, 1.0)
const PANEL: Color = Color(0.08, 0.08, 0.1, 0.95)
const TEXT: Color = Color(0.85, 0.9, 0.95)
const DIM: Color = Color(0.55, 0.6, 0.65)
const CYAN: Color = Color(0.5, 0.8, 1.0)
const AMBER: Color = Color(1.0, 0.75, 0.3)
const RED: Color = Color(1.0, 0.35, 0.35)
const GREEN: Color = Color(0.5, 0.85, 0.5)

var _sample_type: String = "blood"
var _analyte: String = "ethanol"
var _concentration: float = 0.08  # g/dL
var _spe_recovery: float = 0.85
var _matrix_effect: bool = false
var _contamination: bool = false
var _chain_of_custody: bool = true
var _confirmatory: bool = false
var _detected: bool = false
var _measured_conc: float = 0.0
var _uncertainty: float = 0.0

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
	title.text = "FORENSIC TOXICOLOGY  ·  SPE • LC-MS/MS • CHAIN OF CUSTODY"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Screening · confirmatory analysis · matrix effects · legal admissibility"
	subtitle.position = Vector2(24, 40)
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.add_theme_color_override("font_color", DIM)
	add_child(subtitle)

	var sample := _panel("Sample & analyte", Vector2(24, 68), Vector2(560, 280))
	_anchor_dropdown(sample, "Sample type", ["blood", "urine", "saliva", "hair"], _sample_type, func(v): _sample_type = v)
	_anchor_dropdown(sample, "Analyte", ["ethanol", "cocaine", "opioids", "benzodiazepines", "cannabis"], _analyte, func(v): _analyte = v)
	_anchor_slider(sample, "Concentration g/dL", 0.0, 0.5, _concentration, func(v): _concentration = v)
	_anchor_slider(sample, "SPE recovery %", 50.0, 100.0, _spe_recovery * 100, func(v): _spe_recovery = v / 100.0)
	_anchor_checkbox(sample, "Matrix effect", _matrix_effect, func(v): _matrix_effect = v)
	_anchor_checkbox(sample, "Contamination", _contamination, func(v): _contamination = v)
	var run_btn := Button.new()
	run_btn.text = "Run screening"
	run_btn.position = Vector2(14, 280 - 28)
	run_btn.size = Vector2(160, 26)
	run_btn.pressed.connect(func(): _run_screening())
	sample.add_child(run_btn)

	var conf := _panel("Confirmatory & custody", Vector2(608, 68), Vector2(560, 280))
	_anchor_checkbox(conf, "Chain of custody intact", _chain_of_custody, func(v): _chain_of_custody = v)
	_anchor_checkbox(conf, "Confirmatory LC-MS/MS", _confirmatory, func(v): _confirmatory = v)
	var conf_btn := Button.new()
	conf_btn.text = "Evaluate admissibility"
	conf_btn.position = Vector2(14, 280 - 28)
	conf_btn.size = Vector2(180, 26)
	conf_btn.pressed.connect(func(): _evaluate_admissibility())
	conf.add_child(conf_btn)

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
	_run_screening()

func _run_screening() -> void:
	# Screening: measured = true * recovery * matrix_factor + noise
	var matrix_factor = 1.0
	if _matrix_effect:
		matrix_factor = 0.7 + randf_range(-0.1, 0.1)  # ion suppression/enhancement
	if _contamination:
		_concentration += 0.02  # false positive contribution
	var measured = _concentration * _spe_recovery * matrix_factor
	_measured_conc = clampf(measured, 0.0, 1.0)
	_uncertainty = _measured_conc * 0.15  # 15% relative uncertainty
	var cutoff_dict = {
		"ethanol": 0.02,
		"cocaine": 0.01,
		"opioids": 0.005,
		"benzodiazepines": 0.005,
		"cannabis": 0.005,
	}
	var cutoff: float = cutoff_dict.get(_analyte, 0.01)
	_detected = _measured_conc > cutoff

	var txt: PackedStringArray = []
	txt.append("[center][b]Screening result[/b][/center]")
	txt.append("")
	txt.append("Sample: %s  Analyte: %s" % [_sample_type, _analyte])
	txt.append("True concentration: %0.3f g/dL" % _concentration)
	txt.append("SPE recovery: %0.0f%%" % (_spe_recovery * 100))
	txt.append("Matrix effect: %s" % (_matrix_effect and "yes (ion suppression)" or "no"))
	txt.append("Contamination: %s" % (_contamination and "yes" or "no"))
	txt.append("")
	txt.append("Measured: %0.3f ± %0.3f g/dL" % [_measured_conc, _uncertainty])
	txt.append("Cutoff: %0.3f g/dL" % cutoff)
	txt.append("Detected: %s" % (_detected and "POSITIVE" or "negative"))

	_readout.text = "\n".join(txt)

	var why: PackedStringArray = []
	why.append("[b]Why:[/b] SPE recovery <100% under-reads concentration.")
	why.append("Matrix effects suppress/enhance ionisation in LC-MS/MS.")
	why.append("Contamination → false positives. Chain of custody → legal admissibility.")
	_why_panel.text = "\n".join(why)

	var level = "green" if _detected else "green"
	_log.append_text("[color=%s]→[/color] Screening: %s = %0.3f g/dL (cutoff %0.3f)\n" % [level, _analyte, _measured_conc, cutoff])

func _evaluate_admissibility() -> void:
	var txt: PackedStringArray = []
	txt.append("[center][b]Chain of custody & admissibility[/b][/center]")
	txt.append("")
	txt.append("Chain of custody intact: %s" % (_chain_of_custody and "yes" or "BROKEN"))
	txt.append("Confirmatory LC-MS/MS: %s" % (_confirmatory and "yes" or "no"))
	txt.append("Measured: %0.3f ± %0.3f g/dL" % [_measured_conc, _uncertainty])
	txt.append("")
	var admissible = _chain_of_custody and _confirmatory
	txt.append("Legally admissible: %s" % (admissible and "YES" or "NO"))
	txt.append("")
	txt.append("Without chain of custody: evidence excluded.")
	txt.append("Without confirmation: screening only, not for court.")

	_readout.text = "\n".join(txt)
	_why_panel.text = "[b]Why:[/b] Forensic results require documented custody and orthogonal confirmation (LC-MS/MS) to be admissible in court."
	_log.append_text("[color=%s]→[/color] Admissibility: %s\n" % [(_chain_of_custody and _confirmatory and "green" or "red"), (admissible and "YES" or "NO")])
