# Athanor Ascension - Quest Manager (Extended)
# Autoload: QuestManager
# Handles: 10 Acts, 3 backgrounds, faction missions, dynamic events, investigation mode

extends Node

class_name QuestManager

signal quest_started(quest_id: String)
signal quest_completed(quest_id: String)
signal quest_failed(quest_id: String, reason: String)
signal objective_updated(quest_id: String, objective_id: String, progress: float)
signal investigation_mode_toggled(enabled: bool, modes: Array[String])

const CAMPAIGN_DATA = preload("res://data/quests/main_campaign.json")
const QUEST_SCHEMA = preload("res://data/quests/quest_schema.json")

# Quest state
var active_quest: String = ""
var completed_quests: Array[String] = []
var failed_quests: Array[String] = []
var quest_progress: Dictionary = {}  # quest_id -> {objectives: {}, state: {}}
var current_background: String = "academic"
var investigation_mode_active: bool = false
var investigation_vision_modes: Array[String] = []

func _ready() -> void:
	_load_save_data()

func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_quest_data"):
		var data = save_manager.get_quest_data()
		if data:
			active_quest = data.active_quest
			completed_quests = data.completed_quests
			failed_quests = data.failed_quests
			quest_progress = data.quest_progress
			current_background = data.current_background
			if active_quest != "":
				_start_quest(active_quest)

func set_background(background: String) -> void:
	if background in ["academic", "hobbyist", "ex_pharma"]:
		current_background = background

# =============================================================================
# QUEST LIFECYCLE
# =============================================================================

func start_quest(quest_id: String) -> bool:
	if _is_quest_available(quest_id):
		_start_quest(quest_id)
		return true
	return false

func _is_quest_available(quest_id: String) -> bool:
	if quest_id in completed_quests or quest_id in failed_quests:
		return false
	if active_quest != "" and active_quest != quest_id:
		return false

	var quest = _get_quest_definition(quest_id)
	if not quest:
		return false

	# Check prerequisites
	var prereqs = quest.prerequisites
	if prereqs.has("completed_quests"):
		for req in prereqs.completed_quests:
			if req not in completed_quests:
				return false

	if prereqs.has("min_safety_score"):
		var vitals = get_node_or_null("/root/PlayerVitals")
		if vitals and vitals.get_safety_score() < prereqs.min_safety_score:
			return false

	if prereqs.has("required_skills"):
		var skill_manager = get_node_or_null("/root/SkillManager")
		if skill_manager:
			for skill_id in prereqs.required_skills:
				if skill_manager.get_skill_level(skill_id) < prereqs.required_skills[skill_id]:
					return false

	if prereqs.has("background_requirements"):
		if not prereqs.background_requirements.get(current_background, false):
			return false

	if prereqs.has("faction_reputation"):
		var faction_sys = get_node_or_null("/root/FactionSystem")
		if faction_sys:
			for faction_id in prereqs.faction_reputation:
				if faction_sys.get_reputation(faction_id) < prereqs.faction_reputation[faction_id]:
					return false

	return true

func _start_quest(quest_id: String) -> void:
	active_quest = quest_id
	quest_progress[quest_id] = {
		"objectives": {},
		"state": "active",
		"started_at": Time.get_unix_time_from_system(),
		"dynamic_events_triggered": []
	}

	# Initialize objective progress
	var quest = _get_quest_definition(quest_id)
	for obj in quest.objectives:
		quest_progress[quest_id].objectives[obj.objective_id] = {
			"progress": 0.0,
			"completed": false,
			"hidden": obj.hidden,
			"optional": obj.optional
		}

	# Check for investigation mode
	if quest.has("investigation_mode") and quest.investigation_mode.enabled:
		_enable_investigation_mode(quest.investigation_mode)

	quest_started.emit(quest_id)
	_save_quests()

	# Show narrative briefing
	_show_quest_briefing(quest_id)

