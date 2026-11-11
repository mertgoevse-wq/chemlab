# Athanor Ascension — Laboratory Apparatus Suite
# Complete interactive simulation & guided step-by-step controllers for:
# 1. Rotary Evaporator (Rotovap)
# 2. Schlenk Line (Dual Inert Gas / High Vacuum Manifold)
# 3. Analytical Balance & Micropipettes
# 4. High-Performance Liquid & Gas Chromatography (HPLC & GC-MS)
# 5. Soxhlet Extractor (Solid-Liquid Continuous Extraction)
# 6. UV-Vis Spectrophotometer (Beer-Lambert & Spectral Scanning)
# 7. Glovebox (Hermetic Inert Atmosphere Workstation <0.1 ppm O2/H2O)
# 8. High-Speed Centrifuge & Buchner Vacuum Filtration

class_name ApparatusSuite
extends RefCounted

# =============================================================================
# 1. ROTARY EVAPORATOR (ROTOVAP) CONTROLLER
# =============================================================================
class RotovapController extends RefCounted:
	enum State { OFF, ASSEMBLED, HEATING, ROTATING, EVACUATING, DISTILLING, BUMPED, VENTING, COMPLETE }

	var state: State = State.OFF
	var bath_temp_c: float = 22.0
	var bath_target_c: float = 45.0
	var chiller_temp_c: float = 20.0
	var chiller_target_c: float = -5.0
	var rotation_rpm: float = 0.0
	var rotation_target_rpm: float = 120.0
	var vacuum_mbar: float = 1013.25
	var vacuum_target_mbar: float = 45.0
	var flask_volume_ml: float = 250.0
	var solvent_volume_ml: float = 100.0
	var collected_distillate_ml: float = 0.0
	var solvent_name: String = "Ethanol"
	var solvent_bp_1atm_c: float = 78.37
	var keck_clip_secured: bool = false
	var bath_raised: bool = false
	var stopcock_closed: bool = false
	var bump_risk: float = 0.0
	var distillation_rate_ml_min: float = 0.0

	var tutorial_step: int = 0
	const TUTORIAL_STEPS: Array[String] = [
		"1. Secure evaporating flask to vapor duct using Keck clip",
		"2. Turn on recirculating chiller (target <= 0°C)",
		"3. Set water bath temperature (target 40-50°C)",
		"4. Start flask rotation (100 - 150 RPM) to form thin liquid film",
		"5. Close vacuum release stopcock and engage vacuum pump",
		"6. Lower flask into heated water bath once vacuum stabilizes",
		"7. Monitor condensation ring on coil condenser until distillation finishes",
		"8. Raise flask from bath, stop rotation, and open stopcock to vent vacuum"
	]

	func update(delta: float) -> Dictionary:
		# Thermal dynamics
		if state in [State.HEATING, State.ROTATING, State.EVACUATING, State.DISTILLING]:
			bath_temp_c = move_toward(bath_temp_c, bath_target_c, delta * 0.8)
			chiller_temp_c = move_toward(chiller_temp_c, chiller_target_c, delta * 1.2)
			rotation_rpm = move_toward(rotation_rpm, rotation_target_rpm, delta * 30.0)

		# Vacuum pump dynamics
		if stopcock_closed and state in [State.EVACUATING, State.DISTILLING]:
			vacuum_mbar = move_toward(vacuum_mbar, vacuum_target_mbar, delta * 80.0)
		elif not stopcock_closed:
			vacuum_mbar = move_toward(vacuum_mbar, 1013.25, delta * 300.0)

		# Clausius-Clapeyron effective boiling point calculation
		var effective_bp = solvent_bp_1atm_c - (1013.25 - vacuum_mbar) * 0.045

		# Distillation rate and bumping mechanics
		if bath_raised and bath_temp_c > effective_bp and vacuum_mbar < 300.0 and rotation_rpm > 40.0:
			if rotation_rpm < 50.0 and vacuum_mbar < 100.0 and bath_temp_c > effective_bp + 15.0:
				# Violent bumping into condenser
				state = State.BUMPED
				bump_risk = 1.0
			else:
				state = State.DISTILLING
				var delta_t = maxf(0.0, bath_temp_c - effective_bp)
				distillation_rate_ml_min = 0.05 * rotation_rpm * (delta_t / 10.0)
				var evaporated = (distillation_rate_ml_min / 60.0) * delta
				evaporated = minf(evaporated, solvent_volume_ml)
				solvent_volume_ml -= evaporated
				collected_distillate_ml += evaporated
				if solvent_volume_ml <= 0.5:
					state = State.COMPLETE
		else:
			distillation_rate_ml_min = 0.0

		return get_status()

	func secure_keck_clip(secured: bool) -> bool:
		keck_clip_secured = secured
		if secured and tutorial_step == 0:
			tutorial_step = 1
		return true

	func toggle_bath_lift(raised: bool) -> bool:
		bath_raised = raised
		if raised and tutorial_step == 5:
			tutorial_step = 6
		return true

	func set_stopcock(closed: bool) -> void:
		stopcock_closed = closed
		if closed and tutorial_step == 4:
			tutorial_step = 5

	func get_status() -> Dictionary:
		return {
			"state": State.keys()[state],
			"bath_temp_c": roundf(bath_temp_c * 10.0) / 10.0,
			"chiller_temp_c": roundf(chiller_temp_c * 10.0) / 10.0,
			"rotation_rpm": roundf(rotation_rpm),
			"vacuum_mbar": roundf(vacuum_mbar * 10.0) / 10.0,
			"solvent_volume_ml": roundf(solvent_volume_ml * 10.0) / 10.0,
			"collected_distillate_ml": roundf(collected_distillate_ml * 10.0) / 10.0,
			"distillation_rate_ml_min": roundf(distillation_rate_ml_min * 100.0) / 100.0,
			"tutorial_step": tutorial_step,
			"current_instruction": TUTORIAL_STEPS[clampi(tutorial_step, 0, TUTORIAL_STEPS.size() - 1)]
		}

