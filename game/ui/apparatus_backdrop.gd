# Athanor Ascension — Apparatus Backdrop
# Procedural lab glassware silhouettes with animated liquid, bubbles and vapour.
# Used behind the main menu and the loading screen; zero texture cost, ~60 draw calls.

extends Control

const COLOR_LINE: Color = Color(0.42, 0.72, 0.82, 0.32)
const COLOR_GLASS: Color = Color(0.55, 0.82, 0.9, 0.1)
const COLOR_LIQUID: Color = Color(0.1, 0.62, 0.6, 0.2)
const COLOR_AMBER: Color = Color(0.95, 0.62, 0.22, 0.5)
const COLOR_VAPOUR: Color = Color(0.7, 0.85, 0.9, 0.08)

var _time: float = 0.0
var _bubbles: Array[Dictionary] = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1147
	for i in range(46):
		_bubbles.append({
			"x": rng.randf_range(0.0, 1.0),
			"y": rng.randf_range(0.0, 1.0),
			"r": rng.randf_range(1.0, 3.4),
			"speed": rng.randf_range(0.02, 0.09),
			"phase": rng.randf_range(0.0, TAU)
		})


func _process(delta: float) -> void:
	_time += delta
	for bubble in _bubbles:
		bubble["y"] = float(bubble["y"]) - float(bubble["speed"]) * delta
		if float(bubble["y"]) < 0.02:
			bubble["y"] = 0.9
	queue_redraw()


func _draw() -> void:
	var w := size.x
	var h := size.y
	if w <= 1.0 or h <= 1.0:
		return

	# Bench line.
	draw_line(Vector2(0, h * 0.82), Vector2(w, h * 0.82), Color(0.35, 0.5, 0.58, 0.25), 2.0)

	_draw_distillation_rig(Vector2(w * 0.08, h * 0.82), h * 0.42)
	_draw_flask(Vector2(w * 0.44, h * 0.82), h * 0.2, COLOR_LIQUID)
	_draw_flask(Vector2(w * 0.63, h * 0.82), h * 0.14, Color(0.7, 0.3, 0.55, 0.22))
	_draw_burette(Vector2(w * 0.78, h * 0.82), h * 0.34)
	_draw_condenser(Vector2(w * 0.9, h * 0.82), h * 0.3)

	for bubble in _bubbles:
		var pos := Vector2(float(bubble["x"]) * w, float(bubble["y"]) * h * 0.8)
		var drift := sin(_time * 0.7 + float(bubble["phase"])) * 6.0
		draw_circle(pos + Vector2(drift, 0), float(bubble["r"]), Color(0.45, 0.8, 0.85, 0.16))


func _draw_flask(base: Vector2, height: float, liquid_color: Color) -> void:
	var width := height * 0.9
	var neck_w := width * 0.28
	var top := base.y - height
	var points := PackedVector2Array([
		Vector2(base.x - width * 0.5, base.y),
		Vector2(base.x - width * 0.5, base.y - height * 0.42),
		Vector2(base.x - neck_w * 0.5, top),
		Vector2(base.x + neck_w * 0.5, top),
		Vector2(base.x + width * 0.5, base.y - height * 0.42),
		Vector2(base.x + width * 0.5, base.y)
	])
	draw_colored_polygon(points, COLOR_GLASS)
	for i in range(points.size()):
		draw_line(points[i], points[(i + 1) % points.size()], COLOR_LINE, 1.5)

	var liquid_level := base.y - height * 0.26
	var liquid := PackedVector2Array([
		Vector2(base.x - width * 0.46, base.y - 2.0),
		Vector2(base.x - width * 0.46, liquid_level),
		Vector2(base.x + width * 0.46, liquid_level + sin(_time * 1.3) * 1.5),
		Vector2(base.x + width * 0.46, base.y - 2.0)
	])
	draw_colored_polygon(liquid, liquid_color)
	# Meniscus.
	draw_line(Vector2(base.x - width * 0.46, liquid_level), Vector2(base.x + width * 0.46, liquid_level), Color(0.7, 0.95, 1.0, 0.35), 1.2)


