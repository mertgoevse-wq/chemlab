# Athanor Ascension — Accelerator Control Room
# A terminal-style scene: the beamline is drawn schematically, every readout comes
# from AcceleratorPhysics (real relativistic kinematics), and target activation is
# computed from cross-section, flux and irradiation time.

extends Control

const BG: Color = Color(0.03, 0.043, 0.058, 1.0)
const PANEL: Color = Color(0.055, 0.07, 0.088, 1.0)
const GRID: Color = Color(0.18, 0.26, 0.3, 0.5)
const TEXT: Color = Color(0.8, 0.87, 0.91)
const DIM: Color = Color(0.5, 0.59, 0.66)
const CYAN: Color = Color(0.24, 0.85, 0.95)
const AMBER: Color = Color(1.0, 0.7, 0.26)
const RED: Color = Color(1.0, 0.36, 0.32)

var _particle: String = "proton"
var _energy_mev: float = 250.0
var _radius_m: float = 1.2
var _current_ua: float = 10.0
var _medium: String = "air"
var _reaction_id: String = "p_li7"
var _target_mass_g: float = 2.0
var _irradiation_s: float = 600.0
var _cross_section_barn: float = 0.05

var _particle_opt: OptionButton
var _medium_opt: OptionButton
var _reaction_opt: OptionButton
var _energy_slider: HSlider
var _radius_slider: HSlider
var _current_slider: HSlider
var _energy_label: Label
var _radius_label: Label
var _current_label: Label
var _readout: RichTextLabel
var _experiment_panel: RichTextLabel
var _status: RichTextLabel
var _time: float = 0.0


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
	title.text = "IGNIS BEAM FACILITY  ·  OPERATOR TERMINAL"
	title.position = Vector2(24.0, 16.0)
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Relativistic kinematics computed offline · no network dependency"
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

	var left := VBoxContainer.new()
	left.position = Vector2(24.0, 76.0)
	left.custom_minimum_size = Vector2(300, 560)
	left.add_theme_constant_override("separation", 10)
	add_child(left)
	left.add_child(_section("BEAM CONFIGURATION"))

	left.add_child(_small("Particle"))
	_particle_opt = OptionButton.new()
	for p in ["proton", "deuteron", "alpha", "electron", "lithium7", "lead208"]:
		_particle_opt.add_item(p.capitalize(), _particle_opt.item_count)
	_particle_opt.item_selected.connect(func(idx):
		_particle = ["proton", "deuteron", "alpha", "electron", "lithium7", "lead208"][idx]
		_refresh())
	left.add_child(_particle_opt)

	_energy_label = _small("Kinetic energy")
	left.add_child(_energy_label)
	_energy_slider = _slider(5.0, 7000.0, 250.0)
	_energy_slider.value_changed.connect(func(v): _energy_mev = v; _refresh())
	left.add_child(_energy_slider)

	_radius_label = _small("Bending radius")
	left.add_child(_radius_label)
	_radius_slider = _slider(0.2, 6.0, 1.2)
	_radius_slider.value_changed.connect(func(v): _radius_m = v; _refresh())
	left.add_child(_radius_slider)

	_current_label = _small("Beam current")
	left.add_child(_current_label)
	_current_slider = _slider(0.1, 5000.0, 10.0)
	_current_slider.value_changed.connect(func(v): _current_ua = v; _refresh())
	left.add_child(_current_slider)

	left.add_child(_small("Cherenkov medium"))
	_medium_opt = OptionButton.new()
	var media := ["vacuum", "air", "water", "silica_glass", "lead_glass", "heavy_water"]
	for m in media:
		_medium_opt.add_item(m.replace("_", " ").capitalize())
	_medium_opt.selected = 1
	_medium_opt.item_selected.connect(func(idx): _medium = media[idx]; _refresh())
	left.add_child(_medium_opt)

	left.add_child(_section("EXPERIMENT"))
	_reaction_opt = OptionButton.new()
	for r in AcceleratorPhysics.REACTIONS:
		_reaction_opt.add_item(str(r.get("label", r.get("id", "?"))))
	_reaction_opt.selected = 2
	_reaction_opt.item_selected.connect(func(idx):
		_reaction_id = str(AcceleratorPhysics.REACTIONS[idx].get("id", ""))
		_refresh())
	left.add_child(_reaction_opt)

	var run := Button.new()
	run.text = "▶ Run beam to target"
	run.custom_minimum_size = Vector2(0, 34)
	run.pressed.connect(_on_run)
	left.add_child(run)

	_readout = RichTextLabel.new()
	_readout.bbcode_enabled = true
	_readout.fit_content = true
	_readout.position = Vector2(348.0, 76.0)
	_readout.custom_minimum_size = Vector2(420, 300)
	_readout.add_theme_font_size_override("normal_font_size", 12)
	add_child(_readout)

	_status = RichTextLabel.new()
	_status.bbcode_enabled = true
	_status.fit_content = true
	_status.position = Vector2(348.0, 402.0)
	_status.custom_minimum_size = Vector2(880, 150)
	_status.add_theme_font_size_override("normal_font_size", 12)
	add_child(_status)

	_experiment_panel = RichTextLabel.new()
	_experiment_panel.bbcode_enabled = true
	_experiment_panel.fit_content = true
	_experiment_panel.position = Vector2(348.0, 556.0)
	_experiment_panel.custom_minimum_size = Vector2(880, 130)
	_experiment_panel.add_theme_font_size_override("normal_font_size", 11)
	add_child(_experiment_panel)

	_status.text = "[color=#7f8c9b]Select a reaction and run the beam. Thresholds and activation are computed from real kinematics.[/color]"


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


