# Athanor Ascension — Laboratory Cinematics
# Additive set dressing for the walkable laboratory. Nothing here changes the
# simulation: it grades the light, gives the room a horizon (a real window at
# night), adds the dust that makes a light beam visible, and puts the small
# human objects on the bench that boxes never suggest on their own.
#
# All geometry is procedural and shared, so the draw-call and VRAM cost stays
# inside the Iris Xe budget (no textures beyond two 256px noise maps).

class_name LabCinematics
extends RefCounted

const CITY_SHADER = preload("res://shaders/city_window.gdshader")

static func dress(lab: Node3D) -> void:
	if lab == null or lab.has_node("Cinematics"):
		return
	var root := Node3D.new()
	root.name = "Cinematics"
	lab.add_child(root)
	_grade_environment(lab)
	_tune_lights(lab)
	_build_window(root)
	_build_north_window(root)
	_build_ceiling_fixtures(root)
	_build_dust(root)
	_build_light_shafts(root)
	_build_wall_details(root)
	_build_bench_clutter(root)
	_build_stool(root)
	_build_safety_props(root)
	_retint_architecture(lab)


# -----------------------------------------------------------------------------
# Environment grading
# -----------------------------------------------------------------------------

static func _grade_environment(lab: Node3D) -> void:
	var world_env := lab.get_node_or_null("WorldEnvironment") as WorldEnvironment
	if world_env == null:
		world_env = WorldEnvironment.new()
		world_env.name = "WorldEnvironment"
		lab.add_child(world_env)

	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.012, 0.016, 0.022)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.44, 0.53, 0.66)
	env.ambient_light_energy = 0.42
	env.ambient_light_sky_contribution = 0.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED

	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.88
	env.tonemap_white = 4.0

	# Glow may be a no-op on some Compatibility drivers; it is set defensively.
	env.glow_enabled = true
	env.glow_intensity = 0.32
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.25
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT

	env.fog_enabled = true
	env.fog_light_color = Color(0.20, 0.26, 0.34)
	# Compatibility fog is a cheap depth cue, not an atmosphere. At 0.010 the
	# ceiling practicals scatter into solid white blobs.
	env.fog_light_energy = 0.16
	env.fog_density = 0.0018
	env.fog_aerial_perspective = 0.0
	env.fog_sky_affect = 0.0

	env.adjustment_enabled = true
	env.adjustment_brightness = 0.98
	env.adjustment_contrast = 1.06
	env.adjustment_saturation = 1.02

	world_env.environment = env


static func _retint_architecture(lab: Node3D) -> void:
	# A real lab is not white. Muted walls and a dark epoxy floor give the
	# practicals something to fall off; the blue stripe stays as the accent.
	var wall := _material(Color(0.50, 0.54, 0.56), 0.68, 0.0)
	var ceiling := _material(Color(0.58, 0.60, 0.61), 0.75, 0.0)
	var floor_mat := _roughen(_material(Color(0.33, 0.37, 0.42), 0.30, 0.08), 0.03, 0.95)
	var bench_mat := _roughen(_material(Color(0.055, 0.062, 0.070), 0.24, 0.12), 0.06, 0.80)

	for wall_name in ["Wall_North", "Wall_South", "Wall_West", "Wall_East"]:
		var mesh := lab.get_node_or_null("Architecture/%s/MeshInstance3D" % wall_name) as MeshInstance3D
		if mesh != null:
			mesh.material_override = wall
	var ceiling_mesh := lab.get_node_or_null("Architecture/Ceiling/MeshInstance3D") as MeshInstance3D
	if ceiling_mesh != null:
		ceiling_mesh.material_override = ceiling
	var floor_mesh := lab.get_node_or_null("Architecture/Floor/MeshInstance3D") as MeshInstance3D
	if floor_mesh != null:
		floor_mesh.material_override = floor_mat
	var bench := lab.get_node_or_null("Furniture/CentralMainWorkbench/BenchTopMesh") as MeshInstance3D
	if bench != null:
		bench.material_override = bench_mat


