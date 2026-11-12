# Athanor Ascension — Laboratory Apparatus Practicum & Interactive Workbench
# Comprehensive guided tutorials and physical simulation for 8 core apparatuses:
# 1. Rotary Evaporator (Rotovap)
# 2. Schlenk Line (Inert Gas / High Vacuum Manifold)
# 3. Analytical Balance & Micropipettes
# 4. High-Performance Liquid Chromatography (HPLC)
# 5. Soxhlet Extractor (Solid-Liquid Continuous Extraction)
# 6. UV-Vis Spectrophotometer (Beer-Lambert & Spectral Scanning)
# 7. Inert Atmosphere Glovebox (<0.1 ppm O2/H2O)
# 8. High-Speed Centrifuge & Vacuum Filtration

extends Control
class_name ApparatusPracticum

const HUB_SCENE: String = "res://scenes/laboratories/lab_hub.tscn"
const Suite = preload("res://scripts/labs/apparatus_suite.gd")

const BG: Color = Color(0.026, 0.036, 0.048, 1.0)
const PANEL: Color = Color(0.048, 0.064, 0.082, 0.96)
const PANEL_INSET: Color = Color(0.032, 0.044, 0.058, 0.98)
const TEXT: Color = Color(0.85, 0.90, 0.93)
const DIM: Color = Color(0.50, 0.60, 0.67)
const CYAN: Color = Color(0.24, 0.85, 0.92)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const RED: Color = Color(1.0, 0.38, 0.34)
const GREEN: Color = Color(0.38, 0.86, 0.65)
const BLUE: Color = Color(0.35, 0.65, 0.95)

enum ApparatusType { ROTOVAP, SCHLENK, BALANCE, HPLC, SOXHLET, UVVIS, GLOVEBOX, CENTRIFUGE, SEPFUNNEL, NMR, STIRRER, FUMEHOOD, MICROPIPETTE }
var _current_type: ApparatusType = ApparatusType.ROTOVAP

const APPARATUS_MODELS: Dictionary = {
	ApparatusType.ROTOVAP: "res://assets/apparatus/SM_Rotovap.glb",
	ApparatusType.SCHLENK: "res://assets/apparatus/SM_SchlenkLine.glb",
	ApparatusType.BALANCE: "res://assets/apparatus/SM_AnalyticalBalance.glb",
	ApparatusType.HPLC: "res://assets/apparatus/SM_HPLC_System.glb",
	ApparatusType.SOXHLET: "res://assets/apparatus/SM_SoxhletExtractor.glb",
	ApparatusType.UVVIS: "res://assets/apparatus/SM_UVVis_Spectrophotometer.glb",
	ApparatusType.GLOVEBOX: "res://assets/apparatus/SM_Glovebox.glb",
	ApparatusType.CENTRIFUGE: "res://assets/apparatus/SM_Centrifuge.glb",
	ApparatusType.SEPFUNNEL: "res://assets/apparatus/SM_SeparatoryFunnel_500ml.glb",
	ApparatusType.NMR: "res://assets/apparatus/SM_NMR_Spectrometer.glb",
	ApparatusType.STIRRER: "res://assets/apparatus/SM_MagneticStirrer_Hotplate.glb",
	ApparatusType.FUMEHOOD: "res://assets/apparatus/SM_FumeHood_Ducted.glb",
	ApparatusType.MICROPIPETTE: "res://assets/apparatus/SM_Micropipette_Set.glb",
}

const APPARATUS_SCALES: Dictionary = {
	ApparatusType.ROTOVAP: Vector3(1.1, 1.1, 1.1),
	ApparatusType.SCHLENK: Vector3(1.0, 1.0, 1.0),
	ApparatusType.BALANCE: Vector3(1.4, 1.4, 1.4),
	ApparatusType.HPLC: Vector3(0.85, 0.85, 0.85),
	ApparatusType.SOXHLET: Vector3(1.0, 1.0, 1.0),
	ApparatusType.UVVIS: Vector3(1.2, 1.2, 1.2),
	ApparatusType.GLOVEBOX: Vector3(0.55, 0.55, 0.55),
	ApparatusType.CENTRIFUGE: Vector3(1.4, 1.4, 1.4),
	ApparatusType.SEPFUNNEL: Vector3(1.2, 1.2, 1.2),
	ApparatusType.NMR: Vector3(0.55, 0.55, 0.55),
	ApparatusType.STIRRER: Vector3(1.5, 1.5, 1.5),
	ApparatusType.FUMEHOOD: Vector3(0.48, 0.48, 0.48),
	ApparatusType.MICROPIPETTE: Vector3(1.6, 1.6, 1.6),
}

# 3D Viewport Nodes
var _viewport_container: SubViewportContainer
var _sub_viewport: SubViewport
var _turntable: Node3D

# Suite Controllers
var _rotovap: Suite.RotovapController
var _schlenk: Suite.SchlenkLineController
var _balance: Suite.AnalyticalBalanceController
var _hplc: Suite.HPLCController
var _soxhlet: Suite.SoxhletController
var _uvvis: Suite.UVVisController
var _glovebox: Suite.GloveboxController
var _centrifuge: Suite.CentrifugeController
var _sep_funnel: Suite.SeparatoryFunnelController
var _nmr: Suite.NMRSpectrometerController
var _stirrer: Suite.MagneticStirrerController
var _fume_hood: Suite.FumeHoodController
var _micropipette: Suite.MicropipetteSetController

# UI Node References
var _opt_apparatus: OptionButton
var _title_label: Label
var _subtitle_label: Label
var _instructions_label: RichTextLabel
var _status_box: RichTextLabel
var _physics_panel: RichTextLabel
var _ai_advice_label: RichTextLabel
var _controls_vbox: VBoxContainer
var _btn_ai_advisor: Button
var _sim_timer: float = 0.0

# Latest result caches
var _last_hplc_result: Dictionary = {}
var _last_uvvis_result: Dictionary = {}
var _last_nmr_result: Dictionary = {}

func _init() -> void:
	_init_controllers()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if _controls_vbox == null:
		_build_ui()
	_switch_apparatus(ApparatusType.ROTOVAP)
	set_process(true)

func _init_controllers() -> void:
	_rotovap = Suite.RotovapController.new()
	_schlenk = Suite.SchlenkLineController.new()
	_balance = Suite.AnalyticalBalanceController.new()
	_hplc = Suite.HPLCController.new()
	_soxhlet = Suite.SoxhletController.new()
	_uvvis = Suite.UVVisController.new()
	_glovebox = Suite.GloveboxController.new()
	_centrifuge = Suite.CentrifugeController.new()
	_sep_funnel = Suite.SeparatoryFunnelController.new()
	_nmr = Suite.NMRSpectrometerController.new()
	_stirrer = Suite.MagneticStirrerController.new()
	_fume_hood = Suite.FumeHoodController.new()
	_micropipette = Suite.MicropipetteSetController.new()

func _process(delta: float) -> void:
	_sim_timer += delta
	if _turntable != null:
		_turntable.rotation.y += delta * 0.45
	match _current_type:
		ApparatusType.ROTOVAP:
			_rotovap.update(delta)
		ApparatusType.SOXHLET:
			_soxhlet.update(delta)
		ApparatusType.STIRRER:
			_stirrer.update(delta)

	_update_status_display()
	queue_redraw()

