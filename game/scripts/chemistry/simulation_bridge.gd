# Athanor Ascension - Simulation Bridge (Godot ↔ Python Core IPC)
# Autoload: SimulationBridge
# Dual-engine: IPC Mode (Python @ 127.0.0.1:8765) + Embedded Fallback
# Contract per ARCHITECTURE.md §4.1

extends Node

class_name SimulationBridge

signal engine_mode_changed(new_mode: int)
signal reaction_completed(vessel_id: String, reaction_type: int, result: Dictionary)
signal vessel_state_changed(vessel_id: String, state: Dictionary)
signal safety_warning(vessel_id: String, warning: String)
signal temperature_alert(vessel_id: String, temp_c: float, threshold_c: float)
signal precipitation_formed(vessel_id: String, precipitate_name: String, amount_mol: float)
signal ph_changed(vessel_id: String, old_ph: float, new_ph: float)
signal indicator_color_changed(vessel_id: String, color: Color)

enum EngineMode { IPC_CONNECTED, EMBEDDED_FALLBACK, IPC_CONNECTING, IPC_FAILED }
enum IPCTransportMode { TCP, NAMED_PIPE }
enum ReactionType { NONE, ACID_BASE_NEUTRALIZATION, PRECIPITATION, CATALYTIC_DECOMPOSITION, OSCILLATING, REDOX, COMPLEXATION, THERMAL_DECOMPOSITION }

# IPC Configuration
const IPC_HOST: String = "127.0.0.1"
const IPC_PORT: int = 8765
const IPC_NAMED_PIPE_PATH: String = "\\\\.\\pipe\\chemlab_core"
const IPC_TRANSPORT_MODE: IPCTransportMode = IPCTransportMode.TCP
const IPC_TIMEOUT_MS: int = 5000
const MAX_RECONNECT_ATTEMPTS: int = 3
const RECONNECT_DELAY_MS: int = 500

# Thermodynamic constants
const R_GAS: float = 8.314462618
const DELTA_H_NEUTRALIZATION_KJ_MOL: float = -57.1
const PHENOLPHTHALEIN_PKIND: float = 9.4
const WATER_CP_J_G_K: float = 4.184
const WATER_DENSITY_G_ML: float = 1.0

# Colors
const COLOR_COLORLESS: Color = Color(1.0, 1.0, 1.0, 0.0)
const COLOR_FAINT_PINK: Color = Color(1.0, 0.72, 0.82, 0.6)
const COLOR_VIBRANT_MAGENTA: Color = Color(0.92, 0.08, 0.55, 1.0)

# Preload embedded evaluator
const ReactionEvaluator = preload("res://scripts/chemistry/reaction_evaluator.gd")

# State
var _engine_mode: EngineMode = EngineMode.IPC_CONNECTING
var _tcp_peer: StreamPeerTCP
var _pipe_connected: bool = false
var _reconnect_attempts: int = 0
var _reconnect_timer: Timer
var _vessels: Dictionary = {}
var _request_id_counter: int = 0
var _pending_requests: Dictionary = {}
var _use_embedded_fallback: bool = false
var _reaction_evaluator: ReactionEvaluator

# Global modifiers (from talents, equipment, companions)
var _global_yield_modifier: float = 1.0
var _global_purity_bonus: float = 1.0
var _global_speed_modifier: float = 1.0

# Vessel state class
class VesselState:
	var vessel_id: String = ""
	var volume_ml: float = 0.0
	var temperature_c: float = 22.0
	var ph: float = 7.0
	var species_moles: Dictionary = {}
	var species_concentrations: Dictionary = {}
	var color_rgba: Color = COLOR_COLORLESS
	var turbidity: float = 0.0
	var bubble_rate: float = 0.0
	var foam_volume_ml: float = 0.0
	var indicator_present: bool = false
	var indicator_type: String = "phenolphthalein"
	var pressure_kpa: float = 101.325
	var headspace_volume_ml: float = 50.0
	var is_stirring: bool = false
	var stir_rate_rpm: float = 0.0
	var last_reaction_type: int = ReactionType.NONE
	var reaction_progress: float = 0.0
	var safety_flags: Array[String] = []

func _ready() -> void:
	_reaction_evaluator = ReactionEvaluator.new()
	_initialize_ipc()

