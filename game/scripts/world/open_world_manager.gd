# Athanor Ascension — Open World & Side Quests Contract Engine
# Autoload: OpenWorldManager
# Manages multi-sector lab exploration, fast-travel pneumatic network,
# dynamic research contracts, clandestine synthesis orders, remediation drills,
# and Level 99 Mastery Milestones / Attire unlocks across all 20 skill tracks.

extends Node

# =============================================================================
# SIGNALS
# =============================================================================

signal sector_unlocked(sector_id: String, sector_data: Dictionary)
signal sector_entered(sector_id: String, prev_sector_id: String)
signal contract_accepted(contract_id: String, contract_data: Dictionary)
signal contract_progressed(contract_id: String, objective_id: String, current: float, target: float)
signal contract_completed(contract_id: String, rewards: Dictionary)
signal contract_failed(contract_id: String, reason: String)
signal mastery_milestone_reached(skill_id: String, milestone_level: int, reward_item: String)
signal fast_travel_completed(target_sector: String)

# =============================================================================
# SECTOR CATALOG (7 Interconnected Laboratory Sectors)
# =============================================================================

var sectors: Dictionary = {
	"sector_atrium": {
		"id": "sector_atrium",
		"name": "Grand Atrium & Academic Concourse",
		"scene_path": "res://scenes/laboratories/lab_hub.tscn",
		"containment_level": "BSL-1 / General",
		"description": "Central vaulted rotunda and institutional research facilities. Features analytical balance rooms, UV-Vis spectrophotometers, and public notice boards.",
		"unlocked_by_default": true,
		"connected_sectors": ["sector_underground", "sector_pilot_plant", "sector_forensics", "sector_cleanroom"],
		"facilities": ["Analytical Balances", "UV-Vis Spectrophotometer", "Titration Practicum Bench", "Chemical Stores A"]
	},
	"sector_underground": {
		"id": "sector_underground",
		"name": "Underground Alchemical Warren",
		"scene_path": "res://scenes/laboratories/synthesis_lab.tscn",
		"containment_level": "Off-Grid / Unregulated",
		"description": "Subterranean clandestine synthesis benches and customized borosilicate glassware setups. The epicenter of rogue organic chemistry and Aetherkin experimentation.",
		"unlocked_by_default": true,
		"connected_sectors": ["sector_atrium", "sector_pilot_plant", "sector_containment"],
		"facilities": ["Dual-Manifold Schlenk Line", "Rotary Evaporator (Rotovap)", "Soxhlet Extraction Bank", "Distillation Train"]
	},
	"sector_pilot_plant": {
		"id": "sector_pilot_plant",
		"name": "Wing Delta Industrial Pilot Plant",
		"scene_path": "res://scenes/laboratories/pilot_plant.tscn",
		"containment_level": "Industrial Continuous Flow",
		"description": "Full-scale engineering facility with jacketed continuous flow microreactors, automated fraction collectors, and PID thermal mantles.",
		"unlocked_by_default": false,
		"unlock_requirement": { "skill": "engineering", "level": 15 },
		"connected_sectors": ["sector_atrium", "sector_underground", "sector_containment", "sector_orbital"],
		"facilities": ["50L Jacketed CSTR", "Continuous Flow Microreactor", "Centrifugal Separator", "Automated Fraction Collector"]
	},
	"sector_containment": {
		"id": "sector_containment",
		"name": "Hazardous Containment Vault",
		"scene_path": "res://scenes/laboratories/radiochemistry_lab.tscn",
		"containment_level": "BSL-4 / Radiation High-Hazard",
		"description": "Reinforced heavy-shielding vault housing hot cells, inert gloveboxes, negative-pressure airlocks, and cyclotron beam ports.",
		"unlocked_by_default": false,
		"unlock_requirement": { "skill": "containment", "level": 25 },
		"connected_sectors": ["sector_underground", "sector_pilot_plant", "sector_orbital"],
		"facilities": ["Inert Atmosphere Glovebox (<0.1 ppm O2/H2O)", "Hot Cell Telemanipulators", "Cyclotron Target Vault", "Lead Shielding Bay"]
	},
	"sector_forensics": {
		"id": "sector_forensics",
		"name": "Forensic Vault & Spectral Archive",
		"scene_path": "res://scenes/laboratories/forensic_lab.tscn",
		"containment_level": "ISO 17025 Certified",
		"description": "Ultra-sensitive instrumentation suite. High-field 600 MHz superconducting NMR, GC-MS with electron ionization, and chiral HPLC.",
		"unlocked_by_default": false,
		"unlock_requirement": { "skill": "forensics", "level": 20 },
		"connected_sectors": ["sector_atrium", "sector_cleanroom"],
		"facilities": ["600 MHz Cryo-Probe NMR", "Triple-Quad GC-MS", "Chiral C18 HPLC System", "FTIR-ATR Spectrometer"]
	},
	"sector_cleanroom": {
		"id": "sector_cleanroom",
		"name": "Bio-Molecular Cleanroom",
		"scene_path": "res://scenes/laboratories/cleanroom_lab.tscn",
		"containment_level": "ISO Class 5 / BSL-3",
		"description": "Laminar flow sterile suites for genomic engineering, cellular culture, recombinant DNA expression, and Aetherkin symbiont tissue cultivation.",
		"unlocked_by_default": false,
		"unlock_requirement": { "skill": "genetics", "level": 20 },
		"connected_sectors": ["sector_atrium", "sector_forensics", "sector_orbital"],
		"facilities": ["Laminar Airflow Biosafety Cabinet", "High-Throughput PCR Thermocycler", "CO2 Incubator Array", "Automated DNA Sequencer"]
	},
	"sector_orbital": {
		"id": "sector_orbital",
		"name": "Orbital Telemetry & Launchpad",
		"scene_path": "res://scenes/laboratories/orbital_lab.tscn",
		"containment_level": "Zero-G / Vacuum Sublimation",
		"description": "High-altitude environmental and microgravity synthesis node. Perfect for defect-free crystal growth, vacuum vapor deposition, and cosmic radiation harvesting.",
		"unlocked_by_default": false,
		"unlock_requirement": { "skill": "physics", "level": 40 },
		"connected_sectors": ["sector_pilot_plant", "sector_containment", "sector_cleanroom"],
		"facilities": ["Microgravity Crystallizer", "Ultra-High Vacuum Sublimation Chamber", "Magnetron Sputtering Rig", "Cosmic Ray Sensor"]
	}
}