func _build_ui() -> void:
	# Header Panel
	var header := Panel.new()
	header.position = Vector2(0, 0)
	header.size = Vector2(1280, 68)
	var h_style := StyleBoxFlat.new()
	h_style.bg_color = PANEL
	h_style.border_width_bottom = 2
	h_style.border_color = Color(0.18, 0.28, 0.35, 0.8)
	header.add_theme_stylebox_override("panel", h_style)
	add_child(header)

	_title_label = Label.new()
	_title_label.text = "APPARATUS SUITE & INTERACTIVE METROLOGY"
	_title_label.position = Vector2(24, 12)
	_title_label.add_theme_font_size_override("font_size", 18)
	_title_label.add_theme_color_override("font_color", TEXT)
	header.add_child(_title_label)

	_subtitle_label = Label.new()
	_subtitle_label.text = "Certified ISO 17025 Operational Metrology · Real Chemical Thermodynamics"
	_subtitle_label.position = Vector2(24, 38)
	_subtitle_label.add_theme_font_size_override("font_size", 11)
	_subtitle_label.add_theme_color_override("font_color", DIM)
	header.add_child(_subtitle_label)

	# Apparatus Selector
	_opt_apparatus = OptionButton.new()
	_opt_apparatus.position = Vector2(620, 16)
	_opt_apparatus.custom_minimum_size = Vector2(320, 36)
	_opt_apparatus.add_item("1. Rotary Evaporator (Rotovap)", 0)
	_opt_apparatus.add_item("2. Schlenk Line (Vacuum/Argon)", 1)
	_opt_apparatus.add_item("3. Analytical Balance & Pipette", 2)
	_opt_apparatus.add_item("4. HPLC (C18 Reverse-Phase)", 3)
	_opt_apparatus.add_item("5. Soxhlet Continuous Extractor", 4)
	_opt_apparatus.add_item("6. UV-Vis Spectrophotometer", 5)
	_opt_apparatus.add_item("7. Inert Atmosphere Glovebox", 6)
	_opt_apparatus.add_item("8. High-Speed Centrifuge", 7)
	_opt_apparatus.add_item("9. Separatory Funnel (500 mL)", 8)
	_opt_apparatus.add_item("10. NMR Spectrometer (500 MHz)", 9)
	_opt_apparatus.add_item("11. Magnetic Stirrer & Hotplate", 10)
	_opt_apparatus.add_item("12. Ducted Fume Hood (Class II)", 11)
	_opt_apparatus.add_item("13. Micropipette Set & Carousel", 12)
	_opt_apparatus.item_selected.connect(_on_apparatus_selected)
	header.add_child(_opt_apparatus)

	var btn_hub := Button.new()
	btn_hub.text = "← Lab Hub"
	btn_hub.position = Vector2(1140, 16)
	btn_hub.custom_minimum_size = Vector2(110, 36)
	btn_hub.pressed.connect(func(): get_tree().change_scene_to_file(HUB_SCENE))
	header.add_child(btn_hub)

	# Left Column: Step-by-Step Guidance & Interactive Controls
	var left_panel := PanelContainer.new()
	left_panel.position = Vector2(24, 84)
	left_panel.size = Vector2(400, 610)
	var lp_style := StyleBoxFlat.new()
	lp_style.bg_color = PANEL
	lp_style.border_width_left = 1
	lp_style.border_width_top = 1
	lp_style.border_width_right = 1
	lp_style.border_width_bottom = 1
	lp_style.border_color = Color(0.18, 0.28, 0.35, 0.6)
	lp_style.content_margin_left = 16
	lp_style.content_margin_top = 14
	lp_style.content_margin_right = 16
	lp_style.content_margin_bottom = 14
	left_panel.add_theme_stylebox_override("panel", lp_style)
	add_child(left_panel)

	var left_vbox := VBoxContainer.new()
	left_vbox.add_theme_constant_override("separation", 12)
	left_panel.add_child(left_vbox)

	var lbl_step_title := Label.new()
	lbl_step_title.text = "STANDARD OPERATING PROCEDURE (SOP)"
	lbl_step_title.add_theme_font_size_override("font_size", 13)
	lbl_step_title.add_theme_color_override("font_color", CYAN)
	left_vbox.add_child(lbl_step_title)

	_instructions_label = RichTextLabel.new()
	_instructions_label.custom_minimum_size = Vector2(368, 200)
	_instructions_label.bbcode_enabled = true
	_instructions_label.scroll_active = true
	left_vbox.add_child(_instructions_label)

	var sep1 := HSeparator.new()
	left_vbox.add_child(sep1)

	var lbl_ctrl_title := Label.new()
	lbl_ctrl_title.text = "PHYSICAL INSTRUMENT ACTUATORS"
	lbl_ctrl_title.add_theme_font_size_override("font_size", 12)
	lbl_ctrl_title.add_theme_color_override("font_color", AMBER)
	left_vbox.add_child(lbl_ctrl_title)

	_controls_vbox = VBoxContainer.new()
	_controls_vbox.add_theme_constant_override("separation", 8)
	left_vbox.add_child(_controls_vbox)

	# Center Viewport Area (Graph & 3D Interactive Model Rendering)
	var center_panel := Panel.new()
	center_panel.position = Vector2(440, 84)
	center_panel.size = Vector2(480, 610)
	var cp_style := StyleBoxFlat.new()
	cp_style.bg_color = PANEL_INSET
	cp_style.border_width_left = 1
	cp_style.border_width_top = 1
	cp_style.border_width_right = 1
	cp_style.border_width_bottom = 1
	cp_style.border_color = Color(0.18, 0.28, 0.35, 0.8)
	center_panel.add_theme_stylebox_override("panel", cp_style)
	add_child(center_panel)

	# 3D Viewport Setup for Apparatus Model Inspection
	_viewport_container = SubViewportContainer.new()
	_viewport_container.position = Vector2(4, 4)
	_viewport_container.size = Vector2(472, 350)
	_viewport_container.stretch = true
	center_panel.add_child(_viewport_container)

	_sub_viewport = SubViewport.new()
	_sub_viewport.size = Vector2i(472, 350)
	_sub_viewport.transparent_bg = true
	_sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_viewport_container.add_child(_sub_viewport)

	var stage_3d := Node3D.new()
	_sub_viewport.add_child(stage_3d)

	var cam := Camera3D.new()
	cam.position = Vector3(0, 0.40, 1.25)
	cam.look_at_from_position(cam.position, Vector3(0, 0.28, 0))
	cam.fov = 42.0
	stage_3d.add_child(cam)

	var key_light := DirectionalLight3D.new()
	key_light.rotation = Vector3(-0.55, 0.65, 0)
	key_light.light_color = Color(0.96, 0.98, 1.0)
	key_light.light_energy = 1.25
	stage_3d.add_child(key_light)

	var fill_light := DirectionalLight3D.new()
	fill_light.rotation = Vector3(0.4, -2.4, 0)
	fill_light.light_color = Color(0.35, 0.55, 0.75)
	fill_light.light_energy = 0.5
	stage_3d.add_child(fill_light)

	_turntable = Node3D.new()
	stage_3d.add_child(_turntable)

	# Right Column: Live Physics, Telemetry & Local AI Reaction Advisor
	var right_panel := PanelContainer.new()
	right_panel.position = Vector2(936, 84)
	right_panel.size = Vector2(320, 610)
	var rp_style := StyleBoxFlat.new()
	rp_style.bg_color = PANEL
	rp_style.border_width_left = 1
	rp_style.border_width_top = 1
	rp_style.border_width_right = 1
	rp_style.border_width_bottom = 1
	rp_style.border_color = Color(0.18, 0.28, 0.35, 0.6)
	rp_style.content_margin_left = 14
	rp_style.content_margin_top = 14
	rp_style.content_margin_right = 14
	rp_style.content_margin_bottom = 14
	right_panel.add_theme_stylebox_override("panel", rp_style)
	add_child(right_panel)

	var right_vbox := VBoxContainer.new()
	right_vbox.add_theme_constant_override("separation", 10)
	right_panel.add_child(right_vbox)

	var lbl_phys_title := Label.new()
	lbl_phys_title.text = "PHYSICAL STATE & KINETICS"
	lbl_phys_title.add_theme_font_size_override("font_size", 12)
	lbl_phys_title.add_theme_color_override("font_color", GREEN)
	right_vbox.add_child(lbl_phys_title)

	_status_box = RichTextLabel.new()
	_status_box.custom_minimum_size = Vector2(290, 160)
	_status_box.bbcode_enabled = true
	right_vbox.add_child(_status_box)

	var sep2 := HSeparator.new()
	right_vbox.add_child(sep2)

	var lbl_theory_title := Label.new()
	lbl_theory_title.text = "THERMODYNAMIC MODEL"
	lbl_theory_title.add_theme_font_size_override("font_size", 12)
	lbl_theory_title.add_theme_color_override("font_color", BLUE)
	right_vbox.add_child(lbl_theory_title)

	_physics_panel = RichTextLabel.new()
	_physics_panel.custom_minimum_size = Vector2(290, 170)
	_physics_panel.bbcode_enabled = true
	right_vbox.add_child(_physics_panel)

	var sep3 := HSeparator.new()
	right_vbox.add_child(sep3)

	_btn_ai_advisor = Button.new()
	_btn_ai_advisor.text = "💡 Consult AI Reaction Advisor"
	_btn_ai_advisor.custom_minimum_size = Vector2(290, 34)
	_btn_ai_advisor.pressed.connect(_on_ai_advisor_pressed)
	right_vbox.add_child(_btn_ai_advisor)

	_ai_advice_label = RichTextLabel.new()
	_ai_advice_label.custom_minimum_size = Vector2(290, 130)
	_ai_advice_label.bbcode_enabled = true
	_ai_advice_label.text = "[color=#758895]Click above for real-time AI guidance on this apparatus.[/color]"
	right_vbox.add_child(_ai_advice_label)

