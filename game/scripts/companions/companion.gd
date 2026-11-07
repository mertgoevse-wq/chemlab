# Companion — Runtime Instance Class (Godot 4 Engine)
# Represents a single companion instance with all runtime state.

class_name Companion
extends RefCounted

# =============================================================================
# SIGNALS
# =============================================================================

signal level_up(new_level: int, old_level: int)
signal loyalty_changed(new_loyalty: int, delta: int)
signal care_need_changed(need: String, value: float)
signal evolution_triggered(new_species_id: String)
signal ability_learned(ability_id: String)
signal battle_experience_gained(xp: int)
signal hunger_critical()      # Hunger <= 20
signal happiness_critical()   # Happiness <= 20
signal companion_fainted()    # Health <= 0

# =============================================================================
# STATE VARIABLES
# =============================================================================

var instance_id: String = ""
var species_id: String = ""
var nickname: String = ""
var personality: CompanionData.Personality = CompanionData.Personality.CURIOUS

var level: int = 1
var xp: int = 0

# Current calculated stats
var current_stats: Dictionary = {
	"health": 50,
	"max_health": 50,
	"mana": 20,
	"max_mana": 20,
	"attack": 10,
	"defense": 8,
	"speed": 15,
	"intelligence": 12
}

# IVs (Individual Values) - determined at creation, 0-31 each
var ivs: Dictionary = {
	"health": 0,
	"mana": 0,
	"attack": 0,
	"defense": 0,
	"speed": 0,
	"intelligence": 0
}

# EVs (Effort Values) - gained through battle/training, max 510 total, 252 per stat
var evs: Dictionary = {
	"health": 0,
	"mana": 0,
	"attack": 0,
	"defense": 0,
	"speed": 0,
	"intelligence": 0
}

var loyalty: int = 0              # 0-1000
var max_loyalty: int = 1000

# Care needs (0-100, 100 = full/satisfied)
var care_needs: Dictionary = {
	"hunger": 100.0,
	"happiness": 100.0,
	"health": 100.0,
	"grooming": 100.0,
	"exercise": 100.0,
	"social": 100.0
}

# Decay rates per hour (modified by personality/species)
var care_decay_rates: Dictionary = {
	"hunger": 5.0,
	"happiness": 2.0,
	"health": 0.5,
	"grooming": 1.0,
	"exercise": 3.0,
	"social": 2.0
}

var known_abilities: Array[String] = []
var equipped_item: String = ""
var active_bonuses: Array[Dictionary] = []

var battle_record: Dictionary = {
	"wins": 0,
	"losses": 0,
	"total_damage_dealt": 0,
	"total_damage_taken": 0,
	"battles_participated": 0
}

var evolution_stage: int = 0
var birth_time: int = 0
var last_care_time: int = 0
var last_decay_time: int = 0

var is_active: bool = false
var slot_index: int = -1  # 0 or 1 for active battle slots

# Species data reference (set by CompanionManager)
var _species_data: Dictionary = {}

# =============================================================================
# INITIALIZATION
# =============================================================================

func _init(p_instance_id: String, p_species_id: String, p_nickname: String = "", p_personality: CompanionData.Personality = CompanionData.Personality.CURIOUS, p_level: int = 1, p_species_data: Dictionary = {}) -> void:
	instance_id = p_instance_id
	species_id = p_species_id
	nickname = p_nickname if p_nickname != "" else _generate_default_nickname()
	personality = p_personality
	_species_data = p_species_data

	birth_time = Time.get_unix_time_from_system()
	last_care_time = birth_time
	last_decay_time = birth_time

	# Generate IVs (0-31)
	_randomize_ivs()

	# Set initial level and calculate stats
	if p_level > 1:
		set_level(p_level)
	else:
		_recalculate_stats()
		_refill_care_needs()

	# Learn starting abilities
	_learn_starting_abilities()

	# Initialize active bonuses from species data
	_initialize_active_bonuses()

func _generate_default_nickname() -> String:
	var base_name = _species_data.get("display_name", species_id)
	return base_name

func _randomize_ivs() -> void:
	for stat in ivs.keys():
		ivs[stat] = randi() % 32

