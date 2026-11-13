"""Pyrotechnic composition model.

Implements the standard composition arithmetic used in pyrotechnic education:

* oxygen balance (OB) of an oxidiser/fuel pair,
* burn rate as a function of composition and confinement,
* flame colour from the dominant emitting species,
* hazard classification from sensitivity inputs.

The equations are empirical teaching models. They are not a manufacturing
guide: real formulations require licensed facilities, quantity-distance rules
and competent supervision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Elemental composition of common oxidisers as (metal, oxygen mass fraction).
OXIDISERS: dict[str, dict[str, float]] = {
    "potassium_nitrate": {"oxygen": 0.475, "metal": 0.387, "decomp_c": 400.0},
    "potassium_chlorate": {"oxygen": 0.392, "metal": 0.319, "decomp_c": 400.0},
    "potassium_perchlorate": {"oxygen": 0.462, "metal": 0.282, "decomp_c": 600.0},
    "sodium_nitrate": {"oxygen": 0.565, "metal": 0.271, "decomp_c": 380.0},
    "strontium_nitrate": {"oxygen": 0.454, "metal": 0.414, "decomp_c": 570.0},
    "barium_nitrate": {"oxygen": 0.367, "metal": 0.525, "decomp_c": 592.0},
    "ammonium_nitrate": {"oxygen": 0.600, "metal": 0.000, "decomp_c": 210.0},
    "ammonium_perchlorate": {"oxygen": 0.544, "metal": 0.000, "decomp_c": 240.0},
    "copper_ii_oxide": {"oxygen": 0.201, "metal": 0.799, "decomp_c": 1000.0},
}

# Oxygen demand of fuels, grams of O2 per gram of fuel for complete combustion.
FUELS: dict[str, dict[str, float]] = {
    "charcoal": {"oxygen_demand": 2.66, "heat_j_g": 31000.0},
    "sulfur": {"oxygen_demand": 1.00, "heat_j_g": 9200.0},
    "aluminium": {"oxygen_demand": 0.89, "heat_j_g": 31000.0},
    "magnesium": {"oxygen_demand": 0.66, "heat_j_g": 24700.0},
    "dextrin": {"oxygen_demand": 1.19, "heat_j_g": 16000.0},
    "hexamine": {"oxygen_demand": 1.60, "heat_j_g": 30000.0},
    "sodium_benzoate": {"oxygen_demand": 1.55, "heat_j_g": 26000.0},
    "pvc": {"oxygen_demand": 1.40, "heat_j_g": 18000.0},
    "titanium": {"oxygen_demand": 0.67, "heat_j_g": 19000.0},
    "iron_oxide": {"oxygen_demand": 0.30, "heat_j_g": 7000.0},
}

# Emission lines used for star colour, with the species responsible.
COLORANTS: dict[str, dict[str, object]] = {
    "strontium": {"nm": 606, "rgb": (1.0, 0.22, 0.18), "species": "SrCl / SrOH"},
    "barium": {"nm": 524, "rgb": (0.25, 1.0, 0.45), "species": "BaCl / BaOH"},
    "copper": {"nm": 590, "rgb": (0.30, 0.55, 1.0), "species": "CuCl"},
    "sodium": {"nm": 589, "rgb": (1.0, 0.72, 0.20), "species": "Na"},
    "calcium": {"nm": 622, "rgb": (1.0, 0.55, 0.15), "species": "CaCl"},
    "none": {"nm": 0, "rgb": (1.0, 0.85, 0.55), "species": "blackbody"},
}


@dataclass(frozen=True)
class Component:
    substance: str
    fraction: float

    def __post_init__(self) -> None:
        if not 0.0 < self.fraction <= 1.0:
            raise ValueError("component fraction must be in (0, 1]")


@dataclass(frozen=True)
class Composition:
    name: str
    components: tuple[Component, ...]
    colorant: str = "none"
    confinement: float = 0.0  # 0 = open pile, 1 = tightly confined
    moisture_fraction: float = 0.0
    notes: str = ""

    def __post_init__(self) -> None:
        total = sum(c.fraction for c in self.components)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"{self.name}: fractions must sum to 1.0, got {total:.4f}")

    @property
    def oxidiser_fraction(self) -> float:
        return sum(c.fraction for c in self.components if c.substance in OXIDISERS)

    @property
    def fuel_fraction(self) -> float:
        return sum(c.fraction for c in self.components if c.substance in FUELS)


@dataclass(frozen=True)
class BurnResult:
    oxygen_balance_g_o2_per_g: float
    adiabatic_flame_temp_c: float
    burn_rate_mm_s: float
    flame_rgb: tuple[float, float, float]
    emission_nm: int
    sensitivity: str
    hazard_class: str
    warnings: tuple[str, ...] = field(default_factory=tuple)


def oxygen_balance(composition: Composition) -> float:
    """Oxygen balance in g O2 per g composition.

    Positive means the composition carries more oxygen than its fuels need;
    negative means it is fuel-rich.
    """
    supplied = 0.0
    demanded = 0.0
    for component in composition.components:
        if component.substance in OXIDISERS:
            supplied += component.fraction * OXIDISERS[component.substance]["oxygen"]
        elif component.substance in FUELS:
            demanded += component.fraction * FUELS[component.substance]["oxygen_demand"]
    return round(supplied - demanded, 4)


def adiabatic_flame_temp(composition: Composition) -> float:
    """Very rough adiabatic flame temperature above 25 C.

    Uses weighted heat release divided by a lumped product heat capacity.
    Values are order-of-magnitude only, which is all the game needs to colour
    the burn and decide whether metal oxides glow.
    """
    heat = 0.0
    mass = 0.0
    for component in composition.components:
        if component.substance in FUELS:
            heat += component.fraction * FUELS[component.substance]["heat_j_g"]
        else:
            heat += component.fraction * 4000.0
        mass += component.fraction

    balance = oxygen_balance(composition)
    efficiency = max(0.35, 1.0 - abs(balance) * 1.4)
    lumped_cp = 1.25  # J/(g K), products + excess air
    return round(25.0 + (heat * efficiency) / (mass * lumped_cp), 0)


def burn_rate(composition: Composition) -> float:
    """Empirical burn rate in mm/s for a pressed composition."""
    balance = abs(oxygen_balance(composition))
    stoichiometry = max(0.05, 1.0 - balance)
    base = 2.0 + 28.0 * stoichiometry
    confinement = 1.0 + 2.5 * composition.confinement
    moisture = max(0.2, 1.0 - 6.0 * composition.moisture_fraction)
    if "potassium_chlorate" in {c.substance for c in composition.components}:
        base *= 1.9
    if "potassium_perchlorate" in {c.substance for c in composition.components}:
        base *= 1.5
    if "aluminium" in {c.substance for c in composition.components}:
        base *= 0.75
    return round(base * confinement * moisture, 2)


def flame_color(composition: Composition) -> tuple[tuple[float, float, float], int]:
    entry = COLORANTS.get(composition.colorant, COLORANTS["none"])
    return tuple(entry["rgb"]), int(entry["nm"])  # type: ignore[arg-type]


def sensitivity(composition: Composition) -> str:
    substances = {c.substance for c in composition.components}
    if "potassium_chlorate" in substances and "sulfur" in substances:
        return "extreme"
    if "potassium_chlorate" in substances or "potassium_perchlorate" in substances:
        return "high"
    if "aluminium" in substances or "magnesium" in substances:
        return "moderate"
    if "ammonia" not in substances and composition.moisture_fraction > 0.05:
        return "low"
    return "moderate"


def hazard_class(composition: Composition) -> str:
    level = sensitivity(composition)
    if level == "extreme":
        return "1.1A (mass explosion hazard, chlorate/sulfur)"
    if level == "high":
        return "1.1D (detonating secondary explosive risk when confined)"
    if composition.confinement > 0.6:
        return "1.3G (major fire hazard, confined)"
    return "1.4G (minor explosion hazard)"


def evaluate(composition: Composition) -> BurnResult:
    rgb, nm = flame_color(composition)
    warnings: list[str] = []
    substances = {c.substance for c in composition.components}

    if "potassium_chlorate" in substances and "sulfur" in substances:
        warnings.append("Chlorate + sulfur is friction/impact sensitive; never combine.")
    if "barium_nitrate" in substances:
        warnings.append("Barium salts are toxic; use respiratory protection and wash hands.")
    if composition.moisture_fraction > 0.05:
        warnings.append("Moisture above 5% degrades burn reliability.")
    if abs(oxygen_balance(composition)) > 0.25:
        warnings.append("Composition is far from oxygen balance; expect soot or incomplete burn.")

    return BurnResult(
        oxygen_balance_g_o2_per_g=oxygen_balance(composition),
        adiabatic_flame_temp_c=adiabatic_flame_temp(composition),
        burn_rate_mm_s=burn_rate(composition),
        flame_rgb=rgb,  # type: ignore[arg-type]
        emission_nm=nm,
        sensitivity=sensitivity(composition),
        hazard_class=hazard_class(composition),
        warnings=tuple(warnings),
    )
