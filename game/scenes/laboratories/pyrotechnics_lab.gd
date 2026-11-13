# Athanor Ascension — Pyrotechnics Laboratory
# A licensed test bay: composition bench, blast shield, burn pad and formulation
# terminal. All arithmetic is local (PyrotechnicsModel), so the lab works offline.
extends Node3D
class_name PyrotechnicsLab

const Model = preload("res://scripts/labs/pyrotechnics_model.gd")
const PLAYER_SCENE = preload("res://scenes/player/player_controller.tscn")
const HUB_SCENE: String = "res://scenes/laboratories/lab_hub.tscn"
const DATA_PATH: String = "res://data/synthesis/pyrotechnics.json"

const CYAN := Color(0.24, 0.85, 0.92)
const AMBER := Color(1.0, 0.72, 0.28)
const RED := Color(1.0, 0.38, 0.34)
const GREEN := Color(0.38, 0.86, 0.65)
const TEXT := Color(0.88, 0.92, 0.95)
const DIM := Color(0.52, 0.62, 0.70)

var formulations: Array = []
var selected_index: int = 0
var burn_time: float = 0.0
var burn_duration: float = 1.6
var is_burning: bool = false
var last_result: Dictionary = {}

var _flash: MeshInstance3D
var _flash_light: OmniLight3D
var _sparks: GPUParticles3D
var _title: Label
var _stats: RichTextLabel
var _warnings: RichTextLabel
var _selector: OptionButton
var _burn_button: Button
var _log: RichTextLabel
var _player: Node3D


func _ready() -> void:
	_build_room()
	_load_formulations()
	_build_ui()
	_spawn_player()
	if not formulations.is_empty():
		_select_formulation(0)


# =============================================================================
# ROOM
# =============================================================================

func _mat(color: Color, metallic: float = 0.0, roughness: float = 0.6) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metallic
	material.roughness = roughness
	return material


func _box(name: String, size: Vector3, position: Vector3, material: Material, parent: Node = self) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.name = name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = position
	parent.add_child(instance)
	return instance


func _build_room() -> void:
	var epoxy := _mat(Color(0.055, 0.062, 0.072), 0.2, 0.35)
	var steel := _mat(Color(0.42, 0.45, 0.50), 0.8, 0.28)
	var wall := _mat(Color(0.10, 0.11, 0.13), 0.1, 0.7)
	var concrete := _mat(Color(0.16, 0.16, 0.15), 0.0, 0.9)

	_box("Floor", Vector3(18, 0.2, 14), Vector3(0, -0.1, 0), epoxy)
	_box("Ceiling", Vector3(18, 0.2, 14), Vector3(0, 4.2, 0), wall)
	_box("WallNorth", Vector3(18, 4.2, 0.3), Vector3(0, 2.1, -7), wall)
	_box("WallSouth", Vector3(18, 4.2, 0.3), Vector3(0, 2.1, 7), wall)
	_box("WallEast", Vector3(0.3, 4.2, 14), Vector3(9, 2.1, 0), wall)
	_box("WallWest", Vector3(0.3, 4.2, 14), Vector3(-9, 2.1, 0), wall)

	# Composition bench along the north wall.
	_box("BenchTop", Vector3(6.0, 0.12, 1.4), Vector3(-2.5, 1.05, -5.8), steel)
	_box("BenchBody", Vector3(5.6, 0.95, 1.1), Vector3(-2.5, 0.5, -5.8), _mat(Color(0.08, 0.09, 0.11), 0.3, 0.5))
	_box("BenchKick", Vector3(5.6, 0.12, 0.1), Vector3(-2.5, 0.12, -5.3), _mat(Color(0.30, 0.32, 0.35), 0.6, 0.4))

	# Blast shield between bench and burn pad.
	var shield_mat := _mat(Color(0.55, 0.75, 0.85, 0.22), 0.1, 0.05)
	shield_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	shield_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var shield := _box("BlastShield", Vector3(3.6, 1.8, 0.08), Vector3(2.6, 1.9, -4.2), shield_mat)
	shield.rotation_degrees.y = 18.0

	# Burn pad in a sand tray.
	_box("SandTray", Vector3(2.4, 0.25, 2.4), Vector3(2.8, 0.12, -2.0), concrete)
	_box("SandBed", Vector3(2.2, 0.08, 2.2), Vector3(2.8, 0.28, -2.0), _mat(Color(0.72, 0.62, 0.40), 0.0, 1.0))

	# Steel firing line.
	_box("FiringLine", Vector3(0.12, 0.02, 3.2), Vector3(0.9, 0.02, -2.0), _mat(AMBER, 0.4, 0.5))

	# Magazine cabinet and extinguisher.
	_box("MagazineCabinet", Vector3(1.2, 2.0, 0.8), Vector3(-7.2, 1.0, -5.6), _mat(Color(0.35, 0.10, 0.08), 0.4, 0.45))
	_box("CabinetDoor", Vector3(1.1, 1.9, 0.05), Vector3(-7.2, 1.0, -5.18), _mat(Color(0.45, 0.14, 0.10), 0.5, 0.35))
	_box("Extinguisher", Vector3(0.28, 0.75, 0.28), Vector3(-6.0, 0.4, -5.7), _mat(RED, 0.2, 0.4))

	# Ceiling lights: two warm work lamps plus a cool rim.
	for x in [-4.0, 2.5]:
		var lamp := OmniLight3D.new()
		lamp.position = Vector3(x, 4.0, -3.0)
		lamp.light_color = Color(1.0, 0.93, 0.82)
		lamp.light_energy = 1.5
		lamp.omni_range = 10.0
		add_child(lamp)
	var rim := OmniLight3D.new()
	rim.position = Vector3(4.5, 3.2, 1.5)
	rim.light_color = Color(0.45, 0.70, 1.0)
	rim.light_energy = 1.1
	rim.omni_range = 12.0
	add_child(rim)

	_build_flash_rig()


