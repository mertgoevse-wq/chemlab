# ChemLab Quest Campaign & OSHA Safety Compliance Engine (Godot 4 Engine)
# Autoload Singleton: QuestManager
# Manages 6-contract campaign graph, 10 Acts, moral forks, OSHA safety scoring,
# background selection, investigation mode, and celebration fanfare.

extends Node

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

enum QuestStatus {
	LOCKED = 0,
	AVAILABLE = 1,
	IN_PROGRESS = 2,
	COMPLETED = 3
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
signal quest_unlocked(quest_id: String)
signal quest_failed(quest_id: String, reason: String)
signal objective_updated(quest_id: String, objective_id: String, progress: float)
signal safety_score_updated(new_score: float, delta: float, reason: String)
signal safety_warning_triggered(severity: String, title: String, message: String, osha_code: String)
signal fanfare_celebration_started(quest_title: String, xp: int, stars: int)
signal investigation_mode_toggled(enabled: bool, modes: Array[String])

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

var completed_quests: Array[String] = []
var failed_quests: Array[String] = []
var current_background: String = "academic"
var investigation_mode_active: bool = false
var investigation_vision_modes: Array[String] = []

# Master Campaign Catalog (6 authored core contracts for Act I-IV)
var quests: Dictionary = {}

# Backward compatibility alias
var active_quest: String:
	get:
		return active_quest_id
	set(val):
		active_quest_id = val

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	_initialize_quest_catalog()
	_connect_to_input_manager()
	_load_save_data()
	# Start Quest 1 by default if no quest is active
	if active_quest_id != "" and quests.has(active_quest_id):
		if int(quests[active_quest_id].get("status", QuestStatus.LOCKED)) == QuestStatus.AVAILABLE:
			start_quest(active_quest_id)


func _initialize_quest_catalog() -> void:
	quests = {
		"quest_01_orientation": {
			"id": "quest_01_orientation",
			"tier": 1,
			"title": "Orientation & Safety Protocols",
			"category": "Basic Laboratory Technique",
			"speaker": "Prof. Aris Thorne",
			"briefing": "Tear open the PPE station and equip ANSI Z87.1 chemical splash goggles. Place your 250 mL Erlenmeyer flask on the analytical balance and tare. Dispense 25.0 mL of 0.1 M HCl, add 3 drops of phenolphthalein indicator, and titrate dropwise with 0.1 M NaOH until the first faint persistent pink endpoint holds.",
			"description": "Familiarize yourself with laboratory personal protective equipment (PPE), balance taring, precise volumetric measurement, and acid-base titration to a persistent phenolphthalein endpoint.",
			"xp_reward": 500,
			"status": QuestStatus.AVAILABLE,
			"next_quest_id": "quest_02_iodine_clock",
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
					"current": 1.0,
					"target": 8.5,
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
			"speaker": "Dr. Lena Voss",
			"briefing": "Mix potassium iodide and soluble starch solutions in Beaker A. Initiate kinetics by adding hydrogen peroxide, and activate the digital timer to measure the exact instantaneous transition to deep blue triiodide-starch complex.",
			"description": "Measure reaction rates by executing the sudden transition to triiodide-starch complex.",
			"xp_reward": 750,
			"status": QuestStatus.LOCKED,
			"next_quest_id": "quest_03_bz_oscillator",
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
			"speaker": "Prof. Aris Thorne",
			"briefing": "Condition 50 mL malonic acid solution to 45.0 °C on the magnetic hotplate. Add potassium bromate and ferroin catalyst, and observe periodic chemical wave fronts as the redox state cycles between ferriin and ferroin.",
			"description": "Induce periodic chemical wave pulses with malonic acid, bromate, and ferroin catalyst.",
			"xp_reward": 1200,
			"status": QuestStatus.LOCKED,
			"next_quest_id": "quest_04_contaminated_batch",
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
		},
		"quest_04_contaminated_batch": {
			"id": "quest_04_contaminated_batch",
			"tier": 4,
			"title": "The Contaminated Batch",
			"category": "Forensic Analytical Chemistry",
			"speaker": "Dr. Lena Voss",
			"briefing": "An unlabeled production lot has been isolated under fume hood 2. Take a platinum wire flame test of the suspicious salt smear to identify the cation contaminant, then execute an argentometric chloride titration with 0.05 M AgNO3 against potassium chromate indicator. Sign and submit your analytical report.",
			"description": "Investigate an unlabeled production lot under GLP protocol, isolate suspect salts, perform flame analysis, and determine chloride concentration.",
			"xp_reward": 1600,
			"status": QuestStatus.LOCKED,
			"next_quest_id": "quest_05_quiet_synthesis",
			"unlocked_apparatus": ["Fume_Hood", "Platinum_Wire_Loop", "Burette_50ml", "Spectrophotometer"],
			"unlocked_reagents": ["Sample_QC4471", "AgNO3_0.05M", "K2CrO4_Indicator", "Concentrated_HCl"],
			"objectives": [
				{
					"id": "isolate_sample",
					"title": "Isolate Sample QC-4471",
					"description": "Transfer 10.0 mL of suspect lot into certified reaction vessel under hood",
					"current": 0.0,
					"target": 1.0,
					"unit": "steps",
					"is_completed": false,
					"is_active": true,
					"osha_ref": "OSHA 1910.1450(c)"
				},
				{
					"id": "flame_test_identify",
					"title": "Flame Test Contaminant Identification",
					"description": "Perform platinum wire flame emission test on sample residue",
					"current": 0.0,
					"target": 1.0,
					"unit": "tests",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "ASTM E1613"
				},
				{
					"id": "chloride_titration",
					"title": "Argentometric Titration",
					"description": "Titrate aliquot with 0.05 M AgNO3 to brick-red chromate precipitate",
					"current": 0.0,
					"target": 1.0,
					"unit": "titrations",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "EPA Method 9253"
				},
				{
					"id": "sign_qc_report",
					"title": "Sign Quality Control Report",
					"description": "Digitally sign and certify batch analytical deviation findings",
					"current": 0.0,
					"target": 1.0,
					"unit": "reports",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "GLP 21 CFR Part 58"
				}
			]
		},
		"quest_05_quiet_synthesis": {
			"id": "quest_05_quiet_synthesis",
			"tier": 5,
			"title": "The Quiet Synthesis",
			"category": "Preparative Organic Chemistry",
			"speaker": "Mara Kestrel",
			"briefing": "Assemble the dry reflux condenser apparatus under inert atmosphere. Reflux the proprietary precursor at 78.0 °C, recrystallize the target ester from boiling absolute ethanol, and choose how to handle batch disposition.",
			"description": "Synthesize organic precursor under controlled heating, execute solvent recrystallization, and decide product disposition.",
			"xp_reward": 2200,
			"status": QuestStatus.LOCKED,
			"next_quest_id": "quest_06_riverbank_contract",
			"moral_fork": {
				"sell_batch": {
					"title": "Hand over the batch, take the payment",
					"faction": "Cartel",
					"reputation_delta": 25,
					"safety_delta": -5.0
				},
				"keep_evidence": {
					"title": "Seal an archive aliquot and alert the regional inspector",
					"faction": "KHI-ACS",
					"reputation_delta": 30,
					"safety_delta": 5.0
				}
			},
			"unlocked_apparatus": ["Liebig_Condenser", "Round_Bottom_Flask_500ml", "Heating_Mantle", "Buchner_Funnel"],
			"unlocked_reagents": ["Proprietary_Precursor_G7", "Absolute_Ethanol", "Sulfuric_Acid_Catalyst"],
			"objectives": [
				{
					"id": "dry_assembly",
					"title": "Dry Glassware Assembly",
					"description": "Assemble round-bottom flask and Liebig condenser with water cooling lines",
					"current": 0.0,
					"target": 1.0,
					"unit": "assemblies",
					"is_completed": false,
					"is_active": true,
					"osha_ref": "NFPA 45 Laboratory Safety"
				},
				{
					"id": "reflux_synthesis",
					"title": "Controlled Reflux at 78 °C",
					"description": "Maintain steady reflux boil at 78.0 °C for full synthesis duration",
					"current": 0.0,
					"target": 1.0,
					"unit": "runs",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "OSHA 1910.106 Flammable Liquids"
				},
				{
					"id": "recrystallize_batch",
					"title": "Ethanol Recrystallization",
					"description": "Vacuum filter crystals through Buchner funnel and wash with chilled ethanol",
					"current": 0.0,
					"target": 1.0,
					"unit": "batches",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "ISO 14644 Cleanroom Protocol"
				},
				{
					"id": "resolve_disposition",
					"title": "Resolve Product Disposition",
					"description": "Decide disposition through the moral fork: transfer batch or file evidence",
					"current": 0.0,
					"target": 1.0,
					"unit": "decisions",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "Ethical Compliance Standard 7"
				}
			]
		},
		"quest_06_riverbank_contract": {
			"id": "quest_06_riverbank_contract",
			"tier": 6,
			"title": "Riverbank Contract",
			"category": "Environmental Field Chemistry",
			"speaker": "Inspector Hale",
			"briefing": "Deploy to the three watershed sampling locations along the river. Collect water samples with chain-of-custody seals, calibrate your field UV-Vis spectrometer, and submit the compiled analytical dataset to the regional authority.",
			"description": "Field analysis of industrial runoff across three watershed sampling stations with portable spectrometry.",
			"xp_reward": 3000,
			"status": QuestStatus.LOCKED,
			"next_quest_id": "",
			"unlocked_apparatus": ["Field_Sampling_Kit", "Portable_Spectrometer", "Chain_Of_Custody_Seals"],
			"unlocked_reagents": ["Calibration_Standard_A", "Preservative_Nitric_Acid"],
			"objectives": [
				{
					"id": "reach_outfall_sites",
					"title": "Collect Field Samples",
					"description": "Collect water samples from Upstream, Plant Outfall, and Downstream estuary",
					"current": 0.0,
					"target": 3.0,
					"unit": "samples",
					"is_completed": false,
					"is_active": true,
					"osha_ref": "EPA 40 CFR Part 136"
				},
				{
					"id": "calibrate_spectrometer",
					"title": "Calibrate Field Spectrometer",
					"description": "Run baseline zero-point calibration using standard reference solution",
					"current": 0.0,
					"target": 1.0,
					"unit": "calibrations",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "NIST Traceable Calibration"
				},
				{
					"id": "submit_evidence",
					"title": "Submit Chain of Custody",
					"description": "File tamper-evident analytical report to Inspector Hale",
					"current": 0.0,
					"target": 1.0,
					"unit": "submissions",
					"is_completed": false,
					"is_active": false,
					"osha_ref": "Federal Evidence Rule 901"
				}
			]
		}
	}


func _connect_to_input_manager() -> void:
	var im: Node = null
	if Engine.has_singleton("InputManager"):
		im = Engine.get_singleton("InputManager")
	elif is_inside_tree() and get_tree() and get_tree().root and get_tree().root.has_node("InputManager"):
		im = get_tree().root.get_node("InputManager")