# =============================================================================
# 2. SCHLENK LINE (INERT GAS / VACUUM MANIFOLD) CONTROLLER
# =============================================================================
class SchlenkLineController extends RefCounted:
	enum ValvePosition { CLOSED, VACUUM, INERT_GAS }
	enum State { IDLE, VACUUM_ACTIVE, INERT_ACTIVE, PURGING_CYCLE, EQUILIBRATED, PYROPHORIC_TRANSFER }

	var argon_pressure_psi: float = 15.0
	var vacuum_pressure_mbar: float = 1013.25
	var oil_bubbler_rate_bps: float = 1.0  # bubbles per second
	var cold_trap_temp_c: float = 20.0
	var cold_trap_filled_ln2: bool = false
	var ports_valves: Array[int] = [ValvePosition.CLOSED, ValvePosition.CLOSED, ValvePosition.CLOSED, ValvePosition.CLOSED]
	var purge_cycle_counts: Array[int] = [0, 0, 0, 0]
	var port_atmospheres: Array[Dictionary] = []

	var tutorial_step: int = 0
	const TUTORIAL_STEPS: Array[String] = [
		"1. Fill liquid nitrogen (-196°C) cold trap before engaging high-vacuum pump",
		"2. Verify positive argon pressure on mineral oil bubbler (1-2 bubbles/second)",
		"3. Connect reaction flask to Port 1 via thick-walled vacuum tubing",
		"4. Cycle 1: Turn Port 1 to VACUUM line, pump down to < 0.1 mbar for 3 minutes",
		"5. Cycle 1: Turn Port 1 to ARGON line, backfill with inert gas until bubbler accelerates",
		"6. Repeat Evacuate-Refill purge protocol 2 more times (total 3x purge cycles)",
		"7. Port is now inert (< 1 ppm O2) and safe for pyrophoric reagent cannula transfer"
	]

	func _init() -> void:
		port_atmospheres.resize(4)
		for i in range(4):
			port_atmospheres[i] = { "oxygen_ppm": 209000.0, "argon_pct": 0.93, "purged": false }

	func fill_cold_trap(with_ln2: bool) -> void:
		cold_trap_filled_ln2 = with_ln2
		if with_ln2:
			cold_trap_temp_c = -196.0
			if tutorial_step == 0:
				tutorial_step = 1

	func set_port_valve(port_idx: int, pos: ValvePosition) -> Dictionary:
		if port_idx < 0 or port_idx >= 4:
			return { "success": false, "error": "Invalid port index" }

		ports_valves[port_idx] = pos
		var result = { "success": true, "port": port_idx, "position": pos }

		if pos == ValvePosition.VACUUM:
			if not cold_trap_filled_ln2:
				result["warning"] = "HAZARD: Solvent vapors will contaminate pump oil! Fill liquid nitrogen cold trap first."
			# Reduce O2 ppm exponentially
			var cur_o2 = port_atmospheres[port_idx]["oxygen_ppm"]
			port_atmospheres[port_idx]["oxygen_ppm"] = cur_o2 * 0.05
		elif pos == ValvePosition.INERT_GAS:
			purge_cycle_counts[port_idx] += 1
			var cur_o2 = port_atmospheres[port_idx]["oxygen_ppm"]
			port_atmospheres[port_idx]["oxygen_ppm"] = cur_o2 * 0.01
			port_atmospheres[port_idx]["argon_pct"] = 99.99
			if purge_cycle_counts[port_idx] >= 3:
				port_atmospheres[port_idx]["purged"] = true
				if port_idx == 0 and tutorial_step >= 5:
					tutorial_step = 6

		return result

	func get_status() -> Dictionary:
		return {
			"argon_pressure_psi": argon_pressure_psi,
			"oil_bubbler_rate_bps": oil_bubbler_rate_bps,
			"cold_trap_temp_c": cold_trap_temp_c,
			"cold_trap_ready": cold_trap_filled_ln2,
			"port_0_o2_ppm": roundf(port_atmospheres[0]["oxygen_ppm"] * 10.0) / 10.0,
			"port_0_purged": port_atmospheres[0]["purged"],
			"port_0_purge_cycles": purge_cycle_counts[0],
			"tutorial_step": tutorial_step,
			"current_instruction": TUTORIAL_STEPS[clampi(tutorial_step, 0, TUTORIAL_STEPS.size() - 1)]
		}

