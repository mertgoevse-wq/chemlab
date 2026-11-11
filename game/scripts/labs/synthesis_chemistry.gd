# Athanor Ascension — Aspirin Synthesis Model
# Offline, deterministic evaluation of the GDD protocol: salicylic acid +
# acetic anhydride (H2SO4 catalyst) -> acetylsalicylic acid + acetic acid.
#
# Every number below is anchored to the protocol in design/gdd/synthesis-protocols.md:
#   M(salicylic acid) = 138.12 g/mol, M(acetic anhydride) = 102.09 g/mol,
#   density(acetic anhydride) = 1.082 g/mL, M(aspirin) = 180.16 g/mol,
#   pure aspirin melts at 135-136 C.
#
# The model is intentionally transparent: conversion, workup recovery, impurity
# mass fraction and melting-point depression are separate, inspectable terms.
# There is no random roll — a bad batch is the consequence of a bad choice.
extends RefCounted

const Catalog = preload("res://scripts/labs/synthesis_catalog.gd")

const MW_SALICYLIC: float = 138.12
const MW_ANHYDRIDE: float = 102.09
const DENSITY_ANHYDRIDE: float = 1.082
const MW_ASPIRIN: float = 180.16
const MW_ACETIC_ACID: float = 60.05
const MP_PURE: float = 135.5

const CATALYST_OPTIMAL_DROPS: int = 5
const REFLUX_OPTIMAL_MIN: float = 20.0
const TEMP_OPTIMAL_LOW: float = 65.0
const TEMP_OPTIMAL_HIGH: float = 75.0
const TEMP_DEGRADE: float = 85.0
const TEMP_POLYMERIZE: float = 100.0

const PURITY_PASS: float = 95.0
const YIELD_PASS_G: float = 12.0
const MP_TOLERANCE_C: float = 2.5


static func theoretical_yield_g(salicylic_mass_g: float, anhydride_ml: float) -> float:
	var moles_sal: float = maxf(0.0, salicylic_mass_g) / MW_SALICYLIC
	var moles_anh: float = maxf(0.0, anhydride_ml) * DENSITY_ANHYDRIDE / MW_ANHYDRIDE
	return minf(moles_sal, moles_anh) * MW_ASPIRIN


