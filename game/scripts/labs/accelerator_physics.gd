# Athanor Ascension — Accelerator / Beam Physics
# Pure, offline calculations. No network, no LLM, no invented constants.
#
# References for the formulas used below:
#   * gamma = 1 + T/(mc^2); beta = sqrt(1 - 1/gamma^2)
#   * magnetic rigidity: B*rho [T*m] = p [GeV/c] / (0.299792458 * z)
#   * cyclotron frequency: f = z e B / (2 pi gamma m)
#   * synchrotron radiation loss per turn (electrons):
#       U0 [GeV] = 8.85e-5 * E[GeV]^4 / rho[m]
#   * reaction threshold (endothermic, lab frame): T_thr = -Q (1 + m_proj/m_target)
#   * Cherenkov: cos(theta) = 1/(beta n), threshold beta = 1/n
#   * saturation activity: A = N * sigma * phi * (1 - exp(-lambda t))

class_name AcceleratorPhysics
extends RefCounted

const C_LIGHT: float = 299792458.0
const E_CHARGE: float = 1.602176634e-19
const ATOMIC_MASS_U: float = 1.66053906660e-27
const U_MEV: float = 931.49410242
const CLASSICAL_ELECTRON_RADIUS_M: float = 2.8179403262e-15

# Rest masses in MeV/c^2 (CODATA / PDG).
const MASS_MEV: Dictionary = {
	"electron": 0.51099895,
	"proton": 938.27208816,
	"deuteron": 1875.61294257,
	"alpha": 3727.3794066,
	"lead208": 193729.0,     # 208 * 931.494
	"lithium7": 6533.8,
	"copper63": 58690.0,
	"tritium": 2808.92
}

const CHARGE: Dictionary = {
	"electron": -1, "proton": 1, "deuteron": 1, "alpha": 2,
	"lead208": 82, "lithium7": 3, "copper63": 29, "tritium": 1
}

# Q values in MeV for reactions we model.
const REACTIONS: Array = [
	{"id": "dd", "label": "D + D -> He-3 + n", "q_mev": 3.27, "projectile": "deuteron", "target": "deuteron",
		"products": "He-3 + n (2.45 MeV neutron)", "note": "Equal branching to T + p."},
	{"id": "dt", "label": "D + T -> He-4 + n", "q_mev": 17.59, "projectile": "deuteron", "target": "tritium",
		"products": "He-4 (3.5 MeV) + n (14.1 MeV)", "note": "Lowest threshold of the fusion reactions."},
	{"id": "p_li7", "label": "p + Li-7 -> Be-7 + n", "q_mev": -1.644, "projectile": "proton", "target": "lithium7",
		"products": "Be-7 + n", "note": "Endothermic; threshold about 1.88 MeV."},
	{"id": "p_cu63", "label": "p + Cu-63 -> Zn-63 + n", "q_mev": -2.14, "projectile": "proton", "target": "copper63",
		"products": "Zn-63 + n", "note": "Classic cyclotron activation reaction."},
	{"id": "p_p", "label": "p + p -> d + e+ + nu", "q_mev": 1.442, "projectile": "proton", "target": "proton",
		"products": "deuterium + positron + neutrino", "note": "Astrophysical pp chain; cross-section is minuscule."}
]

const TARGETS: Dictionary = {
	"proton": {"density_g_cm3": 0.0000899, "a": 1.0},
	"deuteron": {"density_g_cm3": 0.00018, "a": 2.0},
	"lithium7": {"density_g_cm3": 0.534, "a": 6.94},
	"copper63": {"density_g_cm3": 8.96, "a": 63.0},
	"tritium": {"density_g_cm3": 0.00028, "a": 3.0}
}

const MEDIA_REFRACTIVE_INDEX: Dictionary = {
	"vacuum": 1.0, "air": 1.000293, "water": 1.333, "silica_glass": 1.4585,
	"lead_glass": 1.7, "heavy_water": 1.328
}


static func kinetic_to_gamma(kinetic_mev: float, particle: String) -> float:
	var rest := float(MASS_MEV.get(particle, MASS_MEV["proton"]))
	return 1.0 + maxf(kinetic_mev, 0.0) / rest


static func gamma_to_kinetic(gamma: float, particle: String) -> float:
	var rest := float(MASS_MEV.get(particle, MASS_MEV["proton"]))
	return maxf(gamma - 1.0, 0.0) * rest


static func beta_from_gamma(gamma: float) -> float:
	if gamma <= 1.0:
		return 0.0
	return sqrt(maxf(1.0 - 1.0 / (gamma * gamma), 0.0))


static func beta_from_kinetic(kinetic_mev: float, particle: String) -> float:
	return beta_from_gamma(kinetic_to_gamma(kinetic_mev, particle))


static func momentum_mev_c(kinetic_mev: float, particle: String) -> float:
	var rest := float(MASS_MEV.get(particle, MASS_MEV["proton"]))
	return sqrt(maxf(kinetic_mev * kinetic_mev + 2.0 * kinetic_mev * rest, 0.0))


static func magnetic_rigidity_t_m(kinetic_mev: float, particle: String) -> float:
	var p_gev := momentum_mev_c(kinetic_mev, particle) / 1000.0
	var z := absf(float(CHARGE.get(particle, 1)))
	return p_gev / (0.299792458 * z)


