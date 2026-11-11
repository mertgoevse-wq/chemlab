# Athanor Ascension - Companion System (Aetherkin Runtime)
# Autoload: CompanionManager
# Handles: 26+ species, abilities, evolution, bonding, auto-battler, tactical combat

extends Node

signal companion_added(companion_id: String, species_id: String)
signal companion_removed(companion_id: String)
signal companion_evolved(companion_id: String, new_stage: int)
signal companion_bond_changed(companion_id: String, bond_level: float)
signal companion_xp_gained(companion_id: String, amount: int)
signal companion_ability_triggered(companion_id: String, ability_id: String)
signal active_companions_changed()
signal companion_summoned(companion_id: String, entity_node: Node)
signal companion_dismissed(companion_id: String)
signal companion_sniff_result(companion_id: String, apparatus: Node, diagnostic: Dictionary)
signal companion_scavenge_result(companion_id: String, zone: Node, loot: Array)
signal skill_synergy_applied(companion_id: String, synergy_info: Dictionary)

const SPECIES_DATA = preload("res://data/companions/species_database.json")

# Companion runtime data
var companions: Dictionary = {}  # companion_id -> CompanionInstance
var active_companions: Array[String] = []  # Max 2 walking, 3 total (5 at Lv 50)
var spawned_entities: Dictionary = {}  # companion_id -> CompanionEntity (3D in-lab instance)
var max_active_walking: int = 2
var max_total_companions: int = 3
var next_companion_id: int = 1
var _species_cache: Dictionary = {}

# Companion runtime class
class CompanionInstance:
	var companion_id: String = ""
	var species_id: String = ""
	var name: String = ""
	var level: int = 1
	var xp: int = 0
	var bond: float = 0.0  # 0.0 - 1.0
	var evolution_stage: int = 0  # 0 = base, 1 = evolved, 2 = mythic
	var loyalty: float = 0.5  # 0.0 - 1.0
	var hunger: float = 0.0  # 0.0 - 1.0
	var energy: float = 1.0  # 0.0 - 1.0
	var active: bool = false
	var position: Vector3 = Vector3.ZERO
	var current_ability_cooldowns: Dictionary = {}
	var known_abilities: Array[String] = []
	var stats: Dictionary = {}  # Modified by evolution, bond, equipment

func _ready() -> void:
	_load_species_data()
	_load_save_data()

func _load_species_data() -> void:
	if not _species_cache.is_empty():
		return
	if SPECIES_DATA and SPECIES_DATA.data is Dictionary:
		var data: Dictionary = SPECIES_DATA.data
		for category in ["working_animals", "aetherkin"]:
			if data.has(category) and data[category] is Array:
				for sp in data[category]:
					if sp is Dictionary and sp.has("id"):
						_species_cache[sp.id] = sp

func _get_species(species_id: String) -> Dictionary:
	_load_species_data()
	return _species_cache.get(species_id, {})

func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_companion_data"):
		var data = save_manager.get_companion_data()
		if data:
			companions = data.companions
			active_companions = data.active_companions
			max_active_walking = data.max_active_walking
			max_total_companions = data.max_total_companions
			next_companion_id = data.next_companion_id
			_emit_active_changed()

func _emit_active_changed() -> void:
	active_companions_changed.emit()

# =============================================================================
# PUBLIC API - COMPANION MANAGEMENT
# =============================================================================

func add_companion(species_id: String, custom_name: String = "") -> String:
	var species = _get_species(species_id)
	if species.is_empty():
		return ""

	# Check max companions
	if companions.size() >= max_total_companions:
		return ""

	var companion_id = "comp_%d" % next_companion_id
	next_companion_id += 1

	var comp = CompanionInstance.new()
	comp.companion_id = companion_id
	comp.species_id = species_id
	comp.name = custom_name if custom_name != "" else species.get("name", species_id)
	comp.level = 1
	comp.xp = 0
	comp.bond = 0.1
	comp.evolution_stage = 0
	comp.loyalty = 0.5
	comp.hunger = 0.0
	comp.energy = 1.0
	comp.active = false
	comp.stats = _calculate_base_stats(species).duplicate()

	# Learn starting abilities
	for ability in species.get("starting_abilities", []):
		comp.known_abilities.append(ability)

	companions[companion_id] = comp
	companion_added.emit(companion_id, species_id)

	# Auto-activate if slots available
	if active_companions.size() < max_active_walking:
		set_companion_active(companion_id, true)

	_save_companions()
	return companion_id

