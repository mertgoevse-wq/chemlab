# Athanor Ascension — Fusor / Plasma Physics
# Offline engineering model for the tabletop inertial-electrostatic fusor.
#
# What is real here:
#   * Paschen breakdown voltage for air (Townsend coefficients A=15 /cm/Torr,
#     B=365 V/(cm Torr), gamma_se=0.01).
#   * Gas mean free path from kinetic theory.
#   * Cherenkov-free neutron dose conversion for 2.5 MeV neutrons
#     (H*(10)/Phi ~ 4.0e-10 Sv cm^2, ICRP 74 order of magnitude).
#   * Fusion energy per reaction, Q values.
#
# What is explicitly empirical:
#   * Neutron yield scaling Y ~ I^2 V^2.5 p. Real fusors are dominated by
#     recirculation and grid losses; this is an engineering fit for gameplay,
#     calibrated to ~1e5-1e6 n/s for a well-run 30 kV, 10 mA deuterium fusor.

class_name FusorPhysics
extends RefCounted

const BOLTZMANN: float = 1.380649e-23
const GAS_TEMPERATURE_K: float = 293.15
const DEUTERIUM_DIAMETER_M: float = 2.75e-10
const TORR_TO_PA: float = 133.322368
const Q_DD_MEV: float = 3.27
const NEUTRON_ENERGY_DD_MEV: float = 2.45
const DOSE_CONVERSION_SV_CM2: float = 4.0e-10

const PASCHEN_A: float = 15.0      # 1/(cm*Torr), air
const PASCHEN_B: float = 365.0     # V/(cm*Torr), air
const PASCHEN_GAMMA: float = 0.01
const PASCHEN_MIN_V: float = 327.0

const BUILD_STEPS: Array = [
	{
		"id": "chamber", "title": "Vacuum chamber",
		"detail": "Stainless conflat tee with a viewport. Clean, dry, and leak-tested before any high voltage.",
		"why": "Every virtual leak costs pumping speed; water vapour poisons the discharge and fakes neutron counts."
	},
	{
		"id": "cathode", "title": "Inner grid (cathode)",
		"detail": "A transparent spherical grid, 2-4 cm diameter, on the high-voltage feedthrough.",
		"why": "Ions accelerate toward the centre and pass through the open grid; transparency is why a fusor works at all."
	},
	{
		"id": "feedthrough", "title": "HV feedthrough",
		"detail": "Ceramic-insulated feedthrough rated well above the supply voltage, with a corona ring.",
		"why": "Surface tracking along dirty ceramic is the usual path to a destructive arc."
	},
	{
		"id": "pump", "title": "Two-stage vacuum pump",
		"detail": "Rotary vane backing pump to ~10 mTorr, optionally a turbo for base pressure.",
		"why": "Paschen breakdown needs a controlled pressure-distance product, not simply 'low pressure'."
	},
	{
		"id": "deuterium", "title": "Deuterium supply + needle valve",
		"detail": "Regulated D2 through a fine needle valve, with the chamber pressure read on a capacitance manometer.",
		"why": "Fusion yield scales with deuterium density; too much gas scatters ions before they reach the core."
	},
	{
		"id": "ballast", "title": "Ballast resistor",
		"detail": "10-100 kOhm series resistor in the HV lead.",
		"why": "Turns an arc from a destructive short into a recoverable voltage droop."
	},
	{
		"id": "supply", "title": "Current-limited HV supply",
		"detail": "0-40 kV at a few mA, negative on the cathode, with a hard current limit and interlock.",
		"why": "The energy stored in the supply decides whether a mistake is a fright or an injury."
	},
	{
		"id": "detector", "title": "Neutron detector + survey meter",
		"detail": "Bubble dosimeter or He-3 tube with a moderator; a gamma survey meter is not a neutron detector.",
		"why": "You cannot claim fusion without a detector that actually responds to neutrons."
	},
	{
		"id": "shielding", "title": "Shielding and distance",
		"detail": "Polyethylene/paraffin moderator, and operate from behind distance and a barrier.",
		"why": "2.45 MeV neutrons are moderated by hydrogen-rich material; inverse-square distance is free shielding."
	},
	{
		"id": "interlock", "title": "Interlocks and grounding",
		"detail": "HV off before the chamber is opened, grounding stick, no lone working.",
		"why": "The stored charge can persist after the supply is off. Ground first, then touch."
	}
]

