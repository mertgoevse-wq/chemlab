# Athanor Ascension — Titration equilibrium model
#
# Exact charge-balance solution for a monoprotic acid titrated with a strong base.
# No empirical pH table: [H+] is found by bisection on
#   [Na+] + [H+] = [OH-] + [A-]
# with [A-] = C_acid * Ka / (Ka + [H+]) and [OH-] = Kw / [H+].
# Strong acids are the Ka -> large limit of the same equation, so HCl and acetic
# acid share one code path instead of two approximations.
extends RefCounted

const KW: float = 1.0e-14
const STRONG_KA: float = 1.0e3
const PHENOLPHTHALEIN_PH: float = 8.2


static func ph_at(acid_molarity: float, acid_ml: float, base_molarity: float, base_ml: float, ka: float) -> float:
	var total_l := maxf((acid_ml + base_ml) / 1000.0, 1.0e-9)
	var acid_analytical := acid_molarity * acid_ml / 1000.0 / total_l
	var sodium := base_molarity * base_ml / 1000.0 / total_l
	var ka_safe := maxf(ka, 1.0e-14)

	# f(h) is monotonically increasing in h; bracket the root in log10 space.
	var lo := -14.0
	var hi := 0.0
	for _i in range(70):
		var mid := (lo + hi) * 0.5
		var h := pow(10.0, mid)
		var f := sodium + h - KW / h - acid_analytical * ka_safe / (ka_safe + h)
		if f > 0.0:
			hi = mid
		else:
			lo = mid
	return clampf(-(lo + hi) * 0.5, 0.0, 14.0)


static func equivalence_ml(acid_molarity: float, acid_ml: float, base_molarity: float) -> float:
	if base_molarity <= 0.0:
		return 0.0
	return acid_molarity * acid_ml / base_molarity


static func ph_at_equivalence(acid_molarity: float, acid_ml: float, base_molarity: float, ka: float) -> float:
	var eq := equivalence_ml(acid_molarity, acid_ml, base_molarity)
	return ph_at(acid_molarity, acid_ml, base_molarity, eq, ka)


## Volume of titrant at which the indicator first reaches its transition pH.
## Solved on the same equilibrium curve, so weak-acid buffering is included.
static func endpoint_ml(acid_molarity: float, acid_ml: float, base_molarity: float, ka: float, target_ph: float = PHENOLPHTHALEIN_PH) -> float:
	var eq := equivalence_ml(acid_molarity, acid_ml, base_molarity)
	if eq <= 0.0 or base_molarity <= 0.0:
		return 0.0
	var lo := 0.0
	var hi := eq * 1.5 + 1.0
	for _i in range(70):
		var mid := (lo + hi) * 0.5
		if ph_at(acid_molarity, acid_ml, base_molarity, mid, ka) >= target_ph:
			hi = mid
		else:
			lo = mid
	return (lo + hi) * 0.5


## Colour of the phenolphthalein/solution system at a given pH.
## Below 8.2 the lactone is colourless; the quinoid dianion develops pink to
## magenta as pH rises. Returned alpha is the liquid opacity, not indicator strength.
static func color_for_ph(ph: float) -> Color:
	var colourless := Color(0.16, 0.24, 0.29, 0.92)
	var pink := Color(0.88, 0.18, 0.48, 0.94)
	var magenta := Color(0.72, 0.05, 0.36, 0.96)
	if ph < PHENOLPHTHALEIN_PH:
		return colourless
	if ph <= 10.0:
		var t := clampf((ph - PHENOLPHTHALEIN_PH) / (10.0 - PHENOLPHTHALEIN_PH), 0.0, 1.0)
		return colourless.lerp(pink, t)
	return pink.lerp(magenta, clampf((ph - 10.0) / 2.0, 0.0, 1.0))


static func indicator_state(ph: float) -> String:
	if ph < PHENOLPHTHALEIN_PH:
		return "colourless"
	if ph < 10.0:
		return "persistent pink"
	return "magenta overshoot"