func remove_companion(companion_id: String) -> bool:
	if not companions.has(companion_id):
		return false

	set_companion_active(companion_id, false)
	companions.erase(companion_id)
	companion_removed.emit(companion_id)
	_save_companions()
	return true

func set_companion_active(companion_id: String, active: bool) -> bool:
	if not companions.has(companion_id):
		return false

	var comp = companions[companion_id]
	if comp.active == active:
		return true

	if active:
		if active_companions.size() >= max_active_walking:
			return false
		comp.active = true
		active_companions.append(companion_id)
	else:
		comp.active = false
		active_companions.erase(companion_id)

	active_companions_changed.emit()
	_save_companions()
	return true

func get_active_companions() -> Array[Dictionary]:
	var result = []
	for comp_id in active_companions:
		if companions.has(comp_id):
			result.append(_companion_to_dict(companions[comp_id]))
	return result

func get_all_companions() -> Array[Dictionary]:
	var result = []
	for comp in companions.values():
		result.append(_companion_to_dict(comp))
	return result

func get_companion(companion_id: String) -> Dictionary:
	if companions.has(companion_id):
		return _companion_to_dict(companions[companion_id])
	return {}

# =============================================================================
# XP, LEVELING, EVOLUTION
# =============================================================================

func grant_companion_xp(companion_id: String, amount: int) -> void:
	if not companions.has(companion_id) or amount <= 0:
		return

	var comp: CompanionInstance = companions[companion_id]
	var species = _get_species(comp.species_id)

	comp.xp += amount
	companion_xp_gained.emit(companion_id, amount)

	# Check level up
	var xp_for_next = _xp_for_level(comp.level + 1, species)
	while comp.xp >= xp_for_next:
		_level_up_companion(companion_id)
		xp_for_next = _xp_for_level(comp.level + 1, species)

	_save_companions()

func _level_up_companion(companion_id: String) -> void:
	var comp: CompanionInstance = companions[companion_id]
	var species = _get_species(comp.species_id)

	comp.level += 1

	# Grant stat increases
	_apply_level_stats(comp, species)

	# Learn new abilities
	var ability_unlocks = species.get("ability_unlocks", {})
	if ability_unlocks.has(str(comp.level)):
		for ability in ability_unlocks[str(comp.level)]:
			if ability not in comp.known_abilities:
				comp.known_abilities.append(ability)

	# Check evolution
	var evolution_stages = species.get("evolution_stages", {})
	if evolution_stages.has(str(comp.level)):
		var stage_info = evolution_stages[str(comp.level)]
		var target_stage = stage_info.get("stage", 0) if stage_info is Dictionary else int(stage_info)
		if comp.evolution_stage < target_stage:
			_evolve_companion(companion_id)

	print("%s reached level %d!" % [comp.name, comp.level])

func _evolve_companion(companion_id: String) -> void:
	var comp: CompanionInstance = companions[companion_id]
	var species = _get_species(comp.species_id)

	comp.evolution_stage += 1
	var evo_names = species.get("evolution_names", [])
	var evo_name = evo_names[comp.evolution_stage] if comp.evolution_stage < evo_names.size() else species.get("name", "")
	comp.name = "%s (%s)" % [species.get("name", ""), evo_name]

	# Apply evolution stat multipliers
	var evolution_stages = species.get("evolution_stages", {})
	if evolution_stages.has(str(comp.level)):
		var evo_data = evolution_stages[str(comp.level)]
		if evo_data is Dictionary:
			var multipliers = evo_data.get("stat_multipliers", {})
			for stat in multipliers:
				comp.stats[stat] = comp.stats.get(stat, 1.0) * multipliers[stat]

			# Unlock evolution abilities
			if evo_data.has("abilities"):
				for ability in evo_data.abilities:
					if ability not in comp.known_abilities:
						comp.known_abilities.append(ability)

	companion_evolved.emit(companion_id, comp.evolution_stage)
	print("%s evolved to %s!" % [comp.name, evo_name])

