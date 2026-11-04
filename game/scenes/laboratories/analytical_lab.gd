# Analytical Chemistry Laboratory Scene Controller (Godot 4 Engine)
# Path: res://scenes/laboratories/analytical_lab.gd
# Manages 3D room state, player initialization, fume hood sash kinematics,
# apparatus spawn markers, and QuestManager event synchronization.

extends Node3D
class_name AnalyticalLab

# =============================================================================
# SIGNALS
# =============================================================================
signal laboratory_initialized(lab_name: String, parameters: Dictionary)
signal fume_hood_sash_moved(is_open: bool, height_meters: float)
signal player_spawned(player_node: Node, spawn_position: Vector3)
signal apparatus_spawned(apparatus_name: String, marker_name: String, node: Node)

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================
const LAB_NAME: String = "Analytical Chemistry Core Laboratory"
const LAB_ARCHETYPE_ID: String = "analytical_lab_01"
const DEFAULT_PLAYER_SPAWN: Vector3 = Vector3(0.0, 1.0, 2.5)

# Fume Hood Sash Kinematics
const SASH_CLOSED_Y: float = 0.95
const SASH_WORKING_Y: float = 1.30  # 35 cm OSHA safe working sash opening
const SASH_OPEN_Y: float = 1.70     # Walk-up loading opening
const SASH_TRANSITION_DURATION: float = 0.55 # Smooth pneumatic glide

# Physical laboratory environment parameters
const AMBIENT_TEMPERATURE_C: float = 21.5
const BAROMETRIC_PRESSURE_KPA: float = 101.325
const NOMINAL_EXHAUST_CFM: float = 850.0 # ANSI/AIHA Z9.5 certified

# =============================================================================
# EXPORTED NODES & PATHS
# =============================================================================
@export_group("Laboratory References")
@export var player_spawn_point: Marker3D
@export var fume_hood_sash: Node3D
@export var fume_hood_interaction_area: Area3D
@export var fume_hood_interior_light: OmniLight3D
@export var bench_spotlight: OmniLight3D
@export var ambient_light: OmniLight3D

@export_group("Spawn Point Markers")
@export var spawn_erlenmeyer: Marker3D
@export var spawn_beaker: Marker3D
@export var spawn_bunsen_burner: Marker3D
@export var spawn_magnetic_stirrer: Marker3D
@export var spawn_analytical_balance: Marker3D
@export var spawn_reagent_hcl: Marker3D
@export var spawn_reagent_naoh: Marker3D
@export var spawn_reagent_phenolphthalein: Marker3D
@export var spawn_fume_hood_apparatus: Marker3D

# =============================================================================
# RUNTIME STATE
# =============================================================================
var is_sash_open: bool = false
var current_sash_height: float = SASH_WORKING_Y
var is_player_in_fume_hood_zone: bool = false
var player_instance: Node = null
var sash_tween: Tween = null

var lab_parameters: Dictionary = {
	"lab_id": LAB_ARCHETYPE_ID,
	"lab_title": LAB_NAME,
	"ambient_temperature_c": AMBIENT_TEMPERATURE_C,
	"barometric_pressure_kpa": BAROMETRIC_PRESSURE_KPA,
	"fume_hood_active": true,
	"fume_hood_face_velocity_fpm": 100.0,
	"cleanroom_containment_grade": "ISO Class 7 / Standard Chemical Class 1",
	"safety_shower_ready": true,
	"eye_wash_ready": true
}

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	print(">>> [AnalyticalLab] Initializing 3D Analytical Chemistry Laboratory...")
	# Vitals HUD only belongs on gameplay scenes, never on the menu/loading screen.
	var vitals := get_node_or_null("/root/PlayerVitals")
	if vitals != null and vitals.has_method("set_hud_visible"):
		vitals.set_hud_visible(true)
	_resolve_node_references()
	_initialize_laboratory_state()
	_spawn_or_position_player()
	_setup_fume_hood_interaction()
	_notify_quest_manager()
	laboratory_initialized.emit(LAB_NAME, lab_parameters)
	print(">>> [AnalyticalLab] Laboratory initialization complete. Ready for experiment simulation.")


