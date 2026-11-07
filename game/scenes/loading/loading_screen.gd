# Athanor Ascension - Loading Screen
# Animated alchemical sigil with procedural glassware backdrop

extends Control

class_name LoadingScreen

@export var minimum_display_time: float = 3.0
@export var sigil_animation_speed: float = 1.0

var _start_time: float = 0.0
var _sigil_rotation: float = 0.0
var _pulse_phase: float = 0.0
var _particles: Array[Dictionary] = []
var _loading_complete: bool = false
var _transitioning: bool = false

# UI elements
var _sigil_texture: TextureRect
var _progress_bar: ProgressBar
var _loading_text: Label
var _subtitle_text: Label
var _apparatus_backdrop: ApparatusBackdrop

func _ready() -> void:
	_cache_nodes()
	_start_time = Time.get_ticks_msec() / 1000.0
	_init_particles()
	_start_loading()

func _cache_nodes() -> void:
	_sigil_texture = %SigilTexture
	_progress_bar = %ProgressBar
	_loading_text = %LoadingText
	_subtitle_text = %SubtitleText
	_apparatus_backdrop = %ApparatusBackdrop

	# Set initial text
	_loading_text.text = "Initializing Athanor..."
	_subtitle_text.text = "Real chemistry. Real physics. Offline."
	_progress_bar.value = 0

func _start_loading() -> void:
	# Simulate loading steps
	var steps = [
		{ "text": "Loading thermodynamic database...", "progress": 10, "delay": 0.5 },
		{ "text": "Initializing reaction engine...", "progress": 25, "delay": 0.8 },
		{ "text": "Loading PiHKAL/TiHKAL catalog...", "progress": 40, "delay": 1.0 },
		{ "text": "Preparing Aetherkin companions...", "progress": 55, "delay": 0.8 },
		{ "text": "Calibrating laboratory instruments...", "progress": 70, "delay": 0.6 },
		{ "text": "Establishing faction relations...", "progress": 80, "delay": 0.5 },
		{ "text": "Rendering cinematic environments...", "progress": 90, "delay": 0.5 },
		{ "text": "Finalizing safety protocols...", "progress": 95, "delay": 0.3 },
		{ "text": "Athanor ready.", "progress": 100, "delay": 0.5 }
	]

	_run_loading_sequence(steps)

async func _run_loading_sequence(steps: Array[Dictionary]) -> void:
	for step in steps:
		_loading_text.text = step.text
		_progress_bar.value = step.progress
		await get_tree().create_timer(step.delay).timeout

	_loading_complete = true
	_loading_text.text = "Press any key to begin"
	_subtitle_text.text = "Your laboratory awaits, Alchemist."
	_progress_bar.value = 100

	# Wait for minimum display time
	var elapsed = Time.get_ticks_msec() / 1000.0 - _start_time
	if elapsed < minimum_display_time:
		await get_tree().create_timer(minimum_display_time - elapsed).timeout

	# Wait for input
	await _wait_for_input()

	_transition_to_main_menu()

func _wait_for_input() -> void:
	var timer = Timer.new()
	timer.wait_time = 0.1
	timer.autostart = true

	while true:
		await timer.timeout
		if Input.is_any_key_pressed() or Input.is_mouse_button_pressed(0) or Input.is_joy_button_pressed(0, 0):
			break

func _transition_to_main_menu() -> void:
	_transitioning = true

	# Fade out
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "modulate:a", 0.0, 1.0)
	tween.tween_property(_progress_bar, "modulate:a", 0.0, 1.0)
	tween.tween_property(_loading_text, "modulate:a", 0.0, 1.0)
	tween.tween_property(_subtitle_text, "modulate:a", 0.0, 1.0)

	await tween.finished

	# Change scene
	get_tree().change_scene_to_file("res://scenes/main_menu/main_menu.tscn")

func _process(delta: float) -> void:
	# Rotate sigil
	_sigil_rotation += delta * sigil_animation_speed * 0.3

	# Pulse effect
	_pulse_phase += delta * 2.0

	# Update particles
	_update_particles(delta)

	# Rotate sigil texture
	if has_node("SigilTexture"):
		var sigil = get_node("SigilTexture")
		sigil.rotation = _sigil_rotation
		sigil.modulate = Color(1, 1, 1, 0.8 + sin(Time.get_ticks_msec() / 500.0) * 0.2)

	# Particle effects
	_update_sigil_particles()

func _update_particles(delta: float) -> void:
	# Spawn new particles around sigil
	if randf() < 0.02:
		_spawn_sigil_particle()

	# Update existing particles
	for particle in _particles:
		particle.life -= delta
		particle.alpha = particle.life / particle.max_life
		particle.pos += particle.vel * delta
		particle.vel *= 0.98  # Drag

	# Remove dead particles
	var alive = []
	for p in _particles:
		if p.life > 0:
			alive.append(p)
	_particles = alive

func _spawn_sigil_particle() -> void:
	var angle = randf_range(0.0, TAU)
	var radius = randf_range(50, 150)
	var speed = randf_range(20, 60)

	_particles.append({
		"pos": Vector2(cos(randf_range(0.0, TAU)) * 100, sin(randf_range(0.0, TAU)) * 100),
		"vel": Vector2(cos(randf_range(0.0, TAU)), sin(randf_range(0.0, TAU))) * randf_range(20, 60),
		"size": randf_range(2, 6),
		"color": Color(randf_range(0.2, 1.0), randf_range(0.4, 1.0), randf_range(0.8, 1.0), 1.0),
		"life": randf_range(1.0, 3.0),
		"max_life": randf_range(1.0, 3.0)
	})

func _update_sigil_particles() -> void:
	var canvas = get_canvas_item()
	for particle in _particles:
		var alpha = particle.life / particle.max_life
		draw_circle(particle.pos, particle.size * particle.life, particle.color * particle.alpha)

func _draw() -> void:
	# Draw background glow behind sigil
	var center = get_rect().size / 2
	var time = Time.get_ticks_msec() / 1000.0

	# Outer glow rings
	for i in range(3):
		var radius = 120 + i * 40 + sin(time * 2.0 + i) * 5
		var alpha = 0.15 / (i + 1)
		draw_circle(Vector2(0, 0), radius, Color(0.2, 0.5, 1.0, alpha), false, 3)

	# Alchemical symbols rotating
	for i in range(7):
		var angle = time * 0.5 + i * TAU / 7
		var r = 180 + sin(time * 0.7) * 10
		var pos = Vector2(cos(time * 0.5 + i * TAU / 7) * r, sin(time * 0.5 + i * TAU / 7) * r)
		var symbol = _get_alchemical_symbol(i)
		draw_string(get_theme_default_font(), pos, symbol, HORIZONTAL_ALIGNMENT_CENTER, -1, 24, Color(0.3, 0.6, 1.0, 0.6))

func _get_alchemical_symbol(index: int) -> String:
	var symbols = ["☉", "☽", "☿", "♀", "♁", "♂", "♃"]
	return symbols[index % symbols.size()]