func _xp_for_level(level: int, _species: Dictionary) -> int:
	# Exponential XP curve adapted for companions
	var base = 100
	return int(base * pow(1.5, level - 1))

func _calculate_base_stats(species: Dictionary) -> Dictionary:
	return species.get("base_stats", {}).duplicate()

func _apply_level_stats(comp: CompanionInstance, species: Dictionary) -> void:
	var growth = species.get("stat_growth_per_level", {})
	for stat in growth:
		comp.stats[stat] = comp.stats.get(stat, 1.0) + growth[stat]

# =============================================================================
# BONDING SYSTEM
# =============================================================================

func modify_bond(companion_id: String, amount: float) -> void:
	if not companions.has(companion_id):
		return

	var comp: CompanionInstance = companions[companion_id]
	comp.bond = clamp(comp.bond + amount, 0.0, 1.0)

	# Bond milestones
	_check_bond_milestones(comp)

	companion_bond_changed.emit(companion_id, comp.bond)
	_save_companions()

func _check_bond_milestones(comp: CompanionInstance) -> void:
	var milestones = [0.25, 0.5, 0.75, 0.9, 1.0]
	for milestone in milestones:
		if comp.bond >= milestone:
			# Grant milestone rewards
			_grant_bond_reward(comp, milestone)

func _grant_bond_reward(comp: CompanionInstance, milestone: float) -> void:
	match milestone:
		0.25:
			# Unlock passive ability
			var species = _get_species(comp.species_id)
			var passives = species.get("passive_abilities", [])
			if passives.size() > 0:
				var passive = passives[0]
				if passive not in comp.known_abilities:
					comp.known_abilities.append(passive)
		0.5:
			# Stat boost
			for stat in comp.stats:
				comp.stats[stat] *= 1.1
		0.75:
			# Active ability upgrade
			pass
		0.9:
			# Visual change (glow, particle effect)
			pass
		1.0:
			# Mythic evolution unlock (if species has it)
			var species = _get_species(comp.species_id)
			if species.has("mythic_evolution"):
				# Unlock mythic quest
				pass

# =============================================================================
# ABILITIES SYSTEM
# =============================================================================

func trigger_ability(companion_id: String, ability_id: String, target: Variant = null) -> bool:
	if not companions.has(companion_id):
		return false

	var comp: CompanionInstance = companions[companion_id]
	if ability_id not in comp.known_abilities:
		return false

	if comp.current_ability_cooldowns.has(ability_id):
		var remaining = comp.current_ability_cooldowns[ability_id]
		if remaining > 0:
			return false

	# Get ability definition
	var ability_def = _get_ability_definition(ability_id)
	if not ability_def:
		return false

	# Check energy cost
	var energy_cost = ability_def.get("energy_cost", 0.0)
	if comp.energy < energy_cost:
		return false

	comp.energy -= energy_cost
	comp.current_ability_cooldowns[ability_id] = ability_def.get("cooldown", 0.0)

	# Execute ability effect
	_execute_ability_effect(companion_id, ability_id, ability_def, target)

	companion_ability_triggered.emit(companion_id, ability_id)
	return true

func _execute_ability_effect(companion_id: String, ability_id: String, ability_def: Dictionary, target: Variant) -> void:
	var comp: CompanionInstance = companions[companion_id]
	var ability_type = ability_def.get("type", "")

	# Lab buff abilities
	if ability_type == "lab_buff":
		_apply_lab_buff(ability_def, comp)

	# Combat abilities (tactical)
	elif ability_type == "combat":
		_execute_combat_ability(ability_id, ability_def, comp, target)

	# Utility abilities
	elif ability_type == "utility":
		_execute_utility_ability(ability_id, ability_def, comp, target)

	# Passive abilities are always active
	elif ability_type == "passive":
		pass  # Handled in stat calculations