static func _build_north_window(root: Node3D) -> void:
	# The window over the bench: the reason the glassware has a rim highlight
	# and the room has a horizon when you look up from the balance.
	var frame_mat := _material(Color(0.14, 0.15, 0.17), 0.35, 0.65)
	var glass_mat := ShaderMaterial.new()
	glass_mat.shader = CITY_SHADER
	glass_mat.set_shader_parameter("rain_strength", 0.35)

	var pane := MeshInstance3D.new()
	pane.name = "CityWindowNorth"
	var quad := QuadMesh.new()
	quad.size = Vector2(2.6, 1.25)
	pane.mesh = quad
	pane.material_override = glass_mat
	# The north wall is 0.15 m thick with its inner face at z = -3.925. A pane at
	# -3.94 sits inside the wall and never renders; keep it clearly in the room.
	pane.position = Vector3(0.55, 2.42, -3.90)
	pane.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(pane)

	_box(root, "NWinSill", Vector3(0.55, 1.77, -3.90), Vector3(2.8, 0.08, 0.18), frame_mat)
	_box(root, "NWinHead", Vector3(0.55, 3.07, -3.90), Vector3(2.8, 0.08, 0.18), frame_mat)
	_box(root, "NWinJambL", Vector3(-0.82, 2.42, -3.90), Vector3(0.08, 1.38, 0.18), frame_mat)
	_box(root, "NWinJambR", Vector3(1.92, 2.42, -3.90), Vector3(0.08, 1.38, 0.18), frame_mat)
	_box(root, "NWinMullion", Vector3(0.55, 2.42, -3.91), Vector3(0.055, 1.30, 0.10), frame_mat)
	_box(root, "NWinTransom", Vector3(0.55, 2.70, -3.91), Vector3(2.70, 0.05, 0.10), frame_mat)

	var spill := OmniLight3D.new()
	spill.name = "Light_NorthWindow"
	spill.light_color = Color(0.58, 0.72, 1.0)
	spill.light_energy = 1.15
	spill.omni_range = 5.5
	spill.position = Vector3(0.55, 2.35, -3.35)
	spill.shadow_enabled = false
	root.add_child(spill)


static func _tune_lights(lab: Node3D) -> void:
	# The original scene floods a white room with six omnis at full energy.
	# Reduce them so the practicals and the window do the storytelling.
	var tuning := {
		"DirectionalLight3D": {"energy": 0.12, "color": Color(0.55, 0.66, 0.90)},
		"Light_KeyAmbient": {"energy": 0.55, "color": Color(0.72, 0.80, 0.92)},
		"Light_Bench_Spotlight": {"energy": 2.4, "color": Color(1.0, 0.94, 0.86)},
		"Light_FumeHood_Interior": {"energy": 1.9, "color": Color(0.88, 0.95, 1.0)},
		"Light_Balance_Task": {"energy": 0.80, "color": Color(0.92, 0.96, 1.0)},
		"Light_Sink_Task": {"energy": 0.70, "color": Color(0.92, 0.96, 1.0)},
	}
	for light_name in tuning.keys():
		var light := lab.find_child(str(light_name), true, false) as Light3D
		if light == null:
			continue
		var cfg: Dictionary = tuning[light_name]
		light.light_energy = float(cfg["energy"])
		light.light_color = cfg["color"]
		light.shadow_enabled = light is OmniLight3D and str(light_name) in ["Light_Bench_Spotlight", "Light_FumeHood_Interior"]
		light.shadow_bias = 0.04
		light.shadow_normal_bias = 1.2
		if light is OmniLight3D:
			# Compatibility renderer only supports cube shadows for omnis.
			light.omni_shadow_mode = OmniLight3D.SHADOW_CUBE
			# Slight warm/cool split keeps the room from reading as a single color.
			if str(light_name) == "Light_Bench_Spotlight":
				light.light_color = Color(1.0, 0.92, 0.82)
				light.omni_range = 7.5
				light.shadow_enabled = false


# -----------------------------------------------------------------------------
# Window and city
# -----------------------------------------------------------------------------