func _learn_starting_abilities() -> void:
	var battle_abilities = _species_data.get("battle_abilities", [])
	for ability_id in battle_abilities:
		if ability_id not in known_abilities:
			known_abilities.append(ability_id)

func _initialize_active_bonuses() -> void:
	var chem_bonuses = _species_data.get("chemistry_bonuses", [])
	for bonus in chem_bonuses:
		# Only activate bonuses that are available at current level
		if _is_bonus_unlocked(bonus):
			active_bonuses.append(bonus.duplicate(true))

func _is_bonus_unlocked(bonus: Dictionary) -> bool:
	var unlock_level = bonus.get("unlock_level", 1)
	return level >= unlock_level

# =============================================================================
# LEVEL & XP SYSTEM
# =============================================================================

func add_xp(amount: int) -> void:
	if level >= CompanionData.MAX_COMPANION_LEVEL:
		return

	xp += amount
	var old_level = level
	var new_level = CompanionData.get_level_for_xp(xp)

	if new_level > old_level:
		set_level(new_level)

	# Grant EVs based on activity
	_grant_effort_values(amount)

func set_level(new_level: int) -> void:
	new_level = clamp(new_level, 1, CompanionData.MAX_COMPANION_LEVEL)
	var old_level = level
	level = new_level
	xp = CompanionData.get_xp_for_level(level)

	_recalculate_stats()
	_check_ability_unlocks()
	_check_evolution()
	_check_bonus_unlocks()

	level_up.emit(level, old_level)

func _recalculate_stats() -> void:
	var base_stats = _species_data.get("base_stats", {})
	var growth_rates = _species_data.get("growth_rates", {})

	for stat_name in current_stats.keys():
		if stat_name.begins_with("max_"):
			continue

		var base = base_stats.get(stat_name, 10)
		var growth = growth_rates.get(stat_name, 1.1)
		var iv = ivs.get(stat_name, 0)
		var ev = evs.get(stat_name, 0)

		var personality_mod = CompanionData.get_personality_modifier(personality, stat_name)

		# Calculate final stat
		var final_stat = CompanionData.calculate_stat(base, growth, level, iv, ev)
		final_stat = int(final_stat * personality_mod)

		current_stats[stat_name] = final_stat

		# Update max health/mana
		if stat_name == "health":
			current_stats["max_health"] = final_stat
		elif stat_name == "mana":
			current_stats["max_mana"] = final_stat

	# Heal to full on level up
	current_stats["health"] = current_stats["max_health"]
	current_stats["mana"] = current_stats["max_mana"]

func _grant_effort_values(xp_gained: int) -> void:
	# Grant EVs based on species battle role and activity
	var battle_role = _species_data.get("battle_role", "UTILITY")
	var ev_gain = max(1, xp_gained / 100)

	match battle_role:
		CompanionData.BattleRole.DPS:
			evs["attack"] = min(252, evs["attack"] + ev_gain)
			evs["speed"] = min(252, evs["speed"] + ev_gain * 0.5)
		CompanionData.BattleRole.TANK:
			evs["health"] = min(252, evs["health"] + ev_gain)
			evs["defense"] = min(252, evs["defense"] + ev_gain * 0.5)
		CompanionData.BattleRole.SUPPORT:
			evs["mana"] = min(252, evs["mana"] + ev_gain)
			evs["intelligence"] = min(252, evs["intelligence"] + ev_gain * 0.5)
		CompanionData.BattleRole.CONTROL:
			evs["intelligence"] = min(252, evs["intelligence"] + ev_gain)
			evs["speed"] = min(252, evs["speed"] + ev_gain * 0.5)
		CompanionData.BattleRole.UTILITY:
			evs["speed"] = min(252, evs["speed"] + ev_gain)
			evs["intelligence"] = min(252, evs["intelligence"] + ev_gain * 0.5)

func get_total_evs() -> int:
	var total = 0
	for ev in evs.values():
		total += ev
	return total

# =============================================================================
# LOYALTY & BONDING
# =============================================================================

