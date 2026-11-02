# ChemLab Quest Campaign & OSHA Safety Compliance Engine (Godot 4 Engine)
# Autoload Singleton: QuestManager
# Manages multi-step chemical questlines, objectives, safety scoring, and celebration fanfare.

extends Node

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

enum QuestStatus {
	LOCKED,
	AVAILABLE,
	IN_PROGRESS,
	COMPLETED
}

enum SafetyGrade {
	A_PLUS,      # 95 - 100% (OSHA Exemplary)
	A_COMPLIANT, # 85 - 94%  (Standard Compliant)
	B_CAUTION,   # 70 - 84%  (Minor Violations)
	C_WARNING,   # 50 - 69%  (Serious Safety Violations)
	F_SHUTDOWN   # < 50%     (Facility Evacuation & Stop-Work Order)
}

const INITIAL_SAFETY_SCORE: float = 100.0

# =============================================================================
# SIGNALS
# =============================================================================

signal quest_started(quest_id: String, quest_data: Dictionary)
signal objective_progressed(quest_id: String, objective_idx: int, current: float, target: float, is_done: bool)
signal objective_completed(quest_id: String, objective_idx: int, objective_data: Dictionary)
signal quest_completed(quest_id: String, quest_title: String, xp_reward: int, safety_score: float)
signal safety_score_updated(new_score: float, delta: float, reason: String)
signal safety_warning_triggered(severity: String, title: String, message: String, osha_code: String)
signal fanfare_celebration_started(quest_title: String, xp: int, stars: int)

# =============================================================================
# STATE VARIABLES
# =============================================================================

var active_quest_id: String = "quest_01_orientation"
var current_safety_score: float = INITIAL_SAFETY_SCORE
var ppe_equipped: bool = false
var balance_tared: bool = false
var dispensed_hcl_volume: float = 0.0
var indicator_drops_added: int = 0
var current_flask_ph: float = 1.0 # 0.1 M HCl has pH ~ 1.0

# Master Campaign Catalog
var quests: Dictionary = {}

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	_initialize_quest_catalog()
	_connect_to_input_manager()
	# Start Quest 1 by default
	start_quest("quest_01_orientation")