	if im:
		if im.has_signal("balance_tare_requested") and not im.balance_tare_requested.is_connected(_on_input_tare_requested):
			im.balance_tare_requested.connect(_on_input_tare_requested)
		if im.has_signal("apparatus_poured") and not im.apparatus_poured.is_connected(_on_input_apparatus_poured):
			im.apparatus_poured.connect(_on_input_apparatus_poured)


func _load_save_data() -> void:
	var save_manager = get_node_or_null("/root/SaveManager")
	if save_manager and save_manager.has_method("get_quest_data"):
		var data = save_manager.get_quest_data()
		if data is Dictionary and not data.is_empty():
			from_dict(data)

# =============================================================================
# QUEST PROGRESSION API
# =============================================================================

func start_quest(quest_id: String) -> bool:
	if not quests.has(quest_id):
		push_error("QuestManager: Quest '%s' not found." % quest_id)
		return false

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
	var objs = q.get("objectives", []) as Array
	for i in range(objs.size()):
		objs[i]["is_active"] = (i == 0)

	quest_started.emit(quest_id, q)
	return true


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

	var objs = q.get("objectives", []) as Array
	for i in range(objs.size()):
		var obj = objs[i] as Dictionary
		if obj.get("id", "") == obj_id:
			if obj.get("is_completed", false):
				return

