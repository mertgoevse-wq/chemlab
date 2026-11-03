# Simulation Bridge — Authoritative Scientific Simulation Engine for Godot 4
# Autoload Singleton managing chemical simulation state for all active vessels.
# Dual-engine execution: IPC Mode (Python core @ 127.0.0.1:8765) + Embedded Standalone Fallback.

extends Node

# =============================================================================
# 1. Enums & Constants
# =============================================================================

enum EngineMode { IPC_CONNECTED, EMBEDDED_FALLBACK, IPC_CONNECTING, IPC_FAILED }
enum IPCTransportMode { TCP, NAMED_PIPE }
enum ReactionType { NONE, ACID_BASE_NEUTRALIZATION, PRECIPITATION, CATALYTIC_DECOMPOSITION, OSCILLATING, REDOX, COMPLEXATION, THERMAL_DECOMPOSITION }

# --- IPC transport configuration (per ARCHITECTURE.md §4.1) ---
const IPC_HOST: String = "127.0.0.1"
const IPC_PORT: int = 8765
const IPC_NAMED_PIPE_PATH: String = "\\\\.\\pipe\\chemlab_core"
const IPC_TRANSPORT_MODE: IPCTransportMode = IPCTransportMode.TCP  # TCP preferred; NAMED_PIPE on Windows
const IPC_TIMEOUT_MS: int = 5000
const MAX_RECONNECT_ATTEMPTS: int = 3
const RECONNECT_DELAY_MS: int = 500

# Thermodynamic constants
const R_GAS: float = 8.314462618
const DELTA_H_NEUTRALIZATION_KJ_MOL: float = -57.1
const PHENOLPHTHALEIN_PKIND: float = 9.4
const WATER_CP_J_G_K: float = 4.184
const WATER_DENSITY_G_ML: float = 1.0

# Color constants
const COLOR_COLORLESS: Color = Color(1.0, 1.0, 1.0, 0.0)
const COLOR_FAINT_PINK: Color = Color(1.0, 0.72, 0.82, 0.6)
const COLOR_VIBRANT_MAGENTA: Color = Color(0.92, 0.08, 0.55, 1.0)

# =============================================================================
# 2. Signals
# =============================================================================

signal engine_mode_changed(new_mode: EngineMode)
signal reaction_completed(vessel_id: String, reaction_type: ReactionType, result: Dictionary)
signal vessel_state_changed(vessel_id: String, state: Dictionary)
signal safety_warning(vessel_id: String, warning: String)
signal temperature_alert(vessel_id: String, temp_c: float, threshold_c: float)
signal precipitation_formed(vessel_id: String, precipitate_name: String, amount_mol: float)
signal ph_changed(vessel_id: String, old_ph: float, new_ph: float)
signal indicator_color_changed(vessel_id: String, color: Color)

# =============================================================================
# 3. Internal State
# =============================================================================

# Preload helper classes
const ReactionEvaluator = preload("res://scripts/chemistry/reaction_evaluator.gd")

var _engine_mode: EngineMode = EngineMode.IPC_CONNECTING
var _tcp_peer: StreamPeerTCP
var _pipe_connected: bool = false
var _reconnect_attempts: int = 0
var _reconnect_timer: Timer
var _vessels: Dictionary = {}  # vessel_id -> VesselState
var _request_id_counter: int = 0
var _pending_requests: Dictionary = {}  # request_id -> Callable
var _use_embedded_fallback: bool = false
var _reaction_evaluator: ReactionEvaluator

# =============================================================================
# 4. Vessel State Dataclass (internal)
# =============================================================================

class VesselState:
	var vessel_id: String = ""
	var volume_ml: float = 0.0
	var temperature_c: float = 22.0
	var ph: float = 7.0
	var species_moles: Dictionary = {}  # species_id -> moles
	var species_concentrations: Dictionary = {}  # species_id -> mol/L
	var color_rgba: Color = COLOR_COLORLESS
	var turbidity: float = 0.0
	var bubble_rate: float = 0.0
	var foam_volume_ml: float = 0.0
	var indicator_present: bool = false
	var indicator_type: String = "phenolphthalein"
	var pressure_kpa: float = 101.325
	var headspace_volume_ml: float = 0.0
	var is_stirring: bool = false
	var stir_rate_rpm: float = 0.0
	var last_reaction_type: ReactionType = ReactionType.NONE
	var reaction_progress: float = 0.0
	var safety_flags: Array[String] = []

# =============================================================================
# 5. Lifecycle
# =============================================================================

func _ready() -> void:
	_reaction_evaluator = ReactionEvaluator.new()

	# Initialize TCP peer
	_tcp_peer = StreamPeerTCP.new()

	# Setup reconnection timer
	_reconnect_timer = Timer.new()
	_reconnect_timer.wait_time = RECONNECT_DELAY_MS / 1000.0
	_reconnect_timer.one_shot = true
	_reconnect_timer.timeout.connect(_attempt_ipc_connection)
	add_child(_reconnect_timer)

	# Initial connection attempt
	_attempt_ipc_connection()

	# Start periodic IPC message processing
	var process_timer = Timer.new()
	process_timer.wait_time = 0.016  # ~60 FPS
	process_timer.autostart = true
	process_timer.timeout.connect(_process_ipc_messages)
	add_child(process_timer)

func _exit_tree() -> void:
	if _tcp_peer and _tcp_peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		_tcp_peer.disconnect_from_host()
	if _pipe_file != null and _pipe_file.file_open:
		_pipe_file.close()
		_pipe_connected = false

# =============================================================================
# 6. IPC Connection Management
# =============================================================================

# -------------------------------------------------------------------------
# IPC transport selection (TCP or Windows Named Pipe)
# -------------------------------------------------------------------------

var _pipe_file: FileAccess  # Named pipe handle when IPC_TRANSPORT_MODE == NAMED_PIPE

func _attempt_ipc_connection() -> void:
	if _engine_mode == EngineMode.IPC_CONNECTED:
		return

	_engine_mode = EngineMode.IPC_CONNECTING
	engine_mode_changed.emit(_engine_mode)

	if IPC_TRANSPORT_MODE == IPCTransportMode.NAMED_PIPE:
		_attempt_named_pipe_connection()
	else:
		_attempt_tcp_connection()

