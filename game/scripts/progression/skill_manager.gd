# Athanor Ascension - Skill System (RuneScape Style)
# Autoload: SkillManager
# Handles: XP curves, level ups, Intelligence Points, Talent Trees, Milestones

extends Node

class_name SkillManager

signal skill_xp_gained(skill_id: String, amount: int, new_total: int)
signal skill_leveled_up(skill_id: String, new_level: int)
signal intelligence_points_changed(amount: int, new_total: int)
signal talent_unlocked(talent_id: String)
signal milestone_reached(skill_id: String, milestone_level: int)

# Load skill data from JSON
const SKILL_DATA = preload("res://data/progression/skills.json")

# XP curve from RuneScape formula (precomputed for 120 levels)
var xp_table: Array[int] = []

# Current skill state
var skills: Dictionary = {} # skill_id -> {level, xp, virtual_level}
var intelligence_points: int = 0
var unlocked_talents: Array[String] = []
var reached_milestones: Dictionary = {} # skill_id -> Array[milestone_level]

func _ready() -> void:
	_load_xp_table()
	_initialize_skills()
	_load_save_data()

func _load_xp_table() -> void:
	xp_table = SKILL_DATA.xp_formula.base_xp_per_level.duplicate()
	# Extend to 120 if needed (formula continues)
	while xp_table.size() < 121:
		var level = xp_table.size()
		var xp = 0
		for i in range(1, level + 1):
			xp += int(i + 300 * pow(2.0, i / 7.0))
		xp_table.append(int(xp / 4))

func _initialize_skills() -> void:
	for skill_def in SKILL_DATA.skills:
		var id = skill_def.id
		skills[id] = {
			"level": 1,
			"xp": 0,
			"virtual_level": 1,
			"definition": skill_def
		}

func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_skill_data"):
		var data = save_manager.get_skill_data()
		if data:
			skills = data.skills
			intelligence_points = data.intelligence_points
			unlocked_talents = data.unlocked_talents
			reached_milestones = data.reached_milestones
			_emit_all_signals()

func _emit_all_signals() -> void:
	for skill_id in skills:
		var skill = skills[skill_id]
		skill_xp_gained.emit(skill_id, 0, skill.xp)
		skill_leveled_up.emit(skill_id, skill.level)
		for milestone in reached_milestones.get(skill_id, []):
			milestone_reached.emit(skill_id, milestone)
	intelligence_points_changed.emit(0, intelligence_points)

# =============================================================================
# PUBLIC API
# =============================================================================

func get_skill_level(skill_id: String) -> int:
	if skills.has(skill_id):
		return skills[skill_id].level
	return 0

func get_skill_xp(skill_id: String) -> int:
	if skills.has(skill_id):
		return skills[skill_id].xp
	return 0

func get_skill_progress(skill_id: String) -> float:
	if not skills.has(skill_id):
		return 0.0
	var skill = skills[skill_id]
	var current_level_xp = xp_table[skill.level - 1]
	var next_level_xp = xp_table[skill.level] if skill.level < 120 else current_level_xp
	if next_level_xp <= current_level_xp:
		return 1.0
	return float(skill.xp - current_level_xp) / float(next_level_xp - current_level_xp)

func get_skill_virtual_level(skill_id: String) -> int:
	if skills.has(skill_id):
		return skills[skill_id].virtual_level
	return 0

func get_intelligence_points() -> int:
	return intelligence_points

func has_talent(talent_id: String) -> bool:
	return talent_id in unlocked_talents

func has_milestone(skill_id: String, milestone_level: int) -> bool:
	return milestone_level in reached_milestones.get(skill_id, [])

func get_skill_definition(skill_id: String) -> Dictionary:
	if skills.has(skill_id):
		return skills[skill_id].definition
	return {}

func get_all_skills() -> Array[Dictionary]:
	var result = []
	for skill_id in skills:
		var skill = skills[skill_id]
		var def = skill.definition
		result.append({
			"id": skill_id,
			"name": def.name,
			"category": def.category,
			"icon": def.icon,
			"level": skill.level,
			"xp": skill.xp,
			"progress": get_skill_progress(skill_id),
			"virtual_level": skill.virtual_level
		})
	return result

# =============================================================================
# XP GAIN & LEVELING
# =============================================================================

func grant_skill_xp(skill_id: String, amount: int, source: String = "") -> void:
	if not skills.has(skill_id) or amount <= 0:
		return

	var skill = skills[skill_id]
	if skill.level >= 120:
		return # Max level

	skill.xp += amount
	skill_xp_gained.emit(skill_id, amount, skill.xp)

	# Check for level ups
	while skill.level < 120 and skill.xp >= xp_table[skill.level]:
		_level_up(skill_id)

	_save_skills()

func _level_up(skill_id: String) -> void:
	var skill = skills[skill_id]
	skill.level += 1
	skill_leveled_up.emit(skill_id, skill.level)

	# Check milestones
	var def = skill.definition
	if def.has("milestones") and def.milestones.has(str(skill.level)):
		_reach_milestone(skill_id, skill.level)

	# Virtual levels beyond 120 (for XP tracking)
	if skill.level >= 120:
		skill.virtual_level += 1

func _reach_milestone(skill_id: String, level: int) -> void:
	if not reached_milestones.has(skill_id):
		reached_milestones[skill_id] = []
	reached_milestones[skill_id].append(level)
	milestone_reached.emit(skill_id, level)

	# Grant milestone rewards
	var def = skills[skill_id].definition
	var milestone = def.milestones[str(level)]
	print("Milestone reached: %s level %d - %s" % [skill_id, level, milestone])

	# Grant unlocks
	if def.has("unlocks"):
		_grant_unlocks(def.unlocks)

