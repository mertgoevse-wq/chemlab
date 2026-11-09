# ChemLab 3D Laboratory Simulation (Godot 4 Engine)
# Apparatus: NMR Spectrometer (Nuclear Magnetic Resonance)
# Features:
# 1. First-person interaction with sample insertion/removal
# 2. Sample analysis request via SimulationBridge IPC to Python AnalyticalEngine
# 3. Real-time spectrum visualization on display screen
# 4. Quest integration for "First NMR Analysis" research objective
# 5. Scientific data display with chemical shift (ppm), coupling constants, integration

class_name NMRSpectrometer
extends StaticBody3D

# =============================================================================
# SIGNALS
# =============================================================================

signal power_toggled(is_powered: bool)
signal sample_inserted(sample_info: Dictionary)
signal sample_removed(sample_info: Dictionary)
signal analysis_started(sample_id: String)
signal analysis_completed(sample_id: String, spectrum_data: Dictionary)
signal analysis_failed(sample_id: String, error: String)
signal spectrum_updated(spectrum_data: Dictionary)

# =============================================================================
# EXPORTED PARAMETERS
# =============================================================================

@export_group("Operational Limits")
@export var is_powered_on: bool = true
@export var magnetic_field_strength_t: float = 9.4  # Tesla (400 MHz proton frequency)
@export var sample_temperature_c: float = 25.0
@export var max_sample_queue: int = 10

@export_group("NMR Parameters")
@export var spectral_width_ppm: float = 12.0
@export var acquisition_time_sec: float = 2.5
@export var relaxation_delay_sec: float = 1.0
@export var number_of_scans: int = 16

@export_group("Display Settings")
@export var spectrum_x_min_ppm: float = -1.0
@export var spectrum_x_max_ppm: float = 11.0
@export var auto_phase_correction: bool = true
@export var auto_baseline_correction: bool = true

# =============================================================================
# NODE REFERENCES
# =============================================================================

@onready var magnet_housing: MeshInstance3D = get_node_or_null("MagnetHousing")
@onready var bore_collision: Area3D = get_node_or_null("BoreCollision")
@onready var sample_tube_slot: Marker3D = get_node_or_null("SampleTubeSlot")
@onready var display_screen: MeshInstance3D = get_node_or_null("DisplayScreen")
@onready var screen_material: StandardMaterial3D = display_screen.material_override if display_screen else null
@onready var console_unit: MeshInstance3D = get_node_or_null("ConsoleUnit")
@onready var power_switch: MeshInstance3D = get_node_or_null("PowerSwitch")
@onready var status_led: OmniLight3D = get_node_or_null("StatusLED")
@onready var insertion_sensor: Area3D = get_node_or_null("InsertionSensor")
@onready var audio_motor: AudioStreamPlayer3D = get_node_or_null("MotorAudio")
@onready var audio_shim: AudioStreamPlayer3D = get_node_or_null("ShimAudio")
@onready var interaction_trigger: Area3D = get_node_or_null("InteractionTrigger")

# =============================================================================
# RUNTIME SIMULATION STATE
# =============================================================================

var current_sample: Node = null
var sample_queue: Array[Dictionary] = []
var is_analyzing: bool = false
var current_spectrum_data: Dictionary = {}
var shim_quality: float = 1.0  # 0.0 to 1.0
var analysis_progress: float = 0.0

# Spectral simulation constants
const PROTON_GYROMAGNETIC_RATIO: float = 267.522e6  # rad/s/T
const DEFAULT_SPECTROMETER_FREQ_MHZ: float = 400.0  # 9.4 T magnet

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	add_to_group("interactive_apparatus")
	add_to_group("apparatus")
	add_to_group("interactable")
	set_meta("is_apparatus", true)
	set_meta("apparatus_type", "nmr_spectrometer")
	set_meta("apparatus_name", "NMR Spectrometer (400 MHz)")

	_setup_audio_players()
	_setup_interaction_trigger()
	_setup_bore_collision()
	_update_display_state()
	_update_status_led()

	print(">>> [NMRSpectrometer] 400 MHz NMR Spectrometer initialized. Awaiting sample.")