func _initialize_ipc() -> void:
	_tcp_peer = StreamPeerTCP.new()
	_reconnect_timer = Timer.new()
	_reconnect_timer.wait_time = RECONNECT_DELAY_MS / 1000.0
	_reconnect_timer.one_shot = true
	_reconnect_timer.timeout.connect(_attempt_ipc_connection)
	add_child(_reconnect_timer)

	# Initial connection
	_attempt_ipc_connection()

	# Periodic message processing
	var process_timer = Timer.new()
	process_timer.wait_time = 0.016  # ~60 FPS
	process_timer.autostart = true
	process_timer.timeout.connect(_process_ipc_messages)
	add_child(process_timer)

func _exit_tree() -> void:
	if _tcp_peer and _tcp_peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		_tcp_peer.disconnect_from_host()

# =============================================================================
# IPC CONNECTION MANAGEMENT
# =============================================================================

var _pipe_file: FileAccess

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
	var pipe = FileAccess.open(IPC_NAMED_PIPE_PATH, FileAccess.READ_WRITE)
	if pipe == null:
		_handle_ipc_connection_failed("Named pipe open error")
		return
	_pipe_file = pipe
	_pipe_connected = true
	_on_ipc_connected()

func _on_ipc_connected() -> void:
	_engine_mode = EngineMode.IPC_CONNECTED
	_reconnect_attempts = 0
	_use_embedded_fallback = false
	engine_mode_changed.emit(_engine_mode)
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

func _parse_ipc_response(data: String) -> void:
	var parsed = JSON.parse_string(data)
	if parsed == null:
		return

	var req_id = parsed.get("request_id", "")
	var status = parsed.get("status", "")

	if req_id != "" and _pending_requests.has(req_id):
		var callback = _pending_requests[req_id]
		_pending_requests.erase(req_id)
		callback.call(parsed)
		return

	if status == "SUCCESS":
		var payload = parsed.get("data", {})
		if payload.has("reaction_name") or payload.has("conversion_ratio"):
			var reaction_type_enum = ReactionType.NONE
			var reaction_name = payload.get("reaction_name", "")
			match reaction_name:
				"acid_base_neutralization", "ACID_BASE_NEUTRALIZATION":
					reaction_type_enum = ReactionType.ACID_BASE_NEUTRALIZATION
				"precipitation":
					reaction_type_enum = ReactionType.PRECIPITATION
				"catalytic_decomposition":
					reaction_type_enum = ReactionType.CATALYTIC_DECOMPOSITION
				"oscillating":
					reaction_type_enum = ReactionType.OSCILLATING
				"redox":
					reaction_type_enum = ReactionType.REDOX
				"complexation":
					reaction_type_enum = ReactionType.COMPLEXATION
				"thermal_decomposition":
					reaction_type_enum = ReactionType.THERMAL_DECOMPOSITION

			var result = {
				"vessel_id": payload.get("vessel_id", ""),
				"reaction_type": reaction_type_enum,
				"result": payload
			}
			reaction_completed.emit(payload.get("vessel_id", ""), reaction_type_enum, result)

		if payload.has("volume_ml") or payload.has("temperature_c") or payload.has("ph"):
			var state = {
				"volume_ml": payload.get("volume_ml", 0.0),
				"temperature_c": payload.get("temperature_c", 22.0),
				"ph": payload.get("ph", 7.0),
				"species_moles": payload.get("species_moles", {}),
				"species_concentrations": payload.get("species_concentrations", {}),
				"color_rgba": payload.get("color_rgba", [1.0, 1.0, 1.0, 1.0]),
				"turbidity": payload.get("turbidity", 0.0)
			}
			vessel_state_changed.emit(payload.get("vessel_id", ""), state)

	elif status == "ERROR":
		var error_msg = parsed.get("error", "Unknown IPC error")
		print("[SimulationBridge] IPC response error: %s" % error_msg)

	else:
		if parsed.has("vessel_id"):
			var state = {
				"volume_ml": parsed.get("volume_ml", 0.0),
				"temperature_c": parsed.get("temperature_c", 22.0),
				"ph": parsed.get("ph", 7.0),
				"species_moles": parsed.get("species_moles", {}),
				"species_concentrations": parsed.get("species_concentrations", {}),
				"color_rgba": parsed.get("color_rgba", [1.0, 1.0, 1.0, 1.0]),
				"turbidity": parsed.get("turbidity", 0.0)
			}
			vessel_state_changed.emit(parsed.get("vessel_id", ""), state)

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
# PUBLIC API
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
	var vessel_a_id = _resolve_vessel_id(vessel_a)
	var vessel_b_id = _resolve_vessel_id(vessel_b)

	if not _vessels.has(vessel_a_id) or not _vessels.has(vessel_b_id):
		return {"success": false, "error": "Vessel not found"}

	if volume_transferred_ml <= 0.0:
		return {"success": false, "error": "Volume must be positive"}

	var state_a = _vessels[vessel_a_id]
	var state_b = _vessels[vessel_b_id]

	var actual_volume = min(volume_transferred_ml, state_b.volume_ml)
	if actual_volume <= 0.0:
		return {"success": false, "error": "No volume to transfer"}

	var fraction = actual_volume / state_b.volume_ml

	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		return _mix_solutions_ipc(vessel_a_id, vessel_b_id, actual_volume)

	return _mix_solutions_embedded(state_a, state_b, actual_volume, fraction)

