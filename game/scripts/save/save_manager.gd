# Athanor Ascension - Save Manager
# Autoload: SaveManager
# Handles: Game saves, character data, settings, cloud sync stubs

extends Node

class_name SaveManager

signal save_completed(success: bool)
signal load_completed(success: bool)
signal data_changed(key: String, value: Variant)

const SAVE_SLOTS: int = 10
const CURRENT_VERSION: int = 1

# Save data storage
var save_data: Dictionary = {}
var current_slot: int = 1
var auto_save_enabled: bool = true
var auto_save_interval: float = 300.0  # 5 minutes
var _auto_save_timer: Timer

func _ready() -> void:
	_initialize_save_data()
	_load_settings()
	_start_auto_save()

func _initialize_save_data() -> void:
	save_data = {
		"version": CURRENT_VERSION,
		"slots": {},
		"current_slot": 1,
		"playtime": 0.0,
		"last_save": 0,
		"settings": {
			"graphics": {},
			"audio": {},
			"input": {},
			"gameplay": {}
		},
		"statistics": {
			"total_syntheses": 0,
			"perfect_syntheses": 0,
			"total_deaths": 0,
			"total_playtime": 0.0,
			"labs_unlocked": [],
			"companions_bonded": [],
			"achievements_unlocked": []
		}
	}

func _load_settings() -> void:
	var config = ConfigFile.new()
	if config.load("user://settings.cfg") == OK:
		auto_save_enabled = config.get_value("save", "auto_save", true)
		auto_save_interval = config.get_value("save", "auto_save_interval", 300.0)
		current_slot = config.get_value("save", "current_slot", 1)

func _save_settings() -> void:
	var config = ConfigFile.new()
	config.set_value("save", "auto_save", auto_save_enabled)
	config.set_value("save", "auto_save_interval", auto_save_interval)
	config.set_value("save", "current_slot", current_slot)
	config.save("user://settings.cfg")

func _start_auto_save() -> void:
	if not auto_save_enabled:
		return

	_auto_save_timer = Timer.new()
	_auto_save_timer.wait_time = auto_save_interval
	_auto_save_timer.autostart = true
	_auto_save_timer.timeout.connect(_auto_save)
	add_child(_auto_save_timer)

func _auto_save() -> void:
	if auto_save_enabled:
		save_game(current_slot)

# =============================================================================
# PUBLIC API - SAVE/LOAD
# =============================================================================

func save_game(slot: int = -1) -> bool:
	if slot == -1:
		slot = current_slot

	if slot < 1 or slot > SAVE_SLOTS:
		return false

	var slot_data = _collect_save_data()
	slot_data["slot"] = slot
	slot_data["timestamp"] = Time.get_unix_time_from_system()
	slot_data["playtime"] = save_data.playtime

	save_data.slots[str(slot)] = slot_data
	save_data.current_slot = slot
	save_data.last_save = Time.get_unix_time_from_system()

	var success = _write_save_file()
	save_completed.emit(success)
	return success

func load_game(slot: int) -> bool:
	if slot < 1 or slot > SAVE_SLOTS:
		return false

	var success = _read_save_file()
	if not success:
		return false

	if not save_data.slots.has(str(slot)):
		return false

	var slot_data = save_data.slots[str(slot)]
	if slot_data.get("version", 0) != CURRENT_VERSION:
		print("Warning: Save version mismatch")
		# Could run migration here

	_apply_save_data(slot_data)
	current_slot = slot
	load_completed.emit(true)
	return true

func quick_save() -> bool:
	return save_game(current_slot)

func quick_load() -> bool:
	return load_game(current_slot)

func delete_save(slot: int) -> bool:
	if slot < 1 or slot > SAVE_SLOTS:
		return false

	if save_data.slots.has(str(slot)):
		save_data.slots.erase(str(slot))
		return _write_save_file()
	return false

