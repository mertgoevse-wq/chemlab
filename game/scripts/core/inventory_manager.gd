# Athanor Ascension - Inventory System (Athanor-style)
# Autoload: InventoryManager
# Handles: Equipment slots, quick wheel, crafting, visual appearance

extends Node

signal item_added(item_id: String, quantity: int)
signal item_removed(item_id: String, quantity: int)
signal equipment_changed(slot_id: String, item_id: String)
signal quick_slot_changed(slot_index: int, item_id: String)
signal radial_wheel_opened()
signal radial_wheel_closed()

const EQUIPMENT_DATA = preload("res://data/equipment/equipment_database.json")

func _get_data() -> Dictionary:
	if EQUIPMENT_DATA and EQUIPMENT_DATA.data is Dictionary:
		return EQUIPMENT_DATA.data
	return {}

var _equipment_slots_map: Dictionary = {}

# Equipment slots (Athanor-style)
var equipment: Dictionary = {}  # slot_id -> item_id or null
var quick_slots: Array[String] = []  # 8 quick slots
var inventory: Dictionary = {}  # item_id -> quantity (general inventory)

# Radial wheel state
var radial_wheel_active: bool = false
var radial_wheel_category: String = "tools"  # tools, consumables, companions, equipment

func _ready() -> void:
	_initialize_slots()
	_load_save_data()
	_connect_to_skill_mastery()

func _connect_to_skill_mastery() -> void:
	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr:
		if skill_mgr.has_signal("skill_mastered"):
			skill_mgr.skill_mastered.connect(_on_skill_mastered)
		if skill_mgr.has_signal("all_skills_mastered"):
			skill_mgr.all_skills_mastered.connect(_on_all_skills_mastered)

func _on_skill_mastered(skill_id: String, _level: int) -> void:
	var regalia_id = "regalia_" + skill_id
	if not has_item(regalia_id):
		add_item(regalia_id, 1)

func _on_all_skills_mastered() -> void:
	if not has_item("regalia_omniscient_alchemist"):
		add_item("regalia_omniscient_alchemist", 1)
	if not has_item("hood_omniscient_alchemist"):
		add_item("hood_omniscient_alchemist", 1)

func _initialize_slots() -> void:
	# Initialize equipment slots
	var data = _get_data()
	var slots = data.get("equipment_slots", [])
	for slot in slots:
		var s_id = slot.get("id", "")
		if s_id != "":
			equipment[s_id] = null
			_equipment_slots_map[s_id] = slot

	# Initialize quick slots (8 slots)
	quick_slots.resize(8)
	for i in range(8):
		quick_slots[i] = ""

	# Load equipment definitions
	_load_equipment_definitions()

func _load_equipment_definitions() -> void:
	pass  # Equipment data loaded from JSON when needed

func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_inventory_data"):
		var data = save_manager.get_inventory_data()
		if data:
			equipment = data.equipment
			quick_slots = data.quick_slots
			inventory = data.inventory
			_emit_equipment_signals()

func _emit_equipment_signals() -> void:
	for slot_id in equipment:
		if equipment[slot_id] != "" and equipment[slot_id] != null:
			equipment_changed.emit(slot_id, equipment[slot_id])
	for i in range(quick_slots.size()):
		if quick_slots[i] != "":
			quick_slot_changed.emit(i, quick_slots[i])

# =============================================================================
# PUBLIC API - EQUIPMENT
# =============================================================================

func equip_item(slot_id: String, item_id: String) -> bool:
	if not _equipment_slots_map.has(slot_id) and not equipment.has(slot_id):
		return false

	var item_def = _get_item_definition(item_id)
	if not item_def or item_def.is_empty():
		return false

	if item_def.get("slot", "") != slot_id:
		return false

	# Check level / mastery requirements
	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr:
		if item_def.get("all_skills_mastered", false):
			if not skill_mgr.is_all_skills_mastered():
				return false
		elif item_def.has("skill_requirement") and item_def.skill_requirement is Dictionary:
			var req_skill = item_def.skill_requirement.get("skill", "")
			var req_lvl = int(item_def.skill_requirement.get("level", 1))
			if skill_mgr.get_skill_level(req_skill) < req_lvl:
				return false

	# Unequip current item if any
	if equipment.has(slot_id) and equipment[slot_id] != "" and equipment[slot_id] != null:
		unequip_item(slot_id)

	equipment[slot_id] = item_id
	equipment_changed.emit(slot_id, item_id)
	_apply_equipment_stats(item_id, true)
	_save_inventory()
	return true

func unequip_item(slot_id: String) -> bool:
	if not equipment.has(slot_id) or equipment[slot_id] == "" or equipment[slot_id] == null:
		return false

	var item_id = equipment[slot_id]
	equipment[slot_id] = ""
	equipment_changed.emit(slot_id, "")
	_apply_equipment_stats(item_id, false)
	_save_inventory()
	return true

func get_equipped_item(slot_id: String) -> String:
	return equipment.get(slot_id, "")

