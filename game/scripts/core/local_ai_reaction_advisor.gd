# Athanor Ascension — Local AI & Free Model Reaction Advisor
# Autoload: LocalAIReactionAdvisor
# Connects to:
# 1. Omniroute (http://localhost:20128/v1/chat/completions)
# 2. Ollama (http://localhost:11434/api/generate)
# 3. Free inference endpoints / local LLMs
# Features:
# - Real-time organic reaction forecasting & stoichiometry
# - 1H/13C NMR spectral elucidation & multiplet analysis
# - Interactive apparatus operation guidance
# - 100% Offline deterministic heuristic fallback library

extends Node

# =============================================================================
# SIGNALS
# =============================================================================

signal query_completed(query_id: String, result: Dictionary)
signal query_failed(query_id: String, error_message: String)
signal connection_status_changed(is_connected: bool, endpoint: String)

# =============================================================================
# CONFIGURATION
# =============================================================================

@export var omniroute_url: String = "http://127.0.0.1:20128/v1/chat/completions"
@export var ollama_url: String = "http://127.0.0.1:11434/api/generate"
@export var lm_studio_url: String = "http://127.0.0.1:1234/v1/chat/completions"
@export var preferred_model: String = "kc/kilo-auto/free"  # Omniroute free router or local model
@export var timeout_seconds: float = 2.5
@export var enable_local_ai: bool = true
@export var active_provider: String = "omniroute"  # omniroute | ollama | lm_studio | custom | offline

var _http_request: HTTPRequest
var _pending_queries: Dictionary = {}
var _is_ai_available: bool = false
var _query_counter: int = 0
var _last_latency_ms: float = 0.0

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	_http_request = HTTPRequest.new()
	_http_request.timeout = timeout_seconds
	add_child(_http_request)
	_http_request.request_completed.connect(_on_http_request_completed)

	# Probe local AI endpoints non-blockingly
	if enable_local_ai:
		_check_ai_availability()

# =============================================================================
# PUBLIC API - REACTION PREDICTION
# =============================================================================

func predict_reaction(reactants: Array, conditions: Dictionary = {}) -> Dictionary:
	# Build request payload
	var temp_c = float(conditions.get("temperature_c", 25.0))
	var solvent = str(conditions.get("solvent", "Ethanol"))
	var catalyst = str(conditions.get("catalyst", "none"))

	var query_id = "rxn_%d" % _query_counter
	_query_counter += 1

	# Try fast deterministic offline calculation first
	var offline_prediction = _compute_offline_reaction(reactants, temp_c, solvent, catalyst)

	if not enable_local_ai or not _is_ai_available:
		return offline_prediction

	# If local AI is configured, send asynchronous enhancement
	_send_ai_prompt(query_id, _format_reaction_prompt(reactants, temp_c, solvent, catalyst))
	return offline_prediction

# =============================================================================
# PUBLIC API - SPECTRAL ELUCIDATION
# =============================================================================

func elucidate_nmr_spectrum(peaks: Array, solvent: String = "CDCl3") -> Dictionary:
	# Deduce structural fragments from chemical shift & multiplet splitting
	var fragments: Array[Dictionary] = []
	for p in peaks:
		var ppm = float(p.get("ppm", 0.0))
		var mult = str(p.get("multiplicity", "s")).to_lower()
		var integ = int(p.get("integration", 1))

		var assignment = _assign_chemical_shift(ppm, mult, integ)
		fragments.append(assignment)

	return {
		"solvent": solvent,
		"analyzed_peaks_count": peaks.size(),
		"identified_fragments": fragments,
		"confidence_score": 0.94
	}

# =============================================================================
# PUBLIC API - APPARATUS GUIDANCE
# =============================================================================