func _apply_lab_buff(ability_def: Dictionary, _comp: CompanionInstance) -> void:
	var sim_bridge = get_node_or_null("/root/SimulationBridge")
	if not sim_bridge:
		return

	for effect in ability_def.get("effects", []):
		match effect.get("type", ""):
			"yield_bonus":
				sim_bridge.set_global_yield_modifier(sim_bridge.get_global_yield_modifier() + effect.value)
			"purity_bonus":
				sim_bridge.set_global_purity_bonus(sim_bridge.get_global_purity_bonus() + effect.value)
			"speed_bonus":
				sim_bridge.set_global_speed_modifier(sim_bridge.get_global_speed_modifier() - effect.value)
			"impurity_detection":
				sim_bridge.enable_impurity_detection(effect.value)
			"hazard_warning":
				sim_bridge.enable_hazard_warning(effect.value)

func _execute_combat_ability(_ability_id: String, _ability_def: Dictionary, _comp: CompanionInstance, _target: Variant) -> void:
	# Tactical combat: positioning, timing, resource management
	# This integrates with the combat system
	pass

func _execute_utility_ability(ability_id: String, _ability_def: Dictionary, _comp: CompanionInstance, _target: Variant) -> void:
	match ability_id:
		"fetch_reagent":
			# Companion fetches reagent from storage
			pass
		"clean_spill":
			# Auto-neutralize spill
			var vitals = get_node_or_null("/root/PlayerVitals")
			if vitals and vitals.has_method("trigger_auto_neutralize"):
				vitals.trigger_auto_neutralize()
		"detect_contamination":
			# Enable contamination vision mode
			pass

# =============================================================================
# CARE SYSTEM (Hunger, Energy, Loyalty)
# =============================================================================

func _process(delta: float) -> void:
	for comp in companions.values():
		# Hunger increases over time
		comp.hunger = clamp(comp.hunger + delta * 0.0001, 0.0, 1.0)

		# Energy regenerates
		comp.energy = clamp(comp.energy + delta * 0.001, 0.0, 1.0)

		# Loyalty decreases if neglected
		if comp.hunger > 0.7 or comp.energy < 0.2:
			comp.loyalty = clamp(comp.loyalty - delta * 0.00005, 0.0, 1.0)

		# Cooldown reduction
		for ability_id in comp.current_ability_cooldowns:
			comp.current_ability_cooldowns[ability_id] = max(0.0, comp.current_ability_cooldowns[ability_id] - delta)

		# Low loyalty effects
		if comp.loyalty < 0.3:
			# Chance to disobey, reduced effectiveness
			pass

func feed_companion(companion_id: String, food_id: String) -> bool:
	if not companions.has(companion_id):
		return false

	var comp: CompanionInstance = companions[companion_id]
	var food_def = _get_food_definition(food_id)
	if not food_def:
		return false

	comp.hunger = clamp(comp.hunger - food_def.get("nutrition", 0.0), 0.0, 1.0)
	comp.loyalty = clamp(comp.loyalty + food_def.get("loyalty_bonus", 0.0), 0.0, 1.0)
	comp.energy = clamp(comp.energy + food_def.get("energy_restore", 0.0), 0.0, 1.0)

	modify_bond(companion_id, food_def.get("bond_bonus", 0.0))
	return true

# =============================================================================
# AUTO-BATTLER / TACTICAL COMBAT
# =============================================================================

func start_auto_battle(enemy_party: Array[Dictionary]) -> Dictionary:
	# Auto-battler: Team composition, passive buffs, never required for progression
	var active = get_active_companions()
	if active.is_empty():
		return { "success": false, "reason": "no_active_companions" }

	var battle_result = {
		"victory": false,
		"turns": 0,
		"damage_dealt": 0,
		"damage_taken": 0,
		"xp_gained": 0,
		"loot": []
	}

	# Simplified auto-battle simulation
	var team_power = 0
	for comp_data in active:
		var comp: CompanionInstance = companions[comp_data.companion_id]
		team_power += comp.level * comp.stats.get("power", 10) * (1.0 + comp.bond)

	var enemy_power = 0
	for enemy in enemy_party:
		enemy_power += enemy.level * enemy.stats.get("power", 10)

	if team_power > enemy_power * 1.2:
		battle_result.victory = true
		battle_result.xp_gained = int(enemy_power * 0.5)
		for comp_data in active:
			grant_companion_xp(comp_data.companion_id, battle_result.xp_gained / active.size())
	else:
		battle_result.xp_gained = int(enemy_power * 0.1)

	battle_result.turns = int(10 * (enemy_power / max(team_power, 1)))
	return battle_result