func _slider(min_v: float, max_v: float, value: float) -> HSlider:
	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.step = 0.1
	slider.value = value
	slider.custom_minimum_size = Vector2(280, 22)
	return slider


func _refresh() -> void:
	_energy_label.text = "Kinetic energy · %.1f MeV" % _energy_mev
	_radius_label.text = "Bending radius · %.2f m" % _radius_m
	_current_label.text = "Beam current · %.2f µA" % _current_ua

	var beam := AcceleratorPhysics.describe_beam(_energy_mev, _particle)
	var field := AcceleratorPhysics.required_field_t(_energy_mev, _particle, _radius_m)
	var rev_hz := AcceleratorPhysics.revolution_frequency_hz(_energy_mev, _particle, 2.0 * PI * _radius_m)
	var cherenkov := AcceleratorPhysics.cherenkov_angle_deg(_energy_mev, _particle, _medium)
	var cherenkov_threshold := AcceleratorPhysics.cherenkov_threshold_mev(_particle, _medium)
	var power := AcceleratorPhysics.beam_power_w(_energy_mev, _current_ua)
	var loss := AcceleratorPhysics.synchrotron_loss_ev_per_turn(_energy_mev / 1000.0, _particle, _radius_m)

	_readout.text = "[b][color=#%s]BEAM STATE[/color][/b]\n" % CYAN.to_html(false) + \
		"gamma            %.4f\n" % beam["gamma"] + \
		"beta             %.6f  (%.3f%% c)\n" % [beam["beta"], beam["beta_percent_c"]] + \
		"momentum         %.3f MeV/c\n" % beam["momentum_mev_c"] + \
		"magnetic rigidity %.4f T·m\n" % beam["rigidity_t_m"] + \
		"[color=#%s]required field    %.3f T at r = %.2f m[/color]\n" % [AMBER.to_html(false), field, _radius_m] + \
		"revolution freq   %s Hz\n" % _sci(rev_hz) + \
		"beam power        %s W\n" % _sci(power) + \
		"Cherenkov angle   %.2f° in %s (threshold %.2f MeV)\n" % [cherenkov, _medium, cherenkov_threshold] + \
		"synchrotron loss  %s eV/turn\n" % _sci(loss)

	var reaction := AcceleratorPhysics.reaction(_reaction_id)
	var threshold := AcceleratorPhysics.reaction_threshold_mev(_reaction_id)
	var feasible := _energy_mev >= threshold and str(reaction.get("projectile", "")) == _particle
	var color := CYAN if feasible else AMBER
	_status.text = "[b]TARGET REACTION[/b]\n%s\nQ = %.3f MeV · threshold = %.3f MeV · projectile = %s\n[color=#%s]%s[/color]\n[color=#7f8c9b]%s[/color]" % [
		str(reaction.get("label", "")),
		float(reaction.get("q_mev", 0.0)),
		threshold,
		str(reaction.get("projectile", "")),
		color.to_html(false),
		"Above threshold: reaction channel open." if feasible else "Below threshold or wrong projectile: no reaction.",
		str(reaction.get("note", ""))
	]