func _setup_audio_players() -> void:
	if not audio_motor:
		audio_motor = AudioStreamPlayer3D.new()
		audio_motor.name = "MotorAudio"
		audio_motor.unit_size = 3.0
		audio_motor.max_distance = 15.0
		audio_motor.volume_db = -10.0
		add_child(audio_motor)

	if not audio_shim:
		audio_shim = AudioStreamPlayer3D.new()
		audio_shim.name = "ShimAudio"
		audio_shim.unit_size = 2.0
		audio_shim.max_distance = 8.0
		audio_shim.volume_db = -15.0
		add_child(audio_shim)

	# Load audio streams if available
	if ResourceLoader.exists("res://audio/nmr_magnet_hum.wav"):
		audio_motor.stream = load("res://audio/nmr_magnet_hum.wav")
	if ResourceLoader.exists("res://audio/nmr_shim_pulse.wav"):
		audio_shim.stream = load("res://audio/nmr_shim_pulse.wav")


func _setup_interaction_trigger() -> void:
	if not interaction_trigger:
		interaction_trigger = get_node_or_null("InteractionTrigger")
	if interaction_trigger:
		if not interaction_trigger.body_entered.is_connected(_on_interaction_body_entered):
			interaction_trigger.body_entered.connect(_on_interaction_body_entered)
		if not interaction_trigger.body_exited.is_connected(_on_interaction_body_exited):
			interaction_trigger.body_exited.connect(_on_interaction_body_exited)


func _setup_bore_collision() -> void:
	if not bore_collision:
		bore_collision = get_node_or_null("BoreCollision")
	if bore_collision:
		if not bore_collision.body_entered.is_connected(_on_bore_body_entered):
			bore_collision.body_entered.connect(_on_bore_body_entered)
		if not bore_collision.body_exited.is_connected(_on_bore_body_exited):
			bore_collision.body_exited.connect(_on_bore_body_exited)


func _setup_insertion_sensor() -> void:
	if not insertion_sensor:
		insertion_sensor = get_node_or_null("InsertionSensor")
	if insertion_sensor:
		if not insertion_sensor.body_entered.is_connected(_on_insertion_sensor_body_entered):
			insertion_sensor.body_entered.connect(_on_insertion_sensor_body_entered)
		if not insertion_sensor.body_exited.is_connected(_on_insertion_sensor_body_exited):
			insertion_sensor.body_exited.connect(_on_insertion_sensor_body_exited)


# =============================================================================
# INTERACTION SYSTEM
# =============================================================================

func _on_interaction_body_entered(body: Node3D) -> void:
	if body.is_in_group("player") or body.get_class() == "PlayerController":
		# Player is near the NMR - could show interaction hint
		pass


func _on_interaction_body_exited(body: Node3D) -> void:
	pass


func _on_bore_body_entered(body: Node3D) -> void:
	# Sample tube or vessel entering the magnet bore
	if body.is_in_group("sample_tube") or body.has_meta("sample_type"):
		_insert_sample(body)


func _on_bore_body_exited(body: Node3D) -> void:
	if body == current_sample:
		_remove_sample()


func _on_insertion_sensor_body_entered(body: Node3D) -> void:
	# Fine-grained detection for sample insertion
	if body.is_in_group("sample_tube") or body.has_meta("sample_type"):
		_insert_sample(body)


func _on_insertion_sensor_body_exited(body: Node3D) -> void:
	if body == current_sample:
		_remove_sample()


# =============================================================================
# SAMPLE MANAGEMENT
# =============================================================================

