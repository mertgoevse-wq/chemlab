# Athanor Ascension — Skill Progression Manager
# Autoload: SkillManager
#
# Reads the authoritative GDD data (res://data/progression/skills.json) instead of
# hardcoding tracks. Chemistry, Biology, Forensics and Engineering each carry six
# milestones with apparatus, reagent and ability unlocks. XP uses the documented
# RuneScape-style curve, built once at load.
extends Node

signal xp_gained(skill_id: String, amount: int, total_xp: int, level: int, reason: String)
signal level_up(skill_id: String, old_level: int, new_level: int)
signal milestone_unlocked(skill_id: String, milestone: Dictionary)

const DATA_PATH: String = "res://data/progression/skills.json"
const SAVE_KEY: String = "skills"
const TRACK_ORDER := ["chemistry", "biology", "forensics", "engineering"]
const RANK_FLOORS := [1, 10, 20, 30, 40, 55, 70, 85, 95, 100]

var _tracks: Dictionary = {}
var _rank_titles: Array = []
var _thresholds: Array[int] = []
var _max_level: int = 120
var _xp: Dictionary = {}
var _loaded: bool = false


func _ready() -> void:
	_load_tracks()
	_load_progress()


# =============================================================================
# DATA LOADING
# =============================================================================

func _load_tracks() -> void:
	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("SkillManager: cannot open %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("SkillManager: invalid skills.json")
		return
	var doc: Dictionary = parsed
	var skills: Dictionary = doc.get("skills", {})
	_rank_titles = doc.get("rank_titles", [])
	var curve: Dictionary = doc.get("xp_curve", {})
	_max_level = int(curve.get("max_level", 120))
	_tracks.clear()
	for skill_id in skills.keys():
		var track: Dictionary = skills[skill_id]
		var milestones: Array = track.get("milestones", [])
		milestones.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
			return int(a.get("level", 1)) < int(b.get("level", 1)))
		track["milestones"] = milestones
		_tracks[str(skill_id)] = track
		_xp[str(skill_id)] = int(_xp.get(str(skill_id), 0))
	_build_curve()
	_loaded = true


func _build_curve() -> void:
	# Classic 120-level curve: accumulate the unrounded level terms, divide by 4
	# once, then floor. This reproduces the GDD sample table exactly (83 / 388 /
	# 1154 / 101,333 / 13,034,431) rather than drifting a few XP per level.
	_thresholds.clear()
	_thresholds.append(0)
	var raw: float = 0.0
	for level in range(1, _max_level):
		raw += floor(float(level) + 300.0 * pow(2.0, float(level) / 7.0))
		_thresholds.append(int(floor(raw / 4.0)))


func _load_progress() -> void:
	var save_manager := get_node_or_null("/root/SaveManager")
	if save_manager == null:
		return
	var data: Dictionary = save_manager.get("save_data")
	var stored: Dictionary = data.get(SAVE_KEY, {})
	var values: Dictionary = stored.get("xp", {})
	for skill_id in values.keys():
		if _tracks.has(str(skill_id)):
			_xp[str(skill_id)] = maxi(0, int(values[skill_id]))


func _persist() -> void:
	if not is_inside_tree():
		return
	var save_manager := get_node_or_null("/root/SaveManager")
	if save_manager == null:
		return
	var data: Dictionary = save_manager.get("save_data")
	data[SAVE_KEY] = {"version": 1, "xp": _xp.duplicate()}
	save_manager.save_game()


# =============================================================================
# CURVE & QUERIES
# =============================================================================

func xp_to_reach_level(level: int) -> int:
	if _thresholds.is_empty():
		return 0
	var clamped := clampi(level, 1, _max_level)
	return _thresholds[clamped - 1]


func level_for_xp(xp: int) -> int:
	if _thresholds.is_empty():
		return 1
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


func get_xp(skill_id: String) -> int:
	return int(_xp.get(skill_id, 0))


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


# =============================================================================
# AWARDS
# =============================================================================

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
		push_warning("SkillManager: unknown skill '%s'" % skill_id)
		return result
	var gain := maxi(0, amount)
	if gain == 0:
		result["level_before"] = get_level(skill_id)
		result["level_after"] = result["level_before"]
		result["ok"] = true
		return result

	var before := get_level(skill_id)
	_xp[skill_id] = int(_xp.get(skill_id, 0)) + gain
	var after := get_level(skill_id)

	result["ok"] = true
	result["amount"] = gain
	result["level_before"] = before
	result["level_after"] = after
	result["levels_gained"] = maxi(0, after - before)

	if after > before:
		level_up.emit(skill_id, before, after)
	for milestone in get_milestones(skill_id):
		var milestone_level := int(milestone.get("level", 1))
		if milestone_level > before and milestone_level <= after:
			(result["milestones"] as Array).append(milestone)
			milestone_unlocked.emit(skill_id, milestone)

	xp_gained.emit(skill_id, gain, get_xp(skill_id), after, reason)
	_persist()
	return result


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
	for id_value in ids:
		var track_id := str(id_value)
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