func _on_apparatus_selected(idx: int) -> void:
	_switch_apparatus(idx as ApparatusType)

func _switch_apparatus(type: ApparatusType) -> void:
	_current_type = type
	_update_3d_model()
	_rebuild_controls()
	_update_instructions()
	_update_theory_panel()
	_ai_advice_label.text = "[color=#758895]Awaiting AI inquiry...[/color]"

func _update_3d_model() -> void:
	if _turntable == null:
		return
	for c in _turntable.get_children():
		c.queue_free()

	if APPARATUS_MODELS.has(_current_type):
		var path = str(APPARATUS_MODELS[_current_type])
		if ResourceLoader.exists(path):
			var packed = load(path) as PackedScene
			if packed != null:
				var inst = packed.instantiate()
				if inst != null:
					var s: Vector3 = APPARATUS_SCALES.get(_current_type, Vector3.ONE)
					inst.scale = s
					_turntable.add_child(inst)

func _rebuild_controls() -> void:
	for c in _controls_vbox.get_children():
		c.queue_free()

	match _current_type:
		ApparatusType.ROTOVAP:
			_add_toggle_button("Keck Clip Attached", _rotovap.keck_clip_secured, func(v): _rotovap.secure_keck_clip(v))
			_add_toggle_button("Water Bath Lift", _rotovap.bath_raised, func(v): _rotovap.toggle_bath_lift(v))
			_add_toggle_button("Vacuum Stopcock Closed", _rotovap.stopcock_closed, func(v):
				_rotovap.set_stopcock(v)
				if v: _rotovap.state = Suite.RotovapController.State.DISTILLING
			)
			_add_slider("Rotation Speed (RPM)", 0, 200, _rotovap.rotation_target_rpm, func(v): _rotovap.rotation_target_rpm = v)
			_add_slider("Water Bath Temp (°C)", 20, 80, _rotovap.bath_target_c, func(v): _rotovap.bath_target_c = v)
			_add_slider("Vacuum Target (mbar)", 20, 1013, _rotovap.vacuum_target_mbar, func(v): _rotovap.vacuum_target_mbar = v)
		ApparatusType.SCHLENK:
			_add_toggle_button("Cold Trap Filled (-196°C LN2)", _schlenk.cold_trap_filled_ln2, func(v): _schlenk.fill_cold_trap(v))
			var btn_vac := Button.new()
			btn_vac.text = "Turn Port 0 to VACUUM (Evacuate)"
			btn_vac.pressed.connect(func():
				var res = _schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.VACUUM)
				_update_status_display()
				if res.has("warning"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.warning) + "[/color]"
			)
			_controls_vbox.add_child(btn_vac)

			var btn_inert := Button.new()
			btn_inert.text = "Turn Port 0 to ARGON (Refill)"
			btn_inert.pressed.connect(func():
				_schlenk.set_port_valve(0, Suite.SchlenkLineController.ValvePosition.INERT_GAS)
				_update_status_display()
			)
			_controls_vbox.add_child(btn_inert)
		ApparatusType.BALANCE:
			_add_toggle_button("Draft Shield Doors Closed", _balance.draft_shield_closed, func(v): _balance.set_draft_shield(v))
			var btn_tare := Button.new()
			btn_tare.text = "Zero / Tare Balance (0.0000 g)"
			btn_tare.pressed.connect(func(): _balance.tare())
			_controls_vbox.add_child(btn_tare)
			_add_slider("Place Sample Mass (mg)", 0, 500, 150.0, func(v): _balance.place_mass(v / 1000.0))
		ApparatusType.HPLC:
			_add_toggle_button("Pumps Running", _hplc.is_pumping, func(v): _hplc.start_pumps(v))
			_add_slider("Flow Rate (mL/min)", 0.2, 2.5, _hplc.flow_rate_ml_min, func(v): _hplc.flow_rate_ml_min = v)
			_add_slider("Organic % (Acetonitrile/Water)", 5, 95, _hplc.mobile_phase_b_pct, func(v): _hplc.mobile_phase_b_pct = v)
			var btn_inj := Button.new()
			btn_inj.text = "💉 Inject Sample (Rheodyne 20 µL Loop)"
			btn_inj.pressed.connect(func():
				_last_hplc_result = _hplc.inject_sample("Phenethylamine Mix", [
					{"name": "Uracil (t0)", "logP": -1.07, "concentration_mg_ml": 0.5},
					{"name": "Phenol", "logP": 1.46, "concentration_mg_ml": 1.0},
					{"name": "2C-B Freebase", "logP": 2.85, "concentration_mg_ml": 1.5}
				])
				queue_redraw()
			)
			_controls_vbox.add_child(btn_inj)
		ApparatusType.SOXHLET:
			_add_slider("Heating Mantle Power (%)", 0, 100, _soxhlet.heating_mantle_power_pct, func(v): _soxhlet.heating_mantle_power_pct = v)
			_add_toggle_button("Condenser Cooling Water Flowing", _soxhlet.condenser_water_flowing, func(v): _soxhlet.condenser_water_flowing = v)
		ApparatusType.UVVIS:
			var btn_blank := Button.new()
			btn_blank.text = "Zero / Blank Baseline Solvent"
			btn_blank.pressed.connect(func(): _uvvis.blank_zero())
			_controls_vbox.add_child(btn_blank)

			var btn_scan := Button.new()
			btn_scan.text = "Scan UV-Vis Absorption (200 - 800 nm)"
			btn_scan.pressed.connect(func():
				_last_uvvis_result = _uvvis.scan_absorbance("Luminol Basic Solution", 7800.0, 0.00015, 355.0)
				queue_redraw()
			)
			_controls_vbox.add_child(btn_scan)
		ApparatusType.GLOVEBOX:
			var btn_ante := Button.new()
			btn_ante.text = "Cycle Antechamber (Vacuum-Argon Purge)"
			btn_ante.pressed.connect(func():
				var res = _glovebox.cycle_antechamber()
				_instructions_label.text += "\n[color=#59d99d]" + str(res.status) + "[/color]"
			)
			_controls_vbox.add_child(btn_ante)

			var btn_transfer := Button.new()
			btn_transfer.text = "Transfer Pyrophoric Reagent into Glovebox"
			btn_transfer.pressed.connect(func():
				var res = _glovebox.transfer_item("tert-Butyllithium in Pentane")
				if res.has("warning"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.warning) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Reagent transferred safely under inert atmosphere.[/color]"
			)
			_controls_vbox.add_child(btn_transfer)
		ApparatusType.CENTRIFUGE:
			_add_toggle_button("Opposite Tubes Balanced (±0.01g)", _centrifuge.tubes_balanced, func(v): _centrifuge.set_tubes_balanced(v))
			_add_slider("Target RPM", 1000, 15000, _centrifuge.target_rpm, func(v): _centrifuge.target_rpm = v)
			var btn_spin := Button.new()
			btn_spin.text = "Start Centrifuge Run"
			btn_spin.pressed.connect(func():
				var res = _centrifuge.start(true)
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Rotor at %0.f RPM (RCF: %0.f x g). Pellet separated.[/color]" % [float(res.rpm), float(res.rcf_g_force)]
			)
			_controls_vbox.add_child(btn_spin)
		ApparatusType.SEPFUNNEL:
			_add_toggle_button("Glass Stopper Inserted", _sep_funnel.stopper_on, func(v): _sep_funnel.remove_stopper(not v))
			var btn_shake := Button.new()
			btn_shake.text = "Invert Funnel & Vent Stopcock Away"
			btn_shake.pressed.connect(func():
				var res = _sep_funnel.shake_and_vent()
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Inverted and vented vapor pressure. (Shake #%d)[/color]" % int(res.shaked)
				_update_status_display()
			)
			_controls_vbox.add_child(btn_shake)

			var btn_settle := Button.new()
			btn_settle.text = "Rest in Ring & Settle Emulsion"
			btn_settle.pressed.connect(func():
				var res = _sep_funnel.settle_phases()
				_instructions_label.text += "\n[color=#59d99d]Biphasic boundary sharpened. Partition yield: %.1f%%[/color]" % float(res.efficiency_pct)
				_update_status_display()
			)
			_controls_vbox.add_child(btn_settle)

			var btn_drain := Button.new()
			btn_drain.text = "Open Stopcock: Drain Lower Organic Layer (DCM)"
			btn_drain.pressed.connect(func():
				var res = _sep_funnel.drain_lower_phase(true)
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				elif res.has("warning"):
					_instructions_label.text += "\n[color=#f7a93b]" + str(res.warning) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Drained %.0f mL lower layer. Extracted: %.1f mg atropine.[/color]" % [float(res.drained_ml), float(res.collected_solute_mg)]
				_update_status_display()
			)
			_controls_vbox.add_child(btn_drain)

		ApparatusType.NMR:
			_add_toggle_button("Pneumatic Lift Air Active", _nmr.lift_air_active, func(v):
				_nmr.toggle_lift_air(v)
				_update_status_display()
			)
			_add_toggle_button("Sample Tube in Bore Stator", _nmr.sample_inserted, func(v):
				var res = _nmr.insert_sample(v)
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				_update_status_display()
			)
			_add_toggle_button("Sample Spinning (20 Hz)", _nmr.spinner_spinning, func(v):
				_nmr.toggle_spinning(v)
				_update_status_display()
			)
			var btn_lock := Button.new()
			btn_lock.text = "Engage 2H Lock (CDCl3)"
			btn_lock.pressed.connect(func():
				var res = _nmr.engage_lock()
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Deuterium frequency lock stabilized (98.4%%).[/color]"
				_update_status_display()
			)
			_controls_vbox.add_child(btn_lock)

			var btn_shim := Button.new()
			btn_shim.text = "Execute Gradient Autoshim (Z1-Z4)"
			btn_shim.pressed.connect(func():
				var res = _nmr.execute_autoshim()
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Field homogeneity optimized. Linewidth: %.2f Hz[/color]" % float(res.linewidth_hz)
				_update_status_display()
			)
			_controls_vbox.add_child(btn_shim)

			var btn_nmr_scan := Button.new()
			btn_nmr_scan.text = "Acquire 1H-NMR Spectrum (500 MHz, 16 Scans)"
			btn_nmr_scan.pressed.connect(func():
				_last_nmr_result = _nmr.acquire_1h_spectrum("Atropine Pure", [
					{"shift_ppm": 7.30, "multiplicity": "m", "integral": 5, "label": "Aromatic Ar-H"},
					{"shift_ppm": 5.05, "multiplicity": "t", "integral": 1, "label": "C3-H (tropine)"},
					{"shift_ppm": 4.18, "multiplicity": "dd", "integral": 1, "label": "CH2-OH"},
					{"shift_ppm": 3.75, "multiplicity": "m", "integral": 1, "label": "CH-Ar"},
					{"shift_ppm": 2.95, "multiplicity": "br s", "integral": 2, "label": "Bridgehead N-CH"},
					{"shift_ppm": 2.22, "multiplicity": "s", "integral": 3, "label": "N-CH3"}
				])
				_instructions_label.text += "\n[color=#59d99d]FID collected and Fourier transformed. 6 resonance multiplets resolved.[/color]"
				queue_redraw()
			)
			_controls_vbox.add_child(btn_nmr_scan)

		ApparatusType.STIRRER:
			_add_toggle_button("Heating Element Active", _stirrer.heating_enabled, func(v):
				_stirrer.set_heat(_stirrer.plate_target_temp_c, v)
				_update_status_display()
			)
			_add_slider("Target Temp (°C)", 20, 300, _stirrer.plate_target_temp_c, func(v):
				_stirrer.set_heat(v, _stirrer.heating_enabled)
			)
			_add_slider("Stirring Speed (RPM)", 0, 1500, _stirrer.target_stirring_rpm, func(v):
				_stirrer.set_stir_speed(v)
			)
			var btn_flea := Button.new()
			btn_flea.text = "Reset / Re-couple Decoupled Stir Flea"
			btn_flea.pressed.connect(func():
				_stirrer.reset_decoupled_flea()
				_instructions_label.text += "\n[color=#59d99d]Stir bar re-centered in magnetic field.[/color]"
				_update_status_display()
			)
			_controls_vbox.add_child(btn_flea)

		ApparatusType.FUMEHOOD:
			_add_toggle_button("Ducted Exhaust Blower", _fume_hood.blower_active, func(v):
				_fume_hood.toggle_blower(v)
				_update_status_display()
			)
			_add_slider("Sash Height (Inches)", 0, 34, _fume_hood.sash_height_inches, func(v):
				var res = _fume_hood.set_sash_height(v)
				if bool(res.get("alarm", false)):
					_instructions_label.text += "\n[color=#ff6050]SASH ALARM: Height exceeds 18\" safety barrier![/color]"
				_update_status_display()
			)

		ApparatusType.MICROPIPETTE:
			var btn_p1000 := Button.new()
			btn_p1000.text = "Select P1000 (100 - 1000 µL)"
			btn_p1000.pressed.connect(func():
				_micropipette.select_model(Suite.MicropipetteSetController.PipetteModel.P1000)
				_rebuild_controls()
				_update_status_display()
			)
			_controls_vbox.add_child(btn_p1000)

			var btn_p200 := Button.new()
			btn_p200.text = "Select P200 (20 - 200 µL)"
			btn_p200.pressed.connect(func():
				_micropipette.select_model(Suite.MicropipetteSetController.PipetteModel.P200)
				_rebuild_controls()
				_update_status_display()
			)
			_controls_vbox.add_child(btn_p200)

			_add_slider("Set Volume (µL)", 20, 200, _micropipette.selected_volume_ul, func(v):
				_micropipette.set_volume(v)
			)
			_add_toggle_button("Disposable Tip Attached", _micropipette.tip_attached, func(v):
				if v: _micropipette.attach_tip()
				else: _micropipette.eject_tip()
				_update_status_display()
			)
			var btn_asp := Button.new()
			btn_asp.text = "Aspirate Liquid (1st Stop In, Immerse, Release)"
			btn_asp.pressed.connect(func():
				var res = _micropipette.aspirate(true)
				if res.has("error"):
					_instructions_label.text += "\n[color=#ff6050]" + str(res.error) + "[/color]"
				else:
					_instructions_label.text += "\n[color=#59d99d]Aspirated %.1f µL into tip without bubbles.[/color]" % float(res.aspirated_ul)
				_update_status_display()
			)
			_controls_vbox.add_child(btn_asp)

			var btn_disp := Button.new()
			btn_disp.text = "Dispense & Blowout (1st -> 2nd Stop)"
			btn_disp.pressed.connect(func():
				var res = _micropipette.dispense(true)
				_instructions_label.text += "\n[color=#59d99d]Delivered %.1f µL (Accuracy: %.1f%%).[/color]" % [float(res.dispensed_ul), float(res.accuracy_pct)]
				_update_status_display()
			)
			_controls_vbox.add_child(btn_disp)

func _add_toggle_button(label: String, initial_state: bool, callback: Callable) -> void:
	var btn := CheckButton.new()
	btn.text = label
	btn.button_pressed = initial_state
	btn.toggled.connect(callback)
	_controls_vbox.add_child(btn)

func _add_slider(label: String, min_v: float, max_v: float, curr_v: float, callback: Callable) -> void:
	var lbl := Label.new()
	lbl.text = "%s: %.1f" % [label, curr_v]
	lbl.add_theme_font_size_override("font_size", 11)
	lbl.add_theme_color_override("font_color", DIM)
	_controls_vbox.add_child(lbl)

	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.value = curr_v
	slider.value_changed.connect(func(v: float):
		lbl.text = "%s: %.1f" % [label, v]
		callback.call(v)
	)
	_controls_vbox.add_child(slider)

func _update_instructions() -> void:
	var t: String = ""
	match _current_type:
		ApparatusType.ROTOVAP:
			t = "[b]ROTARY EVAPORATOR (ROTOVAP)[/b]\n"
			for i in range(Suite.RotovapController.TUTORIAL_STEPS.size()):
				var step_str = Suite.RotovapController.TUTORIAL_STEPS[i]
				if i == _rotovap.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.SCHLENK:
			t = "[b]SCHLENK LINE (INERT ATMOSPHERE MANIFOLD)[/b]\n"
			for i in range(Suite.SchlenkLineController.TUTORIAL_STEPS.size()):
				var step_str = Suite.SchlenkLineController.TUTORIAL_STEPS[i]
				if i == _schlenk.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.BALANCE:
			t = "[b]ANALYTICAL BALANCE (0.1 mg PRECISION)[/b]\n"
			for i in range(Suite.AnalyticalBalanceController.TUTORIAL_STEPS.size()):
				var step_str = Suite.AnalyticalBalanceController.TUTORIAL_STEPS[i]
				if i == _balance.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.HPLC:
			t = "[b]HPLC DIODE ARRAY CHROMATOGRAPH[/b]\n"
			t += "[color=#41d9a8]▶ 1. Equilibrate C18 column with mobile phase gradient\n"
			t += "▶ 2. Verify backpressure is stable (< 350 bar)\n"
			t += "▶ 3. Inject analyte through 20 µL Rheodyne sample loop\n"
			t += "▶ 4. Monitor retention times: Uracil (t0), Phenol, and target phenethylamines[/color]"
		ApparatusType.SOXHLET:
			t = "[b]SOXHLET CONTINUOUS EXTRACTOR[/b]\n"
			t += "[color=#41d9a8]▶ 1. Load cellulose thimble with botanical powdered matrix\n"
			t += "▶ 2. Ensure condenser coolant is actively circulating\n"
			t += "▶ 3. Heat solvent flask until reflux siphons automatically every 3-5 min\n"
			t += "▶ 4. Continue until solvent in siphon tube runs clear (> 95% yield)[/color]"
		ApparatusType.UVVIS:
			t = "[b]UV-VIS SPECTROPHOTOMETER[/b]\n"
			t += "[color=#41d9a8]▶ 1. Warm up deuterium (UV) and tungsten-halogen (Vis) lamps\n"
			t += "▶ 2. Insert blank cuvette (pure solvent) and execute baseline zero\n"
			t += "▶ 3. Insert sample quartz cuvette (1.0 cm pathlength)\n"
			t += "▶ 4. Record absorbance and verify linearity within 0.1 - 1.5 AU[/color]"
		ApparatusType.GLOVEBOX:
			t = "[b]HERMETIC GLOVEBOX (<0.1 ppm O2/H2O)[/b]\n"
			t += "[color=#41d9a8]▶ 1. Check O2 and H2O sensors read below 0.1 ppm\n"
			t += "▶ 2. Place reagents in antechamber and run 3x purge cycles\n"
			t += "▶ 3. Open inner door only after full cycle completion\n"
			t += "▶ 4. Perform pyrophoric or moisture-sensitive organometallic transfers[/color]"
		ApparatusType.CENTRIFUGE:
			t = "[b]HIGH-SPEED REFRIGERATED CENTRIFUGE[/b]\n"
			t += "[color=#41d9a8]▶ 1. Weigh opposite tubes on balance to within ±0.01 g\n"
			t += "▶ 2. Load rotor in symmetrical geometric balance\n"
			t += "▶ 3. Lock chamber lid and select desired RPM / RCF\n"
			t += "▶ 4. Allow rotor to decelerate without brake to protect fragile pellets[/color]"
		ApparatusType.SEPFUNNEL:
			t = "[b]SEPARATORY FUNNEL (500 mL LIQUID-LIQUID EXTRACTION)[/b]\n"
			for i in range(Suite.SeparatoryFunnelController.TUTORIAL_STEPS.size()):
				var step_str = Suite.SeparatoryFunnelController.TUTORIAL_STEPS[i]
				if i == _sep_funnel.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.NMR:
			t = "[b]SUPERCONDUCTING NMR SPECTROMETER (500 MHz)[/b]\n"
			for i in range(Suite.NMRSpectrometerController.TUTORIAL_STEPS.size()):
				var step_str = Suite.NMRSpectrometerController.TUTORIAL_STEPS[i]
				if i == _nmr.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.STIRRER:
			t = "[b]DIGITAL MAGNETIC STIRRER & CERAMIC HOTPLATE[/b]\n"
			for i in range(Suite.MagneticStirrerController.TUTORIAL_STEPS.size()):
				var step_str = Suite.MagneticStirrerController.TUTORIAL_STEPS[i]
				if i == _stirrer.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.FUMEHOOD:
			t = "[b]DUCTED CLASS II AERODYNAMIC FUME HOOD[/b]\n"
			for i in range(Suite.FumeHoodController.TUTORIAL_STEPS.size()):
				var step_str = Suite.FumeHoodController.TUTORIAL_STEPS[i]
				if i == _fume_hood.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
		ApparatusType.MICROPIPETTE:
			t = "[b]PRECISION MICROPIPETTE SET & TIP CAROUSEL[/b]\n"
			for i in range(Suite.MicropipetteSetController.TUTORIAL_STEPS.size()):
				var step_str = Suite.MicropipetteSetController.TUTORIAL_STEPS[i]
				if i == _micropipette.tutorial_step:
					t += "[color=#41d9a8]▶ %s[/color]\n" % step_str
				else:
					t += "[color=#758895]  %s[/color]\n" % step_str
	_instructions_label.text = t

func _update_status_display() -> void:
	var t: String = ""
	match _current_type:
		ApparatusType.ROTOVAP:
			var s = _rotovap.get_status()
			t += "[b]State:[/b] %s\n" % str(s.get("state", "OFF"))
			t += "[b]Bath Temp:[/b] %.1f °C (Target %.1f °C)\n" % [float(s.get("bath_temp_c", 0.0)), _rotovap.bath_target_c]
			t += "[b]Chiller Temp:[/b] %.1f °C\n" % float(s.get("chiller_temp_c", 0.0))
			t += "[b]Pressure:[/b] %.1f mbar (Vacuum)\n" % float(s.get("vacuum_mbar", 1013.25))
			t += "[b]Rotation:[/b] %.0f RPM\n" % float(s.get("rotation_rpm", 0.0))
			t += "[b]Distillation Rate:[/b] %.2f mL/min\n" % float(s.get("distillation_rate_ml_min", 0.0))
			t += "[b]Distillate Collected:[/b] %.1f mL\n" % float(s.get("collected_distillate_ml", 0.0))
		ApparatusType.SCHLENK:
			var s = _schlenk.get_status()
			t += "[b]Cold Trap (-196°C LN2):[/b] %s\n" % ("READY" if bool(s.get("cold_trap_ready", false)) else "NOT FILLED - HAZARD")
			t += "[b]Argon Overpressure:[/b] %.1f psi\n" % float(s.get("argon_pressure_psi", 0.0))
			t += "[b]Oil Bubbler Rate:[/b] %.1f bubbles/sec\n" % float(s.get("oil_bubbler_rate_bps", 1.0))
			t += "[b]Port 0 Residual O2:[/b] [color=#41d9a8]%.1f ppm[/color]\n" % float(s.get("port_0_o2_ppm", 209000.0))
			t += "[b]Port 0 Purge Cycles:[/b] %d / 3 (%s)\n" % [int(s.get("port_0_purge_cycles", 0)), "INERT" if bool(s.get("port_0_purged", false)) else "ATMOSPHERIC"]
		ApparatusType.BALANCE:
			var s = _balance.get_reading()
			t += "[b]Mass Display:[/b] [color=#41d9a8]%.4f g[/color]\n" % float(s.get("displayed_mass_g", 0.0))
			t += "[b]Reading Stable (○):[/b] %s\n" % ("YES" if bool(s.get("is_stable", false)) else "NO (Air Draft)")
			t += "[b]Draft Shield Closed:[/b] %s\n" % ("YES" if bool(s.get("draft_shield_closed", false)) else "NO")
		ApparatusType.HPLC:
			t += "[b]System Status:[/b] %s\n" % ("PUMPING" if _hplc.is_pumping else "IDLE")
			t += "[b]Flow Rate:[/b] %.2f mL/min\n" % _hplc.flow_rate_ml_min
			t += "[b]Mobile Phase B:[/b] %.1f %% Acetonitrile\n" % _hplc.mobile_phase_b_pct
			t += "[b]System Pressure:[/b] %.1f bar\n" % _hplc.backpressure_bar
			if not _last_hplc_result.is_empty():
				t += "[b]Injected Sample:[/b] %s\n" % str(_last_hplc_result.get("sample", ""))
				var peaks = _last_hplc_result.get("peaks", [])
				t += "[b]Detected Peaks:[/b] %d resolved\n" % peaks.size()
		ApparatusType.SOXHLET:
			var s = _soxhlet.get_status()
			t += "[b]Siphon Chamber Fill:[/b] %d %%\n" % int(s.get("siphon_chamber_fill_pct", 0))
			t += "[b]Completed Siphon Dumps:[/b] %d\n" % int(s.get("siphon_cycles", 0))
			t += "[b]Extracted Active Analyte:[/b] %.1f mg\n" % float(s.get("extracted_analyte_mg", 0.0))
			t += "[b]Extraction Recovery Yield:[/b] [color=#41d9a8]%.1f %%[/color]\n" % float(s.get("recovery_percentage", 0.0))
		ApparatusType.UVVIS:
			t += "[b]Baseline Blanked:[/b] %s\n" % ("YES" if _uvvis.is_blanked else "NO - CALIBRATION REQUIRED")
			t += "[b]Cuvette Pathlength:[/b] %.1f cm (Quartz)\n" % _uvvis.cuvette_pathlength_cm
			if not _last_uvvis_result.is_empty():
				t += "[b]Sample:[/b] %s\n" % str(_last_uvvis_result.get("compound", ""))
				t += "[b]λ max:[/b] %.0f nm\n" % float(_last_uvvis_result.get("lambda_max_nm", 0.0))
				t += "[b]Absorbance at λ max:[/b] [color=#41d9a8]%.3f AU[/color]\n" % float(_last_uvvis_result.get("absorbance_at_lambda_max", 0.0))
		ApparatusType.GLOVEBOX:
			t += "[b]Oxygen Level:[/b] [color=#41d9a8]%.3f ppm[/color]\n" % _glovebox.o2_ppm
			t += "[b]Moisture Level:[/b] [color=#41d9a8]%.3f ppm[/color]\n" % _glovebox.h2o_ppm
			t += "[b]Chamber Pressure:[/b] +%.1f mbar (Overpressure)\n" % _glovebox.chamber_pressure_mbar
			t += "[b]Antechamber Purged:[/b] %s (%d cycles)\n" % ["YES" if _glovebox.antechamber_purged else "NO", _glovebox.antechamber_purge_cycles]
		ApparatusType.CENTRIFUGE:
			t += "[b]Rotor Speed:[/b] %.0f RPM\n" % _centrifuge.rpm
			var rcf = 1.118e-5 * _centrifuge.rotor_radius_cm * pow(_centrifuge.rpm, 2.0)
			t += "[b]Relative Centrifugal Field:[/b] %.0f x g\n" % rcf
			t += "[b]Rotor Balance:[/b] %s\n" % ("BALANCED" if _centrifuge.tubes_balanced else "IMBALANCED - CUTOFF TRIGGERED")
		ApparatusType.SEPFUNNEL:
			var s = _sep_funnel.get_status()
			t += "[b]Stopper Position:[/b] %s\n" % ("INSERTED" if bool(s.get("stopper_on", true)) else "REMOVED (READY TO DRAIN)")
			t += "[b]Stopcock Status:[/b] %s\n" % ("OPEN" if bool(s.get("stopcock_open", false)) else "CLOSED")
			t += "[b]Organic Volume (DCM):[/b] %.0f mL\n" % float(s.get("organic_ml", 0.0))
			t += "[b]Aqueous Volume:[/b] %.0f mL\n" % float(s.get("aqueous_ml", 0.0))
			t += "[b]Partition Coeff (Kd):[/b] %.1f\n" % float(s.get("kd", 0.0))
			t += "[b]Extracted Atropine:[/b] [color=#41d9a8]%.1f mg[/color]\n" % float(s.get("extracted_mg", 0.0))
		ApparatusType.NMR:
			var s = _nmr.get_status()
			t += "[b]Magnetic Field:[/b] %.3f Tesla (500 MHz 1H)\n" % float(s.get("field_tesla", 11.74))
			t += "[b]Cryogens:[/b] He: %.1f%% · N2: %.1f%%\n" % [float(s.get("he_level", 0.0)), float(s.get("n2_level", 0.0))]
			t += "[b]Sample in Stator:[/b] %s\n" % ("YES" if bool(s.get("sample_in", false)) else "EMPTY")
			t += "[b]Spinning (20 Hz):[/b] %s\n" % ("ACTIVE (1200 RPM)" if bool(s.get("spinning", false)) else "OFF")
			t += "[b]Deuterium Lock:[/b] %s\n" % ("LOCKED (CDCl3)" if bool(s.get("locked", false)) else "UNLOCKED")
			t += "[b]Peak Linewidth:[/b] [color=#41d9a8]%.2f Hz[/color]\n" % float(s.get("linewidth", 1.8))
		ApparatusType.STIRRER:
			var s = _stirrer.get_status()
			t += "[b]Hotplate Surface:[/b] %.1f °C (Target %.0f °C)\n" % [float(s.get("plate_temp", 20.0)), float(s.get("target_plate_temp", 20.0))]
			t += "[b]Solution Temp (PT1000):[/b] [color=#41d9a8]%.1f °C[/color]\n" % float(s.get("solution_temp", 20.0))
			t += "[b]Stir Speed:[/b] %.0f RPM (Target %.0f RPM)\n" % [float(s.get("stirring_rpm", 0.0)), float(s.get("target_rpm", 0.0))]
			t += "[b]Stir Flea Coupling:[/b] %s\n" % ("COUPLED & STABLE" if not bool(s.get("decoupled", false)) else "[color=#ff6050]DECOUPLED / RATTLING[/color]")
		ApparatusType.FUMEHOOD:
			var s = _fume_hood.get_status()
			t += "[b]Blower Fan:[/b] %s\n" % ("RUNNING" if bool(s.get("blower", true)) else "[color=#ff6050]OFFLINE[/color]")
			t += "[b]Face Inflow Velocity:[/b] [color=#41d9a8]%.0f FPM[/color] (OSHA 80-120)\n" % float(s.get("velocity_fpm", 100.0))
			t += "[b]Sash Position:[/b] %.1f inches\n" % float(s.get("sash_inches", 18.0))
			t += "[b]Sash Safety Alarm:[/b] %s\n" % ("[color=#ff6050]ALARM ACTIVE[/color]" if bool(s.get("alarm", false)) else "NORMAL")
		ApparatusType.MICROPIPETTE:
			var s = _micropipette.get_status()
			t += "[b]Selected Pipette:[/b] %s\n" % str(s.get("model", "P200"))
			t += "[b]Dialed Volume:[/b] [color=#41d9a8]%.1f µL[/color]\n" % float(s.get("volume_ul", 100.0))
			t += "[b]Tip Mounted:[/b] %s\n" % ("YES (Polypropylene)" if bool(s.get("tip_attached", false)) else "NO TIP")
			t += "[b]Liquid in Tip:[/b] %.1f µL\n" % float(s.get("aspirated_ul", 0.0))
	_status_box.text = t

func _update_theory_panel() -> void:
	var t: String = ""
	match _current_type:
		ApparatusType.ROTOVAP:
			t = "[b]Clausius-Clapeyron Equation:[/b]\n"
			t += "ln(P2/P1) = -(ΔHvap / R) * (1/T2 - 1/T1)\n\n"
			t += "Lowering pressure to 45 mbar lowers ethanol boiling point from 78.4°C down to 26.2°C, enabling gentle, non-destructive desolvation."
		ApparatusType.SCHLENK:
			t = "[b]Gas Dynamics & Fick's Diffusion:[/b]\n"
			t += "PV = nRT · Dilution Ratio = (P_vac / P_atm)^N\n\n"
			t += "Three cycles to 0.05 mbar followed by 1013 mbar argon reduces residual O2 to 1.2 * 10^-13 atmospheres (sub-ppm)."
		ApparatusType.BALANCE:
			t = "[b]Electromagnetic Force Compensation:[/b]\n"
			t += "F = I * L * B · Thermal draft velocity creates up to 2.4 mg buoyancy offset with open shield."
		ApparatusType.HPLC:
			t = "[b]van Deemter Efficiency Equation:[/b]\n"
			t += "HETP = A + B/u + C*u\n\n"
			t += "Hydrophobic partition k' ∝ exp(0.8 * logP). High logP compounds retain longer on C18 stationary phase."
		ApparatusType.SOXHLET:
			t = "[b]Continuous Extraction Kinetics:[/b]\n"
			t += "C_extracted(t) = C_inf * (1 - exp(-k * N_cycles))\n\n"
			t += "Fresh redistilled reflux solvent continuously washes ground matrix, pushing partition equilibrium to 99%+ recovery."
		ApparatusType.UVVIS:
			t = "[b]Beer-Lambert Law:[/b]\n"
			t += "A = ε * c * l = -log10(I / I0)\n\n"
			t += "Absorbance scales linearly with molar attenuation ε and path length l (1.0 cm standard quartz cuvette)."
		ApparatusType.GLOVEBOX:
			t = "[b]Copper Catalyst & Molecular Sieve Regeneration:[/b]\n"
			t += "2Cu + O2 -> 2CuO (reduced by H2/Ar at 200°C)\n"
			t += "Zeolite 4A traps trace moisture down to <0.05 ppm."
		ApparatusType.CENTRIFUGE:
			t = "[b]Relative Centrifugal Field (RCF):[/b]\n"
			t += "RCF = 1.118 * 10^-5 * r_cm * RPM^2\n\n"
			t += "At 14,000 RPM (r=8.5 cm), particles experience 18,600 x g, pelleted by Stokes' Law velocity."
		ApparatusType.SEPFUNNEL:
			t = "[b]Nernst Partition Law & Multi-Stage Extraction:[/b]\n"
			t += "Kd = [Solute]_org / [Solute]_aq\n\n"
			t += "Fraction extracted = 1 - (Va / (Va + Kd*Vo))^n. Three small extractions always isolate more compound than one large extraction volume."
		ApparatusType.NMR:
			t = "[b]Bloch Equations & Nuclear Larmor Precession:[/b]\n"
			t += "ω0 = γ * B0 · Chemical Shift δ = (ν - ν_ref) / ν_spectrometer * 10^6 ppm\n\n"
			t += "Proton nuclear spins align with 11.74 T superconducting field. RF pulse tips magnetization vector into transverse plane for FID decay."
		ApparatusType.STIRRER:
			t = "[b]Convective Fluid Vortex & Heat Transfer:[/b]\n"
			t += "Nu = 0.037 * Re^0.8 * Pr^(1/3)\n\n"
			t += "High-shear magnetic vortex accelerates solid dissolution and maintains uniform thermal boundaries without hotspot crystallization."
		ApparatusType.FUMEHOOD:
			t = "[b]Bernoulli Fluid Dynamics & Face Velocity:[/b]\n"
			t += "P + 1/2 * ρ * v^2 = constant\n\n"
			t += "Aerodynamic airfoil sill eliminates boundary layer turbulence, preventing room air draft backwash into the operator breathing zone."
		ApparatusType.MICROPIPETTE:
			t = "[b]Air Displacement & Capillary Hydrodynamics:[/b]\n"
			t += "ΔV = A * Δx · Capillary Rise h = 2γ cosθ / (ρ g r)\n\n"
			t += "Piston displacement creates precise internal partial vacuum, drawing calibrated liquid column into sterile polypropylene tip."
	_physics_panel.text = t

func _on_ai_advisor_pressed() -> void:
	var advisor = get_node_or_null("/root/LocalAIReactionAdvisor")
	var app_name = _get_apparatus_slug()
	_ai_advice_label.text = "[color=#f7a93b]Querying Local AI Reaction Advisor...[/color]"

	if advisor and advisor.has_method("get_apparatus_guidance"):
		var guidance = advisor.get_apparatus_guidance(app_name, "active_operation")
		var prompt_text = "[color=#41d9a8][b]AI Advisor Response:[/b][/color]\n"
		for k in guidance.keys():
			prompt_text += "[b]%s:[/b] %s\n" % [str(k).capitalize(), str(guidance[k])]
		_ai_advice_label.text = prompt_text
	else:
		_ai_advice_label.text = "[color=#41d9a8][b]Heuristic Guidance:[/b][/color]\nEnsure GHS hazard criteria are satisfied, PPE is equipped, and glassware joint grease is chemically inert."

func _get_apparatus_slug() -> String:
	match _current_type:
		ApparatusType.ROTOVAP: return "rotovap"
		ApparatusType.SCHLENK: return "schlenk_line"
		ApparatusType.BALANCE: return "analytical_balance"
		ApparatusType.HPLC: return "hplc"
		ApparatusType.SOXHLET: return "soxhlet"
		ApparatusType.UVVIS: return "uvvis"
		ApparatusType.GLOVEBOX: return "glovebox"
		ApparatusType.CENTRIFUGE: return "centrifuge"
		ApparatusType.SEPFUNNEL: return "separatory_funnel"
		ApparatusType.NMR: return "nmr_spectrometer"
		ApparatusType.STIRRER: return "magnetic_stirrer"
		ApparatusType.FUMEHOOD: return "fume_hood"
		ApparatusType.MICROPIPETTE: return "micropipette"
		_: return "apparatus"

func _draw() -> void:
	var telemetry_rect := Rect2(448, 436, 464, 250)

	match _current_type:
		ApparatusType.HPLC:
			_draw_hplc_chromatogram(telemetry_rect)
		ApparatusType.UVVIS:
			_draw_uvvis_spectrum(telemetry_rect)
		ApparatusType.NMR:
			_draw_nmr_spectrum(telemetry_rect)
		_:
			_draw_analog_gauges(telemetry_rect)

func _draw_hplc_chromatogram(rect: Rect2) -> void:
	draw_rect(rect, Color(0.018, 0.026, 0.035, 1.0))
	for y_step in range(6):
		var y = rect.position.y + y_step * (rect.size.y / 5.0)
		draw_line(Vector2(rect.position.x, y), Vector2(rect.end.x, y), Color(0.12, 0.18, 0.22, 0.5), 1.0)
	for x_step in range(6):
		var x = rect.position.x + x_step * (rect.size.x / 5.0)
		draw_line(Vector2(x, rect.position.y), Vector2(x, rect.end.y), Color(0.12, 0.18, 0.22, 0.5), 1.0)

	var points := PackedVector2Array()
	var base_y = rect.end.y - 24.0
	for px in range(int(rect.size.x) - 40):
		var t = float(px) / (rect.size.x - 40.0) * 120.0
		var absorb = 0.015 + 0.005 * sin(t * 0.2)
		absorb += 0.45 * exp(-pow(t - 18.0, 2) / 4.0)
		absorb += 0.85 * exp(-pow(t - 45.0, 2) / 8.0)
		absorb += 1.35 * exp(-pow(t - 88.0, 2) / 12.0)

		var py = base_y - absorb * (rect.size.y * 0.55)
		points.append(Vector2(rect.position.x + 20.0 + px, py))

	if points.size() > 1:
		draw_polyline(points, CYAN, 2.0)

	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.position.y + 24), "HPLC DIODE ARRAY TRACE (λ = 254 nm)", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.end.y - 8), "Time (seconds) →  [0s to 120s gradient elution]", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)