func get_all_equipped() -> Dictionary:
	return equipment.duplicate(true)

func _apply_equipment_stats(item_id: String, equip: bool) -> void:
	var item_def = _get_item_definition(item_id)
	if not item_def or not item_def.has("stats"):
		return

	var multiplier = 1 if equip else -1
	var vitals = get_node_or_null("/root/PlayerVitals")
	var skill_manager = get_node_or_null("/root/SkillManager")

	for stat_name in item_def.stats:
		var value = item_def.stats[stat_name] * multiplier
		_apply_stat_modifier(stat_name, value, equip)

	# Apply set bonuses
	_check_set_bonuses()

func _apply_stat_modifier(stat_name: String, value: float, equip: bool) -> void:
	var vitals = get_node_or_null("/root/PlayerVitals")
	var skill_manager = get_node_or_null("/root/SkillManager")

	match stat_name:
		"protection_chemical", "protection_thermal", "protection_radiation", "protection_physical":
			if vitals:
				var current = vitals.get_protection_multiplier(stat_name)
				vitals.set_protection_multiplier(stat_name, current + value * 0.01)
		"mobility":
			if vitals:
				vitals.set_stamina_regen_multiplier(vitals.get_stamina_regen_multiplier() + value * 0.01)
		"ip_gain":
			if skill_manager:
				skill_manager.set_ip_multiplier(skill_manager.get_ip_multiplier() + value * 0.01)
		"xp_gain":
			if skill_manager:
				skill_manager.set_xp_multiplier(skill_manager.get_xp_multiplier() + value * 0.01)
		"yield_bonus":
			var sim = get_node_or_null("/root/SimulationBridge")
			if sim:
				sim.set_global_yield_modifier(sim.get_global_yield_modifier() + value * 0.01)
		"purity_bonus":
			var sim = get_node_or_null("/root/SimulationBridge")
			if sim:
				sim.set_global_purity_bonus(sim.get_global_purity_bonus() + value * 0.01)
		"speed_bonus":
			var sim = get_node_or_null("/root/SimulationBridge")
			if sim:
				sim.set_global_speed_modifier(sim.get_global_speed_modifier() + value * 0.01)
		"companion_bond":
			var comp = get_node_or_null("/root/CompanionManager")
			if comp:
				comp.set_bond_multiplier(comp.get_bond_multiplier() + value * 0.01)
		"night_vision":
			# Toggle post-process effect
			pass
		"hazard_sense":
			# Enable hazard detection UI
			pass
		"auto_neutralize":
			if vitals:
				vitals.set_auto_neutralize(equip)
		_:
			pass

func _check_set_bonuses() -> void:
	var equipped_items = []
	for slot_id in equipment:
		if equipment[slot_id] != "" and equipment[slot_id] != null:
			equipped_items.append(equipment[slot_id])

	var data = _get_data()
	for set_def in data.get("equipment_sets", []):
		var pieces_equipped = 0
		for piece_id in set_def.get("pieces", []):
			if piece_id in equipped_items:
				pieces_equipped += 1

		# Apply highest achieved bonus
		var bonuses = set_def.get("bonuses", {})
		for bonus_threshold in bonuses:
			var bonus = bonuses[bonus_threshold]
			if pieces_equipped >= int(bonus_threshold):
				_apply_set_bonus(bonus.get("stat", ""), float(bonus.get("value", 0.0)), true)
			else:
				_apply_set_bonus(bonus.get("stat", ""), float(bonus.get("value", 0.0)), false)

func _apply_set_bonus(stat: String, value: float, apply: bool) -> void:
	_apply_stat_modifier(stat, value, apply)

# =============================================================================
# PUBLIC API - QUICK SLOTS (RADIAL WHEEL)
# =============================================================================

func set_quick_slot(index: int, item_id: String) -> bool:
	if index < 0 or index >= 8:
		return false

	if item_id != "" and not _item_exists(item_id):
		return false

	quick_slots[index] = item_id
	quick_slot_changed.emit(index, item_id)
	_save_inventory()
	return true

func get_quick_slot(index: int) -> String:
	if index >= 0 and index < quick_slots.size():
		return quick_slots[index]
	return ""

func get_all_quick_slots() -> Array[String]:
	return quick_slots.duplicate()

func open_radial_wheel(category: String = "tools") -> void:
	radial_wheel_active = true
	radial_wheel_category = category
	radial_wheel_opened.emit()

func close_radial_wheel() -> void:
	radial_wheel_active = false
	radial_wheel_closed.emit()

func is_radial_wheel_active() -> bool:
	return radial_wheel_active