func get_apparatus_guidance(apparatus_name: String, current_state: String) -> Dictionary:
	match apparatus_name.to_lower():
		"rotovap", "rotary_evaporator":
			return {
				"apparatus": "Rotary Evaporator",
				"recommended_bath_c": 45.0,
				"recommended_chiller_c": -5.0,
				"recommended_rpm": 120,
				"safety_check": "Ensure Keck clip is firmly seated before pulling vacuum to prevent flask detachment."
			}
		"schlenk_line":
			return {
				"apparatus": "Schlenk Line",
				"recommended_argon_psi": 15.0,
				"cold_trap": "Liquid Nitrogen (-196°C) is mandatory to protect rotary vane pump oil.",
				"purge_protocol": "Execute minimum 3x Evacuate-Refill cycles before pyrophoric reagent transfer."
			}
		"analytical_balance":
			return {
				"apparatus": "Analytical Balance (0.1 mg)",
				"draft_shield": "Keep all sliding glass panels closed during reading.",
				"tare_reminder": "Always tare with weighing paper or weighing boat in position."
			}
		"hplc":
			return {
				"apparatus": "HPLC Diode Array",
				"column": "C18 Reverse-Phase (4.6 x 150 mm, 5 µm)",
				"max_pressure_bar": 350.0,
				"flow_rate": "1.0 mL/min gradient, degassed mobile phases."
			}
		"glovebox":
			return {
				"apparatus": "Inert Atmosphere Glovebox",
				"o2_target_ppm": "< 0.1 ppm",
				"h2o_target_ppm": "< 0.1 ppm",
				"antechamber": "3x Automated vacuum-argon purge required before opening inner door."
			}
		_:
			return {
				"apparatus": apparatus_name,
				"safety_check": "Verify GHS hazard compatibility and wear proper PPE."
			}

# =============================================================================
# INTERNAL - OFFLINE DETERMINISTIC REACTION DATABASE
# =============================================================================

func _compute_offline_reaction(reactants: Array, temp_c: float, solvent: String, catalyst: String) -> Dictionary:
	var r_clean: Array[String] = []
	for r in reactants:
		r_clean.append(r.strip_edges().to_lower())

	# Case 1: Fischer Esterification (Salicylic Acid + Acetic Anhydride -> Aspirin)
	if (_contains_any(r_clean, ["salicylic acid", "2-hydroxybenzoic acid"]) and
		_contains_any(r_clean, ["acetic anhydride", "acetyl chloride"])):
		return {
			"reaction_name": "O-Acetylation of Salicylic Acid",
			"primary_product": "Acetylsalicylic Acid (Aspirin)",
			"byproduct": "Acetic Acid",
			"theoretical_yield_pct": 92.5 if catalyst.contains("h2so4") or catalyst.contains("acid") else 65.0,
			"enthalpy_kj_mol": -42.8,
			"activation_energy_kj_mol": 58.2,
			"optimal_temp_c": 70.0,
			"status": "feasible",
			"hazards": ["GHS05 Corrosive", "GHS07 Harmful"]
		}

	# Case 2: Nucleophilic Acylation (4-Aminophenol + Acetic Anhydride -> Paracetamol)
	if (_contains_any(r_clean, ["4-aminophenol", "p-aminophenol"]) and
		_contains_any(r_clean, ["acetic anhydride", "acetyl chloride"])):
		return {
			"reaction_name": "Selective N-Acylation of 4-Aminophenol",
			"primary_product": "Paracetamol (Acetaminophen)",
			"byproduct": "Acetic Acid",
			"theoretical_yield_pct": 88.0,
			"enthalpy_kj_mol": -54.3,
			"activation_energy_kj_mol": 44.1,
			"optimal_temp_c": 60.0,
			"status": "feasible",
			"hazards": ["GHS07 Harmful"]
		}

	# Case 3: Baeyer-Drewson Indigo Synthesis (2-Nitrobenzaldehyde + Acetone + NaOH)
	if (_contains_any(r_clean, ["2-nitrobenzaldehyde", "o-nitrobenzaldehyde"]) and
		_contains_any(r_clean, ["acetone", "propanone"])):
		return {
			"reaction_name": "Baeyer-Drewson Indigo Condensation",
			"primary_product": "Indigo (Vat Blue 1)",
			"byproduct": "Acetic Acid, Water",
			"theoretical_yield_pct": 74.0,
			"enthalpy_kj_mol": -88.5,
			"activation_energy_kj_mol": 62.0,
			"optimal_temp_c": 25.0,
			"precipitate_formed": true,
			"precipitate_color_rgb": [0.05, 0.15, 0.65],
			"status": "feasible",
			"hazards": ["GHS07 Harmful"]
		}

	# Case 4: Acid-Base Neutralization (HCl + NaOH -> NaCl + H2O)
	if (_contains_any(r_clean, ["hydrochloric acid", "hcl"]) and
		_contains_any(r_clean, ["sodium hydroxide", "naoh"])):
		return {
			"reaction_name": "Strong Acid-Strong Base Neutralization",
			"primary_product": "Sodium Chloride",
			"byproduct": "Water",
			"theoretical_yield_pct": 100.0,
			"enthalpy_kj_mol": -57.1,
			"activation_energy_kj_mol": 5.0,
			"optimal_temp_c": 25.0,
			"status": "instantaneous",
			"hazards": ["GHS05 Corrosive"]
		}

	# Case 5: Default General Organic Coupling
	return {
		"reaction_name": "Organic Condensation / Coupling",
		"primary_product": "Coupled Adduct",
		"byproduct": "Solvent Soluble Salt",
		"theoretical_yield_pct": 70.0,
		"enthalpy_kj_mol": -25.0,
		"activation_energy_kj_mol": 65.0,
		"optimal_temp_c": temp_c,
		"status": "equilibrium",
		"hazards": ["Standard Laboratory Hazard"]
	}