func _initialize_quest_catalog() -> void:
	quests = {
		"quest_01_orientation": {
			"id": "quest_01_orientation",
			"tier": 1,
			"title": "Orientation & Safety Protocols",
			"category": "Basic Laboratory Technique",
			"description": "Familiarize yourself with laboratory personal protective equipment (PPE), balance taring, precise volumetric measurement, and acid-base titration to a persistent phenolphthalein endpoint.",
			"xp_reward": 500,
			"status": QuestStatus.AVAILABLE,
			"unlocked_apparatus": ["Safety_Goggles", "Erlenmeyer_250ml", "Analytical_Balance", "Burette_50ml", "Pasteur_Pipette"],
			"unlocked_reagents": ["HCl_0.1M", "NaOH_0.1M", "Phenolphthalein_Indicator", "Distilled_Water"],
			"objectives": [
				{
					"id": "equip_ppe",
					"title": "Equip Safety Goggles",
					"description": "Tear open PPE station and equip safety goggles",
					"current": 0.0,
					"target": 1.0,
					"unit": "goggles",
					"is_completed": false,
					"is_active": true,
					"osha_ref": "OSHA 1910.133(a)(1)"
				},
				{
					"id": "place_flask_tare",
					"title": "Analytical Balance Tare",
					"description": "Place 250 mL Erlenmeyer Flask on Analytical Balance and Tare",
					"current": 0.0,
					"target": 1.0,
					"unit": "Tare",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "GLP Standard Protocol 4.2"
				},
				{
					"id": "dispense_hcl",
					"title": "Dispense Acid Reagent",
					"description": "Dispense 25.0 mL of 0.1 M Hydrochloric Acid (HCl)",
					"current": 0.0,
					"target": 25.0,
					"unit": "mL",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "OSHA 1910.1450 Chemical Hygiene"
				},
				{
					"id": "add_indicator",
					"title": "Add pH Indicator",
					"description": "Add 3 drops of Phenolphthalein Indicator",
					"current": 0.0,
					"target": 3.0,
					"unit": "drops",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "ASTM E200 Standard Practice"
				},
				{
					"id": "titrate_naoh",
					"title": "Titrate to Endpoint",
					"description": "Titrate dropwise with 0.1 M NaOH until persistent pink endpoint (pH 8.2 - 9.0)",
					"current": 1.0, # initial pH
					"target": 8.5, # target midpoint pH
					"unit": "pH",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "EPA Method 310.1"
				}
			]
		},
		"quest_02_iodine_clock": {
			"id": "quest_02_iodine_clock",
			"tier": 2,
			"title": "Landolt Iodine Clock Kinetics",
			"category": "Chemical Kinetics & Dynamics",
			"description": "Measure reaction rates by executing the sudden transition to triiodide-starch complex.",
			"xp_reward": 750,
			"status": QuestStatus.LOCKED,
			"unlocked_apparatus": ["Magnetic_Stirrer", "Graduated_Cylinder_100ml"],
			"unlocked_reagents": ["Hydrogen_Peroxide", "Potassium_Iodide", "Soluble_Starch"],
			"objectives": [
				{
					"id": "prepare_solutions",
					"title": "Prepare Reactants",
					"description": "Mix Potassium Iodide and Starch solution in Beaker A",
					"current": 0.0,
					"target": 1.0,
					"unit": "steps",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "OSHA 1910.1200"
				},
				{
					"id": "add_peroxide_clock",
					"title": "Initiate Kinetics",
					"description": "Pour Hydrogen Peroxide and activate stopwatch timer",
					"current": 0.0,
					"target": 1.0,
					"unit": "steps",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "OSHA 1910.1450"
				}
			]
		},
		"quest_03_bz_oscillator": {
			"id": "quest_03_bz_oscillator",
			"tier": 3,
			"title": "Belousov-Zhabotinsky Oscillation",
			"category": "Non-Equilibrium Thermodynamics",
			"description": "Induce periodic chemical wave pulses with malonic acid, bromate, and ferroin catalyst.",
			"xp_reward": 1200,
			"status": QuestStatus.LOCKED,
			"unlocked_apparatus": ["Petri_Dish", "Spectrophotometer"],
			"unlocked_reagents": ["Malonic_Acid", "Potassium_Bromate", "Ferroin_Catalyst"],
			"objectives": [
				{
					"id": "heat_malonic_acid",
					"title": "Thermal Conditioning",
					"description": "Heat 50 mL Malonic Acid Solution to 45.0 °C on magnetic hotplate",
					"current": 20.0,
					"target": 45.0,
					"unit": "°C",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "NFPA 45 Fire Protection"
				}
			]
		}
	}


func _connect_to_input_manager() -> void:
	# Intercept InputManager events to automatically advance objectives
	if Engine.has_singleton("InputManager"):
		var im = Engine.get_singleton("InputManager")
		if im.has_signal("balance_tare_requested"):
			im.balance_tare_requested.connect(_on_input_tare_requested)
		if im.has_signal("apparatus_poured"):
			im.apparatus_poured.connect(_on_input_apparatus_poured)
	else:
		# Check autoload tree node
		var root = get_tree().root if get_tree() else null
		if root and root.has_node("InputManager"):
			var im = root.get_node("InputManager")
			im.balance_tare_requested.connect(_on_input_tare_requested)
			im.apparatus_poured.connect(_on_input_apparatus_poured)

# =============================================================================
# QUEST PROGRESSION API
# =============================================================================

func start_quest(quest_id: String) -> void:
	if not quests.has(quest_id):
		push_error("QuestManager: Quest '%s' not found." % quest_id)
		return

	active_quest_id = quest_id
	var q = quests[quest_id] as Dictionary
	q["status"] = QuestStatus.IN_PROGRESS

	# Reset states for Quest 1
	if quest_id == "quest_01_orientation":
		ppe_equipped = false
		balance_tared = false
		dispensed_hcl_volume = 0.0
		indicator_drops_added = 0
		current_flask_ph = 1.0

	# Mark first objective active
	var objs = q["objectives"] as Array
	for i in range(objs.size()):
		objs[i]["is_active"] = (i == 0)

	quest_started.emit(quest_id, q)


func get_active_quest() -> Dictionary:
	return quests.get(active_quest_id, {})