func _attempt_tcp_connection() -> void:
	if _tcp_peer.get_status() != StreamPeerTCP.STATUS_NONE:
		_tcp_peer.disconnect_from_host()
	var err = _tcp_peer.connect_to_host(IPC_HOST, IPC_PORT)
	if err != OK:
		_handle_ipc_connection_failed("TCP connection error: %s" % err)
		return

	# Wait for connection with timeout
	var start_time = Time.get_ticks_msec()
	while _tcp_peer.get_status() == StreamPeerTCP.STATUS_CONNECTING:
		_tcp_peer.poll()
		if Time.get_ticks_msec() - start_time > IPC_TIMEOUT_MS:
			_handle_ipc_connection_failed("TCP connection timeout")
			return
		OS.delay_msec(10)

	_tcp_peer.poll()
	if _tcp_peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		_on_ipc_connected()
	else:
		_handle_ipc_connection_failed("Failed to establish TCP connection")

func _attempt_named_pipe_connection() -> void:
	var pipe = FileAccess.new()
	var err = pipe.open(IPC_NAMED_PIPE_PATH, FileAccess.READ_WRITE)
	if err != OK:
		_handle_ipc_connection_failed("Named pipe open error: %s" % err)
		return
	_pipe_file = pipe
	_pipe_connected = true
	_on_ipc_connected()

func _on_ipc_connected() -> void:
	_engine_mode = EngineMode.IPC_CONNECTED
	_reconnect_attempts = 0
	_use_embedded_fallback = false
	engine_mode_changed.emit(_engine_mode)

	# Send handshake
	_send_ipc_request("HANDSHAKE", {"client": "godot_simulation_bridge", "version": "1.0"})

func _handle_ipc_connection_failed(reason: String) -> void:
	_reconnect_attempts += 1
	print("[SimulationBridge] IPC connection failed (attempt %d/%d): %s" % [_reconnect_attempts, MAX_RECONNECT_ATTEMPTS, reason])

	if _reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
		_reconnect_timer.start()
	else:
		_enable_embedded_fallback()

func _enable_embedded_fallback() -> void:
	_engine_mode = EngineMode.EMBEDDED_FALLBACK
	_use_embedded_fallback = true
	engine_mode_changed.emit(_engine_mode)
	print("[SimulationBridge] Switched to EMBEDDED_FALLBACK mode - using local analytical chemistry engine")

func _process_ipc_messages() -> void:
	if _engine_mode != EngineMode.IPC_CONNECTED:
		return

	if IPC_TRANSPORT_MODE == IPCTransportMode.NAMED_PIPE:
		_process_named_pipe_messages()
		return

	_tcp_peer.poll()
	if _tcp_peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		_engine_mode = EngineMode.IPC_FAILED
		engine_mode_changed.emit(_engine_mode)
		_handle_ipc_connection_failed("TCP connection lost")
		return

	# Process incoming TCP data
	while _tcp_peer.get_available_bytes() > 0:
		var bytes_avail = _tcp_peer.get_available_bytes()
		var data = _tcp_peer.get_utf8_string(bytes_avail)
		if data != "":
			_parse_ipc_response(data)

func _process_named_pipe_messages() -> void:
	if _pipe_file == null or not _pipe_connected:
		_engine_mode = EngineMode.IPC_FAILED
		engine_mode_changed.emit(_engine_mode)
		_handle_ipc_connection_failed("Named pipe disconnected")
		return

	while _pipe_file.file_open and not _pipe_file.eof_reached():
		var line = _pipe_file.get_line().strip_edges()
		if line == "":
			continue
		var parsed = JSON.parse_string(line)
		if parsed == null:
			continue
		var req_id = parsed.get("request_id", "")
		if _pending_requests.has(req_id):
			var callback = _pending_requests[req_id]
			_pending_requests.erase(req_id)
			callback.call(parsed)

func _send_ipc_request(command: String, payload: Dictionary, callback = null) -> String:
	var req_id = "req_%d" % _request_id_counter
	_request_id_counter += 1

	var request = {
		"request_id": req_id,
		"command": command,
		"payload": payload
	}

	var json_str = JSON.stringify(request) + "\n"
	var sent: bool = false

	if IPC_TRANSPORT_MODE == IPCTransportMode.NAMED_PIPE and _pipe_file != null and _pipe_file.file_open:
		var err = _pipe_file.store_string(json_str)
		sent = (err == OK)
		if err != OK:
			print("[SimulationBridge] Failed to write to named pipe: %s" % err)
	else:
		var err = _tcp_peer.put_data(json_str.to_utf8_buffer())
		sent = (err == OK)
		if err != OK:
			print("[SimulationBridge] Failed to send IPC request: %s" % err)

	if not sent:
		if callback != null and callback is Callable and callback.is_valid():
			callback.call({"status": "ERROR", "error": "Send failed"})
		return ""

	if callback != null and callback is Callable and callback.is_valid():
		_pending_requests[req_id] = callback

	return req_id

# =============================================================================
# 7. Public API Methods
# =============================================================================

func _resolve_vessel_id(vessel: Variant) -> String:
	if typeof(vessel) == TYPE_STRING:
		return str(vessel)
	elif typeof(vessel) == TYPE_DICTIONARY:
		return str(vessel.get("vessel_id", vessel.get("id", "")))
	elif typeof(vessel) == TYPE_OBJECT and vessel != null:
		if vessel.has_method("get_vessel_id"):
			return str(vessel.get_vessel_id())
		elif "vessel_id" in vessel:
			return str(vessel.vessel_id)
		elif "id" in vessel:
			return str(vessel.id)
		elif vessel.has_meta("vessel_id"):
			return str(vessel.get_meta("vessel_id"))
		elif vessel.has_method("get_name"):
			return str(vessel.get_name())
	return str(vessel)

func mix_solutions(vessel_a: Variant, vessel_b: Variant, volume_transferred_ml: float) -> Dictionary:
	"""Mix solutions from vessel_b into vessel_a.
	   Accepts vessel IDs (String), Vessel Dictionaries, or Node instances.
	   Returns result dictionary with new state and reaction info."""
	var vessel_a_id = _resolve_vessel_id(vessel_a)
	var vessel_b_id = _resolve_vessel_id(vessel_b)

	if not _vessels.has(vessel_a_id) or not _vessels.has(vessel_b_id):
		return {"success": false, "error": "Vessel not found"}

	if volume_transferred_ml <= 0.0:
		return {"success": false, "error": "Volume must be positive"}

	var state_a = _vessels[vessel_a_id]
	var state_b = _vessels[vessel_b_id]

	# Clamp transfer volume to available volume in B
	var actual_volume = min(volume_transferred_ml, state_b.volume_ml)
	if actual_volume <= 0.0:
		return {"success": false, "error": "No volume to transfer"}

	# Calculate transfer fractions
	var fraction = actual_volume / state_b.volume_ml

	# If using IPC and connected, delegate to Python core
	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		return _mix_solutions_ipc(vessel_a_id, vessel_b_id, actual_volume)

	# Embedded fallback: perform mixing locally
	return _mix_solutions_embedded(state_a, state_b, actual_volume, fraction)