func _exit_tree() -> void:
	var vitals := get_node_or_null("/root/PlayerVitals")
	if vitals != null and vitals.has_method("set_hud_visible"):
		vitals.set_hud_visible(false)


func _resolve_node_references() -> void:
	# Fallback resolution using get_node_or_null if exports are unlinked
	if not player_spawn_point:
		player_spawn_point = get_node_or_null("SpawnPoints/Spawn_Player") as Marker3D
	if not fume_hood_sash:
		fume_hood_sash = get_node_or_null("Furniture/FumeHoodStation/FumeHood_SashAssembly") as Node3D
	if not fume_hood_interaction_area:
		fume_hood_interaction_area = get_node_or_null("Furniture/FumeHoodStation/InteractionArea_Sash") as Area3D
	if not fume_hood_interior_light:
		fume_hood_interior_light = get_node_or_null("Lighting/Light_FumeHood_Interior") as OmniLight3D
	if not bench_spotlight:
		bench_spotlight = get_node_or_null("Lighting/Light_Bench_Spotlight") as OmniLight3D

	# Spawn markers
	if not spawn_erlenmeyer:
		spawn_erlenmeyer = get_node_or_null("SpawnPoints/Spawn_ErlenmeyerFlask") as Marker3D
	if not spawn_beaker:
		spawn_beaker = get_node_or_null("SpawnPoints/Spawn_Beaker") as Marker3D
	if not spawn_bunsen_burner:
		spawn_bunsen_burner = get_node_or_null("SpawnPoints/Spawn_BunsenBurner") as Marker3D
	if not spawn_magnetic_stirrer:
		spawn_magnetic_stirrer = get_node_or_null("SpawnPoints/Spawn_MagneticStirrer") as Marker3D
	if not spawn_analytical_balance:
		spawn_analytical_balance = get_node_or_null("SpawnPoints/Spawn_AnalyticalBalance") as Marker3D
	if not spawn_reagent_hcl:
		spawn_reagent_hcl = get_node_or_null("SpawnPoints/Spawn_Reagent_HCl") as Marker3D
	if not spawn_reagent_naoh:
		spawn_reagent_naoh = get_node_or_null("SpawnPoints/Spawn_Reagent_NaOH") as Marker3D
	if not spawn_reagent_phenolphthalein:
		spawn_reagent_phenolphthalein = get_node_or_null("SpawnPoints/Spawn_Reagent_Phenolphthalein") as Marker3D
	if not spawn_fume_hood_apparatus:
		spawn_fume_hood_apparatus = get_node_or_null("SpawnPoints/Spawn_FumeHood_Apparatus") as Marker3D


# =============================================================================
# 1. LABORATORY STATE INITIALIZATION
# =============================================================================

func _initialize_laboratory_state() -> void:
	# Set baseline lighting optimization for Intel Iris Xe Compatibility renderer
	if bench_spotlight:
		bench_spotlight.omni_range = 4.8
		bench_spotlight.omni_attenuation = 1.0
		bench_spotlight.light_energy = 1.6
		bench_spotlight.light_color = Color(1.0, 0.98, 0.94) # 4000 K soft neutral white

	if fume_hood_interior_light:
		fume_hood_interior_light.omni_range = 2.6
		fume_hood_interior_light.light_energy = 2.0
		fume_hood_interior_light.light_color = Color(0.92, 0.97, 1.0) # 5000 K daylight fluorescent

	# Set initial sash position
	if fume_hood_sash:
		fume_hood_sash.position.y = SASH_CLOSED_Y
		current_sash_height = SASH_CLOSED_Y
		is_sash_open = false


# =============================================================================
# 2. PLAYER SPAWN & LOCOMOTION PLACEMENT
# =============================================================================