static func evaluate(params: Dictionary) -> Dictionary:
	var proto: Dictionary = {}
	if params.has("protocol") and params["protocol"] is Dictionary:
		proto = params["protocol"]
	elif params.has("protocol_id"):
		proto = Catalog.get_protocol(str(params["protocol_id"]))

	var is_custom: bool = not proto.is_empty() and str(proto.get("id", "aspirin")) != "aspirin"
	var rA: Dictionary = proto.get("reagent_a", {})
	var rB: Dictionary = proto.get("reagent_b", {})
	var reflux_info: Dictionary = proto.get("reflux", {})
	var anal_info: Dictionary = proto.get("analytical", {})

	var mw_a: float = float(rA.get("mw", MW_SALICYLIC)) if is_custom else MW_SALICYLIC
	var mw_b: float = float(rB.get("mw", MW_ANHYDRIDE)) if is_custom else MW_ANHYDRIDE
	var density_b: float = float(rB.get("density", DENSITY_ANHYDRIDE)) if is_custom else DENSITY_ANHYDRIDE
	var mw_product: float = float(proto.get("mw", MW_ASPIRIN)) if is_custom else MW_ASPIRIN
	var mp_pure: float = float(anal_info.get("mp_pure", MP_PURE)) if is_custom else MP_PURE
	var mp_tol: float = float(anal_info.get("mp_tolerance", MP_TOLERANCE_C)) if is_custom else MP_TOLERANCE_C
	var tlc_rf_pure: float = float(anal_info.get("tlc_rf", 0.45)) if is_custom else 0.45
	var purity_pass: float = float(anal_info.get("purity_pass", PURITY_PASS)) if is_custom else PURITY_PASS
	var yield_pass_g: float = float(anal_info.get("yield_pass_g", YIELD_PASS_G)) if is_custom else YIELD_PASS_G

	var temp_opt_low: float = float(reflux_info.get("temp_optimal_low", TEMP_OPTIMAL_LOW)) if is_custom else TEMP_OPTIMAL_LOW
	var temp_opt_high: float = float(reflux_info.get("temp_optimal_high", TEMP_OPTIMAL_HIGH)) if is_custom else TEMP_OPTIMAL_HIGH
	var temp_degrade: float = float(reflux_info.get("temp_degrade", TEMP_DEGRADE)) if is_custom else TEMP_DEGRADE
	var temp_poly: float = float(reflux_info.get("temp_polymerize", TEMP_POLYMERIZE)) if is_custom else TEMP_POLYMERIZE
	var opt_reflux_min: float = float(reflux_info.get("optimal_min", REFLUX_OPTIMAL_MIN)) if is_custom else REFLUX_OPTIMAL_MIN

	var rA_name: String = str(rA.get("name", "Salicylic acid")) if is_custom else "Salicylic acid"
	var rB_name: String = str(rB.get("name", "Acetic anhydride")) if is_custom else "Acetic anhydride"

	var mass_g: float = clampf(float(params.get("reagent_a_mass", params.get("salicylic_mass_g", 13.8))), 0.0, 500.0)
	var anhydride_ml: float = clampf(float(params.get("reagent_b_amount", params.get("anhydride_ml", 14.2))), 0.0, 500.0)
	var drops: int = clampi(int(params.get("catalyst_drops", 5)), 0, 10)
	var temp_c: float = clampf(float(params.get("reflux_temp_c", 70.0)), 0.0, 140.0)
	var max_reflux: float = maxf(120.0, opt_reflux_min * 2.0)
	var reflux_min: float = clampf(float(params.get("reflux_min", 20.0)), 0.0, max_reflux)
	var stir_rpm: float = clampf(float(params.get("stir_rpm", 450.0)), 0.0, 1500.0)
	var hood_on: bool = bool(params.get("fume_hood", false))
	var ice_c: float = clampf(float(params.get("ice_bath_c", 2.0)), -15.0, 30.0)
	var quench_water_ml: float = clampf(float(params.get("quench_water_ml", 30.0)), 0.0, 120.0)
	var recryst_ethanol_ml: float = clampf(float(params.get("recryst_ethanol_ml", 15.0)), 0.0, 80.0)
	var seeded: bool = bool(params.get("seed_crystal", true))
	var ppe_ok: bool = bool(params.get("ppe", false))

	var flags: Array[String] = []
	var warnings: Array[String] = []

	var moles_sal: float = mass_g / mw_a
	var moles_anh: float = anhydride_ml * density_b / mw_b
	var equivalents: float = moles_anh / moles_sal if moles_sal > 0.0 else 0.0
	var limiting_moles: float = minf(moles_sal, moles_anh)
	var theoretical_g: float = limiting_moles * mw_product

	if mass_g <= 0.0 or anhydride_ml <= 0.0:
		return _rejected("Both reagents are required before the reaction can start.")

	if moles_sal <= moles_anh:
		flags.append("SALICYLIC_LIMITING" if not is_custom else "PRECURSOR_LIMITING")
	else:
		flags.append("ANHYDRIDE_LIMITING" if not is_custom else "REAGENT_LIMITING")
		warnings.append("%s is the limiting reagent. Theoretical yield is capped by 1:1 stoichiometry, not by excess starting material." % rB_name)

	# --- Conversion: temperature window, time, catalyst, mass transfer ----------
	var temp_factor: float
	if temp_c < temp_opt_low - 25.0:
		temp_factor = 0.12
	elif temp_c < temp_opt_low:
		temp_factor = lerpf(0.12, 0.97, (temp_c - (temp_opt_low - 25.0)) / 25.0)
	elif temp_c <= temp_opt_high:
		var mid: float = (temp_opt_low + temp_opt_high) * 0.5
		temp_factor = 1.0 - absf(temp_c - mid) * 0.003
	elif temp_c <= temp_degrade:
		temp_factor = lerpf(1.0, 0.88, (temp_c - temp_opt_high) / maxf(1.0, (temp_degrade - temp_opt_high)))
	elif temp_c <= temp_poly:
		temp_factor = lerpf(0.88, 0.66, (temp_c - temp_degrade) / maxf(1.0, (temp_poly - temp_degrade)))
	else:
		temp_factor = maxf(0.30, 0.66 - (temp_c - temp_poly) * 0.02)
		flags.append("THERMAL_RUNAWAY")
		warnings.append("Above %0.0f °C product degrades and batch polymerises/pyrolyses." % temp_poly)

	var time_factor: float = clampf(reflux_min / opt_reflux_min, 0.0, 1.0)
	if reflux_min < (opt_reflux_min * 0.4):
		flags.append("INCOMPLETE_REFLUX")
		warnings.append("Reflux was stopped before acylation had time to finish; starting material remains unreacted.")

	var catalyst_factor: float
	if drops == 0:
		catalyst_factor = 0.28
		flags.append("MISSING_CATALYST")
		warnings.append("No catalyst charged. Reaction proceeds very slowly; conversion remains low.")
	elif drops <= 2:
		catalyst_factor = 0.78
		flags.append("WEAK_CATALYST")
		warnings.append("Insufficient catalyst: conversion is sluggish and crude product is contaminated.")
	elif drops <= 6:
		catalyst_factor = 1.0
	else:
		catalyst_factor = 0.97
		warnings.append("Excess catalyst chars some product and makes workup unnecessarily corrosive.")

	var stir_factor: float
	if stir_rpm < 200.0:
		stir_factor = 0.78
		flags.append("POOR_MIXING")
		warnings.append("Below 200 rpm the organic phases separate and mass transfer limits the reaction.")
	elif stir_rpm > 1000.0:
		stir_factor = 0.92
		flags.append("VORTEX_CAVITATION")
		warnings.append("Above 1000 rpm the vortex pulls vapour into the stirrer bearing and splashes the flask walls.")
	else:
		stir_factor = 1.0

	var conversion: float = clampf(temp_factor * time_factor * catalyst_factor * stir_factor, 0.0, 0.995)
	if equivalents < 1.0:
		conversion *= clampf(equivalents, 0.0, 1.0)
	if conversion < 0.80:
		flags.append("LOW_CONVERSION")

	# --- Workup recovery -------------------------------------------------------
	var recovery: float = 0.88
	if seeded:
		recovery += 0.02
	else:
		recovery -= 0.035
		warnings.append("No seed crystal: crystallisation is delayed and fine crystals are lost through the filter.")
	if ice_c > 10.0:
		recovery -= (ice_c - 10.0) * 0.006
		flags.append("WARM_CRYSTALLISATION")
		warnings.append("The ice bath was too warm; product stays dissolved and recovery drops.")
	if quench_water_ml < 8.0:
		recovery -= 0.03
	if quench_water_ml > 45.0:
		recovery -= (quench_water_ml - 45.0) * 0.002
	if recryst_ethanol_ml > 0.0:
		recovery -= 0.03

	var yield_g: float = theoretical_g * conversion * clampf(recovery, 0.20, 0.98)

	# --- Purity: unreacted starting material, tar, excess reagent, workup residue ----------
	var purity: float = 99.4
	purity -= (1.0 - conversion) * 45.0

	var tar: float = 0.0
	if temp_c > temp_degrade:
		tar += (temp_c - temp_degrade) * 1.15
		flags.append("TARRING")
		warnings.append("Above %0.0f °C product discolours and tar forms." % temp_degrade)
	if temp_c > temp_poly:
		tar += (temp_c - temp_poly) * 2.0
		flags.append("POLYMERISATION")
	purity -= tar

	if quench_water_ml < 10.0:
		var unhydrolysed: float = (10.0 - quench_water_ml) * 0.9
		purity -= unhydrolysed
		flags.append("POOR_QUENCH")
		warnings.append("Not enough water to destroy excess reagent.")

	if equivalents > 2.4:
		purity -= (equivalents - 2.4) * 7.0
		flags.append("EXCESS_ANHYDRIDE")
		warnings.append("A large excess of reagent leaves by-products and makes the quench violent.")

	if recryst_ethanol_ml >= 10.0:
		purity += 3.0
	elif recryst_ethanol_ml > 0.0:
		purity -= 2.0
		warnings.append("Too little solvent for recrystallisation; impurities stay in crystal lattice.")
	else:
		purity -= 3.0
		flags.append("NO_RECRYSTALLISATION")
		warnings.append("The crude product was not recrystallised, so melting-point range stays broad.")

	purity = clampf(purity, 8.0, 99.8)

	var mp_c: float = mp_pure - (100.0 - purity) * 0.65
	if tar > 0.0:
		mp_c -= 4.0
	var mp_range: float = 0.8 + (100.0 - purity) * 0.15
	var tlc_rf: float = tlc_rf_pure + (100.0 - purity) * 0.001

	# --- Safety gate -----------------------------------------------------------
	if not hood_on:
		flags.append("NO_FUME_HOOD")
		warnings.append("Reaction was run on open bench without fume hood ventilation.")
	if not ppe_ok:
		flags.append("MISSING_PPE")
		warnings.append("Goggles, nitrile gloves and a lab coat are mandatory for this protocol.")
	var safety_pass: bool = hood_on and ppe_ok and temp_c <= temp_poly

	# --- Quest checks & score --------------------------------------------------
	var checks := {
		"tlc": purity >= 80.0,
		"melting_point": absf(mp_c - mp_pure) <= mp_tol,
		"purity": purity >= purity_pass,
		"yield": yield_g >= yield_pass_g
	}
	var purity_ok: bool = bool(checks["purity"])
	var yield_ok: bool = bool(checks["yield"])

	var score: float = purity * 0.62
	score += minf(yield_g / maxf(1.0, theoretical_g * 0.8), 1.0) * 23.0
	score += 12.0 if safety_pass else 2.0
	score = clampf(score, 0.0, 100.0)

	var stars: int = 0
	if purity_ok and yield_ok and safety_pass:
		if purity >= 97.0 and yield_g >= (theoretical_g * 0.75):
			stars = 3
		else:
			stars = 2
	elif purity >= 80.0 and yield_g >= 6.0:
		stars = 1

	var grade: String = "Rejected — off specification"
	if stars == 3:
		grade = "Reference grade"
	elif stars == 2:
		grade = "Pharmaceutical grade"
	elif stars == 1:
		grade = "Crude product — needs rework"

	var xp_chemistry: int = int(round(220.0 * score / 100.0))
	var xp_engineering: int = 0
	if hood_on:
		xp_engineering += 30
	if temp_c >= TEMP_OPTIMAL_LOW and temp_c <= TEMP_OPTIMAL_HIGH:
		xp_engineering += 25
	if stir_rpm >= 300.0 and stir_rpm <= 900.0:
		xp_engineering += 15

	if not purity_ok:
		flags.append("LOW_PURITY")
		warnings.append("Purity %.1f %% is below the %.1f %% pharmaceutical gate." % [purity, PURITY_PASS])
		flags.append("LOW_YIELD")
		warnings.append("Isolated mass %.1f g is below the %.1f g contract minimum." % [yield_g, YIELD_PASS_G])

	return {
		"ok": true,
		"moles_salicylic": moles_sal,
		"moles_anhydride": moles_anh,
		"equivalents": equivalents,
		"theoretical_g": theoretical_g,
		"conversion": conversion,
		"recovery": recovery,
		"yield_g": yield_g,
		"purity": purity,
		"melting_point_c": mp_c,
		"melting_range_c": mp_range,
		"tlc_rf": tlc_rf,
		"tar_index": tar,
		"score": score,
		"stars": stars,
		"grade": grade,
		"xp_chemistry": xp_chemistry,
		"xp_engineering": xp_engineering,
		"checks": checks,
		"safety_pass": safety_pass,
		"flags": flags,
		"warnings": warnings,
		"limiting_reagent": "salicylic acid" if moles_sal <= moles_anh else "acetic anhydride"
	}


static func _rejected(reason: String) -> Dictionary:
	return {
		"ok": false,
		"error": reason,
		"flags": ["INVALID_BATCH"],
		"warnings": [reason],
		"yield_g": 0.0,
		"purity": 0.0,
		"melting_point_c": 0.0,
		"score": 0.0,
		"stars": 0,
		"safety_pass": false,
		"xp_chemistry": 0,
		"xp_engineering": 0,
		"checks": {"tlc": false, "melting_point": false, "purity": false, "yield": false},
		"grade": "Rejected — invalid batch"
	}