static func _build_window(root: Node3D) -> void:
	var frame_mat := _material(Color(0.16, 0.17, 0.19), 0.35, 0.65)
	var glass_mat := ShaderMaterial.new()
	glass_mat.shader = CITY_SHADER

	var pane := MeshInstance3D.new()
	pane.name = "CityWindow"
	var quad := QuadMesh.new()
	quad.size = Vector2(3.6, 1.9)
	pane.mesh = quad
	pane.material_override = glass_mat
	pane.position = Vector3(-4.865, 2.18, -0.2)
	pane.rotation.y = PI * 0.5
	pane.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(pane)

	# Reveal / frame: four bars plus two mullions.
	_box(root, "WindowSill", Vector3(-4.82, 1.20, -0.2), Vector3(0.22, 0.10, 3.75), frame_mat)
	_box(root, "WindowHead", Vector3(-4.82, 3.16, -0.2), Vector3(0.22, 0.10, 3.75), frame_mat)
	_box(root, "WindowJambN", Vector3(-4.82, 2.18, -2.10), Vector3(0.22, 1.95, 0.10), frame_mat)
	_box(root, "WindowJambS", Vector3(-4.82, 2.18, 1.70), Vector3(0.22, 1.95, 0.10), frame_mat)
	_box(root, "WindowMullionA", Vector3(-4.84, 2.18, -0.78), Vector3(0.10, 1.90, 0.06), frame_mat)
	_box(root, "WindowMullionB", Vector3(-4.84, 2.18, 0.42), Vector3(0.10, 1.90, 0.06), frame_mat)
	_box(root, "WindowTransom", Vector3(-4.84, 2.58, -0.2), Vector3(0.10, 0.06, 3.55), frame_mat)

	# Cold spill from the city, and a warm sodium bounce from the sill.
	var city_light := OmniLight3D.new()
	city_light.name = "Light_CityWindow"
	city_light.light_color = Color(0.55, 0.70, 1.0)
	city_light.light_energy = 1.6
	city_light.omni_range = 7.0
	city_light.omni_attenuation = 1.4
	city_light.position = Vector3(-4.25, 2.25, -0.2)
	city_light.shadow_enabled = false
	root.add_child(city_light)

	var sodium := OmniLight3D.new()
	sodium.name = "Light_SodiumSpill"
	sodium.light_color = Color(1.0, 0.62, 0.32)
	sodium.light_energy = 0.55
	sodium.omni_range = 3.2
	sodium.position = Vector3(-4.1, 1.55, 0.9)
	root.add_child(sodium)


# -----------------------------------------------------------------------------
# Ceiling practicals
# -----------------------------------------------------------------------------

static func _build_ceiling_fixtures(root: Node3D) -> void:
	var housing := _material(Color(0.10, 0.11, 0.12), 0.45, 0.55)
	var panel := _emissive(Color(0.96, 0.95, 0.92), 0.45)

	var spots := [Vector3(-2.45, 3.44, 0.15), Vector3(0.0, 3.44, 0.15), Vector3(2.45, 3.44, 0.15)]
	for i in range(spots.size()):
		var p: Vector3 = spots[i]
		_box(root, "FixtureHousing_%d" % i, p, Vector3(1.15, 0.045, 0.46), housing)
		_box(root, "FixturePanel_%d" % i, p + Vector3(0, -0.028, 0), Vector3(0.98, 0.012, 0.34), panel)


static func _build_light_shafts(root: Node3D) -> void:
	var shaft_mat := StandardMaterial3D.new()
	shaft_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	shaft_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	shaft_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	shaft_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	shaft_mat.albedo_color = Color(0.72, 0.82, 1.0, 0.022)
	shaft_mat.disable_receive_shadows = true

	var spots := [Vector3(-2.45, 1.65, 0.15), Vector3(0.0, 1.65, 0.15), Vector3(2.45, 1.65, 0.15)]
	for i in range(spots.size()):
		var cone := MeshInstance3D.new()
		cone.name = "LightShaft_%d" % i
		var mesh := CylinderMesh.new()
		mesh.top_radius = 0.28
		mesh.bottom_radius = 1.15
		mesh.height = 1.85
		mesh.cap_top = false
		mesh.cap_bottom = false
		mesh.radial_segments = 24
		mesh.rings = 1
		mesh.material = shaft_mat
		cone.mesh = mesh
		cone.position = spots[i]
		cone.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		cone.extra_cull_margin = 1.0
		root.add_child(cone)