func _draw_uvvis_spectrum(rect: Rect2) -> void:
	draw_rect(rect, Color(0.018, 0.026, 0.035, 1.0))
	for y_step in range(6):
		var y = rect.position.y + y_step * (rect.size.y / 5.0)
		draw_line(Vector2(rect.position.x, y), Vector2(rect.end.x, y), Color(0.12, 0.18, 0.22, 0.5), 1.0)
	for x_step in range(6):
		var x = rect.position.x + x_step * (rect.size.x / 5.0)
		draw_line(Vector2(x, rect.position.y), Vector2(x, rect.end.y), Color(0.12, 0.18, 0.22, 0.5), 1.0)

	var base_y = rect.end.y - 24.0
	var points := PackedVector2Array()

	for px in range(int(rect.size.x) - 40):
		var wl = 200.0 + (float(px) / (rect.size.x - 40.0)) * 600.0
		var a = 0.02
		a += 0.95 * exp(-pow(wl - 355.0, 2) / 450.0)
		a += 0.65 * exp(-pow(wl - 300.0, 2) / 300.0)
		var py = base_y - a * (rect.size.y * 0.60)
		points.append(Vector2(rect.position.x + 20.0 + px, py))

	if points.size() > 1:
		draw_polyline(points, GREEN, 2.0)

	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.position.y + 24), "UV-VIS ABSORPTION SPECTRUM: LUMINOL", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, GREEN)
	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.end.y - 8), "Wavelength λ (nm) →  [200 nm to 800 nm]", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)