func _mix_solutions_embedded(vessel_a: VesselState, vessel_b: VesselState, volume_ml: float, fraction: float) -> Dictionary:
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

	# 3. Thermal equilibration
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

	# 8. Update vessel B
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
	var future = { "success": false, "pending": true }

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

	var start = Time.get_ticks_msec()
	while future.pending and Time.get_ticks_msec() - start < 1000:
		_process_ipc_messages()
		OS.delay_msec(1)

	if future.pending:
		future.pending = false
		future.success = false
		future.error = "IPC timeout, falling back to embedded"
		_enable_embedded_fallback()
		return mix_solutions(vessel_a_id, vessel_b_id, volume_ml)

	return future

func _on_mix_response(response: Dictionary, future: Dictionary) -> void:
	future.pending = false
	var data = response.get("data", {})
	if response.get("status") == "SUCCESS":
		future.success = true
		future.vessel_a = data.get("vessel_id", "")
		future.vessel_b = data
		future.reaction = {
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
		future.success = false
		future.error = response.get("error", "Unknown IPC error")

# =============================================================================
# VESSEL MANAGEMENT
# =============================================================================

func create_vessel(vessel_id: String, initial_volume_ml: float = 0.0, initial_temp_c: float = 22.0) -> Dictionary:
	if _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel already exists"}

	var vessel = VesselState.new()
	vessel.vessel_id = vessel_id
	vessel.volume_ml = max(0.0, initial_volume_ml)
	vessel.temperature_c = initial_temp_c
	vessel.ph = 7.0
	vessel.headspace_volume_ml = 50.0
	vessel.pressure_kpa = 101.325

	_vessels[vessel_id] = vessel
	vessel_state_changed.emit(vessel_id, _vessel_to_dict(vessel))

	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func add_reagent(vessel_id: String, species_id: String, moles: float, concentration_m: float = 0.0) -> Dictionary:
	if not _vessels.has(vessel_id):
		return {"success": false, "error": "Vessel not found"}

	if not _reaction_evaluator.has_species(species_id):
		return {"success": false, "error": "Unknown species: %s" % species_id}

	if moles <= 0.0:
		return {"success": false, "error": "Moles must be positive"}

	var vessel = _vessels[vessel_id]
	var sp = _reaction_evaluator.get_species(species_id)

	vessel.species_moles[species_id] = vessel.species_moles.get(species_id, 0.0) + moles

	if vessel.volume_ml <= 0.0 and concentration_m > 0.0:
		vessel.volume_ml = (moles / concentration_m) * 1000.0
	elif vessel.volume_ml <= 0.0:
		var mass_g = moles * sp.molecular_weight_g_mol
		vessel.volume_ml = mass_g / sp.density_g_cm3

	_recalculate_concentrations(vessel)
	vessel.ph = _calculate_ph(vessel)

	if vessel.indicator_present:
		vessel.color_rgba = _reaction_evaluator.phenolphthalein_color(vessel.ph)

	vessel_state_changed.emit(vessel_id, _vessel_to_dict(vessel))
	return {"success": true, "vessel": _vessel_to_dict(vessel)}

func set_indicator(vessel_id: String, indicator_type: String = "phenolphthalein", enabled: bool = true) -> Dictionary:
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

func get_engine_mode() -> int:
	return _engine_mode

func force_embedded_fallback() -> void:
	_enable_embedded_fallback()

# =============================================================================
# EMBEDDED CHEMISTRY ENGINE (Core Calculations)
# =============================================================================

func _recalculate_concentrations(vessel: VesselState) -> void:
	vessel.species_concentrations.clear()
	if vessel.volume_ml <= 0.0:
		return
	var vol_l = vessel.volume_ml / 1000.0
	for species_id in vessel.species_moles:
		vessel.species_concentrations[species_id] = vessel.species_moles[species_id] / vol_l

func _calculate_ph(vessel: VesselState) -> float:
	var strong_acid_moles = 0.0
	var strong_base_moles = 0.0
	var weak_acids: Dictionary = {}
	var weak_bases: Dictionary = {}

	for species_id in vessel.species_moles:
		var moles = vessel.species_moles[species_id]
		if moles <= 0.0:
			continue

		var sp = _reaction_evaluator.get_species(species_id)

		if sp.is_acid:
			if sp.acid_pka < 0:
				strong_acid_moles += moles
			else:
				weak_acids[species_id] = { "moles": moles, "pka": sp.acid_pka }
		elif sp.is_base:
			if species_id in ["NaOH_aq", "KOH_aq"] or sp.acid_pka > 14:
				strong_base_moles += moles
			else:
				weak_bases[species_id] = { "moles": moles, "pka": sp.acid_pka }

	var net_h = strong_acid_moles - strong_base_moles
	var vol_l = max(vessel.volume_ml / 1000.0, 0.001)

	if net_h > 0:
		var h_conc = net_h / vol_l
		return clamp(-_log10(max(h_conc, 1e-14)), 0.0, 14.0)
	elif net_h < 0:
		var oh_conc = -net_h / vol_l
		var poh = -_log10(max(oh_conc, 1e-14))
		return clamp(14.0 - poh, 0.0, 14.0)
	else:
		if weak_acids.size() > 0 and weak_bases.size() > 0:
			var wa_id = weak_acids.keys()[0]
			var wb_id = weak_bases.keys()[0]
			var wa = weak_acids[wa_id]
			var wb = weak_bases[wb_id]
			var conc_a = wa.moles / vol_l
			var conc_b = wb.moles / vol_l
			return _reaction_evaluator.henderson_hasselbalch_ph(wa.pka, conc_b, conc_a)
		elif weak_acids.size() > 0:
			var wa = weak_acids.values()[0]
			var conc = wa.moles / vol_l
			if conc > 0:
				var h = sqrt(pow(10.0, -wa.pka) * conc)
				return clamp(-_log10(max(h, 1e-14)), 0.0, 14.0)
		elif weak_bases.size() > 0:
			var wb = weak_bases.values()[0]
			var conc = wb.moles / vol_l
			if conc > 0:
				var kb = pow(10.0, -(14.0 - wb.pka))
				var oh = sqrt(kb * conc)
				var poh = -_log10(max(oh, 1e-14))
				return clamp(14.0 - poh, 0.0, 14.0)

	return 7.0

func _log10(val: float) -> float:
	return _reaction_evaluator.log10(val)

func _execute_reactions(vessel: VesselState) -> Dictionary:
	var result = {
		"reaction_occurred": false,
		"reaction_type": ReactionType.NONE,
		"heat_released_kj": 0.0,
		"temperature_rise_c": 0.0,
		"products_formed": {},
		"consumed": {}
	}

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
			vessel.species_moles[acid_id] -= reacted
			vessel.species_moles[base_id] -= reacted

			vessel.species_moles["H2O"] = vessel.species_moles.get("H2O", 0.0) + reacted
			var salt_id = "NaCl_aq"
			if acid_id == "HCl_aq" and base_id == "NaOH_aq":
				salt_id = "NaCl_aq"
			vessel.species_moles[salt_id] = vessel.species_moles.get(salt_id, 0.0) + reacted

			result["reaction_occurred"] = true
			result["reaction_type"] = ReactionType.ACID_BASE_NEUTRALIZATION
			result["consumed"][acid_id] = reacted
			result["consumed"][base_id] = reacted
			result["products_formed"][salt_id] = reacted
			result["products_formed"]["H2O"] = reacted

			var heat_kj = reacted * abs(DELTA_H_NEUTRALIZATION_KJ_MOL) * _global_yield_modifier
			result["heat_released_kj"] = heat_kj

			var total_mass_g = vessel.volume_ml * WATER_DENSITY_G_ML
			var delta_t = _reaction_evaluator.calculate_adiabatic_temp_rise(
				DELTA_H_NEUTRALIZATION_KJ_MOL, reacted, total_mass_g, WATER_CP_J_G_K
			) * _global_yield_modifier
			vessel.temperature_c += delta_t
			result["temperature_rise_c"] = delta_t

			if vessel.temperature_c > 80.0:
				safety_warning.emit(vessel.vessel_id, "Temperature exceeds 80°C: %0.1f°C" % vessel.temperature_c)
			if vessel.temperature_c > 95.0:
				temperature_alert.emit(vessel.vessel_id, vessel.temperature_c, 95.0)
				vessel.safety_flags.append("THERMAL_HAZARD")

	_recalculate_concentrations(vessel)
	return result

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
# GLOBAL MODIFIERS (Talents, Equipment, Companions)
# =============================================================================

func set_global_yield_modifier(value: float) -> void:
	_global_yield_modifier = clamp(value, 0.1, 3.0)

func get_global_yield_modifier() -> float:
	return _global_yield_modifier

func set_global_purity_bonus(value: float) -> void:
	_global_purity_bonus = clamp(value, 0.5, 2.0)

func get_global_purity_bonus() -> float:
	return _global_purity_bonus

func set_global_speed_modifier(value: float) -> void:
	_global_speed_modifier = clamp(value, 0.1, 3.0)

func get_global_speed_modifier() -> float:
	return _global_speed_modifier

# =============================================================================
# THERMODYNAMICS QUERY (Cantera via IPC or Embedded)
# =============================================================================

func query_cantera_thermodynamics(reactants: Dictionary, products: Dictionary, temperature_c: float = 25.0) -> Dictionary:
	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		var future = { "pending": true }
		_send_ipc_request("CALCULATE_THERMODYNAMICS", {
			"reactants": reactants,
			"products": products,
			"temperature_c": temperature_c
		}, func(resp):
			future.pending = false
			future.result = resp
		)
		var start = Time.get_ticks_msec()
		while future.pending and Time.get_ticks_msec() - start < 500:
			_process_ipc_messages()
			OS.delay_msec(1)
		if not future.pending and future.has("result"):
			return future.result

	return _embedded_thermodynamics(reactants, products, temperature_c)

func _embedded_thermodynamics(reactants: Dictionary, products: Dictionary, temperature_c: float) -> Dictionary:
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

# =============================================================================
# RDKIT STRUCTURE QUERY
# =============================================================================

func query_rdkit_structure(smiles: String, compound_name: String = "") -> Dictionary:
	if _engine_mode == EngineMode.IPC_CONNECTED and not _use_embedded_fallback:
		var future = { "pending": true }
		_send_ipc_request("RDKIT_CONFORMER", {
			"smiles": smiles,
			"compound_name": compound_name
		}, func(resp):
			future.pending = false
			future.result = resp
		)
		var start = Time.get_ticks_msec()
		while future.pending and Time.get_ticks_msec() - start < 500:
			_process_ipc_messages()
			OS.delay_msec(1)
		if not future.pending and future.has("result"):
			return future.result

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
# SELF-TESTS
# =============================================================================

func run_self_tests() -> Dictionary:
	var results = { "passed": 0, "failed": 0, "tests": [] }

	var neut_test = _reaction_evaluator.verify_neutralization_constants()
	results.tests.append({
		"name": "Neutralization ΔH verification",
		"passed": neut_test.within_tolerance_5_percent,
		"detail": "Calculated: %0.2f kJ/mol, Expected: -57.1 kJ/mol" % neut_test.calculated_delta_h_kj_mol
	})

	var ph = _reaction_evaluator.henderson_hasselbalch_ph(4.76, 0.1, 0.1)
	results.tests.append({
		"name": "Henderson-Hasselbalch pH = pKa at equal concentrations",
		"passed": abs(ph - 4.76) < 0.01,
		"detail": "pH = %0.2f" % ph
	})

	var col1 = _reaction_evaluator.phenolphthalein_color(7.0)
	var col2 = _reaction_evaluator.phenolphthalein_color(8.5)
	var col3 = _reaction_evaluator.phenolphthalein_color(9.5)
	results.tests.append({
		"name": "Phenolphthalein color transitions",
		"passed": col1.a == 0.0 and col2.a > 0.0 and col3 == COLOR_VIBRANT_MAGENTA,
		"detail": "pH 7: alpha=%0.2f, pH 8.5: alpha=%0.2f, pH 9.5: magenta=%s" % [col1.a, col2.a, col3 == COLOR_VIBRANT_MAGENTA]
	})

	var k1 = _reaction_evaluator.calculate_arrhenius_k(25.0, 50.0, 1e10)
	var k2 = _reaction_evaluator.calculate_arrhenius_k(50.0, 50.0, 1e10)
	results.tests.append({
		"name": "Arrhenius temperature acceleration",
		"passed": k2 > k1 * 2.0,
		"detail": "k(25°C)=%e, k(50°C)=%e, ratio=%0.1f" % [k1, k2, k2/k1]
	})

	var precip = _reaction_evaluator.solubility_product_check(1e-4, 1e-4, 1e-10)
	results.tests.append({
		"name": "Solubility product precipitation check",
		"passed": precip == true,
		"detail": "[Ag+]=1e-4, [Cl-]=1e-4, Ksp=1e-10 -> precipitate=%s" % precip
	})

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