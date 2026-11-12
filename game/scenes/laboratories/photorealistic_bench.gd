# Athanor Ascension — Photorealistic Laboratory Bench Scene Controller
# Reference Visual Architecture: beispiel1.jpg, beispiel2.jpg, beispiel3.jpg
#
# Real-time PBR photorealistic laboratory environment with:
# 1. Chemical-resistant reflective black epoxy benchtop with PBR reflections.
# 2. Fractional Distillation Rig: Vigreux column, Liebig condenser, cooling hoses,
#    Keck clips, iron retort clamp stand, take-off adapter, receiver on lab jack.
# 3. Precision Analytical Balance: 4-decimal readout, glass draft shield, tare.
# 4. Digital Magnetic Stirrer & Hotplate: IKA-style blue chassis, white ceramic top,
#    dual 7-segment LED displays (Temp °C, RPM), rotary knobs, Rankine vortex.
# 5. Bench Accessories: Wooden test tube rack, porcelain dishes, crucible tongs, scoopula.
# 6. GHS / NFPA Hazard Warning Placards on laboratory wall.
# 7. 3D Spatial Annotation Labels & Floating Action Guide Arrows.
# 8. Responsive UI sidebar & reagent actuators connected to Synthesis Catalog.

extends Control
class_name PhotorealisticBench

const HUB_SCENE: String = "res://scenes/laboratories/lab_hub.tscn"
const Catalog = preload("res://scripts/labs/synthesis_catalog.gd")
const Chem = preload("res://scripts/labs/synthesis_chemistry.gd")

const GLASS_SHADER = preload("res://shaders/glass_shader.gdshader")
const LIQUID_SHADER = preload("res://shaders/liquid_shader.gdshader")

# Color Palette (Athanor High-Tech UI & PBR)
const COLOR_BG: Color = Color(0.024, 0.032, 0.042, 1.0)
const COLOR_PANEL: Color = Color(0.045, 0.060, 0.078, 0.95)
const COLOR_PANEL_HEADER: Color = Color(0.060, 0.082, 0.105, 0.98)
const COLOR_CYAN: Color = Color(0.24, 0.85, 0.92, 1.0)
const COLOR_AMBER: Color = Color(1.0, 0.72, 0.28, 1.0)
const COLOR_GREEN: Color = Color(0.38, 0.86, 0.65, 1.0)
const COLOR_RED: Color = Color(1.0, 0.38, 0.34, 1.0)
const COLOR_TEXT: Color = Color(0.88, 0.92, 0.95, 1.0)
const COLOR_DIM: Color = Color(0.52, 0.62, 0.70, 1.0)
const COLOR_BLUE_IKA: Color = Color(0.08, 0.28, 0.65, 1.0)
const COLOR_EPOXY_BENCH: Color = Color(0.05, 0.055, 0.062, 1.0)
const COLOR_CERAMIC_WHITE: Color = Color(0.96, 0.96, 0.95, 1.0)
const COLOR_HOSE_ORANGE: Color = Color(0.95, 0.58, 0.12, 1.0)
const COLOR_BRASS: Color = Color(0.82, 0.68, 0.25, 1.0)
const COLOR_STAINLESS: Color = Color(0.85, 0.86, 0.88, 1.0)
const COLOR_WOOD: Color = Color(0.78, 0.55, 0.32, 1.0)

# Runtime Apparatus Simulation State
var current_protocol: Dictionary = {}
var is_stirring: bool = false
var stir_rpm: float = 0.0
var target_stir_rpm: float = 450.0
var mantle_temp_c: float = 21.5
var target_temp_c: float = 78.4
var balance_mass_g: float = 0.0000
var balance_tared: bool = false
var is_boiling: bool = false
var condensate_flow_rate: float = 0.0 # mL/min
var distillate_collected_ml: float = 0.0
var sim_time: float = 0.0

# Active Reagent on Bench
var active_reagent_name: String = "Ethanol / Water 1:1"
var active_protocol_id: String = "limonene_citrus_steam_distillation"

# 3D Node References
var _sub_viewport: SubViewport
var _camera: Camera3D
var _world_root: Node3D
var _distillation_flask_liquid: MeshInstance3D
var _stir_bar: MeshInstance3D
var _condenser_vapor: MeshInstance3D
var _receiver_liquid: MeshInstance3D
var _balance_display_mesh: MeshInstance3D
var _stirrer_temp_display: Label3D
var _stirrer_rpm_display: Label3D
var _balance_weight_display: Label3D
var _guide_arrow: Node3D

# UI References
var _lbl_header_stirrer: Label
var _lbl_header_temp: Label
var _lbl_header_status: Label
var _lbl_balance_readout: Label
var _log_console: RichTextLabel
var _opt_protocol: OptionButton

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_load_initial_protocol()
	_setup_3d_viewport_and_scene()
	_setup_ui_overlay()
	set_process(true)

func _load_initial_protocol() -> void:
	current_protocol = Catalog.get_protocol("limonene_citrus_steam_distillation")
	if current_protocol.is_empty():
		current_protocol = Catalog.get_protocol("aspirin")

func _process(delta: float) -> void:
	sim_time += delta
	_update_physical_thermodynamics(delta)
	_update_displays(delta)

# =============================================================================
# 1. 3D PHYSICAL SCENE & PBR BENCHTOP GENERATION
# =============================================================================

func _setup_3d_viewport_and_scene() -> void:
	var vp_container := SubViewportContainer.new()
	vp_container.name = "ViewportContainer"
	vp_container.set_anchors_preset(Control.PRESET_FULL_RECT)
	vp_container.stretch = true
	add_child(vp_container)

	_sub_viewport = SubViewport.new()
	_sub_viewport.name = "LaboratoryViewport"
	_sub_viewport.size = Vector2i(1280, 720)
	_sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp_container.add_child(_sub_viewport)

	_world_root = Node3D.new()
	_world_root.name = "BenchSceneRoot"
	_sub_viewport.add_child(_world_root)

	_setup_environment_and_lighting()
	_build_room_and_bench()
	_build_fractional_distillation_rig()
	_build_analytical_balance_station()
	_build_magnetic_stirrer_station()
	_build_wooden_test_tube_rack()
	_build_benchtop_accessories()
	_build_wall_ghs_placards()
	_build_3d_spatial_labels()
	_build_guide_arrow()

