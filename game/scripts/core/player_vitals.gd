# Athanor Ascension — Player Vitals
# Autoload: PlayerVitals
#
# Health is intentionally separate from XP/skills: laboratory mistakes cost blood,
# lung capacity and radiation dose, not experience points. Radiation is tracked in
# millisieverts (ICRP-style operational quantities), chemical exposure in ppm·min.
#
# Units and thresholds are simplified for play but anchored to real occupational
# limits (OSHA PEL, ICRP dose limits) so the HUD numbers are not fantasy.

extends Node

signal health_changed(current: float, maximum: float)
signal injury_added(injury: Dictionary)
signal injury_healed(injury_id: String)
signal exposure_changed(chemical: String, ppm_minutes: float)
signal radiation_changed(dose_msv: float)
signal incapacitated(reason: String)
signal stabilised()

const MAX_HEALTH: float = 100.0
const REVIVE_HEALTH: float = 25.0
const RADIATION_ANNUAL_LIMIT_MSV: float = 20.0   # occupational effective dose, ICRP
const RADIATION_HARD_LIMIT_MSV: float = 1000.0    # acute sickness territory

const INJURY_PROFILES: Dictionary = {
	"chemical_burn": {"label": "Chemical burn", "damage_per_tick": 0.9, "heal_seconds": 45.0},
	"thermal_burn": {"label": "Thermal burn", "damage_per_tick": 0.7, "heal_seconds": 60.0},
	"laceration": {"label": "Glass laceration", "damage_per_tick": 0.5, "heal_seconds": 35.0},
	"inhalation": {"label": "Inhalation injury", "damage_per_tick": 0.45, "heal_seconds": 90.0},
	"eye_splash": {"label": "Eye splash", "damage_per_tick": 0.0, "heal_seconds": 30.0},
	"radiation": {"label": "Radiation exposure", "damage_per_tick": 0.0, "heal_seconds": 0.0}
}

var health: float = MAX_HEALTH
var stamina: float = 100.0
var is_incapacitated: bool = false
var death_count: int = 0
var radiation_msv: float = 0.0
var chemical_exposure: Dictionary = {}   # chemical -> ppm·min
var injuries: Array = []
var last_damage_source: String = ""

var _injury_counter: int = 0
var _revive_timer: float = 0.0
var _hud: CanvasLayer = null
var _hud_script = preload("res://ui/vitals_hud.gd")


func _ready() -> void:
	_ensure_save_link()
	_spawn_hud()


func _process(delta: float) -> void:
	# Injuries bleed/progress slowly and heal on their own clock. This is the
	# failure pressure that makes bad technique matter between experiments.
	for injury in injuries.duplicate():
		var profile: Dictionary = INJURY_PROFILES.get(str(injury.get("type", "")), {})
		var damage := float(profile.get("damage_per_tick", 0.0)) * float(injury.get("severity", 1.0)) * delta
		if damage > 0.0 and not is_incapacitated:
			_apply_raw_damage(damage, str(injury.get("type", "injury")))
		injury["remaining_s"] = float(injury.get("remaining_s", 0.0)) - delta
		if float(injury["remaining_s"]) <= 0.0:
			_heal_injury(str(injury.get("id", "")))

	injuries = injuries.filter(func(i): return float(i.get("remaining_s", 0.0)) > 0.0)

	if is_incapacitated:
		_revive_timer -= delta
		if _revive_timer <= 0.0:
			_stabilise()

	if stamina < 100.0:
		stamina = minf(100.0, stamina + 3.0 * delta)


func apply_damage(amount: float, type: String = "blunt", source: String = "laboratory accident") -> Dictionary:
	if amount <= 0.0:
		return {"ok": false, "error": "zero_damage"}
	last_damage_source = source
	_apply_raw_damage(amount, type)

	# Anything above a scratch leaves an ongoing injury with a real recovery time.
	if amount >= 6.0:
		_add_injury(type, clampf(amount / 20.0, 0.4, 2.0))
	return {"ok": true, "health": health, "incapacitated": is_incapacitated}


func _apply_raw_damage(amount: float, type: String) -> void:
	health = clampf(health - amount, 0.0, MAX_HEALTH)
	health_changed.emit(health, MAX_HEALTH)
	if health <= 0.0 and not is_incapacitated:
		is_incapacitated = true
		death_count += 1
		_revive_timer = 6.0
		incapacitated.emit(last_damage_source if last_damage_source != "" else type)


func _add_injury(type: String, severity: float) -> void:
	var profile: Dictionary = INJURY_PROFILES.get(type, {"label": type.capitalize(), "heal_seconds": 40.0})
	_injury_counter += 1
	var injury := {
		"id": "inj_%d" % _injury_counter,
		"type": type,
		"label": profile.get("label", type),
		"severity": severity,
		"remaining_s": float(profile.get("heal_seconds", 40.0))
	}
	# Do not stack the same injury type into an unreadable list.
	for existing in injuries:
		if str(existing.get("type", "")) == type:
			existing["severity"] = minf(3.0, float(existing.get("severity", 1.0)) + severity * 0.5)
			existing["remaining_s"] = maxf(float(existing.get("remaining_s", 0.0)), float(injury["remaining_s"]))
			injury_added.emit(existing)
			return
	injuries.append(injury)
	injury_added.emit(injury)