func _draw_distillation_rig(base: Vector2, height: float) -> void:
	var column_w := height * 0.12
	var x := base.x
	# Round-bottom boiling flask.
	draw_circle(Vector2(x, base.y - height * 0.16), height * 0.16, COLOR_GLASS)
	draw_arc(Vector2(x, base.y - height * 0.16), height * 0.16, 0, TAU, 40, COLOR_LINE, 1.5)
	draw_circle(Vector2(x, base.y - height * 0.16), height * 0.13, Color(0.9, 0.55, 0.18, 0.22))
	# Fractionating column.
	var col_rect := Rect2(x - column_w * 0.5, base.y - height * 0.95, column_w, height * 0.62)
	draw_rect(col_rect, COLOR_GLASS, true)
	draw_rect(col_rect, COLOR_LINE, false, 1.4)
	for i in range(7):
		var y := col_rect.position.y + col_rect.size.y * (float(i) + 0.5) / 7.0
		draw_line(Vector2(col_rect.position.x, y), Vector2(col_rect.end.x, y), Color(0.5, 0.75, 0.82, 0.18), 1.0)
	# Vapour pulses rising in the column.
	for i in range(4):
		var t := fmod(_time * 0.18 + float(i) * 0.25, 1.0)
		var y := lerpf(col_rect.end.y, col_rect.position.y, t)
		draw_circle(Vector2(x + sin(t * 8.0 + i) * column_w * 0.4, y), 2.2, Color(0.75, 0.92, 1.0, 0.25 * (1.0 - t)))
	# Take-off arm and receiver.
	var arm_y := col_rect.position.y + 12.0
	draw_line(Vector2(x + column_w * 0.5, arm_y), Vector2(x + height * 0.42, arm_y + height * 0.12), COLOR_LINE, 2.0)
	_draw_flask(Vector2(x + height * 0.46, base.y), height * 0.2, Color(0.92, 0.7, 0.24, 0.25))


func _draw_burette(base: Vector2, height: float) -> void:
	var tube := Rect2(base.x - 4.0, base.y - height, 8.0, height * 0.82)
	draw_rect(tube, COLOR_GLASS, true)
	draw_rect(tube, COLOR_LINE, false, 1.2)
	for i in range(10):
		var y := tube.position.y + tube.size.y * float(i) / 10.0
		draw_line(Vector2(tube.position.x - 5.0, y), Vector2(tube.position.x, y), COLOR_LINE, 1.0)
	var filled := Rect2(tube.position + Vector2(1.0, 4.0), Vector2(6.0, tube.size.y * 0.55), )
	draw_rect(filled, Color(0.55, 0.35, 0.85, 0.3), true)
	# Drop animation.
	var drop_t := fmod(_time * 0.5, 1.0)
	draw_circle(Vector2(base.x, base.y - height * 0.1 + drop_t * 26.0), 2.4, Color(0.7, 0.55, 0.95, 0.55))


func _draw_condenser(base: Vector2, height: float) -> void:
	var outer := Rect2(base.x - 13.0, base.y - height, 26.0, height * 0.8)
	draw_rect(outer, COLOR_GLASS, true)
	draw_rect(outer, COLOR_LINE, false, 1.2)
	for i in range(5):
		var y := outer.position.y + outer.size.y * float(i) / 5.0
		draw_line(Vector2(outer.position.x + 5.0, y), Vector2(outer.end.x - 5.0, y), Color(0.4, 0.7, 0.8, 0.22), 2.0)
	draw_line(Vector2(base.x, outer.position.y), Vector2(base.x, outer.end.y), Color(0.6, 0.85, 0.95, 0.3), 1.0)
	# Cooling water flow.
	var flow := fmod(_time * 0.4, 1.0)
	draw_circle(Vector2(outer.position.x + 5.0, lerpf(outer.end.y, outer.position.y, flow)), 2.0, Color(0.4, 0.85, 1.0, 0.5))