func start_tactical_combat(enemy_party: Array[Dictionary]) -> Dictionary:
	# Tactical combat: Direct control, positioning, timing, resource management
	# This would open a combat scene
	return { "scene": "res://scenes/combat/tactical_combat.tscn", "party": get_active_companions(), "enemies": enemy_party }

# =============================================================================
# HELPERS
# =============================================================================

func _companion_to_dict(comp: CompanionInstance) -> Dictionary:
	return {
		"companion_id": comp.companion_id,
		"species_id": comp.species_id,
		"name": comp.name,
		"level": comp.level,
		"xp": comp.xp,
		"bond": comp.bond,
		"evolution_stage": comp.evolution_stage,
		"loyalty": comp.loyalty,
		"hunger": comp.hunger,
		"energy": comp.energy,
		"active": comp.active,
		"known_abilities": comp.known_abilities,
		"stats": comp.stats,
		"species_name": _get_species(comp.species_id).get("name", comp.species_id)
	}

func _get_ability_definition(ability_id: String) -> Dictionary:
	# Would load from abilities database
	return {}

func _get_food_definition(food_id: String) -> Dictionary:
	# Would load from food database
	return {}

# =============================================================================
# 3D PHYSICAL COMPANION SUMMONING & LABORATORY COMMANDS
# =============================================================================

func summon_companion(companion_id: String, parent_node: Node3D = null, spawn_pos: Vector3 = Vector3.ZERO) -> CharacterBody3D:
	"""Summon an active companion into the 3D physical laboratory environment."""
	if not companions.has(companion_id):
		push_warning("CompanionManager: cannot summon unknown companion '%s'" % companion_id)
		return null

	var comp: CompanionInstance = companions[companion_id]

	# Ensure marked active
	if not comp.active:
		set_companion_active(companion_id, true)

	# If already spawned, return existing entity
	if spawned_entities.has(companion_id) and is_instance_valid(spawned_entities[companion_id]):
		return spawned_entities[companion_id]

	# Instantiate CompanionEntity
	var entity_script = load("res://scenes/companions/companion_entity.gd")
	var entity = entity_script.new() as CharacterBody3D
	entity.name = "Companion_%s" % companion_id
	entity.companion_instance_id = companion_id
	entity.species_id = comp.species_id
	entity.companion_name = comp.name

	# Determine parent scene tree location
	var target_parent = parent_node
	if target_parent == null:
		var tree = get_tree()
		if tree and tree.current_scene:
			target_parent = tree.current_scene

	if target_parent:
		target_parent.add_child(entity)
		# Position near player or designated spawn
		var player_node = target_parent.get_node_or_null("Player")
		if player_node and player_node is Node3D:
			entity.set_target_player(player_node)
			if spawn_pos == Vector3.ZERO:
				entity.global_position = player_node.global_position + Vector3(1.2, 0.2, 1.0)
			else:
				entity.global_position = spawn_pos
		elif spawn_pos != Vector3.ZERO:
			entity.global_position = spawn_pos

	# Connect entity signals
	entity.sniff_completed.connect(func(apparatus: Node, diagnostic: Dictionary):
		_on_companion_sniff_completed(companion_id, apparatus, diagnostic)
	)
	entity.scavenge_completed.connect(func(zone: Node, loot: Array):
		_on_companion_scavenge_completed(companion_id, zone, loot)
	)

	spawned_entities[companion_id] = entity
	companion_summoned.emit(companion_id, entity)

	# Automatically link symbiotic skill synergy to player
	wire_skill_synergy(companion_id)

	return entity


func dismiss_companion(companion_id: String) -> bool:
	"""Dismiss companion from 3D lab physical presence back to resting status."""
	if not spawned_entities.has(companion_id):
		return false

	var entity = spawned_entities[companion_id]
	if is_instance_valid(entity):
		entity.queue_free()

	spawned_entities.erase(companion_id)
	companion_dismissed.emit(companion_id)
	return true


