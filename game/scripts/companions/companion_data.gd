# Companion System — Data Structures & Enums (Godot 4 Engine)
# Defines all companion species, rarities, personalities, and chemistry support bonuses.
# Complements the existing progressive skill/quest system.

class_name CompanionData
extends RefCounted

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

enum CompanionCategory {
	REAL_ANIMAL,       # Lab rats, cats, dogs, birds, reptiles, amphibians
	AETHERKIN          # Original alchemical creatures: Cinderling, Brinejack, Null Moth, Ember Drake...
}

enum Rarity {
	COMMON,        # 1-star: Easy to acquire, modest bonuses
	UNCOMMON,      # 2-star: Moderate acquisition, good bonuses
	RARE,          # 3-star: Hard to find, strong bonuses
	EPIC,          # 4-star: Very rare, powerful bonuses
	LEGENDARY,     # 5-star: Extremely rare, game-changing bonuses
	MYTHIC         # 6-star: Unique (Dragon, Phoenix at level 100+)
}

enum Personality {
	CURIOUS,       # Bonus: Detection/analysis speed
	LOYAL,         # Bonus: Loyalty gain, damage reduction
	PLAYFUL,       # Bonus: XP gain, hunger slower
	STOIC,         # Bonus: Stress resistance, safety compliance
	AGGRESSIVE,    # Bonus: Battle damage, intimidation
	TIMID,         # Bonus: Stealth, escape chance
	INTELLECTUAL,  # Bonus: Computational/science XP
	PROTECTIVE,    # Bonus: Shield allies, damage intercept
	MISCHIEVOUS,   # Bonus: Reagent discovery, chaos effects
	NOBLE          # Bonus: All stats, rare evolution paths
}

enum CareNeed {
	HUNGER,        # Food consumption rate
	HAPPINESS,     # Interaction/play needs
	HEALTH,        # Medical attention, injury recovery
	GROOMING,      # Cleaning, maintenance
	EXERCISE,      # Activity, movement needs
	SOCIAL         # Bonding with player/other companions
}

enum EvolutionTrigger {
	LEVEL_UP,           # Reach specific level
	ITEM_USE,           # Use evolution item
	FRIENDSHIP_MAX,     # Max loyalty/bond
	SKILL_MASTERY,      # Player reaches skill level
	BATTLE_VICTORIES,   # Win N battles
	SPECIAL_CONDITION,  # Unique condition (time, location, etc.)
	BREEDING_RESULT     # Result of breeding
}

enum BattleRole {
	SUPPORT,      # Buffs, heals, utility
	DPS,          # Damage dealer
	TANK,         # Damage absorption, taunt
	CONTROL,      # Debuffs, crowd control
	UTILITY       # Special mechanics (detection, etc.)
}

# Max companions system
const MAX_COMPANIONS_OWNED: int = 3      # Later upgradeable to 5
const MAX_ACTIVE_COMPANIONS: int = 2     # Battle party size
const MAX_COMPANION_LEVEL: int = 100
const BASE_LOYALTY_GAIN_PER_INTERACTION: float = 1.0
const BASE_HUNGER_DECAY_PER_HOUR: float = 5.0

# =============================================================================
# DATA CLASSES (using Dictionary-based approach for serialization)
# =============================================================================