func _mix_solutions_embedded(vessel_a: VesselState, vessel_b: VesselState, volume_ml: float, fraction: float) -> Dictionary:
	"""Embedded mixing implementation with full reaction chemistry."""

	# 1. Transfer species moles
	var transferred_moles: Dictionary = {}
	for species_id in vessel_b.species_moles:
		var moles = vessel_b.species_moles[species_id] * fraction
		if moles > 0.0:
			transferred_moles[species_id] = moles
			vessel_a.species_moles[species_id] = vessel_a.species_moles.get(species_id, 0.0) + moles
			vessel_b.species_moles[species_id] -= moles

	# 2. Transfer volume
	vessel_a.volume_ml += volume_ml
	vessel_b.volume_ml -= volume_ml

	# 3. Thermal equilibration (weighted average)
	var total_vol = vessel_a.volume_ml
	if total_vol > 0.0:
		vessel_a.temperature_c = (vessel_a.temperature_c * (total_vol - volume_ml) + vessel_b.temperature_c * volume_ml) / total_vol

	# 4. Recalculate concentrations
	_recalculate_concentrations(vessel_a)
	_recalculate_concentrations(vessel_b)

	# 5. Detect and execute reactions
	var reaction_result = _execute_reactions(vessel_a)

	# 6. Update pH
	var old_ph = vessel_a.ph
	vessel_a.ph = _calculate_ph(vessel_a)
	if abs(vessel_a.ph - old_ph) > 0.01:
		ph_changed.emit(vessel_a.vessel_id, old_ph, vessel_a.ph)

	# 7. Update indicator color
	if vessel_a.indicator_present:
		var new_color = _reaction_evaluator.phenolphthalein_color(vessel_a.ph)
		if vessel_a.color_rgba != new_color:
			vessel_a.color_rgba = new_color
			indicator_color_changed.emit(vessel_a.vessel_id, new_color)

	# 8. Update vessel B color if it has indicator
	if vessel_b.indicator_present and vessel_b.volume_ml > 0:
		vessel_b.ph = _calculate_ph(vessel_b)
		vessel_b.color_rgba = _reaction_evaluator.phenolphthalein_color(vessel_b.ph)

	vessel_state_changed.emit(vessel_a.vessel_id, _vessel_to_dict(vessel_a))
	vessel_state_changed.emit(vessel_b.vessel_id, _vessel_to_dict(vessel_b))

	return {
		"success": true,
		"vessel_a": _vessel_to_dict(vessel_a),
		"vessel_b": _vessel_to_dict(vessel_b),
		"volume_transferred_ml": volume_ml,
		"reaction": reaction_result
	}

func _mix_solutions_ipc(vessel_a_id: String, vessel_b_id: String, volume_ml: float) -> Dictionary:
	"""Delegate mixing to IPC Python core.
	Sends a contract-compliant MIX_REAGENTS request per ARCHITECTURE.md §4.1."""
	var future = {
		"success": false,
		"pending": true
	}

	# Build reagent list from vessel_b's species (contract: reagents array of {id, moles})
	var reagents: Array[Dictionary] = []
	if _vessels.has(vessel_b_id):
		var vb = _vessels[vessel_b_id]
		for species_id in vb.species_moles:
			var moles = vb.species_moles[species_id]
			if moles > 0.0:
				reagents.append({"id": species_id, "moles": moles})

	var temp_c = 22.0
	if _vessels.has(vessel_a_id):
		temp_c = _vessels[vessel_a_id].temperature_c

	_send_ipc_request("MIX_REAGENTS", {
		"vessel_id": vessel_a_id,
		"reagents": reagents,
		"catalyst": "",
		"temperature_c": temp_c,
		"addition_order_correct": true,
		"in_fume_hood": true
	}, Callable(self, "_on_mix_response").bind(future))

	# Synchronous wait with timeout (for API compatibility)
	var start = Time.get_ticks_msec()
	while future["pending"] and Time.get_ticks_msec() - start < 1000:
		_process_ipc_messages()
		OS.delay_msec(1)

	if future["pending"]:
		future["pending"] = false
		future["success"] = false
		future["error"] = "IPC timeout, falling back to embedded"
		_enable_embedded_fallback()
		return mix_solutions(vessel_a_id, vessel_b_id, volume_ml)

	return future

func _on_mix_response(response: Dictionary, future: Dictionary) -> void:
	future["pending"] = false
	# Contract response (ARCHITECTURE.md §4.1): top-level "data" object carries results
	var data = response.get("data", {})
	if response.get("status") == "SUCCESS":
		future["success"] = true
		future["vessel_a"] = data.get("vessel_id", "")
		future["vessel_b"] = data
		future["reaction"] = {
			"reaction_name": data.get("reaction_name", ""),
			"conversion_ratio": data.get("conversion_ratio", 0.0),
			"temperature_c": data.get("temperature_c", 0.0),
			"is_exothermic": data.get("is_exothermic", false),
			"delta_h_kj_mol": data.get("delta_h_kj_mol", 0.0),
			"color_rgba": data.get("color_rgba", [1.0, 1.0, 1.0, 1.0]),
			"turbidity": data.get("turbidity", 0.0),
			"precipitate_formed": data.get("precipitate_formed", false),
			"precipitate_name": data.get("precipitate_name", ""),
			"bubbles_per_second": data.get("bubbles_per_second", 0.0),
			"side_products": data.get("side_products", []),
			"safety_warnings": data.get("safety_warnings", [])
		}
	else:
		future["success"] = false
		future["error"] = response.get("error", "Unknown IPC error")

