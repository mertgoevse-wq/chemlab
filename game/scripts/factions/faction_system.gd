# Athanor Ascension - Faction Manager
# Autoload: FactionSystem
# Handles: 5 factions, reputation, vendors, dynamic world state, NPC attitudes

extends Node

signal reputation_changed(faction_id: String, old_rep: int, new_rep: int)
signal tier_changed(faction_id: String, old_tier: String, new_tier: String)
signal vendor_unlocked(faction_id: String, vendor_id: String)
signal world_state_changed()

const FACTION_DATA = preload("res://data/factions/faction_database.json")

func _get_data() -> Dictionary:
	if FACTION_DATA and FACTION_DATA.data is Dictionary:
		return FACTION_DATA.data
	return {}

func _get_factions() -> Dictionary:
	return _get_data().get("factions", {})

func _get_faction(faction_id: String) -> Dictionary:
	return _get_factions().get(faction_id, {})

func _get_reputation_system() -> Dictionary:
	return _get_data().get("reputation_system", {})

func _get_dynamic_world_state() -> Dictionary:
	return _get_data().get("dynamic_world_state", {})

var reputations: Dictionary = {}
var unlocked_vendors: Dictionary = {}  # faction_id -> Array[vendor_id]

func _ready() -> void:
	_initialize_reputations()
	_load_save_data()

func _initialize_reputations() -> void:
	var factions = _get_factions()
	for faction_id in factions:
		var faction = factions[faction_id]
		reputations[faction_id] = faction.get("starting_reputation", 0)
		unlocked_vendors[faction_id] = []

func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_faction_data"):
		var data = save_manager.get_faction_data()
		if data:
			reputations = data.reputations
			unlocked_vendors = data.unlocked_vendors
			_emit_all_signals()

func _emit_all_signals() -> void:
	for faction_id in reputations:
		var old_tier = _get_tier_at_rep(faction_id, 0)
		var new_tier = _get_tier_at_rep(faction_id, reputations[faction_id])
		if old_tier != new_tier:
			tier_changed.emit(faction_id, old_tier, new_tier)

# =============================================================================
# PUBLIC API - REPUTATION
# =============================================================================

func get_reputation(faction_id: String) -> int:
	return reputations.get(faction_id, -100)

func modify_reputation(faction_id: String, amount: int, source: String = "") -> void:
	if not reputations.has(faction_id):
		return

	var old_rep = reputations[faction_id]
	var new_rep = clamp(old_rep + amount, -100, 100)
	reputations[faction_id] = new_rep

	reputation_changed.emit(faction_id, old_rep, new_rep)

	# Check tier change
	var old_tier = _get_tier_at_rep(faction_id, old_rep)
	var new_tier = _get_tier_at_rep(faction_id, new_rep)
	if old_tier != new_tier:
		tier_changed.emit(faction_id, old_tier, new_tier)
		_check_vendor_unlocks(faction_id)
		_update_npc_attitudes(faction_id)

	# Cross-faction effects
	_apply_cross_faction_effects(faction_id, amount)

	_save_factions()
	print("Rep %s: %d -> %d (%s)" % [faction_id, old_rep, new_rep, source])

func _get_tier_at_rep(faction_id: String, rep: int) -> String:
	var faction = _get_faction(faction_id)
	for tier in faction.get("reputation_tiers", []):
		if rep >= tier.get("min", -100) and rep <= tier.get("max", 100):
			return tier.get("title", "Unknown")
	return "Unknown"

func get_current_tier(faction_id: String) -> String:
	return _get_tier_at_rep(faction_id, reputations.get(faction_id, 0))

func get_tier_info(faction_id: String, tier_title: String) -> Dictionary:
	var faction = _get_faction(faction_id)
	for tier in faction.get("reputation_tiers", []):
		if tier.get("title", "") == tier_title:
			return tier
	return {}

# =============================================================================
# CROSS-FACTION EFFECTS
# =============================================================================

func _apply_cross_faction_effects(source_faction: String, amount: int) -> void:
	var cross_effects = _get_reputation_system().get("cross_faction_effects", {})
	if not cross_effects.has(source_faction):
		return

	var effects = cross_effects[source_faction]
	for target_faction in effects:
		if reputations.has(target_faction):
			var cross_amount = int(amount * effects[target_faction])
			if cross_amount != 0:
				var old = reputations[target_faction]
				reputations[target_faction] = clamp(old + cross_amount, -100, 100)
				if old != reputations[target_faction]:
					reputation_changed.emit(target_faction, old, reputations[target_faction])
					var old_tier = _get_tier_at_rep(target_faction, old)
					var new_tier = _get_tier_at_rep(target_faction, reputations[target_faction])
					if old_tier != new_tier:
						tier_changed.emit(target_faction, old_tier, new_tier)
						_check_vendor_unlocks(target_faction)
						_update_npc_attitudes(target_faction)

# =============================================================================
# VENDORS
# =============================================================================