func _spawn_or_position_player() -> void:
	var spawn_pos = DEFAULT_PLAYER_SPAWN
	if player_spawn_point:
		spawn_pos = player_spawn_point.global_position

	# Look for existing player in scene
	var existing_player = get_tree().get_first_node_in_group("player")
	if existing_player:
		player_instance = existing_player
		player_instance.global_position = spawn_pos
		# Face workbench (-Z axis)
		player_instance.rotation = Vector3(0.0, deg_to_rad(180.0), 0.0)
		player_spawned.emit(player_instance, spawn_pos)
		return

	# Load and instantiate player scene
	var candidate_paths = [
		"res://scenes/player/player_controller.tscn",
		"res://scenes/player/player.tscn"
	]
	for player_scene_path in candidate_paths:
		if ResourceLoader.exists(player_scene_path):
			var player_resource = load(player_scene_path) as PackedScene
			if player_resource:
				player_instance = player_resource.instantiate()
				add_child(player_instance)
				player_instance.global_position = spawn_pos
				player_instance.rotation = Vector3(0.0, deg_to_rad(180.0), 0.0)
				player_spawned.emit(player_instance, spawn_pos)
				print(">>> [AnalyticalLab] Player successfully spawned from %s at: %s" % [player_scene_path, spawn_pos])
				return

	print(">>> [AnalyticalLab] Warning: Player scene not found. Running in inspection mode.")


# =============================================================================
# 3. FUME HOOD SASH INTERACTION (E-KEY KINEMATICS)
# =============================================================================

func _setup_fume_hood_interaction() -> void:
	if not fume_hood_interaction_area:
		return

	fume_hood_interaction_area.body_entered.connect(_on_fume_hood_area_body_entered)
	fume_hood_interaction_area.body_exited.connect(_on_fume_hood_area_body_exited)


func _on_fume_hood_area_body_entered(body: Node3D) -> void:
	if body.is_in_group("player") or body == player_instance:
		is_player_in_fume_hood_zone = true
		_update_player_hud_prompt("[E] %s Fume Hood Sash" % ("Close" if is_sash_open else "Open"))


func _on_fume_hood_area_body_exited(body: Node3D) -> void:
	if body.is_in_group("player") or body == player_instance:
		is_player_in_fume_hood_zone = false
		_clear_player_hud_prompt()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E and is_player_in_fume_hood_zone:
			toggle_fume_hood_sash()


func toggle_fume_hood_sash() -> void:
	if is_sash_open:
		close_fume_hood_sash()
	else:
		open_fume_hood_sash()


func open_fume_hood_sash(target_y: float = SASH_OPEN_Y) -> void:
	if not fume_hood_sash:
		return

	if sash_tween and sash_tween.is_running():
		sash_tween.kill()

	sash_tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	sash_tween.tween_property(fume_hood_sash, "position:y", target_y, SASH_TRANSITION_DURATION)

	is_sash_open = true
	current_sash_height = target_y
	lab_parameters["fume_hood_sash_open"] = true
	fume_hood_sash_moved.emit(true, target_y)

	# Calculate face velocity reduction when sash is opened high
	var opening_area_m2 = 1.6 * (target_y - SASH_CLOSED_Y)
	var face_velocity_fpm = clampf(100.0 * (0.35 / maxf(0.1, target_y - SASH_CLOSED_Y)), 45.0, 120.0)
	lab_parameters["fume_hood_face_velocity_fpm"] = face_velocity_fpm

	if is_player_in_fume_hood_zone:
		_update_player_hud_prompt("[E] Close Fume Hood Sash | Face Vel: %.0f FPM" % face_velocity_fpm)

	print(">>> [AnalyticalLab] Fume hood sash opened to %.2f m (Face Velocity: %.0f FPM)" % [target_y, face_velocity_fpm])