func _insert_sample(sample_node: Node3D) -> void:
	if current_sample != null:
		print("[NMRSpectrometer] Sample already present, ignoring new insertion")
		return

	current_sample = sample_node

	# Extract sample metadata
	var sample_info = _extract_sample_metadata(sample_node)
	sample_info["insertion_time"] = Time.get_unix_time_from_system()
	sample_info["sample_id"] = _generate_sample_id()

	# Position sample in bore
	if sample_tube_slot:
		sample_node.global_position = sample_tube_slot.global_position
		sample_node.global_rotation = sample_tube_slot.global_rotation

	# Add to queue
	sample_queue.append(sample_info)
	sample_inserted.emit(sample_info)

	# Update display
	_update_display_state()

	# Auto-start analysis if only sample
	if sample_queue.size() == 1 and not is_analyzing:
		_start_next_analysis()

	print("[NMRSpectrometer] Sample inserted: ", sample_info["sample_id"])


func _remove_sample() -> void:
	if current_sample == null:
		return

	var sample_info = _extract_sample_metadata(current_sample)
	sample_removed.emit(sample_info)

	# Remove from queue if present
	for i in range(sample_queue.size()):
		if sample_queue[i].get("sample_id") == sample_info.get("sample_id"):
			sample_queue.remove_at(i)
			break

	current_sample = null
	_update_display_state()
	print("[NMRSpectrometer] Sample removed")


func _extract_sample_metadata(sample_node: Node3D) -> Dictionary:
	var metadata = {
		"name": sample_node.name,
		"sample_type": sample_node.get_meta("sample_type", "unknown"),
		"compound_name": sample_node.get_meta("compound_name", "Unknown Compound"),
		"concentration_mM": sample_node.get_meta("concentration_mM", 50.0),
		"solvent": sample_node.get_meta("solvent", "CDCl3"),
		"temperature_c": sample_temperature_c,
		"volume_ml": sample_node.get_meta("volume_ml", 0.6),
	}
	return metadata


func _generate_sample_id() -> String:
	return "NMR_" + str(Time.get_unix_time_from_system()) + "_" + str(randi_range(1000, 9999))


# =============================================================================
# ANALYSIS PIPELINE
# =============================================================================

func _start_next_analysis() -> void:
	if sample_queue.is_empty() or is_analyzing:
		return

	is_analyzing = true
	analysis_progress = 0.0

	var sample_info = sample_queue[0]
	analysis_started.emit(sample_info["sample_id"])

	# Simulate shimming process
	_run_shimming_sequence(sample_info)

	# Request analysis via SimulationBridge (IPC to Python)
	_request_nmr_analysis(sample_info)


func _run_shimming_sequence(sample_info: Dictionary) -> void:
	# Simulate shimming - affects spectral resolution
	if audio_shim:
		audio_shim.play()

	# Quality depends on sample properties and magnet stability
	shim_quality = 0.85 + randf_range(0.0, 0.15)
	shim_quality = clamp(shim_quality, 0.5, 1.0)

	# Simulate shim time
	await get_tree().create_timer(1.5).timeout

	if is_instance_valid(self):
		# Shimming complete, proceed to acquisition
		_start_acquisition(sample_info)


func _start_acquisition(sample_info: Dictionary) -> void:
	if audio_motor:
		audio_motor.play()

	# Simulate acquisition time
	var acq_time = acquisition_time_sec
	await get_tree().create_timer(acq_time).timeout

	if is_instance_valid(self):
		# Acquisition complete, process FID to spectrum
		_process_fid_to_spectrum(sample_info)