			var target = float(obj.get("target", 1.0))
			var cur = float(obj.get("current", 0.0))
			obj["current"] = minf(cur + amount, target)
			var is_done = (float(obj["current"]) >= target)

			objective_progressed.emit(active_quest_id, i, float(obj["current"]), target, is_done)
			objective_updated.emit(active_quest_id, obj_id, float(obj["current"]) / maxf(0.001, target))

			if is_done:
				_complete_objective_internal(i)
			break


func complete_objective_by_id(obj_id: String) -> void:
	var q = get_active_quest()
	if q.is_empty():
		return

	var objs = q.get("objectives", []) as Array
	for i in range(objs.size()):
		var obj = objs[i] as Dictionary
		if obj.get("id", "") == obj_id and not obj.get("is_completed", false):
			obj["current"] = obj.get("target", 1.0)
			_complete_objective_internal(i)
			break


func _complete_objective_internal(idx: int) -> void:
	var q = get_active_quest()
	var objs = q.get("objectives", []) as Array
	if idx < 0 or idx >= objs.size():
		return

	var obj = objs[idx] as Dictionary
	obj["is_completed"] = true
	obj["is_active"] = false
	objective_completed.emit(active_quest_id, idx, obj)

	# Unlock next objective in sequence if exists
	if idx + 1 < objs.size():
		objs[idx + 1]["is_active"] = true
		var next_obj = objs[idx + 1]
		objective_progressed.emit(active_quest_id, idx + 1, float(next_obj.get("current", 0.0)), float(next_obj.get("target", 1.0)), false)
	else:
		# Check if all objectives are completed
		var all_done := true
		for o in objs:
			if not o.get("is_completed", false):
				all_done = false
				break
		if all_done:
			_complete_active_quest()


func _complete_active_quest() -> void:
	var q = get_active_quest()
	if q.is_empty():
		return