func _show_quest_briefing(quest_id: String) -> void:
	var quest = _get_quest_definition(quest_id)
	var briefing = quest.narrative_briefing

	# Get background-specific text
	var intro_text = briefing.intro_text
	if briefing.has("background_variants") and briefing.background_variants.has(current_background):
		intro_text = briefing.background_variants[current_background]

	# Emit to UI (would show in quest log)
	print("QUEST STARTED: %s" % quest.title)
	print(intro_text)

	# Play audio log if exists
	if briefing.audio_log_id:
		_play_audio_log(briefing.audio_log_id)

func complete_quest(quest_id: String) -> void:
	if quest_id != active_quest:
		return

	var quest = _get_quest_definition(quest_id)

	# Grant rewards
	_grant_quest_rewards(quest)

	# Mark completed
	completed_quests.append(quest_id)
	quest_progress[quest_id].state = "completed"
	active_quest = ""

	# Disable investigation mode if active
	if investigation_mode_active:
		_disable_investigation_mode()

	quest_completed.emit(quest_id)
	_save_quests()

	# Check for follow-up quests
	_check_quest_chain(quest_id)

func fail_quest(quest_id: String, reason: String) -> void:
	if quest_id != active_quest:
		return

	failed_quests.append(quest_id)
	quest_progress[quest_id].state = "failed"
	active_quest = ""

	if investigation_mode_active:
		_disable_investigation_mode()

	quest_failed.emit(quest_id, reason)
	_save_quests()

	# Show failure narrative
	_show_quest_failure(quest_id, reason)

func _show_quest_failure(quest_id: String, reason: String) -> void:
	var quest = _get_quest_definition(quest_id)
	var failure_text = "Quest failed: %s" % reason

	# Background-specific reprimand
	var failure_conditions = quest.failure_conditions
	for cond in failure_conditions:
		if cond.trigger_metric == reason or reason in cond.trigger_metric:
			if cond.background_variants.has(current_background):
				failure_text = cond.background_variants[current_background]
			else:
				failure_text = cond.narrative_reprimand
			break

	print("QUEST FAILED: %s" % failure_text)

# =============================================================================
# OBJECTIVE TRACKING
# =============================================================================

func update_objective(quest_id: String, objective_id: String, progress: float, completed: bool = false) -> void:
	if not quest_progress.has(quest_id) or not quest_progress[quest_id].objectives.has(objective_id):
		return

	var obj_progress = quest_progress[quest_id].objectives[objective_id]
	obj_progress.progress = clamp(progress, 0.0, 1.0)
	if completed or obj_progress.progress >= 1.0:
		obj_progress.completed = true
		obj_progress.progress = 1.0

	objective_updated.emit(quest_id, objective_id, obj_progress.progress)

	# Check if all main objectives complete
	_check_quest_completion(quest_id)

	_save_quests()

func _check_quest_completion(quest_id: String) -> void:
	var quest = _get_quest_definition(quest_id)
	var progress = quest_progress[quest_id]

	var all_main_complete = true
	for obj in quest.objectives:
		if not obj.optional:
			if not progress.objectives.has(obj.objective_id) or not progress.objectives[obj.objective_id].completed:
				all_main_complete = false
				break

	if all_main_complete:
		complete_quest(quest_id)

# =============================================================================
# DYNAMIC EVENTS
# =============================================================================

func _process(delta: float) -> void:
	if active_quest == "":
		return

	var quest = _get_quest_definition(active_quest)
	if not quest.has("dynamic_events"):
		return

	var progress = quest_progress[active_quest]

	for event in quest.dynamic_events:
		if event.event_id in progress.dynamic_events_triggered:
			continue

		# Check trigger condition
		if _check_event_trigger(event, progress):
			if randf() < event.trigger_chance:
				_trigger_dynamic_event(active_quest, event)
				progress.dynamic_events_triggered.append(event.event_id)

func _check_event_trigger(event: Dictionary, progress: Dictionary) -> bool:
	if not event.has("trigger_condition") or event.trigger_condition == "":
		return true

	# Parse condition (simplified)
	# Could be: "temperature_c > 80", "has_item:antidote", etc.
	return true