func command_sniff(companion_id: String, target_apparatus: Node) -> bool:
	"""Command summoned companion to sniff apparatus for chemical composition & vapor leaks."""
	if not spawned_entities.has(companion_id) or not is_instance_valid(spawned_entities[companion_id]):
		if companions.has(companion_id):
			summon_companion(companion_id)
		else:
			return false

	var entity = spawned_entities[companion_id]
	if entity.has_method("command_sniff"):
		entity.command_sniff(target_apparatus)
		return true
	return false


func command_scavenge(companion_id: String, target_zone: Node) -> bool:
	"""Command summoned companion to dart into hazardous containment and scavenge dropped reagents."""
	if not spawned_entities.has(companion_id) or not is_instance_valid(spawned_entities[companion_id]):
		if companions.has(companion_id):
			summon_companion(companion_id)
		else:
			return false

	var entity = spawned_entities[companion_id]
	if entity.has_method("command_scavenge"):
		entity.command_scavenge(target_zone)
		return true
	return false


func _get_autoload_node(node_name: String) -> Node:
	if is_inside_tree() and get_tree() and get_tree().root:
		return get_tree().root.get_node_or_null(node_name)
	elif Engine.has_singleton(node_name):
		return Engine.get_singleton(node_name)
	return null


func _on_companion_sniff_completed(companion_id: String, apparatus: Node, diagnostic: Dictionary) -> void:
	var skill_mgr = _get_autoload_node("SkillManager")
	if skill_mgr and skill_mgr.has_method("add_xp"):
		skill_mgr.add_xp("forensics", 35, "Companion chemical diagnostic")
		skill_mgr.add_xp("lab_safety", 25, "Companion vapor leak verification")

	grant_companion_xp(companion_id, 40)
	modify_bond(companion_id, 0.03)
	companion_sniff_result.emit(companion_id, apparatus, diagnostic)


func _on_companion_scavenge_completed(companion_id: String, zone: Node, loot: Array) -> void:
	var skill_mgr = _get_autoload_node("SkillManager")
	if skill_mgr and skill_mgr.has_method("add_xp"):
		skill_mgr.add_xp("containment", 50, "Hazard zone scavenging")
		skill_mgr.add_xp("lab_safety", 30, "Zero-exposure sample retrieval")

	var inv = _get_autoload_node("InventoryManager")
	if inv and inv.has_method("add_item"):
		for item in loot:
			inv.add_item(item.get("item_id", "sample_vial"), item.get("quantity", 1))

	grant_companion_xp(companion_id, 60)
	modify_bond(companion_id, 0.05)
	companion_scavenge_result.emit(companion_id, zone, loot)


# =============================================================================
# SYMBIOTIC SKILL WIRING & MULTIPLIERS
# =============================================================================

func wire_skill_synergy(companion_id: String) -> Dictionary:
	"""Connect companion elemental traits directly to SkillManager multipliers and bonuses."""
	if not companions.has(companion_id):
		return {}

	var comp: CompanionInstance = companions[companion_id]
	var species_id = comp.species_id
	var skill_mgr = _get_autoload_node("SkillManager")

	var synergy = {
		"companion_id": companion_id,
		"species_id": species_id,
		"boosted_skills": {},
		"synergy_label": ""
	}

	match species_id:
		"cinderling":
			synergy["boosted_skills"] = {
				"chemistry": 1.25,
				"thermodynamics": 1.30
			}
			synergy["synergy_label"] = "Thermal Homeostasis: +25% Chemistry XP & Exotherm Suppression"
		"wall_gecko":
			synergy["boosted_skills"] = {
				"lab_safety": 1.35,
				"containment": 1.30
			}
			synergy["synergy_label"] = "Aerosol Adhesion: +35% Lab Safety XP & Particulate Filtering"
		"lab_rat", "instrumented_rat":
			synergy["boosted_skills"] = {
				"toxicology": 1.30,
				"forensics": 1.25
			}
			synergy["synergy_label"] = "Neural Biomarker Sniffing: +30% Toxicology & Purity Detection"
		"brinejack":
			synergy["boosted_skills"] = {
				"physics": 1.20,
				"materials_science": 1.25
			}
			synergy["synergy_label"] = "Crystalline Resonance: +25% Materials Science XP & Salinity Balance"
		_:
			synergy["boosted_skills"] = {
				"chemistry": 1.10
			}
			synergy["synergy_label"] = "Aetheric Resonance: +10% Chemistry XP"

	if skill_mgr and skill_mgr.has_method("set_xp_multiplier"):
		for skill_track in synergy["boosted_skills"].keys():
			var mult = float(synergy["boosted_skills"][skill_track])
			skill_mgr.set_xp_multiplier(skill_track, mult)

	skill_synergy_applied.emit(companion_id, synergy)
	return synergy