func _setup_environment_and_lighting() -> void:
	# Camera Setup (First-Person Laboratory View matching beispiel1, 2, 3)
	_camera = Camera3D.new()
	_camera.name = "LabCamera"
	_camera.position = Vector3(0.0, 0.48, 0.95)
	_camera.look_at_from_position(_camera.position, Vector3(0.0, 0.28, -0.05))
	_camera.fov = 48.0
	_world_root.add_child(_camera)

	# WorldEnvironment with ACES Tonemapping & Subtle Glow
	var env_node := WorldEnvironment.new()
	env_node.name = "WorldEnv"
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.85, 0.88, 0.92, 1.0) # Clean white clinical daylight
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.78, 0.82, 0.88, 1.0)
	env.ambient_light_energy = 0.65
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.05
	env.glow_enabled = true
	env.glow_intensity = 0.25
	env.glow_bloom = 0.05
	env_node.environment = env
	_world_root.add_child(env_node)

	# Key Laboratory Ceiling Fluorescent Fixture (Clean 5500 K white)
	var key_light := DirectionalLight3D.new()
	key_light.name = "CeilingKeyLight"
	key_light.rotation_degrees = Vector3(-55.0, 30.0, 0.0)
	key_light.light_color = Color(0.98, 0.99, 1.0)
	key_light.light_energy = 1.35
	key_light.shadow_enabled = true
	_world_root.add_child(key_light)

	# Bench Practical Spotlight (Warm task illumination over distillation & balance)
	var bench_spot := OmniLight3D.new()
	bench_spot.name = "BenchTaskLight"
	bench_spot.position = Vector3(0.0, 1.10, 0.20)
	bench_spot.light_color = Color(1.0, 0.98, 0.95)
	bench_spot.light_energy = 1.50
	bench_spot.omni_range = 3.5
	bench_spot.omni_attenuation = 1.0
	_world_root.add_child(bench_spot)

func _build_room_and_bench() -> void:
	# 1. Reflective Black Epoxy Lab Countertop (Matching beispiel1.jpg)
	var bench_mesh := BoxMesh.new()
	bench_mesh.size = Vector3(3.2, 0.08, 1.4)
	var bench_inst := MeshInstance3D.new()
	bench_inst.name = "EpoxyCountertop"
	bench_inst.mesh = bench_mesh
	bench_inst.position = Vector3(0.0, 0.0, 0.0)

	var mat_bench := StandardMaterial3D.new()
	mat_bench.albedo_color = COLOR_EPOXY_BENCH
	mat_bench.metallic = 0.15
	mat_bench.roughness = 0.12 # Deep glossy mirror reflection of glassware
	mat_bench.metallic_specular = 0.85
	bench_inst.material_override = mat_bench
	_world_root.add_child(bench_inst)

	# Countertop Front Wood Edging Strip (Beispiel 1 aesthetic)
	var edge_mesh := BoxMesh.new()
	edge_mesh.size = Vector3(3.2, 0.08, 0.04)
	var edge_inst := MeshInstance3D.new()
	edge_inst.mesh = edge_mesh
	edge_inst.position = Vector3(0.0, 0.0, 0.72)
	var mat_wood := StandardMaterial3D.new()
	mat_wood.albedo_color = COLOR_WOOD
	mat_wood.roughness = 0.55
	edge_inst.material_override = mat_wood
	_world_root.add_child(edge_inst)

	# 2. Laboratory Rear Wall (Satin composite tiles)
	var wall_mesh := QuadMesh.new()
	wall_mesh.size = Vector2(4.5, 2.2)
	var wall_inst := MeshInstance3D.new()
	wall_inst.name = "LabRearWall"
	wall_inst.mesh = wall_mesh
	wall_inst.position = Vector3(0.0, 0.85, -0.65)
	var mat_wall := StandardMaterial3D.new()
	mat_wall.albedo_color = Color(0.78, 0.82, 0.84, 1.0)
	mat_wall.roughness = 0.40
	wall_inst.material_override = mat_wall
	_world_root.add_child(wall_inst)

	# 3. Upper Laboratory Cabinets (Top of beispiel1.jpg)
	var cab_mesh := BoxMesh.new()
	cab_mesh.size = Vector3(3.6, 0.45, 0.38)
	var cab_inst := MeshInstance3D.new()
	cab_inst.mesh = cab_mesh
	cab_inst.position = Vector3(0.0, 1.55, -0.45)
	var mat_cab := StandardMaterial3D.new()
	mat_cab.albedo_color = Color(0.92, 0.93, 0.94)
	mat_cab.roughness = 0.35
	cab_inst.material_override = mat_cab
	_world_root.add_child(cab_inst)

# =============================================================================
# 2. FRACTIONAL DISTILLATION APPARATUS (beispiel1.jpg)
# =============================================================================