static func required_field_t(kinetic_mev: float, particle: String, radius_m: float) -> float:
	if radius_m <= 0.0:
		return 0.0
	return magnetic_rigidity_t_m(kinetic_mev, particle) / radius_m


static func cyclotron_frequency_hz(kinetic_mev: float, particle: String, field_t: float) -> float:
	var gamma := kinetic_to_gamma(kinetic_mev, particle)
	var mass_kg := float(MASS_MEV.get(particle, MASS_MEV["proton"])) * 1.0e6 * E_CHARGE / (C_LIGHT * C_LIGHT)
	var z := absf(float(CHARGE.get(particle, 1)))
	return z * E_CHARGE * field_t / (2.0 * PI * gamma * mass_kg)


static func revolution_frequency_hz(kinetic_mev: float, particle: String, circumference_m: float) -> float:
	if circumference_m <= 0.0:
		return 0.0
	return beta_from_kinetic(kinetic_mev, particle) * C_LIGHT / circumference_m


static func synchrotron_loss_ev_per_turn(energy_gev: float, particle: String, radius_m: float) -> float:
	if particle != "electron" or radius_m <= 0.0:
		return 0.0
	return 8.85e-5 * pow(energy_gev, 4.0) / radius_m * 1.0e9


static func cherenkov_angle_deg(kinetic_mev: float, particle: String, medium: String) -> float:
	var n := float(MEDIA_REFRACTIVE_INDEX.get(medium, 1.0))
	var beta := beta_from_kinetic(kinetic_mev, particle)
	if beta * n <= 1.0 or n <= 1.0:
		return 0.0
	return rad_to_deg(acos(clampf(1.0 / (beta * n), -1.0, 1.0)))


static func cherenkov_threshold_mev(particle: String, medium: String) -> float:
	var n := float(MEDIA_REFRACTIVE_INDEX.get(medium, 1.0))
	if n <= 1.0:
		return 0.0
	var beta := 1.0 / n
	var gamma := 1.0 / sqrt(maxf(1.0 - beta * beta, 1e-12))
	return gamma_to_kinetic(gamma, particle)


static func reaction_threshold_mev(reaction_id: String) -> float:
	for r in REACTIONS:
		if str(r.get("id", "")) == reaction_id:
			var q := float(r.get("q_mev", 0.0))
			if q >= 0.0:
				return 0.0
			var m_proj := float(MASS_MEV.get(str(r.get("projectile", "proton")), MASS_MEV["proton"]))
			var m_target := float(MASS_MEV.get(str(r.get("target", "proton")), MASS_MEV["proton"]))
			return -q * (1.0 + m_proj / m_target)
	return 0.0


static func reaction(reaction_id: String) -> Dictionary:
	for r in REACTIONS:
		if str(r.get("id", "")) == reaction_id:
			return r
	return {}


static func beam_power_w(kinetic_mev: float, particle_current_ua: float) -> float:
	# 1 uA = 1e-6 C/s = 1e-6/e particles per second. Per particle T MeV.
	# The charge cancels: P[W] = I[uA] * T[MeV].
	return abs(particle_current_ua) * kinetic_mev


static func luminosity_cm2_s(beam_a: float, beam_b: float, revolution_hz: float,
		sigma_x_mm: float, sigma_y_mm: float) -> float:
	var sigma_x_cm := maxf(sigma_x_mm, 1e-6) * 0.1
	var sigma_y_cm := maxf(sigma_y_mm, 1e-6) * 0.1
	return (beam_a * beam_b * revolution_hz) / (4.0 * PI * sigma_x_cm * sigma_y_cm)


static func activation_bq(target_atoms: float, cross_section_barn: float, flux_per_cm2_s: float,
		half_life_s: float, irradiation_s: float) -> float:
	if target_atoms <= 0.0 or flux_per_cm2_s <= 0.0 or half_life_s <= 0.0:
		return 0.0
	var sigma_cm2 := cross_section_barn * 1.0e-24
	var lambda := log(2.0) / half_life_s
	return target_atoms * sigma_cm2 * flux_per_cm2_s * (1.0 - exp(-lambda * maxf(irradiation_s, 0.0)))


static func target_atom_count(target: String, mass_g: float) -> float:
	var info: Dictionary = TARGETS.get(target, {})
	var molar_mass := float(info.get("a", 1.0))
	if molar_mass <= 0.0:
		return 0.0
	return mass_g / molar_mass * 6.02214076e23


static func describe_beam(kinetic_mev: float, particle: String) -> Dictionary:
	var gamma := kinetic_to_gamma(kinetic_mev, particle)
	var beta := beta_from_gamma(gamma)
	return {
		"particle": particle,
		"kinetic_mev": kinetic_mev,
		"gamma": gamma,
		"beta": beta,
		"beta_percent_c": beta * 100.0,
		"momentum_mev_c": momentum_mev_c(kinetic_mev, particle),
		"rigidity_t_m": magnetic_rigidity_t_m(kinetic_mev, particle),
		"relativistic": beta > 0.1,
		"ultra_relativistic": beta > 0.99
	}


static func recommend_field(kinetic_mev: float, particle: String, radius_m: float) -> Dictionary:
	var b := required_field_t(kinetic_mev, particle, radius_m)
	var note := "Feasible with resistive magnets." if b < 2.0 else ("Needs superconducting magnets." if b < 10.0 else "Beyond niobium-titanium practical fields.")
	return {"field_t": b, "note": note}