func modify_loyalty(delta: int) -> void:
	var old_loyalty = loyalty
	loyalty = clamp(loyalty + delta, 0, max_loyalty)

	if loyalty != old_loyalty:
		loyalty_changed.emit(loyalty, loyalty - old_loyalty)

		# Check for friendship evolution
		if loyalty >= max_loyalty and old_loyalty < max_loyalty:
			_check_friendship_evolution()

func get_loyalty_percent() -> float:
	return loyalty / max_loyalty

func get_loyalty_tier() -> String:
	var pct = get_loyalty_percent()
	if pct >= 1.0: return "Soulbound"
	if pct >= 0.9: return "Devoted"
	if pct >= 0.7: return "Trusted"
	if pct >= 0.5: return "Friendly"
	if pct >= 0.3: return "Acquainted"
	if pct >= 0.1: return "Wary"
	return "Stranger"

# =============================================================================
# CARE SYSTEM
# =============================================================================

func update_care_decay(delta_hours: float) -> void:
	var current_time = Time.get_unix_time_from_system()
	var hours_passed = (current_time - last_decay_time) / 3600.0

	if hours_passed < 0.01:  # Less than 36 seconds
		return

	last_decay_time = current_time

	for need in care_needs.keys():
		var decay_rate = care_decay_rates.get(need, 1.0)

		# Personality modifiers
		if personality == CompanionData.Personality.PLAYFUL and need == "hunger":
			decay_rate *= 0.8
		elif personality == CompanionData.Personality.STOIC and need in ["hunger", "happiness"]:
			decay_rate *= 0.7
		elif personality == CompanionData.Personality.TIMID and need == "social":
			decay_rate *= 1.3

		# Loyalty bonus: higher loyalty = slower decay
		var loyalty_mod = 1.0 - (get_loyalty_percent() * 0.3)  # Up to 30% reduction
		decay_rate *= loyalty_mod

		var old_value = care_needs[need]
		care_needs[need] = max(0.0, care_needs[need] - decay_rate * hours_passed)

		if care_needs[need] != old_value:
			care_need_changed.emit(need, care_needs[need])

		# Critical warnings
		if need == "hunger" and care_needs[need] <= 20.0 and old_value > 20.0:
			hunger_critical.emit()
		elif need == "happiness" and care_needs[need] <= 20.0 and old_value > 20.0:
			happiness_critical.emit()

	# Health damage from neglect
	_check_neglect_damage()

func _check_neglect_damage() -> void:
	var critical_needs = 0
	for need in ["hunger", "health", "happiness"]:
		if care_needs[need] <= 10.0:
			critical_needs += 1

	if critical_needs > 0:
		var dmg = critical_needs * 2.0  # 2 HP per critical need per hour
		take_damage(dmg, "neglect")

func care_action(need: String, amount: float, item_id: String = "") -> bool:
	if not care_needs.has(need):
		return false

	var old_value = care_needs[need]
	care_needs[need] = min(100.0, care_needs[need] + amount)

	# Loyalty gain from care
	var loyalty_gain = int(amount * 0.5 * (1.0 + get_loyalty_percent() * 0.5))
	modify_loyalty(loyalty_gain)

	last_care_time = Time.get_unix_time_from_system()

	# Special item effects
	if item_id != "":
		_apply_care_item_effect(item_id, need)

	care_need_changed.emit(need, care_needs[need])
	return true

func _apply_care_item_effect(item_id: String, need: String) -> void:
	# Item-specific bonus effects
	match item_id:
		"premium_treat":
			modify_loyalty(10)
			care_needs["happiness"] = min(100.0, care_needs["happiness"] + 10.0)
		"vitamin_supplement":
			care_needs["health"] = min(100.0, care_needs["health"] + 15.0)
		"grooming_kit":
			care_needs["grooming"] = 100.0
		"exercise_wheel":
			care_needs["exercise"] = min(100.0, care_needs["exercise"] + 20.0)
		"companion_toy":
			care_needs["social"] = min(100.0, care_needs["social"] + 15.0)
			modify_loyalty(5)

func _refill_care_needs() -> void:
	for need in care_needs.keys():
		care_needs[need] = 100.0