func _draw_analog_gauges(rect: Rect2) -> void:
	draw_rect(rect, Color(0.018, 0.026, 0.035, 1.0))
	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.position.y + 24), "ACTIVE APPARATUS METROLOGY & PRESSURE TELEMETRY", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, CYAN)

	# Left Gauge: Primary Metrology Dial
	var center1 := Vector2(rect.position.x + rect.size.x * 0.28, rect.position.y + 130)
	draw_circle(center1, 56, Color(0.04, 0.06, 0.08, 1.0))
	draw_arc(center1, 56, 0, TAU, 48, Color(0.2, 0.3, 0.4, 0.8), 2.0)

	var angle1 = -PI * 0.75 + (sin(_sim_timer * 1.5) * 0.5 + 0.5) * PI * 1.5
	var needle_end1 = center1 + Vector2(cos(angle1), sin(angle1)) * 46.0
	draw_line(center1, needle_end1, AMBER, 2.5)
	draw_circle(center1, 6, AMBER)
	draw_string(ThemeDB.fallback_font, Vector2(center1.x - 70, center1.y + 76), "PRIMARY SENSOR", HORIZONTAL_ALIGNMENT_CENTER, 140, 10, DIM)

	# Right Gauge: Flow & Rotation Gauge
	var center2 := Vector2(rect.position.x + rect.size.x * 0.72, rect.position.y + 130)
	draw_circle(center2, 56, Color(0.04, 0.06, 0.08, 1.0))
	draw_arc(center2, 56, 0, TAU, 48, Color(0.2, 0.3, 0.4, 0.8), 2.0)

	var angle2 = -PI * 0.75 + (cos(_sim_timer * 2.1) * 0.5 + 0.5) * PI * 1.5
	var needle_end2 = center2 + Vector2(cos(angle2), sin(angle2)) * 46.0
	draw_line(center2, needle_end2, CYAN, 2.5)
	draw_circle(center2, 6, CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(center2.x - 70, center2.y + 76), "FLOW / ROTATION", HORIZONTAL_ALIGNMENT_CENTER, 140, 10, DIM)