func _check_vendor_unlocks(faction_id: String) -> void:
	var faction = _get_faction(faction_id)
	var current_rep = reputations[faction_id]
	var vendors = faction.get("vendors", {})

	for vendor_id in vendors:
		var vendor = vendors[vendor_id]
		var unlock_tier = vendor.get("discount_at_tier", "")
		var unlock_rep = _get_min_rep_for_tier(faction_id, unlock_tier)

		if current_rep >= unlock_rep and vendor_id not in unlocked_vendors[faction_id]:
			unlocked_vendors[faction_id].append(vendor_id)
			vendor_unlocked.emit(faction_id, vendor_id)
			print("Vendor unlocked: %s (%s)" % [vendor_id, faction_id])

func _get_min_rep_for_tier(faction_id: String, tier_title: String) -> int:
	var faction = _get_faction(faction_id)
	for tier in faction.get("reputation_tiers", []):
		if tier.get("title", "") == tier_title:
			return tier.get("min", 100)
	return 100

func get_unlocked_vendors(faction_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if not unlocked_vendors.has(faction_id):
		return result

	var faction = _get_faction(faction_id)
	var vendors = faction.get("vendors", {})
	for vendor_id in unlocked_vendors[faction_id]:
		if vendors.has(vendor_id):
			var vendor = vendors[vendor_id].duplicate()
			vendor["id"] = vendor_id
			vendor["faction"] = faction_id
			result.append(vendor)
	return result

func get_vendor_items(faction_id: String, vendor_id: String) -> Array:
	var faction = _get_faction(faction_id)
	var vendors = faction.get("vendors", {})
	if vendors.has(vendor_id):
		return vendors[vendor_id].get("items", []).duplicate()
	return []

func purchase_from_vendor(faction_id: String, vendor_id: String, item_id: String, quantity: int = 1) -> bool:
	if vendor_id not in unlocked_vendors.get(faction_id, []):
		return false

	var faction = _get_faction(faction_id)
	var vendors = faction.get("vendors", {})
	if not vendors.has(vendor_id):
		return false

	var vendor = vendors[vendor_id]
	var items = vendor.get("items", [])
	if item_id not in items:
		return false

	# Check discount
	var discount = 0.0
	for tier in faction.get("reputation_tiers", []):
		if reputations[faction_id] >= tier.get("min", 0) and tier.get("title", "") == vendor.get("discount_at_tier", ""):
			discount = 0.15  # 15% discount at unlock tier
			break

	# Would process payment, add to inventory
	var inv_manager = get_node_or_null("/root/InventoryManager")
	if inv_manager:
		return inv_manager.add_item(item_id, quantity)
	return false

# =============================================================================
# DYNAMIC WORLD STATE
# =============================================================================

func get_lab_control(lab_id: String) -> Dictionary:
	# Determine which faction controls a lab based on reputation and events
	var lab_control_state = _get_dynamic_world_state().get("lab_control", {})
	var labs = lab_control_state.get("labs", [])
	if lab_id not in labs:
		return { "control": "neutral", "faction": null }

	# Simplified: highest reputation faction gets control
	var max_rep = -101
	var controlling_faction = null
	for faction_id in reputations:
		if reputations[faction_id] > max_rep:
			max_rep = reputations[faction_id]
			controlling_faction = faction_id

	var contested = false
	var second_max = -101
	for faction_id in reputations:
		if faction_id != controlling_faction and reputations[faction_id] > second_max:
			second_max = reputations[faction_id]
			if max_rep - second_max < 20:
				contested = true

	if contested:
		return { "control": "contested", "faction": controlling_faction }
	else:
		return { "control": "controlled", "faction": controlling_faction }

func get_market_price_multiplier(reagent_id: String) -> float:
	# Prices affected by faction control of producing labs
	var base_price = 1.0
	# Would check which faction controls precursor labs
	return base_price

func get_npc_attitude(faction_id: String) -> String:
	var rep = reputations.get(faction_id, 0)
	var npc_attitudes = _get_dynamic_world_state().get("npc_attitudes", {})
	var thresholds = npc_attitudes.get("thresholds", {})

	if rep <= thresholds.get("hostile", -50):
		return "hostile"
	elif rep <= thresholds.get("unfriendly", -10):
		return "unfriendly"
	elif rep <= thresholds.get("neutral", 10):
		return "neutral"
	elif rep <= thresholds.get("friendly", 50):
		return "friendly"
	else:
		return "reverent"

func _update_npc_attitudes(faction_id: String) -> void:
	# NPCs would update their dialogue/behavior
	world_state_changed.emit()

# =============================================================================
# FACTION MISSIONS
# =============================================================================

func get_available_faction_missions(faction_id: String) -> Array[Dictionary]:
	var missions = []
	# Would load from faction mission database
	return missions

func start_faction_mission(faction_id: String, mission_id: String) -> bool:
	# Would start a faction-specific quest
	var quest_manager = get_node_or_null("/root/QuestManager")
	if quest_manager:
		return quest_manager.start_faction_mission(faction_id, mission_id)
	return false

# =============================================================================
# SAVE/LOAD
# =============================================================================

func _save_factions() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("set_faction_data"):
		save_manager.set_faction_data({
			"reputations": reputations,
			"unlocked_vendors": unlocked_vendors
		})

func to_dict() -> Dictionary:
	return {
		"reputations": reputations,
		"unlocked_vendors": unlocked_vendors
	}

func from_dict(data: Dictionary) -> void:
	reputations = data.get("reputations", reputations)
	unlocked_vendors = data.get("unlocked_vendors", unlocked_vendors)
	_emit_all_signals()