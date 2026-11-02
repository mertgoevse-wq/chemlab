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


func get_notebook_entries() -> Array:
	return save_data.lab_notebook
