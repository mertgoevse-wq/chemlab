# Athanor Ascension - Vitals HUD
# Handles: Health, stamina, radiation, chemical exposure, injuries display

extends CanvasLayer

class_name VitalsHUD

@export var show_detailed: bool = true
@export var compact_mode: bool = false

var vitals: PlayerVitals
var _hud_visible: bool = false

# UI elements
var _health_bar: ProgressBar
var _stamina_bar: ProgressBar
var _radiation_bar: ProgressBar
var _chemical_bar: ProgressBar
var _health_label: Label
var _stamina_label: Label
var _radiation_label: Label
var _chemical_label: Label
var _injury_container: VBoxContainer
var _effects_container: HBoxContainer

func _ready() -> void:
	_cache_nodes()
	_connect_signals()
	_update_all()

func _cache_nodes() -> void:
	if has_node("%HealthBar"):
		_health_bar = %HealthBar
		_stamina_bar = %StaminaBar
		_radiation_bar = %RadiationBar
		_chemical_bar = %ChemicalBar
		_health_label = %HealthLabel
		_stamina_label = %StaminaLabel
		_radiation_label = %RadiationLabel
		_chemical_label = %ChemicalLabel
		_injury_container = %InjuryContainer
		_effects_container = %EffectsContainer
	else:
		_build_default_ui()

	vitals = get_node_or_null("/root/PlayerVitals")

func _build_default_ui() -> void:
	var root_control := Control.new()
	root_control.name = "HUDControl"
	root_control.set_anchors_preset(Control.PRESET_FULL_RECT)
	root_control.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root_control)

	var panel := PanelContainer.new()
	panel.name = "VitalsPanel"
	panel.position = Vector2(20, 20)
	panel.custom_minimum_size = Vector2(280, 160)
	root_control.add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.name = "VitalsVBox"
	panel.add_child(vbox)

	# Health
	var h_box := HBoxContainer.new()
	var h_title := Label.new()
	h_title.text = "VITALS:"
	h_box.add_child(h_title)
	_health_label = Label.new()
	_health_label.text = "100 / 100"
	h_box.add_child(_health_label)
	vbox.add_child(h_box)

	_health_bar = ProgressBar.new()
	_health_bar.max_value = 100
	_health_bar.value = 100
	_health_bar.custom_minimum_size = Vector2(260, 16)
	vbox.add_child(_health_bar)

	# Stamina
	var s_box := HBoxContainer.new()
	var s_title := Label.new()
	s_title.text = "STAMINA:"
	s_box.add_child(s_title)
	_stamina_label = Label.new()
	_stamina_label.text = "100%"
	s_box.add_child(_stamina_label)
	vbox.add_child(s_box)

	_stamina_bar = ProgressBar.new()
	_stamina_bar.max_value = 100
	_stamina_bar.value = 100
	_stamina_bar.custom_minimum_size = Vector2(260, 12)
	vbox.add_child(_stamina_bar)

	# Radiation
	var r_box := HBoxContainer.new()
	var r_title := Label.new()
	r_title.text = "RAD DOSE:"
	r_box.add_child(r_title)
	_radiation_label = Label.new()
	_radiation_label.text = "0.00 mSv"
	r_box.add_child(_radiation_label)
	vbox.add_child(r_box)

	_radiation_bar = ProgressBar.new()
	_radiation_bar.max_value = 1000
	_radiation_bar.value = 0
	_radiation_bar.custom_minimum_size = Vector2(260, 12)
	vbox.add_child(_radiation_bar)

	# Chemical exposure
	var c_box := HBoxContainer.new()
	var c_title := Label.new()
	c_title.text = "TOXIC EXPOSURE:"
	c_box.add_child(c_title)
	_chemical_label = Label.new()
	_chemical_label.text = "0 ppm·min"
	c_box.add_child(_chemical_label)
	vbox.add_child(c_box)

	_chemical_bar = ProgressBar.new()
	_chemical_bar.max_value = 5000
	_chemical_bar.value = 0
	_chemical_bar.custom_minimum_size = Vector2(260, 12)
	vbox.add_child(_chemical_bar)

	# Containers
	_injury_container = VBoxContainer.new()
	_injury_container.name = "InjuryContainer"
	vbox.add_child(_injury_container)

	_effects_container = HBoxContainer.new()
	_effects_container.name = "EffectsContainer"
	vbox.add_child(_effects_container)

func _connect_signals() -> void:
	if vitals:
		vitals.health_changed.connect(_on_health_changed)
		vitals.injury_added.connect(_on_injury_added)
		vitals.injury_healed.connect(_on_injury_healed)
		vitals.exposure_changed.connect(_on_exposure_changed)
		vitals.radiation_changed.connect(_on_radiation_changed)
		vitals.incapacitated.connect(_on_incapacitated)
		vitals.stabilised.connect(_on_stabilised)

func set_hud_visible(p_visible: bool) -> void:
	_hud_visible = p_visible
	visible = p_visible

func _update_all() -> void:
	if not vitals:
		return

	_on_health_changed(vitals.health, PlayerVitals.MAX_HEALTH)
	_on_stamina_changed(vitals.stamina)
	_on_radiation_changed(vitals.radiation_msv)
	_on_exposure_changed("", 0.0)  # Will update all chemicals

	for injury in vitals.injuries:
		_add_injury_ui(injury)

func _on_health_changed(current: float, maximum: float) -> void:
	_health_bar.max_value = maximum
	_health_bar.value = current
	_health_label.text = "%d / %d" % [int(current), int(maximum)]

	# Color coding
	if current / maximum > 0.6:
		_set_bar_fill_color(_health_bar, Color(0.2, 0.8, 0.2))
	elif current / maximum > 0.3:
		_set_bar_fill_color(_health_bar, Color(1.0, 0.8, 0.0))
	else:
		_set_bar_fill_color(_health_bar, Color(1.0, 0.2, 0.2))

