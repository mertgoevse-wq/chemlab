# Athanor Ascension - Progressive Skill System
# Autoload: SkillManager
# Handles: 15 skill tracks, 120 levels, exponential XP curves, Intelligence Points, Talent Trees, Milestones

extends Node

# Legacy signals for backwards-compatibility with tests and UI
signal xp_gained(skill_id: String, amount: int, total_xp: int, level: int, reason: String)
signal level_up(skill_id: String, old_level: int, new_level: int)
signal milestone_unlocked(skill_id: String, milestone: Dictionary)

# Modern signals
signal skill_xp_gained(skill_id: String, amount: int, new_total: int)
signal skill_leveled_up(skill_id: String, new_level: int)
signal intelligence_points_changed(amount: int, new_total: int)
signal talent_unlocked(talent_id: String)
signal milestone_reached(skill_id: String, milestone_level: int)
signal skill_mastered(skill_id: String, level: int)
signal all_skills_mastered()

const DATA_PATH: String = "res://data/progression/skills.json"
const SAVE_KEY: String = "skills"
const TRACK_ORDER: Array[String] = [
	"chemistry", "biology", "physics", "mathematics",
	"forensics", "toxicology", "apparatus_building", "lab_safety",
	"automation", "containment", "nuclear_engineering", "genetics",
	"biochemistry", "pharmacology", "synthetic_biology", "radiochemistry",
	"environmental_science", "materials_science", "computational_chemistry", "engineering"
]
const RANK_FLOORS: Array[int] = [1, 10, 20, 30, 40, 55, 70, 85, 95, 100]
const MASTERY_LEVEL: int = 99
const MAX_SKILL_LEVEL: int = 99

var _tracks: Dictionary = {}
var _rank_titles: Array = []
var _thresholds: Array[int] = []
var _max_level: int = 120
var _xp: Dictionary = {}
var _raw_data: Dictionary = {}

# Public properties for autoload consumer compatibility
var xp_table: Array[int] = []
var skills: Dictionary = {} # skill_id -> {level, xp, virtual_level, definition}
var xp_multipliers: Dictionary = {}
var intelligence_points: int = 0
var unlocked_talents: Array[String] = []
var reached_milestones: Dictionary = {} # skill_id -> Array[int]


func _init() -> void:
	_load_tracks()
	_build_curve()
	_initialize_skills()


func _ready() -> void:
	if _tracks.is_empty():
		_load_tracks()
	if _thresholds.is_empty():
		_build_curve()
	_initialize_skills()
	_load_save_data()


# =============================================================================
# DATA LOADING & INITIALIZATION
# =============================================================================

func _load_tracks() -> void:
	_tracks.clear()
	_rank_titles.clear()

	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	if file != null:
		var parsed: Variant = JSON.parse_string(file.get_as_text())
		file.close()
		if typeof(parsed) == TYPE_DICTIONARY:
			_raw_data = parsed

	if _raw_data.has("rank_titles") and typeof(_raw_data["rank_titles"]) == TYPE_ARRAY:
		_rank_titles = _raw_data["rank_titles"].duplicate()
	else:
		_rank_titles = [
			"Trainee (Labor-Praktikant)",
			"Apprentice (Chemielaborant-Lehrling)",
			"Journeyman (Technischer Assistent)",
			"Expert (Analytiker)",
			"Specialist (Synthese-Spezialist)",
			"Master (Laborleiter)",
			"Grandmaster (Meister-Alchemist)",
			"Archmage (Forschungsdirektor)",
			"Legend (Kavli-Helmholtz Fellow)",
			"Transcendent (Athanor Architect)"
		]

	var curve: Dictionary = _raw_data.get("xp_formula", _raw_data.get("xp_curve", {}))
	_max_level = int(curve.get("max_level", 120))

	var raw_skills = _raw_data.get("skills", [])
	if typeof(raw_skills) == TYPE_ARRAY:
		for s_def in raw_skills:
			if typeof(s_def) == TYPE_DICTIONARY:
				var sid := str(s_def.get("id", ""))
				if sid != "":
					_tracks[sid] = _normalize_track(sid, s_def)
					_xp[sid] = int(_xp.get(sid, 0))
	elif typeof(raw_skills) == TYPE_DICTIONARY:
		for sid in raw_skills.keys():
			var s_def = raw_skills[sid]
			if typeof(s_def) == TYPE_DICTIONARY:
				_tracks[str(sid)] = _normalize_track(str(sid), s_def)
				_xp[str(sid)] = int(_xp.get(str(sid), 0))

	# Ensure engineering alias exists for apparatus building if requested
	if not _tracks.has("engineering") and _tracks.has("apparatus_building"):
		_tracks["engineering"] = _tracks["apparatus_building"]


