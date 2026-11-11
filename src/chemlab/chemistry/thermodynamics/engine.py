"""
ChemLab Thermodynamics Engine — standard-state calculation core.

Migrated from:
  * src/chemlab/simulation/cantera_engine.py (CanteraThermodynamicsEngine)
  * chemlab_core/chemistry/reaction_engine.py (ThermodynamicState, THERMO_DATABASE)

Provides standard-state calculations from catalog inputs:
  * Reaction Enthalpy (ΔH°_rxn), Entropy (ΔS°_rxn), Gibbs Free Energy (ΔG°_rxn)
  * Equilibrium Constant K_eq(T) from ΔG°
  * Arrhenius kinetics: k(T) = A · exp(-E_a / (R · T))
  * Titration curves via Henderson-Hasselbalch
  * Adiabatic temperature rise estimates

Reference coverage varies by species. Fundamental compounds use published data
where available; estimated catalog values remain estimates and calculations do
not promote them to experimentally measured constants.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Universal gas constant in J/(mol * K)
R_GAS: float = 8.314462618


@dataclass(frozen=True)
class ThermodynamicState:
    """Standard thermodynamic properties of a pure chemical species at 298.15 K, 1 atm."""

    formula: str
    name: str
    delta_h_f_kj_mol: float  # Standard enthalpy of formation (kJ/mol)
    s_standard_j_mol_k: float  # Standard molar entropy (J/(mol*K))
    cp_j_mol_k: float  # Constant-pressure molar heat capacity (J/(mol*K))
    molecular_weight_g_mol: float
    density_g_cm3: float = 1.0


@dataclass
class ReactionThermodynamicsResult:
    """Computed thermodynamic and kinetic profile for a specific chemical reaction."""

    equation: str
    temperature_k: float
    delta_h_kj_mol: float
    delta_s_j_mol_k: float
    delta_g_kj_mol: float
    is_exothermic: bool
    is_spontaneous: bool
    equilibrium_constant_k_eq: float
    rate_constant_k: float
    adiabatic_temperature_rise_c: float
    half_life_seconds: float | None = None
    warnings: list[str] = field(default_factory=list)


# Reference NIST / CRC Handbook standard thermodynamic database
THERMO_DATABASE: dict[str, ThermodynamicState] = {
    # Inorganics & Acids/Bases
    "H2O": ThermodynamicState("H2O", "Water (liquid)", -285.83, 69.91, 75.38, 18.015, 1.000),
    "H2O_gas": ThermodynamicState("H2O", "Water (steam)", -241.82, 188.83, 33.58, 18.015, 0.0006),
    "HCl_aq": ThermodynamicState(
        "HCl", "Hydrochloric Acid (aq)", -167.16, 56.5, 75.0, 36.461, 1.18
    ),
    "NaOH_aq": ThermodynamicState(
        "NaOH", "Sodium Hydroxide (aq)", -470.11, 48.1, 87.0, 39.997, 2.13
    ),
    "NaCl_aq": ThermodynamicState(
        "NaCl", "Sodium Chloride (aq)", -407.27, 115.5, 85.0, 58.443, 2.16
    ),
    "H2SO4_aq": ThermodynamicState("H2SO4", "Sulfuric Acid", -909.27, 20.1, 138.0, 98.079, 1.84),
    "HNO3_aq": ThermodynamicState("HNO3", "Nitric Acid", -207.36, 146.4, 109.9, 63.013, 1.51),
    "NH3_aq": ThermodynamicState("NH3", "Ammonia (aq)", -80.29, 111.3, 79.0, 17.031, 0.90),
    "NH4Cl_s": ThermodynamicState("NH4Cl", "Ammonium Chloride", -314.43, 94.6, 84.1, 53.491, 1.53),
    "CuSO4_aq": ThermodynamicState(
        "CuSO4", "Copper(II) Sulfate", -771.4, -99.0, 100.0, 159.609, 2.28
    ),
    "H2O2_aq": ThermodynamicState("H2O2", "Hydrogen Peroxide", -191.17, 143.9, 89.1, 34.015, 1.45),
    "O2_gas": ThermodynamicState("O2", "Oxygen gas", 0.0, 205.15, 29.38, 31.999, 0.0014),
    "CO2_gas": ThermodynamicState("CO2", "Carbon Dioxide", -393.51, 213.74, 37.11, 44.01, 0.0019),
    "KMnO4_s": ThermodynamicState(
        "KMnO4", "Potassium Permanganate", -837.2, 171.7, 117.6, 158.034, 2.70
    ),
    "KI_aq": ThermodynamicState("KI", "Potassium Iodide", -327.9, 106.3, 51.3, 166.002, 3.12),
    # Organic synthesis & pharmaceuticals
    "salicylic_acid": ThermodynamicState(
        "C7H6O3", "Salicylic Acid", -589.9, 180.2, 159.0, 138.121, 1.44
    ),
    "acetic_anhydride": ThermodynamicState(
        "C4H6O3", "Acetic Anhydride", -624.4, 269.0, 182.0, 102.089, 1.08
    ),
    "aspirin": ThermodynamicState(
        "C9H8O4", "Acetylsalicylic Acid", -756.2, 208.5, 210.0, 180.158, 1.40
    ),
    "acetic_acid": ThermodynamicState("C2H4O2", "Acetic Acid", -484.5, 159.8, 124.3, 60.052, 1.05),
    "4_aminophenol": ThermodynamicState(
        "C6H7NO", "4-Aminophenol", -184.2, 155.0, 145.0, 109.126, 1.29
    ),
    "paracetamol": ThermodynamicState(
        "C8H9NO2", "Acetaminophen", -445.8, 195.0, 192.0, 151.163, 1.26
    ),
    "2_nitrobenzaldehyde": ThermodynamicState(
        "C7H5NO3", "2-Nitrobenzaldehyde", -171.0, 220.0, 165.0, 151.119, 1.34
    ),
    "acetone": ThermodynamicState("C3H6O", "Acetone", -248.4, 200.4, 126.3, 58.079, 0.784),
    "indigo": ThermodynamicState("C16H10N2O2", "Indigo Dye", -122.5, 310.0, 290.0, 262.268, 1.35),
    "ethanol": ThermodynamicState("C2H6O", "Ethanol", -277.69, 160.7, 112.3, 46.068, 0.789),
    "methanol": ThermodynamicState("CH4O", "Methanol", -238.6, 126.8, 81.6, 32.042, 0.792),
    "diethyl_ether": ThermodynamicState(
        "C4H10O", "Diethyl Ether", -279.3, 218.4, 172.5, 74.122, 0.713
    ),
    "toluene": ThermodynamicState("C7H8", "Toluene", 12.0, 221.0, 157.3, 92.141, 0.867),
    "benzene": ThermodynamicState("C6H6", "Benzene", 49.0, 173.3, 136.0, 78.114, 0.876),
    "chloroform": ThermodynamicState("CHCl3", "Chloroform", -134.1, 201.7, 114.2, 119.38, 1.489),
    "dichloromethane": ThermodynamicState(
        "CH2Cl2", "Dichloromethane", -124.2, 177.8, 100.4, 84.93, 1.326
    ),
    "ethyl_acetate": ThermodynamicState(
        "C4H8O2", "Ethyl Acetate", -480.0, 259.4, 170.1, 88.11, 0.902
    ),
    "benzoic_acid": ThermodynamicState(
        "C7H6O2", "Benzoic Acid", -385.2, 167.6, 146.8, 122.12, 1.266
    ),
    "benzaldehyde": ThermodynamicState("C7H6O", "Benzaldehyde", -86.8, 224.5, 170.8, 106.12, 1.044),
    "aniline": ThermodynamicState("C6H7N", "Aniline", 31.1, 191.3, 190.7, 93.13, 1.022),
    "acetanilide": ThermodynamicState("C8H9NO", "Acetanilide", -213.6, 185.0, 178.0, 135.17, 1.219),
    "luminol": ThermodynamicState("C8H7N3O2", "Luminol", -145.0, 210.0, 195.0, 177.16, 1.43),
    "caffeine": ThermodynamicState("C8H10N4O2", "Caffeine", -337.8, 245.0, 230.0, 194.19, 1.23),
    "hydroquinone": ThermodynamicState(
        "C6H6O2", "Hydroquinone", -364.5, 140.0, 148.0, 110.11, 1.30
    ),
    "sodium_bicarbonate": ThermodynamicState(
        "NaHCO3", "Sodium Bicarbonate", -950.8, 101.7, 87.6, 84.007, 2.20
    ),
    "sodium_carbonate": ThermodynamicState(
        "Na2CO3", "Sodium Carbonate", -1130.7, 135.0, 112.3, 105.988, 2.54
    ),
    "calcium_chloride": ThermodynamicState(
        "CaCl2", "Calcium Chloride", -795.8, 104.6, 72.5, 110.98, 2.15
    ),
    "silver_nitrate": ThermodynamicState(
        "AgNO3", "Silver Nitrate", -124.4, 140.9, 93.0, 169.87, 4.35
    ),
    "iron_iii_chloride": ThermodynamicState(
        "FeCl3", "Iron(III) Chloride", -399.5, 142.3, 96.6, 162.2, 2.90
    ),
    "sodium_thiosulfate": ThermodynamicState(
        "Na2S2O3", "Sodium Thiosulfate", -1123.0, 155.0, 130.0, 158.11, 1.667
    ),
}


def _populate_pihkal_tihkal_species() -> None:
    try:
        from chemlab.chemistry.literature_catalogs import PIHKAL_TIHKAL_SPECIES

        for sid, sp in PIHKAL_TIHKAL_SPECIES.items():
            if sid not in THERMO_DATABASE:
                THERMO_DATABASE[sid] = ThermodynamicState(
                    formula=sp.formula,
                    name=sp.name,
                    delta_h_f_kj_mol=sp.delta_h_f_kj_mol,
                    s_standard_j_mol_k=sp.s_standard_j_mol_k,
                    cp_j_mol_k=sp.cp_j_mol_k,
                    molecular_weight_g_mol=sp.molecular_weight_g_mol,
                    density_g_cm3=sp.density_g_cm3,
                )
    except ImportError:
        pass


_populate_pihkal_tihkal_species()


class CanteraThermodynamicsEngine:
    """Rigorous chemical thermodynamics and Arrhenius kinetics calculator."""

    def __init__(self) -> None:
        self.db = THERMO_DATABASE

    def get_species(self, key: str) -> ThermodynamicState | None:
        """Retrieves species thermodynamic state by identifier or formula."""
        return self.db.get(key)

    def calculate_reaction_thermodynamics(
        self,
        reactants: dict[str, float],
        products: dict[str, float],
        temperature_c: float = 25.0,
        activation_energy_kj_mol: float = 55.0,
        pre_exponential_factor_a: float = 1.0e11,
    ) -> ReactionThermodynamicsResult:
        """
        Calculates thermodynamic parameters from the configured species data:
          ΔH°_rxn = Σ (ν_prod * ΔH°_f,prod) - Σ (ν_react * ΔH°_f,react)
          ΔS°_rxn = Σ (ν_prod * S°_prod) - Σ (ν_react * S°_react)
          ΔG°(T) = ΔH°_rxn - T * ΔS°_rxn
          K_eq(T) = exp(-ΔG° / (R * T))
          k(T) = A * exp(-E_a / (R * T))
        """
        temp_k = temperature_c + 273.15

        h_reactants = sum(
            coeff * self.db[s].delta_h_f_kj_mol for s, coeff in reactants.items() if s in self.db
        )
        h_products = sum(
            coeff * self.db[s].delta_h_f_kj_mol for s, coeff in products.items() if s in self.db
        )
        delta_h_kj = h_products - h_reactants

        s_reactants = sum(
            coeff * self.db[s].s_standard_j_mol_k for s, coeff in reactants.items() if s in self.db
        )
        s_products = sum(
            coeff * self.db[s].s_standard_j_mol_k for s, coeff in products.items() if s in self.db
        )
        delta_s_j = s_products - s_reactants

        delta_g_kj = delta_h_kj - (temp_k * (delta_s_j / 1000.0))

        exponent = -(delta_g_kj * 1000.0) / (R_GAS * temp_k)
        clamped_exp = max(-700.0, min(700.0, exponent))
        k_eq = math.exp(clamped_exp)

        ea_j = activation_energy_kj_mol * 1000.0
        arrhenius_exp = -ea_j / (R_GAS * temp_k)
        rate_k = pre_exponential_factor_a * math.exp(max(-700.0, min(700.0, arrhenius_exp)))

        half_life = (math.log(2) / rate_k) if rate_k > 1e-12 else None

        total_heat_capacity = (
            sum(coeff * self.db[s].cp_j_mol_k for s, coeff in products.items() if s in self.db)
            or 100.0
        )
        delta_t_ad = max(0.0, (-delta_h_kj * 1000.0) / total_heat_capacity)

        warnings: list[str] = []
        if delta_h_kj < -150.0:
            warnings.append(
                "Stark exotherme Reaktion — Explosions- und Siedeverzugsgefahr ohne Kühlbad."
            )
        if delta_t_ad > 120.0:
            warnings.append(
                "Adiabatischer Temperatursprung überschreitet Lösemittelsiedepunkt — Rückflusskühler erforderlich."
            )
        if delta_g_kj > 30.0:
            warnings.append(
                "Reaktion ist unter Normalbedingungen nicht spontan (ΔG° > 0) — Energiezufuhr oder Katalysator nötig."
            )

        react_str = " + ".join(f"{int(c) if c == int(c) else c} {s}" for s, c in reactants.items())
        prod_str = " + ".join(f"{int(c) if c == int(c) else c} {s}" for s, c in products.items())
        equation = f"{react_str} -> {prod_str}"

        return ReactionThermodynamicsResult(
            equation=equation,
            temperature_k=round(temp_k, 2),
            delta_h_kj_mol=round(delta_h_kj, 2),
            delta_s_j_mol_k=round(delta_s_j, 2),
            delta_g_kj_mol=round(delta_g_kj, 2),
            is_exothermic=delta_h_kj < 0,
            is_spontaneous=delta_g_kj < 0,
            equilibrium_constant_k_eq=k_eq,
            rate_constant_k=rate_k,
            adiabatic_temperature_rise_c=round(delta_t_ad, 1),
            half_life_seconds=round(half_life, 3) if half_life else None,
            warnings=warnings,
        )

    def calculate_titration_curve(
        self,
        analyte_conc_m: float,
        analyte_vol_ml: float,
        titrant_conc_m: float,
        pka: float = 4.76,
        points: int = 50,
    ) -> list[tuple[float, float]]:
        """
        Computes accurate pH titration curve points (V_titrant_ml, pH)
        using Henderson-Hasselbalch buffer equation and excess ion concentration.
        """
        v_equiv_ml = (analyte_conc_m * analyte_vol_ml) / titrant_conc_m
        curve: list[tuple[float, float]] = []

        max_v = v_equiv_ml * 2.0
        step = max_v / float(points)

        for i in range(points + 1):
            v_add = i * step
            if v_add == 0:
                ph = 0.5 * (pka - math.log10(max(1e-5, analyte_conc_m)))
            elif v_add < v_equiv_ml:
                fraction = v_add / v_equiv_ml
                ratio = fraction / max(1e-6, 1.0 - fraction)
                ph = pka + math.log10(max(1e-4, ratio))
            elif abs(v_add - v_equiv_ml) < (step * 0.25):
                salt_conc = (analyte_conc_m * analyte_vol_ml) / (analyte_vol_ml + v_add)
                poh = 0.5 * ((14.0 - pka) - math.log10(max(1e-5, salt_conc)))
                ph = 14.0 - poh
            else:
                excess_moles = (v_add - v_equiv_ml) * 0.001 * titrant_conc_m
                total_vol_l = (analyte_vol_ml + v_add) * 0.001
                oh_conc = excess_moles / total_vol_l
                poh = -math.log10(max(1e-14, oh_conc))
                ph = min(14.0, 14.0 - poh)

            curve.append((round(v_add, 2), round(max(0.0, min(14.0, ph)), 2)))

        return curve


# Global singleton instance
THERMO_ENGINE = CanteraThermodynamicsEngine()