func get_overall_care_score() -> float:
	var total = 0.0
	for value in care_needs.values():
		total += value
	return total / care_needs.size()

# =============================================================================
# HEALTH & COMBAT
# =============================================================================

func take_damage(amount: float, source: String = "unknown") -> bool:
	var defense = current_stats.get("defense", 10)
	var actual_damage = max(1.0, amount - defense * 0.1)

	current_stats["health"] = max(0, current_stats["health"] - actual_damage)
	battle_record["total_damage_taken"] += actual_damage

	# Health care need decreases
	care_needs["health"] = max(0.0, care_needs["health"] - actual_damage * 0.5)
	care_need_changed.emit("health", care_needs["health"])

	if current_stats["health"] <= 0:
		companion_fainted.emit()
		return true
	return false

func heal(amount: float) -> void:
	current_stats["health"] = min(current_stats["max_health"], current_stats["health"] + amount)
	care_needs["health"] = min(100.0, care_needs["health"] + amount * 0.5)
	care_need_changed.emit("health", care_needs["health"])

func restore_mana(amount: float) -> void:
	current_stats["mana"] = min(current_stats["max_mana"], current_stats["mana"] + amount)

func is_fainted() -> bool:
	return current_stats["health"] <= 0

func get_health_percent() -> float:
	var max_hp = current_stats.get("max_health", 1)
	return current_stats["health"] / max_hp

# =============================================================================
# ABILITIES
# =============================================================================

func _check_ability_unlocks() -> void:
	var battle_abilities = _species_data.get("battle_abilities", [])
	var ability_unlock_levels = _species_data.get("ability_unlock_levels", {})

	for ability_id in battle_abilities:
		if ability_id in known_abilities:
			continue

		var unlock_level = ability_unlock_levels.get(ability_id, 1)
		if level >= unlock_level:
			learn_ability(ability_id)

func learn_ability(ability_id: String) -> bool:
	if ability_id in known_abilities:
		return false

	known_abilities.append(ability_id)
	ability_learned.emit(ability_id)
	return true

func forget_ability(ability_id: String) -> bool:
	if ability_id in known_abilities:
		known_abilities.erase(ability_id)
		return true
	return false

func get_available_abilities() -> Array[String]:
	return known_abilities.duplicate()

# =============================================================================
# EVOLUTION
# =============================================================================

func _check_evolution() -> void:
	var evo_data = _species_data.get("evolution_line", {})
	if evo_data.is_empty():
		return

	var trigger = evo_data.get("trigger", "LEVEL_UP")
	var condition = evo_data.get("condition", {})
	var target_species = evo_data.get("evolves_to", "")

	if target_species == "":
		return

	var should_evolve = false

	match trigger:
		"LEVEL_UP":
			var req_level = condition.get("level", 0)
			if level >= req_level:
				should_evolve = true
		"FRIENDSHIP_MAX":
			if loyalty >= max_loyalty:
				should_evolve = true
		"SKILL_MASTERY":
			# Checked externally by CompanionManager
			pass
		"BATTLE_VICTORIES":
			var req_wins = condition.get("wins", 0)
			if battle_record["wins"] >= req_wins:
				should_evolve = true
		"ITEM_USE":
			# Triggered by item use externally
			pass

	if should_evolve:
		evolve(target_species)

func evolve(new_species_id: String, new_species_data: Dictionary = {}) -> bool:
	if new_species_id == species_id:
		return false

	var old_species = species_id
	species_id = new_species_id
	evolution_stage += 1

	# Update species data reference
	if not new_species_data.is_empty():
		_species_data = new_species_data

	# Recalculate stats with new base stats
	_recalculate_stats()

	# Learn new abilities
	_learn_starting_abilities()

	# Update active bonuses
	_initialize_active_bonuses()

	evolution_triggered.emit(new_species_id)
	return true

func can_evolve() -> bool:
	var evo_data = _species_data.get("evolution_line", {})
	if evo_data.is_empty():
		return false

	var trigger = evo_data.get("trigger", "LEVEL_UP")
	var condition = evo_data.get("condition", {})

	match trigger:
		"LEVEL_UP":
			return level >= condition.get("level", 999)
		"FRIENDSHIP_MAX":
			return loyalty >= max_loyalty
		"BATTLE_VICTORIES":
			return battle_record["wins"] >= condition.get("wins", 999)
		"ITEM_USE":
			return _has_evolution_item(condition.get("item_id", ""))
		"SKILL_MASTERY":
			# Checked externally
			return false

	return false

