# Athanor Ascension - Apparatus Backdrop
# Procedural glassware backdrop for loading screen

extends Control

class_name ApparatusBackdrop

@export var glassware_count: int = 12
@export var animation_speed: float = 0.5
@export var color_scheme: Color = Color(0.2, 0.5, 1.0, 0.3)

var _glassware: Array[Dictionary] = []
var _time: float = 0.0

func _ready() -> void:
	_generate_glassware()
	set_process(true)

func _generate_glassware() -> void:
	var rect = get_rect()
	var center = rect.size / 2

	for i in range(glassware_count):
		var angle = i * TAU / glassware_count
		var radius = randf_range(80, 180)
		var type = randi() % 4  # 0=flask, 1=beaker, 2=tube, 3=condenser

		_glassware.append({
			"type": type,
			"base_angle": angle,
			"radius": radius,
			"phase_offset": randf_range(0.0, TAU),
			"scale": randf_range(0.5, 1.2),
			"alpha": randf_range(0.15, 0.35),
			"liquid_level": randf_range(0.1, 0.9),
			"liquid_color": Color(
				randf_range(0.1, 0.5),
				randf_range(0.2, 0.6),
				randf_range(0.4, 1.0),
				randf_range(0.2, 0.5)
			)
		})

func _process(delta: float) -> void:
	_time += delta
	queue_redraw()

func _draw() -> void:
	var center = get_rect().size / 2

	for gw in _glassware:
		var angle = gw.base_angle + sin(_time * animation_speed + gw.phase_offset) * 0.3
		var pos = center + Vector2(cos(angle), sin(angle)) * gw.radius
		var scale = gw.scale
		var alpha = gw.alpha

		_draw_glassware(pos, gw.type, scale, alpha, gw.liquid_level, gw.liquid_color)

func _draw_glassware(pos: Vector2, type: int, scale: float, alpha: float, liquid_level: float, liquid_color: Color) -> void:
	var s = 20.0 * scale

	match type:
		0: # Erlenmeyer flask
			_draw_flask(pos, s, alpha, liquid_level, liquid_color)
		1: # Beaker
			_draw_beaker(pos, s, alpha, liquid_level, liquid_color)
		2: # Test tube
			_draw_tube(pos, s, alpha, liquid_level, liquid_color)
		3: # Condenser
			_draw_condenser(pos, s, alpha, liquid_level, liquid_color)

func _draw_flask(pos: Vector2, s: float, alpha: float, liquid_level: float, liquid_color: Color) -> void:
	# Flask body
	var points = [
		Vector2(-s * 0.6, s * 0.5),
		Vector2(-s * 0.2, -s * 0.3),
		Vector2(s * 0.2, -s * 0.3),
		Vector2(s * 0.6, s * 0.5)
	]
	draw_polyline(points, Color(0.8, 0.85, 0.9, alpha), 2.0, true)

	# Neck
	draw_line(Vector2(-s * 0.2, -s * 0.3), Vector2(-s * 0.15, -s * 0.6), Color(0.8, 0.85, 0.9, alpha), 2.0)
	draw_line(Vector2(s * 0.2, -s * 0.3), Vector2(s * 0.15, -s * 0.6), Color(0.8, 0.85, 0.9, alpha), 2.0)
	draw_line(Vector2(-s * 0.15, -s * 0.6), Vector2(s * 0.15, -s * 0.6), Color(0.8, 0.85, 0.9, alpha), 2.0)

	# Liquid
	var liquid_h = s * 0.8 * liquid_level
	var liquid_top = s * 0.5 - liquid_h
	if liquid_h > 0:
		var liq_points = [
			Vector2(-s * 0.6, s * 0.5),
			Vector2(-s * 0.6 + (s * 0.4) * (1.0 - liquid_level), liquid_top),
			Vector2(s * 0.6 - (s * 0.4) * (1.0 - liquid_level), liquid_top),
			Vector2(s * 0.6, s * 0.5)
		]
		draw_polygon(liq_points, [liquid_color])