func _build_fractional_distillation_rig() -> void:
	var rig_root := Node3D.new()
	rig_root.name = "FractionalDistillationRig"
	rig_root.position = Vector3(-0.10, 0.04, 0.0)
	_world_root.add_child(rig_root)

	# Heating Mantle / Stirrer Base (Light blue / grey chassis)
	var mantle_body := BoxMesh.new()
	mantle_body.size = Vector3(0.24, 0.10, 0.24)
	var mantle_inst := MeshInstance3D.new()
	mantle_inst.mesh = mantle_body
	mantle_inst.position = Vector3(-0.15, 0.05, 0.0)
	var mat_mantle := StandardMaterial3D.new()
	mat_mantle.albedo_color = Color(0.62, 0.72, 0.80)
	mat_mantle.roughness = 0.4
	mantle_inst.material_override = mat_mantle
	rig_root.add_child(mantle_inst)

	# Mantle Front Dual Rotary Knobs
	for kx in [-0.05, 0.05]:
		var knob_mesh := CylinderMesh.new()
		knob_mesh.top_radius = 0.016
		knob_mesh.bottom_radius = 0.016
		knob_mesh.height = 0.014
		var knob_inst := MeshInstance3D.new()
		knob_inst.mesh = knob_mesh
		knob_inst.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		knob_inst.position = Vector3(-0.15 + kx, 0.04, 0.125)
		var mat_knob := StandardMaterial3D.new()
		mat_knob.albedo_color = Color(0.75, 0.82, 0.88)
		knob_inst.material_override = mat_knob
		rig_root.add_child(knob_inst)

	# Heating Top Plate (White porcelain / ceramic)
	var plate_mesh := CylinderMesh.new()
	plate_mesh.top_radius = 0.09
	plate_mesh.bottom_radius = 0.09
	plate_mesh.height = 0.012
	var plate_inst := MeshInstance3D.new()
	plate_inst.mesh = plate_mesh
	plate_inst.position = Vector3(-0.15, 0.105, 0.0)
	var mat_plate := StandardMaterial3D.new()
	mat_plate.albedo_color = COLOR_CERAMIC_WHITE
	mat_plate.roughness = 0.2
	plate_inst.material_override = mat_plate
	rig_root.add_child(plate_inst)

	# Round-Bottom Boiling Flask (500 mL)
	var rbf_mesh := SphereMesh.new()
	rbf_mesh.radius = 0.065
	rbf_mesh.height = 0.13
	var rbf_inst := MeshInstance3D.new()
	rbf_inst.name = "RoundBottomFlask"
	rbf_inst.mesh = rbf_mesh
	rbf_inst.position = Vector3(-0.15, 0.165, 0.0)
	var mat_glass := StandardMaterial3D.new()
	mat_glass.albedo_color = Color(0.92, 0.96, 1.0, 0.20)
	mat_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_glass.roughness = 0.04
	mat_glass.metallic = 0.1
	rbf_inst.material_override = mat_glass
	rig_root.add_child(rbf_inst)

	# Liquid inside Round-Bottom Flask
	var liq_mesh := SphereMesh.new()
	liq_mesh.radius = 0.058
	liq_mesh.height = 0.075
	_distillation_flask_liquid = MeshInstance3D.new()
	_distillation_flask_liquid.name = "BoilingLiquid"
	_distillation_flask_liquid.mesh = liq_mesh
	_distillation_flask_liquid.position = Vector3(-0.15, 0.145, 0.0)
	var mat_liq := StandardMaterial3D.new()
	mat_liq.albedo_color = Color(0.35, 0.65, 0.85, 0.70)
	mat_liq.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_liq.roughness = 0.05
	_distillation_flask_liquid.material_override = mat_liq
	rig_root.add_child(_distillation_flask_liquid)

	# Vertical Vigreux Distillation Column with Glass Indentations
	var vig_mesh := CylinderMesh.new()
	vig_mesh.top_radius = 0.016
	vig_mesh.bottom_radius = 0.016
	vig_mesh.height = 0.34
	var vig_inst := MeshInstance3D.new()
	vig_inst.mesh = vig_mesh
	vig_inst.position = Vector3(-0.15, 0.38, 0.0)
	vig_inst.material_override = mat_glass
	rig_root.add_child(vig_inst)

	# Indentation rings on Vigreux column
	for ring_idx in range(6):
		var ring_m := TorusMesh.new()
		ring_m.inner_radius = 0.012
		ring_m.outer_radius = 0.019
		var ring_i := MeshInstance3D.new()
		ring_i.mesh = ring_m
		ring_i.position = Vector3(-0.15, 0.26 + float(ring_idx) * 0.045, 0.0)
		ring_i.material_override = mat_glass
		rig_root.add_child(ring_i)

	# Distillation Still Head with Thermometer Adapter
	var head_mesh := CylinderMesh.new()
	head_mesh.top_radius = 0.015
	head_mesh.bottom_radius = 0.015
	head_mesh.height = 0.09
	var head_inst := MeshInstance3D.new()
	head_inst.mesh = head_mesh
	head_inst.position = Vector3(-0.15, 0.58, 0.0)
	head_inst.material_override = mat_glass
	rig_root.add_child(head_inst)

	# Thermometer Stem & Red Alcohol Bulb
	var thermo_mesh := CylinderMesh.new()
	thermo_mesh.top_radius = 0.003
	thermo_mesh.bottom_radius = 0.003
	thermo_mesh.height = 0.16
	var thermo_inst := MeshInstance3D.new()
	thermo_inst.mesh = thermo_mesh
	thermo_inst.position = Vector3(-0.15, 0.60, 0.0)
	var mat_thermo := StandardMaterial3D.new()
	mat_thermo.albedo_color = Color(1.0, 0.95, 0.95, 0.6)
	mat_thermo.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	thermo_inst.material_override = mat_thermo
	rig_root.add_child(thermo_inst)

	# Liebig Condenser (Outer Cooling Water Jacket angled down at 22°)
	var cond_angle := -22.0
	var cond_len := 0.38
	var cond_mesh := CylinderMesh.new()
	cond_mesh.top_radius = 0.024
	cond_mesh.bottom_radius = 0.024
	cond_mesh.height = cond_len
	var cond_inst := MeshInstance3D.new()
	cond_inst.mesh = cond_mesh
	cond_inst.rotation_degrees = Vector3(0.0, 0.0, cond_angle)
	cond_inst.position = Vector3(0.02, 0.49, 0.0)
	cond_inst.material_override = mat_glass
	rig_root.add_child(cond_inst)

	# Inner Vapor Tube of Condenser
	var inner_tube := CylinderMesh.new()
	inner_tube.top_radius = 0.008
	inner_tube.bottom_radius = 0.008
	inner_tube.height = cond_len + 0.04
	_condenser_vapor = MeshInstance3D.new()
	_condenser_vapor.mesh = inner_tube
	_condenser_vapor.rotation_degrees = Vector3(0.0, 0.0, cond_angle)
	_condenser_vapor.position = Vector3(0.02, 0.49, 0.0)
	var mat_vapor := StandardMaterial3D.new()
	mat_vapor.albedo_color = Color(0.90, 0.95, 1.0, 0.35)
	mat_vapor.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_condenser_vapor.material_override = mat_vapor
	rig_root.add_child(_condenser_vapor)

	# Iron Retort Stand Base Plate & Rod
	var stand_base_mesh := BoxMesh.new()
	stand_base_mesh.size = Vector3(0.24, 0.025, 0.16)
	var stand_base := MeshInstance3D.new()
	stand_base.mesh = stand_base_mesh
	stand_base.position = Vector3(0.06, 0.015, -0.05)
	var mat_castiron := StandardMaterial3D.new()
	mat_castiron.albedo_color = Color(0.20, 0.22, 0.24)
	mat_castiron.metallic = 0.7
	mat_castiron.roughness = 0.45
	stand_base.material_override = mat_castiron
	rig_root.add_child(stand_base)

	var rod_mesh := CylinderMesh.new()
	rod_mesh.top_radius = 0.007
	rod_mesh.bottom_radius = 0.007
	rod_mesh.height = 0.72
	var rod_inst := MeshInstance3D.new()
	rod_inst.mesh = rod_mesh
	rod_inst.position = Vector3(0.06, 0.38, -0.05)
	var mat_rod := StandardMaterial3D.new()
	mat_rod.albedo_color = COLOR_STAINLESS
	mat_rod.metallic = 0.9
	mat_rod.roughness = 0.25
	rod_inst.material_override = mat_rod
	rig_root.add_child(rod_inst)

	# Clamp Arms with Amber/Yellow Keck Clips (beispiel1.jpg)
	for cy in [0.44, 0.52]:
		var clamp_mesh := BoxMesh.new()
		clamp_mesh.size = Vector3(0.06, 0.022, 0.025)
		var clamp_inst := MeshInstance3D.new()
		clamp_inst.mesh = clamp_mesh
		clamp_inst.position = Vector3(0.06, cy, -0.02)
		var mat_clamp := StandardMaterial3D.new()
		mat_clamp.albedo_color = COLOR_AMBER
		mat_clamp.roughness = 0.3
		clamp_inst.material_override = mat_clamp
		rig_root.add_child(clamp_inst)

	# Realistic Flexible Orange/Yellow Water Hoses (beispiel1.jpg)
	# Water Inlet (Bottom, cold in) and Water Outlet (Top, warm out)
	for hose_data in [
		{"pos": Vector3(0.15, 0.32, 0.0), "h": 0.26, "rot": Vector3(10.0, 0.0, 15.0)},
		{"pos": Vector3(-0.02, 0.36, 0.0), "h": 0.30, "rot": Vector3(-8.0, 0.0, -10.0)}
	]:
		var hose_mesh := CylinderMesh.new()
		hose_mesh.top_radius = 0.012
		hose_mesh.bottom_radius = 0.012
		hose_mesh.height = float(hose_data["h"])
		var hose_inst := MeshInstance3D.new()
		hose_inst.mesh = hose_mesh
		hose_inst.position = Vector3(hose_data["pos"])
		hose_inst.rotation_degrees = Vector3(hose_data["rot"])
		var mat_hose := StandardMaterial3D.new()
		mat_hose.albedo_color = COLOR_HOSE_ORANGE
		mat_hose.roughness = 0.4
		hose_inst.material_override = mat_hose
		rig_root.add_child(hose_inst)

	# Vacuum Adapter / Distillate Take-off leading down
	var adapter_mesh := CylinderMesh.new()
	adapter_mesh.top_radius = 0.012
	adapter_mesh.bottom_radius = 0.012
	adapter_mesh.height = 0.12
	var adapter_inst := MeshInstance3D.new()
	adapter_inst.mesh = adapter_mesh
	adapter_inst.position = Vector3(0.24, 0.34, 0.0)
	adapter_inst.material_override = mat_glass
	rig_root.add_child(adapter_inst)

	# Elevated Tripod / Scissor Lab Jack for Receiver (beispiel1.jpg)
	var jack_mesh := CylinderMesh.new()
	jack_mesh.top_radius = 0.055
	jack_mesh.bottom_radius = 0.055
	jack_mesh.height = 0.08
	var jack_inst := MeshInstance3D.new()
	jack_inst.mesh = jack_mesh
	jack_inst.position = Vector3(0.24, 0.04, 0.0)
	jack_inst.material_override = mat_castiron
	rig_root.add_child(jack_inst)

	# Receiver Graduated Cylinder / Flask
	var rec_mesh := CylinderMesh.new()
	rec_mesh.top_radius = 0.018
	rec_mesh.bottom_radius = 0.018
	rec_mesh.height = 0.16
	var rec_inst := MeshInstance3D.new()
	rec_inst.mesh = rec_mesh
	rec_inst.position = Vector3(0.24, 0.16, 0.0)
	rec_inst.material_override = mat_glass
	rig_root.add_child(rec_inst)

	# Distillate Liquid in Receiver
	var dist_mesh := CylinderMesh.new()
	dist_mesh.top_radius = 0.016
	dist_mesh.bottom_radius = 0.016
	dist_mesh.height = 0.06
	_receiver_liquid = MeshInstance3D.new()
	_receiver_liquid.mesh = dist_mesh
	_receiver_liquid.position = Vector3(0.24, 0.11, 0.0)
	var mat_dist := StandardMaterial3D.new()
	mat_dist.albedo_color = Color(0.85, 0.95, 1.0, 0.65)
	mat_dist.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_dist.roughness = 0.05
	_receiver_liquid.material_override = mat_dist
	rig_root.add_child(_receiver_liquid)