func _normalize_track(sid: String, def: Dictionary) -> Dictionary:
	var track := def.duplicate(true)
	track["id"] = sid
	if not track.has("display_name"):
		track["display_name"] = str(def.get("name", sid.capitalize()))
	if not track.has("color_hex"):
		track["color_hex"] = "#25d9eb"

	var raw_milestones = def.get("milestones")
	var norm_ms: Array = []

	if typeof(raw_milestones) == TYPE_ARRAY:
		for m in raw_milestones:
			if typeof(m) == TYPE_DICTIONARY:
				var nm := (m as Dictionary).duplicate(true)
				if not nm.has("level"):
					nm["level"] = 1
				if not nm.has("unlocked_apparatus"):
					nm["unlocked_apparatus"] = []
				if not nm.has("unlocked_reagents"):
					nm["unlocked_reagents"] = []
				if not nm.has("unlocked_abilities"):
					nm["unlocked_abilities"] = []
				norm_ms.append(nm)
	elif typeof(raw_milestones) == TYPE_DICTIONARY:
		var dict_ms: Dictionary = raw_milestones
		var levels: Array = []
		for k in dict_ms.keys():
			levels.append(int(k))
		levels.sort()
		for lvl in levels:
			var val = dict_ms[str(lvl)]
			var title := "Level %d Mastery" % lvl
			var desc := ""
			if typeof(val) == TYPE_STRING:
				desc = val
			elif typeof(val) == TYPE_DICTIONARY:
				title = str(val.get("title", title))
				desc = str(val.get("description", ""))

			var app_unlocks: Array = []
			var reag_unlocks: Array = []
			var abil_unlocks: Array = [desc]
			if def.has("unlocks") and typeof(def["unlocks"]) == TYPE_DICTIONARY:
				var unl: Dictionary = def["unlocks"]
				if lvl <= 10:
					app_unlocks = unl.get("equipment", []).duplicate()
					reag_unlocks = unl.get("reagents", []).duplicate()
				elif lvl <= 50:
					app_unlocks = unl.get("equipment", []).duplicate()

			norm_ms.append({
				"level": lvl,
				"title": title,
				"description": desc,
				"unlocked_apparatus": app_unlocks,
				"unlocked_reagents": reag_unlocks,
				"unlocked_abilities": abil_unlocks
			})

	norm_ms.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return int(a.get("level", 1)) < int(b.get("level", 1)))
	track["milestones"] = norm_ms
	return track


func _build_curve() -> void:
	_thresholds.clear()
	_thresholds.append(0)
	var raw: float = 0.0
	for level in range(1, _max_level):
		raw += floor(float(level) + 300.0 * pow(2.0, float(level) / 7.0))
		_thresholds.append(int(floor(raw / 4.0)))
	xp_table = _thresholds.duplicate()


func _initialize_skills() -> void:
	skills.clear()
	for skill_id in _tracks.keys():
		var lvl := get_level(skill_id)
		var xp := get_xp(skill_id)
		skills[skill_id] = {
			"level": lvl,
			"xp": xp,
			"virtual_level": lvl,
			"definition": _tracks[skill_id]
		}


# =============================================================================
# CURVE & LEVEL QUERIES
# =============================================================================

func xp_to_reach_level(level: int) -> int:
	if _thresholds.is_empty():
		_build_curve()
	var clamped := clampi(level, 1, _max_level)
	return _thresholds[clamped - 1]


func get_xp_for_level(level: int) -> int:
	return xp_to_reach_level(level)


func level_for_xp(xp: int) -> int:
	if _thresholds.is_empty():
		_build_curve()
	var lo: int = 0
	var hi: int = _thresholds.size() - 1
	while lo < hi:
		var mid: int = int((lo + hi + 1) / 2)
		if _thresholds[mid] <= xp:
			lo = mid
		else:
			hi = mid - 1
	return lo + 1