func _draw_beaker(pos: Vector2, s: float, alpha: float, liquid_level: float, liquid_color: Color) -> void:
	# Beaker body
	var points = [
		Vector2(-s * 0.5, s * 0.6),
		Vector2(-s * 0.5, -s * 0.4),
		Vector2(s * 0.5, -s * 0.4),
		Vector2(s * 0.5, s * 0.6)
	]
	draw_polyline(points, Color(0.8, 0.85, 0.9, alpha), 2.0, true)

	# Spout
	draw_line(Vector2(s * 0.5, -s * 0.2), Vector2(s * 0.7, -s * 0.3), Color(0.8, 0.85, 0.9, alpha), 2.0)

	# Liquid
	var liquid_h = s * 1.0 * liquid_level
	var liquid_top = s * 0.6 - liquid_h
	if liquid_h > 0:
		var liq_points = [
			Vector2(-s * 0.5, s * 0.6),
			Vector2(-s * 0.5, liquid_top),
			Vector2(s * 0.5, liquid_top),
			Vector2(s * 0.5, s * 0.6)
		]
		draw_polygon(liq_points, [liquid_color])

func _draw_tube(pos: Vector2, s: float, alpha: float, liquid_level: float, liquid_color: Color) -> void:
	# Test tube body
	var points = [
		Vector2(-s * 0.25, s * 0.7),
		Vector2(-s * 0.25, -s * 0.5),
		Vector2(s * 0.25, -s * 0.5),
		Vector2(s * 0.25, s * 0.7)
	]
	draw_polyline(points, Color(0.8, 0.85, 0.9, alpha), 2.0, true)

	# Rounded bottom
	draw_arc(pos + Vector2(0, s * 0.7), s * 0.25, PI, 0, 16, Color(0.8, 0.85, 0.9, alpha), 2.0)

	# Liquid
	var liquid_h = s * 1.2 * liquid_level
	var liquid_top = s * 0.7 - liquid_h
	if liquid_h > 0:
		var liq_points = [
			Vector2(-s * 0.25, s * 0.7),
			Vector2(-s * 0.25, liquid_top),
			Vector2(s * 0.25, liquid_top),
			Vector2(s * 0.25, s * 0.7)
		]
		draw_polygon(liq_points, [liquid_color])

func _draw_condenser(pos: Vector2, s: float, alpha: float, liquid_level: float, liquid_color: Color) -> void:
	# Outer jacket
	var outer = [
		Vector2(-s * 0.4, s * 0.6),
		Vector2(-s * 0.4, -s * 0.6),
		Vector2(s * 0.4, -s * 0.6),
		Vector2(s * 0.4, s * 0.6)
	]
	draw_polyline(outer, Color(0.7, 0.8, 0.9, alpha), 1.5, true)

	# Inner tube
	var inner = [
		Vector2(-s * 0.15, s * 0.5),
		Vector2(-s * 0.15, -s * 0.5),
		Vector2(s * 0.15, -s * 0.5),
		Vector2(s * 0.15, s * 0.5)
	]
	draw_polyline(inner, Color(0.8, 0.85, 0.95, alpha), 1.5, true)

	# Cooling water in jacket (blue tint)
	var water_h = s * 1.2 * liquid_level
	var water_top = s * 0.6 - water_h
	if water_h > 0:
		var water_points = [
			Vector2(-s * 0.38, s * 0.6),
			Vector2(-s * 0.38, water_top),
			Vector2(-s * 0.17, water_top),
			Vector2(-s * 0.17, s * 0.6),
			Vector2(s * 0.17, s * 0.6),
			Vector2(s * 0.17, water_top),
			Vector2(s * 0.38, water_top),
			Vector2(s * 0.38, s * 0.6)
		]
		draw_polygon(water_points, [Color(0.2, 0.4, 1.0, alpha * 0.5)])