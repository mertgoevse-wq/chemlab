# Athanor Ascension — Python Synthesis Bridge
# Bridges the offline Python synthesis database with the interactive Godot synthesis terminal
# Author: Athanor Ascension Team, 2024
class_name PythonSynthesisBridge
extends RefCounted

const PYTHON_EXECUTABLE: String = "python"  # Adjust if using specific venv path
const BRIDGE_SCRIPT_PATH: String = "C:/Users/Win11 Pro/Desktop/chemlab/src/chemlab/simulation/total_syntheses.py"

# Cache for loaded protocols to avoid repeated Python calls
static var _cached_protocols: Dictionary = {}
static var _categories_cache: Array[String] = []
static var _protocols_by_id_cache: Dictionary = {}


static func is_python_bridge_available() -> bool:
	# Check if Python and the bridge script are available
	var output := []
	var exit_code := OS.execute(PYTHON_EXECUTABLE, ["-c", "import sys; print(sys.version_info[0])"], output, true)
	if exit_code != 0:
		print("Python not found or not accessible")
		return false

	var file := FileAccess.open(BRIDGE_SCRIPT_PATH, FileAccess.READ)
	if file == null:
		print("Python synthesis bridge script not found at: " + BRIDGE_SCRIPT_PATH)
		return false
	file.close()

	return true


static func load_all_protocols() -> bool:
	if not is_python_bridge_available():
		return false

	# Execute Python script to get all protocols
	var output := []
	var python_cmd := """
import json
import sys
sys.path.insert(0, 'C:/Users/Win11 Pro/Desktop/chemlab/src')
from chemlab.simulation.total_syntheses import SynthesisRegistry

registry = SynthesisRegistry()
protocols = {}
for pid in registry.list_available_protocols():
    protocol = registry.get_protocol(pid)
    protocols[pid] = {
        'id': protocol.id,
        'name': protocol.target_molecule,
        'cas': protocol.cas_number,
        'mw': protocol.molar_mass_g_mol,
        'description': protocol.description,
        'initial_reagents': list(protocol.initial_reagents),
        'catalysts': list(protocol.catalysts),
        'stages': [{
            'number': stage.stage_number,
            'name': stage.name,
            'description': stage.description,
            'technique': stage.technique,
            'inputs': list(stage.required_inputs),
            'temperature': stage.temperature_target_c,
            'duration': stage.duration_s,
            'safety': stage.safety_notes
        } for stage in protocol.stages],
        'color': protocol.final_color_rgb,
        'sublimation_point': protocol.sublimation_point_c,
        'produces_precipitate': protocol.produces_colored_precipitate
    }

print(json.dumps(protocols, indent=2))
"""

	var exit_code := OS.execute(PYTHON_EXECUTABLE, ["-c", python_cmd], output, true)

	if exit_code != 0 or output.is_empty():
		print("Failed to execute Python synthesis bridge")
		return false

	var json_text := PackedStringArray(output).join("")
	var json_parser := JSON.new()
	var err := json_parser.parse(json_text)

	if err != OK:
		print("Failed to parse JSON from Python bridge")
		return false

	var protocols_data = json_parser.data
	if not (protocols_data is Dictionary):
		print("Invalid protocol data format from Python bridge")
		return false

	# Cache the protocols
	_cached_protocols = protocols_data

	# Build categories from protocol types
	var categories_set := {}
	for protocol_id in _cached_protocols:
		var protocol = _cached_protocols[protocol_id]
		var category := _infer_category_from_protocol(protocol)
		categories_set[category] = true

	_categories_cache = categories_set.keys()
	_categories_cache.sort()

	_protocols_by_id_cache = _cached_protocols.duplicate()

	print("Loaded " + str(_cached_protocols.size()) + " synthesis protocols from Python database")
	return true


static func _infer_category_from_protocol(protocol: Dictionary) -> String:
	var name: String = protocol.get("name", "").to_lower()
	var desc: String = protocol.get("description", "").to_lower()

	if "aspirin" in name or "acetylsalicylic" in desc:
		return "Industrial APIs"
	elif "paracetamol" in name or "acetaminophen" in desc:
		return "Industrial APIs"
	elif "caffeine" in name:
		return "Natural Product Isolation & Extractions"
	elif "indigo" in name:
		return "Classical Organic & Dyes (Vogel)"
	elif "benzocaine" in name:
		return "Industrial APIs"
	elif "tropinone" in name:
		return "Tropane Alkaloids & Classic Syntheses"
	elif "atropine" in name:
		return "Tropane Alkaloids & Classic Syntheses"
	elif "extraction" in desc or "isolation" in desc:
		return "Natural Product Isolation & Extractions"
	elif "alkaloid" in desc:
		return "Tropane Alkaloids & Classic Syntheses"
	elif "dye" in desc or "pigment" in desc:
		return "Classical Organic & Dyes (Vogel)"
	else:
		return "Python Database Protocols"