func get_level(skill_id: String) -> int:
	return level_for_xp(int(_xp.get(skill_id, 0)))


func get_skill_level(skill_id: String) -> int:
	return get_level(skill_id)


func get_xp(skill_id: String) -> int:
	return int(_xp.get(skill_id, 0))


func get_skill_xp(skill_id: String) -> int:
	return get_xp(skill_id)


func get_tracks() -> Dictionary:
	return _tracks


func get_track(skill_id: String) -> Dictionary:
	return _tracks.get(skill_id, {})


func has_track(skill_id: String) -> bool:
	return _tracks.has(skill_id)


func get_max_level() -> int:
	return _max_level


func get_rank_title(level: int) -> String:
	if _rank_titles.is_empty():
		return "Trainee"
	var index: int = 0
	for i in range(RANK_FLOORS.size()):
		if level >= int(RANK_FLOORS[i]):
			index = i
	return str(_rank_titles[clampi(index, 0, _rank_titles.size() - 1)])


func get_progress(skill_id: String) -> float:
	var xp := get_xp(skill_id)
	var level := get_level(skill_id)
	if level >= _max_level:
		return 1.0
	var current := xp_to_reach_level(level)
	var next := xp_to_reach_level(level + 1)
	if next <= current:
		return 1.0
	return clampf(float(xp - current) / float(next - current), 0.0, 1.0)


func get_skill_progress(skill_id: String) -> float:
	return get_progress(skill_id)


func get_level_span(skill_id: String) -> Dictionary:
	var level := get_level(skill_id)
	var xp := get_xp(skill_id)
	var floor_xp := xp_to_reach_level(level)
	if level >= _max_level:
		return {"into": xp - floor_xp, "span": 0, "level": level}
	return {
		"into": xp - floor_xp,
		"span": xp_to_reach_level(level + 1) - floor_xp,
		"level": level
	}


func get_milestones(skill_id: String) -> Array:
	return get_track(skill_id).get("milestones", [])


func get_next_milestone(skill_id: String) -> Dictionary:
	var level := get_level(skill_id)
	for milestone in get_milestones(skill_id):
		if int(milestone.get("level", 1)) > level:
			return milestone
	return {}


func is_milestone_unlocked(skill_id: String, milestone: Dictionary) -> bool:
	return get_level(skill_id) >= int(milestone.get("level", 1))


func get_unlocked_apparatus(skill_id: String = "") -> Array[String]:
	return _collect_unlocks(skill_id, "unlocked_apparatus")


func get_unlocked_reagents(skill_id: String = "") -> Array[String]:
	return _collect_unlocks(skill_id, "unlocked_reagents")


func get_unlocked_abilities(skill_id: String = "") -> Array[String]:
	return _collect_unlocks(skill_id, "unlocked_abilities")


func _collect_unlocks(skill_id: String, key: String) -> Array[String]:
	var out: Array[String] = []
	var level := get_level(skill_id)
	var ids: Array = TRACK_ORDER if skill_id == "" else [skill_id]
	for id_val in ids:
		var track_id := str(id_val)
		if not _tracks.has(track_id):
			continue
		for milestone in get_milestones(track_id):
			if int(milestone.get("level", 1)) > level:
				continue
			for entry in milestone.get(key, []):
				var text := str(entry)
				if not out.has(text):
					out.append(text)
	return out


func get_skill_definition(skill_id: String) -> Dictionary:
	return _tracks.get(skill_id, {})


func get_all_skills() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for skill_id in _tracks.keys():
		var def = _tracks[skill_id]
		var lvl = get_level(skill_id)
		result.append({
			"id": skill_id,
			"name": def.get("name", def.get("display_name", skill_id.capitalize())),
			"category": def.get("category", "General"),
			"icon": def.get("icon", ""),
			"level": lvl,
			"xp": get_xp(skill_id),
			"progress": get_progress(skill_id),
			"virtual_level": lvl
		})
	return result


# =============================================================================
# XP GAIN & LEVELING
# =============================================================================

func set_xp_multiplier(skill_id: String, multiplier: float) -> void:
	xp_multipliers[skill_id] = multiplier


func get_xp_multiplier(skill_id: String) -> float:
	return xp_multipliers.get(skill_id, 1.0)