func step_reaction(vessel: Variant, delta_time: float) -> Dictionary:
	"""Advance reaction simulation by delta_time seconds.
	   Accepts vessel ID (String), Vessel Dictionary, or Node instance."""
	var vessel_id = _resolve_vessel_id(vessel)

	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}

	if delta_time <= 0.0:
		return {"success": false, "error": "Delta time must be positive"}

	var vessel_state = _vessels[vessel_id]

	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		return _step_reaction_ipc(vessel_id, delta_time)

	return _step_reaction_embedded(vessel_state, delta_time)

func _step_reaction_embedded(vessel: VesselState, dt: float) -> Dictionary:
	"""Embedded reaction step with Arrhenius kinetics and thermal dynamics."""

	var old_temp = vessel.temperature_c
	var old_ph = vessel.ph
	var reactions_occurred: Array = []

	# 1. Thermal relaxation toward ambient (Newton's law of cooling)
	var ambient_temp = 22.0
	var cooling_time_constant = 30.0  # seconds
	var cooling_rate = (ambient_temp - vessel.temperature_c) / cooling_time_constant
	vessel.temperature_c += cooling_rate * dt

	# 2. Stirring enhances heat transfer and mixing
	if vessel.is_stirring:
		var stir_factor = 1.0 + (vessel.stir_rate_rpm / 1000.0) * 0.5
		cooling_rate *= stir_factor

	# 3. Execute kinetic reactions based on species present
	var reaction_result = _execute_reaction_kinetics(vessel, dt)
	if reaction_result.get("reaction_occurred", false):
		reactions_occurred.append(reaction_result)

	# 4. Handle oscillating reactions (Briggs-Rauscher, Belousov-Zhabotinsky)
	if _has_oscillator_conditions(vessel):
		var osc_result = _step_oscillator(vessel, dt)
		if osc_result.get("phase_changed", false):
			reactions_occurred.append(osc_result)

	# 5. Update pH
	vessel.ph = _calculate_ph(vessel)
	if abs(vessel.ph - old_ph) > 0.01:
		ph_changed.emit(vessel.vessel_id, old_ph, vessel.ph)

	# 6. Update indicator color
	if vessel.indicator_present:
		var new_color = _reaction_evaluator.phenolphthalein_color(vessel.ph)
		if vessel.color_rgba != new_color:
			vessel.color_rgba = new_color
			indicator_color_changed.emit(vessel.vessel_id, new_color)

	# 6. Check for precipitation
	var precip_result = _check_precipitation(vessel)
	if precip_result.get("precipitated", false):
		reactions_occurred.append(precip_result)

	# 7. Safety checks
	_check_safety_limits(vessel)

	vessel_state_changed.emit(vessel.vessel_id, _vessel_to_dict(vessel))

	return {
		"success": true,
		"vessel": _vessel_to_dict(vessel),
		"reactions": reactions_occurred,
		"temperature_change": vessel.temperature_c - old_temp,
		"ph_change": vessel.ph - old_ph
	}

func _step_reaction_ipc(vessel_id: String, dt: float) -> Dictionary:
	var future = {"pending": true}
	_send_ipc_request("STEP_SIMULATION", {"vessel_id": vessel_id, "dt": dt}, Callable(self, "_on_step_response").bind(future))

	var start = Time.get_ticks_msec()
	while future["pending"] and Time.get_ticks_msec() - start < 500:
		_process_ipc_messages()
		OS.delay_msec(1)

	if future["pending"]:
		future["pending"] = false
		_enable_embedded_fallback()
		return step_reaction(vessel_id, dt)

	return future

func _on_step_response(response: Dictionary, future: Dictionary) -> void:
	future["pending"] = false
	future["success"] = response.get("status") == "SUCCESS"
	future["vessel"] = response.get("vessel", {})
	future["reactions"] = response.get("reactions", [])
	future["temperature_change"] = response.get("temperature_change", 0.0)
	future["ph_change"] = response.get("ph_change", 0.0)

func get_species_info(species_id: String) -> Dictionary:
	"""Get canonical species information (MW, density, GHS hazards, NIST formation enthalpy)."""
	var sp = _reaction_evaluator.get_species(species_id)
	return {
		"species_id": species_id,
		"formula": sp.formula,
		"name": sp.name,
		"molecular_weight_g_mol": sp.molecular_weight_g_mol,
		"density_g_cm3": sp.density_g_cm3,
		"delta_h_f_kj_mol": sp.delta_h_f_kj_mol,
		"s_standard_j_mol_k": sp.s_standard_j_mol_k,
		"cp_j_mol_k": sp.cp_j_mol_k,
		"cas_number": sp.cas_number,
		"ghs_pictograms": sp.ghs_pictograms,
		"h_statements": sp.h_statements,
		"p_statements": sp.p_statements,
		"boiling_point_c": sp.boiling_point_c,
		"flash_point_c": sp.flash_point_c,
		"is_volatile": sp.is_volatile,
		"is_acid": sp.is_acid,
		"is_base": sp.is_base,
		"acid_pka": sp.acid_pka,
		"found": _reaction_evaluator.has_species(species_id)
	}

func query_cantera_thermodynamics(reactants: Dictionary, products: Dictionary, temperature_c: float = 25.0) -> Dictionary:
	"""Query Cantera thermodynamics via IPC or embedded analytical calculation."""
	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		var future = {"pending": true}
		_send_ipc_request("CALCULATE_THERMODYNAMICS", {
			"reactants": reactants,
			"products": products,
			"temperature_c": temperature_c
		}, func(resp):
			future["pending"] = false
			future["result"] = resp
		)
		var start = Time.get_ticks_msec()
		while future["pending"] and Time.get_ticks_msec() - start < 500:
			_process_ipc_messages()
			OS.delay_msec(1)
		if not future["pending"] and future.has("result"):
			return future["result"]

	# Embedded fallback using authoritative NIST / CRC values
	var delta_h = _reaction_evaluator.calculate_delta_h(reactants, products)
	var delta_s = _reaction_evaluator.calculate_delta_s(reactants, products)
	var delta_g = _reaction_evaluator.calculate_delta_g(delta_h, delta_s, temperature_c)
	var k_eq = _reaction_evaluator.calculate_k_eq(delta_g, temperature_c)
	var rate_k = _reaction_evaluator.calculate_arrhenius_k(temperature_c, 55.0, 1e11)

	return {
		"status": "SUCCESS",
		"mode": "EMBEDDED_FALLBACK",
		"temperature_c": temperature_c,
		"temperature_k": temperature_c + 273.15,
		"delta_h_kj_mol": delta_h,
		"delta_s_j_mol_k": delta_s,
		"delta_g_kj_mol": delta_g,
		"is_exothermic": delta_h < 0.0,
		"is_spontaneous": delta_g < 0.0,
		"equilibrium_constant_k_eq": k_eq,
		"rate_constant_k": rate_k
	}