# =============================================================================
# 3. ANALYTICAL BALANCE STATION (beispiel2 & 3)
# =============================================================================

func _build_analytical_balance_station() -> void:
	var bal_root := Node3D.new()
	bal_root.name = "AnalyticalBalanceStation"
	bal_root.position = Vector3(0.65, 0.04, 0.05)
	_world_root.add_child(bal_root)

	# White/Light Grey Plastic Housing Base
	var base_mesh := BoxMesh.new()
	base_mesh.size = Vector3(0.26, 0.065, 0.32)
	var base_inst := MeshInstance3D.new()
	base_inst.mesh = base_mesh
	base_inst.position = Vector3(0.0, 0.032, 0.0)
	var mat_bal_chassis := StandardMaterial3D.new()
	mat_bal_chassis.albedo_color = Color(0.92, 0.93, 0.95)
	mat_bal_chassis.roughness = 0.3
	base_inst.material_override = mat_bal_chassis
	bal_root.add_child(base_inst)

	# Glass Draft Shield Chamber (Sliding glass doors)
	var shield_mesh := BoxMesh.new()
	shield_mesh.size = Vector3(0.22, 0.22, 0.20)
	var shield_inst := MeshInstance3D.new()
	shield_inst.mesh = shield_mesh
	shield_inst.position = Vector3(0.0, 0.175, -0.03)
	var mat_shield := StandardMaterial3D.new()
	mat_shield.albedo_color = Color(0.90, 0.96, 1.0, 0.18)
	mat_shield.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_shield.roughness = 0.05
	shield_inst.material_override = mat_shield
	bal_root.add_child(shield_inst)

	# Circular Stainless Steel Weighing Pan
	var pan_mesh := CylinderMesh.new()
	pan_mesh.top_radius = 0.045
	pan_mesh.bottom_radius = 0.045
	pan_mesh.height = 0.005
	var pan_inst := MeshInstance3D.new()
	pan_inst.mesh = pan_mesh
	pan_inst.position = Vector3(0.0, 0.075, -0.03)
	var mat_pan := StandardMaterial3D.new()
	mat_pan.albedo_color = COLOR_STAINLESS
	mat_pan.metallic = 0.95
	mat_pan.roughness = 0.15
	pan_inst.material_override = mat_pan
	bal_root.add_child(pan_inst)

	# Sloped Front Bezel with Digital Display (beispiel3.jpg: "0 g")
	var bezel_mesh := BoxMesh.new()
	bezel_mesh.size = Vector3(0.24, 0.03, 0.09)
	var bezel_inst := MeshInstance3D.new()
	bezel_inst.mesh = bezel_mesh
	bezel_inst.rotation_degrees = Vector3(25.0, 0.0, 0.0)
	bezel_inst.position = Vector3(0.0, 0.045, 0.11)
	var mat_bezel := StandardMaterial3D.new()
	mat_bezel.albedo_color = Color(0.85, 0.88, 0.90)
	mat_bezel.roughness = 0.35
	bezel_inst.material_override = mat_bezel
	bal_root.add_child(bezel_inst)

	# 3D Digital Label Readout on Balance Face
	_balance_weight_display = Label3D.new()
	_balance_weight_display.text = "0.0000 g"
	_balance_weight_display.font_size = 28
	_balance_weight_display.modulate = Color(0.05, 0.10, 0.15, 1.0)
	_balance_weight_display.outline_modulate = Color(0.9, 0.95, 0.9, 1.0)
	_balance_weight_display.rotation_degrees = Vector3(-65.0, 0.0, 0.0)
	_balance_weight_display.position = Vector3(0.0, 0.065, 0.11)
	bal_root.add_child(_balance_weight_display)

# =============================================================================
# 4. DIGITAL MAGNETIC STIRRER & HOTPLATE STATION (beispiel2 & 3)
# =============================================================================

