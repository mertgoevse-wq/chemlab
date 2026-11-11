# Athanor Ascension - Character Creation Manager
# Handles: 3 backgrounds, 5 specializations, appearance, prologue cinematics

extends Node

signal character_created(character_data: Dictionary)
signal appearance_changed(category: String, value: Variant)
signal background_selected(background_id: String)
signal specialization_selected(spec_id: String)

const CHARACTER_DATA = preload("res://data/character/character_creation.json")

var _cached_data: Dictionary = {}

func _get_data() -> Dictionary:
	if not _cached_data.is_empty():
		return _cached_data
	if CHARACTER_DATA and CHARACTER_DATA.data is Dictionary:
		_cached_data = CHARACTER_DATA.data
	return _cached_data

# Character creation state
var selected_background: String = "academic"
var selected_specialization: String = "organic_synthesis"
var appearance: Dictionary = {}
var character_name: String = ""
var pronouns: String = "they/them"
var lab_coat_style: String = "academic_white"

static func get_default_name_for_background(bg_id: String) -> String:
	match bg_id:
		"academic":
			return "Dr. Aris Thorne"
		"hobbyist":
			return "Vesper Finch"
		"ex_pharma":
			return "Kaelen Voss"
		_:
			return "Dr. Aris Thorne"

func _ready() -> void:
	_reset_appearance()

func _reset_appearance() -> void:
	appearance = {
		"face": { "preset": 0, "scars": [], "tattoos": [] },
		"hair": { "style": 0, "color": "natural_brown", "facial_hair": "clean" },
		"eyes": { "color": "brown", "detail": "normal" },
		"body": { "type": "average", "skin_tone": 0, "markings": [] },
		"voice": { "preset": "calm_neutral", "pitch": 0, "speed": 0 },
		"attire": { "coat_style": "academic_white", "goggles": "standard_ansi", "gloves": "nitrile_cyan" }
	}

# =============================================================================
# BACKGROUND SELECTION
# =============================================================================

func get_available_backgrounds() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var data = _get_data()
	var backgrounds = data.get("backgrounds", [])
	var cinematics = data.get("prologue_cinematic", {})
	for bg in backgrounds:
		var bg_id = bg.get("id", "")
		var video = ""
		if cinematics.has(bg_id) and cinematics[bg_id] is Dictionary:
			video = cinematics[bg_id].get("video", "")
		result.append({
			"id": bg_id,
			"name": bg.get("name", ""),
			"description": bg.get("description", ""),
			"starting_location": bg.get("starting_location", ""),
			"mentor": bg.get("mentor", ""),
			"starting_skills": bg.get("starting_skills", {}),
			"starting_equipment": bg.get("starting_equipment", []),
			"starting_intelligence_points": bg.get("starting_intelligence_points", 0),
			"unique_ability": bg.get("unique_ability", ""),
			"story_hook": bg.get("story_hook", ""),
			"prologue_video": video
		})
	return result

func select_background(background_id: String) -> bool:
	if not _is_valid_background(background_id):
		return false

	selected_background = background_id
	background_selected.emit(background_id)
	appearance_changed.emit("background", background_id)
	return true

func _is_valid_background(background_id: String) -> bool:
	var backgrounds = _get_data().get("backgrounds", [])
	for bg in backgrounds:
		if bg.get("id", "") == background_id:
			return true
	return false

func get_background_data(background_id: String) -> Dictionary:
	var backgrounds = _get_data().get("backgrounds", [])
	for bg in backgrounds:
		if bg.get("id", "") == background_id:
			return bg
	return {}

# =============================================================================
# SPECIALIZATION SELECTION
# =============================================================================

func get_available_specializations() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var specs = _get_data().get("specializations", [])
	for spec in specs:
		result.append({
			"id": spec.get("id", ""),
			"name": spec.get("name", ""),
			"description": spec.get("description", ""),
			"primary_skills": spec.get("primary_skills", []),
			"bonus_skill_xp": spec.get("bonus_skill_xp", {}),
			"unlocks_lab": spec.get("unlocks_lab", ""),
			"companion_affinity": spec.get("companion_affinity", {})
		})
	return result

func select_specialization(spec_id: String) -> bool:
	if not _is_valid_specialization(spec_id):
		return false

	selected_specialization = spec_id
	specialization_selected.emit(spec_id)
	return true

func _is_valid_specialization(spec_id: String) -> bool:
	var specs = _get_data().get("specializations", [])
	for spec in specs:
		if spec.get("id", "") == spec_id:
			return true
	return false

func get_specialization_data(spec_id: String) -> Dictionary:
	var specs = _get_data().get("specializations", [])
	for spec in specs:
		if spec.get("id", "") == spec_id:
			return spec
	return {}

# =============================================================================
# APPEARANCE CUSTOMIZATION
# =============================================================================

func get_appearance_options() -> Dictionary:
	return _get_data().get("appearance", {})

func set_appearance_option(category: String, option: String, value: Variant) -> bool:
	if not appearance.has(category):
		return false

	appearance[category][option] = value
	appearance_changed.emit(category, { option: value })
	return true

func set_appearance_category(category: String, data: Dictionary) -> bool:
	if not appearance.has(category):
		return false

	appearance[category] = data
	appearance_changed.emit(category, data)
	return true