func _request_nmr_analysis(sample_info: Dictionary) -> void:
	# Send IPC request to Python AnalyticalEngine via SimulationBridge
	var sim_bridge = get_node_or_null("/root/SimulationBridge")
	if sim_bridge and sim_bridge.has_method("request_nmr_analysis"):
		var request = {
			"sample_id": sample_info["sample_id"],
			"compound_name": sample_info["compound_name"],
			"concentration_mM": sample_info["concentration_mM"],
			"solvent": sample_info["solvent"],
			"temperature_c": sample_info["temperature_c"],
			"magnetic_field_t": magnetic_field_strength_t,
			"spectral_width_ppm": spectral_width_ppm,
			"number_of_scans": number_of_scans,
			"relaxation_delay_sec": relaxation_delay_sec,
		}
		sim_bridge.request_nmr_analysis(request)
	else:
		# Fallback: simulate locally
		_simulate_nmr_spectrum_locally(sample_info)


func _simulate_nmr_spectrum_locally(sample_info: Dictionary) -> void:
	# Local simulation when IPC not available
	var compound = sample_info["compound_name"]
	var spectrum = _generate_simulated_spectrum(compound, sample_info)

	# Apply shim quality to line widths
	_apply_shim_broadening(spectrum)

	# Store and emit
	current_spectrum_data = spectrum
	spectrum_updated.emit(spectrum)
	analysis_completed.emit(sample_info["sample_id"], spectrum)

	# Complete analysis
	_complete_analysis(sample_info["sample_id"])


func _process_fid_to_spectrum(sample_info: Dictionary) -> void:
	# In real implementation, this would process actual FID data from Python
	# For now, simulate based on compound structure
	var compound = sample_info["compound_name"]
	var spectrum = _generate_simulated_spectrum(compound, sample_info)

	# Apply shim quality
	_apply_shim_broadening(spectrum)

	current_spectrum_data = spectrum
	spectrum_updated.emit(spectrum)
	analysis_completed.emit(sample_info["sample_id"], spectrum)

	_complete_analysis(sample_info["sample_id"])


func _generate_simulated_spectrum(compound_name: String, sample_info: Dictionary) -> Dictionary:
	# Generate realistic NMR spectrum based on known chemical shifts
	var peaks = _get_chemical_shifts_for_compound(compound_name)
	var concentration = sample_info.get("concentration_mM", 50.0)
	var solvent = sample_info.get("solvent", "CDCl3")

	# Generate spectrum data points
	var n_points = 16384
	var x_min = spectrum_x_min_ppm
	var x_max = spectrum_x_max_ppm
	var x_step = (x_max - x_min) / n_points

	var x_data = []
	var y_data = []

	for i in range(n_points):
		var ppm = x_min + i * x_step
		var intensity = 0.0

		# Sum Lorentzian peaks
		for peak in peaks:
			var center = peak["ppm"]
			var width = peak["width"] / shim_quality  # Broader with poor shim
			var height = peak["intensity"] * (concentration / 50.0)

			# Lorentzian lineshape
			var delta = ppm - center
			intensity += height * (width * width) / (delta * delta + width * width)

		# Add solvent peak if applicable
		if solvent == "CDCl3":
			var chcl3_center = 7.26
			var delta = ppm - chcl3_center
			intensity += 0.1 * (0.01 * 0.01) / (delta * delta + 0.01 * 0.01)
		elif solvent == "DMSO-d6":
			var dmso_center = 2.50
			var delta = ppm - dmso_center
			intensity += 0.1 * (0.01 * 0.01) / (delta * delta + 0.01 * 0.01)

		# Add noise
		intensity += randf_range(-0.002, 0.002)

		x_data.append(ppm)
		y_data.append(max(0.0, intensity))

	return {
		"sample_id": sample_info.get("sample_id", "unknown"),
		"compound_name": compound_name,
		"x_ppm": x_data,
		"y_intensity": y_data,
		"peaks": peaks,
		"solvent": sample_info.get("solvent", "CDCl3"),
		"temperature_c": sample_temperature_c,
		"magnetic_field_t": magnetic_field_strength_t,
		"spectrometer_freq_mhz": DEFAULT_SPECTROMETER_FREQ_MHZ,
		"acquisition_params": {
			"spectral_width_ppm": spectral_width_ppm,
			"number_of_scans": number_of_scans,
			"relaxation_delay_sec": relaxation_delay_sec,
		},
		"shim_quality": shim_quality,
		"timestamp": Time.get_unix_time_from_system(),
	}