func _build_magnetic_stirrer_station() -> void:
	var stirrer_root := Node3D.new()
	stirrer_root.name = "MagneticStirrerStation"
	stirrer_root.position = Vector3(0.05, 0.04, 0.18)
	_world_root.add_child(stirrer_root)

	# Royal Blue Die-Cast Chassis (IKA / Scilogex style)
	var body_mesh := BoxMesh.new()
	body_mesh.size = Vector3(0.22, 0.09, 0.26)
	var body_inst := MeshInstance3D.new()
	body_inst.mesh = body_mesh
	body_inst.position = Vector3(0.0, 0.045, 0.0)
	var mat_body := StandardMaterial3D.new()
	mat_body.albedo_color = COLOR_BLUE_IKA
	mat_body.metallic = 0.25
	mat_body.roughness = 0.35
	body_inst.material_override = mat_body
	stirrer_root.add_child(body_inst)

	# White Solid Ceramic Heating Plate Top
	var plate_mesh := CylinderMesh.new()
	plate_mesh.top_radius = 0.085
	plate_mesh.bottom_radius = 0.085
	plate_mesh.height = 0.015
	var plate_inst := MeshInstance3D.new()
	plate_inst.mesh = plate_mesh
	plate_inst.position = Vector3(0.0, 0.098, -0.03)
	var mat_plate := StandardMaterial3D.new()
	mat_plate.albedo_color = COLOR_CERAMIC_WHITE
	mat_plate.roughness = 0.15
	plate_inst.material_override = mat_plate
	stirrer_root.add_child(plate_inst)

	# PTFE White Magnetic Stirrer Flea / Bar
	var flea_mesh := CylinderMesh.new()
	flea_mesh.top_radius = 0.005
	flea_mesh.bottom_radius = 0.005
	flea_mesh.height = 0.035
	_stir_bar = MeshInstance3D.new()
	_stir_bar.name = "MagneticStirBar"
	_stir_bar.mesh = flea_mesh
	_stir_bar.rotation_degrees = Vector3(0.0, 0.0, 90.0)
	_stir_bar.position = Vector3(0.0, 0.11, -0.03)
	var mat_flea := StandardMaterial3D.new()
	mat_flea.albedo_color = Color(0.98, 0.98, 0.98)
	_stir_bar.material_override = mat_flea
	stirrer_root.add_child(_stir_bar)

	# Beaker sitting on Stirrer with Liquid
	var bk_mesh := CylinderMesh.new()
	bk_mesh.top_radius = 0.05
	bk_mesh.bottom_radius = 0.05
	bk_mesh.height = 0.12
	var bk_inst := MeshInstance3D.new()
	bk_inst.mesh = bk_mesh
	bk_inst.position = Vector3(0.0, 0.165, -0.03)
	var mat_bk_glass := StandardMaterial3D.new()
	mat_bk_glass.albedo_color = Color(0.90, 0.95, 1.0, 0.22)
	mat_bk_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_bk_glass.roughness = 0.03
	bk_inst.material_override = mat_bk_glass
	stirrer_root.add_child(bk_inst)

	# Dual Knurled Rotary Control Knobs
	for kx in [-0.055, 0.055]:
		var k_mesh := CylinderMesh.new()
		k_mesh.top_radius = 0.018
		k_mesh.bottom_radius = 0.018
		k_mesh.height = 0.018
		var k_inst := MeshInstance3D.new()
		k_inst.mesh = k_mesh
		k_inst.rotation_degrees = Vector3(65.0, 0.0, 0.0)
		k_inst.position = Vector3(kx, 0.045, 0.125)
		var mat_k := StandardMaterial3D.new()
		mat_k.albedo_color = Color(0.15, 0.35, 0.70)
		k_inst.material_override = mat_k
		stirrer_root.add_child(k_inst)

	# Dual Red 7-Segment LED Displays (beispiel2: "123.2", "250")
	_stirrer_temp_display = Label3D.new()
	_stirrer_temp_display.text = "78.4"
	_stirrer_temp_display.font_size = 22
	_stirrer_temp_display.modulate = Color(1.0, 0.25, 0.20, 1.0) # Glowing Red LED
	_stirrer_temp_display.rotation_degrees = Vector3(-45.0, 0.0, 0.0)
	_stirrer_temp_display.position = Vector3(-0.048, 0.075, 0.095)
	stirrer_root.add_child(_stirrer_temp_display)

	_stirrer_rpm_display = Label3D.new()
	_stirrer_rpm_display.text = "450"
	_stirrer_rpm_display.font_size = 22
	_stirrer_rpm_display.modulate = Color(1.0, 0.25, 0.20, 1.0)
	_stirrer_rpm_display.rotation_degrees = Vector3(-45.0, 0.0, 0.0)
	_stirrer_rpm_display.position = Vector3(0.048, 0.075, 0.095)
	stirrer_root.add_child(_stirrer_rpm_display)

	# Immersion Thermocouple Sensor Rod & Wire dipping into beaker (beispiel2 & 3)
	var probe_stem := CylinderMesh.new()
	probe_stem.top_radius = 0.0025
	probe_stem.bottom_radius = 0.0025
	probe_stem.height = 0.22
	var probe_inst := MeshInstance3D.new()
	probe_inst.mesh = probe_stem
	probe_inst.position = Vector3(0.08, 0.20, -0.01)
	probe_inst.rotation_degrees = Vector3(0.0, 0.0, -12.0)
	var mat_probe := StandardMaterial3D.new()
	mat_probe.albedo_color = COLOR_STAINLESS
	mat_probe.metallic = 0.9
	probe_inst.material_override = mat_probe
	stirrer_root.add_child(probe_inst)

# =============================================================================
# 5. BENCHTOP ACCESSORIES & WOODEN TEST TUBE RACK (beispiel2 & 3)
# =============================================================================

func _build_wooden_test_tube_rack() -> void:
	var rack_root := Node3D.new()
	rack_root.name = "WoodenTestTubeRack"
	rack_root.position = Vector3(-0.55, 0.04, 0.18)
	_world_root.add_child(rack_root)

	var mat_wood := StandardMaterial3D.new()
	mat_wood.albedo_color = COLOR_WOOD
	mat_wood.roughness = 0.60

	# Bottom Deck
	var deck_mesh := BoxMesh.new()
	deck_mesh.size = Vector3(0.32, 0.012, 0.09)
	var b_deck := MeshInstance3D.new()
	b_deck.mesh = deck_mesh
	b_deck.position = Vector3(0.0, 0.006, 0.0)
	b_deck.material_override = mat_wood
	rack_root.add_child(b_deck)

	# Top Perforated Deck
	var t_deck := MeshInstance3D.new()
	t_deck.mesh = deck_mesh
	t_deck.position = Vector3(0.0, 0.085, 0.0)
	t_deck.material_override = mat_wood
	rack_root.add_child(t_deck)

	# End Uprights
	for ex in [-0.155, 0.155]:
		var end_mesh := BoxMesh.new()
		end_mesh.size = Vector3(0.012, 0.11, 0.09)
		var end_inst := MeshInstance3D.new()
		end_inst.mesh = end_mesh
		end_inst.position = Vector3(ex, 0.055, 0.0)
		end_inst.material_override = mat_wood
		rack_root.add_child(end_inst)

	# Glass Test Tubes with Translucent Reaction Suspensions
	var tube_mesh := CylinderMesh.new()
	tube_mesh.top_radius = 0.009
	tube_mesh.bottom_radius = 0.009
	tube_mesh.height = 0.12
	var mat_tube_glass := StandardMaterial3D.new()
	mat_tube_glass.albedo_color = Color(0.92, 0.96, 1.0, 0.28)
	mat_tube_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA

	for idx in range(5):
		var tx := -0.11 + float(idx) * 0.055
		var tube_inst := MeshInstance3D.new()
		tube_inst.mesh = tube_mesh
		tube_inst.position = Vector3(tx, 0.08, 0.0)
		tube_inst.material_override = mat_tube_glass
		rack_root.add_child(tube_inst)

		# Liquid inside test tube (slightly milky/translucent blue or cloudy white)
		var liq_inner := CylinderMesh.new()
		liq_inner.top_radius = 0.008
		liq_inner.bottom_radius = 0.008
		liq_inner.height = 0.06
		var liq_inst := MeshInstance3D.new()
		liq_inst.mesh = liq_inner
		liq_inst.position = Vector3(tx, 0.05, 0.0)
		var mat_inner := StandardMaterial3D.new()
		mat_inner.albedo_color = Color(0.82, 0.88, 0.95, 0.60)
		mat_inner.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		liq_inst.material_override = mat_inner
		rack_root.add_child(liq_inst)