func _draw_nmr_spectrum(rect: Rect2) -> void:
	draw_rect(rect, Color(0.015, 0.022, 0.032, 1.0))
	for y_step in range(5):
		var y = rect.position.y + y_step * (rect.size.y / 4.0)
		draw_line(Vector2(rect.position.x, y), Vector2(rect.end.x, y), Color(0.10, 0.16, 0.20, 0.5), 1.0)
	for x_step in range(11):
		var x = rect.position.x + x_step * (rect.size.x / 10.0)
		draw_line(Vector2(x, rect.position.y), Vector2(x, rect.end.y), Color(0.10, 0.16, 0.20, 0.5), 1.0)

	var base_y = rect.end.y - 28.0
	var points := PackedVector2Array()
	# Chemical shift ppm axis runs 10 ppm (left) to 0 ppm (right)
	for px in range(int(rect.size.x) - 40):
		var ppm = 10.0 - (float(px) / (rect.size.x - 40.0) * 10.0)
		var intensity = 0.008 + 0.003 * sin(ppm * 50.0)
		# Atropine peaks
		intensity += 1.40 * exp(-pow((ppm - 7.30) / 0.06, 2)) # Ar-H
		intensity += 0.85 * exp(-pow((ppm - 5.05) / 0.03, 2)) # C3-H
		intensity += 0.95 * exp(-pow((ppm - 4.18) / 0.04, 2)) # CH2-OH
		intensity += 0.70 * exp(-pow((ppm - 3.75) / 0.04, 2)) # CH-Ar
		intensity += 0.65 * exp(-pow((ppm - 2.95) / 0.05, 2)) # N-CH
		intensity += 1.25 * exp(-pow((ppm - 2.22) / 0.02, 2)) # N-CH3
		intensity += 1.80 * exp(-pow((ppm - 7.26) / 0.01, 2)) # CDCl3 residual solvent

		var py = base_y - intensity * (rect.size.y * 0.45)
		points.append(Vector2(rect.position.x + 20.0 + px, py))

	if points.size() > 1:
		draw_polyline(points, AMBER, 2.0)

	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.position.y + 24), "1H-NMR FOURIER TRANSFORM SPECTRUM (500.13 MHz · CDCl3)", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, AMBER)
	draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + 16, rect.end.y - 8), "Chemical Shift δ (ppm) ← [10.0 ppm down to 0.0 ppm TMS reference]", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)