func _assign_chemical_shift(ppm: float, mult: String, integ: int) -> Dictionary:
	if ppm >= 0.8 and ppm <= 1.5:
		return {
			"ppm": ppm,
			"fragment": "-CH3 (Aliphatic Methyl)",
			"neighboring_protons": 2 if mult == "t" else (1 if mult == "d" else 0)
		}
	elif ppm > 1.5 and ppm <= 2.8:
		return {
			"ppm": ppm,
			"fragment": "-CH2-C=O or -CH2-Ar (Allylic / Carbonyl Alpha)",
			"neighboring_protons": 3 if mult == "q" else 1
		}
	elif ppm > 3.2 and ppm <= 4.5:
		return {
			"ppm": ppm,
			"fragment": "-O-CH2- or -CH-OH (Ether / Alcohol Alpha)",
			"neighboring_protons": 3 if mult == "q" else 0
		}
	elif ppm >= 6.5 and ppm <= 8.5:
		return {
			"ppm": ppm,
			"fragment": "Aromatic C-H (Phenyl Ring)",
			"neighboring_protons": 1 if mult in ["d", "dd"] else 2
		}
	elif ppm >= 9.0 and ppm <= 10.5:
		return {
			"ppm": ppm,
			"fragment": "-CHO (Aldehyde)",
			"neighboring_protons": 0
		}
	elif ppm >= 10.5 and ppm <= 13.0:
		return {
			"ppm": ppm,
			"fragment": "-COOH (Carboxylic Acid)",
			"neighboring_protons": 0
		}

	return {
		"ppm": ppm,
		"fragment": "Unassigned Resonance",
		"neighboring_protons": 0
	}

func _contains_any(arr: Array[String], targets: Array[String]) -> bool:
	for a in arr:
		for t in targets:
			if a.contains(t):
				return true
	return false

# =============================================================================
# PROVIDER CONFIGURATION & TESTING
# =============================================================================