func _build_benchtop_accessories() -> void:
	# 1. Porcelain Evaporating Dishes with Crystalline Powders (beispiel2 & 3)
	for dx in [-0.35, -0.22]:
		var dish_mesh := CylinderMesh.new()
		dish_mesh.top_radius = 0.038
		dish_mesh.bottom_radius = 0.024
		dish_mesh.height = 0.022
		var dish_inst := MeshInstance3D.new()
		dish_inst.mesh = dish_mesh
		dish_inst.position = Vector3(dx, 0.05, 0.32)
		var mat_dish := StandardMaterial3D.new()
		mat_dish.albedo_color = Color(0.96, 0.96, 0.94)
		dish_inst.material_override = mat_dish
		_world_root.add_child(dish_inst)

		# White Crystalline Powder inside
		var powder_mesh := CylinderMesh.new()
		powder_mesh.top_radius = 0.034
		powder_mesh.bottom_radius = 0.028
		powder_mesh.height = 0.010
		var powder_inst := MeshInstance3D.new()
		powder_inst.mesh = powder_mesh
		powder_inst.position = Vector3(dx, 0.056, 0.32)
		var mat_powder := StandardMaterial3D.new()
		mat_powder.albedo_color = Color(0.98, 0.98, 0.96)
		mat_powder.roughness = 0.85
		powder_inst.material_override = mat_powder
		_world_root.add_child(powder_inst)

	# 2. Stainless Steel Laboratory Spatula / Scoopula (beispiel2 & 3)
	var spat_mesh := BoxMesh.new()
	spat_mesh.size = Vector3(0.18, 0.003, 0.012)
	var spat_inst := MeshInstance3D.new()
	spat_inst.mesh = spat_mesh
	spat_inst.rotation_degrees = Vector3(0.0, 32.0, 0.0)
	spat_inst.position = Vector3(-0.16, 0.042, 0.35)
	var mat_steel := StandardMaterial3D.new()
	mat_steel.albedo_color = COLOR_STAINLESS
	mat_steel.metallic = 0.92
	mat_steel.roughness = 0.20
	spat_inst.material_override = mat_steel
	_world_root.add_child(spat_inst)

	# 3. Laboratory Crucible Tongs in Foreground (beispiel2 & 3)
	var tongs_root := Node3D.new()
	tongs_root.position = Vector3(0.08, 0.042, 0.44)
	tongs_root.rotation_degrees = Vector3(0.0, -15.0, 0.0)
	_world_root.add_child(tongs_root)

	var tong_arm := BoxMesh.new()
	tong_arm.size = Vector3(0.24, 0.006, 0.014)
	var t1 := MeshInstance3D.new()
	t1.mesh = tong_arm
	t1.material_override = mat_steel
	tongs_root.add_child(t1)

	var t2 := MeshInstance3D.new()
	t2.mesh = tong_arm
	t2.position = Vector3(0.0, 0.004, 0.02)
	t2.material_override = mat_steel
	tongs_root.add_child(t2)

# =============================================================================
# 6. GHS HAZARD PLACARDS & 3D SPATIAL LABELS (beispiel1.jpg)
# =============================================================================

func _build_wall_ghs_placards() -> void:
	var placard_specs := [
		{"pos": Vector3(0.70, 0.88, -0.63), "text": "FLAMMABLE", "color": Color(0.95, 0.45, 0.15)},
		{"pos": Vector3(0.88, 0.88, -0.63), "text": "BIOHAZARD", "color": Color(0.95, 0.85, 0.15)},
		{"pos": Vector3(0.70, 0.70, -0.63), "text": "HIGH VOLTAGE", "color": Color(0.95, 0.85, 0.15)},
		{"pos": Vector3(0.88, 0.70, -0.63), "text": "RADIATION", "color": Color(0.95, 0.85, 0.15)},
		{"pos": Vector3(1.06, 0.70, -0.63), "text": "OXIDIZER", "color": Color(0.95, 0.45, 0.15)}
	]

	for spec in placard_specs:
		var quad := QuadMesh.new()
		quad.size = Vector2(0.14, 0.14)
		var inst := MeshInstance3D.new()
		inst.mesh = quad
		inst.position = spec["pos"]
		var mat_quad := StandardMaterial3D.new()
		mat_quad.albedo_color = spec["color"]
		mat_quad.roughness = 0.3
		inst.material_override = mat_quad
		_world_root.add_child(inst)

		var lbl := Label3D.new()
		lbl.text = spec["text"]
		lbl.font_size = 14
		lbl.modulate = Color(0.05, 0.05, 0.05)
		lbl.position = spec["pos"] + Vector3(0.0, 0.0, 0.005)
		_world_root.add_child(lbl)

func _build_3d_spatial_labels() -> void:
	# Bench Surface Spatial Text Annotations (from beispiel1.jpg)
	var labels_data := [
		{"pos": Vector3(-0.25, 0.045, 0.18), "text": "Etanol ve su karışımı\n(Ethanol / Water Feed)"},
		{"pos": Vector3(-0.06, 0.045, 0.18), "text": "Isıtıcı düğmesi\n(Heat / Stir Actuator)"},
		{"pos": Vector3(0.24, 0.045, 0.18), "text": "Etanol ayrımı\n(Distillate Fraction)"},
		{"pos": Vector3(0.65, 0.045, 0.25), "text": "Analitik Terazi\n(Analytical Balance ±0.1mg)"}
	]

	for l_data in labels_data:
		var lbl := Label3D.new()
		lbl.text = l_data["text"]
		lbl.font_size = 18
		lbl.modulate = Color(0.92, 0.95, 0.98, 0.95)
		lbl.outline_modulate = Color(0.02, 0.05, 0.08, 0.95)
		lbl.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
		lbl.position = l_data["pos"]
		_world_root.add_child(lbl)

