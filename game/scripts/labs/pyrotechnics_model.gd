# Athanor Ascension — Pyrotechnic Composition Model (offline)
# Mirrors src/chemlab/chemistry/pyrotechnics.py so the lab works without IPC.
# Teaching arithmetic only: oxygen balance, burn rate, flame colour, hazard.
extends RefCounted
class_name PyrotechnicsModel

const OXIDISERS: Dictionary = {
	"potassium_nitrate": {"oxygen": 0.475, "metal": 0.387},
	"potassium_chlorate": {"oxygen": 0.392, "metal": 0.319},
	"potassium_perchlorate": {"oxygen": 0.462, "metal": 0.282},
	"sodium_nitrate": {"oxygen": 0.565, "metal": 0.271},
	"strontium_nitrate": {"oxygen": 0.454, "metal": 0.414},
	"barium_nitrate": {"oxygen": 0.367, "metal": 0.525},
	"ammonium_nitrate": {"oxygen": 0.600, "metal": 0.0},
	"copper_ii_oxide": {"oxygen": 0.201, "metal": 0.799},
}

const FUELS: Dictionary = {
	"charcoal": {"oxygen_demand": 2.66, "heat": 31000.0},
	"sulfur": {"oxygen_demand": 1.00, "heat": 9200.0},
	"aluminium": {"oxygen_demand": 0.89, "heat": 31000.0},
	"magnesium": {"oxygen_demand": 0.66, "heat": 24700.0},
	"dextrin": {"oxygen_demand": 1.19, "heat": 16000.0},
	"hexamine": {"oxygen_demand": 1.60, "heat": 30000.0},
	"sodium_benzoate": {"oxygen_demand": 1.55, "heat": 26000.0},
	"titanium": {"oxygen_demand": 0.67, "heat": 19000.0},
}

const COLORANTS: Dictionary = {
	"strontium": {"nm": 606, "rgb": Color(1.0, 0.22, 0.18)},
	"barium": {"nm": 524, "rgb": Color(0.25, 1.0, 0.45)},
	"copper": {"nm": 590, "rgb": Color(0.30, 0.55, 1.0)},
	"sodium": {"nm": 589, "rgb": Color(1.0, 0.72, 0.20)},
	"none": {"nm": 0, "rgb": Color(1.0, 0.85, 0.55)},
}


static func oxygen_balance(components: Array) -> float:
	var supplied := 0.0
	var demanded := 0.0
	for component in components:
		var substance := str(component.get("substance", ""))
		var fraction := float(component.get("fraction", 0.0))
		if OXIDISERS.has(substance):
			supplied += fraction * float(OXIDISERS[substance]["oxygen"])
		elif FUELS.has(substance):
			demanded += fraction * float(FUELS[substance]["oxygen_demand"])
	return snappedf(supplied - demanded, 0.0001)


static func burn_rate(components: Array, confinement: float, moisture: float = 0.0) -> float:
	var balance: float = absf(oxygen_balance(components))
	var stoichiometry: float = maxf(0.05, 1.0 - balance)
	var base: float = 2.0 + 28.0 * stoichiometry
	for component in components:
		var substance := str(component.get("substance", ""))
		if substance == "potassium_chlorate":
			base *= 1.9
		elif substance == "potassium_perchlorate":
			base *= 1.5
		elif substance == "aluminium":
			base *= 0.75
	return snappedf(base * (1.0 + 2.5 * confinement) * maxf(0.2, 1.0 - 6.0 * moisture), 0.01)


static func sensitivity(components: Array) -> String:
	var names: Array[String] = []
	for component in components:
		names.append(str(component.get("substance", "")))
	if "potassium_chlorate" in names and "sulfur" in names:
		return "extreme"
	if "potassium_chlorate" in names or "potassium_perchlorate" in names:
		return "high"
	if "aluminium" in names or "magnesium" in names or "titanium" in names:
		return "moderate"
	return "moderate"


static func evaluate(formulation: Dictionary) -> Dictionary:
	var components: Array = formulation.get("components", [])
	var colorant := str(formulation.get("colorant", "none"))
	var color_data: Dictionary = COLORANTS.get(colorant, COLORANTS["none"])
	var confinement := float(formulation.get("confinement", 0.0))
	var balance := oxygen_balance(components)
	var rate := burn_rate(components, confinement)

	var heat := 0.0
	for component in components:
		var substance := str(component.get("substance", ""))
		var fraction := float(component.get("fraction", 0.0))
		heat += fraction * float(FUELS.get(substance, {"heat": 4000.0})["heat"])
	var efficiency: float = maxf(0.35, 1.0 - absf(balance) * 1.4)

	var warnings: Array[String] = []
	var names: Array[String] = []
	for component in components:
		names.append(str(component.get("substance", "")))
	if "potassium_chlorate" in names and "sulfur" in names:
		warnings.append("Chlorate + sulfur is friction sensitive: never combine.")
	if "barium_nitrate" in names:
		warnings.append("Barium salts are toxic; wear respiratory protection.")
	if absf(balance) > 0.25:
		warnings.append("Far from oxygen balance: expect soot or incomplete burn.")

	var level := sensitivity(components)
	var hazard := "1.4G (minor explosion hazard)"
	if level == "extreme":
		hazard = "1.1A (mass explosion hazard)"
	elif level == "high":
		hazard = "1.1D (detonation risk when confined)"
	elif confinement > 0.6:
		hazard = "1.3G (major fire hazard, confined)"

	return {
		"oxygen_balance": balance,
		"burn_rate_mm_s": rate,
		"flame_temp_c": snappedf(25.0 + heat * efficiency / 1.25, 1.0),
		"flame_color": color_data["rgb"],
		"emission_nm": int(color_data["nm"]),
		"sensitivity": level,
		"hazard_class": hazard,
		"warnings": warnings,
	}