static func _build_dust(root: Node3D) -> void:
	var mote := QuadMesh.new()
	mote.size = Vector2(0.006, 0.006)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.albedo_color = Color(1.0, 0.95, 0.85, 0.55)
	mat.disable_receive_shadows = true
	mote.material = mat

	var dust := CPUParticles3D.new()
	dust.name = "DustMotes"
	dust.mesh = mote
	dust.amount = 110
	dust.lifetime = 13.0
	dust.preprocess = 12.0
	dust.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	dust.emission_box_extents = Vector3(4.2, 1.5, 3.2)
	dust.position = Vector3(0.0, 1.85, -0.1)
	dust.direction = Vector3(0.1, 1.0, 0.05)
	dust.spread = 55.0
	dust.initial_velocity_min = 0.01
	dust.initial_velocity_max = 0.06
	dust.gravity = Vector3(0.0, 0.004, 0.0)
	dust.scale_amount_min = 0.5
	dust.scale_amount_max = 1.7
	dust.color = Color(1.0, 0.95, 0.85, 0.0)
	dust.emitting = true
	root.add_child(dust)


# -----------------------------------------------------------------------------
# Architecture details
# -----------------------------------------------------------------------------

static func _build_wall_details(root: Node3D) -> void:
	var steel := _material(Color(0.23, 0.25, 0.28), 0.38, 0.70)
	var dark := _material(Color(0.10, 0.11, 0.13), 0.50, 0.30)

	# Door on the south wall, so facing away from the bench still reads as a room.
	_box(root, "DoorPanel", Vector3(2.6, 1.06, 3.87), Vector3(0.95, 2.12, 0.06), _material(Color(0.30, 0.34, 0.38), 0.52, 0.10))
	_box(root, "DoorFrameL", Vector3(2.06, 1.06, 3.86), Vector3(0.07, 2.18, 0.09), steel)
	_box(root, "DoorFrameR", Vector3(3.14, 1.06, 3.86), Vector3(0.07, 2.18, 0.09), steel)
	_box(root, "DoorFrameTop", Vector3(2.6, 2.17, 3.86), Vector3(1.15, 0.07, 0.09), steel)
	_sphere(root, "DoorHandle", Vector3(3.00, 1.02, 3.83), 0.028, _material(Color(0.75, 0.72, 0.62), 0.22, 0.90))

	var exit_sign := Label3D.new()
	exit_sign.name = "ExitSign"
	exit_sign.text = "EXIT"
	exit_sign.font_size = 64
	exit_sign.pixel_size = 0.0032
	exit_sign.modulate = Color(0.35, 1.0, 0.62)
	exit_sign.outline_modulate = Color(0.0, 0.12, 0.05)
	exit_sign.position = Vector3(2.6, 2.45, 3.80)
	exit_sign.rotation.y = PI
	root.add_child(exit_sign)
	_box(root, "ExitSignBox", Vector3(2.6, 2.45, 3.845), Vector3(0.42, 0.16, 0.025), _material(Color(0.05, 0.16, 0.09), 0.5, 0.0))

	# A warm task lamp over the bench. The practical gives the glass and steel
	# a specular highlight, which is what actually sells the material read.
	_cyl(root, "BenchLampShade", Vector3(0.0, 2.62, -0.55), 0.19, 0.10, _material(Color(0.16, 0.17, 0.18), 0.35, 0.55), Vector3(0, 0, PI))
	_cyl(root, "BenchLampStem", Vector3(0.0, 2.86, -0.55), 0.012, 0.40, _material(Color(0.30, 0.31, 0.33), 0.30, 0.80))
	var lamp := OmniLight3D.new()
	lamp.name = "Light_BenchPractical"
	lamp.light_color = Color(1.0, 0.80, 0.56)
	lamp.light_energy = 1.35
	lamp.omni_range = 3.6
	lamp.omni_attenuation = 1.2
	lamp.position = Vector3(0.0, 2.50, -0.55)
	lamp.shadow_enabled = false
	root.add_child(lamp)

	# Wall clock: a face, a rim, two hands. Fixed at 21:40, the night shift.
	_cyl(root, "ClockRim", Vector3(4.88, 2.35, 1.1), 0.24, 0.035, steel, Vector3(0, 0, PI * 0.5))
	_cyl(root, "ClockFace", Vector3(4.85, 2.35, 1.1), 0.215, 0.01, _material(Color(0.86, 0.87, 0.84), 0.35, 0.0), Vector3(0, 0, PI * 0.5))
	_box(root, "ClockHour", Vector3(4.84, 2.40, 1.1), Vector3(0.008, 0.11, 0.012), dark, Vector3(0, 0, -0.5))
	_box(root, "ClockMinute", Vector3(4.84, 2.28, 1.1), Vector3(0.008, 0.16, 0.012), dark, Vector3(0, 0, 0.25))

	# Upper cabinets over the balance bench.
	var cabinet := _material(Color(0.82, 0.84, 0.86), 0.42, 0.05)
	_box(root, "WallCabinet", Vector3(3.9, 2.55, -3.55), Vector3(1.9, 0.72, 0.36), cabinet)
	_box(root, "WallCabinetSplit", Vector3(3.9, 2.55, -3.72), Vector3(0.03, 0.68, 0.02), steel)
	_box(root, "WallCabinetHandleL", Vector3(3.45, 2.55, -3.72), Vector3(0.02, 0.18, 0.02), steel)
	_box(root, "WallCabinetHandleR", Vector3(4.35, 2.55, -3.72), Vector3(0.02, 0.18, 0.02), steel)

	# Under-cabinet LED strip, the reason the bench edge reads at night.
	_box(root, "UnderCabinetLED", Vector3(3.9, 2.18, -3.55), Vector3(1.8, 0.012, 0.03), _emissive(Color(1.0, 0.95, 0.85), 2.0))

	# Safety board: a yellow panel with a readable header.
	_box(root, "SafetyBoard", Vector3(-2.9, 2.10, -3.88), Vector3(1.25, 0.85, 0.03), _material(Color(0.92, 0.78, 0.28), 0.55, 0.0))
	var label := Label3D.new()
	label.name = "SafetyBoardText"
	label.text = "CHEMICAL HYGIENE PLAN\n\nEYE WASH  ·  SHOWER\nSPILL KIT  ·  WASTE\n\nNO FOOD. NO SOLO WORK."
	label.font_size = 40
	label.pixel_size = 0.0032
	label.modulate = Color(0.10, 0.09, 0.06)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.position = Vector3(-2.9, 2.10, -3.855)
	root.add_child(label)