const FAILURES: Array = [
	{"id": "no_vacuum", "label": "No discharge", "cause": "Pressure outside the Paschen window or no D2 admitted.", "severity": "none"},
	{"id": "glow_only", "label": "Glow discharge, no measurable neutrons", "cause": "Yield below detector background; increase current slowly or improve grid transparency.", "severity": "mild"},
	{"id": "arc", "label": "Arc / supply trip", "cause": "Pressure too high or grid contaminated; ballast resistor absorbed the event.", "severity": "moderate"},
	{"id": "overheat", "label": "Grid overheating", "cause": "Ion bombardment exceeds radiative cooling; reduce current.", "severity": "moderate"},
	{"id": "radiation", "label": "Dose rate above survey limit", "cause": "Distance or shielding insufficient for the measured yield.", "severity": "severe"}
]


static func mean_free_path_m(pressure_mtorr: float) -> float:
	if pressure_mtorr <= 0.0:
		return INF
	var pressure_pa := pressure_mtorr * 1.0e-3 * TORR_TO_PA
	return BOLTZMANN * GAS_TEMPERATURE_K / (sqrt(2.0) * PI * DEUTERIUM_DIAMETER_M * DEUTERIUM_DIAMETER_M * pressure_pa)


static func paschen_breakdown_v(pressure_mtorr: float, gap_cm: float) -> float:
	if pressure_mtorr <= 0.0 or gap_cm <= 0.0:
		return INF
	var pd := pressure_mtorr * gap_cm
	if pd <= 0.0:
		return INF
	var denominator := log(PASCHEN_A * pd) - log(log(1.0 + 1.0 / PASCHEN_GAMMA))
	if denominator <= 0.0:
		return INF
	return maxf(PASCHEN_MIN_V, (PASCHEN_B * pd) / denominator)


static func paschen_minimum() -> Dictionary:
	# dV/d(pd)=0 gives the Paschen minimum; solve numerically for the model.
	var best_pd := 0.0
	var best_v := INF
	var pd := 0.01
	while pd < 50.0:
		var v := _paschen_from_pd(pd)
		if v < best_v:
			best_v = v
			best_pd = pd
		pd += 0.01
	return {"pd_torr_cm": best_pd, "voltage_v": best_v}


static func _paschen_from_pd(pd: float) -> float:
	if pd <= 0.0:
		return INF
	var denominator := log(PASCHEN_A * pd) - log(log(1.0 + 1.0 / PASCHEN_GAMMA))
	if denominator <= 0.0:
		return INF
	return maxf(PASCHEN_MIN_V, (PASCHEN_B * pd) / denominator)


static func neutron_yield_per_s(voltage_kv: float, current_ma: float, pressure_mtorr: float) -> float:
	if voltage_kv <= 0.0 or current_ma <= 0.0 or pressure_mtorr <= 0.0:
		return 0.0
	# Empirical engineering scaling, deliberately bounded to keep runaway numbers
	# in the regime a small fusor can actually reach.
	return 1.0e4 * pow(voltage_kv / 20.0, 2.5) * pow(current_ma / 10.0, 2.0) * (pressure_mtorr / 5.0)


static func fusion_power_w(yield_per_s: float) -> float:
	return yield_per_s * Q_DD_MEV * 1.0e6 * 1.602176634e-19


static func input_power_w(voltage_kv: float, current_ma: float) -> float:
	return voltage_kv * 1000.0 * current_ma * 1.0e-3


static func energy_gain_q(voltage_kv: float, current_ma: float, pressure_mtorr: float) -> float:
	var input_p := input_power_w(voltage_kv, current_ma)
	if input_p <= 0.0:
		return 0.0
	return fusion_power_w(neutron_yield_per_s(voltage_kv, current_ma, pressure_mtorr)) / input_p