func add_xp(skill_id: String, amount: int, reason: String = "") -> Dictionary:
	var result := {
		"ok": false,
		"skill": skill_id,
		"amount": 0,
		"level_before": 1,
		"level_after": 1,
		"levels_gained": 0,
		"milestones": []
	}
	if not _tracks.has(skill_id):
		return result

	var gain := maxi(0, amount)
	var effective_gain := int(round(gain * get_xp_multiplier(skill_id)))
	var before := get_level(skill_id)

	if effective_gain == 0:
		result["level_before"] = before
		result["level_after"] = before
		result["ok"] = true
		return result

	_xp[skill_id] = int(_xp.get(skill_id, 0)) + effective_gain
	var after := get_level(skill_id)

	if skills.has(skill_id):
		skills[skill_id].level = after
		skills[skill_id].xp = _xp[skill_id]
		skills[skill_id].virtual_level = after

	result["ok"] = true
	result["amount"] = effective_gain
	result["level_before"] = before
	result["level_after"] = after
	result["levels_gained"] = maxi(0, after - before)

	if after > before:
		level_up.emit(skill_id, before, after)
		skill_leveled_up.emit(skill_id, after)
		if before < 99 and after >= 99:
			skill_mastered.emit(skill_id, after)
			if is_all_skills_mastered():
				all_skills_mastered.emit()

	var newly_unlocked_milestones: Array = []
	for milestone in get_milestones(skill_id):
		var ms_level := int(milestone.get("level", 1))
		if ms_level > before and ms_level <= after:
			newly_unlocked_milestones.append(milestone)
			if not reached_milestones.has(skill_id):
				reached_milestones[skill_id] = []
			if not ms_level in reached_milestones[skill_id]:
				reached_milestones[skill_id].append(ms_level)
			milestone_unlocked.emit(skill_id, milestone)
			milestone_reached.emit(skill_id, ms_level)

	result["milestones"] = newly_unlocked_milestones

	xp_gained.emit(skill_id, effective_gain, get_xp(skill_id), after, reason)
	skill_xp_gained.emit(skill_id, effective_gain, get_xp(skill_id))

	_save_skills()
	return result


func grant_skill_xp(skill_id: String, amount: int, source: String = "") -> void:
	add_xp(skill_id, amount, source)


func has_milestone(skill_id: String, milestone_level: int) -> bool:
	return milestone_level in reached_milestones.get(skill_id, [])


func is_all_skills_mastered() -> bool:
	for skill_id in TRACK_ORDER:
		if get_level(skill_id) < 99:
			return false
	return true


func get_mastered_skills() -> Array[String]:
	var result: Array[String] = []
	for skill_id in TRACK_ORDER:
		if get_level(skill_id) >= 99:
			result.append(skill_id)
	return result


# =============================================================================
# INTELLIGENCE POINTS & TALENT TREES
# =============================================================================

func get_intelligence_points() -> int:
	return intelligence_points


func grant_intelligence_points(amount: int, source: String = "") -> void:
	if amount <= 0:
		return
	intelligence_points += amount
	intelligence_points_changed.emit(amount, intelligence_points)
	_save_skills()


func spend_intelligence_points(amount: int, talent_id: String = "") -> bool:
	if intelligence_points < amount:
		return false
	intelligence_points -= amount
	if talent_id != "" and not talent_id in unlocked_talents:
		unlocked_talents.append(talent_id)
		talent_unlocked.emit(talent_id)
	intelligence_points_changed.emit(-amount, intelligence_points)
	_save_skills()
	return true


func has_talent(talent_id: String) -> bool:
	return talent_id in unlocked_talents


func unlock_talent(tree_id: String, tier_index: int) -> bool:
	var intel: Dictionary = _raw_data.get("intelligence_points", {})
	var talent_trees: Dictionary = intel.get("talent_trees", {})
	var talent_data: Dictionary = talent_trees.get(tree_id, {})
	if talent_data.is_empty():
		return false

	var tiers: Array = talent_data.get("tiers", [])
	if tier_index >= tiers.size():
		return false

	var tier: Dictionary = tiers[tier_index]
	for i in range(tier_index):
		var prereq_id := "%s_tier_%d" % [tree_id, i]
		if not has_talent(prereq_id):
			return false

	var talent_id := "%s_tier_%d" % [tree_id, tier_index]
	if has_talent(talent_id):
		return true

	var cost := int(tier.get("cost", 1))
	if spend_intelligence_points(cost, talent_id):
		_apply_talent_effect(tree_id, tier_index, str(tier.get("effect", "")))
		return true
	return false