func _build_guide_arrow() -> void:
	# 3D Glowing Green Interaction Target Arrow (from beispiel3.jpg)
	_guide_arrow = Node3D.new()
	_guide_arrow.name = "TargetGuideArrow"
	_guide_arrow.position = Vector3(0.0, 0.40, -0.03)

	var arrow_cone := CylinderMesh.new()
	arrow_cone.top_radius = 0.0
	arrow_cone.bottom_radius = 0.028
	arrow_cone.height = 0.06
	var cone_inst := MeshInstance3D.new()
	cone_inst.mesh = arrow_cone
	cone_inst.rotation_degrees = Vector3(180.0, 0.0, 0.0)
	cone_inst.position = Vector3(0.0, -0.03, 0.0)

	var mat_arrow := StandardMaterial3D.new()
	mat_arrow.albedo_color = COLOR_GREEN
	mat_arrow.emission_enabled = true
	mat_arrow.emission = COLOR_GREEN
	mat_arrow.emission_energy_multiplier = 1.8
	cone_inst.material_override = mat_arrow
	_guide_arrow.add_child(cone_inst)

	var arrow_stem := CylinderMesh.new()
	arrow_stem.top_radius = 0.012
	arrow_stem.bottom_radius = 0.012
	arrow_stem.height = 0.06
	var stem_inst := MeshInstance3D.new()
	stem_inst.mesh = arrow_stem
	stem_inst.position = Vector3(0.0, 0.03, 0.0)
	stem_inst.material_override = mat_arrow
	_guide_arrow.add_child(stem_inst)

	_world_root.add_child(_guide_arrow)

# =============================================================================
# 7. USER INTERFACE OVERLAY (beispiel3.jpg)
# =============================================================================

func _setup_ui_overlay() -> void:
	# 1. Left Vertical Action Sidebar (beispiel3.jpg icon stack)
	var left_bar := Panel.new()
	left_bar.position = Vector2(16, 16)
	left_bar.size = Vector2(58, 688)
	var lb_style := StyleBoxFlat.new()
	lb_style.bg_color = COLOR_PANEL_HEADER
	lb_style.corner_radius_top_left = 6
	lb_style.corner_radius_bottom_left = 6
	left_bar.add_theme_stylebox_override("panel", lb_style)
	add_child(left_bar)

	var left_vbox := VBoxContainer.new()
	left_vbox.position = Vector2(5, 12)
	left_vbox.size = Vector2(48, 660)
	left_vbox.add_theme_constant_override("separation", 14)
	left_bar.add_child(left_vbox)

	var side_buttons := [
		{"icon": "☰", "tooltip": "Main Menu / Lab Hub", "fn": func(): get_tree().change_scene_to_file(HUB_SCENE)},
		{"icon": "📋", "tooltip": "SOP Checklist", "fn": _on_sop_clicked},
		{"icon": "🥽", "tooltip": "Safety PPE Gear", "fn": _on_ppe_clicked},
		{"icon": "📷", "tooltip": "Inspection Camera", "fn": _on_camera_clicked},
		{"icon": "📓", "tooltip": "Laboratory Notebook", "fn": _on_notebook_clicked},
		{"icon": "⚖", "tooltip": "Tare & Calibrate", "fn": _on_tare_clicked},
		{"icon": "📘", "tooltip": "Synthesis Protocols", "fn": _on_protocols_clicked}
	]

	for s_btn in side_buttons:
		var btn := Button.new()
		btn.text = s_btn["icon"]
		btn.tooltip_text = s_btn["tooltip"]
		btn.custom_minimum_size = Vector2(48, 48)
		btn.pressed.connect(s_btn["fn"])
		left_vbox.add_child(btn)

	# 2. Top Status Bar Header (beispiel3 status pills: Magnetic stirring, Temperature)
	var header_bar := Panel.new()
	header_bar.position = Vector2(86, 16)
	header_bar.size = Vector2(880, 52)
	var hb_style := StyleBoxFlat.new()
	hb_style.bg_color = COLOR_PANEL_HEADER
	hb_style.corner_radius_top_right = 6
	hb_style.corner_radius_bottom_right = 6
	header_bar.add_theme_stylebox_override("panel", hb_style)
	add_child(header_bar)

	var header_hbox := HBoxContainer.new()
	header_hbox.position = Vector2(16, 8)
	header_hbox.size = Vector2(850, 36)
	header_hbox.add_theme_constant_override("separation", 24)
	header_bar.add_child(header_hbox)

	_lbl_header_stirrer = Label.new()
	_lbl_header_stirrer.text = "🌀 Magnetic Stirring: 0 RPM"
	_lbl_header_stirrer.add_theme_color_override("font_color", COLOR_CYAN)
	header_hbox.add_child(_lbl_header_stirrer)

	_lbl_header_temp = Label.new()
	_lbl_header_temp.text = "🔥 Bath Temp: 21.5 °C"
	_lbl_header_temp.add_theme_color_override("font_color", COLOR_AMBER)
	header_hbox.add_child(_lbl_header_temp)

	_lbl_header_status = Label.new()
	_lbl_header_status.text = "⚗ Reflux & Distillation: Idle"
	_lbl_header_status.add_theme_color_override("font_color", COLOR_GREEN)
	header_hbox.add_child(_lbl_header_status)

	# 3. Right Action Menu / Reagent Rack (beispiel3.jpg action list)
	var right_panel := Panel.new()
	right_panel.position = Vector2(982, 16)
	right_panel.size = Vector2(282, 688)
	var rp_style := StyleBoxFlat.new()
	rp_style.bg_color = COLOR_PANEL
	rp_style.corner_radius_top_left = 6
	rp_style.corner_radius_bottom_left = 6
	right_panel.add_theme_stylebox_override("panel", rp_style)
	add_child(right_panel)

	var right_vbox := VBoxContainer.new()
	right_vbox.position = Vector2(14, 14)
	right_vbox.size = Vector2(254, 660)
	right_vbox.add_theme_constant_override("separation", 8)
	right_panel.add_child(right_vbox)

	var lbl_actions_title := Label.new()
	lbl_actions_title.text = "PHYSICAL ACTUATORS"
	lbl_actions_title.add_theme_font_size_override("font_size", 13)
	lbl_actions_title.add_theme_color_override("font_color", COLOR_CYAN)
	right_vbox.add_child(lbl_actions_title)

	var actions := [
		{"label": "Place Beaker on Stirrer", "fn": _on_place_beaker},
		{"label": "Place Sensor Probe", "fn": _on_place_sensor},
		{"label": "Tare Analytical Balance", "fn": _on_tare_clicked},
		{"label": "Weigh Citric Acid (10.0 g)", "fn": func(): _add_reagent_to_balance("Citric acid", 10.0000)},
		{"label": "Weigh Sodium Bicarbonate (8.4 g)", "fn": func(): _add_reagent_to_balance("Baking soda", 8.4000)},
		{"label": "Charge Precursor to Flask", "fn": _charge_precursor_to_flask},
		{"label": "Toggle Magnetic Stirrer (450 RPM)", "fn": _toggle_stirrer},
		{"label": "Toggle Heating Mantle (78 °C)", "fn": _toggle_heating},
		{"label": "Collect Distillate Fraction", "fn": _collect_fraction},
		{"label": "Reset Benchtop State", "fn": _reset_benchtop}
	]

	for act in actions:
		var btn := Button.new()
		btn.text = act["label"]
		btn.custom_minimum_size = Vector2(254, 34)
		btn.pressed.connect(act["fn"])
		right_vbox.add_child(btn)

	right_vbox.add_child(HSeparator.new())

	var lbl_log_title := Label.new()
	lbl_log_title.text = "BENCH METROLOGY LOG"
	lbl_log_title.add_theme_font_size_override("font_size", 11)
	lbl_log_title.add_theme_color_override("font_color", COLOR_AMBER)
	right_vbox.add_child(lbl_log_title)

	_log_console = RichTextLabel.new()
	_log_console.custom_minimum_size = Vector2(254, 160)
	_log_console.bbcode_enabled = true
	_log_console.scroll_active = true
	_log_console.text = "[color=#6ddbaa]✓ System calibrated.[/color]\n• Ready for synthesis & fractional distillation."
	right_vbox.add_child(_log_console)