static func neutron_flux_at_distance(yield_per_s: float, distance_m: float) -> float:
	if distance_m <= 0.0:
		return 0.0
	var area_cm2 := 4.0 * PI * pow(distance_m * 100.0, 2.0)
	return yield_per_s / area_cm2


static func dose_rate_usv_h(yield_per_s: float, distance_m: float) -> float:
	# Sv/h = flux * conversion; convert to µSv/h.
	var flux := neutron_flux_at_distance(yield_per_s, distance_m)
	return flux * DOSE_CONVERSION_SV_CM2 * 1.0e6


static func annual_dose_fraction(dose_usv_h: float, hours: float) -> float:
	var dose_msv := dose_usv_h * hours / 1000.0
	return dose_msv / 20.0


static func pressure_window_ok(pressure_mtorr: float) -> bool:
	return pressure_mtorr >= 0.5 and pressure_mtorr <= 20.0


static func simulate_run(voltage_kv: float, current_ma: float, pressure_mtorr: float,
		distance_m: float, build_complete: bool) -> Dictionary:
	var breakdown := paschen_breakdown_v(pressure_mtorr, 4.0)
	var yield_per_s := neutron_yield_per_s(voltage_kv, current_ma, pressure_mtorr)
	if not build_complete:
		return {
			"ok": false, "failure": "incomplete_build",
			"message": "The vacuum and HV chain are not complete. Finish the build checklist before energising.",
			"neutron_yield_per_s": 0.0
		}
	if not pressure_window_ok(pressure_mtorr):
		return {
			"ok": false, "failure": "no_vacuum",
			"message": "Pressure %.1f mTorr sits outside the fusor window (0.5-20 mTorr)." % pressure_mtorr,
			"breakdown_v": breakdown,
			"neutron_yield_per_s": 0.0
		}
	if voltage_kv < 8.0:
		return {
			"ok": false, "failure": "glow_only",
			"message": "At %.1f kV the discharge strikes but ion energy is too low for useful D-D yield." % voltage_kv,
			"breakdown_v": breakdown,
			"neutron_yield_per_s": yield_per_s
		}
	if pressure_mtorr > 12.0:
		return {
			"ok": false, "failure": "arc",
			"message": "At %.1f mTorr the mean free path collapses and the supply trips." % pressure_mtorr,
			"breakdown_v": breakdown,
			"mean_free_path_m": mean_free_path_m(pressure_mtorr),
			"neutron_yield_per_s": 0.0
		}
	var dose := dose_rate_usv_h(yield_per_s, distance_m)
	var result := {
		"ok": true,
		"failure": "",
		"breakdown_v": breakdown,
		"mean_free_path_m": mean_free_path_m(pressure_mtorr),
		"neutron_yield_per_s": yield_per_s,
		"fusion_power_w": fusion_power_w(yield_per_s),
		"input_power_w": input_power_w(voltage_kv, current_ma),
		"q": energy_gain_q(voltage_kv, current_ma, pressure_mtorr),
		"flux_n_cm2_s_at_distance": neutron_flux_at_distance(yield_per_s, distance_m),
		"dose_usv_h": dose,
		"annual_fraction": annual_dose_fraction(dose, 1.0)
	}
	if dose > 20.0:
		result["ok"] = false
		result["failure"] = "radiation"
		result["message"] = "Dose rate %.1f µSv/h at the operator position exceeds the lab survey limit. Add distance or shielding." % dose
	else:
		result["message"] = "Stable discharge. %s n/s, Q = %s." % [_sci(yield_per_s), _sci(energy_gain_q(voltage_kv, current_ma, pressure_mtorr))]
	return result


static func _sci(value: float) -> String:
	if value <= 0.0:
		return "0"
	var exponent := int(floor(log(value) / log(10.0)))
	var mantissa := value / pow(10.0, exponent)
	return "%.2f e%d" % [mantissa, exponent]