func close_fume_hood_sash() -> void:
	if not fume_hood_sash:
		return

	if sash_tween and sash_tween.is_running():
		sash_tween.kill()

	sash_tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
	sash_tween.tween_property(fume_hood_sash, "position:y", SASH_CLOSED_Y, SASH_TRANSITION_DURATION)

	is_sash_open = false
	current_sash_height = SASH_CLOSED_Y
	lab_parameters["fume_hood_sash_open"] = false
	lab_parameters["fume_hood_face_velocity_fpm"] = 100.0
	fume_hood_sash_moved.emit(false, SASH_CLOSED_Y)

	if is_player_in_fume_hood_zone:
		_update_player_hud_prompt("[E] Open Fume Hood Sash (Airflow: Sealed)")

	print(">>> [AnalyticalLab] Fume hood sash closed to safe sealed position.")


func _update_player_hud_prompt(prompt_text: String) -> void:
	if player_instance and player_instance.has_method("_update_interaction_prompt"):
		player_instance._update_interaction_prompt("Fume Hood Sash", prompt_text)


func _clear_player_hud_prompt() -> void:
	if player_instance and player_instance.has_method("_hide_interaction_prompt"):
		player_instance._hide_interaction_prompt()


# =============================================================================
# 4. QUEST MANAGER NOTIFICATION & SYNCHRONIZATION
# =============================================================================

func _notify_quest_manager() -> void:
	var qm: Node = null

	# 1. Check Autoload singleton
	var root = get_tree().root if get_tree() else null
	if root and root.has_node("QuestManager"):
		qm = root.get_node("QuestManager")
	elif Engine.has_singleton("QuestManager"):
		qm = Engine.get_singleton("QuestManager")

	if qm:
		print(">>> [AnalyticalLab] Notifying QuestManager: Player entered Analytical Chemistry Lab.")
		# Check if QuestManager provides custom laboratory entry method
		if qm.has_method("on_laboratory_entered"):
			qm.call("on_laboratory_entered", LAB_ARCHETYPE_ID, lab_parameters)
		elif qm.has_method("notify_location_entered"):
			qm.call("notify_location_entered", "analytical_lab")

		# If orientation quest is active, verify room readiness
		if qm.has_method("get_active_quest"):
			var active_q = qm.call("get_active_quest") as Dictionary
			if not active_q.is_empty():
				print(">>> [AnalyticalLab] Active Quest: '%s' is synchronized with laboratory environment." % active_q.get("title", ""))
	else:
		print(">>> [AnalyticalLab] QuestManager singleton not mounted. Standalone lab mode active.")


# =============================================================================
# 5. APPARATUS & REAGENT GETTERS / SPAWNERS
# =============================================================================

func get_spawn_marker(marker_key: String) -> Marker3D:
	match marker_key.to_lower():
		"erlenmeyer", "erlenmeyer_flask": return spawn_erlenmeyer
		"beaker": return spawn_beaker
		"bunsen_burner", "burner": return spawn_bunsen_burner
		"magnetic_stirrer", "stirrer": return spawn_magnetic_stirrer
		"analytical_balance", "balance": return spawn_analytical_balance
		"hcl", "reagent_hcl": return spawn_reagent_hcl
		"naoh", "reagent_naoh": return spawn_reagent_naoh
		"phenolphthalein", "indicator": return spawn_reagent_phenolphthalein
		"fume_hood", "fume_hood_apparatus": return spawn_fume_hood_apparatus
		_: return null


func get_all_spawn_markers() -> Dictionary:
	return {
		"erlenmeyer_flask": spawn_erlenmeyer,
		"beaker": spawn_beaker,
		"bunsen_burner": spawn_bunsen_burner,
		"magnetic_stirrer": spawn_magnetic_stirrer,
		"analytical_balance": spawn_analytical_balance,
		"reagent_hcl": spawn_reagent_hcl,
		"reagent_naoh": spawn_reagent_naoh,
		"reagent_phenolphthalein": spawn_reagent_phenolphthalein,
		"fume_hood_apparatus": spawn_fume_hood_apparatus
	}