# SpeciesBaseData — Static species definition (loaded from JSON)
# {
#   "species_id": "lab_rat",
#   "display_name": "Lab Rat",
#   "category": "REAL_ANIMAL",
#   "rarity": "COMMON",
#   "description": "A keen-nosed rodent trained to detect impurities.",
#   "base_stats": {
#     "health": 50,
#     "mana": 20,
#     "attack": 10,
#     "defense": 8,
#     "speed": 15,
#     "intelligence": 12
#   },
#   "growth_rates": {        # Per-level stat growth multipliers
#     "health": 1.15,
#     "mana": 1.10,
#     "attack": 1.12,
#     "defense": 1.10,
#     "speed": 1.08,
#     "intelligence": 1.15
#   },
#   "chemistry_bonuses": [
#     {
#       "bonus_type": "IMPURITY_DETECTION",
#       "description": "Detects reagent impurities 20% faster",
#       "magnitude": 0.20,
#       "skill_synergy": ["analytical", "safety"]
#     }
#   ],
#   "battle_role": "UTILITY",
#   "battle_abilities": ["sniff_out", "quick_bite", "scurry"],
#   "evolution_line": {
#     "evolves_to": "enhanced_lab_rat",
#     "trigger": "LEVEL_UP",
#     "condition": {"level": 25}
#   },
#   "care_profile": {
#     "hunger_rate": 1.0,
#     "happiness_decay": 0.5,
#     "preferred_food": ["cheese", "seeds", "pellets"],
#     "favorite_activity": "maze_run"
#   },
#   "breeding": {
#     "breeding_group": "rodent",
#     "breeding_time_hours": 2,
#     "egg_type": "live_birth",
#     "offspring_species": ["lab_rat", "enhanced_lab_rat"],
#     "inheritable_traits": ["intelligence", "speed"]
#   },
#   "unlock_requirement": {
#     "type": "DEFAULT",
#     "value": null
#   },
#   "sprite_path": "res://assets/companions/lab_rat.tscn",
#   "portrait_path": "res://assets/companions/portraits/lab_rat.png"
# }

# CompanionInstanceData — Runtime companion state (saved to JSON)
# {
#   "instance_id": "comp_001",
#   "species_id": "lab_rat",
#   "nickname": "Ratthew",
#   "personality": "CURIOUS",
#   "level": 1,
#   "xp": 0,
#   "current_stats": {
#     "health": 50,
#     "max_health": 50,
#     "mana": 20,
#     "max_mana": 20,
#     "attack": 10,
#     "defense": 8,
#     "speed": 15,
#     "intelligence": 12
#   },
#   "loyalty": 0,              # 0-1000 (1000 = max bond)
#   "care_needs": {
#     "hunger": 100,           # 0-100 (100 = full)
#     "happiness": 100,
#     "health": 100,
#     "grooming": 100,
#     "exercise": 100,
#     "social": 100
#   },
#   "active_bonuses": [],      # Currently active chemistry bonuses
#   "known_abilities": ["sniff_out"],
#   "equipped_item": null,
#   "battle_record": {
#     "wins": 0,
#     "losses": 0,
#     "total_damage_dealt": 0,
#     "total_damage_taken": 0
#   },
#   "evolution_stage": 0,
#   "birth_time": 0,           # Unix timestamp
#   "last_care_time": 0,
#   "is_active": false,        # In battle party
#   "slot_index": -1           # 0 or 1 for active slots
# }

# =============================================================================
# CHEMISTRY BONUS TYPES
# =============================================================================

# IMPURITY_DETECTION — Reduces impurity generation chance, faster analysis
# HEAT_RESISTANCE — Player takes less heat damage, reactions more stable
# FIRE_RESISTANCE — Reduces fire/explosion risk
# REBIRTH — On fatal accident, revive once with cooldown
# YIELD_BOOST — Increases synthesis yield %
# PURITY_BOOST — Increases product purity
# REAGENT_FINDER — Chance to find extra reagents
# XP_MULTIPLIER — Bonus skill XP from all sources
# SAFETY_BUFFER — Safety score decays slower
# REACTION_ACCELERATOR — Reactions complete faster
# CATALYST_EFFICIENCY — Catalysts last longer / work better
# HAZARD_IMMUNITY — Immune to specific hazard types
# MANA_REGEN — Faster mana/stamina regeneration
# LOOT_QUALITY — Better quality drops
# BREEDING_BOOST — Better breeding outcomes

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

static func rarity_to_stars(rarity: Rarity) -> int:
	return rarity + 1

static func rarity_to_color(rarity: Rarity) -> Color:
	match rarity:
		Rarity.COMMON: return Color(0.7, 0.7, 0.7)      # Gray
		Rarity.UNCOMMON: return Color(0.2, 0.8, 0.2)    # Green
		Rarity.RARE: return Color(0.2, 0.5, 1.0)        # Blue
		Rarity.EPIC: return Color(0.7, 0.3, 1.0)        # Purple
		Rarity.LEGENDARY: return Color(1.0, 0.7, 0.1)   # Gold
		Rarity.MYTHIC: return Color(1.0, 0.2, 0.6)      # Red-Pink
	return Color(1, 1, 1)