func get_radial_wheel_items(category: String) -> Array[Dictionary]:
	var items = []

	match category:
		"tools":
			for item_id in inventory:
				var def = _get_item_definition(item_id)
				if def and def.category in ["tool", "apparatus", "glassware"]:
					items.append({ "id": item_id, "name": def.name, "icon": def.icon, "quantity": inventory[item_id] })
		"consumables":
			for item_id in inventory:
				var def = _get_item_definition(item_id)
				if def and def.category in ["consumable", "reagent", "antidote", "injectable"]:
					items.append({ "id": item_id, "name": def.name, "icon": def.icon, "quantity": inventory[item_id] })
		"companions":
			var comp_manager = get_node_or_null("/root/CompanionManager")
			if comp_manager:
				items = comp_manager.get_active_companions()
		"equipment":
			for slot_id in equipment:
				var item_id = equipment[slot_id]
				if item_id != "" and item_id != null:
					var def = _get_item_definition(item_id)
					if def:
						items.append({ "id": item_id, "name": def.name, "icon": def.icon, "slot": slot_id })

	return items

# =============================================================================
# PUBLIC API - GENERAL INVENTORY
# =============================================================================

func add_item(item_id: String, quantity: int = 1) -> bool:
	if quantity <= 0:
		return false

	if not _item_exists(item_id):
		return false

	inventory[item_id] = inventory.get(item_id, 0) + quantity
	item_added.emit(item_id, quantity)
	_save_inventory()
	return true

func remove_item(item_id: String, quantity: int = 1) -> bool:
	if quantity <= 0:
		return false

	if not inventory.has(item_id) or inventory[item_id] < quantity:
		return false

	inventory[item_id] -= quantity
	if inventory[item_id] <= 0:
		inventory.erase(item_id)

	item_removed.emit(item_id, quantity)
	_save_inventory()
	return true

func get_item_quantity(item_id: String) -> int:
	return inventory.get(item_id, 0)

func has_item(item_id: String, quantity: int = 1) -> bool:
	return inventory.get(item_id, 0) >= quantity

func get_all_inventory() -> Dictionary:
	return inventory.duplicate(true)

func get_inventory_by_category(category: String) -> Dictionary:
	var result = {}
	for item_id in inventory:
		var def = _get_item_definition(item_id)
		if def and def.category == category:
			result[item_id] = inventory[item_id]
	return result

# =============================================================================
# CRAFTING
# =============================================================================

func can_craft(recipe_id: String) -> bool:
	# Check if player has required materials and skill level
	var recipe = _get_recipe(recipe_id)
	if not recipe:
		return false

	# Check skill requirements
	var skill_manager = get_node_or_null("/root/SkillManager")
	if skill_manager and recipe.has("skill_requirements"):
		for skill_id in recipe.skill_requirements:
			if skill_manager.get_skill_level(skill_id) < recipe.skill_requirements[skill_id]:
				return false

	# Check materials
	if recipe.has("materials"):
		for material in recipe.materials:
			if not has_item(material.item_id, material.quantity):
				return false

	# Check station access
	if recipe.has("station"):
		if not _has_station_access(recipe.station):
			return false

	return true

func craft_item(recipe_id: String, quantity: int = 1) -> bool:
	if not can_craft(recipe_id):
		return false

	var recipe = _get_recipe(recipe_id)

	# Consume materials
	if recipe.has("materials"):
		for material in recipe.materials:
			remove_item(material.item_id, material.quantity * quantity)

	# Produce result
	if recipe.has("result"):
		add_item(recipe.result.item_id, recipe.result.quantity * quantity)

	# Grant XP
	if recipe.has("xp_reward"):
		var skill_manager = get_node_or_null("/root/SkillManager")
		if skill_manager:
			for skill_id in recipe.xp_reward:
				skill_manager.grant_skill_xp(skill_id, recipe.xp_reward[skill_id] * quantity, "crafting")

	return true

func _has_station_access(station_id: String) -> bool:
	# Check if player has access to crafting station
	# This would check unlocked labs, built stations, etc.
	return true  # Simplified for now

# =============================================================================
# HELPERS
# =============================================================================

func _get_item_definition(item_id: String) -> Dictionary:
	# Search in equipment items
	for item in _get_data().get("equipment_items", []):
		if item.get("id", "") == item_id:
			return item

	# Fallback basic structure
	return {
		"id": item_id,
		"name": item_id,
		"category": "unknown",
		"icon": "",
		"slot": "",
		"stats": {}
	}

func _get_recipe(recipe_id: String) -> Dictionary:
	# Would load from crafting recipes database
	return {}

func _item_exists(item_id: String) -> bool:
	# Check if item exists in any database
	return true  # Simplified

func _save_inventory() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("set_inventory_data"):
		save_manager.set_inventory_data({
			"equipment": equipment,
			"quick_slots": quick_slots,
			"inventory": inventory
		})

func to_dict() -> Dictionary:
	return {
		"equipment": equipment,
		"quick_slots": quick_slots,
		"inventory": inventory
	}

func from_dict(data: Dictionary) -> void:
	equipment = data.get("equipment", equipment)
	quick_slots = data.get("quick_slots", quick_slots)
	inventory = data.get("inventory", inventory)
	_emit_equipment_signals()