func get_save_info(slot: int) -> Dictionary:
	if slot < 1 or slot > SAVE_SLOTS:
		return {}

	if not save_data.slots.has(str(slot)):
		return { "empty": true, "slot": slot }

	var slot_data = save_data.slots[str(slot)]
	return {
		"slot": slot,
		"timestamp": slot_data.get("timestamp", 0),
		"playtime": slot_data.get("playtime", 0.0),
		"character_name": slot_data.get("character", {}).get("name", "Unknown"),
		"background": slot_data.get("character", {}).get("background", ""),
		"specialization": slot_data.get("character", {}).get("specialization", ""),
		"location": slot_data.get("location", "Unknown"),
		"playtime_formatted": _format_playtime(slot_data.get("playtime", 0.0))
	}

func get_all_saves() -> Array[Dictionary]:
	var result = []
	for i in range(1, SAVE_SLOTS + 1):
		result.append(get_save_info(i))
	return result

func _format_playtime(seconds: float) -> String:
	var hours = int(seconds / 3600)
	var minutes = int((seconds % 3600) / 60)
	return "%02d:%02d" % [hours, minutes]

# =============================================================================
# DATA COLLECTION / APPLICATION
# =============================================================================

func _collect_save_data() -> Dictionary:
	var skill_manager = get_node_or_null("/root/SkillManager")
	var inv_manager = get_node_or_null("/root/InventoryManager")
	var vitals = get_node_or_null("/root/PlayerVitals")
	var quest_manager = get_node_or_null("/root/QuestManager")
	var comp_manager = get_node_or_null("/root/CompanionManager")
	var faction_sys = get_node_or_null("/root/FactionSystem")
	var char_creator = get_node_or_null("/root/CharacterCreator")

	return {
		"version": CURRENT_VERSION,
		"character": char_creator.to_dict() if char_creator else {},
		"skills": skill_manager.to_dict() if skill_manager else {},
		"inventory": inv_manager.to_dict() if inv_manager else {},
		"vitals": vitals.to_dict() if vitals else {},
		"quests": quest_manager.to_dict() if quest_manager else {},
		"companions": comp_manager.to_dict() if comp_manager else {},
		"factions": faction_sys.to_dict() if faction_sys else {},
		"location": _get_current_location(),
		"playtime": save_data.playtime + (Time.get_unix_time_from_system() - _get_session_start())
	}

func _apply_save_data(slot_data: Dictionary) -> void:
	var skill_manager = get_node_or_null("/root/SkillManager")
	var inv_manager = get_node_or_null("/root/InventoryManager")
	var vitals = get_node_or_null("/root/PlayerVitals")
	var quest_manager = get_node_or_null("/root/QuestManager")
	var comp_manager = get_node_or_null("/root/CompanionManager")
	var faction_sys = get_node_or_null("/root/FactionSystem")
	var char_creator = get_node_or_null("/root/CharacterCreator")

	if char_creator and slot_data.has("character"):
		char_creator.apply_character_to_game(slot_data.character)

	if skill_manager and slot_data.has("skills"):
		skill_manager.from_dict(slot_data.skills)

	if inv_manager and slot_data.has("inventory"):
		inv_manager.from_dict(slot_data.inventory)

	if vitals and slot_data.has("vitals"):
		vitals.from_dict(slot_data.vitals)

	if quest_manager and slot_data.has("quests"):
		quest_manager.from_dict(slot_data.quests)

	if comp_manager and slot_data.has("companions"):
		comp_manager.from_dict(slot_data.companions)

	if faction_sys and slot_data.has("factions"):
		faction_sys.from_dict(slot_data.factions)

	# Restore location would be handled by scene system

	print("Save data applied from slot %d" % current_slot)

func _get_current_location() -> String:
	# Would get current scene/location
	return "Unknown"

func _get_session_start() -> int:
	return Time.get_unix_time_from_system()  # Simplified

# =============================================================================
# FILE I/O
# =============================================================================

func _write_save_file() -> bool:
	var file = FileAccess.open("user://save_%d.dat" % current_slot, FileAccess.WRITE)
	if file == null:
		return false

	var json_str = JSON.stringify(save_data, "\t")
	file.store_string(json_str)
	file.close()
	return true