# =============================================================================
# 3. ANALYTICAL BALANCE & MICROPIPETTES CONTROLLER
# =============================================================================
class AnalyticalBalanceController extends RefCounted:
	var draft_shield_closed: bool = true
	var pan_mass_g: float = 0.0
	var tare_offset_g: float = 0.0
	var displayed_mass_g: float = 0.0
	var is_stable: bool = true
	var electrostatic_grounded: bool = true
	var calibration_passed: bool = true

	var tutorial_step: int = 0
	const TUTORIAL_STEPS: Array[String] = [
		"1. Close all glass draft shield doors to prevent air current drift",
		"2. Press TARE to zero balance reading (0.0000 g)",
		"3. Open sliding door, place weighing boat on stainless steel pan",
		"4. Press TARE again with weighing boat in place",
		"5. Transfer sample using spatula in small increments until target mass is reached",
		"6. Close draft shield door and record mass once stability indicator (○) illuminates"
	]

	func tare() -> void:
		tare_offset_g = pan_mass_g
		displayed_mass_g = 0.0000
		if tutorial_step in [1, 3]:
			tutorial_step += 1

	func place_mass(mass_g: float) -> void:
		pan_mass_g += mass_g
		_update_reading()

	func set_draft_shield(closed: bool) -> void:
		draft_shield_closed = closed
		_update_reading()
		if closed and tutorial_step == 0:
			tutorial_step = 1

	func _update_reading() -> void:
		var net = pan_mass_g - tare_offset_g
		var noise = 0.0
		if not draft_shield_closed:
			noise += (randf() - 0.5) * 0.008  # Air drift
			is_stable = false
		else:
			is_stable = true

		if not electrostatic_grounded:
			noise += (randf() - 0.5) * 0.003

		displayed_mass_g = maxf(0.0, net + noise)

	func get_reading() -> Dictionary:
		return {
			"displayed_mass_g": roundf(displayed_mass_g * 10000.0) / 10000.0,
			"is_stable": is_stable,
			"draft_shield_closed": draft_shield_closed,
			"precision_decimal_places": 4,
			"tutorial_step": tutorial_step,
			"current_instruction": TUTORIAL_STEPS[clampi(tutorial_step, 0, TUTORIAL_STEPS.size() - 1)]
		}