func _trigger_dynamic_event(quest_id: String, event: Dictionary) -> void:
	print("DYNAMIC EVENT: %s - %s" % [event.event_id, event.description])

	# Apply consequences
	if event.has("consequences"):
		for key in event.consequences:
			var value = event.consequences[key]
			_apply_event_consequence(key, value)

	# Could spawn enemies, modify objectives, etc.

func _apply_event_consequence(key: String, value: Variant) -> void:
	match key:
		"spawn_enemies":
			# Would spawn combat encounter
			pass
		"modify_objective":
			# Modify objective target
			pass
		"damage_player":
			var vitals = get_node_or_null("/root/PlayerVitals")
			if vitals:
				vitals.apply_damage(value, "dynamic_event")
		"change_faction_rep":
			var faction_sys = get_node_or_null("/root/FactionSystem")
			if faction_sys:
				for faction in value:
					faction_sys.modify_reputation(faction, value[faction])

# =============================================================================
# INVESTIGATION MODE (Assassin's Creed Eagle Vision)
# =============================================================================

func _enable_investigation_mode(investigation_data: Dictionary) -> void:
	investigation_mode_active = true
	investigation_vision_modes = investigation_data.vision_modes

	investigation_mode_toggled.emit(true, investigation_vision_modes)

	# Show clues in world
	if investigation_data.has("clues"):
		for clue in investigation_data.clues:
			_show_investigation_clue(clue)

func _disable_investigation_mode() -> void:
	investigation_mode_active = false
	investigation_vision_modes = []
	investigation_mode_toggled.emit(false, [])

	# Hide clues
	_hide_investigation_clues()

func _show_investigation_clue(clue: Dictionary) -> void:
	# Would create visual marker in world visible only in investigation mode
	print("CLUE REVEALED (%s): %s" % [clue.vision_mode_required, clue.reveals])

func _hide_investigation_clues() -> void:
	# Hide all investigation markers
	pass

func get_investigation_mode() -> bool:
	return investigation_mode_active

func get_investigation_vision_modes() -> Array[String]:
	return investigation_vision_modes.duplicate()

# =============================================================================
# FACTION MISSIONS
# =============================================================================

func start_faction_mission(faction_id: String, mission_id: String) -> bool:
	var faction_sys = get_node_or_null("/root/FactionSystem")
	if not faction_sys:
		return false

	# Check if mission exists and is available
	var mission = _get_faction_mission(faction_id, mission_id)
	if not mission:
		return false

	# Start as regular quest
	return start_quest(mission.quest_id)

func _get_faction_mission(faction_id: String, mission_id: String) -> Dictionary:
	# Would load from faction missions database
	return {}

# =============================================================================
# QUEST CHAINS & CONVERGENCE
# =============================================================================

func _check_quest_chain(completed_quest_id: String) -> void:
	# Check if completing this quest unlocks others
	var campaign = CAMPAIGN_DATA

	for act in campaign.acts:
		for quest in act.main_quests:
			if quest.quest_id == completed_quest_id:
				# Check for convergence points
				if act.has("convergence"):
					_trigger_convergence(act.convergence)
				break

		# Check faction missions
		if act.has("faction_missions"):
			for fm in act.faction_missions:
				if _is_quest_available(fm.quest_id):
					# Notify player of new faction mission
					print("New faction mission available: %s" % fm.title)

func _trigger_convergence(convergence_text: String) -> void:
	print("CONVERGENCE: %s" % convergence_text)
	# All three backgrounds meet here - narrative moment

# =============================================================================
# BACKGROUND-SPECIFIC NARRATIVE
# =============================================================================

func get_narrative_text(quest_id: String, text_key: String) -> String:
	var quest = _get_quest_definition(quest_id)
	if not quest:
		return ""

	var text_obj = quest.narrative_briefing
	if text_obj.has(text_key):
		var text = text_obj[text_key]
		if text_obj.has("background_variants") and text_obj.background_variants.has(current_background):
			return text_obj.background_variants[current_background]
		return text

	return ""

func get_failure_text(quest_id: String, condition_id: String) -> String:
	var quest = _get_quest_definition(quest_id)
	if not quest or not quest.has("failure_conditions"):
		return "Quest failed."

	for cond in quest.failure_conditions:
		if cond.condition_id == condition_id:
			if cond.background_variants.has(current_background):
				return cond.background_variants[current_background]
			return cond.narrative_reprimand

	return "Quest failed."

