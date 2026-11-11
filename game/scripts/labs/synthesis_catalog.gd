# Athanor Ascension — Synthesis Protocol Catalog
# Bridges the offline literature JSON databases (PiHKAL, TiHKAL, Industrial APIs)
# with the interactive synthesis terminal and stoichiometric chemistry engine.
class_name SynthesisCatalog
extends RefCounted

const PIHKAL_PATH: String = "res://data/synthesis/pihkal_complete.json"
const TIHKAL_PATH: String = "res://data/synthesis/tihkal_complete.json"

static var _catalog_cache: Dictionary = {}
static var _protocols_by_id: Dictionary = {}
static var _categories: Array[String] = []


static func get_categories() -> Array[String]:
	_ensure_loaded()
	return _categories


static func get_protocols_in_category(cat: String) -> Array[Dictionary]:
	_ensure_loaded()
	var list: Array[Dictionary] = []
	var cat_data: Array = _catalog_cache.get(cat, [])
	for item in cat_data:
		if item is Dictionary:
			list.append(item)
	return list


static func get_protocol(id: String) -> Dictionary:
	_ensure_loaded()
	if _protocols_by_id.has(id):
		return _protocols_by_id[id]
	# Fallback to default aspirin
	if _protocols_by_id.has("aspirin"):
		return _protocols_by_id["aspirin"]
	return _make_aspirin_protocol()


static func get_all_protocol_ids() -> Array[String]:
	_ensure_loaded()
	var ids: Array[String] = []
	for k in _protocols_by_id.keys():
		ids.append(str(k))
	return ids


static func _ensure_loaded() -> void:
	if not _catalog_cache.is_empty():
		return

	_catalog_cache = {}
	_protocols_by_id = {}
	_categories = ["Industrial APIs", "PiHKAL Phenethylamines", "TiHKAL Tryptamines"]

	# 1. Load built-in Industrial APIs
	var industrial: Array[Dictionary] = [
		_make_aspirin_protocol(),
		_make_paracetamol_protocol(),
		_make_caffeine_protocol(),
		_make_indigo_protocol(),
		_make_benzocaine_protocol()
	]
	_catalog_cache["Industrial APIs"] = industrial
	for p in industrial:
		_protocols_by_id[p["id"]] = p

	# 2. Load PiHKAL compounds
	var pihkal_list := _load_json_protocols(PIHKAL_PATH, "PiHKAL Phenethylamines")
	_catalog_cache["PiHKAL Phenethylamines"] = pihkal_list
	for p in pihkal_list:
		_protocols_by_id[p["id"]] = p

	# 3. Load TiHKAL compounds
	var tihkal_list := _load_json_protocols(TIHKAL_PATH, "TiHKAL Tryptamines")
	_catalog_cache["TiHKAL Tryptamines"] = tihkal_list
	for p in tihkal_list:
		_protocols_by_id[p["id"]] = p


static func _load_json_protocols(file_path: String, category: String) -> Array[Dictionary]:
	var list: Array[Dictionary] = []
	if not FileAccess.file_exists(file_path):
		return list

	var file := FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		return list

	var text := file.get_as_text()
	file.close()

	var test_json := JSON.new()
	var err := test_json.parse(text)
	if err != OK:
		return list

	var root_data = test_json.data
	if not (root_data is Dictionary) or not root_data.has("compounds"):
		return list

	var compounds: Array = root_data.get("compounds", [])
	for c in compounds:
		if not (c is Dictionary):
			continue
		var proto := _convert_compound_to_protocol(c, category)
		list.append(proto)

	return list