class MicropipetteController extends RefCounted:
	enum Model { P10, P20, P200, P1000 }
	enum Technique { FORWARD, REVERSE }

	var model: Model = Model.P1000
	var selected_volume_ul: float = 1000.0
	var min_volume_ul: float = 100.0
	var max_volume_ul: float = 1000.0
	var tip_attached: bool = false
	var aspirated_volume_ul: float = 0.0
	var plunger_stop: int = 0  # 0: rest, 1: first stop (measure), 2: second stop (blowout)

	func set_volume(volume_ul: float) -> bool:
		if volume_ul < min_volume_ul or volume_ul > max_volume_ul:
			return false
		selected_volume_ul = volume_ul
		return true

	func attach_tip(attached: bool) -> void:
		tip_attached = attached

	func aspirate(technique: Technique = Technique.FORWARD) -> Dictionary:
		if not tip_attached:
			return { "success": false, "error": "Cannot aspirate without pipette tip! Risk of barrel contamination." }
		aspirated_volume_ul = selected_volume_ul
		plunger_stop = 0
		return { "success": true, "volume_ul": aspirated_volume_ul, "technique": "forward" if technique == Technique.FORWARD else "reverse" }

	func dispense() -> Dictionary:
		if aspirated_volume_ul <= 0.0:
			return { "success": false, "dispensed_ul": 0.0 }
		var delivered = aspirated_volume_ul
		aspirated_volume_ul = 0.0
		plunger_stop = 2  # Complete blowout
		return { "success": true, "dispensed_ul": delivered }

# =============================================================================
# 4. HPLC & GC-MS CONTROLLER
# =============================================================================
class HPLCController extends RefCounted:
	var flow_rate_ml_min: float = 1.0
	var backpressure_bar: float = 145.0
	var max_pressure_bar: float = 400.0
	var column_type: String = "C18 Reverse-Phase (4.6 x 150 mm, 5 µm)"
	var mobile_phase_a: String = "Water + 0.1% Formic Acid"
	var mobile_phase_b: String = "Acetonitrile"
	var mobile_phase_b_pct: float = 30.0
	var column_temp_c: float = 35.0
	var uv_wavelength_nm: float = 254.0
	var is_pumping: bool = false
	var injection_volume_ul: float = 20.0
	var chromatogram: Array[Dictionary] = []

	func start_pumps(running: bool) -> void:
		is_pumping = running

	func inject_sample(sample_name: String, compounds: Array) -> Dictionary:
		if not is_pumping:
			return { "success": false, "error": "HPLC pumps must be running to inject sample" }

		# Generate chromatogram peaks based on hydrophobicity (logP)
		chromatogram.clear()
		var t_dead = 1.5  # Dead time (void volume)
		for comp in compounds:
			var log_p: float = float(comp.get("logP", 1.5))
			var conc: float = float(comp.get("concentration_mg_ml", 1.0))
			# Retention time model: higher logP retains longer on C18
			var k_prime = exp(log_p * 0.8) * (100.0 / maxf(1.0, mobile_phase_b_pct))
			var t_r = t_dead * (1.0 + k_prime)
			var peak_width = 0.15 + (t_r * 0.03)
			var height = conc * 850.0
			var area = height * peak_width * 1.064
			chromatogram.append({
				"compound": comp.get("name", "Unknown"),
				"retention_time_min": roundf(t_r * 100.0) / 100.0,
				"peak_width_min": roundf(peak_width * 1000.0) / 1000.0,
				"peak_height_mau": roundf(height * 10.0) / 10.0,
				"peak_area": roundf(area * 10.0) / 10.0,
				"theoretical_plates": roundf(16.0 * pow(t_r / peak_width, 2.0))
			})

		return {
			"success": true,
			"sample": sample_name,
			"runtime_min": 15.0,
			"peaks": chromatogram
		}

class GCMSController extends RefCounted:
	var carrier_gas: String = "Helium"
	var carrier_flow_ml_min: float = 1.2
	var inlet_temp_c: float = 250.0
	var oven_temp_initial_c: float = 60.0
	var oven_temp_final_c: float = 280.0
	var ramp_rate_c_min: float = 15.0
	var split_ratio: int = 20
	var ionization_mode: String = "Electron Ionization (70 eV EI)"
	var mass_range_mz: Vector2 = Vector2(40.0, 550.0)

	func run_ms_scan(compound_name: String, molecular_weight: float, fragmentation: Array[Dictionary]) -> Dictionary:
		return {
			"compound": compound_name,
			"molecular_ion_mz": molecular_weight,
			"ionization_energy_ev": 70.0,
			"base_peak_mz": fragmentation[0].get("mz", 43.0) if not fragmentation.is_empty() else 43.0,
			"mass_spectrum": fragmentation
		}

