# Athanor Ascension - Apparatus Backdrop (UI)
# Animated procedural glassware backdrop for loading screen and menus

extends Control

class_name ApparatusBackdrop

@export var animation_speed: float = 1.0
@export var glassware_count: int = 12
@export var color_palette: Array[Color] = [
	Color(0.9, 0.95, 1.0, 0.3),   # Clear glass
	Color(0.2, 0.6, 1.0, 0.4),    # Blue solution
	Color(1.0, 0.4, 0.2, 0.4),    # Orange reaction
	Color(0.2, 0.8, 0.4, 0.4),    # Green precipitate
	Color(1.0, 0.8, 0.0, 0.4),    # Yellow indicator
	Color(0.6, 0.3, 0.9, 0.4),    # Purple organic
	Color(0.0, 1.0, 0.5, 0.4),    # Radioluminescent green
	Color(1.0, 0.2, 0.6, 0.4),    # Pink phenolphthalein
]

var _glassware: Array[Dictionary] = []
var _time: float = 0.0
var _animation_enabled: bool = true

func _ready() -> void:
	_generate_glassware()
	set_process(true)

func _generate_glassware() -> void:
	_randomize()

	for i in range(glassware_count):
		var gw = {
			"type": randi() % 6,  # 0=beaker, 1=flask, 2=graduated, 3=test_tube, 4=condenser, 5=buret
			"x": randf_range(0.05, 0.95),
			"y": randf_range(0.1, 0.9),
			"scale": randf_range(0.08, 0.18),
			"rotation": randf_range(-0.1, 0.1),
			"color": color_palette[randi() % color_palette.size()],
			"fill": randf_range(0.1, 0.9),
			"bubbles": [],
			 "condensation": randf_range(0.0, 0.3),
			"liquid_wave_phase": randf_range(0.0, TAU),
			"liquid_wave_speed": randf_range(0.5, 2.0),
			"bubble_timer": randf_range(0.0, 2.0),
			"bubble_interval": randf_range(1.0, 4.0),
			"glint_timer": randf_range(0.0, 5.0),
			"glint_interval": randf_range(3.0, 8.0)
		}
		_glassware.append(gw)

func _process(delta: float) -> void:
	if not _animation_enabled:
		return

	_time += delta

	for gw in _glassware:
		# Liquid wave animation
		gw.liquid_wave_phase += gw.liquid_wave_speed * delta

		# Bubble generation
		gw.bubble_timer += delta
		if gw.bubble_timer >= gw.bubble_interval and gw.fill > 0.2:
			_add_bubble(gw)
			gw.bubble_timer = 0.0
			gw.bubble_interval = randf_range(1.0, 4.0)

		# Update bubbles
		for bubble in gw.bubbles:
			bubble.y -= delta * bubble.speed * 0.1
			bubble.x += sin(_time * 2.0 + bubble.phase) * delta * 0.01
			bubble.life -= delta
			bubble.alpha = clamp(bubble.life / bubble.max_life, 0.0, 1.0)

		# Remove dead bubbles
		var alive = []
		for bubble in gw.bubbles:
			if bubble.life > 0:
				alive.append(bubble)
		gw.bubbles = alive

		# Glint effect
		gw.glint_timer += delta
		if gw.glint_timer >= gw.glint_interval:
			gw.glint_timer = 0.0
			gw.glint_interval = randf_range(3.0, 8.0)

func _add_bubble(gw: Dictionary) -> void:
	var bubble = {
		"x": randf_range(-0.3, 0.3),
		"y": 0.5 * gw.fill,
		"size": randf_range(0.01, 0.03),
		"speed": randf_range(0.5, 1.5),
		"phase": randf_range(0.0, TAU),
		"life": randf_range(1.0, 3.0),
		"max_life": randf_range(1.0, 3.0),
		"alpha": 1.0
	}
	gw.bubbles.append(bubble)