static func _convert_compound_to_protocol(c: Dictionary, category: String) -> Dictionary:
	var cid: String = str(c.get("compound_id", "unknown"))
	var cname: String = str(c.get("name", "Unknown Compound"))
	var chem_name: String = str(c.get("chemical_name", cname))
	var mw: float = float(c.get("molecular_weight", 200.0))
	var mp: float = float(c.get("mp_c", 150.0))
	var rf: float = float(c.get("tlc_rf", 0.40))
	var cas: String = str(c.get("cas_number", "N/A"))
	var formula: String = str(c.get("formula", "C10H15N"))
	var desc: String = str(c.get("description", ""))

	var routes: Array = c.get("routes", [])
	var first_route: Dictionary = routes[0] if not routes.is_empty() and routes[0] is Dictionary else {}
	var steps: Array = first_route.get("steps", [])
	var first_step: Dictionary = steps[0] if not steps.is_empty() and steps[0] is Dictionary else {}
	var reagents: Array = first_step.get("reagents", [])
	var cond: Dictionary = first_step.get("conditions", {})

	# Reagent A (limiting precursor)
	var rA: Dictionary = reagents[0] if reagents.size() > 0 and reagents[0] is Dictionary else {}
	var rA_name: String = str(rA.get("name", "Primary Precursor"))
	var rA_amount: float = float(rA.get("amount", 10.0))
	var rA_unit: String = str(rA.get("unit", "g"))
	var rA_mw: float = mw * 0.75  # realistic precursor MW ratio

	# Reagent B (reagent / reactant)
	var rB: Dictionary = reagents[1] if reagents.size() > 1 and reagents[1] is Dictionary else {}
	var rB_name: String = str(rB.get("name", "Coupling Reagent"))
	var rB_amount: float = float(rB.get("amount", 12.0))
	var rB_unit: String = str(rB.get("unit", "mL"))
	var rB_mw: float = 65.0
	var rB_density: float = 1.15

	var opt_temp: float = float(cond.get("temperature_c", 75.0))
	var opt_dur: float = float(cond.get("duration_min", 30.0))

	return {
		"id": cid,
		"name": cname,
		"chemical_name": chem_name,
		"category": category,
		"code": "SHULGIN-%s" % cid.to_upper(),
		"cas": cas,
		"mw": mw,
		"formula": formula,
		"description": desc,
		"reaction_title": "%s → %s" % [rA_name, cname],
		"reagent_a": {
			"id": str(rA.get("reagent_id", "reagent_a")),
			"name": rA_name,
			"unit": rA_unit,
			"mw": rA_mw,
			"default": rA_amount,
			"min": maxf(1.0, rA_amount * 0.5),
			"max": rA_amount * 2.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": str(rB.get("reagent_id", "reagent_b")),
			"name": rB_name,
			"unit": rB_unit,
			"mw": rB_mw,
			"density": rB_density,
			"default": rB_amount,
			"min": maxf(1.0, rB_amount * 0.5),
			"max": rB_amount * 2.5,
			"step": 0.1,
			"decimals": 1
		},
		"catalyst": {
			"name": "Catalyst / Acid Drops",
			"unit": "drops",
			"default": 5,
			"min": 0,
			"max": 10,
			"optimal": 5
		},
		"reflux": {
			"temp_optimal_low": maxf(0.0, opt_temp - 8.0),
			"temp_optimal_high": opt_temp + 8.0,
			"temp_degrade": opt_temp + 18.0,
			"temp_polymerize": opt_temp + 35.0,
			"default_temp": opt_temp,
			"temp_min": maxf(0.0, opt_temp - 30.0),
			"temp_max": opt_temp + 50.0,
			"optimal_min": opt_dur,
			"default_min": opt_dur,
			"duration_min": maxf(5.0, opt_dur * 0.25),
			"duration_max": opt_dur * 2.5
		},
		"workup": {
			"ice_c": 2.0,
			"water_ml": 50.0,
			"ethanol_ml": 20.0,
			"seeded": true
		},
		"analytical": {
			"mp_pure": mp,
			"mp_tolerance": 3.0,
			"tlc_rf": rf,
			"purity_pass": 95.0,
			"yield_pass_g": rA_amount * (mw / rA_mw) * 0.65
		},
		"hazards": [
			{"code": "GHS02", "text": "flammable solvents / reagents"},
			{"code": "GHS06", "text": "toxic / bioactive compound"},
			{"code": "GHS07", "text": "irritant / exothermic addition"},
			{"code": "GHS08", "text": "respiratory / neurological active"}
		]
	}