static func _build_bench_clutter(root: Node3D) -> void:
	var paper := _material(Color(0.88, 0.86, 0.80), 0.72, 0.0)
	var ink := _material(Color(0.10, 0.12, 0.16), 0.55, 0.0)
	var board := _material(Color(0.22, 0.16, 0.12), 0.60, 0.0)

	# Notebook and pen beside the balance, where a chemist would actually leave them.
	_box(root, "Notebook", Vector3(1.3, 0.925, -2.75), Vector3(0.20, 0.014, 0.28), board, Vector3(0, 0.3, 0))
	_box(root, "NotebookPage", Vector3(1.3, 0.934, -2.75), Vector3(0.185, 0.004, 0.26), paper, Vector3(0, 0.3, 0))
	_box(root, "Pen", Vector3(1.16, 0.94, -2.62), Vector3(0.135, 0.009, 0.009), ink, Vector3(0, 1.1, 0))

	# A small stack of labelled sample vials in a wooden rack.
	var rack := _material(Color(0.34, 0.25, 0.18), 0.65, 0.0)
	_box(root, "VialRack", Vector3(-2.55, 0.94, -2.90), Vector3(0.30, 0.035, 0.12), rack)
	for i in range(4):
		_cyl(root, "Vial_%d" % i, Vector3(-2.67 + i * 0.075, 0.985, -2.90), 0.019, 0.075,
			_material(Color(0.70, 0.74, 0.70, 0.35), 0.10, 0.0, 0.45))
		_cyl(root, "VialCap_%d" % i, Vector3(-2.67 + i * 0.075, 1.026, -2.90), 0.021, 0.012,
			_material(Color(0.15, 0.18, 0.22), 0.45, 0.05))

	# Glassware silhouettes already exist in the apparatus instances; add a
	# single large amber stock bottle for scale and color contrast.
	_cyl(root, "StockBottle_Body", Vector3(-3.55, 1.06, -1.90), 0.085, 0.22,
		_material(Color(0.55, 0.34, 0.09, 0.86), 0.16, 0.0, 0.9))
	_cyl(root, "StockBottle_Neck", Vector3(-3.55, 1.21, -1.90), 0.032, 0.09,
		_material(Color(0.55, 0.34, 0.09, 0.86), 0.16, 0.0, 0.9))
	_cyl(root, "StockBottle_Cap", Vector3(-3.55, 1.265, -1.90), 0.037, 0.03,
		_material(Color(0.10, 0.11, 0.12), 0.40, 0.0))