func get_active_objective() -> Dictionary:
	var q = get_active_quest()
	if q.is_empty():
		return {}
	for obj in q.get("objectives", []):
		if obj.get("is_active", false) and not obj.get("is_completed", false):
			return obj
	return {}


func advance_objective(obj_id: String, amount: float = 1.0) -> void:
	var q = get_active_quest()
	if q.is_empty():
		return

	var objs = q["objectives"] as Array
	for i in range(objs.size()):
		var obj = objs[i] as Dictionary
		if obj["id"] == obj_id:
			if obj["is_completed"]:
				return

			obj["current"] = minf(obj["current"] + amount, obj["target"])
			var is_done = (obj["current"] >= obj["target"])

			objective_progressed.emit(active_quest_id, i, obj["current"], obj["target"], is_done)

			if is_done:
				_complete_objective_internal(i)
			break


func complete_objective_by_id(obj_id: String) -> void:
	var q = get_active_quest()
	if q.is_empty():
		return

	var objs = q["objectives"] as Array
	for i in range(objs.size()):
		var obj = objs[i] as Dictionary
		if obj["id"] == obj_id and not obj["is_completed"]:
			obj["current"] = obj["target"]
			_complete_objective_internal(i)
			break


func _complete_objective_internal(idx: int) -> void:
	var q = get_active_quest()
	var objs = q["objectives"] as Array
	var obj = objs[idx] as Dictionary

	obj["is_completed"] = true
	obj["is_active"] = false
	objective_completed.emit(active_quest_id, idx, obj)

	# Unlock next objective in sequence
	if idx + 1 < objs.size():
		objs[idx + 1]["is_active"] = true
		var next_obj = objs[idx + 1]
		objective_progressed.emit(active_quest_id, idx + 1, next_obj["current"], next_obj["target"], false)
	else:
		# All objectives complete: Complete Quest
		_complete_active_quest()


func _complete_active_quest() -> void:
	var q = get_active_quest()
	q["status"] = QuestStatus.COMPLETED
	var xp = int(q.get("xp_reward", 500))
	var title = str(q.get("title", "Laboratory Quest"))

	# Calculate stars based on OSHA safety compliance
	var stars = 3
	if current_safety_score < 75.0:
		stars = 1
	elif current_safety_score < 90.0:
		stars = 2

	# Emit completion fanfare
	fanfare_celebration_started.emit(title, xp, stars)
	quest_completed.emit(active_quest_id, title, xp, current_safety_score)

	# Update SaveManager if present
	_sync_with_save_manager(xp)

# =============================================================================
# OSHA SAFETY COMPLIANCE & PENALTY ENGINE
# =============================================================================

func trigger_safety_violation(penalty: float, title: String, message: String, osha_code: String) -> void:
	current_safety_score = maxf(0.0, current_safety_score - penalty)
	safety_score_updated.emit(current_safety_score, -penalty, message)
	safety_warning_triggered.emit("WARNING" if penalty < 20.0 else "CRITICAL", title, message, osha_code)


func get_safety_grade() -> SafetyGrade:
	if current_safety_score >= 95.0:
		return SafetyGrade.A_PLUS
	elif current_safety_score >= 85.0:
		return SafetyGrade.A_COMPLIANT
	elif current_safety_score >= 70.0:
		return SafetyGrade.B_CAUTION
	elif current_safety_score >= 50.0:
		return SafetyGrade.C_WARNING
	return SafetyGrade.F_SHUTDOWN


func get_safety_grade_string() -> String:
	match get_safety_grade():
		SafetyGrade.A_PLUS: return "Grade A+ (OSHA Exemplary Compliance)"
		SafetyGrade.A_COMPLIANT: return "Grade A (OSHA Standard Compliant)"
		SafetyGrade.B_CAUTION: return "Grade B (Minor Non-Conformance)"
		SafetyGrade.C_WARNING: return "Grade C (Safety Notice Issued)"
		_: return "Grade F (Facility Stop-Work Order)"

# =============================================================================
# SIMULATION ACTION HANDLERS (ORIENTED FOR QUEST 1)
# =============================================================================

func equip_safety_goggles() -> void:
	if ppe_equipped:
		return
	ppe_equipped = true
	advance_objective("equip_ppe", 1.0)