static func get_categories() -> Array[String]:
	if _categories_cache.is_empty():
		load_all_protocols()
	return _categories_cache


static func get_protocols_in_category(category: String) -> Array[Dictionary]:
	if _cached_protocols.is_empty():
		load_all_protocols()

	var protocols_in_category: Array[Dictionary] = []

	for protocol_id in _cached_protocols:
		var protocol = _cached_protocols[protocol_id]
		var protocol_category := _infer_category_from_protocol(protocol)

		if protocol_category == category:
			protocols_in_category.append(protocol)

	return protocols_in_category


static func get_protocol(protocol_id: String) -> Dictionary:
	if _cached_protocols.is_empty():
		load_all_protocols()

	var pid := protocol_id.to_lower()
	if _cached_protocols.has(pid):
		return _cached_protocols[pid]

	# Fallback to default if not found
	if _cached_protocols.has("aspirin"):
		return _cached_protocols["aspirin"]

	return {}


static func get_all_protocol_ids() -> Array[String]:
	if _cached_protocols.is_empty():
		load_all_protocols()
	return _cached_protocols.keys()


static func convert_python_to_godot_format(python_protocol: Dictionary) -> Dictionary:
	# Convert Python protocol format to Godot's expected format
	var stages: Array = python_protocol.get("stages", [])
	var first_stage: Dictionary = stages[0] if not stages.is_empty() else {}
	var reagents: Array = first_stage.get("inputs", [])

	var rA_name: String = reagents[0] if reagents.size() > 0 else "Precursor A"
	var rB_name: String = reagents[1] if reagents.size() > 1 else "Reagent B"

	var mw: float = python_protocol.get("mw", 200.0)
	var rA_mw: float = mw * 0.75  # Realistic precursor ratio
	var rB_mw: float = mw * 0.85  # Realistic reagent ratio

	return {
		"id": python_protocol.get("id", "python_protocol"),
		"name": python_protocol.get("name", "Python Protocol"),
		"chemical_name": python_protocol.get("name", ""),
		"category": _infer_category_from_protocol(python_protocol),
		"code": "PY-" + python_protocol.get("id", "unknown").to_upper(),
		"cas": python_protocol.get("cas", "N/A"),
		"mw": mw,
		"formula": "",  # Would need SMILES conversion
		"description": python_protocol.get("description", ""),
		"literature_reference": "Python Synthesis Database",
		"source": "Python Bridge",
		"reaction_title": rA_name + " → " + python_protocol.get("name", "Product"),
		"reagent_a": {
			"id": python_protocol.get("id", "") + "_reagent_a",
			"name": rA_name,
			"unit": "g",
			"mw": rA_mw,
			"default": 10.0,
			"min": 5.0,
			"max": 20.0,
			"step": 0.1,
			"decimals": 1
		},
		"reagent_b": {
			"id": python_protocol.get("id", "") + "_reagent_b",
			"name": rB_name,
			"unit": "mL",
			"mw": rB_mw,
			"density": 1.0,
			"default": 12.0,
			"min": 6.0,
			"max": 25.0,
			"step": 0.1,
			"decimals": 1
		},
		"catalyst": {
			"name": "Catalyst",
			"unit": "drops",
			"default": 5,
			"min": 0,
			"max": 10,
			"optimal": 5
		},
		"reflux": {
			"temp_optimal_low": 70.0,
			"temp_optimal_high": 80.0,
			"temp_degrade": 95.0,
			"temp_polymerize": 115.0,
			"default_temp": 75.0,
			"temp_min": 40.0,
			"temp_max": 130.0,
			"optimal_min": 30.0,
			"default_min": 30.0,
			"duration_min": 10.0,
			"duration_max": 60.0
		},
		"workup": {
			"ice_c": 2.0,
			"water_ml": 30.0,
			"ethanol_ml": 15.0,
			"seeded": true
		},
		"analytical": {
			"mp_pure": 150.0,
			"mp_tolerance": 3.0,
			"tlc_rf": 0.45,
			"purity_pass": 95.0,
			"yield_pass_g": 8.0
		},
		"hazards": [
			{"code": "GHS07", "text": "chemical reaction - use standard precautions"}
		]
	}