func _heal_injury(injury_id: String) -> void:
	var before := injuries.size()
	injuries = injuries.filter(func(i): return str(i.get("id", "")) != injury_id)
	if injuries.size() != before:
		injury_healed.emit(injury_id)


func heal(amount: float) -> void:
	health = clampf(health + amount, 0.0, MAX_HEALTH)
	health_changed.emit(health, MAX_HEALTH)


func add_chemical_exposure(chemical: String, ppm: float, minutes: float) -> void:
	if ppm <= 0.0 or minutes <= 0.0:
		return
	var key := chemical.to_lower()
	chemical_exposure[key] = float(chemical_exposure.get(key, 0.0)) + ppm * minutes
	var dose := float(chemical_exposure[key])
	exposure_changed.emit(key, dose)

	# Chronic exposure pressure above 10x the 8-hour PEL-equivalent budget.
	# (ppm·min budget here is a gameplay abstraction, clearly labelled as such.)
	if dose > 5000.0:
		_add_injury("inhalation", clampf(dose / 20000.0, 0.3, 1.5))
		_apply_raw_damage(0.3, "inhalation")


func add_radiation(dose_msv: float) -> void:
	if dose_msv <= 0.0:
		return
	radiation_msv += dose_msv
	radiation_changed.emit(radiation_msv)
	if radiation_msv > RADIATION_ANNUAL_LIMIT_MSV:
		_apply_raw_damage(dose_msv * 0.05, "radiation")
	if radiation_msv >= RADIATION_HARD_LIMIT_MSV and not is_incapacitated:
		_apply_raw_damage(MAX_HEALTH, "radiation")


func _stabilise() -> void:
	is_incapacitated = false
	health = REVIVE_HEALTH
	# Stabilisation costs resources, not XP: the safety officer bills the lab.
	stamina = 50.0
	health_changed.emit(health, MAX_HEALTH)
	stabilised.emit()


func doff_suit(protection: Dictionary) -> void:
	# Suits are consumed by the action; this hook exists so lab scenes can ask for
	# the mitigation factor without duplicating suit tables.
	pass


func mitigation_for(hazard: String) -> float:
	# Multiplier applied by lab scenes to incoming damage (1.0 = no protection).
	var factor := 1.0
	for injury in injuries:
		if str(injury.get("type", "")) == hazard:
			factor += 0.1
	return clampf(factor, 0.2, 2.0)


func set_hazard_protection(value: float) -> void:
	_protection_factor = clampf(value, 0.05, 1.0)


var _protection_factor: float = 1.0


func apply_hazard_damage(amount: float, type: String, source: String) -> Dictionary:
	return apply_damage(amount * _protection_factor, type, source)


func to_dict() -> Dictionary:
	return {
		"health": health,
		"stamina": stamina,
		"is_incapacitated": is_incapacitated,
		"death_count": death_count,
		"radiation_msv": radiation_msv,
		"chemical_exposure": chemical_exposure.duplicate(true),
		"injuries": injuries.duplicate(true)
	}


func from_dict(data: Dictionary) -> void:
	health = clampf(float(data.get("health", MAX_HEALTH)), 0.0, MAX_HEALTH)
	stamina = clampf(float(data.get("stamina", 100.0)), 0.0, 100.0)
	death_count = int(data.get("death_count", 0))
	radiation_msv = maxf(0.0, float(data.get("radiation_msv", 0.0)))
	chemical_exposure = data.get("chemical_exposure", {}).duplicate(true)
	injuries.clear()
	for injury in data.get("injuries", []):
		injuries.append(injury)
	is_incapacitated = false
	health_changed.emit(health, MAX_HEALTH)


func _ensure_save_link() -> void:
	var save_manager := get_node_or_null("/root/SaveManager")
	if save_manager == null:
		return
	if save_manager.has_method("set_setting"):
		save_manager.save_data["vitals"] = to_dict()
		save_manager.save_completed.connect(_on_save_completed)


func _on_save_completed(_success: bool) -> void:
	var save_manager := get_node_or_null("/root/SaveManager")
	if save_manager != null:
		save_manager.save_data["vitals"] = to_dict()


func _spawn_hud() -> void:
	if _hud != null:
		return
	_hud = CanvasLayer.new()
	_hud.name = "VitalsHUD"
	_hud.layer = 20
	var control := Control.new()
	control.set_script(_hud_script)
	control.set_anchors_preset(Control.PRESET_FULL_RECT)
	control.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(control)
	add_child(_hud)
	# Vitals belong to laboratory gameplay, not to the menu or loading screen.
	_hud.visible = false


func set_hud_visible(is_visible: bool) -> void:
	if _hud != null:
		_hud.visible = is_visible