func _apply_talent_effect(tree_id: String, tier_index: int, effect: String) -> void:
	match tree_id:
		"synthesis_mastery":
			var sim_bridge = get_node_or_null("/root/SimulationBridge")
			if sim_bridge:
				match tier_index:
					0: if sim_bridge.has_method("set_global_yield_modifier"): sim_bridge.set_global_yield_modifier(1.05)
					1: if sim_bridge.has_method("unlock_protecting_groups"): sim_bridge.unlock_protecting_groups()
					2:
						if sim_bridge.has_method("set_global_purity_bonus"): sim_bridge.set_global_purity_bonus(1.10)
						if sim_bridge.has_method("set_global_speed_bonus"): sim_bridge.set_global_speed_bonus(0.90)
					3: if sim_bridge.has_method("enable_retrosynthesis_ai"): sim_bridge.enable_retrosynthesis_ai()
					4: if sim_bridge.has_method("enable_one_click_synthesis"): sim_bridge.enable_one_click_synthesis()
		"safety_expertise":
			var vitals = get_node_or_null("/root/PlayerVitals")
			if vitals:
				match tier_index:
					0: if vitals.has_method("set_injury_severity_modifier"): vitals.set_injury_severity_modifier(0.8)
					1: if vitals.has_method("enable_auto_neutralization"): vitals.enable_auto_neutralization()
					2: if vitals.has_method("set_fume_hood_efficiency"): vitals.set_fume_hood_efficiency(1.25)
					3: if vitals.has_method("set_radiation_modifier"): vitals.set_radiation_modifier(0.5)
					4: if vitals.has_method("enable_chrysalis_warden"): vitals.enable_chrysalis_warden()
		"companion_bond":
			var comp_manager = get_node_or_null("/root/CompanionManager")
			if comp_manager:
				match tier_index:
					0: if comp_manager.has_method("set_max_slots"): comp_manager.set_max_slots(4)
					1: if comp_manager.has_method("set_xp_multiplier"): comp_manager.set_xp_multiplier(1.25)
					2: if comp_manager.has_method("unlock_mythic_evolution"): comp_manager.unlock_mythic_evolution()
					3: if comp_manager.has_method("enable_telepathic_link"): comp_manager.enable_telepathic_link()
					4: if comp_manager.has_method("unlock_ember_drake"): comp_manager.unlock_ember_drake()
		"social_influence":
			var faction_sys = get_node_or_null("/root/FactionSystem")
			if faction_sys:
				match tier_index:
					0: if faction_sys.has_method("set_rep_multiplier"): faction_sys.set_rep_multiplier(1.15)
					1: if faction_sys.has_method("unlock_faction_vendors"): faction_sys.unlock_faction_vendors()
					2: if faction_sys.has_method("enable_npc_relationships"): faction_sys.enable_npc_relationships()
					3: if faction_sys.has_method("enable_mediation"): faction_sys.enable_mediation()
					4: if faction_sys.has_method("enable_faction_founding"): faction_sys.enable_faction_founding()


# =============================================================================
# PERSISTENCE & SERIALIZATION
# =============================================================================

func _save_skills() -> void:
	if not is_inside_tree():
		return
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("set_skill_data"):
		save_manager.set_skill_data(to_dict())


func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_skill_data"):
		var data = save_manager.get_skill_data()
		if typeof(data) == TYPE_DICTIONARY and not data.is_empty():
			from_dict(data)


func to_dict() -> Dictionary:
	return {
		"xp": _xp.duplicate(),
		"intelligence_points": intelligence_points,
		"unlocked_talents": unlocked_talents.duplicate(),
		"reached_milestones": reached_milestones.duplicate()
	}


func from_dict(data: Dictionary) -> void:
	var loaded_xp: Dictionary = data.get("xp", {})
	for k in loaded_xp.keys():
		_xp[str(k)] = maxi(0, int(loaded_xp[k]))
	intelligence_points = int(data.get("intelligence_points", 0))
	unlocked_talents.assign(data.get("unlocked_talents", []))
	reached_milestones = data.get("reached_milestones", {}).duplicate()
	_initialize_skills()