func _build_flash_rig() -> void:
	var flash_mesh := SphereMesh.new()
	flash_mesh.radius = 0.32
	flash_mesh.height = 0.64
	var flash_mat := StandardMaterial3D.new()
	flash_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	flash_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	flash_mat.emission_enabled = true
	flash_mat.emission = AMBER
	flash_mat.emission_energy_multiplier = 6.0
	flash_mat.albedo_color = Color(1.0, 0.8, 0.4, 0.9)
	_flash = MeshInstance3D.new()
	_flash.name = "BurnFlash"
	_flash.mesh = flash_mesh
	_flash.material_override = flash_mat
	_flash.position = Vector3(2.8, 0.45, -2.0)
	_flash.scale = Vector3.ONE * 0.01
	_flash.visible = false
	add_child(_flash)

	_flash_light = OmniLight3D.new()
	_flash_light.name = "BurnLight"
	_flash_light.position = _flash.position + Vector3(0, 0.3, 0)
	_flash_light.light_color = AMBER
	_flash_light.light_energy = 0.0
	_flash_light.omni_range = 9.0
	add_child(_flash_light)

	_sparks = GPUParticles3D.new()
	_sparks.name = "Sparks"
	_sparks.position = _flash.position + Vector3(0, 0.2, 0)
	_sparks.emitting = false
	_sparks.amount = 48
	_sparks.lifetime = 0.9
	var process := ParticleProcessMaterial.new()
	process.direction = Vector3(0, 1, 0)
	process.spread = 28.0
	process.initial_velocity_min = 1.5
	process.initial_velocity_max = 4.5
	process.gravity = Vector3(0, -9.8, 0)
	process.scale_min = 0.02
	process.scale_max = 0.06
	var spark_mat := StandardMaterial3D.new()
	spark_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark_mat.albedo_color = AMBER
	spark_mat.emission_enabled = true
	spark_mat.emission = AMBER
	spark_mat.emission_energy_multiplier = 5.0
	_sparks.process_material = process
	var spark_quad := QuadMesh.new()
	spark_quad.size = Vector2(0.05, 0.05)
	spark_quad.material = spark_mat
	_sparks.draw_pass_1 = spark_quad
	add_child(_sparks)


func _spawn_player() -> void:
	var packed: PackedScene = PLAYER_SCENE
	if packed == null:
		return
	_player = packed.instantiate()
	_player.position = Vector3(0.0, 1.0, 4.2)
	add_child(_player)


# =============================================================================
# DATA & UI
# =============================================================================

func _load_formulations() -> void:
	if not FileAccess.file_exists(DATA_PATH):
		push_warning("pyrotechnics.json missing")
		return
	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if parsed is Dictionary:
		formulations = parsed.get("formulations", [])


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "HUD"
	add_child(layer)

	var panel := PanelContainer.new()
	panel.position = Vector2(18, 18)
	panel.custom_minimum_size = Vector2(420, 520)
	layer.add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 16)
	margin.add_theme_constant_override("margin_right", 16)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	panel.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	margin.add_child(column)

	_title = Label.new()
	_title.text = "PYROTECHNICS TEST BAY"
	_title.add_theme_color_override("font_color", AMBER)
	_title.add_theme_font_size_override("font_size", 18)
	column.add_child(_title)

	var subtitle := Label.new()
	subtitle.text = "Licensed composition bay · Class 1.4 magazine"
	subtitle.add_theme_color_override("font_color", DIM)
	subtitle.add_theme_font_size_override("font_size", 11)
	column.add_child(subtitle)

	_selector = OptionButton.new()
	for formulation in formulations:
		_selector.add_item(str(formulation.get("name", "Formulation")))
	_selector.item_selected.connect(_select_formulation)
	column.add_child(_selector)

	_stats = RichTextLabel.new()
	_stats.bbcode_enabled = true
	_stats.fit_content = true
	_stats.custom_minimum_size = Vector2(0, 190)
	_stats.add_theme_font_size_override("normal_font_size", 12)
	column.add_child(_stats)

	_warnings = RichTextLabel.new()
	_warnings.bbcode_enabled = true
	_warnings.fit_content = true
	_warnings.custom_minimum_size = Vector2(0, 70)
	_warnings.add_theme_font_size_override("normal_font_size", 11)
	column.add_child(_warnings)

	_burn_button = Button.new()
	_burn_button.text = "RUN BURN TEST"
	_burn_button.custom_minimum_size = Vector2(0, 38)
	_burn_button.pressed.connect(run_burn_test)
	column.add_child(_burn_button)

	_log = RichTextLabel.new()
	_log.bbcode_enabled = true
	_log.scroll_active = true
	_log.custom_minimum_size = Vector2(0, 110)
	_log.add_theme_font_size_override("normal_font_size", 11)
	column.add_child(_log)

	var back := Button.new()
	back.text = "← Return to Hub (Esc)"
	back.pressed.connect(_return_to_hub)
	column.add_child(back)

	_log.append_text("[color=#6ddbaa]✓ Bay calibrated. Sand tray dry.[/color]\n")


