# ChemLab High-Tech Precision Reticle
# Procedurally renders a subtle dot / circle reticle with dynamic hover state
# Adheres to ChemLab palette: Clinical White (#FAFAFA) & Cyan Accent (#38E1FF)

extends Control
class_name CrosshairReticle

@export var color_idle: Color = Color(0.96, 0.96, 0.98, 0.65) # Clinical White with alpha
@export var color_hover: Color = Color(0.22, 0.88, 1.0, 0.95) # Cyan Accent (#38E1FF)
@export var dot_radius: float = 2.0
@export var ring_radius: float = 8.0
@export var tick_length: float = 4.0
@export var tick_gap: float = 4.0

var is_hovering: bool = false
var hover_factor: float = 0.0

func _ready() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE

func _process(delta: float) -> void:
	var target_factor = 1.0 if is_hovering else 0.0
	if not is_equal_approx(hover_factor, target_factor):
		hover_factor = lerpf(hover_factor, target_factor, 14.0 * delta)
		queue_redraw()

func set_hover(hover: bool) -> void:
	if is_hovering != hover:
		is_hovering = hover
		queue_redraw()

func _draw() -> void:
	var col = color_idle.lerp(color_hover, hover_factor)
	var active_ring = ring_radius + hover_factor * 2.0
	var active_dot = dot_radius + hover_factor * 0.75

	# Center dot
	draw_circle(Vector2.ZERO, active_dot, col)

	# Outer subtle circle / ring
	var ring_col = Color(col.r, col.g, col.b, col.a * (0.35 + hover_factor * 0.35))
	draw_arc(Vector2.ZERO, active_ring, 0.0, TAU, 32, ring_col, 1.0, true)

	# 4 Precision Axis Ticks
	var inner_gap = active_ring + tick_gap
	var outer_len = inner_gap + tick_length + hover_factor * 2.0

	# Left
	draw_line(Vector2(-outer_len, 0), Vector2(-inner_gap, 0), col, 1.0)
	# Right
	draw_line(Vector2(inner_gap, 0), Vector2(outer_len, 0), col, 1.0)
	# Top
	draw_line(Vector2(0, -outer_len), Vector2(0, -inner_gap), col, 1.0)
	# Bottom
	draw_line(Vector2(0, inner_gap), Vector2(0, outer_len), col, 1.0)