static func personality_to_color(personality: Personality) -> Color:
	match personality:
		Personality.CURIOUS: return Color(0.4, 0.8, 1.0)
		Personality.LOYAL: return Color(0.9, 0.6, 0.2)
		Personality.PLAYFUL: return Color(1.0, 0.5, 0.8)
		Personality.STOIC: return Color(0.6, 0.6, 0.7)
		Personality.AGGRESSIVE: return Color(1.0, 0.3, 0.3)
		Personality.TIMID: return Color(0.7, 0.8, 0.9)
		Personality.INTELLECTUAL: return Color(0.5, 0.4, 1.0)
		Personality.PROTECTIVE: return Color(0.3, 0.9, 0.5)
		Personality.MISCHIEVOUS: return Color(0.9, 0.4, 1.0)
		Personality.NOBLE: return Color(1.0, 0.85, 0.2)
	return Color(1, 1, 1)

static func category_to_string(cat: CompanionCategory) -> String:
	match cat:
		CompanionCategory.REAL_ANIMAL: return "Working Animal"
		CompanionCategory.AETHERKIN: return "Aetherkin"
	return "Unknown"

static func battle_role_to_string(role: BattleRole) -> String:
	match role:
		BattleRole.SUPPORT: return "Support"
		BattleRole.DPS: return "DPS"
		BattleRole.TANK: return "Tank"
		BattleRole.CONTROL: return "Control"
		BattleRole.UTILITY: return "Utility"
	return "Unknown"

static func care_need_to_string(need: CareNeed) -> String:
	match need:
		CareNeed.HUNGER: return "Hunger"
		CareNeed.HAPPINESS: return "Happiness"
		CareNeed.HEALTH: return "Health"
		CareNeed.GROOMING: return "Grooming"
		CareNeed.EXERCISE: return "Exercise"
		CareNeed.SOCIAL: return "Social"
	return "Unknown"

static func get_xp_for_level(level: int) -> int:
	"""Uses the canonical exponential progression curve for levels 1-120."""
	if level <= 1:
		return 0
	var total = 0
	for i in range(1, level):
		total += int(floor(i + 300.0 * pow(2.0, i / 7.0) / 4.0))
	return total

static func get_level_for_xp(xp: int) -> int:
	var level = 1
	while level < MAX_COMPANION_LEVEL:
		var next_xp = get_xp_for_level(level + 1)
		if xp < next_xp:
			break
		level += 1
	return level

static func calculate_stat(base: float, growth: float, level: int, iv: float = 0.0, ev: float = 0.0) -> int:
	"""Calculate stat at given level with IV/EV system (Pokemon-style)."""
	# Formula: floor((2 * base + iv + ev/4) * level / 100) + level + 10 (for HP) or +5 (others)
	var stat = (2.0 * base + iv + ev / 4.0) * level / 100.0
	return int(floor(stat)) + level + 5

static func get_personality_modifier(personality: Personality, stat_name: String) -> float:
	"""Personality provides ±10% modifier to specific stats."""
	match personality:
		Personality.CURIOUS:
			if stat_name in ["intelligence", "speed"]: return 1.1
		Personality.LOYAL:
			if stat_name in ["defense", "health"]: return 1.1
		Personality.PLAYFUL:
			if stat_name in ["speed", "attack"]: return 1.1
		Personality.STOIC:
			if stat_name in ["defense", "health"]: return 1.15
		Personality.AGGRESSIVE:
			if stat_name == "attack": return 1.15
			if stat_name == "defense": return 0.95
		Personality.TIMID:
			if stat_name == "speed": return 1.15
			if stat_name == "attack": return 0.9
		Personality.INTELLECTUAL:
			if stat_name == "intelligence": return 1.2
			if stat_name == "attack": return 0.9
		Personality.PROTECTIVE:
			if stat_name in ["defense", "health"]: return 1.1
		Personality.MISCHIEVOUS:
			if stat_name in ["speed", "intelligence"]: return 1.1
		Personality.NOBLE:
			return 1.05  # All stats +5%
	return 1.0