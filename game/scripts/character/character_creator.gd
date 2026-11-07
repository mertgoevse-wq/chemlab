# Athanor Ascension - Character Creation Manager
# Handles: 3 backgrounds, 5 specializations, appearance, prologue cinematics

extends Node

class_name CharacterCreator

signal character_created(character_data: Dictionary)
signal appearance_changed(category: String, value: Variant)
signal background_selected(background_id: String)
signal specialization_selected(spec_id: String)

const CHARACTER_DATA = preload("res://data/character/character_creation.json")

# Character creation state
var selected_background: String = ""
var selected_specialization: String = ""
var appearance: Dictionary = {}
var character_name: String = ""

func _ready() -> void:
	_reset_appearance()

func _reset_appearance() -> void:
	appearance = {
		"face": { "preset": 0, "scars": [], "tattoos": [] },
		"hair": { "style": 0, "color": "natural_brown", "facial_hair": "clean" },
		"eyes": { "color": "brown", "detail": "normal" },
		"body": { "type": "average", "skin_tone": 0, "markings": [] },
		"voice": { "preset": "calm_male", "pitch": 0, "speed": 0 }
	}

# =============================================================================
# BACKGROUND SELECTION
# =============================================================================

func get_available_backgrounds() -> Array[Dictionary]:
	var result = []
	for bg in CHARACTER_DATA.backgrounds:
		result.append({
			"id": bg.id,
			"name": bg.name,
			"description": bg.description,
			"starting_location": bg.starting_location,
			"mentor": bg.mentor,
			"starting_skills": bg.starting_skills,
			"starting_equipment": bg.starting_equipment,
			"starting_intelligence_points": bg.starting_intelligence_points,
			"unique_ability": bg.unique_ability,
			"story_hook": bg.story_hook,
			"prologue_video": bg.prologue_cinematic[bg.id].video
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
	for bg in CHARACTER_DATA.backgrounds:
		if bg.id == background_id:
			return true
	return false

func get_background_data(background_id: String) -> Dictionary:
	for bg in CHARACTER_DATA.backgrounds:
		if bg.id == background_id:
			return bg
	return {}

# =============================================================================
# SPECIALIZATION SELECTION
# =============================================================================

func get_available_specializations() -> Array[Dictionary]:
	var result = []
	for spec in CHARACTER_DATA.specializations:
		result.append({
			"id": spec.id,
			"name": spec.name,
			"description": spec.description,
			"primary_skills": spec.primary_skills,
			"bonus_skill_xp": spec.bonus_skill_xp,
			"unlocks_lab": spec.unlocks_lab,
			"companion_affinity": spec.companion_affinity
		})
	return result

func select_specialization(spec_id: String) -> bool:
	if not _is_valid_specialization(spec_id):
		return false

	selected_specialization = spec_id
	specialization_selected.emit(spec_id)
	return true

func _is_valid_specialization(spec_id: String) -> bool:
	for spec in CHARACTER_DATA.specializations:
		if spec.id == spec_id:
			return true
	return false

func get_specialization_data(spec_id: String) -> Dictionary:
	for spec in CHARACTER_DATA.specializations:
		if spec.id == spec_id:
			return spec
	return {}

# =============================================================================
# APPEARANCE CUSTOMIZATION
# =============================================================================

func get_appearance_options() -> Dictionary:
	return CHARACTER_DATA.appearance

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
	if name.length() < 2 or name.length() > 24:
		return false
	# Basic validation - no special chars except spaces, hyphens, apostrophes
	if not name.match("^[a-zA-Z0-9\\s\\-'\\u00C0-\\u017F]+$"):
		return false
	character_name = name
	return true

func create_character() -> Dictionary:
	if selected_background == "":
		return { "success": false, "error": "No background selected" }
	if selected_specialization == "":
		return { "success": false, "error": "No specialization selected" }
	if character_name == "":
		return { "success": false, "error": "No name entered" }

	var bg_data = get_background_data(selected_background)
	var spec_data = get_specialization_data(selected_specialization)

	var character_data = {
		"name": character_name,
		"background": selected_background,
		"specialization": selected_specialization,
		"appearance": appearance.duplicate(true),
		"starting_skills": bg_data.starting_skills.duplicate(true),
		"starting_equipment": bg_data.starting_equipment.duplicate(true),
		"starting_intelligence_points": bg_data.starting_intelligence_points,
		"unique_ability": bg_data.unique_ability,
		"specialization_bonus_xp": spec_data.bonus_skill_xp.duplicate(true),
		"unlocks_lab": spec_data.unlocks_lab,
		"companion_affinity": spec_data.companion_affinity.duplicate(true),
		"prologue_video": CHARACTER_DATA.prologue_cinematic[selected_background].video,
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
			for _ in range(level):
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

	# Set prologue video
	if save_manager:
		save_manager.set_prologue_video(character_data.prologue_video)

	# Save character
	if save_manager:
		save_manager.set_character_data(character_data)

func _get_equip_definition(equip_id: String) -> Dictionary:
	# Would load from equipment database
	return {}