func _select_formulation(index: int) -> void:
	if index < 0 or index >= formulations.size():
		return
	selected_index = index
	var formulation: Dictionary = formulations[index]
	last_result = Model.evaluate(formulation)
	_selector.select(index)

	var color: Color = last_result["flame_color"]
	_stats.text = (
		"[b]%s[/b]\n"
		+ "[color=#85949f]%s[/color]\n\n"
		+ "Oxygen balance   [b]%+.3f[/b] g O₂/g\n"
		+ "Burn rate        [b]%.1f[/b] mm/s\n"
		+ "Flame temperature [b]%.0f[/b] °C\n"
		+ "Emission         [b]%d nm[/b] [color=#%s]■[/color]\n"
		+ "Sensitivity      [b]%s[/b]\n"
		+ "Hazard class     [b]%s[/b]"
	) % [
		str(formulation.get("name", "")),
		str(formulation.get("effect", "")),
		float(last_result["oxygen_balance"]),
		float(last_result["burn_rate_mm_s"]),
		float(last_result["flame_temp_c"]),
		int(last_result["emission_nm"]),
		color.to_html(false),
		str(last_result["sensitivity"]).to_upper(),
		str(last_result["hazard_class"]),
	]

	var warning_text := ""
	for warning in last_result.get("warnings", []):
		warning_text += "[color=#ffb45c]! %s[/color]\n" % str(warning)
	if warning_text.is_empty():
		warning_text = "[color=#6ddbaa]No composition warnings.[/color]"
	_warnings.text = warning_text


func run_burn_test() -> void:
	if is_burning or formulations.is_empty():
		return
	var formulation: Dictionary = formulations[selected_index]
	last_result = Model.evaluate(formulation)
	is_burning = true
	burn_time = 0.0
	var color: Color = last_result["flame_color"]
	_flash.visible = true
	_flash.scale = Vector3.ONE * 0.05
	var material := _flash.material_override as StandardMaterial3D
	if material != null:
		material.emission = color
		material.albedo_color = Color(color.r, color.g, color.b, 0.9)
	_flash_light.light_color = color
	_sparks.emitting = true
	var spark_material := (_sparks.draw_pass_1 as QuadMesh).material as StandardMaterial3D
	if spark_material != null:
		spark_material.emission = color
		spark_material.albedo_color = color
	_burn_button.disabled = true
	_log.append_text(
		"[color=#ffcf7a]▶ %s — %.1f mm/s, %.0f °C, %d nm[/color]\n"
		% [
			str(formulation.get("name", "")),
			float(last_result["burn_rate_mm_s"]),
			float(last_result["flame_temp_c"]),
			int(last_result["emission_nm"]),
		]
	)


func _process(delta: float) -> void:
	if not is_burning:
		return
	burn_time += delta
	var progress: float = clampf(burn_time / burn_duration, 0.0, 1.0)
	var pulse: float = sin(progress * PI)
	_flash.scale = Vector3.ONE * (0.25 + pulse * 1.1)
	_flash_light.light_energy = pulse * 3.2
	_sparks.amount_ratio = clampf(1.0 - progress * 0.7, 0.0, 1.0)
	if progress >= 1.0:
		is_burning = false
		_flash.visible = false
		_flash_light.light_energy = 0.0
		_sparks.emitting = false
		_burn_button.disabled = false
		_log.append_text("[color=#6ddbaa]✓ Burn complete. Tray inspected.[/color]\n")


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		_return_to_hub()


func _return_to_hub() -> void:
	if ResourceLoader.exists(HUB_SCENE):
		get_tree().change_scene_to_file(HUB_SCENE)