# =============================================================================
# 5. SOXHLET EXTRACTOR CONTROLLER
# =============================================================================
class SoxhletController extends RefCounted:
	var heating_mantle_power_pct: float = 65.0
	var boiling_flask_solvent_ml: float = 250.0
	var solvent_name: String = "Ethanol (96%)"
	var biomass_matrix: String = "Camellia sinensis (Black Tea Leaves)"
	var thimble_sample_mass_g: float = 25.0
	var target_analyte: String = "Caffeine"
	var analyte_total_mass_mg: float = 750.0  # 3% caffeine in tea
	var extracted_analyte_mass_mg: float = 0.0
	var siphon_cycles_completed: int = 0
	var siphon_chamber_fill_ml: float = 0.0
	var siphon_threshold_ml: float = 25.0
	var condenser_water_flowing: bool = true

	func update(delta: float) -> Dictionary:
		if heating_mantle_power_pct > 30.0 and condenser_water_flowing:
			# Evaporation & Condensation into extraction chamber
			var rate_ml_sec = 0.45 * (heating_mantle_power_pct / 100.0)
			siphon_chamber_fill_ml += rate_ml_sec * delta

			# Check siphon threshold trigger
			if siphon_chamber_fill_ml >= siphon_threshold_ml:
				# Automatic siphon dump back into boiling flask
				siphon_chamber_fill_ml = 0.0
				siphon_cycles_completed += 1
				# Extraction kinetics (diminishing returns per cycle)
				var remaining_mg = analyte_total_mass_mg - extracted_analyte_mass_mg
				var extraction_efficiency = 0.28  # 28% of remaining per cycle
				var extracted_this_cycle = remaining_mg * extraction_efficiency
				extracted_analyte_mass_mg += extracted_this_cycle

		return get_status()

	func get_status() -> Dictionary:
		var recovery_pct = (extracted_analyte_mass_mg / maxf(1.0, analyte_total_mass_mg)) * 100.0
		return {
			"siphon_cycles": siphon_cycles_completed,
			"siphon_chamber_fill_pct": roundf((siphon_chamber_fill_ml / siphon_threshold_ml) * 100.0),
			"extracted_analyte_mg": roundf(extracted_analyte_mass_mg * 10.0) / 10.0,
			"recovery_percentage": roundf(recovery_pct * 10.0) / 10.0,
			"condenser_safe": condenser_water_flowing
		}

# =============================================================================
# 6. UV-VIS SPECTROPHOTOMETER CONTROLLER
# =============================================================================
class UVVisController extends RefCounted:
	var lamp_deuterium_on: bool = true   # 190 - 380 nm
	var lamp_tungsten_on: bool = true    # 350 - 1100 nm
	var cuvette_pathlength_cm: float = 1.0
	var cuvette_material: String = "Quartz (190 - 2500 nm)"
	var is_blanked: bool = false
	var blank_solvent: String = "Methanol"

	func blank_zero() -> void:
		is_blanked = true

	func scan_absorbance(compound_name: String, molar_extinction_coeff: float, conc_mol_l: float, lambda_max_nm: float) -> Dictionary:
		if not is_blanked:
			return { "success": false, "error": "Must perform solvent blank calibration (zero) before measurement!" }

		# Beer-Lambert Law: A = epsilon * c * l
		var a_max = molar_extinction_coeff * conc_mol_l * cuvette_pathlength_cm
		var spectrum: Array[Dictionary] = []

		for wl in range(200, 801, 10):
			var dist = float(wl) - lambda_max_nm
			var gaussian_shape = exp(-pow(dist, 2.0) / (2.0 * pow(30.0, 2.0)))
			var a_wl = a_max * gaussian_shape
			# Transmittance: T = 10^(-A)
			var t_pct = pow(10.0, -a_wl) * 100.0
			spectrum.append({
				"wavelength_nm": wl,
				"absorbance": roundf(a_wl * 1000.0) / 1000.0,
				"transmittance_pct": roundf(t_pct * 10.0) / 10.0
			})

		return {
			"success": true,
			"compound": compound_name,
			"lambda_max_nm": lambda_max_nm,
			"absorbance_at_lambda_max": roundf(a_max * 1000.0) / 1000.0,
			"cuvette_pathlength_cm": cuvette_pathlength_cm,
			"spectrum": spectrum
		}