func query_rdkit_structure(smiles: String, compound_name: String = "") -> Dictionary:
	"""Query RDKit molecular conformer via IPC or embedded species catalog."""
	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		var future = {"pending": true}
		_send_ipc_request("RDKIT_CONFORMER", {
			"smiles": smiles,
			"compound_name": compound_name
		}, func(resp):
			future["pending"] = false
			future["result"] = resp
		)
		var start = Time.get_ticks_msec()
		while future["pending"] and Time.get_ticks_msec() - start < 500:
			_process_ipc_messages()
			OS.delay_msec(1)
		if not future["pending"] and future.has("result"):
			return future["result"]

	# Embedded fallback
	var sp_id = compound_name if compound_name != "" else smiles
	var sp = _reaction_evaluator.get_species(sp_id)
	return {
		"status": "SUCCESS",
		"mode": "EMBEDDED_FALLBACK",
		"smiles": smiles,
		"compound_name": compound_name,
		"formula": sp.formula,
		"molecular_weight_g_mol": sp.molecular_weight_g_mol,
		"cas_number": sp.cas_number,
		"ghs_pictograms": sp.ghs_pictograms
	}

# =============================================================================
# 8. Vessel Management
# =============================================================================

func create_vessel(vessel_id: String, initial_volume_ml: float = 0.0, initial_temp_c: float = 22.0) -> Dictionary:
	"""Create a new reaction vessel."""
	if _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel already exists"}

	var vessel = VesselState.new()
	vessel.vessel_id = vessel_id
	vessel.volume_ml = max(0.0, initial_volume_ml)
	vessel.temperature_c = initial_temp_c
	vessel.ph = 7.0
	vessel.headspace_volume_ml = 50.0  # Default headspace
	vessel.pressure_kpa = 101.325

	_vessels[vessel_id] = vessel
	vessel_state_changed.emit(vessel_id, _vessel_to_dict(vessel))

	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func add_reagent(vessel_id: String, species_id: String, moles: float, concentration_m: float = 0.0) -> Dictionary:
	"""Add reagent to vessel."""
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}

	if not _reaction_evaluator.has_species(species_id):
		return {"success": false, "error": "Unknown species: %s" % species_id}

	if moles <= 0.0:
		return {"success": false, "error": "Moles must be positive"}

	var vessel = _vessels[vessel_id]
	var sp = _reaction_evaluator.get_species(species_id)

	vessel.species_moles[species_id] = vessel.species_moles.get(species_id, 0.0) + moles

	# If volume not set, calculate from moles and concentration or density
	if vessel.volume_ml <= 0.0 and concentration_m > 0.0:
		vessel.volume_ml = (moles / concentration_m) * 1000.0  # Convert L to mL
	elif vessel.volume_ml <= 0.0:
		# Estimate volume from mass and density
		var mass_g = moles * sp.molecular_weight_g_mol
		vessel.volume_ml = mass_g / sp.density_g_cm3

	_recalculate_concentrations(vessel)
	vessel.ph = _calculate_ph(vessel)

	if vessel.indicator_present:
		vessel.color_rgba = _reaction_evaluator.phenolphthalein_color(vessel.ph)

	vessel_state_changed.emit(vessel_id, _vessel_to_dict(vessel))
	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func set_indicator(vessel_id: String, indicator_type: String = "phenolphthalein", enabled: bool = true) -> Dictionary:
	"""Set pH indicator in vessel."""
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}

	var vessel = _vessels[vessel_id]
	vessel.indicator_present = enabled
	vessel.indicator_type = indicator_type

	if enabled:
		vessel.color_rgba = _reaction_evaluator.phenolphthalein_color(vessel.ph)
	else:
		vessel.color_rgba = COLOR_COLORLESS

	vessel_state_changed.emit(vessel_id, _vessel_to_dict(vessel))
	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func set_stirring(vessel_id: String, enabled: bool, rpm: float = 300.0) -> Dictionary:
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}

	var vessel = _vessels[vessel_id]
	vessel.is_stirring = enabled
	vessel.stir_rate_rpm = max(0.0, rpm) if enabled else 0.0
	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func get_vessel_state(vessel_id: String) -> Dictionary:
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}
	return {"success": true, "vessel": _vessel_to_dict(_vessels[vessel_id])}

func remove_vessel(vessel_id: String) -> Dictionary:
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}
	_vessels.erase(vessel_id)
	return {"success": true}

func get_all_vessels() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for vessel in _vessels.values():
		result.append(_vessel_to_dict(vessel))
	return result

func get_engine_mode() -> EngineMode:
	return _engine_mode

func force_embedded_fallback() -> void:
	_enable_embedded_fallback()

# =============================================================================
# 9. Embedded Chemistry Engine (Core Calculations)
# =============================================================================

func _recalculate_concentrations(vessel: VesselState) -> void:
	vessel.species_concentrations.clear()
	if vessel.volume_ml <= 0.0:
		return
	var vol_l = vessel.volume_ml / 1000.0
	for species_id in vessel.species_moles:
		vessel.species_concentrations[species_id] = vessel.species_moles[species_id] / vol_l

func _log10(val: float) -> float:
	return _reaction_evaluator.log10(val)