# =============================================================================
# HELPERS
# =============================================================================

func _get_quest_definition(quest_id: String) -> Dictionary:
	# Search in campaign data
	var campaign = CAMPAIGN_DATA

	for act in campaign.acts:
		for quest in act.main_quests:
			if quest.quest_id == quest_id:
				return quest

	# Check faction missions
	for act in campaign.acts:
		if act.has("faction_missions"):
			for fm in act.faction_missions:
				if fm.quest_id == quest_id:
					return fm

	return {}

func _grant_quest_rewards(quest: Dictionary) -> void:
	var rewards = quest.rewards

	if rewards.has("skill_xp"):
		var skill_manager = get_node_or_null("/root/SkillManager")
		if skill_manager:
			for skill_id in rewards.skill_xp:
				skill_manager.grant_skill_xp(skill_id, rewards.skill_xp[skill_id], "quest_reward")

	if rewards.has("intelligence_points"):
		var skill_manager = get_node_or_null("/root/SkillManager")
		if skill_manager:
			skill_manager.grant_intelligence_points(rewards.intelligence_points, "quest_reward")

	if rewards.has("faction_reputation"):
		var faction_sys = get_node_or_null("/root/FactionSystem")
		if faction_sys:
			for faction in rewards.faction_reputation:
				faction_sys.modify_reputation(faction, rewards.faction_reputation[faction])

	if rewards.has("items"):
		var inv_manager = get_node_or_null("/root/InventoryManager")
		if inv_manager:
			for item in rewards.items:
				inv_manager.add_item(item.item_id, item.quantity)

	if rewards.has("equipment"):
		var inv_manager = get_node_or_null("/root/InventoryManager")
		if inv_manager:
			for equip_id in rewards.equipment:
				# Would equip automatically or add to inventory
				inv_manager.add_item(equip_id, 1)

	if rewards.has("companion_unlock"):
		var comp_manager = get_node_or_null("/root/CompanionManager")
		if comp_manager:
			comp_manager.add_companion(rewards.companion_unlock)

	if rewards.has("lab_access"):
		var save_manager = get_node_or_null("/root/SaveManager")
		if save_manager:
			for lab in rewards.lab_access:
				save_manager.unlock_content("lab", lab)

	if rewards.has("background_specific"):
		var bg_rewards = rewards.background_specific[current_background]
		# Apply background-specific rewards
		pass

func _play_audio_log(audio_log_id: String) -> void:
	# Would play audio log
	print("Playing audio log: %s" % audio_log_id)

func _save_quests() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("set_quest_data"):
		save_manager.set_quest_data({
			"active_quest": active_quest,
			"completed_quests": completed_quests,
			"failed_quests": failed_quests,
			"quest_progress": quest_progress,
			"current_background": current_background
		})

func get_active_quest() -> String:
	return active_quest

func get_quest_progress(quest_id: String) -> Dictionary:
	return quest_progress.get(quest_id, {})

func is_quest_completed(quest_id: String) -> bool:
	return quest_id in completed_quests

func is_quest_failed(quest_id: String) -> bool:
	return quest_id in failed_quests

func get_available_quests() -> Array[String]:
	var available = []
	var campaign = CAMPAIGN_DATA

	for act in campaign.acts:
		for quest in act.main_quests:
			if _is_quest_available(quest.quest_id):
				available.append(quest.quest_id)

	return available

func to_dict() -> Dictionary:
	return {
		"active_quest": active_quest,
		"completed_quests": completed_quests,
		"failed_quests": failed_quests,
		"quest_progress": quest_progress,
		"current_background": current_background
	}

func from_dict(data: Dictionary) -> void:
	active_quest = data.get("active_quest", "")
	completed_quests = data.get("completed_quests", [])
	failed_quests = data.get("failed_quests", [])
	quest_progress = data.get("quest_progress", {})
	current_background = data.get("current_background", "academic")

	if active_quest != "":
		_start_quest(active_quest)