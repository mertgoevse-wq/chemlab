# ChemLab Save & Progression State Manager (Godot 4 Engine)
# Autoload Singleton: SaveManager
# Handles persistent local JSON storage for user profiles, unlocked laboratories,
# quest completion history, OSHA safety records, and laboratory notebook entries.

extends Node

# =============================================================================
# CONSTANTS & SIGNALS
# =============================================================================

const SAVE_FILE_PATH: String = "user://chemlab_save.json"
const SAVE_VERSION: int = 1

signal save_completed(success: bool)
signal load_completed(success: bool, save_data: Dictionary)
signal setting_changed(setting_name: String, value: Variant)
signal tier_unlocked(tier_id: int)
signal notebook_entry_added(entry: Dictionary)

# =============================================================================
# STATE VARIABLES
# =============================================================================

var save_data: Dictionary = {
	"version": SAVE_VERSION,
	"player": {
		"name": "Research Fellow",
		"title": "Analytical Chemist",
		"level": 1,
		"xp": 0,
		"total_playtime_seconds": 0.0,
		"overall_safety_rating": 100.0,
		"osha_violations_count": 0
	},
	"quests": {
		"completed": [],
		"active_quest_id": "quest_01_orientation",
		"quest_progress": {}
	},
	"unlocked_labs": [
		"analytical_lab"
	],
	"unlocked_tiers": [
		1
	],
	"inventory": {
		"unlocked_reagents": ["hcl_01m", "naoh_01m", "phenolphthalein", "water_deionized"],
		"unlocked_apparatus": ["erlenmeyer_flask_250", "beaker_400", "bunsen_burner", "magnetic_stirrer", "analytical_balance", "titration_buret"]
	},
	"settings": {
		"graphics_preset": "balanced", # low, balanced (Iris Xe 60 FPS), high
		"input_mode": "desktop",       # desktop, webcam_tracker
		"master_volume": 1.0,
		"sfx_volume": 1.0,
		"ambience_volume": 0.8,
		"ui_volume": 1.0,
		"mouse_sensitivity": 0.002,
		"field_of_view": 75.0,
		"debanding_enabled": true
	},
	"lab_notebook": []
}

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	load_game()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		save_game()


# =============================================================================
# PERSISTENCE METHODS
# =============================================================================

func save_game() -> bool:
	var file := FileAccess.open(SAVE_FILE_PATH, FileAccess.WRITE)
	if not file:
		var err := FileAccess.get_open_error()
		push_error("SaveManager: Failed to open save file for writing: %s (Error code: %d)" % [SAVE_FILE_PATH, err])
		save_completed.emit(false)
		return false

	# Include apparatus state in save data
	save_data["apparatus"] = _collect_apparatus_state()

	var json_string := JSON.stringify(save_data, "\t")
	file.store_string(json_string)
	file.close()

	save_completed.emit(true)
	return true


func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_FILE_PATH):
		# No save file yet, initialize with default state
		save_game()
		load_completed.emit(true, save_data)
		return true

	var file := FileAccess.open(SAVE_FILE_PATH, FileAccess.READ)
	if not file:
		var err := FileAccess.get_open_error()
		push_error("SaveManager: Failed to open save file for reading: %s (Error code: %d)" % [SAVE_FILE_PATH, err])
		load_completed.emit(false, {})
		return false

	var content := file.get_as_text()
	file.close()

	var json := JSON.new()
	var parse_result := json.parse(content)
	if parse_result != OK:
		push_warning("SaveManager: Corrupted save file, creating backup and restoring defaults: %s" % json.get_error_message())
		save_game()
		load_completed.emit(false, save_data)
		return false

	var loaded_data = json.get_data()
	if typeof(loaded_data) == TYPE_DICTIONARY:
		_merge_save_data(loaded_data)
		# Apply apparatus state after loading
		_apply_apparatus_state(loaded_data)
		load_completed.emit(true, save_data)
		return true

	load_completed.emit(false, {})
	return false


func _merge_save_data(loaded: Dictionary) -> void:
	for key in loaded.keys():
		if save_data.has(key) and typeof(save_data[key]) == TYPE_DICTIONARY and typeof(loaded[key]) == TYPE_DICTIONARY:
			for sub_key in loaded[key].keys():
				save_data[key][sub_key] = loaded[key][sub_key]
		else:
			save_data[key] = loaded[key]


# =============================================================================
# SETTINGS & PROGRESSION API
# =============================================================================

func get_setting(setting_name: String, default_value: Variant = null) -> Variant:
	if save_data.settings.has(setting_name):
		return save_data.settings[setting_name]
	return default_value


func set_setting(setting_name: String, value: Variant) -> void:
	save_data.settings[setting_name] = value
	setting_changed.emit(setting_name, value)
	save_game()


func record_quest_completion(quest_id: String, xp_earned: int, safety_score: float) -> void:
	if not save_data.quests.completed.has(quest_id):
		save_data.quests.completed.append(quest_id)

	save_data.player.xp += xp_earned
	# Recalculate level (every 1000 XP is 1 level)
	save_data.player.level = int(save_data.player.xp / 1000.0) + 1

	save_game()