func _grant_unlocks(unlocks: Dictionary) -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if not save_manager or not save_manager.has_method("unlock_content"):
		return

	if unlocks.has("reagents"):
		for reagent in unlocks.reagents:
			save_manager.unlock_content("reagent", reagent)
	if unlocks.has("equipment"):
		for equip in unlocks.equipment:
			save_manager.unlock_content("equipment", equip)
	if unlocks.has("labs"):
		for lab in unlocks.labs:
			save_manager.unlock_content("lab", lab)
	if unlocks.has("companions"):
		for comp in unlocks.companions:
			save_manager.unlock_content("companion", comp)

# =============================================================================
# INTELLIGENCE POINTS (META-CURRENCY)
# =============================================================================

func grant_intelligence_points(amount: int, source: String = "") -> void:
	if amount <= 0:
		return
	intelligence_points += amount
	intelligence_points_changed.emit(amount, intelligence_points)
	print("Granted %d IP (%s). Total: %d" % [amount, source, intelligence_points])
	_save_skills()

func spend_intelligence_points(amount: int, talent_id: String = "") -> bool:
	if intelligence_points < amount:
		return false
	intelligence_points -= amount
	if talent_id != "":
		unlocked_talents.append(talent_id)
		talent_unlocked.emit(talent_id)
	intelligence_points_changed.emit(-amount, intelligence_points)
	_save_skills()
	return true

# =============================================================================
# TALENT TREES
# =============================================================================

func unlock_talent(tree_id: String, tier_index: int) -> bool:
	var talent_data = SKILL_DATA.intelligence_points.talent_trees[tree_id]
	if not talent_data:
		return false

	if tier_index >= talent_data.tiers.size():
		return false

	var tier = talent_data.tiers[tier_index]

	# Check prerequisites (previous tiers)
	for i in range(tier_index):
		var prereq_id = "%s_tier_%d" % [tree_id, i]
		if not has_talent(prereq_id):
			return false

	var talent_id = "%s_tier_%d" % [tree_id, tier_index]
	if has_talent(talent_id):
		return true

	if spend_intelligence_points(tier.cost, talent_id):
		_apply_talent_effect(tree_id, tier_index, tier.effect)
		return true
	return false

func _apply_talent_effect(tree_id: String, tier_index: int, effect: String) -> void:
	# Apply talent effects to game systems
	match tree_id:
		"synthesis_mastery":
			_apply_synthesis_talent(tier_index, effect)
		"safety_expertise":
			_apply_safety_talent(tier_index, effect)
		"companion_bond":
			_apply_companion_talent(tier_index, effect)
		"exploration":
			_apply_exploration_talent(tier_index, effect)
		"social_influence":
			_apply_social_talent(tier_index, effect)

func _apply_synthesis_talent(tier: int, effect: String) -> void:
	# Apply to chemistry simulations
	var sim_bridge = get_node_or_null("/root/SimulationBridge")
	if sim_bridge:
		match tier:
			0: sim_bridge.set_global_yield_modifier(1.05)
			1: sim_bridge.unlock_protecting_groups()
			2: sim_bridge.set_global_purity_bonus(1.10); sim_bridge.set_global_speed_bonus(0.90)
			3: sim_bridge.enable_retrosynthesis_ai()
			4: sim_bridge.enable_one_click_synthesis()

func _apply_safety_talent(tier: int, effect: String) -> void:
	var vitals = get_node_or_null("/root/PlayerVitals")
	if vitals:
		match tier:
			0: vitals.set_injury_severity_modifier(0.8)
			1: vitals.enable_auto_neutralization()
			2: vitals.set_fume_hood_efficiency(1.25)
			3: vitals.set_radiation_modifier(0.5)
			4: vitals.enable_chrysalis_warden()

func _apply_companion_talent(tier: int, effect: String) -> void:
	var comp_manager = get_node_or_null("/root/CompanionManager")
	if comp_manager:
		match tier:
			0: comp_manager.set_max_slots(4)
			1: comp_manager.set_xp_multiplier(1.25)
			2: comp_manager.unlock_mythic_evolution()
			3: comp_manager.enable_telepathic_link()
			4: comp_manager.unlock_ember_drake()

func _apply_exploration_talent(tier: int, effect: String) -> void:
	# Implement via world system
	pass

func _apply_social_talent(tier: int, effect: String) -> void:
	var faction_sys = get_node_or_null("/root/FactionSystem")
	if faction_sys:
		match tier:
			0: faction_sys.set_rep_multiplier(1.15)
			1: faction_sys.unlock_faction_vendors()
			2: faction_sys.enable_npc_relationships()
			3: faction_sys.enable_mediation()
			4: faction_sys.enable_faction_founding()

# =============================================================================
# SAVE/LOAD
# =============================================================================

func _save_skills() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("set_skill_data"):
		save_manager.set_skill_data({
			"skills": skills,
			"intelligence_points": intelligence_points,
			"unlocked_talents": unlocked_talents,
			"reached_milestones": reached_milestones
		})

func to_dict() -> Dictionary:
	return {
		"skills": skills,
		"intelligence_points": intelligence_points,
		"unlocked_talents": unlocked_talents,
		"reached_milestones": reached_milestones
	}

func from_dict(data: Dictionary) -> void:
	skills = data.get("skills", skills)
	intelligence_points = data.get("intelligence_points", 0)
	unlocked_talents = data.get("unlocked_talents", [])
	reached_milestones = data.get("reached_milestones", {})
	_emit_all_signals()