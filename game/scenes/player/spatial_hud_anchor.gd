# ChemLab Spatial HUD Anchor
# Follows the 3D projected screen position of the targeted laboratory apparatus
# Renders subtle corner framing brackets and contextual distance indicators

extends Control
class_name SpatialHUDAnchor

@export var bracket_color: Color = Color(0.22, 0.88, 1.0, 0.75) # #38E1FF
@export var bracket_size: float = 16.0
@export var corner_length: float = 5.0
@export var line_width: float = 1.5

var distance_text: String = ""

func _ready() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE

func update_target(screen_pos: Vector2, distance_m: float) -> void:
	position = screen_pos
	distance_text = "%.1fm" % distance_m
	visible = true
	queue_redraw()

func clear_target() -> void:
	visible = false

func _draw() -> void:
	var half = bracket_size * 0.5
	var cl = corner_length
	var col = bracket_color

	# Top-Left corner
	draw_line(Vector2(-half, -half), Vector2(-half + cl, -half), col, line_width)
	draw_line(Vector2(-half, -half), Vector2(-half, -half + cl), col, line_width)

	# Top-Right corner
	draw_line(Vector2(half, -half), Vector2(half - cl, -half), col, line_width)
	draw_line(Vector2(half, -half), Vector2(half, -half + cl), col, line_width)

	# Bottom-Left corner
	draw_line(Vector2(-half, half), Vector2(-half + cl, half), col, line_width)
	draw_line(Vector2(-half, half), Vector2(-half, half - cl), col, line_width)

	# Bottom-Right corner
	draw_line(Vector2(half, half), Vector2(half - cl, half), col, line_width)
	draw_line(Vector2(half, half), Vector2(half, half - cl), col, line_width)

	# Draw subtle distance string if set
	if not distance_text.is_empty():
		var font = ThemeDB.fallback_font
		var font_size = 11
		if font:
			draw_string(font, Vector2(half + 6.0, 4.0), distance_text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, col)