func _has_evolution_item(item_id: String) -> bool:
	# Checked via SaveManager/Inventory
	return false

func get_evolution_info() -> Dictionary:
	var evo_data = _species_data.get("evolution_line", {})
	if evo_data.is_empty():
		return {"can_evolve": false}

	return {
		"can_evolve": can_evolve(),
		"target_species": evo_data.get("evolves_to", ""),
		"trigger": evo_data.get("trigger", ""),
		"condition": evo_data.get("condition", {}),
		"current_stage": evolution_stage
	}

# =============================================================================
# CHEMISTRY BONUSES
# =============================================================================

func _check_bonus_unlocks() -> void:
	var chem_bonuses = _species_data.get("chemistry_bonuses", [])
	for bonus in chem_bonuses:
		if _is_bonus_unlocked(bonus):
			# Check if already active
			var already_active = false
			for active in active_bonuses:
				if active.get("bonus_type") == bonus.get("bonus_type"):
					already_active = true
					break
			if not already_active:
				active_bonuses.append(bonus.duplicate(true))

func get_active_chemistry_bonuses() -> Array[Dictionary]:
	return active_bonuses.duplicate(true)

func get_bonus_magnitude(bonus_type: String) -> float:
	var total = 0.0
	for bonus in active_bonuses:
		if bonus.get("bonus_type") == bonus_type:
			total += bonus.get("magnitude", 0.0)
	return total

func has_bonus(bonus_type: String) -> bool:
	for bonus in active_bonuses:
		if bonus.get("bonus_type") == bonus_type:
			return true
	return false

# =============================================================================
# BATTLE SYSTEM INTEGRATION
# =============================================================================

func record_battle_result(won: bool, damage_dealt: int, damage_taken: int, xp_gained: int) -> void:
	battle_record["battles_participated"] += 1
	battle_record["total_damage_dealt"] += damage_dealt
	battle_record["total_damage_taken"] += damage_taken

	if won:
		battle_record["wins"] += 1
	else:
		battle_record["losses"] += 1

	add_xp(xp_gained)
	battle_experience_gained.emit(xp_gained)

func get_battle_stats() -> Dictionary:
	return {
		"health": current_stats["health"],
		"max_health": current_stats["max_health"],
		"mana": current_stats["mana"],
		"max_mana": current_stats["max_mana"],
		"attack": current_stats["attack"],
		"defense": current_stats["defense"],
		"speed": current_stats["speed"],
		"intelligence": current_stats["intelligence"],
		"abilities": known_abilities.duplicate(),
		"role": _species_data.get("battle_role", "UTILITY")
	}

# =============================================================================
# BREEDING
# =============================================================================

func can_breed_with(other: Companion) -> bool:
	var my_breeding = _species_data.get("breeding", {})
	var other_breeding = other._species_data.get("breeding", {})

	if my_breeding.is_empty() or other_breeding.is_empty():
		return false

	# Same breeding group
	if my_breeding.get("breeding_group") != other_breeding.get("breeding_group"):
		return false

	# Both at max level or high enough
	if level < 30 or other.level < 30:
		return false

	# High loyalty for both
	if loyalty < 500 or other.loyalty < 500:
		return false

	# Not fainted
	if is_fainted() or other.is_fainted():
		return false

	return true

func get_breeding_info() -> Dictionary:
	var breeding = _species_data.get("breeding", {})
	return {
		"breeding_group": breeding.get("breeding_group", ""),
		"breeding_time_hours": breeding.get("breeding_time_hours", 2),
		"egg_type": breeding.get("egg_type", "live_birth"),
		"possible_offspring": breeding.get("offspring_species", []),
		"inheritable_traits": breeding.get("inheritable_traits", [])
	}

# =============================================================================
# SERIALIZATION
# =============================================================================