func _get_chemical_shifts_for_compound(compound_name: String) -> Array[Dictionary]:
	# Known chemical shifts for common compounds (ppm, multiplicity, J_coupling, integration)
	var shifts = {
		"ethanol": [
			{"ppm": 1.18, "multiplicity": "t", "J_hz": 7.0, "integration": 3, "assignment": "CH3", "width": 0.02},
			{"ppm": 3.65, "multiplicity": "q", "J_hz": 7.0, "integration": 2, "assignment": "CH2", "width": 0.02},
			{"ppm": 2.60, "multiplicity": "s", "J_hz": 0.0, "integration": 1, "assignment": "OH", "width": 0.03},
		],
		"acetone": [
			{"ppm": 2.17, "multiplicity": "s", "J_hz": 0.0, "integration": 6, "assignment": "2x CH3", "width": 0.015},
		],
		"acetic_acid": [
			{"ppm": 2.09, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "CH3", "width": 0.015},
			{"ppm": 11.5, "multiplicity": "s", "J_hz": 0.0, "integration": 1, "assignment": "COOH", "width": 0.05},
		],
		"ethyl_acetate": [
			{"ppm": 1.26, "multiplicity": "t", "J_hz": 7.1, "integration": 3, "assignment": "CH3CH2", "width": 0.02},
			{"ppm": 2.04, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "COCH3", "width": 0.015},
			{"ppm": 4.12, "multiplicity": "q", "J_hz": 7.1, "integration": 2, "assignment": "OCH2", "width": 0.02},
		],
		"benzene": [
			{"ppm": 7.27, "multiplicity": "s", "J_hz": 0.0, "integration": 6, "assignment": "Ar-H", "width": 0.01},
		],
		"toluene": [
			{"ppm": 2.34, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "CH3", "width": 0.015},
			{"ppm": 7.18, "multiplicity": "m", "J_hz": 7.5, "integration": 5, "assignment": "Ar-H", "width": 0.02},
		],
		"aspirin": [
			{"ppm": 2.31, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "OCOCH3", "width": 0.015},
			{"ppm": 7.0, "multiplicity": "m", "J_hz": 8.0, "integration": 4, "assignment": "Ar-H", "width": 0.02},
			{"ppm": 8.0, "multiplicity": "dd", "J_hz": [8.0, 1.5], "integration": 1, "assignment": "Ar-H", "width": 0.02},
		],
		"paracetamol": [
			{"ppm": 2.09, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "CH3", "width": 0.015},
			{"ppm": 6.75, "multiplicity": "d", "J_hz": 8.5, "integration": 2, "assignment": "Ar-H", "width": 0.02},
			{"ppm": 7.35, "multiplicity": "d", "J_hz": 8.5, "integration": 2, "assignment": "Ar-H", "width": 0.02},
			{"ppm": 9.8, "multiplicity": "s", "J_hz": 0.0, "integration": 1, "assignment": "NH/OH", "width": 0.03},
		],
		"caffeine": [
			{"ppm": 3.38, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "N-CH3", "width": 0.015},
			{"ppm": 3.52, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "N-CH3", "width": 0.015},
			{"ppm": 3.98, "multiplicity": "s", "J_hz": 0.0, "integration": 3, "assignment": "N-CH3", "width": 0.015},
			{"ppm": 7.95, "multiplicity": "s", "J_hz": 0.0, "integration": 1, "assignment": "C-H", "width": 0.02},
		],
		"glucose": [
			{"ppm": 3.2, "multiplicity": "m", "J_hz": 7.0, "integration": 1, "assignment": "H-2", "width": 0.03},
			{"ppm": 3.4, "multiplicity": "m", "J_hz": 7.0, "integration": 1, "assignment": "H-3", "width": 0.03},
			{"ppm": 3.45, "multiplicity": "m", "J_hz": 7.0, "integration": 1, "assignment": "H-4", "width": 0.03},
			{"ppm": 3.7, "multiplicity": "m", "J_hz": 7.0, "integration": 1, "assignment": "H-5", "width": 0.03},
			{"ppm": 3.85, "multiplicity": "m", "J_hz": 7.0, "integration": 2, "assignment": "H-6", "width": 0.03},
			{"ppm": 5.23, "multiplicity": "d", "J_hz": 3.8, "integration": 1, "assignment": "H-1 (alpha)", "width": 0.02},
			{"ppm": 4.63, "multiplicity": "d", "J_hz": 7.8, "integration": 1, "assignment": "H-1 (beta)", "width": 0.02},
		],
	}

	var name_lower = compound_name.to_lower()
	if shifts.has(name_lower):
		return shifts[name_lower]

	# Default: generate generic peaks
	return _generate_generic_peaks()