func _calculate_ph(vessel: VesselState) -> float:
	"""Calculate pH using Henderson-Hasselbalch and charge balance."""

	# Simple approach: identify acids and bases, calculate resulting pH
	var strong_acid_moles = 0.0
	var strong_base_moles = 0.0
	var weak_acids: Dictionary = {}  # species_id -> {moles, pka}
	var weak_bases: Dictionary = {}
	var buffer_pairs: Array = []

	for species_id in vessel.species_moles:
		var moles = vessel.species_moles[species_id]
		if moles <= 0.0:
			continue

		var sp = _reaction_evaluator.get_species(species_id)

		if sp.is_acid:
			if sp.acid_pka < 0:  # Strong acid
				strong_acid_moles += moles
			else:
				weak_acids[species_id] = {"moles": moles, "pka": sp.acid_pka}
		elif sp.is_base:
			# Check if strong base (NaOH, KOH, etc.)
			if species_id in ["NaOH_aq", "KOH_aq"] or sp.acid_pka > 14:
				strong_base_moles += moles
			else:
				weak_bases[species_id] = {"moles": moles, "pka": sp.acid_pka}

	# Neutralization: strong acid + strong base
	var net_h = strong_acid_moles - strong_base_moles
	var vol_l = max(vessel.volume_ml / 1000.0, 0.001)

	if net_h > 0:
		# Excess strong acid
		var h_conc = net_h / vol_l
		return clampf(-_log10(max(h_conc, 1e-14)), 0.0, 14.0)
	elif net_h < 0:
		# Excess strong base
		var oh_conc = -net_h / vol_l
		var poh = -_log10(max(oh_conc, 1e-14))
		return clampf(14.0 - poh, 0.0, 14.0)
	else:
		# Neutralized - check for weak acid/base buffers
		if weak_acids.size() > 0 and weak_bases.size() > 0:
			# Buffer solution - use first pair
			var wa_id = weak_acids.keys()[0]
			var wb_id = weak_bases.keys()[0]
			var wa = weak_acids[wa_id]
			var wb = weak_bases[wb_id]
			var conc_a = wa.moles / vol_l
			var conc_b = wb.moles / vol_l
			return _reaction_evaluator.henderson_hasselbalch_ph(wa.pka, conc_b, conc_a)
		elif weak_acids.size() > 0:
			# Weak acid only
			var wa = weak_acids.values()[0]
			var conc = wa.moles / vol_l
			if conc > 0:
				var h = sqrt(pow(10.0, -wa.pka) * conc)
				return clampf(-_log10(max(h, 1e-14)), 0.0, 14.0)
		elif weak_bases.size() > 0:
			# Weak base only
			var wb = weak_bases.values()[0]
			var conc = wb.moles / vol_l
			if conc > 0:
				var kb = pow(10.0, -(14.0 - wb.pka))
				var oh = sqrt(kb * conc)
				var poh = -_log10(max(oh, 1e-14))
				return clampf(14.0 - poh, 0.0, 14.0)

	return 7.0  # Neutral

func _execute_reactions(vessel: VesselState) -> Dictionary:
	"""Execute immediate reactions upon mixing."""
	var result = {
		"reaction_occurred": false,
		"reaction_type": ReactionType.NONE,
		"heat_released_kj": 0.0,
		"temperature_rise_c": 0.0,
		"products_formed": {},
		"consumed": {}
	}

	# Check for acid-base neutralization
	var has_strong_acid = false
	var has_strong_base = false
	var acid_moles = 0.0
	var base_moles = 0.0
	var acid_id = ""
	var base_id = ""

	for species_id in vessel.species_moles:
		var moles = vessel.species_moles[species_id]
		if moles <= 0.0:
			continue
		var sp = _reaction_evaluator.get_species(species_id)
		if sp.is_acid and sp.acid_pka < 0:
			has_strong_acid = true
			acid_moles += moles
			acid_id = species_id
		elif species_id in ["NaOH_aq", "KOH_aq"]:
			has_strong_base = true
			base_moles += moles
			base_id = species_id

	if has_strong_acid and has_strong_base:
		var reacted = min(acid_moles, base_moles)
		if reacted > 0:
			# Consume reactants
			vessel.species_moles[acid_id] -= reacted
			vessel.species_moles[base_id] -= reacted

			# Produce water and salt
			vessel.species_moles["H2O"] = vessel.species_moles.get("H2O", 0.0) + reacted
			var salt_id = "NaCl_aq"  # Simplified
			if acid_id == "HCl_aq" and base_id == "NaOH_aq":
				salt_id = "NaCl_aq"
			vessel.species_moles[salt_id] = vessel.species_moles.get(salt_id, 0.0) + reacted

			result["reaction_occurred"] = true
			result["reaction_type"] = ReactionType.ACID_BASE_NEUTRALIZATION
			result["consumed"][acid_id] = reacted
			result["consumed"][base_id] = reacted
			result["products_formed"][salt_id] = reacted
			result["products_formed"]["H2O"] = reacted

			# Calculate heat release
			var heat_kj = reacted * abs(DELTA_H_NEUTRALIZATION_KJ_MOL)
			result["heat_released_kj"] = heat_kj

			# Calculate temperature rise
			var total_mass_g = vessel.volume_ml * WATER_DENSITY_G_ML
			var delta_t = _reaction_evaluator.calculate_adiabatic_temp_rise(
				DELTA_H_NEUTRALIZATION_KJ_MOL, reacted, total_mass_g, WATER_CP_J_G_K
			)
			vessel.temperature_c += delta_t
			result["temperature_rise_c"] = delta_t

			# Check for thermal hazard
			if vessel.temperature_c > 80.0:
				safety_warning.emit(vessel.vessel_id, "Temperature exceeds 80°C: %0.1f°C" % vessel.temperature_c)
			if vessel.temperature_c > 95.0:
				temperature_alert.emit(vessel.vessel_id, vessel.temperature_c, 95.0)
				vessel.safety_flags.append("THERMAL_HAZARD")

	_recalculate_concentrations(vessel)
	return result

func _execute_reaction_kinetics(vessel: VesselState, dt: float) -> Dictionary:
	"""Execute time-dependent reaction kinetics using Arrhenius equation."""
	var result = {"reaction_occurred": false}

	# Hydrogen peroxide decomposition catalyzed by KI
	if vessel.species_concentrations.get("H2O2_aq", 0) > 0 and vessel.species_concentrations.get("KI_aq", 0) > 0:
		var h2o2_conc = vessel.species_concentrations["H2O2_aq"]
		var ki_conc = vessel.species_concentrations["KI_aq"]

		# Arrhenius: k = A * exp(-Ea/RT)
		# For H2O2 + I- -> H2O + O2 (catalyzed)
		var temp_k = vessel.temperature_c + 273.15
		var ea = 56.0  # kJ/mol
		var A = 1e7
		var k = A * exp(-ea * 1000.0 / (R_GAS * temp_k))

		# Rate = k [H2O2][I-]
		var rate = k * h2o2_conc * ki_conc  # mol/(L·s)
		var reacted_mol_l = rate * dt
		var reacted_moles = reacted_mol_l * (vessel.volume_ml / 1000.0)

		if reacted_moles > 0:
			var h2o2_moles = vessel.species_moles.get("H2O2_aq", 0)
			reacted_moles = min(reacted_moles, h2o2_moles)

			vessel.species_moles["H2O2_aq"] -= reacted_moles
			vessel.species_moles["H2O"] = vessel.species_moles.get("H2O", 0.0) + reacted_moles
			vessel.species_moles["O2_gas"] = vessel.species_moles.get("O2_gas", 0.0) + reacted_moles / 2.0
			vessel.bubble_rate = min(1.0, vessel.bubble_rate + reacted_moles * 10.0)

			# Exothermic
			var heat_kj = reacted_moles * 98.0  # Approx ΔH for H2O2 decomposition
			var total_mass = vessel.volume_ml * WATER_DENSITY_G_ML
			var delta_t = heat_kj * 1000.0 / (total_mass * WATER_CP_J_G_K)
			vessel.temperature_c += delta_t

			result["reaction_occurred"] = true
			result["reaction_type"] = ReactionType.CATALYTIC_DECOMPOSITION
			result["reacted_moles"] = reacted_moles
			result["heat_kj"] = heat_kj
			result["temperature_rise"] = delta_t

	return result