func _set_bar_fill_color(bar: ProgressBar, color: Color) -> void:
	if not bar:
		return
	var style: StyleBoxFlat = null
	if bar.has_theme_stylebox_override("fill"):
		style = bar.get_theme_stylebox("fill") as StyleBoxFlat
	if not style:
		style = StyleBoxFlat.new()
		style.set_corner_radius_all(2)
		bar.add_theme_stylebox_override("fill", style)
	style.bg_color = color

func _on_stamina_changed(stamina: float) -> void:
	_stamina_bar.value = stamina
	_stamina_label.text = "%d%%" % int(stamina)

func _on_radiation_changed(dose_msv: float) -> void:
	var max_rad = PlayerVitals.RADIATION_HARD_LIMIT_MSV
	_radiation_bar.max_value = max_rad
	_radiation_bar.value = dose_msv
	_radiation_label.text = "%.2f mSv" % dose_msv

	# Color coding
	if dose_msv > PlayerVitals.RADIATION_ANNUAL_LIMIT_MSV:
		_set_bar_fill_color(_radiation_bar, Color(1.0, 0.0, 0.0))
	elif dose_msv > 10.0:
		_set_bar_fill_color(_radiation_bar, Color(1.0, 0.5, 0.0))
	else:
		_set_bar_fill_color(_radiation_bar, Color(0.0, 0.5, 1.0))

func _on_exposure_changed(chemical: String, ppm_minutes: float) -> void:
	# Update chemical exposure display
	var total_exposure = 0.0
	for chem in vitals.chemical_exposure:
		total_exposure += vitals.chemical_exposure[chem]

	var max_exp = 5000.0  # Gameplay budget
	_chemical_bar.max_value = max_exp
	_chemical_bar.value = total_exposure
	_chemical_label.text = "%.0f ppm·min" % total_exposure

	# Color coding
	if total_exposure > max_exp * 0.8:
		_set_bar_fill_color(_chemical_bar, Color(1.0, 0.0, 0.0))
	elif total_exposure > max_exp * 0.5:
		_set_bar_fill_color(_chemical_bar, Color(1.0, 0.5, 0.0))
	else:
		_set_bar_fill_color(_chemical_bar, Color(0.5, 0.0, 1.0))

	# Update detailed chemical list if visible
	if show_detailed:
		_update_chemical_details()

func _update_chemical_details() -> void:
	# Would populate detailed chemical exposure list
	pass

func _on_injury_added(injury: Dictionary) -> void:
	_add_injury_ui(injury)

func _add_injury_ui(injury: Dictionary) -> void:
	var injury_ui = HBoxContainer.new()
	injury_ui.name = "Injury_%s" % injury.id

	var icon = TextureRect.new()
	icon.texture = _get_injury_icon(injury.type)
	icon.set_custom_minimum_size(Vector2(24, 24))
	injury_ui.add_child(icon)

	var label = Label.new()
	label.text = "%s (%.1fx)" % [injury.label, injury.severity]
	label.add_theme_color_override("font_color", _get_injury_color(injury.type))
	injury_ui.add_child(label)

	var progress = ProgressBar.new()
	progress.max_value = injury.remaining_s
	progress.value = injury.remaining_s
	progress.set_custom_minimum_size(Vector2(100, 16))
	injury_ui.add_child(progress)

	# Store reference for updates
	injury_ui.set_meta("injury_id", injury.id)
	injury_ui.set_meta("progress_bar", progress)

	_injury_container.add_child(injury_ui)

func _on_injury_healed(injury_id: String) -> void:
	for child in _injury_container.get_children():
		if child.get_meta("injury_id", "") == injury_id:
			child.queue_free()
			break

func _on_incapacitated(reason: String) -> void:
	# Show incapacitation overlay
	var overlay = ColorRect.new()
	overlay.color = Color(0, 0, 0, 0.8)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(overlay)

	var label = Label.new()
	label.text = "INCAPACITATED\n%s" % reason
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 48)
	label.add_theme_color_override("font_color", Color(1, 0.2, 0.2))
	overlay.add_child(label)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)

	# Auto-remove on stabilise
	var timer = Timer.new()
	timer.wait_time = 6.0
	timer.one_shot = true
	timer.timeout.connect(func(): overlay.queue_free())
	overlay.add_child(timer)
	timer.start()

func _on_stabilised() -> void:
	# Remove incapacitation overlay
	for child in get_children():
		if child is ColorRect:
			child.queue_free()

func _get_injury_icon(injury_type: String) -> Texture2D:
	# Would return appropriate icon
	return null

func _get_injury_color(injury_type: String) -> Color:
	match injury_type:
		"chemical_burn": return Color(0.6, 0.2, 0.2)
		"thermal_burn": return Color(1.0, 0.4, 0.0)
		"laceration": return Color(1.0, 0.2, 0.2)
		"inhalation": return Color(0.6, 0.6, 0.6)
		"eye_splash": return Color(1.0, 0.0, 1.0)
		"radiation": return Color(0.0, 1.0, 0.0)
		_: return Color(1.0, 1.0, 1.0)

func _process(delta: float) -> void:
	if not _injury_container:
		return
	# Update injury timers
	for child in _injury_container.get_children():
		if child.has_meta("progress_bar"):
			var progress = child.get_meta("progress_bar") as ProgressBar
			if progress and progress.value > 0.0:
				progress.value = maxf(0.0, progress.value - delta)