static func _make_aspirin_protocol() -> Dictionary:
	return {
		"id": "aspirin",
		"name": "Acetylsalicylic acid",
		"chemical_name": "2-Acetoxybenzoic acid",
		"category": "Industrial APIs",
		"code": "SYN-01",
		"cas": "50-78-2",
		"mw": 180.16,
		"formula": "C9H8O4",
		"description": "Salicylic acid + acetic anhydride → acetylsalicylic acid + acetic acid. One equivalent each; anhydride charged at 1.4–1.6 eq so acid is limiting.",
		"reaction_title": "Salicylic acid + acetic anhydride → acetylsalicylic acid",
		"reagent_a": {
			"id": "salicylic_acid",
			"name": "Salicylic acid",
			"unit": "g",
			"mw": 138.12,
			"default": 13.8,
			"min": 10.0,
			"max": 17.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": "acetic_anhydride",
			"name": "Acetic anhydride",
			"unit": "mL",
			"mw": 102.09,
			"density": 1.082,
			"default": 14.2,
			"min": 8.0,
			"max": 22.0,
			"step": 0.1,
			"decimals": 1
		},
		"catalyst": {
			"name": "H₂SO₄ catalyst",
			"unit": "drops",
			"default": 5,
			"min": 0,
			"max": 8,
			"optimal": 5
		},
		"reflux": {
			"temp_optimal_low": 65.0,
			"temp_optimal_high": 75.0,
			"temp_degrade": 85.0,
			"temp_polymerize": 100.0,
			"default_temp": 70.0,
			"temp_min": 40.0,
			"temp_max": 110.0,
			"optimal_min": 20.0,
			"default_min": 20.0,
			"duration_min": 5.0,
			"duration_max": 40.0
		},
		"workup": {
			"ice_c": 2.0,
			"water_ml": 30.0,
			"ethanol_ml": 15.0,
			"seeded": true
		},
		"analytical": {
			"mp_pure": 135.5,
			"mp_tolerance": 2.5,
			"tlc_rf": 0.45,
			"purity_pass": 95.0,
			"yield_pass_g": 12.0
		},
		"hazards": [
			{"code": "GHS05", "text": "corrosive (anhydride, H₂SO₄)"},
			{"code": "GHS07", "text": "harmful / lachrymator"},
			{"code": "GHS08", "text": "respiratory sensitisation"}
		]
	}


static func _make_paracetamol_protocol() -> Dictionary:
	return {
		"id": "paracetamol",
		"name": "Paracetamol (APAP)",
		"chemical_name": "N-(4-Hydroxyphenyl)acetamide",
		"category": "Industrial APIs",
		"code": "SYN-02",
		"cas": "103-90-2",
		"mw": 151.16,
		"formula": "C8H9NO2",
		"description": "4-Aminophenol + acetic anhydride → paracetamol + acetic acid. Nucleophilic acylation of primary aromatic amine over phenolic OH.",
		"reaction_title": "4-Aminophenol + acetic anhydride → paracetamol",
		"reagent_a": {
			"id": "4_aminophenol",
			"name": "4-Aminophenol",
			"unit": "g",
			"mw": 109.13,
			"default": 10.9,
			"min": 5.0,
			"max": 16.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": "acetic_anhydride",
			"name": "Acetic anhydride",
			"unit": "mL",
			"mw": 102.09,
			"density": 1.082,
			"default": 11.0,
			"min": 6.0,
			"max": 20.0,
			"step": 0.1,
			"decimals": 1
		},
		"catalyst": {
			"name": "Glacial acetic acid / drops",
			"unit": "drops",
			"default": 4,
			"min": 0,
			"max": 8,
			"optimal": 4
		},
		"reflux": {
			"temp_optimal_low": 80.0,
			"temp_optimal_high": 90.0,
			"temp_degrade": 105.0,
			"temp_polymerize": 125.0,
			"default_temp": 85.0,
			"temp_min": 50.0,
			"temp_max": 130.0,
			"optimal_min": 15.0,
			"default_min": 15.0,
			"duration_min": 5.0,
			"duration_max": 35.0
		},
		"workup": {
			"ice_c": 3.0,
			"water_ml": 40.0,
			"ethanol_ml": 10.0,
			"seeded": true
		},
		"analytical": {
			"mp_pure": 169.5,
			"mp_tolerance": 2.0,
			"tlc_rf": 0.52,
			"purity_pass": 96.0,
			"yield_pass_g": 11.5
		},
		"hazards": [
			{"code": "GHS07", "text": "harmful if swallowed"},
			{"code": "GHS08", "text": "suspected mutagenic effect"}
		]
	}