func get_current_appearance() -> Dictionary:
	return appearance.duplicate(true)

# =============================================================================
# CHARACTER FINALIZATION
# =============================================================================

func set_character_name(name: String) -> bool:
	var trimmed = name.strip_edges()
	if trimmed.is_empty():
		character_name = ""
		return true
	if trimmed.length() < 2 or trimmed.length() > 24:
		return false
	var regex = RegEx.new()
	regex.compile("^[a-zA-Z0-9\\s\\-'.]+$")
	if not regex.search(trimmed):
		return false
	character_name = trimmed
	return true

func set_pronouns(p: String) -> void:
	pronouns = p

func set_lab_coat_style(style: String) -> void:
	lab_coat_style = style
	if appearance.has("attire"):
		appearance["attire"]["coat_style"] = style

func create_character() -> Dictionary:
	if selected_background == "":
		selected_background = "academic"
	if selected_specialization == "":
		selected_specialization = "organic_synthesis"
	var final_name = character_name.strip_edges()
	if final_name == "":
		final_name = get_default_name_for_background(selected_background)

	var bg_data = get_background_data(selected_background)
	var spec_data = get_specialization_data(selected_specialization)
	var cinematics = _get_data().get("prologue_cinematic", {})
	var prologue_vid = ""
	if cinematics.has(selected_background) and cinematics[selected_background] is Dictionary:
		prologue_vid = cinematics[selected_background].get("video", "")

	var character_data = {
		"name": final_name,
		"pronouns": pronouns,
		"lab_coat_style": lab_coat_style,
		"background": selected_background,
		"specialization": selected_specialization,
		"appearance": appearance.duplicate(true),
		"starting_skills": bg_data.get("starting_skills", {}).duplicate(true),
		"starting_equipment": bg_data.get("starting_equipment", []).duplicate(true),
		"starting_intelligence_points": bg_data.get("starting_intelligence_points", 0),
		"unique_ability": bg_data.get("unique_ability", ""),
		"specialization_bonus_xp": spec_data.get("bonus_skill_xp", {}).duplicate(true),
		"unlocks_lab": spec_data.get("unlocks_lab", ""),
		"companion_affinity": spec_data.get("companion_affinity", {}).duplicate(true),
		"prologue_video": prologue_vid,
		"open_progression": true, # Open-ended: all 20 skill tracks can be leveled to 120
		"created_at": Time.get_unix_time_from_system()
	}

	character_created.emit(character_data)
	return { "success": true, "character": character_data }

func apply_character_to_game(character_data: Dictionary) -> void:
	var skill_manager = get_node_or_null("/root/SkillManager")
	var inv_manager = get_node_or_null("/root/InventoryManager")
	var vitals = get_node_or_null("/root/PlayerVitals")
	var quest_manager = get_node_or_null("/root/QuestManager")
	var save_manager = get_node_or_null("/root/SaveManager")

	# Apply starting skills
	if skill_manager and character_data.has("starting_skills"):
		for skill_id in character_data.starting_skills:
			var level = character_data.starting_skills[skill_id]
			for _lvl in range(level):
				skill_manager.grant_skill_xp(skill_id, 100, "character_creation")

	# Apply specialization bonus XP
	if skill_manager and character_data.has("specialization_bonus_xp"):
		for skill_id in character_data.specialization_bonus_xp:
			var mult = character_data.specialization_bonus_xp[skill_id]
			skill_manager.set_xp_multiplier(skill_id, mult)

	# Grant starting equipment
	if inv_manager and character_data.has("starting_equipment"):
		for equip_id in character_data.starting_equipment:
			inv_manager.add_item(equip_id, 1)
			# Auto-equip if appropriate slot
			var equip_def = _get_equip_definition(equip_id)
			if equip_def and equip_def.has("slot"):
				inv_manager.equip_item(equip_def.slot, equip_id)

	# Grant Intelligence Points
	if skill_manager and character_data.has("starting_intelligence_points"):
		skill_manager.grant_intelligence_points(character_data.starting_intelligence_points, "character_creation")

	# Set background for quest manager
	if quest_manager:
		quest_manager.set_background(character_data.background)
		if quest_manager.has_method("set_player_name"):
			quest_manager.set_player_name(character_data.name)

	# Set prologue video
	if save_manager:
		save_manager.set_prologue_video(character_data.prologue_video)

	# Save character
	if save_manager:
		save_manager.set_character_data(character_data)

func to_dict() -> Dictionary:
	return {
		"name": character_name,
		"pronouns": pronouns,
		"lab_coat_style": lab_coat_style,
		"background": selected_background,
		"specialization": selected_specialization,
		"appearance": appearance.duplicate(true)
	}

func from_dict(data: Dictionary) -> void:
	character_name = data.get("name", "")
	pronouns = data.get("pronouns", "they/them")
	lab_coat_style = data.get("lab_coat_style", "academic_white")
	selected_background = data.get("background", "academic")
	selected_specialization = data.get("specialization", "organic_synthesis")
	appearance = data.get("appearance", appearance)

func _get_equip_definition(equip_id: String) -> Dictionary:
	# Would load from equipment database
	return {}