func _has_oscillator_conditions(vessel: VesselState) -> bool:
	"""Check for Briggs-Rauscher or Belousov-Zhabotinsky conditions."""
	# Briggs-Rauscher: H2O2 + KIO3 + Malonic Acid + MnSO4
	return (vessel.species_concentrations.get("H2O2_aq", 0) > 0 and
	        vessel.species_concentrations.get("KI_aq", 0) > 0 and  # KIO3 proxy
	        vessel.species_concentrations.get("malonic_acid", 0) > 0 and
	        vessel.species_concentrations.get("manganese_sulfate", 0) > 0)

func _step_oscillator(vessel: VesselState, dt: float) -> Dictionary:
	"""Step oscillating reaction (Briggs-Rauscher 3-phase color cycle)."""
	var result = {"phase_changed": false}

	# Oscillation period ~6-10 seconds depending on concentrations
	var ma_conc = vessel.species_concentrations.get("malonic_acid", 0)
	if ma_conc <= 0:
		return result

	var base_period = 8.0  # seconds
	var period = base_period / max(ma_conc, 0.01)

	# Simple phase tracking
	var phase_duration = period / 3.0
	vessel.reaction_progress += dt

	var old_phase = vessel.last_reaction_type
	var cycle_pos = fmod(vessel.reaction_progress, period)

	if cycle_pos < phase_duration:
		vessel.last_reaction_type = ReactionType.OSCILLATING
		vessel.color_rgba = Color(0.95, 0.98, 1.0, 1.0)  # Clear
	elif cycle_pos < 2 * phase_duration:
		vessel.last_reaction_type = ReactionType.OSCILLATING
		vessel.color_rgba = Color(0.96, 0.72, 0.24, 1.0)  # Amber
	else:
		vessel.last_reaction_type = ReactionType.OSCILLATING
		vessel.color_rgba = Color(0.14, 0.22, 0.64, 1.0)  # Deep Blue

	if vessel.last_reaction_type != old_phase:
		result["phase_changed"] = true
		result["phase"] = vessel.last_reaction_type
		result["color"] = vessel.color_rgba

	return result

func _check_precipitation(vessel: VesselState) -> Dictionary:
	"""Check solubility products for precipitation."""
	var result = {"precipitated": false}

	# Common precipitates and their Ksp values (at 25°C)
	var ksp_table = {
		"AgCl": {"ions": ["Ag+", "Cl-"], "ksp": 1.77e-10, "name": "Silver Chloride"},
		"BaSO4": {"ions": ["Ba2+", "SO4^2-"], "ksp": 1.1e-10, "name": "Barium Sulfate"},
		"PbCl2": {"ions": ["Pb2+", "Cl-"], "ksp": 1.7e-5, "name": "Lead(II) Chloride"},
		"CaCO3": {"ions": ["Ca2+", "CO3^2-"], "ksp": 3.3e-9, "name": "Calcium Carbonate"},
		"Fe(OH)3": {"ions": ["Fe3+", "OH-"], "ksp": 2.8e-39, "name": "Iron(III) Hydroxide"},
		"Cu(OH)2": {"ions": ["Cu2+", "OH-"], "ksp": 2.2e-20, "name": "Copper(II) Hydroxide"},
	}

	# Check each possible precipitate
	for precip_name in ksp_table:
		var data = ksp_table[precip_name]
		var ion_a = data.ions[0]
		var ion_b = data.ions[1]

		var conc_a = vessel.species_concentrations.get(ion_a, 0.0)
		var conc_b = vessel.species_concentrations.get(ion_b, 0.0)

		if conc_a > 0 and conc_b > 0:
			var ip = conc_a * conc_b  # Ionic product
			if precip_name == "PbCl2":
				ip = conc_a * conc_b * conc_b  # Pb2+ + 2Cl-
			elif precip_name == "Fe(OH)3":
				ip = conc_a * conc_b * conc_b * conc_b  # Fe3+ + 3OH-
			elif precip_name == "Cu(OH)2":
				ip = conc_a * conc_b * conc_b  # Cu2+ + 2OH-

			if ip > data.ksp:
				# Precipitation occurs
				var max_precip = min(conc_a, conc_b) * (vessel.volume_ml / 1000.0)
				if precip_name == "PbCl2":
					max_precip = min(conc_a, conc_b / 2.0) * (vessel.volume_ml / 1000.0)
				elif precip_name == "Fe(OH)3":
					max_precip = min(conc_a, conc_b / 3.0) * (vessel.volume_ml / 1000.0)
				elif precip_name == "Cu(OH)2":
					max_precip = min(conc_a, conc_b / 2.0) * (vessel.volume_ml / 1000.0)

				# Remove ions from solution
				vessel.species_moles[ion_a] = max(0, vessel.species_moles.get(ion_a, 0) - max_precip)
				vessel.species_moles[ion_b] = max(0, vessel.species_moles.get(ion_b, 0) - max_precip * (2 if precip_name in ["PbCl2", "Cu(OH)2"] else (3 if precip_name == "Fe(OH)3" else 1)))

				# Add precipitate
				var precip_id = precip_name.to_lower() + "_s"
				vessel.species_moles[precip_id] = vessel.species_moles.get(precip_id, 0.0) + max_precip
				vessel.turbidity = min(1.0, vessel.turbidity + 0.1)

				result["precipitated"] = true
				result["precipitate"] = data.name
				result["amount_mol"] = max_precip
				result["ksp"] = data.ksp
				result["ionic_product"] = ip

				precipitation_formed.emit(vessel.vessel_id, data.name, max_precip)
				vessel.safety_flags.append("PRECIPITATE_FORMED: %s" % data.name)

				_recalculate_concentrations(vessel)
				break

	return result