# =============================================================================
# RESEARCH CONTRACTS & SIDE QUESTS CATALOG
# =============================================================================

var contracts: Dictionary = {
	"contract_aspirin_purity": {
		"id": "contract_aspirin_purity",
		"title": "Contract: Pharmacopeial Aspirin Assay",
		"category": "Analytical Services",
		"sector": "sector_atrium",
		"requester": "Metropolitan Health Authority",
		"min_level": { "skill": "chemistry", "level": 5 },
		"description": "Perform high-performance liquid chromatography (HPLC) and acid-base back-titration on commercial acetylsalicylic acid batches to detect salicylic acid hydrolysis impurities.",
		"xp_reward": { "chemistry": 600, "analytical_chemistry": 400 },
		"reputation": { "academic": 25 },
		"credits_reward": 500,
		"item_rewards": ["hplc_precision_column_c18", "standard_buffer_pack"],
		"status": "available",
		"objectives": [
			{ "id": "synthesize_aspirin", "title": "Synthesize Crude Acetylsalicylic Acid Crystals", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "nmr_verify", "title": "Verify Purity via 1H-NMR Spectroscopy", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_luminol_chemiluminescence": {
		"id": "contract_luminol_chemiluminescence",
		"title": "Contract: Forensic Luminol Quantum Yield",
		"category": "Forensic Investigation",
		"sector": "sector_forensics",
		"requester": "State Crime Laboratory",
		"min_level": { "skill": "forensics", "level": 15 },
		"description": "Synthesize and calibrate forensic luminol reagent with hydrogen peroxide and potassium ferricyanide catalyst. Measure chemiluminescent emission peak at 425 nm.",
		"xp_reward": { "forensics": 850, "chemistry": 500 },
		"reputation": { "academic": 30 },
		"credits_reward": 750,
		"item_rewards": ["photomultiplier_tube_blue", "fluorescein_sodium_salt"],
		"status": "available",
		"objectives": [
			{ "id": "prepare_luminol_stock", "title": "Prepare 0.1% Luminol in 5% Na2CO3 Buffer", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "add_oxidant", "title": "Inject 3% H2O2 & Fe(III) Catalyst Solution", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "measure_emission", "title": "Measure 425 nm Luminescence (>1000 RLU)", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_schlenk_pyrophoric_transfer": {
		"id": "contract_schlenk_pyrophoric_transfer",
		"title": "Contract: Schlenk Manifold Air-Free Purge",
		"category": "Safety Remediation",
		"sector": "sector_underground",
		"requester": "Organometallic Synthesis Syndicate",
		"min_level": { "skill": "lab_safety", "level": 25 },
		"description": "Execute a rigorous 3x evacuate-refill cycle on a dual-manifold Schlenk line using dry argon. Transfer moisture-sensitive n-butyllithium without fire or flash.",
		"xp_reward": { "lab_safety": 1200, "containment": 800, "chemistry": 600 },
		"reputation": { "underground": 45 },
		"credits_reward": 1200,
		"item_rewards": ["schlenk_tap_greaseless_viton", "argon_purification_scrubber"],
		"status": "available",
		"objectives": [
			{ "id": "vacuum_evacuate", "title": "Evacuate Manifold to <0.05 mbar (High Vacuum)", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "refill_argon", "title": "Refill with Pure Argon (Check Mineral Oil Bubbler)", "current": 0.0, "target": 3.0, "is_done": false },
			{ "id": "cannula_transfer", "title": "Complete Syringe/Cannula Transfer without Leak", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_soxhlet_caffeine_extraction": {
		"id": "contract_soxhlet_caffeine_extraction",
		"title": "Contract: Botanical Soxhlet Alkaloid Extraction",
		"category": "Natural Product Isolation",
		"sector": "sector_underground",
		"requester": "Apothecary Guild",
		"min_level": { "skill": "apparatus_building", "level": 20 },
		"description": "Assemble a continuous Soxhlet extractor with Allihn condenser. Run 8 siphon discharge cycles with dichloromethane on Camellia sinensis to isolate crude caffeine crystals.",
		"xp_reward": { "apparatus_building": 900, "pharmacology": 700 },
		"reputation": { "academic": 20, "underground": 20 },
		"credits_reward": 900,
		"item_rewards": ["soxhlet_borosilicate_body", "sublimation_adapter_cold_finger"],
		"status": "available",
		"objectives": [
			{ "id": "assemble_soxhlet", "title": "Assemble Heating Mantle, Flask, Soxhlet, Condenser", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "run_siphon_cycles", "title": "Maintain Reflux for 8 Siphon Discharge Cycles", "current": 0.0, "target": 8.0, "is_done": false },
			{ "id": "rotovap_concentrate", "title": "Rotovap Solvent to Recover Pure Caffeine Cake", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_clandestine_pihkal_order": {
		"id": "contract_clandestine_pihkal_order",
		"title": "Contract: Shulgin Pathway 2C-B Selective Bromination",
		"category": "Underground Synthesis",
		"sector": "sector_underground",
		"requester": "Anonymous Counter-Culture Archivist",
		"min_level": { "skill": "pharmacology", "level": 35 },
		"description": "Execute Step 3 of PiHKAL #20 (2C-B). Controlled addition of elemental bromine in glacial acetic acid to 2,5-dimethoxyphenethylamine. Crystallize hydrobromide salt.",
		"xp_reward": { "pharmacology": 1800, "toxicology": 1000, "chemistry": 1200 },
		"reputation": { "underground": 60, "ex_pharma": 30 },
		"credits_reward": 2500,
		"item_rewards": ["glacial_acetic_acid_carboy", "recrystallization_buchner_frit"],
		"status": "available",
		"objectives": [
			{ "id": "dissolve_precursor", "title": "Dissolve 2C-H in Anhydrous Glacial Acetic Acid", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "dropwise_bromine", "title": "Dropwise Addition of Br2/AcOH Solution at 18-22°C", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "filter_wash", "title": "Vacuum Filter 2C-B HBr & Wash with Ice-Cold Et2O", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_glovebox_inert_catalyst": {
		"id": "contract_glovebox_inert_catalyst",
		"title": "Contract: Glovebox Deoxygenation & Catalyst Prep",
		"category": "Materials Engineering",
		"sector": "sector_containment",
		"requester": "KHI Advanced Catalysis Group",
		"min_level": { "skill": "containment", "level": 30 },
		"description": "Purge antechamber and regenerate copper catalyst bed. Achieve <0.1 ppm O2 and <0.1 ppm H2O to formulate pyrophoric palladium-BINAP asymmetric hydrogenation catalyst.",
		"xp_reward": { "containment": 1500, "materials_science": 1200, "automation": 800 },
		"reputation": { "ex_pharma": 40 },
		"credits_reward": 1800,
		"item_rewards": ["palladium_binap_chiral_catalyst", "oxygen_zirconia_sensor_probe"],
		"status": "available",
		"objectives": [
			{ "id": "purge_antechamber", "title": "Execute 3x Antechamber Vacuum/Refill Cycle", "current": 0.0, "target": 3.0, "is_done": false },
			{ "id": "verify_atmosphere", "title": "Sensors Confirm O2 < 0.1 ppm & H2O < 0.1 ppm", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "weigh_pyrophoric", "title": "Weigh & Seal Pyrophoric Catalyst Aliquot", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_cyclotron_isotope_harvest": {
		"id": "contract_cyclotron_isotope_harvest",
		"title": "Contract: Fluorine-18 Cyclotron Target Extraction",
		"category": "Radiochemistry",
		"sector": "sector_containment",
		"requester": "Positron Emission Tomography Consortium",
		"min_level": { "skill": "radiochemistry", "level": 40 },
		"description": "Irradiate [18O]H2O target in cyclotron with 18 MeV protons. Remote-transfer [18F]fluoride to hot cell module and synthesize 2-deoxy-2-[18F]fluoro-D-glucose (18F-FDG).",
		"xp_reward": { "radiochemistry": 2500, "nuclear_engineering": 2000 },
		"reputation": { "academic": 50, "ex_pharma": 30 },
		"credits_reward": 3500,
		"item_rewards": ["lead_transport_pig_heavy", "quaternary_ammonium_qma_cartridge"],
		"status": "available",
		"objectives": [
			{ "id": "proton_irradiation", "title": "Verify Target Irradiated (Beam Current 40 µA)", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "hot_cell_transfer", "title": "Operate Manipulator to Elute [18F] via QMA Cartridge", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "decay_corrected_yield", "title": "Confirm Radiochemical Purity > 98.5%", "current": 0.0, "target": 1.0, "is_done": false }
		]
	},
	"contract_emergency_hf_spill_drill": {
		"id": "contract_emergency_hf_spill_drill",
		"title": "Contract: Emergency Hydrofluoric Acid Spill Remediation",
		"category": "Safety Drill",
		"sector": "sector_atrium",
		"requester": "Institutional Safety Board",
		"min_level": { "skill": "lab_safety", "level": 30 },
		"description": "Simulated breach of 48% HF container. Sound klaxon, don neoprene gloves and full-face respirator, deploy calcium gluconate neutralizer, and verify zero fluoride ions.",
		"xp_reward": { "lab_safety": 2000, "toxicology": 1500, "environmental_science": 1000 },
		"reputation": { "academic": 40, "ex_pharma": 40 },
		"credits_reward": 2200,
		"item_rewards": ["calcium_gluconate_dispenser_auto", "hf_resistant_pfa_beaker_set"],
		"status": "available",
		"objectives": [
			{ "id": "evacuation_klaxon", "title": "Trigger Automated Sector Containment Airlock", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "neutralize_spill", "title": "Apply Calcium Carbonate/Gluconate Neutralizing Powder", "current": 0.0, "target": 1.0, "is_done": false },
			{ "id": "verify_clearance", "title": "Fluoride Ion-Selective Electrode Reads < 0.01 ppm", "current": 0.0, "target": 1.0, "is_done": false }
		]
	}
}

# =============================================================================
# RUNTIME STATE
# =============================================================================

var current_sector_id: String = "sector_atrium"
var active_contract_id: String = ""
var unlocked_sectors: Array[String] = ["sector_atrium", "sector_underground"]
var completed_contracts: Array[String] = []
var player_credits: int = 1000

func _ready() -> void:
	_check_sector_unlocks()
	_connect_progression_listeners()


func _connect_progression_listeners() -> void:
	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr:
		if skill_mgr.has_signal("skill_leveled_up"):
			skill_mgr.skill_leveled_up.connect(func(skill_id: String, new_lvl: int):
				_on_skill_leveled_up(skill_id, new_lvl)
			)


# =============================================================================
# SECTOR & FAST TRAVEL MANAGEMENT
# =============================================================================

func get_current_sector() -> Dictionary:
	return sectors.get(current_sector_id, {})


func get_all_sectors() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for sec_id in sectors:
		var sec = sectors[sec_id].duplicate(true)
		sec["unlocked"] = is_sector_unlocked(sec_id)
		sec["is_current"] = (sec_id == current_sector_id)
		result.append(sec)
	return result


func is_sector_unlocked(sector_id: String) -> bool:
	if not sectors.has(sector_id):
		return false
	if sector_id in unlocked_sectors:
		return true

	var sec = sectors[sector_id]
	if sec.get("unlocked_by_default", false):
		return true

	var req = sec.get("unlock_requirement", {})
	if req.is_empty():
		return true

	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr:
		var skill_name = req.get("skill", "")
		var req_lvl = int(req.get("level", 1))
		return skill_mgr.get_skill_level(skill_name) >= req_lvl

	return false


func _check_sector_unlocks() -> void:
	for sec_id in sectors:
		if not sec_id in unlocked_sectors and is_sector_unlocked(sec_id):
			unlocked_sectors.append(sec_id)
			sector_unlocked.emit(sec_id, sectors[sec_id])


func fast_travel_to_sector(target_sector_id: String) -> bool:
	if not sectors.has(target_sector_id):
		return false
	if not is_sector_unlocked(target_sector_id):
		return false

	var prev = current_sector_id
	current_sector_id = target_sector_id
	sector_entered.emit(target_sector_id, prev)
	fast_travel_completed.emit(target_sector_id)

	# Transition to target lab scene
	var scene_path = sectors[target_sector_id].get("scene_path", "")
	if scene_path != "" and ResourceLoader.exists(scene_path):
		var tree = get_tree()
		if tree:
			tree.change_scene_to_file(scene_path)
	return true


func transit_to_sector(target_sector_id: String) -> Dictionary:
	if not sectors.has(target_sector_id):
		return {"success": false, "error": "Unknown sector: %s" % target_sector_id}
	if not target_sector_id in unlocked_sectors:
		unlocked_sectors.append(target_sector_id)
		sector_unlocked.emit(target_sector_id, sectors[target_sector_id])
	var prev = current_sector_id
	current_sector_id = target_sector_id
	sector_entered.emit(target_sector_id, prev)
	fast_travel_completed.emit(target_sector_id)
	return {"success": true, "sector": sectors[target_sector_id], "prev_sector": prev}


# =============================================================================
# CONTRACT / SIDE QUEST MANAGEMENT
# =============================================================================

func get_available_contracts() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for cid in contracts:
		var c = contracts[cid]
		if c.get("status", "") == "available" and _is_contract_eligible(c):
			result.append(c.duplicate(true))
	return result


func _is_contract_eligible(c: Dictionary) -> bool:
	var min_req = c.get("min_level", {})
	if min_req.is_empty():
		return true
	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr:
		var skill_name = min_req.get("skill", "")
		var lvl = int(min_req.get("level", 1))
		return skill_mgr.get_skill_level(skill_name) >= lvl
	return true


func accept_contract(contract_id: String) -> bool:
	if not contracts.has(contract_id):
		return false
	var c = contracts[contract_id]
	if not _is_contract_eligible(c):
		return false

	active_contract_id = contract_id
	c["status"] = "in_progress"
	contract_accepted.emit(contract_id, c)
	return true


func start_contract(contract_id: String) -> bool:
	return accept_contract(contract_id)


func update_contract_objective(contract_id: String, objective_id: String, amount: float = 1.0) -> bool:
	return progress_contract_objective(contract_id, objective_id, amount)


func is_contract_complete(contract_id: String) -> bool:
	if not contracts.has(contract_id):
		return false
	var c = contracts[contract_id]
	if c.get("status", "") == "completed" or c.get("status", "") == "ready_to_claim":
		return true
	var objectives = c.get("objectives", [])
	if objectives.is_empty():
		return false
	for obj in objectives:
		if not obj.get("is_done", false):
			return false
	return true


func claim_contract_rewards(contract_id: String) -> Dictionary:
	if not contracts.has(contract_id):
		return {"success": false, "error": "Contract not found"}
	var c = contracts[contract_id]
	if not is_contract_complete(contract_id):
		return {"success": false, "error": "Objectives not complete"}

	c["status"] = "completed"
	if not contract_id in completed_contracts:
		completed_contracts.append(contract_id)

	var credits = int(c.get("credits_reward", 0))
	player_credits += credits

	var skill_mgr = get_node_or_null("/root/SkillManager")
	if not skill_mgr and get_tree() and get_tree().root:
		skill_mgr = get_tree().root.get_node_or_null("SkillManager")
	if skill_mgr and c.has("xp_reward"):
		for skill_name in c.xp_reward:
			var xp_val = int(c.xp_reward[skill_name])
			if skill_mgr.has_method("add_xp"):
				skill_mgr.add_xp(skill_name, xp_val)
			elif skill_mgr.has_method("grant_skill_xp"):
				skill_mgr.grant_skill_xp(skill_name, xp_val, "contract:" + contract_id)

	var inv_mgr = get_node_or_null("/root/InventoryManager")
	if not inv_mgr and get_tree() and get_tree().root:
		inv_mgr = get_tree().root.get_node_or_null("InventoryManager")
	if inv_mgr and c.has("item_rewards"):
		for item_id in c.item_rewards:
			inv_mgr.add_item(item_id, 1)

	if active_contract_id == contract_id:
		active_contract_id = ""

	contract_completed.emit(contract_id, {
		"credits": credits,
		"xp": c.get("xp_reward", {}),
		"items": c.get("item_rewards", [])
	})
	return {
		"success": true,
		"credits": credits,
		"xp": c.get("xp_reward", {}),
		"items": c.get("item_rewards", [])
	}


func progress_contract_objective(contract_id: String, objective_id: String, amount: float = 1.0) -> bool:
	if not contracts.has(contract_id):
		return false
	var c = contracts[contract_id]
	if c.get("status", "") != "in_progress":
		return false

	var objectives = c.get("objectives", [])
	var all_done = true
	var found = false

	for obj in objectives:
		if obj.id == objective_id and not obj.is_done:
			obj.current = minf(obj.current + amount, obj.target)
			if is_equal_approx(obj.current, obj.target) or obj.current >= obj.target:
				obj.is_done = true
			contract_progressed.emit(contract_id, objective_id, obj.current, obj.target)
			found = true
		if not obj.is_done:
			all_done = false

	if all_done:
		c["status"] = "ready_to_claim"

	return found


func _complete_contract(contract_id: String) -> void:
	if not contracts.has(contract_id):
		return
	var c = contracts[contract_id]
	c["status"] = "completed"
	if not contract_id in completed_contracts:
		completed_contracts.append(contract_id)

	# Grant XP rewards
	var skill_mgr = get_node_or_null("/root/SkillManager")
	if skill_mgr and c.has("xp_reward"):
		for skill_name in c.xp_reward:
			var xp_val = int(c.xp_reward[skill_name])
			skill_mgr.grant_skill_xp(skill_name, xp_val, "contract:" + contract_id)

	# Grant Credits
	var credits = int(c.get("credits_reward", 0))
	player_credits += credits

	# Grant Item rewards
	var inv_mgr = get_node_or_null("/root/InventoryManager")
	if inv_mgr and c.has("item_rewards"):
		for item_id in c.item_rewards:
			inv_mgr.add_item(item_id, 1)

	if active_contract_id == contract_id:
		active_contract_id = ""

	contract_completed.emit(contract_id, {
		"credits": credits,
		"xp": c.get("xp_reward", {}),
		"items": c.get("item_rewards", [])
	})


# =============================================================================
# MASTERY PROGRESSION HOOKS (Action-based skill loops & Level 99 Milestones)
# =============================================================================

func _on_skill_leveled_up(skill_id: String, new_lvl: int) -> void:
	_check_sector_unlocks()

	# Check classic progression milestones (25, 50, 75, 92 halfway, 99 Master, 120 Transcendent)
	match new_lvl:
		25:
			mastery_milestone_reached.emit(skill_id, 25, "apprentice_lab_token_" + skill_id)
		50:
			mastery_milestone_reached.emit(skill_id, 50, "adept_lab_token_" + skill_id)
		75:
			mastery_milestone_reached.emit(skill_id, 75, "expert_lab_token_" + skill_id)
		92:
			# Level 92 is precisely 50% of Level 99 XP in classic exponential mastery progression
			mastery_milestone_reached.emit(skill_id, 92, "halfway_crest_" + skill_id)
		99:
			var regalia_item = "regalia_" + skill_id
			mastery_milestone_reached.emit(skill_id, 99, regalia_item)
			var inv = get_node_or_null("/root/InventoryManager")
			if inv:
				inv.add_item(regalia_item, 1)
		120:
			mastery_milestone_reached.emit(skill_id, 120, "transcendent_trim_" + skill_id)


# =============================================================================
# SERIALIZATION & PERSISTENCE
# =============================================================================

func to_dict() -> Dictionary:
	return {
		"current_sector_id": current_sector_id,
		"unlocked_sectors": unlocked_sectors.duplicate(),
		"active_contract_id": active_contract_id,
		"completed_contracts": completed_contracts.duplicate(),
		"player_credits": player_credits
	}


func from_dict(data: Dictionary) -> void:
	current_sector_id = data.get("current_sector_id", "sector_atrium")
	unlocked_sectors = Array(data.get("unlocked_sectors", ["sector_atrium", "sector_underground"])).map(func(v): return str(v))
	active_contract_id = data.get("active_contract_id", "")
	completed_contracts = Array(data.get("completed_contracts", [])).map(func(v): return str(v))
	player_credits = int(data.get("player_credits", 1000))