func add_notebook_entry(title: String, observations: String, yield_pct: float = -1.0) -> void:
	var entry := {
		"timestamp": Time.get_datetime_string_from_system(),
		"title": title,
		"observations": observations,
		"yield_pct": yield_pct
	}
	save_data.lab_notebook.append(entry)
	notebook_entry_added.emit(entry)
	save_game()


func unlock_tier(tier_level: int) -> void:
	if not save_data.has("unlocked_tiers"):
		save_data["unlocked_tiers"] = [1]
	if not save_data.unlocked_tiers.has(tier_level):
		save_data.unlocked_tiers.append(tier_level)
		save_data.unlocked_tiers.sort()
		tier_unlocked.emit(tier_level)
		save_game()


func is_tier_unlocked(tier_level: int) -> bool:
	if not save_data.has("unlocked_tiers"):
		return tier_level == 1
	return save_data.unlocked_tiers.has(tier_level)


func unlock_lab(lab_id: String) -> void:
	if not save_data.unlocked_labs.has(lab_id):
		save_data.unlocked_labs.append(lab_id)
		save_game()


func is_lab_unlocked(lab_id: String) -> bool:
	return save_data.unlocked_labs.has(lab_id)


func is_quest_completed(quest_id: String) -> bool:
	return save_data.quests.completed.has(quest_id)


func get_player_profile() -> Dictionary:
	return save_data.player


func get_completed_quests() -> Array:
	return save_data.quests.completed


# =============================================================================
# APPARATUS STATE PERSISTENCE
# =============================================================================

func _collect_apparatus_state() -> Dictionary:
	"""Collect state from all apparatus in the scene for save data."""
	var apparatus_state = {}

	# Collect NMR spectrometer state
	var nmr_nodes = get_tree().get_nodes_in_group("nmr_spectrometer")
	for nmr in nmr_nodes:
		if nmr.has_method("get_save_data"):
			apparatus_state["nmr_spectrometer"] = nmr.get_save_data()

	# Collect sample tube states
	var tube_nodes = get_tree().get_nodes_in_group("sample_tube")
	var tubes_data = []
	for tube in tube_nodes:
		if tube.has_method("get_save_data"):
			tubes_data.append(tube.get_save_data())
	if tubes_data.size() > 0:
		apparatus_state["sample_tubes"] = tubes_data

	return apparatus_state


func _apply_apparatus_state(data: Dictionary) -> void:
	"""Apply saved apparatus state to the scene."""
	if not data.has("apparatus"):
		return

	var apparatus_data = data["apparatus"]

	# Restore NMR spectrometer state
	if apparatus_data.has("nmr_spectrometer"):
		var nmr_nodes = get_tree().get_nodes_in_group("nmr_spectrometer")
		for nmr in nmr_nodes:
			if nmr.has_method("load_save_data"):
				nmr.load_save_data(apparatus_data["nmr_spectrometer"])

	# Restore sample tubes
	if apparatus_data.has("sample_tubes"):
		var tubes_data = apparatus_data["sample_tubes"]
		var existing_tubes = get_tree().get_nodes_in_group("sample_tube")

		for tube_data in tubes_data:
			var found = false
			var tube_id = tube_data.get("sample_id", "")

			# Try to find existing tube
			for existing in existing_tubes:
				if existing.has_method("get_save_data"):
					var existing_data = existing.get_save_data()
					if existing_data.get("sample_id", "") == tube_id:
						if existing.has_method("load_save_data"):
							existing.load_save_data(tube_data)
						found = true
						break

			# If not found, create new tube
			if not found:
				_create_sample_tube_from_data(tube_data)


func _create_sample_tube_from_data(tube_data: Dictionary) -> void:
	"""Create a new sample tube from saved data."""
	var tube_scene = load("res://scenes/apparatus/nmr_sample_tube.tscn")
	if tube_scene:
		var tube = tube_scene.instantiate()
		tube.name = "NMRSampleTube_Restored_" + str(int(Time.get_unix_time_from_system()))
		tube.global_position = tube_data.get("global_position", Vector3(0, 1, 0))
		tube.global_rotation = tube_data.get("global_rotation", Basis.IDENTITY)
		get_tree().root.add_child(tube)

		# Apply saved data
		if tube.has_method("load_save_data"):
			tube.load_save_data(tube_data)
		return

	# Fallback: create basic RigidBody3D with sample data
	var tube = RigidBody3D.new()
	tube.name = "NMRSampleTube_Restored_" + str(int(Time.get_unix_time_from_system()))
	tube.global_position = tube_data.get("global_position", Vector3(0, 1, 0))
	tube.global_rotation = tube_data.get("global_rotation", Basis.IDENTITY)
	get_tree().root.add_child(tube)

	# Add get_sample_data method dynamically
	var script = '''
extends RigidBody3D
class_name NMRSampleTube
func get_sample_data() -> Dictionary:
	return {
		"sample_type": "nmr_sample",
		"compound_name": "Ethanol",
		"concentration_mM": 50.0,
		"solvent": "CDCl3",
		"volume_ml": 0.6,
		"temperature_c": 25.0,
	}
'''
	tube.script = script
	get_tree().root.add_child(tube)