func place_flask_on_balance() -> void:
	# Ready to tare
	pass


func tare_analytical_balance() -> void:
	# Requires PPE first or penalty
	if not ppe_equipped:
		trigger_safety_violation(
			20.0,
			"OSHA 1910.133 Violation",
			"Chemical splash goggles must be equipped before operating analytical instruments!",
			"29 CFR 1910.133(a)(1)"
		)

	balance_tared = true
	advance_objective("place_flask_tare", 1.0)


func dispense_hcl(volume_ml: float) -> void:
	if not ppe_equipped:
		trigger_safety_violation(
			25.0,
			"Corrosive Acid Hazard",
			"Handling 0.1 M HCl without ANSI-rated eye protection violates OSHA chemical hygiene protocol!",
			"29 CFR 1910.1450(e)"
		)

	if not balance_tared:
		trigger_safety_violation(
			5.0,
			"Measurement Non-Conformance",
			"Dispensing acid into untared flask creates unacceptable analytical error margin.",
			"GLP 4.2"
		)

	dispensed_hcl_volume += volume_ml
	advance_objective("dispense_hcl", volume_ml)


func add_phenolphthalein_drops(drops: int = 1) -> void:
	if dispensed_hcl_volume < 20.0:
		trigger_safety_violation(
			5.0,
			"Procedural Deviation",
			"Phenolphthalein indicator must be added to acidic aliquot, not dry glassware.",
			"Standard Acid-Base Protocol"
		)

	indicator_drops_added += drops
	advance_objective("add_indicator", float(drops))


func titrate_naoh_drop(volume_added_ml: float, pour_rate: float) -> void:
	if indicator_drops_added < 1:
		trigger_safety_violation(
			10.0,
			"Blind Titration Hazard",
			"Titrating without visual indicator risks runaway neutralization overshoot!",
			"EPA 310.1"
		)

	# Over-pouring / dumping instead of dropwise titration penalty
	if pour_rate > 0.65:
		trigger_safety_violation(
			15.0,
			"Violent Stream Influx",
			"Dropwise titration required near equivalence point. High flow rate caused splash hazard!",
			"OSHA 1910.1450"
		)

	# Calculate chemical neutralization curve:
	# V_acid = 25 mL, C_acid = 0.1 M -> 2.5 mmol H+
	# As NaOH (0.1 M) enters, pH rises along sigmoidal curve:
	# At equivalence point (25.0 mL NaOH), pH jumps rapidly from 4 to 10
	# Phenolphthalein transitions at pH 8.2 - 9.0 (faint persistent pink)
	current_flask_ph = clampf(current_flask_ph + (volume_added_ml * 0.35), 1.0, 12.0)

	if current_flask_ph >= 8.2 and current_flask_ph <= 9.0:
		# Perfect persistent pink endpoint reached!
		complete_objective_by_id("titrate_naoh")
	elif current_flask_ph > 10.5:
		# Over-titrated into magenta overshoot
		trigger_safety_violation(
			10.0,
			"Titration Overshoot",
			"Excess base added! Color changed to deep magenta (pH > 10.5). Endpoint missed.",
			"Analytical Deviation"
		)

# =============================================================================
# INPUT MANAGER CALLBACKS
# =============================================================================

func _on_input_tare_requested() -> void:
	tare_analytical_balance()


func _on_input_apparatus_poured(rate: float) -> void:
	if rate <= 0.0:
		return

	# If active objective is titrate_naoh, pour acts as titrant
	var act_obj = get_active_objective()
	if act_obj.get("id", "") == "titrate_naoh":
		var delta_vol = rate * 0.08 # ml per tick
		titrate_naoh_drop(delta_vol, rate)
	elif act_obj.get("id", "") == "dispense_hcl":
		var delta_acid = rate * 0.5 # ml per tick
		dispense_hcl(delta_acid)

# =============================================================================
# INTEGRATION WITH SAVE MANAGER
# =============================================================================

func _sync_with_save_manager(xp_awarded: int) -> void:
	var root = get_tree().root if get_tree() else null
	if root and root.has_node("SaveManager"):
		var sm = root.get_node("SaveManager")
		if sm.has_method("record_quest_completion"):
			sm.record_quest_completion(active_quest_id, xp_awarded, current_safety_score)