func _read_save_file() -> bool:
	var file = FileAccess.open("user://save_%d.dat" % current_slot, FileAccess.READ)
	if file == null:
		return false

	var json_str = file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(json_str)
	if parsed == null:
		return false

	save_data = parsed
	return true

# =============================================================================
# SETTINGS MANAGEMENT
# =============================================================================

func set_setting(category: String, key: String, value: Variant) -> void:
	if not save_data.settings.has(category):
		save_data.settings[category] = {}
	save_data.settings[category][key] = value
	data_changed.emit("%s/%s" % [category, key], value)

func get_setting(category: String, key: String, default: Variant = null) -> Variant:
	if save_data.settings.has(category) and save_data.settings[category].has(key):
		return save_data.settings[category][key]
	return default

func set_auto_save(enabled: bool) -> void:
	auto_save_enabled = enabled
	_save_settings()
	if enabled:
		_start_auto_save()
	else:
		if _auto_save_timer:
			_auto_save_timer.stop()

func set_auto_save_interval(seconds: float) -> void:
	auto_save_interval = max(60.0, seconds)
	_save_settings()
	if _auto_save_timer:
		_auto_save_timer.wait_time = auto_save_interval

# =============================================================================
# STATISTICS
# =============================================================================

func increment_stat(stat: String, amount: int = 1) -> void:
	if save_data.statistics.has(stat):
		save_data.statistics[stat] += amount
	else:
		save_data.statistics[stat] = amount

func unlock_lab(lab_id: String) -> void:
	if lab_id not in save_data.statistics.labs_unlocked:
		save_data.statistics.labs_unlocked.append(lab_id)
		data_changed.emit("labs_unlocked", save_data.statistics.labs_unlocked)

func unlock_companion(companion_id: String) -> void:
	if companion_id not in save_data.statistics.companions_bonded:
		save_data.statistics.companions_bonded.append(companion_id)
		data_changed.emit("companions_bonded", save_data.statistics.companions_bonded)

func unlock_achievement(achievement_id: String) -> void:
	if achievement_id not in save_data.statistics.achievements_unlocked:
		save_data.statistics.achievements_unlocked.append(achievement_id)
		data_changed.emit("achievements_unlocked", save_data.statistics.achievements_unlocked)

func add_playtime(seconds: float) -> void:
	save_data.statistics.total_playtime += seconds
	save_data.playtime += seconds

# =============================================================================
# EXPORT/IMPORT
# =============================================================================

func export_save(slot: int, path: String) -> bool:
	if not save_data.slots.has(str(slot)):
		return false

	var file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false

	var json_str = JSON.stringify(save_data.slots[str(slot)], "\t")
	file.store_string(json_str)
	file.close()
	return true

func import_save(slot: int, path: String) -> bool:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false

	var json_str = file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(json_str)
	if parsed == null:
		return false

	save_data.slots[str(slot)] = parsed
	return _write_save_file()

# =============================================================================
# CLOUD SYNC STUBS
# =============================================================================

func sync_to_cloud() -> void:
	# Steam Cloud API integration stub
	print("Cloud sync not yet implemented")

func sync_from_cloud() -> void:
	print("Cloud sync not yet implemented")

# =============================================================================
# PROLOGUE VIDEO
# =============================================================================

func set_prologue_video(video_path: String) -> void:
	set_setting("gameplay", "prologue_video", video_path)

func get_prologue_video() -> String:
	return get_setting("gameplay", "prologue_video", "")

# =============================================================================
# CHARACTER DATA
# =============================================================================

func set_character_data(data: Dictionary) -> void:
	save_data.character = data
	data_changed.emit("character", data)

func get_character_data() -> Dictionary:
	return save_data.get("character", {})

# =============================================================================
# HELPERS
# =============================================================================

func to_dict() -> Dictionary:
	return save_data

func from_dict(data: Dictionary) -> void:
	save_data = data