static func _make_caffeine_protocol() -> Dictionary:
	return {
		"id": "caffeine",
		"name": "Caffeine Isolation",
		"chemical_name": "1,3,7-Trimethylxanthine",
		"category": "Industrial APIs",
		"code": "SYN-03",
		"cas": "58-08-2",
		"mw": 194.19,
		"formula": "C8H10N4O2",
		"description": "Solid-liquid extraction of raw botanical material followed by base partition and cold-finger vacuum sublimation.",
		"reaction_title": "Crude botanical extract → pure caffeine sublimation",
		"reagent_a": {
			"id": "crude_extract",
			"name": "Crude extract solids",
			"unit": "g",
			"mw": 194.19,
			"default": 15.0,
			"min": 5.0,
			"max": 25.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": "dichloromethane",
			"name": "Dichloromethane (DCM)",
			"unit": "mL",
			"mw": 84.93,
			"density": 1.326,
			"default": 25.0,
			"min": 10.0,
			"max": 50.0,
			"step": 1.0,
			"decimals": 0
		},
		"catalyst": {
			"name": "Na2CO3 base wash drops",
			"unit": "drops",
			"default": 5,
			"min": 0,
			"max": 10,
			"optimal": 5
		},
		"reflux": {
			"temp_optimal_low": 40.0,
			"temp_optimal_high": 45.0,
			"temp_degrade": 60.0,
			"temp_polymerize": 80.0,
			"default_temp": 42.0,
			"temp_min": 25.0,
			"temp_max": 90.0,
			"optimal_min": 25.0,
			"default_min": 25.0,
			"duration_min": 10.0,
			"duration_max": 50.0
		},
		"workup": {
			"ice_c": 0.0,
			"water_ml": 20.0,
			"ethanol_ml": 10.0,
			"seeded": false
		},
		"analytical": {
			"mp_pure": 236.0,
			"mp_tolerance": 3.0,
			"tlc_rf": 0.38,
			"purity_pass": 97.0,
			"yield_pass_g": 3.2
		},
		"hazards": [
			{"code": "GHS07", "text": "moderate oral toxicity"},
			{"code": "GHS08", "text": "suspected carcinogen (DCM extraction solvent)"}
		]
	}