func set_provider(provider: String, custom_url: String = "", custom_model: String = "") -> void:
	active_provider = provider.to_lower()
	match active_provider:
		"omniroute":
			if not custom_url.is_empty(): omniroute_url = custom_url
			if not custom_model.is_empty(): preferred_model = custom_model
			enable_local_ai = true
		"ollama":
			if not custom_url.is_empty(): ollama_url = custom_url
			if not custom_model.is_empty(): preferred_model = custom_model
			enable_local_ai = true
		"lm_studio":
			if not custom_url.is_empty(): lm_studio_url = custom_url
			if not custom_model.is_empty(): preferred_model = custom_model
			enable_local_ai = true
		"custom":
			if not custom_url.is_empty(): omniroute_url = custom_url
			if not custom_model.is_empty(): preferred_model = custom_model
			enable_local_ai = true
		"offline":
			enable_local_ai = false
			_is_ai_available = false

	if enable_local_ai:
		probe_endpoint()

func get_active_endpoint() -> String:
	match active_provider:
		"omniroute", "custom": return omniroute_url
		"ollama": return ollama_url
		"lm_studio": return lm_studio_url
		_: return "Offline Heuristic (No Endpoint)"

func is_ai_connected() -> bool:
	return _is_ai_available

func get_last_latency_ms() -> float:
	return _last_latency_ms

func probe_endpoint(custom_url: String = "") -> void:
	var target_url = custom_url if not custom_url.is_empty() else get_active_endpoint()
	if not enable_local_ai or active_provider == "offline":
		_is_ai_available = false
		connection_status_changed.emit(false, "Offline Deterministic Engine")
		return

	var start_time = Time.get_ticks_msec()
	var test_http = HTTPRequest.new()
	test_http.timeout = 1.5
	add_child(test_http)
	test_http.request_completed.connect(func(res, code, _h, _b):
		_last_latency_ms = float(Time.get_ticks_msec() - start_time)
		_is_ai_available = (code == 200 or code == 401 or code == 404 or code == 405)
		connection_status_changed.emit(_is_ai_available, target_url)
		test_http.queue_free()
	)
	test_http.request(target_url, ["Content-Type: application/json"], HTTPClient.METHOD_POST, "{}")

# =============================================================================
# NETWORK - AI ENDPOINT COMMUNICATION
# =============================================================================

func _check_ai_availability() -> void:
	probe_endpoint()

func _send_ai_prompt(query_id: String, prompt: String) -> void:
	if not _http_request:
		return

	var endpoint = get_active_endpoint()
	var payload: Dictionary = {}

	if active_provider == "ollama":
		payload = {
			"model": preferred_model,
			"prompt": prompt,
			"stream": false,
			"format": "json"
		}
	else:
		payload = {
			"model": preferred_model,
			"messages": [
				{"role": "system", "content": "You are a Ph.D. analytical and organic chemist reaction predictor for ChemLab. Return JSON only."},
				{"role": "user", "content": prompt}
			],
			"temperature": 0.2
		}

	var json_str = JSON.stringify(payload)
	var headers = ["Content-Type: application/json"]
	_pending_queries[query_id] = Time.get_ticks_msec()
	_http_request.request(endpoint, headers, HTTPClient.METHOD_POST, json_str)

func _format_reaction_prompt(reactants: Array, temp_c: float, solvent: String, catalyst: String) -> String:
	return "Predict products and thermodynamics for reaction between %s at %.1f C in %s with catalyst %s." % [
		", ".join(reactants), temp_c, solvent, catalyst
	]

func _on_http_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		query_failed.emit("api_error", "HTTP %d received from local AI endpoint" % response_code)
		return

	var json = JSON.new()
	var err = json.parse(body.get_string_from_utf8())
	if err == OK and json.data is Dictionary:
		var choices = json.data.get("choices", [])
		if choices.size() > 0:
			var msg = choices[0].get("message", {}).get("content", "")
			query_completed.emit("ai_response", { "raw_content": msg })