# =============================================================================
# 8. PHYSICAL THERMODYNAMICS & SIMULATION TICK
# =============================================================================

func _update_physical_thermodynamics(delta: float) -> void:
	# Stirrer RPM Smooth Acceleration
	if is_stirring:
		stir_rpm = move_toward(stir_rpm, target_stir_rpm, delta * 250.0)
	else:
		stir_rpm = move_toward(stir_rpm, 0.0, delta * 300.0)

	# Mantle Temperature & Boiling Kinetics
	if is_boiling:
		mantle_temp_c = move_toward(mantle_temp_c, target_temp_c, delta * 12.0)
	else:
		mantle_temp_c = move_toward(mantle_temp_c, 21.5, delta * 6.0)

	# Distillation Condensate Flow
	if mantle_temp_c >= 78.0 and is_boiling:
		condensate_flow_rate = 1.85 # mL/min
		distillate_collected_ml += (condensate_flow_rate / 60.0) * delta
	else:
		condensate_flow_rate = 0.0

	# 3D Animation: Stir Bar Rotation
	if _stir_bar != null and stir_rpm > 5.0:
		_stir_bar.rotation.y += delta * (stir_rpm / 60.0) * TAU

	# 3D Animation: Guide Arrow Hover
	if _guide_arrow != null:
		_guide_arrow.position.y = 0.40 + sin(sim_time * 3.5) * 0.025

	# 3D Animation: Condenser Vapor Translucency Pulse
	if _condenser_vapor != null and is_boiling:
		var mat: StandardMaterial3D = _condenser_vapor.material_override as StandardMaterial3D
		if mat != null:
			mat.albedo_color.a = 0.35 + sin(sim_time * 6.0) * 0.15

func _update_displays(_delta: float) -> void:
	if _stirrer_rpm_display != null:
		_stirrer_rpm_display.text = "%.0f" % stir_rpm
	if _stirrer_temp_display != null:
		_stirrer_temp_display.text = "%.1f" % mantle_temp_c
	if _balance_weight_display != null:
		_balance_weight_display.text = "%.4f g" % balance_mass_g

	if _lbl_header_stirrer != null:
		_lbl_header_stirrer.text = "🌀 Magnetic Stirring: %.0f RPM" % stir_rpm
	if _lbl_header_temp != null:
		_lbl_header_temp.text = "🔥 Bath Temp: %.1f °C" % mantle_temp_c
	if _lbl_header_status != null:
		if is_boiling and mantle_temp_c >= 78.0:
			_lbl_header_status.text = "⚗ Distilling: %.2f mL collected" % distillate_collected_ml
		elif is_boiling:
			_lbl_header_status.text = "⚗ Heating to Reflux (%.1f °C)" % mantle_temp_c
		else:
			_lbl_header_status.text = "⚗ Reflux & Distillation: Idle"

# =============================================================================
# 9. INTERACTIVE ACTION HANDLERS
# =============================================================================

func _on_place_beaker() -> void:
	_log("[color=#38dbe8]• Beaker placed on magnetic hotplate.[/color]")
	if _guide_arrow != null:
		_guide_arrow.position = Vector3(0.05, 0.35, 0.18)

func _on_place_sensor() -> void:
	_log("[color=#ffb45c]• PT1000 thermocouple immersed in analyte.[/color]")

func _on_tare_clicked() -> void:
	balance_mass_g = 0.0000
	balance_tared = true
	_log("[color=#6ddbaa]✓ Analytical Balance zeroed (TARE).[/color]")

func _add_reagent_to_balance(reagent_name: String, mass: float) -> void:
	balance_mass_g += mass
	_log("• Weighed [b]%.4f g[/b] of %s on balance." % [mass, reagent_name])

func _charge_precursor_to_flask() -> void:
	if balance_mass_g > 0.0001:
		_log("• Charged [b]%.4f g[/b] of analyte into round-bottom flask." % balance_mass_g)
		balance_mass_g = 0.0000
	else:
		_log("[color=#ff6b60]! No reagent on balance to transfer. Weigh reagent first.[/color]")

func _toggle_stirrer() -> void:
	is_stirring = not is_stirring
	_log("• Magnetic stirrer: [b]%s[/b] (target %d RPM)." % ["ON" if is_stirring else "OFF", int(target_stir_rpm)])

func _toggle_heating() -> void:
	is_boiling = not is_boiling
	_log("• Heating mantle: [b]%s[/b] (target %.1f °C)." % ["ON" if is_boiling else "OFF", target_temp_c])

func _collect_fraction() -> void:
	if distillate_collected_ml > 0.001:
		_log("[color=#6ddbaa]✓ Collected %.2f mL distillate fraction (95.2%% purity).[/color]" % distillate_collected_ml)
		distillate_collected_ml = 0.0
	else:
		_log("[color=#ffb45c]! Condenser still warming up. Wait for steady drip.[/color]")

func _reset_benchtop() -> void:
	is_stirring = false
	is_boiling = false
	balance_mass_g = 0.0000
	distillate_collected_ml = 0.0
	_log("[color=#85949f]• Benchtop apparatus reset to cold baseline.[/color]")

func _on_sop_clicked() -> void:
	_log("[b]SOP Guidance:[/b] Heat mantle to 78.4 °C for fractional ethanol separation.")

func _on_ppe_clicked() -> void:
	_log("[color=#6ddbaa]✓ PPE Active: Safety Goggles, Nitrile Gloves, Flame-Resistant Lab Coat.[/color]")

func _on_camera_clicked() -> void:
	# Toggle camera view angle between overview and apparatus close-up
	if _camera.position.z > 0.8:
		_camera.position = Vector3(0.05, 0.32, 0.50)
		_log("• Camera view: Close-up bench inspection.")
	else:
		_camera.position = Vector3(0.0, 0.48, 0.95)
		_log("• Camera view: Overview laboratory bench.")

func _on_notebook_clicked() -> void:
	_log("• Batch entry written to Electronic Lab Notebook (ELN).")

func _on_protocols_clicked() -> void:
	_log("• Active catalog protocol: %s" % str(current_protocol.get("name", "Distillation")))

var log_history: Array[String] = []

func _log(bbcode: String) -> void:
	log_history.append(bbcode)
	if _log_console != null:
		_log_console.append_text("\n" + bbcode)

func has_log(substr: String) -> bool:
	for entry in log_history:
		if entry.contains(substr):
			return true
	return false
