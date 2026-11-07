# Athanor Ascension - Python Chemistry Core
# Offline scientific engine for Godot IPC bridge
# Cantera-free pure Python implementation with NIST/CRC constants

from __future__ import annotations

import math
import json
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from queue import Queue, Empty
from enum import Enum

# =============================================================================
# THERMODYNAMIC DATABASE (NIST/CRC)
# =============================================================================

R_GAS = 8.314462618  # J/(mol*K)

@dataclass(frozen=True)
class ThermodynamicState:
    """Standard thermodynamic properties at 298.15 K, 1 atm."""
    formula: str
    name: str
    delta_h_f_kj_mol: float
    s_standard_j_mol_k: float
    cp_j_mol_k: float
    molecular_weight_g_mol: float
    density_g_cm3: float = 1.0
    is_acid: bool = False
    is_base: bool = False
    acid_pka: float = 7.0
    boiling_point_c: float = 100.0
    flash_point_c: float = -1.0
    is_volatile: bool = False
    ghs_pictograms: List[str] = field(default_factory=list)
    h_statements: List[str] = field(default_factory=list)
    p_statements: List[str] = field(default_factory=list)
    cas_number: str = ""

# Reference NIST/CRC database
THERMO_DB: Dict[str, ThermodynamicState] = {
    # Water
    "H2O": ThermodynamicState("H2O", "Water (liquid)", -285.83, 69.91, 75.38, 18.015, 1.000),
    "H2O_gas": ThermodynamicState("H2O", "Water (steam)", -241.82, 188.83, 33.58, 18.015, 0.0006),

    # Strong acids
    "HCl_aq": ThermodynamicState("HCl", "Hydrochloric Acid (aq)", -167.16, 56.5, 75.0, 36.461, 1.18,
        is_acid=True, acid_pka=-7.0, boiling_point_c=110.0, is_volatile=True,
        ghs_pictograms=["GHS05", "GHS07"], h_statements=["H314", "H335"],
        p_statements=["P260", "P280", "P305+P351+P338"], cas_number="7647-01-0"),

    "H2SO4_aq": ThermodynamicState("H2SO4", "Sulfuric Acid", -909.27, 20.1, 138.0, 98.079, 1.84,
        is_acid=True, acid_pka=-3.0, boiling_point_c=337.0, is_volatile=False,
        ghs_pictograms=["GHS05"], h_statements=["H314"],
        p_statements=["P280", "P305+P351+P338"], cas_number="7664-93-9"),

    "HNO3_aq": ThermodynamicState("HNO3", "Nitric Acid", -207.36, 146.4, 109.9, 63.013, 1.51,
        is_acid=True, acid_pka=-1.4, boiling_point_c=121.0, is_volatile=True,
        ghs_pictograms=["GHS03", "GHS05", "GHS07"], h_statements=["H272", "H314", "H331"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="7697-37-2"),

    # Strong bases
    "NaOH_aq": ThermodynamicState("NaOH", "Sodium Hydroxide (aq)", -470.11, 48.1, 87.0, 39.997, 2.13,
        is_base=True, acid_pka=15.7, boiling_point_c=1390.0, is_volatile=False,
        ghs_pictograms=["GHS05"], h_statements=["H314"],
        p_statements=["P280", "P305+P351+P338"], cas_number="1310-73-2"),

    "KOH_aq": ThermodynamicState("KOH", "Potassium Hydroxide (aq)", -482.4, 78.9, 95.0, 56.106, 2.04,
        is_base=True, acid_pka=15.7, boiling_point_c=1327.0, is_volatile=False,
        ghs_pictograms=["GHS05"], h_statements=["H314"],
        p_statements=["P280", "P305+P351+P338"], cas_number="1310-58-3"),

    # Weak acids
    "CH3COOH_aq": ThermodynamicState("CH3COOH", "Acetic Acid", -484.5, 159.8, 124.3, 60.052, 1.05,
        is_acid=True, acid_pka=4.76, boiling_point_c=118.0, is_volatile=True,
        ghs_pictograms=["GHS02", "GHS05", "GHS07"], h_statements=["H226", "H314", "H332"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="64-19-7"),

    "C7H6O3": ThermodynamicState("C7H6O3", "Salicylic Acid", -589.9, 180.2, 159.0, 138.121, 1.44,
        is_acid=True, acid_pka=2.97, boiling_point_c=211.0, is_volatile=False,
        ghs_pictograms=["GHS07"], h_statements=["H315", "H319", "H335"],
        p_statements=["P261", "P280", "P305+P351+P338"], cas_number="69-72-7"),

    "C4H6O3": ThermodynamicState("C4H6O3", "Acetic Anhydride", -624.4, 269.0, 182.0, 102.089, 1.08,
        acid_pka=15.0, boiling_point_c=140.0, is_volatile=True,
        ghs_pictograms=["GHS02", "GHS05", "GHS07"], h_statements=["H226", "H314", "H332"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="108-24-7"),

    "C9H8O4": ThermodynamicState("C9H8O4", "Acetylsalicylic Acid (Aspirin)", -756.2, 208.5, 210.0, 180.158, 1.40,
        is_acid=True, acid_pka=3.49, boiling_point_c=140.0, is_volatile=False,
        ghs_pictograms=["GHS07"], h_statements=["H315", "H319"],
        p_statements=["P280", "P305+P351+P338"], cas_number="50-78-2"),

    "C6H7NO": ThermodynamicState("C6H7NO", "4-Aminophenol", -184.2, 155.0, 145.0, 109.126, 1.29,
        is_base=True, acid_pka=10.3, boiling_point_c=284.0, is_volatile=False,
        ghs_pictograms=["GHS07", "GHS09"], h_statements=["H301", "H315", "H319", "H410"],
        p_statements=["P273", "P280", "P305+P351+P338"], cas_number="123-30-8"),

    "C8H9NO2": ThermodynamicState("C8H9NO2", "Paracetamol", -445.8, 195.0, 192.0, 151.163, 1.26,
        is_acid=True, acid_pka=9.5, boiling_point_c=420.0, is_volatile=False,
        ghs_pictograms=["GHS07"], h_statements=["H301", "H315", "H319"],
        p_statements=["P280", "P305+P351+P338"], cas_number="103-90-2"),

    # Salts
    "NaCl_aq": ThermodynamicState("NaCl", "Sodium Chloride (aq)", -407.27, 115.5, 85.0, 58.443, 2.16,
        acid_pka=7.0, boiling_point_c=1465.0, is_volatile=False, cas_number="7647-14-5"),

    "NaHCO3_aq": ThermodynamicState("NaHCO3", "Sodium Bicarbonate", -950.8, 101.7, 87.6, 84.007, 2.20,
        is_base=True, acid_pka=10.3, boiling_point_c=851.0, is_volatile=False, cas_number="144-55-8"),

    # Peroxides
    "H2O2_aq": ThermodynamicState("H2O2", "Hydrogen Peroxide", -191.17, 143.9, 89.1, 34.015, 1.45,
        acid_pka=11.7, boiling_point_c=150.0, is_volatile=True,
        ghs_pictograms=["GHS03", "GHS05", "GHS07"], h_statements=["H272", "H314", "H332"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="7722-84-1"),

    # Iodides
    "KI_aq": ThermodynamicState("KI", "Potassium Iodide", -327.9, 106.3, 51.3, 166.002, 3.12,
        acid_pka=7.0, boiling_point_c=1330.0, is_volatile=False, cas_number="7681-11-0"),

    # Gases
    "O2_gas": ThermodynamicState("O2", "Oxygen Gas", 0.0, 205.15, 29.38, 31.999, 0.0014,
        boiling_point_c=-183.0, is_volatile=True,
        ghs_pictograms=["GHS03", "GHS04"], h_statements=["H270", "H280"],
        p_statements=["P220", "P244"], cas_number="7782-44-7"),

    "CO2_gas": ThermodynamicState("CO2", "Carbon Dioxide", -393.51, 213.74, 37.11, 44.01, 0.0019,
        is_acid=True, acid_pka=6.35, boiling_point_c=-78.5, is_volatile=True,
        ghs_pictograms=["GHS04"], h_statements=["H280"], p_statements=["P403"], cas_number="124-38-9"),

    # Organic solvents
    "C2H5OH": ThermodynamicState("C2H5OH", "Ethanol", -277.69, 160.7, 112.3, 46.068, 0.789,
        acid_pka=15.9, boiling_point_c=78.37, is_volatile=True,
        ghs_pictograms=["GHS02", "GHS07"], h_statements=["H225", "H319"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="64-17-5"),

    "CH3OH": ThermodynamicState("CH3OH", "Methanol", -238.6, 126.8, 81.6, 32.042, 0.792,
        acid_pka=15.5, boiling_point_c=64.7, is_volatile=True,
        ghs_pictograms=["GHS02", "GHS06", "GHS08"], h_statements=["H225", "H301", "H311", "H331", "H370"],
        p_statements=["P210", "P280", "P305+P351+P338", "P310"], cas_number="67-56-1"),

    # Indicators
    "phenolphthalein": ThermodynamicState("C20H14O4", "Phenolphthalein", -500.0, 200.0, 200.0, 318.32, 1.27,
        is_acid=True, acid_pka=9.4, boiling_point_c=300.0, is_volatile=False, cas_number="77-09-8"),

    # Briggs-Rauscher components
    "MnSO4_aq": ThermodynamicState("MnSO4", "Manganese(II) Sulfate", -1065.0, 120.0, 100.0, 151.001, 3.25,
        boiling_point_c=700.0, is_volatile=False,
        ghs_pictograms=["GHS07", "GHS09"], h_statements=["H302", "H315", "H319", "H410"],
        p_statements=["P273", "P280", "P305+P351+P338"], cas_number="7785-87-7"),

    "KIO3_aq": ThermodynamicState("KIO3", "Potassium Iodate", -490.0, 150.0, 110.0, 214.001, 3.89,
        boiling_point_c=560.0, is_volatile=False,
        ghs_pictograms=["GHS03", "GHS07"], h_statements=["H272", "H302", "H315", "H319"],
        p_statements=["P210", "P280", "P305+P351+P338"], cas_number="7758-05-6"),

    "malonic_acid": ThermodynamicState("C3H4O4", "Malonic Acid", -850.0, 160.0, 130.0, 104.06, 1.62,
        is_acid=True, acid_pka=2.83, boiling_point_c=200.0, is_volatile=False,
        ghs_pictograms=["GHS07"], h_statements=["H315", "H319"],
        p_statements=["P280", "P305+P351+P338"], cas_number="141-82-2"),

    # Precipitation ions
    "Ag+": ThermodynamicState("Ag+", "Silver Ion", 105.0, 72.0, 50.0, 107.87, 1.0, is_ion=True),
    "Cl-": ThermodynamicState("Cl-", "Chloride Ion", -167.2, 56.5, 50.0, 35.45, 1.0, is_ion=True),
    "Ba2+": ThermodynamicState("Ba2+", "Barium Ion", -537.6, 8.0, 50.0, 137.33, 1.0, is_ion=True),
    "SO4^2-": ThermodynamicState("SO4^2-", "Sulfate Ion", -909.3, 20.1, 50.0, 96.06, 1.0, is_ion=True),
    "Pb2+": ThermodynamicState("Pb2+", "Lead(II) Ion", 0.0, 18.5, 50.0, 207.2, 1.0, is_ion=True),
    "Ca2+": ThermodynamicState("Ca2+", "Calcium Ion", -542.8, -53.1, 50.0, 40.08, 1.0, is_ion=True),
    "CO3^2-": ThermodynamicState("CO3^2-", "Carbonate Ion", -677.1, -56.9, 50.0, 60.01, 1.0,
        is_base=True, acid_pka=10.3, is_ion=True),
    "Fe3+": ThermodynamicState("Fe3+", "Iron(III) Ion", -48.5, -137.7, 50.0, 55.85, 1.0,
        is_acid=True, acid_pka=2.2, is_ion=True),
    "OH-": ThermodynamicState("OH-", "Hydroxide Ion", -230.0, -10.9, 50.0, 17.01, 1.0,
        is_base=True, acid_pka=15.7, is_ion=True),
    "Cu2+": ThermodynamicState("Cu2+", "Copper(II) Ion", 64.8, -99.6, 50.0, 63.55, 1.0,
        is_acid=True, acid_pka=7.0, is_ion=True),
}

# =============================================================================
# CORE CALCULATION ENGINE
# =============================================================================

@dataclass
class ReactionThermodynamicsResult:
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
    half_life_seconds: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

class CanteraThermodynamicsEngine:
    """Pure Python thermodynamics and kinetics calculator."""

    def __init__(self):
        self.db = THERMO_DB

    def get_species(self, key: str) -> Optional[ThermodynamicState]:
        return self.db.get(key)

    def calculate_reaction_thermodynamics(
        self,
        reactants: Dict[str, float],
        products: Dict[str, float],
        temperature_c: float = 25.0,
        activation_energy_kj_mol: float = 55.0,
        pre_exponential_factor_a: float = 1.0e11,
    ) -> ReactionThermodynamicsResult:
        temp_k = temperature_c + 273.15

        # Enthalpy of reaction
        h_reactants = sum(
            coeff * self.db[s].delta_h_f_kj_mol for s, coeff in reactants.items() if s in self.db
        )
        h_products = sum(
            coeff * self.db[s].delta_h_f_kj_mol for s, coeff in products.items() if s in self.db
        )
        delta_h_kj = h_products - h_reactants

        # Entropy of reaction
        s_reactants = sum(
            coeff * self.db[s].s_standard_j_mol_k for s, coeff in reactants.items() if s in self.db
        )
        s_products = sum(
            coeff * self.db[s].s_standard_j_mol_k for s, coeff in products.items() if s in self.db
        )
        delta_s_j = s_products - s_reactants

        # Gibbs Free Energy
        delta_g_kj = delta_h_kj - (temp_k * (delta_s_j / 1000.0))

        # Equilibrium constant
        exponent = -(delta_g_kj * 1000.0) / (R_GAS * temp_k)
        clamped_exp = max(-700.0, min(700.0, exponent))
        k_eq = math.exp(clamped_exp)

        # Arrhenius rate constant
        ea_j = activation_energy_kj_mol * 1000.0
        arrhenius_exp = -ea_j / (R_GAS * temp_k)
        rate_k = pre_exponential_factor_a * math.exp(max(-700.0, min(700.0, arrhenius_exp)))

        # Half-life
        half_life = (math.log(2) / rate_k) if rate_k > 1e-12 else None

        # Adiabatic temperature rise
        total_heat_capacity = (
            sum(coeff * self.db[s].cp_j_mol_k for s, coeff in products.items() if s in self.db)
            or 100.0
        )
        delta_t_ad = max(0.0, (-delta_h_kj * 1000.0) / total_heat_capacity)

        # Warnings
        warnings = []
        if delta_h_kj < -150.0:
            warnings.append("Stark exotherme Reaktion — Explosions- und Siedeverzugsgefahr ohne Kühlbad.")
        if delta_t_ad > 120.0:
            warnings.append("Adiabatischer Temperatursprung überschreitet Lösemittelsiedepunkt — Rückflusskühler erforderlich.")
        if delta_g_kj > 30.0:
            warnings.append("Reaktion ist unter Normalbedingungen nicht spontan (ΔG° > 0) — Energiezufuhr oder Katalysator nötig.")

        # Equation string
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
            warnings=warnings
        )

    def calculate_titration_curve(
        self,
        analyte_conc_m: float,
        analyte_vol_ml: float,
        titrant_conc_m: float,
        pka: float = 4.76,
        points: int = 50,
    ) -> List[Tuple[float, float]]:
        v_equiv_ml = (analyte_conc_m * analyte_vol_ml) / titrant_conc_m
        curve = []

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


# =============================================================================
# SIDE REACTIONS & IMPURITY ENGINE
# =============================================================================

from enum import Enum

class ImpuritySeverity(str, Enum):
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"

@dataclass(frozen=True)
class ImpurityProduct:
    name: str
    formula: str
    mass_fraction: float
    severity: ImpuritySeverity
    description: str

@dataclass
class ReactionConditionParameters:
    reaction_id: str
    temperature_c: float
    has_catalyst: bool = True
    addition_order_correct: bool = True
    stirring_rpm: int = 400
    reaction_time_s: float = 60.0

@dataclass
class SideReactionReport:
    is_successful: bool
    purity_percentage: float
    tarring_extent: float = 0.0
    unreacted_fraction: float = 0.0
    violent_exotherm: bool = False
    aerosol_splashing: bool = False
    impurities: List[ImpurityProduct] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    color_discoloration_rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0)

class SideReactionAnalyzer:
    def evaluate_conditions(self, params: ReactionConditionParameters) -> SideReactionReport:
        rid = params.reaction_id.lower().strip()

        # Physical Hazard: Inverted addition of water into concentrated acid
        if not params.addition_order_correct:
            return SideReactionReport(
                is_successful=False,
                purity_percentage=10.0,
                tarring_extent=0.0,
                unreacted_fraction=0.8,
                violent_exotherm=True,
                aerosol_splashing=True,
                impurities=[
                    ImpurityProduct(
                        name="Aerosolisierte Schwefelsäuretröpfchen",
                        formula="H2SO4 (aq, aerosol)",
                        mass_fraction=0.15,
                        severity=ImpuritySeverity.CRITICAL,
                        description="Siedeverzug durch extreme Hydratationswärme."
                    )
                ],
                warnings=[
                    "GEFAHR: Erst das Wasser, dann die Säure, sonst geschieht das Ungeheure!",
                    "Plötzliches Sieden und Verspritzen von ätzender Säure durch unzureichende Wärmeabfuhr."
                ],
                color_discoloration_rgb=(0.95, 0.95, 0.95)
            )

        if "aspirin" in rid:
            return self._evaluate_aspirin(params)
        if "paracetamol" in rid:
            return self._evaluate_paracetamol(params)
        if "acetanilide" in rid:
            return self._evaluate_acetanilide(params)

        return self._evaluate_generic(params)

    def _evaluate_aspirin(self, p: ReactionConditionParameters) -> SideReactionReport:
        optimal_t = 65.0
        delta_t = p.temperature_c - optimal_t
        impurities = []
        warnings = []
        tarring = 0.0
        unreacted = 0.0
        color = (0.96, 0.96, 0.98)

        if not p.has_catalyst:
            unreacted = 0.72
            warnings.append("Fehlender Katalysator (H2SO4): Reaktion verlaeuft unvollstaendig. Hoher Eduktanteil.")
            impurities.append(ImpurityProduct(
                name="Unreagierte Salicylsäure", formula="C7H6O3", mass_fraction=unreacted,
                severity=ImpuritySeverity.CRITICAL,
                description="Ausgangsmaterial verunreinigt den Kristallkuchen."
            ))

        if delta_t > 20.0:
            tarring = min(1.0, 0.15 + (delta_t - 20.0) * 0.015)
            poly_fraction = min(0.45, 0.1 + (delta_t - 20.0) * 0.012)
            impurities.append(ImpurityProduct(
                name="Polysalicylate & Braune Verharzung (Teer)", formula="[-C7H4O2-]n",
                mass_fraction=poly_fraction, severity=ImpuritySeverity.CRITICAL,
                description="Selbstkondensation der Salicylsäure durch extreme Überhitzung."
            ))
            warnings.append(f"Kritische Überhitzung ({p.temperature_c:.1f} °C > 85 °C): Zersetzung und Verharzung.")
            color = (0.45, 0.28, 0.12)

        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(5.0, min(99.0, (1.0 - loss * 0.85) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.15 and unreacted < 0.2

        return SideReactionReport(
            is_successful=is_success, purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3), unreacted_fraction=round(unreacted, 3),
            impurities=impurities, warnings=warnings, color_discoloration_rgb=color
        )

    def _evaluate_paracetamol(self, p: ReactionConditionParameters) -> SideReactionReport:
        impurities = []
        warnings = []
        color = (0.94, 0.92, 0.88)
        unreacted = 0.0
        tarring = 0.0

        if p.temperature_c > 80.0:
            ox_fraction = min(0.35, (p.temperature_c - 80.0) * 0.015)
            diacetyl_fraction = min(0.20, (p.temperature_c - 80.0) * 0.008)
            impurities.append(ImpurityProduct(
                name="N-Acetyl-p-benzochinonimin (NAPQI-Derivate)", formula="C8H7NO2",
                mass_fraction=round(ox_fraction, 3), severity=ImpuritySeverity.CRITICAL,
                description="Oxidatives Nebenprodukt. Stark verfärbend und zelltoxisch."
            ))
            impurities.append(ImpurityProduct(
                name="N,O-Diacetyl-4-aminophenol", formula="C10H11NO3",
                mass_fraction=round(diacetyl_fraction, 3), severity=ImpuritySeverity.MODERATE,
                description="Zweifache Acylierung an Hydroxyl- und Aminogruppe."
            ))
            warnings.append("Thermische Überhitzung begünstigt chinoiden Abbau und doppelte Acylierung.")
            color = (0.35, 0.18, 0.42)
            tarring = min(0.5, (p.temperature_c - 80.0) * 0.01)

        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(8.0, min(99.0, (1.0 - loss * 0.8) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.1

        return SideReactionReport(
            is_successful=is_success, purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3), unreacted_fraction=round(unreacted, 3),
            impurities=impurities, warnings=warnings, color_discoloration_rgb=color
        )

    def _evaluate_acetanilide(self, p: ReactionConditionParameters) -> SideReactionReport:
        impurities = []
        warnings = []
        color = (0.97, 0.97, 0.99)
        unreacted = 0.0
        tarring = 0.0

        if p.temperature_c < 45.0:
            unreacted = min(0.65, 0.20 + (45.0 - p.temperature_c) * 0.015)
            warnings.append("Niedrige Temperatur: Unvollständige Acetylierung, unreagiertes Anilin verbleibt.")
            impurities.append(ImpurityProduct(
                name="Unreagiertes Anilin", formula="C6H7N", mass_fraction=round(unreacted, 3),
                severity=ImpuritySeverity.MODERATE,
                description="Flüssiges aromatisches Amin mindert Kristallinität."
            ))

        if p.temperature_c > 105.0:
            ox_delta = p.temperature_c - 105.0
            tarring = min(0.60, 0.12 + ox_delta * 0.018)
            azo_fraction = min(0.30, 0.05 + ox_delta * 0.01)
            impurities.append(ImpurityProduct(
                name="Azobenzol & dunkelbraune Oxidationsharze", formula="C12H10N2",
                mass_fraction=round(azo_fraction, 3), severity=ImpuritySeverity.CRITICAL,
                description="Thermisch-oxidative Dimerisierung des Anilins."
            ))
            warnings.append(f"Thermische Überhitzung ({p.temperature_c:.1f}°C): Oxidation zu Azobenzol und Verharzung.")
            color = (0.42, 0.22, 0.08)

        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(5.0, min(99.0, (1.0 - loss * 0.8) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.12 and unreacted < 0.25

        return SideReactionReport(
            is_successful=is_success, purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3), unreacted_fraction=round(unreacted, 3),
            impurities=impurities, warnings=warnings, color_discoloration_rgb=color
        )

    def _evaluate_generic(self, p: ReactionConditionParameters) -> SideReactionReport:
        return SideReactionReport(
            is_successful=True, purity_percentage=96.0,
            tarring_extent=0.0, unreacted_fraction=0.04,
            impurities=[], warnings=[], color_discoloration_rgb=(1.0, 1.0, 1.0)
        )


# =============================================================================
# IPC SERVER (Python Core)
# =============================================================================

class IPCCommand(str, Enum):
    HANDSHAKE = "HANDSHAKE"
    MIX_REAGENTS = "MIX_REAGENTS"
    STEP_SIMULATION = "STEP_SIMULATION"
    CALCULATE_THERMODYNAMICS = "CALCULATE_THERMODYNAMICS"
    RDKIT_CONFORMER = "RDKIT_CONFORMER"

class IPCServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.engine = CanteraThermodynamicsEngine()
        self.side_analyzer = SideReactionAnalyzer()
        self.vessels: Dict[str, Dict] = {}
        self.running = False
        self.server_socket: Optional[socket.socket] = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[IPC Server] Listening on {self.host}:{self.port}")

        while self.running:
            try:
                client, addr = self.server_socket.accept()
                print(f"[IPC Server] Client connected: {addr}")
                thread = threading.Thread(target=self._handle_client, args=(client,))
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"[IPC Server] Error: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def _handle_client(self, client: socket.socket):
        buffer = ""
        try:
            while self.running:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        request = json.loads(line)
                        response = self._process_request(request)
                        if response:
                            client.send((json.dumps(response) + "\n").encode('utf-8'))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"[IPC Server] Client error: {e}")
        finally:
            client.close()

    def _process_request(self, request: Dict) -> Optional[Dict]:
        command = request.get("command", "")
        payload = request.get("payload", {})
        req_id = request.get("request_id", "")

        try:
            if command == IPCCommand.HANDSHAKE:
                return {"request_id": req_id, "status": "SUCCESS", "data": {"server": "chemlab_core", "version": "1.0"}}

            elif command == IPCCommand.MIX_REAGENTS:
                return self._handle_mix_reagents(payload, req_id)

            elif command == IPCCommand.STEP_SIMULATION:
                return self._handle_step_simulation(payload, req_id)

            elif command == IPCCommand.CALCULATE_THERMODYNAMICS:
                return self._handle_thermodynamics(payload, req_id)

            elif command == IPCCommand.RDKIT_CONFORMER:
                return self._handle_rdkit(payload, req_id)

        except Exception as e:
            return {"request_id": req_id, "status": "ERROR", "error": str(e)}

        return {"request_id": req_id, "status": "ERROR", "error": f"Unknown command: {command}"}

    def _handle_mix_reagents(self, payload: Dict, req_id: str) -> Dict:
        vessel_id = payload.get("vessel_id", "")
        reagents = payload.get("reagents", [])
        catalyst = payload.get("catalyst", "")
        temperature_c = payload.get("temperature_c", 22.0)
        addition_order_correct = payload.get("addition_order_correct", True)
        in_fume_hood = payload.get("in_fume_hood", True)

        # Create or get vessel
        if vessel_id not in self.vessels:
            self.vessels[vessel_id] = {
                "volume_ml": 0.0, "temperature_c": temperature_c, "ph": 7.0,
                "species_moles": {}, "species_concentrations": {},
                "color_rgba": [1.0, 1.0, 1.0, 1.0], "turbidity": 0.0,
                "bubble_rate": 0.0, "foam_volume_ml": 0.0,
                "indicator_present": False, "indicator_type": "phenolphthalein",
                "pressure_kpa": 101.325, "headspace_volume_ml": 50.0,
                "is_stirring": False, "stir_rate_rpm": 0.0,
                "last_reaction_type": "NONE", "reaction_progress": 0.0,
                "safety_flags": []
            }

        vessel = self.vessels[vessel_id]

        # Add reagents to vessel
        total_moles = 0.0
        for reagent in reagents:
            species_id = reagent.get("id", "")
            moles = reagent.get("moles", 0.0)
            if species_id in THERMO_DB and moles > 0:
                vessel["species_moles"][species_id] = vessel["species_moles"].get(species_id, 0.0) + moles
                total_moles += moles

        # Estimate volume if not set
        if vessel["volume_ml"] <= 0.0 and total_moles > 0:
            # Rough estimate from first reagent
            first_reagent = reagents[0] if reagents else None
            if first_reagent and first_reagent.get("id") in THERMO_DB:
                sp = THERMO_DB[first_reagent["id"]]
                mass_g = total_moles * sp.molecular_weight_g_mol
                vessel["volume_ml"] = mass_g / sp.density_g_cm3

        # Recalculate concentrations
        self._recalculate_concentrations(vessel)
        vessel["temperature_c"] = temperature_c
        vessel["ph"] = self._calculate_ph(vessel)

        # Execute reactions
        reaction_result = self._execute_reactions(vessel)

        # Update indicator
        if vessel["indicator_present"]:
            vessel["color_rgba"] = self._phenolphthalein_color(vessel["ph"])

        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "data": {
                "vessel_id": vessel_id,
                "reaction_name": reaction_result.get("reaction_name", ""),
                "conversion_ratio": reaction_result.get("conversion_ratio", 0.0),
                "temperature_c": vessel["temperature_c"],
                "is_exothermic": reaction_result.get("is_exothermic", False),
                "delta_h_kj_mol": reaction_result.get("heat_released_kj", 0.0),
                "color_rgba": vessel["color_rgba"],
                "turbidity": vessel["turbidity"],
                "precipitate_formed": reaction_result.get("precipitate_formed", False),
                "precipitate_name": reaction_result.get("precipitate_name", ""),
                "bubbles_per_second": vessel["bubble_rate"],
                "side_products": reaction_result.get("side_products", []),
                "safety_warnings": vessel["safety_flags"]
            }
        }

    def _handle_step_simulation(self, payload: Dict, req_id: str) -> Dict:
        vessel_id = payload.get("vessel_id", "")
        dt = payload.get("dt", 1.0)

        if vessel_id not in self.vessels:
            return {"request_id": req_id, "status": "ERROR", "error": "Vessel not found"}

        vessel = self.vessels[vessel_id]
        old_temp = vessel["temperature_c"]
        old_ph = vessel["ph"]

        # Thermal relaxation
        ambient_temp = 22.0
        cooling_time_constant = 30.0
        cooling_rate = (ambient_temp - vessel["temperature_c"]) / cooling_time_constant
        vessel["temperature_c"] += cooling_rate * dt

        # Stirring enhancement
        if vessel["is_stirring"]:
            stir_factor = 1.0 + (vessel["stir_rate_rpm"] / 1000.0) * 0.5
            cooling_rate *= stir_factor

        # Kinetic reactions
        reaction_result = self._execute_reaction_kinetics(vessel, dt)

        # Oscillating reactions
        if self._has_oscillator_conditions(vessel):
            osc_result = self._step_oscillator(vessel, dt)
            if osc_result.get("phase_changed", False):
                pass  # Handle phase change

        # Update pH
        vessel["ph"] = self._calculate_ph(vessel)

        # Indicator
        if vessel["indicator_present"]:
            vessel["color_rgba"] = self._phenolphthalein_color(vessel["ph"])

        # Precipitation check
        precip_result = self._check_precipitation(vessel)
        if precip_result.get("precipitated", False):
            pass

        # Safety checks
        self._check_safety_limits(vessel)

        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "vessel": self._vessel_to_dict(vessel),
            "reactions": [reaction_result] if reaction_result.get("reaction_occurred") else [],
            "temperature_change": vessel["temperature_c"] - old_temp,
            "ph_change": vessel["ph"] - old_ph
        }

    def _handle_thermodynamics(self, payload: Dict, req_id: str) -> Dict:
        reactants = payload.get("reactants", {})
        products = payload.get("products", {})
        temperature_c = payload.get("temperature_c", 25.0)

        result = self.engine.calculate_reaction_thermodynamics(
            reactants, products, temperature_c
        )

        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "data": {
                "equation": result.equation,
                "temperature_k": result.temperature_k,
                "delta_h_kj_mol": result.delta_h_kj_mol,
                "delta_s_j_mol_k": result.delta_s_j_mol_k,
                "delta_g_kj_mol": result.delta_g_kj_mol,
                "is_exothermic": result.is_exothermic,
                "is_spontaneous": result.is_spontaneous,
                "equilibrium_constant_k_eq": result.equilibrium_constant_k_eq,
                "rate_constant_k": result.rate_constant_k,
                "adiabatic_temperature_rise_c": result.adiabatic_temperature_rise_c,
                "half_life_seconds": result.half_life_seconds,
                "warnings": result.warnings
            }
        }

    def _handle_rdkit(self, payload: Dict, req_id: str) -> Dict:
        # Placeholder for RDKit conformer generation
        smiles = payload.get("smiles", "")
        compound_name = payload.get("compound_name", "")

        sp_id = compound_name if compound_name else smiles
        if sp_id in THERMO_DB:
            sp = THERMO_DB[sp_id]
            return {
                "request_id": req_id,
                "status": "SUCCESS",
                "data": {
                    "smiles": smiles,
                    "compound_name": compound_name,
                    "formula": sp.formula,
                    "molecular_weight_g_mol": sp.molecular_weight_g_mol,
                    "cas_number": sp.cas_number,
                    "ghs_pictograms": sp.ghs_pictograms
                }
            }

        return {"request_id": req_id, "status": "ERROR", "error": "Species not found"}

    # =============================================================================
    # HELPER METHODS (same as Godot bridge)
    # =============================================================================

    def _recalculate_concentrations(self, vessel: Dict) -> None:
        vessel["species_concentrations"].clear()
        if vessel["volume_ml"] <= 0.0:
            return
        vol_l = vessel["volume_ml"] / 1000.0
        for species_id in vessel["species_moles"]:
            vessel["species_concentrations"][species_id] = vessel["species_moles"][species_id] / vol_l

    def _calculate_ph(self, vessel: Dict) -> float:
        strong_acid_moles = 0.0
        strong_base_moles = 0.0
        weak_acids = {}
        weak_bases = {}

        for species_id in vessel["species_moles"]:
            moles = vessel["species_moles"][species_id]
            if moles <= 0.0:
                continue

            if species_id not in THERMO_DB:
                continue
            sp = THERMO_DB[species_id]

            if sp.is_acid:
                if sp.acid_pka < 0:
                    strong_acid_moles += moles
                else:
                    weak_acids[species_id] = {"moles": moles, "pka": sp.acid_pka}
            elif sp.is_base:
                if species_id in ["NaOH_aq", "KOH_aq"] or sp.acid_pka > 14:
                    strong_base_moles += moles
                else:
                    weak_bases[species_id] = {"moles": moles, "pka": sp.acid_pka}

        net_h = strong_acid_moles - strong_base_moles
        vol_l = max(vessel["volume_ml"] / 1000.0, 0.001)

        if net_h > 0:
            h_conc = net_h / vol_l
            return max(0.0, min(14.0, -math.log10(max(h_conc, 1e-14))))
        elif net_h < 0:
            oh_conc = -net_h / vol_l
            poh = -math.log10(max(oh_conc, 1e-14))
            return max(0.0, min(14.0, 14.0 - poh))
        else:
            if weak_acids and weak_bases:
                wa_id = list(weak_acids.keys())[0]
                wb_id = list(weak_bases.keys())[0]
                wa = weak_acids[wa_id]
                wb = weak_bases[wb_id]
                conc_a = wa["moles"] / vol_l
                conc_b = wb["moles"] / vol_l
                return wa["pka"] + math.log10(max(1e-4, conc_b / max(conc_a, 1e-10)))
            elif weak_acids:
                wa = list(weak_acids.values())[0]
                conc = wa["moles"] / vol_l
                if conc > 0:
                    h = math.sqrt(pow(10.0, -wa["pka"]) * conc)
                    return max(0.0, min(14.0, -math.log10(max(h, 1e-14))))
            elif weak_bases:
                wb = list(weak_bases.values())[0]
                conc = wb["moles"] / vol_l
                if conc > 0:
                    kb = pow(10.0, -(14.0 - wb["pka"]))
                    oh = math.sqrt(kb * conc)
                    poh = -math.log10(max(oh, 1e-14))
                    return max(0.0, min(14.0, 14.0 - poh))
        return 7.0

    def _phenolphthalein_color(self, ph: float) -> List[float]:
        if ph < 8.2:
            return [1.0, 1.0, 1.0, 0.0]
        elif ph < 9.0:
            alpha = (ph - 8.2) / 0.8 * 0.6
            return [1.0, 1.0 - alpha * 0.3, 1.0 - alpha * 0.2, alpha]
        elif ph < 10.0:
            alpha = 0.6 + (ph - 9.0) / 1.0 * 0.4
            return [1.0, 0.72 - (alpha - 0.6) * 0.5, 0.82 - (alpha - 0.6) * 0.3, alpha]
        else:
            return [0.92, 0.08, 0.55, 1.0]

    def _execute_reactions(self, vessel: Dict) -> Dict:
        result = {
            "reaction_occurred": False,
            "reaction_name": "",
            "conversion_ratio": 0.0,
            "heat_released_kj": 0.0,
            "temperature_rise_c": 0.0,
            "products_formed": {},
            "consumed": {},
            "is_exothermic": False,
            "precipitate_formed": False,
            "precipitate_name": "",
            "side_products": [],
            "safety_flags": []
        }

        has_strong_acid = False
        has_strong_base = False
        acid_moles = 0.0
        base_moles = 0.0
        acid_id = ""
        base_id = ""

        for species_id in vessel["species_moles"]:
            moles = vessel["species_moles"][species_id]
            if moles <= 0.0 or species_id not in THERMO_DB:
                continue
            sp = THERMO_DB[species_id]
            if sp.is_acid and sp.acid_pka < 0:
                has_strong_acid = True
                acid_moles += moles
                acid_id = species_id
            elif species_id in ["NaOH_aq", "KOH_aq"]:
                has_strong_base = True
                base_moles += moles
                base_id = species_id

        if has_strong_acid and has_strong_base:
            reacted = min(acid_moles, base_moles)
            if reacted > 0:
                vessel["species_moles"][acid_id] -= reacted
                vessel["species_moles"][base_id] -= reacted

                vessel["species_moles"]["H2O"] = vessel["species_moles"].get("H2O", 0.0) + reacted
                salt_id = "NaCl_aq"
                if acid_id == "HCl_aq" and base_id == "NaOH_aq":
                    salt_id = "NaCl_aq"
                vessel["species_moles"][salt_id] = vessel["species_moles"].get(salt_id, 0.0) + reacted

                result["reaction_occurred"] = True
                result["reaction_name"] = "acid_base_neutralization"
                result["conversion_ratio"] = reacted / max(acid_moles, base_moles)
                result["consumed"][acid_id] = reacted
                result["consumed"][base_id] = reacted
                result["products_formed"][salt_id] = reacted
                result["products_formed"]["H2O"] = reacted
                result["is_exothermic"] = True

                heat_kj = reacted * 57.1  # kJ/mol for HCl + NaOH
                result["heat_released_kj"] = heat_kj

                total_mass_g = vessel["volume_ml"] * 1.0
                delta_t = (heat_kj * 1000.0) / (total_mass_g * 4.184)
                vessel["temperature_c"] += delta_t
                result["temperature_rise_c"] = delta_t

                if vessel["temperature_c"] > 80.0:
                    vessel["safety_flags"].append("THERMAL_HAZARD")
                if vessel["temperature_c"] > 95.0:
                    vessel["safety_flags"].append("BOILING")

        self._recalculate_concentrations(vessel)
        return result

    def _execute_reaction_kinetics(self, vessel: Dict, dt: float) -> Dict:
        result = {"reaction_occurred": False}

        # H2O2 decomposition catalyzed by KI
        h2o2_conc = vessel["species_concentrations"].get("H2O2_aq", 0)
        ki_conc = vessel["species_concentrations"].get("KI_aq", 0)

        if h2o2_conc > 0 and ki_conc > 0:
            temp_k = vessel["temperature_c"] + 273.15
            ea = 56.0  # kJ/mol
            A = 1e7
            k = A * math.exp(-ea * 1000.0 / (R_GAS * temp_k))
            rate = k * h2o2_conc * ki_conc
            reacted_mol_l = rate * dt
            reacted_moles = reacted_mol_l * (vessel["volume_ml"] / 1000.0)

            if reacted_moles > 0:
                h2o2_moles = vessel["species_moles"].get("H2O2_aq", 0)
                reacted_moles = min(reacted_moles, h2o2_moles)

                vessel["species_moles"]["H2O2_aq"] -= reacted_moles
                vessel["species_moles"]["H2O"] = vessel["species_moles"].get("H2O", 0.0) + reacted_moles
                vessel["species_moles"]["O2_gas"] = vessel["species_moles"].get("O2_gas", 0.0) + reacted_moles / 2.0
                vessel["bubble_rate"] = min(1.0, vessel["bubble_rate"] + reacted_moles * 10.0)

                heat_kj = reacted_moles * 98.0
                total_mass = vessel["volume_ml"] * 1.0
                delta_t = heat_kj * 1000.0 / (total_mass * 4.184)
                vessel["temperature_c"] += delta_t

                result["reaction_occurred"] = True
                result["reaction_name"] = "catalytic_decomposition"
                result["reacted_moles"] = reacted_moles
                result["heat_kj"] = heat_kj
                result["temperature_rise"] = delta_t

        self._recalculate_concentrations(vessel)
        return result

    def _has_oscillator_conditions(self, vessel: Dict) -> bool:
        return (vessel["species_concentrations"].get("H2O2_aq", 0) > 0 and
                vessel["species_concentrations"].get("KI_aq", 0) > 0 and
                vessel["species_concentrations"].get("malonic_acid", 0) > 0 and
                vessel["species_concentrations"].get("MnSO4_aq", 0) > 0)

    def _step_oscillator(self, vessel: Dict, dt: float) -> Dict:
        result = {"phase_changed": False}
        ma_conc = vessel["species_concentrations"].get("malonic_acid", 0)
        if ma_conc <= 0:
            return result

        base_period = 8.0
        period = base_period / max(ma_conc, 0.01)
        phase_duration = period / 3.0
        vessel["reaction_progress"] = vessel.get("reaction_progress", 0.0) + dt
        cycle_pos = vessel["reaction_progress"] % period

        old_phase = vessel.get("last_reaction_type", 0)
        if cycle_pos < phase_duration:
            vessel["last_reaction_type"] = 1
            vessel["color_rgba"] = [0.95, 0.98, 1.0, 1.0]
        elif cycle_pos < 2 * phase_duration:
            vessel["last_reaction_type"] = 2
            vessel["color_rgba"] = [0.96, 0.72, 0.24, 1.0]
        else:
            vessel["last_reaction_type"] = 3
            vessel["color_rgba"] = [0.14, 0.22, 0.64, 1.0]

        if vessel["last_reaction_type"] != old_phase:
            result["phase_changed"] = True
            result["phase"] = vessel["last_reaction_type"]
            result["color"] = vessel["color_rgba"]

        return result

    def _check_precipitation(self, vessel: Dict) -> Dict:
        result = {"precipitated": False}

        ksp_table = {
            "AgCl": {"ions": ["Ag+", "Cl-"], "ksp": 1.77e-10, "name": "Silver Chloride"},
            "BaSO4": {"ions": ["Ba2+", "SO4^2-"], "ksp": 1.1e-10, "name": "Barium Sulfate"},
            "PbCl2": {"ions": ["Pb2+", "Cl-"], "ksp": 1.7e-5, "name": "Lead(II) Chloride"},
            "CaCO3": {"ions": ["Ca2+", "CO3^2-"], "ksp": 3.3e-9, "name": "Calcium Carbonate"},
            "Fe(OH)3": {"ions": ["Fe3+", "OH-"], "ksp": 2.8e-39, "name": "Iron(III) Hydroxide"},
            "Cu(OH)2": {"ions": ["Cu2+", "OH-"], "ksp": 2.2e-20, "name": "Copper(II) Hydroxide"},
        }

        for precip_name in ksp_table:
            data = ksp_table[precip_name]
            ion_a = data["ions"][0]
            ion_b = data["ions"][1]
            conc_a = vessel["species_concentrations"].get(ion_a, 0.0)
            conc_b = vessel["species_concentrations"].get(ion_b, 0.0)

            if conc_a > 0 and conc_b > 0:
                ip = conc_a * conc_b
                if precip_name == "PbCl2":
                    ip = conc_a * conc_b * conc_b
                elif precip_name == "Fe(OH)3":
                    ip = conc_a * conc_b * conc_b * conc_b
                elif precip_name == "Cu(OH)2":
                    ip = conc_a * conc_b * conc_b

                if ip > data["ksp"]:
                    max_precip = min(conc_a, conc_b) * (vessel["volume_ml"] / 1000.0)
                    if precip_name == "PbCl2":
                        max_precip = min(conc_a, conc_b / 2.0) * (vessel["volume_ml"] / 1000.0)
                    elif precip_name == "Fe(OH)3":
                        max_precip = min(conc_a, conc_b / 3.0) * (vessel["volume_ml"] / 1000.0)
                    elif precip_name == "Cu(OH)2":
                        max_precip = min(conc_a, conc_b / 2.0) * (vessel["volume_ml"] / 1000.0)

                    vessel["species_moles"][ion_a] = max(0, vessel["species_moles"].get(ion_a, 0) - max_precip)
                    vessel["species_moles"][ion_b] = max(0, vessel["species_moles"].get(ion_b, 0) - max_precip * (2 if precip_name in ["PbCl2", "Cu(OH)2"] else (3 if precip_name == "Fe(OH)3" else 1)))

                    precip_id = precip_name.lower() + "_s"
                    vessel["species_moles"][precip_id] = vessel["species_moles"].get(precip_id, 0.0) + max_precip
                    vessel["turbidity"] = min(1.0, vessel["turbidity"] + 0.1)

                    result["precipitated"] = True
                    result["precipitate"] = data["name"]
                    result["amount_mol"] = max_precip
                    result["ksp"] = data["ksp"]
                    result["ionic_product"] = ip

                    self._recalculate_concentrations(vessel)
                    break

        return result

    def _check_safety_limits(self, vessel: Dict) -> None:
        if vessel["temperature_c"] > 100.0:
            vessel["safety_flags"].append("BOILING")
        elif vessel["temperature_c"] > 80.0:
            vessel["safety_flags"].append("HIGH_TEMP_WARNING")

        gas_moles = 0.0
        for species_id in vessel["species_moles"]:
            if species_id in THERMO_DB:
                sp = THERMO_DB[species_id]
                if sp.boiling_point_c < vessel["temperature_c"] or sp.is_volatile:
                    gas_moles += vessel["species_moles"][species_id]

        if gas_moles > 0 and vessel["headspace_volume_ml"] > 0:
            temp_k = vessel["temperature_c"] + 273.15
            vol_l = vessel["headspace_volume_ml"] / 1000.0
            pressure_pa = gas_moles * R_GAS * temp_k / vol_l
            pressure_kpa = pressure_pa / 1000.0
            vessel["pressure_kpa"] = 101.325 + pressure_kpa
            if vessel["pressure_kpa"] > 200.0:
                vessel["safety_flags"].append("OVERPRESSURE")

    def _vessel_to_dict(self, vessel: Dict) -> Dict:
        return {
            "volume_ml": vessel["volume_ml"],
            "temperature_c": vessel["temperature_c"],
            "ph": vessel["ph"],
            "species_moles": vessel["species_moles"],
            "species_concentrations": vessel["species_concentrations"],
            "color_rgba": vessel["color_rgba"],
            "turbidity": vessel["turbidity"],
            "bubble_rate": vessel["bubble_rate"],
            "foam_volume_ml": vessel["foam_volume_ml"],
            "indicator_present": vessel["indicator_present"],
            "indicator_type": vessel["indicator_type"],
            "pressure_kpa": vessel["pressure_kpa"],
            "headspace_volume_ml": vessel["headspace_volume_ml"],
            "is_stirring": vessel["is_stirring"],
            "stir_rate_rpm": vessel["stir_rate_rpm"],
            "last_reaction_type": vessel.get("last_reaction_type", "NONE"),
            "reaction_progress": vessel.get("reaction_progress", 0.0),
            "safety_flags": vessel["safety_flags"]
        }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("Starting ChemLab Core IPC Server...")
    server = IPCServer("127.0.0.1", 8765)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()