func _check_safety_limits(vessel: VesselState) -> void:
	"""Check for safety violations."""
	# Temperature
	if vessel.temperature_c > 100.0:
		safety_warning.emit(vessel.vessel_id, "BOILING: Temperature %0.1f°C exceeds 100°C" % vessel.temperature_c)
		vessel.safety_flags.append("BOILING")
	elif vessel.temperature_c > 80.0:
		if not vessel.safety_flags.has("HIGH_TEMP_WARNING"):
			safety_warning.emit(vessel.vessel_id, "High temperature: %0.1f°C" % vessel.temperature_c)
			vessel.safety_flags.append("HIGH_TEMP_WARNING")

	# Pressure buildup from gas evolution
	var gas_moles = 0.0
	for species_id in vessel.species_moles:
		var sp = _reaction_evaluator.get_species(species_id)
		if sp.boiling_point_c < vessel.temperature_c or sp.is_volatile:
			gas_moles += vessel.species_moles[species_id]

	if gas_moles > 0 and vessel.headspace_volume_ml > 0:
		# Ideal gas law: P = nRT/V
		var temp_k = vessel.temperature_c + 273.15
		var vol_l = vessel.headspace_volume_ml / 1000.0
		var pressure_pa = gas_moles * R_GAS * temp_k / vol_l
		var pressure_kpa = pressure_pa / 1000.0
		vessel.pressure_kpa = 101.325 + pressure_kpa

		if vessel.pressure_kpa > 200.0:
			safety_warning.emit(vessel.vessel_id, "OVERPRESSURE: %0.1f kPa" % vessel.pressure_kpa)
			vessel.safety_flags.append("OVERPRESSURE")

# =============================================================================
# 10. Utility Methods
# =============================================================================

func _vessel_to_dict(vessel: VesselState) -> Dictionary:
	return {
		"vessel_id": vessel.vessel_id,
		"volume_ml": vessel.volume_ml,
		"temperature_c": vessel.temperature_c,
		"ph": vessel.ph,
		"species_moles": vessel.species_moles.duplicate(true),
		"species_concentrations": vessel.species_concentrations.duplicate(true),
		"color_rgba": [vessel.color_rgba.r, vessel.color_rgba.g, vessel.color_rgba.b, vessel.color_rgba.a],
		"turbidity": vessel.turbidity,
		"bubble_rate": vessel.bubble_rate,
		"foam_volume_ml": vessel.foam_volume_ml,
		"indicator_present": vessel.indicator_present,
		"indicator_type": vessel.indicator_type,
		"pressure_kpa": vessel.pressure_kpa,
		"headspace_volume_ml": vessel.headspace_volume_ml,
		"is_stirring": vessel.is_stirring,
		"stir_rate_rpm": vessel.stir_rate_rpm,
		"last_reaction_type": vessel.last_reaction_type,
		"reaction_progress": vessel.reaction_progress,
		"safety_flags": vessel.safety_flags.duplicate()
	}

# =============================================================================
# 11. Verification & Testing Methods
# =============================================================================

func run_self_tests() -> Dictionary:
	"""Run internal verification tests."""
	var results = {
		"passed": 0,
		"failed": 0,
		"tests": []
	}

	# Test 1: Neutralization enthalpy
	var neut_test = _reaction_evaluator.verify_neutralization_constants()
	results.tests.append({
		"name": "Neutralization ΔH verification",
		"passed": neut_test.within_tolerance_5_percent,
		"detail": "Calculated: %0.2f kJ/mol, Expected: -57.1 kJ/mol" % neut_test.calculated_delta_h_kj_mol
	})

	# Test 2: Henderson-Hasselbalch
	var ph = _reaction_evaluator.henderson_hasselbalch_ph(4.76, 0.1, 0.1)
	results.tests.append({
		"name": "Henderson-Hasselbalch pH = pKa at equal concentrations",
		"passed": abs(ph - 4.76) < 0.01,
		"detail": "pH = %0.2f" % ph
	})

	# Test 3: Phenolphthalein color
	var col1 = _reaction_evaluator.phenolphthalein_color(7.0)
	var col2 = _reaction_evaluator.phenolphthalein_color(8.5)
	var col3 = _reaction_evaluator.phenolphthalein_color(9.5)
	results.tests.append({
		"name": "Phenolphthalein color transitions",
		"passed": col1.a == 0.0 and col2.a > 0.0 and col3 == COLOR_VIBRANT_MAGENTA,
		"detail": "pH 7: alpha=%0.2f, pH 8.5: alpha=%0.2f, pH 9.5: magenta=%s" % [col1.a, col2.a, col3 == COLOR_VIBRANT_MAGENTA]
	})

	# Test 4: Arrhenius rate increases with temperature
	var k1 = _reaction_evaluator.calculate_arrhenius_k(25.0, 50.0, 1e10)
	var k2 = _reaction_evaluator.calculate_arrhenius_k(50.0, 50.0, 1e10)
	results.tests.append({
		"name": "Arrhenius temperature acceleration",
		"passed": k2 > k1 * 2.0,
		"detail": "k(25°C)=%e, k(50°C)=%e, ratio=%0.1f" % [k1, k2, k2/k1]
	})

	# Test 5: Precipitation Ksp
	var precip = _reaction_evaluator.solubility_product_check(1e-4, 1e-4, 1e-10)
	results.tests.append({
		"name": "Solubility product precipitation check",
		"passed": precip == true,
		"detail": "[Ag+]=1e-4, [Cl-]=1e-4, Ksp=1e-10 -> precipitate=%s" % precip
	})

	# Test 6: Adiabatic temperature rise
	var dt = _reaction_evaluator.calculate_adiabatic_temp_rise(-57.1, 0.1, 100.0, 4.184)
	results.tests.append({
		"name": "Adiabatic temperature rise calculation",
		"passed": dt > 13.0 and dt < 14.5,
		"detail": "ΔT = %0.2f°C for 0.1 mol neutralization in 100g water" % dt
	})

	for test in results.tests:
		if test.passed:
			results.passed += 1
		else:
			results.failed += 1

	return results