func to_dict() -> Dictionary:
	return {
		"instance_id": instance_id,
		"species_id": species_id,
		"nickname": nickname,
		"personality": personality,
		"level": level,
		"xp": xp,
		"current_stats": current_stats,
		"ivs": ivs,
		"evs": evs,
		"loyalty": loyalty,
		"care_needs": care_needs,
		"care_decay_rates": care_decay_rates,
		"known_abilities": known_abilities,
		"equipped_item": equipped_item,
		"active_bonuses": active_bonuses,
		"battle_record": battle_record,
		"evolution_stage": evolution_stage,
		"birth_time": birth_time,
		"last_care_time": last_care_time,
		"last_decay_time": last_decay_time,
		"is_active": is_active,
		"slot_index": slot_index
	}

static func from_dict(data: Dictionary, species_data: Dictionary = {}) -> Companion:
	var comp = Companion.new()
	comp.instance_id = data.get("instance_id", "")
	comp.species_id = data.get("species_id", "")
	comp.nickname = data.get("nickname", "")
	comp.personality = data.get("personality", CompanionData.Personality.CURIOUS)
	comp.level = data.get("level", 1)
	comp.xp = data.get("xp", 0)
	comp.current_stats = data.get("current_stats", {})
	comp.ivs = data.get("ivs", {})
	comp.evs = data.get("evs", {})
	comp.loyalty = data.get("loyalty", 0)
	comp.care_needs = data.get("care_needs", {})
	comp.care_decay_rates = data.get("care_decay_rates", {})
	comp.known_abilities = data.get("known_abilities", [])
	comp.equipped_item = data.get("equipped_item", "")
	comp.active_bonuses = data.get("active_bonuses", [])
	comp.battle_record = data.get("battle_record", {})
	comp.evolution_stage = data.get("evolution_stage", 0)
	comp.birth_time = data.get("birth_time", 0)
	comp.last_care_time = data.get("last_care_time", 0)
	comp.last_decay_time = data.get("last_decay_time", 0)
	comp.is_active = data.get("is_active", false)
	comp.slot_index = data.get("slot_index", -1)
	comp._species_data = species_data

	# Reinitialize bonuses if needed
	if comp.active_bonuses.is_empty():
		comp._initialize_active_bonuses()

	return comp

# =============================================================================
# DISPLAY & UTILITY
# =============================================================================

func get_display_name() -> String:
	return nickname if nickname != "" else _species_data.get("display_name", species_id)

func get_species_display_name() -> String:
	return _species_data.get("display_name", species_id)

func get_rarity() -> CompanionData.Rarity:
	return _species_data.get("rarity", CompanionData.Rarity.COMMON)

func get_category() -> CompanionData.CompanionCategory:
	return _species_data.get("category", CompanionData.CompanionCategory.REAL_ANIMAL)

func get_battle_role() -> CompanionData.BattleRole:
	return _species_data.get("battle_role", CompanionData.BattleRole.UTILITY)

func get_personality_name() -> String:
	var names = {
		CompanionData.Personality.CURIOUS: "Curious",
		CompanionData.Personality.LOYAL: "Loyal",
		CompanionData.Personality.PLAYFUL: "Playful",
		CompanionData.Personality.STOIC: "Stoic",
		CompanionData.Personality.AGGRESSIVE: "Aggressive",
		CompanionData.Personality.TIMID: "Timid",
		CompanionData.Personality.INTELLECTUAL: "Intellectual",
		CompanionData.Personality.PROTECTIVE: "Protective",
		CompanionData.Personality.MISCHIEVOUS: "Mischievous",
		CompanionData.Personality.NOBLE: "Noble"
	}
	return names.get(personality, "Unknown")

func get_summary() -> Dictionary:
	return {
		"instance_id": instance_id,
		"name": get_display_name(),
		"species": get_species_display_name(),
		"level": level,
		"loyalty_tier": get_loyalty_tier(),
		"health_pct": get_health_percent(),
		"care_score": get_overall_care_score(),
		"rarity": get_rarity(),
		"personality": get_personality_name(),
		"is_active": is_active,
		"slot_index": slot_index,
		"evolution_info": get_evolution_info()
	}