	q["status"] = QuestStatus.COMPLETED
	if not completed_quests.has(active_quest_id):
		completed_quests.append(active_quest_id)

	var xp = int(q.get("xp_reward", 500))
	var title = str(q.get("title", "Laboratory Quest"))

	# Unlock next contract in chain
	var next_id = str(q.get("next_quest_id", ""))
	if next_id != "" and quests.has(next_id):
		quests[next_id]["status"] = QuestStatus.AVAILABLE
		quest_unlocked.emit(next_id)

	# Calculate stars based on OSHA safety compliance
	var stars = 3
	if current_safety_score < 75.0:
		stars = 1
	elif current_safety_score < 90.0:
		stars = 2

	# Emit completion signals
	fanfare_celebration_started.emit(title, xp, stars)
	quest_completed.emit(active_quest_id, title, xp, current_safety_score)

	# Grant XP through SkillManager
	if is_inside_tree() and get_tree() and get_tree().root:
		var root = get_tree().root
		if root.has_node("SkillManager"):
			var sm = root.get_node("SkillManager")
			if sm.has_method("grant_skill_xp"):
				sm.grant_skill_xp("chemistry", xp, "quest_completion")
			elif sm.has_method("add_xp"):
				sm.add_xp("chemistry", xp)

	_sync_with_save_manager(xp)


func fail_quest(quest_id: String, reason: String) -> void:
	if quest_id == active_quest_id:
		if quests.has(quest_id):
			quests[quest_id]["status"] = QuestStatus.LOCKED
		if not failed_quests.has(quest_id):
			failed_quests.append(quest_id)
		quest_failed.emit(quest_id, reason)

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
# SIMULATION ACTION HANDLERS
# =============================================================================

func equip_safety_goggles() -> void:
	if ppe_equipped:
		return
	ppe_equipped = true
	advance_objective("equip_ppe", 1.0)


func place_flask_on_balance() -> void:
	pass


func tare_analytical_balance() -> void:
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