static func _make_indigo_protocol() -> Dictionary:
	return {
		"id": "indigo",
		"name": "Indigo Dye",
		"chemical_name": "2-(1,3-Dihydro-3-oxo-2H-indol-2-ylidene)-1,2-dihydro-3H-indol-3-one",
		"category": "Industrial APIs",
		"code": "SYN-04",
		"cas": "482-89-3",
		"mw": 262.26,
		"formula": "C16H10N2O2",
		"description": "Baeyer-Drewson synthesis: 2-nitrobenzaldehyde + acetone in aqueous NaOH aldol condensation followed by oxidative dimerization.",
		"reaction_title": "2-Nitrobenzaldehyde + acetone → indigo precipitate",
		"reagent_a": {
			"id": "2_nitrobenzaldehyde",
			"name": "2-Nitrobenzaldehyde",
			"unit": "g",
			"mw": 151.12,
			"default": 10.0,
			"min": 4.0,
			"max": 18.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": "acetone",
			"name": "Acetone solvent/reagent",
			"unit": "mL",
			"mw": 58.08,
			"density": 0.784,
			"default": 15.0,
			"min": 8.0,
			"max": 30.0,
			"step": 0.5,
			"decimals": 1
		},
		"catalyst": {
			"name": "1M NaOH catalyst drops",
			"unit": "drops",
			"default": 6,
			"min": 0,
			"max": 10,
			"optimal": 6
		},
		"reflux": {
			"temp_optimal_low": 22.0,
			"temp_optimal_high": 30.0,
			"temp_degrade": 50.0,
			"temp_polymerize": 70.0,
			"default_temp": 25.0,
			"temp_min": 15.0,
			"temp_max": 80.0,
			"optimal_min": 15.0,
			"default_min": 15.0,
			"duration_min": 5.0,
			"duration_max": 30.0
		},
		"workup": {
			"ice_c": 4.0,
			"water_ml": 50.0,
			"ethanol_ml": 20.0,
			"seeded": false
		},
		"analytical": {
			"mp_pure": 390.0,
			"mp_tolerance": 10.0,
			"tlc_rf": 0.65,
			"purity_pass": 92.0,
			"yield_pass_g": 6.8
		},
		"hazards": [
			{"code": "GHS02", "text": "highly flammable acetone"},
			{"code": "GHS07", "text": "skin and eye irritant"}
		]
	}


static func _make_benzocaine_protocol() -> Dictionary:
	return {
		"id": "benzocaine",
		"name": "Benzocaine",
		"chemical_name": "Ethyl 4-aminobenzoate",
		"category": "Industrial APIs",
		"code": "SYN-05",
		"cas": "94-09-7",
		"mw": 165.19,
		"formula": "C9H11NO2",
		"description": "Fischer esterification: 4-aminobenzoic acid (PABA) + absolute ethanol with catalytic sulfuric acid under Dean-Stark water removal.",
		"reaction_title": "4-Aminobenzoic acid + ethanol → ethyl 4-aminobenzoate",
		"reagent_a": {
			"id": "paba",
			"name": "4-Aminobenzoic acid",
			"unit": "g",
			"mw": 137.14,
			"default": 13.7,
			"min": 8.0,
			"max": 20.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": "ethanol_abs",
			"name": "Absolute ethanol",
			"unit": "mL",
			"mw": 46.07,
			"density": 0.789,
			"default": 35.0,
			"min": 20.0,
			"max": 60.0,
			"step": 1.0,
			"decimals": 0
		},
		"catalyst": {
			"name": "Concentrated H₂SO₄ drops",
			"unit": "drops",
			"default": 6,
			"min": 0,
			"max": 10,
			"optimal": 6
		},
		"reflux": {
			"temp_optimal_low": 76.0,
			"temp_optimal_high": 80.0,
			"temp_degrade": 95.0,
			"temp_polymerize": 115.0,
			"default_temp": 78.0,
			"temp_min": 50.0,
			"temp_max": 120.0,
			"optimal_min": 45.0,
			"default_min": 45.0,
			"duration_min": 15.0,
			"duration_max": 75.0
		},
		"workup": {
			"ice_c": 2.0,
			"water_ml": 50.0,
			"ethanol_ml": 15.0,
			"seeded": true
		},
		"analytical": {
			"mp_pure": 90.0,
			"mp_tolerance": 2.0,
			"tlc_rf": 0.48,
			"purity_pass": 95.0,
			"yield_pass_g": 12.8
		},
		"hazards": [
			{"code": "GHS05", "text": "acid burns during initial charge"},
			{"code": "GHS07", "text": "local anesthetic skin desensitisation"}
		]
	}