func _draw() -> void:
	var size = get_rect().size
	var center = size / 2

	for gw in _glassware:
		var pos = Vector2(gw.x * size.x, gw.y * size.y)
		var scale = min(size.x, size.y) * gw.scale

		# Draw glassware based on type
		match gw.type:
			0: _draw_beaker(pos, scale, gw)
			1: _draw_flask(pos, scale, gw)
			2: _draw_graduated(pos, scale, gw)
			3: _draw_test_tube(pos, scale, gw)
			4: _draw_condenser(pos, scale, gw)
			5: _draw_buret(pos, scale, gw)

func _draw_beaker(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 0.8
	var h = scale * 1.2
	var rect = Rect2(pos - Vector2(w/2, h/2), Vector2(w, h))

	# Glass walls
	draw_rect(rect, gw.color, false, max(1.0, scale * 0.5))

	# Liquid
	var liquid_h = h * gw.fill
	var liquid_rect = Rect2(pos.x - w/2, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, gw.color, true)

	# Liquid wave
	var wave_h = sin(_time * gw.liquid_wave_speed + gw.liquid_wave_phase) * scale * 0.02
	var wave_y = pos.y + h/2 - liquid_h + wave_h
	draw_line(Vector2(pos.x - w/2, wave_y), Vector2(pos.x + w/2, wave_y), gw.color, max(1.0, scale * 0.3))

	# Bubbles
	for bubble in gw.bubbles:
		var bp = pos + Vector2(bubble.x * w, bubble.y * h)
		draw_circle(bp, bubble.size * scale * bubble.alpha, Color(gw.color.r, gw.color.g, gw.color.b, bubble.alpha * 0.8))

	# Condensation
	if gw.condensation > 0.05:
		for i in range(int(gw.condensation * 5)):
			var cx = pos.x + randf_range(-w/2, w/2)
			var cy = pos.y + randf_range(-h/2, h/2)
			draw_circle(Vector2(cx, cy), scale * 0.01, Color(1, 1, 1, gw.condensation * 0.3))

	# Glint
	if gw.glint_timer < 0.1:
		var glint_pos = pos + Vector2(randf_range(-w/2, w/2), randf_range(-h/2, h/2))
		draw_circle(glint_pos, scale * 0.15, Color(1, 1, 1, 0.8 * (1.0 - gw.glint_timer * 10)))

func _draw_flask(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 0.7
	var h = scale * 1.4
	var neck_w = w * 0.3
	var neck_h = h * 0.25

	# Body
	var body_rect = Rect2(pos.x - w/2, pos.y - h/2 + neck_h, w, h - neck_h)
	draw_rect(body_rect, gw.color, false, max(1.0, scale * 0.5))

	# Neck
	var neck_rect = Rect2(pos.x - neck_w/2, pos.y - h/2, neck_w, neck_h)
	draw_rect(neck_rect, gw.color, false, max(1.0, scale * 0.5))

	# Liquid
	var liquid_h = (h - neck_h) * gw.fill
	var liquid_rect = Rect2(pos.x - w/2, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, gw.color, true)

	# Bubbles
	for bubble in gw.bubbles:
		var bp = pos + Vector2(bubble.x * w, bubble.y * h)
		draw_circle(bp, bubble.size * scale * bubble.alpha, Color(gw.color.r, gw.color.g, gw.color.b, bubble.alpha * 0.8))

func _draw_graduated(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 0.5
	var h = scale * 1.6
	var rect = Rect2(pos - Vector2(w/2, h/2), Vector2(w, h))

	draw_rect(rect, gw.color, false, max(1.0, scale * 0.4))

	# Graduation marks
	for i in range(10):
		var mark_y = pos.y - h/2 + (h/10) * i
		draw_line(Vector2(pos.x - w/2, mark_y), Vector2(pos.x + w/2, mark_y), gw.color, max(1.0, scale * 0.2))

	# Liquid
	var liquid_h = h * gw.fill
	var liquid_rect = Rect2(pos.x - w/2, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, gw.color, true)

	# Bubbles
	for bubble in gw.bubbles:
		var bp = pos + Vector2(bubble.x * w, bubble.y * h)
		draw_circle(bp, bubble.size * scale * bubble.alpha, Color(gw.color.r, gw.color.g, gw.color.b, bubble.alpha * 0.8))

func _draw_test_tube(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 0.4
	var h = scale * 1.5
	var radius = w/2

	# Tube body
	var rect = Rect2(pos.x - radius, pos.y - h/2, w, h - radius)
	draw_rect(rect, gw.color, false, max(1.0, scale * 0.4))

	# Round bottom
	draw_circle(pos, radius, gw.color, false, max(1.0, scale * 0.4))

	# Liquid
	var liquid_h = min(h * gw.fill, h - radius)
	var liquid_rect = Rect2(pos.x - radius, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, gw.color, true)

	# Round bottom liquid
	if liquid_h > h - radius:
		draw_circle(pos, radius, gw.color, true)

	# Bubbles
	for bubble in gw.bubbles:
		var bp = pos + Vector2(bubble.x * w, bubble.y * h)
		draw_circle(bp, bubble.size * scale * bubble.alpha, Color(gw.color.r, gw.color.g, gw.color.b, bubble.alpha * 0.8))

func _draw_condenser(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 1.2
	var h = scale * 1.0
	var inner_w = w * 0.3
	var inner_h = h * 0.6

	# Outer jacket
	var outer_rect = Rect2(pos - Vector2(w/2, h/2), Vector2(w, h))
	draw_rect(outer_rect, gw.color, false, max(1.0, scale * 0.4))

	# Inner tube
	var inner_rect = Rect2(pos - Vector2(inner_w/2, inner_h/2), Vector2(inner_w, inner_h))
	draw_rect(inner_rect, gw.color, false, max(1.0, scale * 0.4))

	# Cooling liquid (outer)
	var liquid_h = h * gw.fill
	var liquid_rect = Rect2(pos.x - w/2, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, Color(0.2, 0.6, 1.0, 0.3), true)

	# Condensation droplets
	for i in range(int(gw.condensation * 8)):
		var cx = pos.x + randf_range(-w/2, w/2)
		var cy = pos.y + randf_range(-h/2, h/2)
		draw_circle(Vector2(cx, cy), scale * 0.015, Color(1, 1, 1, gw.condensation * 0.4))

func _draw_buret(pos: Vector2, scale: float, gw: Dictionary) -> void:
	var w = scale * 0.35
	var h = scale * 1.8
	var rect = Rect2(pos - Vector2(w/2, h/2), Vector2(w, h))

	draw_rect(rect, gw.color, false, max(1.0, scale * 0.3))

	# Graduation marks
	for i in range(20):
		var mark_y = pos.y - h/2 + (h/20) * i
		draw_line(Vector2(pos.x - w/2, mark_y), Vector2(pos.x + w/2, mark_y), gw.color, max(1.0, scale * 0.15))

	# Stopcock at bottom
	var stopcock_rect = Rect2(pos.x - w, pos.y + h/2 - scale * 0.1, w * 2, scale * 0.1)
	draw_rect(stopcock_rect, Color(0.3, 0.3, 0.3), true)

	# Liquid
	var liquid_h = h * gw.fill
	var liquid_rect = Rect2(pos.x - w/2, pos.y + h/2 - liquid_h, w, liquid_h)
	draw_rect(liquid_rect, gw.color, true)

	# Meniscus
	var meniscus_y = pos.y + h/2 - h * gw.fill
	draw_line(Vector2(pos.x - w/2, meniscus_y), Vector2(pos.x + w/2, meniscus_y), gw.color, max(1.0, scale * 0.3))

	# Bubbles (rare in buret)
	for bubble in gw.bubbles:
		if randf() < 0.1:
			var bp = pos + Vector2(bubble.x * w, bubble.y * h)
			draw_circle(bp, bubble.size * scale * bubble.alpha, Color(gw.color.r, gw.color.g, gw.color.b, bubble.alpha * 0.5))