static func _build_stool(root: Node3D) -> void:
	var chrome := _material(Color(0.55, 0.57, 0.60), 0.22, 0.90)
	var seat_mat := _material(Color(0.10, 0.12, 0.15), 0.68, 0.0)
	var base := Vector3(3.15, 0.0, 2.15)
	_cyl(root, "StoolSeat", base + Vector3(0, 0.66, 0), 0.17, 0.045, seat_mat)
	_cyl(root, "StoolPost", base + Vector3(0, 0.33, 0), 0.026, 0.62, chrome)
	for i in range(4):
		var a := TAU * float(i) / 4.0 + 0.3
		var foot := base + Vector3(cos(a) * 0.17, 0.03, sin(a) * 0.17)
		_cyl(root, "StoolFoot_%d" % i, foot + Vector3(0, 0.11, 0), 0.016, 0.24, chrome, Vector3(0.5 * cos(a), 0, -0.5 * sin(a)))


static func _build_safety_props(root: Node3D) -> void:
	var red := _material(Color(0.62, 0.07, 0.06), 0.32, 0.15)
	var black := _material(Color(0.09, 0.09, 0.10), 0.50, 0.20)
	# Fire extinguisher beside the door.
	var p := Vector3(3.65, 0.0, 3.55)
	_cyl(root, "ExtinguisherBody", p + Vector3(0, 0.30, 0), 0.075, 0.46, red)
	_cyl(root, "ExtinguisherTop", p + Vector3(0, 0.545, 0), 0.035, 0.06, black)
	_box(root, "ExtinguisherHandle", p + Vector3(0, 0.60, 0), Vector3(0.10, 0.025, 0.03), black)
	_box(root, "ExtinguisherLabel", p + Vector3(0, 0.34, 0.077), Vector3(0.10, 0.16, 0.004), _material(Color(0.90, 0.88, 0.80), 0.70, 0.0))

	# Spill kit: a yellow lidded bin under the sink.
	_box(root, "SpillKit", Vector3(-4.25, 0.22, 2.65), Vector3(0.42, 0.44, 0.34), _material(Color(0.85, 0.68, 0.12), 0.45, 0.0))
	_box(root, "SpillKitLid", Vector3(-4.25, 0.455, 2.65), Vector3(0.45, 0.03, 0.37), _material(Color(0.15, 0.15, 0.16), 0.45, 0.1))


# -----------------------------------------------------------------------------
# Surface texture
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Primitive helpers
# -----------------------------------------------------------------------------

static func _material(color: Color, roughness: float = 0.5, metallic: float = 0.0, alpha: float = 1.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	var c := color
	c.a = alpha
	mat.albedo_color = c
	mat.roughness = roughness
	mat.metallic = metallic
	if alpha < 1.0:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat


# A perfectly uniform roughness value is what makes a surface read as CG. Real
# epoxy and phenolic are patchy: wear paths, cleaning marks, thin spots. One
# tiled noise texture over roughness is enough to break the uniformity without
# pretending to be a scanned material.
static func _roughen(mat: StandardMaterial3D, frequency: float = 0.035, amount: float = 0.85) -> StandardMaterial3D:
	var noise := FastNoiseLite.new()
	noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency = frequency
	noise.fractal_octaves = 3

	var tex := NoiseTexture2D.new()
	tex.width = 512
	tex.height = 512
	tex.seamless = true
	tex.noise = noise
	tex.generate_mipmaps = true

	mat.roughness_texture = tex
	# Godot multiplies the texture with mat.roughness; keep the mean near 1.0 so
	# the material does not drift glossy or chalky, only vary.
	mat.roughness = clampf(mat.roughness * amount + 0.08, 0.05, 1.0)
	mat.uv1_scale = Vector3(4.0, 4.0, 1.0)
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return mat


static func _emissive(color: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = energy
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return mat


static func _box(parent: Node3D, node_name: String, pos: Vector3, size: Vector3, mat: Material, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = node_name
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh.material = mat
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	parent.add_child(mi)
	return mi


static func _cyl(parent: Node3D, node_name: String, pos: Vector3, radius: float, height: float, mat: Material, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = node_name
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 20
	mesh.rings = 1
	mesh.material = mat
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	parent.add_child(mi)
	return mi


static func _sphere(parent: Node3D, node_name: String, pos: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = node_name
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh.radial_segments = 16
	mesh.rings = 8
	mesh.material = mat
	mi.mesh = mesh
	mi.position = pos
	parent.add_child(mi)
	return mi