func _generate_generic_peaks() -> Array[Dictionary]:
	# Generate 3-5 random peaks in typical organic region
	var peaks = []
	var n_peaks = randi_range(3, 5)

	for i in range(n_peaks):
		var ppm = randf_range(0.5, 9.5)
		var mult_types = ["s", "d", "t", "q", "m"]
		var mult = mult_types[randi_range(0, mult_types.size() - 1)]
		var J = 0.0
		if mult != "s" and mult != "m":
			J = randf_range(5.0, 12.0)

		peaks.append({
			"ppm": ppm,
			"multiplicity": mult,
			"J_hz": J,
			"integration": randi_range(1, 3),
			"assignment": "Unknown",
			"width": randf_range(0.01, 0.03),
		})

	return peaks


func _apply_shim_broadening(spectrum: Dictionary) -> void:
	# Broaden peaks based on shim quality
	if not spectrum.has("peaks"):
		return

	for peak in spectrum["peaks"]:
		peak["width"] = peak["width"] / shim_quality


func _complete_analysis(sample_id: String) -> void:
	is_analyzing = false
	analysis_progress = 1.0

	# Remove completed sample from queue
	if sample_queue.size() > 0:
		sample_queue.remove_at(0)

	# Process next sample if available
	if sample_queue.size() > 0:
		_start_next_analysis()
	else:
		_update_display_state()
		if audio_motor:
			audio_motor.stop()


# =============================================================================
# DISPLAY & VISUALIZATION
# =============================================================================

func _update_display_state() -> void:
	# Update display screen material based on current state
	if not display_screen or not screen_material:
		return

	var mat = display_screen.get_surface_override_material(0)
	if not mat:
		mat = StandardMaterial3D.new()
		display_screen.set_surface_override_material(0, mat)
		screen_material = mat

	if current_spectrum_data.has("y_intensity"):
		# Show spectrum on screen
		mat.albedo_color = Color(0.02, 0.02, 0.05)
		mat.emission_enabled = true
		mat.emission_energy_multiplier = 3.0
		# In a full implementation, we'd use a ViewportTexture to render the actual spectrum
	else:
		# Show idle state
		mat.albedo_color = Color(0.1, 0.1, 0.15)
		mat.emission_enabled = false
		mat.emission_energy_multiplier = 0.0


func _update_status_led() -> void:
	if not status_led:
		return

	if is_analyzing:
		status_led.light_color = Color(0.0, 1.0, 1.0)  # Cyan - analyzing
		status_led.light_energy = 2.0
	elif current_sample != null:
		status_led.light_color = Color(1.0, 1.0, 0.0)  # Yellow - sample ready
		status_led.light_energy = 1.5
	elif is_powered_on:
		status_led.light_color = Color(0.0, 1.0, 0.0)  # Green - ready
		status_led.light_energy = 1.0
	else:
		status_led.light_color = Color(0.5, 0.5, 0.5)  # Gray - off
		status_led.light_energy = 0.5