# =============================================================================
# 7. GLOVEBOX (INERT ATMOSPHERE WORKSTATION) CONTROLLER
# =============================================================================
class GloveboxController extends RefCounted:
	var o2_ppm: float = 0.05
	var h2o_ppm: float = 0.08
	var chamber_pressure_mbar: float = 3.5  # Positive overpressure
	var copper_catalyst_active: bool = true
	var molecular_sieve_active: bool = true
	var antechamber_purged: bool = false
	var antechamber_purge_cycles: int = 0
	var gloves_integrity_pass: bool = true

	func cycle_antechamber() -> Dictionary:
		antechamber_purge_cycles += 1
		if antechamber_purge_cycles >= 3:
			antechamber_purged = true
			return { "success": true, "cycles": antechamber_purge_cycles, "status": "Antechamber fully purged (< 0.5 ppm O2). Inner door safe to open." }
		return { "success": true, "cycles": antechamber_purge_cycles, "status": "Purge cycle %d of 3 complete." % antechamber_purge_cycles }

	func transfer_item(item_name: String) -> Dictionary:
		if not antechamber_purged:
			# Contamination spike
			o2_ppm += 45.0
			h2o_ppm += 30.0
			return {
				"success": false,
				"warning": "CONTAMINATION DETECTED! Inner door opened without 3x antechamber purge cycle. O2 rose to %.1f ppm." % o2_ppm
			}
		return { "success": true, "item": item_name, "atmosphere_clean": true }

# =============================================================================
# 8. CENTRIFUGE & BUCHNER FILTRATION CONTROLLER
# =============================================================================
class CentrifugeController extends RefCounted:
	var rpm: float = 0.0
	var target_rpm: float = 10000.0
	var rotor_radius_cm: float = 8.5
	var tubes_balanced: bool = true
	var lid_locked: bool = true
	var running: bool = false
	var pellet_formed: bool = false

	func set_tubes_balanced(balanced: bool) -> void:
		tubes_balanced = balanced

	func start(run: bool) -> Dictionary:
		if run and not tubes_balanced:
			return {
				"success": false,
				"error": "CRITICAL ROTOR IMBALANCE! Opposite tube masses must be within ±0.01 g. Emergency cutoff engaged."
			}
		running = run
		if running:
			rpm = target_rpm
			# Relative Centrifugal Force: RCF = 1.118e-5 * r * RPM^2
			var rcf_g = 1.118e-5 * rotor_radius_cm * pow(rpm, 2.0)
			pellet_formed = true
			return { "success": true, "rpm": rpm, "rcf_g_force": roundf(rcf_g) }
		else:
			rpm = 0.0
			return { "success": true, "rpm": 0.0 }

class BuchnerFiltrationController extends RefCounted:
	var vacuum_active: bool = false
	var filter_paper_seated: bool = false
	var filter_paper_wetted: bool = false
	var slurry_volume_ml: float = 100.0
	var cake_mass_dry_g: float = 0.0
	var filtrate_volume_ml: float = 0.0

	func prepare_funnel(paper: bool, wetted_with_solvent: bool) -> void:
		filter_paper_seated = paper
		filter_paper_wetted = wetted_with_solvent

	func filter_slurry(slurry_ml: float, solid_content_g: float) -> Dictionary:
		if not vacuum_active:
			return { "success": false, "error": "Engage water aspirator or vacuum pump before pouring slurry." }
		if not filter_paper_wetted:
			return { "success": false, "warning": "Unwetted filter paper allowed solid crystals to bypass into filtrate!" }

		filtrate_volume_ml = slurry_ml * 0.92
		cake_mass_dry_g = solid_content_g
		return {
			"success": true,
			"cake_mass_dry_g": cake_mass_dry_g,
			"filtrate_volume_ml": filtrate_volume_ml,
			"filtration_efficiency_pct": 99.2
		}