	if pour_rate > 0.65:
		trigger_safety_violation(
			15.0,
			"Violent Stream Influx",
			"Dropwise titration required near equivalence point. High flow rate caused splash hazard!",
			"OSHA 1910.1450"
		)

	current_flask_ph = clampf(current_flask_ph + (volume_added_ml * 0.35), 1.0, 12.0)

	if current_flask_ph >= 8.2 and current_flask_ph <= 9.0:
		complete_objective_by_id("titrate_naoh")
	elif current_flask_ph > 10.5:
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

	var act_obj = get_active_objective()
	var act_id = str(act_obj.get("id", ""))
	if act_id == "titrate_naoh":
		var delta_vol = rate * 0.08
		titrate_naoh_drop(delta_vol, rate)
	elif act_id == "dispense_hcl":
		var delta_acid = rate * 0.5
		dispense_hcl(delta_acid)


# =============================================================================
# APPARATUS EVENT INTEGRATION
# =============================================================================

func on_apparatus_event(apparatus_type: String, event_type: String, data: Dictionary) -> void:
	"""Handle events from apparatus like NMR spectrometer."""
	if apparatus_type == "nmr_spectrometer":
		_handle_nmr_event(event_type, data)


func _handle_nmr_event(event_type: String, data: Dictionary) -> void:
	"""Handle NMR spectrometer events for quest progression."""
	var quest_id = "quest_012_first_nmr_analysis"

	# Only process if this quest is active
	if active_quest_id != quest_id:
		return

	var q = get_active_quest()
	if q.is_empty():
		return

	match event_type:
		"sample_inserted":
			# Complete "load_sample" objective
			complete_objective_by_id("load_sample")

		"nmr_analysis_complete":
			# Complete "run_1h_nmr" and "interpret_spectrum" objectives
			complete_objective_by_id("run_1h_nmr")
			complete_objective_by_id("interpret_spectrum")

		"sample_removed":
			pass

# =============================================================================
# BACKGROUND & INVESTIGATION MODE
# =============================================================================

func set_background(background: String) -> void:
	if background in ["academic", "hobbyist", "ex_pharma"]:
		current_background = background


func get_background() -> String:
	return current_background


func get_investigation_mode() -> bool:
	return investigation_mode_active


func set_investigation_mode(enabled: bool, modes: Array[String] = []) -> void:
	investigation_mode_active = enabled
	investigation_vision_modes = modes
	investigation_mode_toggled.emit(enabled, modes)


func get_available_quests() -> Array[String]:
	var result: Array[String] = []
	for q_id in quests.keys():
		var status = int(quests[q_id].get("status", QuestStatus.LOCKED))
		if status == QuestStatus.AVAILABLE:
			result.append(q_id)
	return result


func is_quest_completed(quest_id: String) -> bool:
	return quest_id in completed_quests or (quests.has(quest_id) and int(quests[quest_id].get("status", 0)) == QuestStatus.COMPLETED)

# =============================================================================
# PERSISTENCE HELPERS
# =============================================================================

func _sync_with_save_manager(xp_awarded: int) -> void:
	if is_inside_tree() and get_tree() and get_tree().root:
		var root = get_tree().root
		if root.has_node("SaveManager"):
			var sm = root.get_node("SaveManager")
			if sm.has_method("record_quest_completion"):
				sm.record_quest_completion(active_quest_id, xp_awarded, current_safety_score)


func to_dict() -> Dictionary:
	return {
		"active_quest_id": active_quest_id,
		"current_safety_score": current_safety_score,
		"completed_quests": completed_quests,
		"failed_quests": failed_quests,
		"current_background": current_background
	}


func from_dict(data: Dictionary) -> void:
	active_quest_id = data.get("active_quest_id", data.get("active_quest", "quest_01_orientation"))
	current_safety_score = float(data.get("current_safety_score", INITIAL_SAFETY_SCORE))
	completed_quests.assign(data.get("completed_quests", []))
	failed_quests.assign(data.get("failed_quests", []))
	current_background = data.get("current_background", "academic")