# =============================================================================
# PUBLIC API
# =============================================================================

func get_interaction_info() -> Dictionary:
	return {
		"name": "NMR Spectrometer (400 MHz)",
		"can_pickup": false,
		"prompt": "[E] Insert/Remove Sample | [Left Click] Start Analysis | [Right Click] View Spectrum",
		"hints": "Insert sample tube into magnet bore. Left click to start analysis. Right click to view spectrum.",
	}


func on_picked_up(player: Node) -> void:
	# NMR is not pickupable
	pass


func on_dropped(player: Node) -> void:
	pass


func interact(player: Node) -> void:
	# Toggle power or open sample door
	if is_powered_on:
		# If sample present, start analysis
		if current_sample != null and not is_analyzing:
			_start_next_analysis()
		elif current_sample == null:
			print("[NMRSpectrometer] No sample inserted. Insert a sample tube first.")
	else:
		toggle_power()


func toggle_power() -> void:
	is_powered_on = !is_powered_on
	power_toggled.emit(is_powered_on)
	_update_status_led()

	if is_powered_on:
		print("[NMRSpectrometer] Powered ON - Magnet ramp up sequence initiated")
		if audio_motor:
			audio_motor.play()
	else:
		print("[NMRSpectrometer] Powered OFF - Magnet ramp down")
		if audio_motor:
			audio_motor.stop()
		if audio_shim:
			audio_shim.stop()


func get_current_spectrum() -> Dictionary:
	return current_spectrum_data


func get_sample_queue() -> Array:
	return sample_queue.duplicate()


# =============================================================================
# QUEST INTEGRATION
# =============================================================================

func _notify_quest_manager(event_type: String, data: Dictionary) -> void:
	var quest_manager = get_node_or_null("/root/QuestManager")
	if quest_manager and quest_manager.has_method("on_apparatus_event"):
		quest_manager.on_apparatus_event("nmr_spectrometer", event_type, data)


# Called when analysis completes - could trigger quest progress
func _on_analysis_complete_for_quest(sample_id: String, spectrum: Dictionary) -> void:
	_notify_quest_manager("nmr_analysis_complete", {
		"sample_id": sample_id,
		"compound_identified": spectrum.get("compound_name", "unknown"),
		"peak_count": spectrum.get("peaks", []).size(),
	})


# =============================================================================
# SAVE/LOAD SUPPORT
# =============================================================================

func get_save_data() -> Dictionary:
	return {
		"is_powered_on": is_powered_on,
		"magnetic_field_strength_t": magnetic_field_strength_t,
		"sample_temperature_c": sample_temperature_c,
		"spectral_width_ppm": spectral_width_ppm,
		"acquisition_time_sec": acquisition_time_sec,
		"relaxation_delay_sec": relaxation_delay_sec,
		"number_of_scans": number_of_scans,
		"current_spectrum": current_spectrum_data,
		"shim_quality": shim_quality,
		"sample_queue": sample_queue,
	}


func load_save_data(data: Dictionary) -> void:
	is_powered_on = data.get("is_powered_on", true)
	magnetic_field_strength_t = data.get("magnetic_field_strength_t", 9.4)
	sample_temperature_c = data.get("sample_temperature_c", 25.0)
	spectral_width_ppm = data.get("spectral_width_ppm", 12.0)
	acquisition_time_sec = data.get("acquisition_time_sec", 2.5)
	relaxation_delay_sec = data.get("relaxation_delay_sec", 1.0)
	number_of_scans = data.get("number_of_scans", 16)
	current_spectrum_data = data.get("current_spectrum", {})
	shim_quality = data.get("shim_quality", 1.0)
	sample_queue = data.get("sample_queue", [])

	_update_display_state()
	_update_status_led()