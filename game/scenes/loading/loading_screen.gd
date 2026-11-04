# Athanor Ascension — Loading Screen
# Animated alchemical sigil + procedural laboratory backdrop. Loads the main menu
# on a worker thread and never blocks the window: the first frame is up in <100 ms.

extends Control

const MAIN_MENU: String = "res://scenes/main_menu/main_menu.tscn"
const BACKDROP_SCRIPT = preload("res://ui/apparatus_backdrop.gd")
const MIN_DISPLAY_SECONDS: float = 1.8

const TIPS: Array[String] = [
	"Paschen's law decides whether a plasma strikes, not the voltage alone.",
	"Curated genome hotspots carry real HGVS annotations; everything else is a VUS.",
	"Suits trade mobility for protection. Read the hazard before the label.",
	"A fusor is a neutron source, not a power plant. Distance is free shielding.",
	"Record the mass, the moles and the temperature. Memory is not a lab notebook.",
	"Cooling water flows opposite to vapour. Counter-current is not a detail."
]

var _progress: float = 0.0
var _elapsed: float = 0.0
var _tip_index: int = 0
var _tip_timer: float = 0.0
var _thread_id: int = -1
var _load_state: int = 0
var _target_scene: PackedScene = null
var _changing: bool = false
var _title_label: Label
var _status_label: Label
var _tip_label: Label


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var backdrop := Control.new()
	backdrop.set_script(BACKDROP_SCRIPT)
	add_child(backdrop)
	move_child(backdrop, 0)

	_title_label = Label.new()
	_title_label.text = "ATHANOR ASCENSION"
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_title_label.offset_left = -320.0
	_title_label.offset_right = 320.0
	_title_label.offset_top = 92.0
	_title_label.add_theme_font_size_override("font_size", 44)
	_title_label.add_theme_color_override("font_color", Color(0.88, 0.93, 0.96))
	add_child(_title_label)

	var subtitle := Label.new()
	subtitle.text = "the furnace remembers"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.set_anchors_preset(Control.PRESET_CENTER_TOP)
	subtitle.offset_left = -220.0
	subtitle.offset_right = 220.0
	subtitle.offset_top = 148.0
	subtitle.add_theme_font_size_override("font_size", 13)
	subtitle.add_theme_color_override("font_color", Color(0.55, 0.68, 0.74))
	add_child(subtitle)

	_status_label = Label.new()
	_status_label.text = "preparing the athanor"
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_status_label.offset_left = -280.0
	_status_label.offset_right = 280.0
	_status_label.offset_top = -96.0
	_status_label.add_theme_font_size_override("font_size", 12)
	_status_label.add_theme_color_override("font_color", Color(0.62, 0.75, 0.8))
	add_child(_status_label)

	_tip_label = Label.new()
	_tip_label.text = TIPS[0]
	_tip_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tip_label.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_tip_label.offset_left = -380.0
	_tip_label.offset_right = 380.0
	_tip_label.offset_top = -56.0
	_tip_label.add_theme_font_size_override("font_size", 11)
	_tip_label.add_theme_color_override("font_color", Color(0.42, 0.52, 0.58))
	add_child(_tip_label)

	var skip := Button.new()
	skip.text = "skip  ›"
	skip.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	skip.offset_left = -96.0
	skip.offset_right = -20.0
	skip.offset_top = -40.0
	skip.offset_bottom = -12.0
	skip.pressed.connect(_go_to_menu)
	add_child(skip)

	var fade := ColorRect.new()
	fade.color = Color(0.02, 0.03, 0.04, 1.0)
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(fade)
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 0.0, 0.45)
	tween.tween_callback(func(): fade.queue_free())

	_thread_id = ResourceLoader.load_threaded_request(MAIN_MENU)
	set_process(true)


func _process(delta: float) -> void:
	_elapsed += delta
	_tip_timer += delta
	if _tip_timer > 3.2:
		_tip_timer = 0.0
		_tip_index = (_tip_index + 1) % TIPS.size()
		_tip_label.text = TIPS[_tip_index]

	if _thread_id >= 0:
		var status := ResourceLoader.load_threaded_get_status(MAIN_MENU, [])
		match status:
			ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				_load_state = 0
			ResourceLoader.THREAD_LOAD_LOADED:
				_load_state = 1
			_:
				_load_state = -1

	var target := clampf(_elapsed / MIN_DISPLAY_SECONDS, 0.0, 1.0)
	if _load_state == 1:
		target = maxf(target, 0.55)
	_progress = maxf(_progress, target)
	_status_label.text = "preparing the athanor  ·  %d%%" % int(_progress * 100.0)

	if _elapsed >= MIN_DISPLAY_SECONDS and _load_state == 1 and not _changing:
		_go_to_menu()
	queue_redraw()


func _go_to_menu() -> void:
	if _changing:
		return
	_changing = true
	if _load_state == 1:
		_target_scene = ResourceLoader.load_threaded_get(MAIN_MENU)
	if _target_scene != null:
		get_tree().change_scene_to_packed(_target_scene)
	else:
		get_tree().change_scene_to_file(MAIN_MENU)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.022, 0.032, 0.042, 0.55), true)

	# Alchemical sigil: concentric rings, triangle and square, rotating at
	# different rates. Drawn with plain geometry, no textures.
	var center := Vector2(size.x * 0.5, size.y * 0.44)
	var radius := minf(size.y * 0.2, 170.0)
	draw_circle(center, radius * 0.42, Color(0.06, 0.12, 0.14, 0.55))
	draw_arc(center, radius, 0, TAU, 96, Color(0.32, 0.72, 0.78, 0.45), 1.5)
	draw_arc(center, radius * 0.86, 0, TAU, 96, Color(0.32, 0.72, 0.78, 0.22), 1.0)
	draw_arc(center, radius * 0.3, 0, TAU, 48, Color(0.85, 0.65, 0.3, 0.5), 1.4)

	var t := _elapsed
	for i in range(3):
		var angle := t * (0.25 + i * 0.18) + TAU * float(i) / 3.0
		var r := radius * (0.62 + i * 0.11)
		var a := center + Vector2(cos(angle), sin(angle)) * r
		var b := center + Vector2(cos(angle + TAU / 3.0), sin(angle + TAU / 3.0)) * r
		var c := center + Vector2(cos(angle + 2.0 * TAU / 3.0), sin(angle + 2.0 * TAU / 3.0)) * r
		draw_polyline(PackedVector2Array([a, b, c, a]), Color(0.5, 0.8, 0.82, 0.16), 1.0)

	# Progress arc.
	var arc_radius := radius * 1.12
	draw_arc(center, arc_radius, -PI * 0.5, -PI * 0.5 + TAU * _progress, 128, Color(0.35, 0.85, 0.9, 0.85), 3.0)
	for i in range(12):
		var angle := -PI * 0.5 + TAU * float(i) / 12.0
		var inner := center + Vector2(cos(angle), sin(angle)) * (arc_radius + 6.0)
		var outer := center + Vector2(cos(angle), sin(angle)) * (arc_radius + 11.0)
		draw_line(inner, outer, Color(0.3, 0.5, 0.55, 0.35), 1.0)