func _on_run() -> void:
	var reaction := AcceleratorPhysics.reaction(_reaction_id)
	var threshold := AcceleratorPhysics.reaction_threshold_mev(_reaction_id)
	if str(reaction.get("projectile", "")) != _particle:
		_status.text = "[color=#%s]Interlock: this reaction needs a %s beam, not %s.[/color]" % [RED.to_html(false), str(reaction.get("projectile", "")), _particle]
		return
	if _energy_mev < threshold:
		_status.text = "[color=#%s]Below threshold: %.1f MeV < %.2f MeV. Increase beam energy.[/color]" % [RED.to_html(false), _energy_mev, threshold]
		return

	var beam := AcceleratorPhysics.describe_beam(_energy_mev, _particle)
	var power := AcceleratorPhysics.beam_power_w(_energy_mev, _current_ua)
	var target := str(reaction.get("target", "lithium7"))
	var atoms := AcceleratorPhysics.target_atom_count(target, _target_mass_g)
	# Particle flux from current: I/e.
	var flux := _current_ua * 1.0e-6 / 1.602176634e-19
	var half_life := 53.22 * 86400.0   # Be-7, 53.22 d
	var activity := AcceleratorPhysics.activation_bq(atoms, _cross_section_barn, flux, half_life, _irradiation_s)

	_experiment_panel.text = "[b]RUN LOG[/b]\nBeam %.1f MeV %s · %.2f µA · beam power %s W\nTarget %s, %.1f g → %s atoms\nCross-section %.3f barn, %d s irradiation\nSaturation-corrected activity: %s Bq (%s µCi)\n[color=#7f8c9b]%s[/color]" % [
		_energy_mev, _particle, _current_ua, _sci(power), target.replace("_", " "), _target_mass_g, _sci(atoms),
		_cross_section_barn, int(_irradiation_s), _sci(activity), _sci(activity / 37000.0),
		"Activity uses A = N·σ·Φ·(1-e^-λt) for Be-7 (53.22 d). Cross-section is an operator input, not a prediction."
	]
	_status.text = "[color=#%s]Run complete. Beam stable at %.4f c.[/color]" % [CYAN.to_html(false), beam["beta"]]


func _sci(value: float) -> String:
	if value == 0.0:
		return "0"
	var sign_value := -1.0 if value < 0.0 else 1.0
	var v := absf(value)
	var exponent := int(floor(log(v) / log(10.0)))
	var mantissa := v / pow(10.0, exponent)
	return "%s%.2f e%d" % ["-" if sign_value < 0.0 else "", mantissa, exponent]


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)
	draw_line(Vector2(0, 64), Vector2(size.x, 64), GRID, 1.0)

	# Beamline schematic: source -> accelerating section -> dipole arc -> target.
	var origin := Vector2(370.0, 660.0)
	draw_string(ThemeDB.fallback_font, Vector2(24, 664), "BEAMLINE SCHEMATIC", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)
	var source := origin + Vector2(0, 0)
	draw_circle(source, 16.0, Color(0.12, 0.2, 0.24))
	draw_arc(source, 16.0, 0, TAU, 32, CYAN, 1.5)
	draw_string(ThemeDB.fallback_font, source + Vector2(-16, 34), "ION SOURCE", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	var linac_start := source + Vector2(34, 0)
	var linac_end := linac_start + Vector2(170, 0)
	draw_rect(Rect2(linac_start, Vector2(170, 26)), Color(0.08, 0.13, 0.16), true)
	draw_rect(Rect2(linac_start, Vector2(170, 26)), GRID, false, 1.0)
	for i in range(8):
		var x := linac_start.x + 8 + i * 20
		draw_line(Vector2(x, linac_start.y + 2), Vector2(x, linac_start.y + 24), Color(0.3, 0.6, 0.7, 0.4), 1.0)

	# Dipole arc.
	var center := Vector2(linac_end.x + 140, linac_end.y - 60)
	var arc_radius := 150.0
	draw_arc(center, arc_radius, deg_to_rad(70), deg_to_rad(170), 40, CYAN, 1.4)
	draw_string(ThemeDB.fallback_font, center + Vector2(-34, -arc_radius - 8), "DIPOLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Target chamber.
	var target_pos := Vector2(1090.0, 520.0)
	draw_circle(target_pos, 34.0, Color(0.1, 0.16, 0.18))
	draw_arc(target_pos, 34.0, 0, TAU, 32, AMBER, 1.5)
	draw_string(ThemeDB.fallback_font, target_pos + Vector2(-38, 54), "TARGET / HOT CELL", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)

	# Animated bunches.
	var path_start := source
	var path_end := linac_start
	var t := fmod(_time * 0.35, 1.0)
	draw_circle(path_start.lerp(path_end, t), 2.4, CYAN)
	var t2 := fmod(_time * 0.18, 1.0)
	var angle := lerpf(deg_to_rad(170), deg_to_rad(70), t2)
	var arc_point := center + Vector2(cos(angle), sin(angle)) * arc_radius
	draw_circle(arc_point, 3.0, CYAN)
	var t3 := fmod(_time * 0.22 + 0.4, 1.0)
	draw_circle(arc_point.lerp(target_pos, t3), 2.2, AMBER)

	# Radiation pulse at target.
	var pulse := 0.5 + 0.5 * sin(_time * 2.0)
	draw_arc(target_pos, 44.0 + pulse * 10.0, 0, TAU, 32, Color(1.0, 0.5, 0.2, 0.16 * (1.0 - pulse)), 2.0)