func sync_all_skill_synergies() -> void:
	for comp_id in active_companions:
		wire_skill_synergy(comp_id)


# =============================================================================
# SERIALIZATION & PERSISTENCE
# =============================================================================

func _serialize_companion_instance(comp: CompanionInstance) -> Dictionary:
	return {
		"companion_id": comp.companion_id,
		"species_id": comp.species_id,
		"name": comp.name,
		"level": comp.level,
		"xp": comp.xp,
		"bond": comp.bond,
		"evolution_stage": comp.evolution_stage,
		"loyalty": comp.loyalty,
		"hunger": comp.hunger,
		"energy": comp.energy,
		"active": comp.active,
		"position": [comp.position.x, comp.position.y, comp.position.z],
		"known_abilities": comp.known_abilities.duplicate(),
		"stats": comp.stats.duplicate(true)
	}


func _deserialize_companion_instance(data: Dictionary) -> CompanionInstance:
	var comp = CompanionInstance.new()
	comp.companion_id = data.get("companion_id", "")
	comp.species_id = data.get("species_id", "")
	comp.name = data.get("name", "")
	comp.level = int(data.get("level", 1))
	comp.xp = int(data.get("xp", 0))
	comp.bond = float(data.get("bond", 0.1))
	comp.evolution_stage = int(data.get("evolution_stage", 0))
	comp.loyalty = float(data.get("loyalty", 0.5))
	comp.hunger = float(data.get("hunger", 0.0))
	comp.energy = float(data.get("energy", 1.0))
	comp.active = bool(data.get("active", false))
	var pos = data.get("position", [0, 0, 0])
	if pos is Array and pos.size() >= 3:
		comp.position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	var abilities = data.get("known_abilities", [])
	if abilities is Array:
		for a in abilities:
			comp.known_abilities.append(str(a))
	comp.stats = data.get("stats", {}).duplicate(true)
	return comp


func _save_companions() -> void:
	var save_manager = _get_autoload_node("SaveManager")
	if save_manager and save_manager.has_method("set_companion_data"):
		save_manager.set_companion_data(to_dict())


func to_dict() -> Dictionary:
	var comps_serialized = {}
	for cid in companions.keys():
		var c = companions[cid]
		if c is CompanionInstance:
			comps_serialized[cid] = _serialize_companion_instance(c)
		elif c is Dictionary:
			comps_serialized[cid] = c

	return {
		"companions": comps_serialized,
		"active_companions": active_companions.duplicate(),
		"max_active_walking": max_active_walking,
		"max_total_companions": max_total_companions,
		"next_companion_id": next_companion_id
	}


func from_dict(data: Dictionary) -> void:
	companions.clear()
	var raw_comps = data.get("companions", {})
	if raw_comps is Dictionary:
		for cid in raw_comps.keys():
			var val = raw_comps[cid]
			if val is Dictionary:
				companions[cid] = _deserialize_companion_instance(val)
			elif val is CompanionInstance:
				companions[cid] = val

	active_companions.clear()
	var raw_active = data.get("active_companions", [])
	if raw_active is Array:
		for a in raw_active:
			active_companions.append(str(a))

	max_active_walking = data.get("max_active_walking", 2)
	max_total_companions = data.get("max_total_companions", 3)
	next_companion_id = data.get("next_companion_id", 1)
	_emit_active_changed()
	sync_all_skill_synergies()