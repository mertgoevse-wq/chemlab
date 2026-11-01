"""
ChemLab Consequence & Thermodynamic Engine — Free Simulation Mode
Realistic consequence matrices for arbitrary chemical combinations:
- Exothermic neutralization / heat release
- Endothermic cooling / dissolution
- Precipitate formation (solubility equilibria)
- Gas evolution (effervescence, vapor generation)
- Safe explosion containment in the fume hood vs uncontained blast on open bench
- Chemical oscillators (Briggs-Rauscher, Belousov-Zhabotinsky)
"""

from dataclasses import dataclass, field
from enum import Enum


class VesselEnvironment(Enum):
    MAIN_BENCH = "main_bench"
    FUME_HOOD = "fume_hood"
    GLOVE_BOX = "glove_box"
    HEATING_MANTLE = "heating_mantle"
    ICE_BATH = "ice_bath"


class ConsequenceType(Enum):
    NO_VISIBLE_REACTION = "no_visible_reaction"
    EXOTHERMIC_NEUTRALIZATION = "exothermic_neutralization"
    ENDOTHERMIC_DISSOLUTION = "endothermic_dissolution"
    PRECIPITATION = "precipitation"
    GAS_EVOLUTION = "gas_evolution"
    EXPLOSION = "explosion"
    OSCILLATING_REACTION = "oscillating_reaction"
    REDOX_COLOR_SHIFT = "redox_color_shift"
    THERMAL_DECOMPOSITION = "thermal_decomposition"


class ReactionEffect(Enum):
    HEAT_RELEASE = "heat_release"
    COOLING = "cooling"
    PRECIPITATE = "precipitate"
    EFFERVESCENCE = "effervescence"
    FLAME = "flame"
    VAPOR_CLOUD = "vapor_cloud"
    COLOR_CHANGE = "color_change"
    ODOR_RELEASE = "odor_release"
    SHOCKWAVE = "shockwave"


@dataclass
class OscillationCycle:
    period_seconds: float
    color_sequence: list[tuple[float, float, float, float]]
    phase_names: list[str]


@dataclass
class ConsequenceResult:
    consequence: ConsequenceType
    initial_temp_c: float
    final_temp_c: float
    temp_delta_c: float
    effects: list[ReactionEffect] = field(default_factory=list)
    precipitate_name: str | None = None
    precipitate_color: tuple[float, float, float, float] | None = None
    precipitate_mass_g: float = 0.0
    gas_released_formula: str | None = None
    gas_volume_liters: float = 0.0
    is_contained: bool = True
    safety_report: str = "Conditions nominal."
    oscillation_cycle: OscillationCycle | None = None
    mixture_color_rgba: tuple[float, float, float, float] = (0.95, 0.98, 1.0, 1.0)
    details: str = ""


class ConsequenceEngine:
    """Evaluates arbitrary reagent mixtures in specific laboratory environments."""

    def mix(
        self,
        vessel_env: VesselEnvironment,
        reagent_ids: list[str],
        volumes_ml: list[float] | None = None,  # noqa: ARG002
        masses_or_volumes: list[float] | None = None,  # noqa: ARG002
        initial_temp_c: float = 20.0,
    ) -> ConsequenceResult:
        reg_set = set(reagent_ids)

        checks = (
            self._check_oscillation(reg_set, initial_temp_c),
            self._check_explosion(reg_set, vessel_env, initial_temp_c),
            self._check_neutralization(reg_set, initial_temp_c),
            self._check_endothermic(reg_set, initial_temp_c),
            self._check_precipitation(reg_set, initial_temp_c),
            self._check_gas_evolution(reg_set, initial_temp_c),
        )
        for res in checks:
            if res is not None:
                return res

        return ConsequenceResult(
            consequence=ConsequenceType.NO_VISIBLE_REACTION,
            initial_temp_c=initial_temp_c,
            final_temp_c=initial_temp_c,
            temp_delta_c=0.0,
            effects=[],
            is_contained=True,
            safety_report="Reagents miscible or in stable suspension.",
            mixture_color_rgba=(0.95, 0.98, 1.0, 0.9),
            details="Homogeneous solution without observable phase shift or enthalpy anomaly.",
        )

    def _check_oscillation(
        self, reg_set: set[str], initial_temp_c: float
    ) -> ConsequenceResult | None:
        br_reagents = {
            "hydrogen_peroxide_30",
            "potassium_iodate",
            "malonic_acid",
            "manganese_sulfate",
            "starch_indicator",
        }
        if not br_reagents.issubset(reg_set):
            return None

        cycle = OscillationCycle(
            period_seconds=2.5,
            color_sequence=[
                (0.95, 0.98, 1.0, 0.9),
                (0.85, 0.55, 0.10, 0.95),
                (0.08, 0.05, 0.45, 0.98),
            ],
            phase_names=["Clear Initial", "Amber Triiodide", "Deep Blue Starch-Iodine Complex"],
        )
        return ConsequenceResult(
            consequence=ConsequenceType.OSCILLATING_REACTION,
            initial_temp_c=initial_temp_c,
            final_temp_c=initial_temp_c + 3.2,
            temp_delta_c=3.2,
            effects=[
                ReactionEffect.COLOR_CHANGE,
                ReactionEffect.HEAT_RELEASE,
                ReactionEffect.EFFERVESCENCE,
            ],
            gas_released_formula="O2/CO2",
            gas_volume_liters=0.15,
            is_contained=True,
            safety_report="Oscillating kinetic system stabilized. Cyclic redox potential in equilibrium.",
            oscillation_cycle=cycle,
            mixture_color_rgba=(0.08, 0.05, 0.45, 0.98),
            details="Briggs-Rauscher iodine clock oscillator active.",
        )

    def _check_explosion(
        self, reg_set: set[str], vessel_env: VesselEnvironment, initial_temp_c: float
    ) -> ConsequenceResult | None:
        is_explosive = (
            "potassium_permanganate" in reg_set and "sulfuric_acid_conc" in reg_set
        ) or (
            "perchloric_acid_70" in reg_set
            and any("solvent" in r or "ethanol" in r for r in reg_set)
        )
        if not is_explosive:
            return None

        contained = vessel_env == VesselEnvironment.FUME_HOOD
        report = (
            "Fume hood blast shield contained explosive thermal decomposition. "
            "Toxic gases scrubbed by exhaust ventilation."
            if contained
            else "Uncontained blast! Shrapnel dispersed across open laboratory bench. Emergency evacuation required."
        )

        return ConsequenceResult(
            consequence=ConsequenceType.EXPLOSION,
            initial_temp_c=initial_temp_c,
            final_temp_c=initial_temp_c + 320.0,
            temp_delta_c=320.0,
            effects=[
                ReactionEffect.SHOCKWAVE,
                ReactionEffect.FLAME,
                ReactionEffect.VAPOR_CLOUD,
                ReactionEffect.HEAT_RELEASE,
            ],
            gas_released_formula="O2/O3/MnO2-aerosol",
            gas_volume_liters=8.5,
            is_contained=contained,
            safety_report=report,
            mixture_color_rgba=(0.1, 0.05, 0.05, 1.0),
            details="Vigorous exothermic oxidation formed unstable manganese heptoxide / violent thermal detonation.",
        )

    def _check_neutralization(
        self, reg_set: set[str], initial_temp_c: float
    ) -> ConsequenceResult | None:
        acids = {
            "hydrochloric_acid_37",
            "sulfuric_acid_conc",
            "nitric_acid_65",
            "sulfuric_acid_dilute",
        }
        bases = {
            "sodium_hydroxide_sol",
            "potassium_hydroxide_pellets",
            "ammonia_solution_25",
            "calcium_hydroxide",
        }
        if not (reg_set.intersection(acids) and reg_set.intersection(bases)):
            return None

        delta_t = 18.5 if "sulfuric_acid_conc" in reg_set else 14.2
        return ConsequenceResult(
            consequence=ConsequenceType.EXOTHERMIC_NEUTRALIZATION,
            initial_temp_c=initial_temp_c,
            final_temp_c=initial_temp_c + delta_t,
            temp_delta_c=delta_t,
            effects=[ReactionEffect.HEAT_RELEASE],
            is_contained=True,
            safety_report="Neutralization completed safely with release of reaction enthalpy.",
            mixture_color_rgba=(0.95, 0.98, 1.0, 0.9),
            details=f"Acid-base neutralization produced neutral salt solution with enthalpy release of delta_T = +{delta_t:.1f}°C.",
        )

    def _check_endothermic(
        self, reg_set: set[str], initial_temp_c: float
    ) -> ConsequenceResult | None:
        if "ammonium_nitrate" in reg_set and "water_deionized" in reg_set:
            return ConsequenceResult(
                consequence=ConsequenceType.ENDOTHERMIC_DISSOLUTION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c - 12.4,
                temp_delta_c=-12.4,
                effects=[ReactionEffect.COOLING],
                is_contained=True,
                safety_report="Endothermic crystal lattice solvation absorbed thermal energy from solvent.",
                mixture_color_rgba=(0.94, 0.97, 1.0, 0.88),
                details="Rapid endothermic dissolution cooled solution from 22.0°C to 9.6°C.",
            )

        if "barium_hydroxide_octahydrate" in reg_set and "ammonium_thiocyanate" in reg_set:
            return ConsequenceResult(
                consequence=ConsequenceType.ENDOTHERMIC_DISSOLUTION,
                initial_temp_c=initial_temp_c,
                final_temp_c=-4.5,
                temp_delta_c=-24.5,
                effects=[ReactionEffect.COOLING, ReactionEffect.ODOR_RELEASE],
                gas_released_formula="NH3",
                is_contained=True,
                safety_report="Severe endothermic cooling below water freezing point. Ammonia vapor emitted.",
                mixture_color_rgba=(0.9, 0.9, 0.9, 1.0),
                details="Spontaneous solid-solid endothermic reaction froze external water droplet.",
            )
        return None

    def _check_precipitation(
        self, reg_set: set[str], initial_temp_c: float
    ) -> ConsequenceResult | None:
        if ("silver_nitrate_sol" in reg_set or "silver_nitrate" in reg_set) and (
            "sodium_chloride_sol" in reg_set or "hydrochloric_acid_37" in reg_set
        ):
            return ConsequenceResult(
                consequence=ConsequenceType.PRECIPITATION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c + 0.5,
                temp_delta_c=0.5,
                effects=[ReactionEffect.PRECIPITATE, ReactionEffect.COLOR_CHANGE],
                precipitate_name="Silver Chloride (AgCl)",
                precipitate_color=(0.95, 0.95, 0.95, 1.0),
                precipitate_mass_g=1.43,
                is_contained=True,
                safety_report="Dense curdy white silver chloride precipitate settled out of solution.",
                mixture_color_rgba=(0.92, 0.92, 0.94, 0.98),
                details="Ag+ (aq) + Cl- (aq) -> AgCl (s) (Ksp = 1.77e-10).",
            )

        if "lead_nitrate_sol" in reg_set and "potassium_iodide_sol" in reg_set:
            return ConsequenceResult(
                consequence=ConsequenceType.PRECIPITATION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c + 0.3,
                temp_delta_c=0.3,
                effects=[ReactionEffect.PRECIPITATE, ReactionEffect.COLOR_CHANGE],
                precipitate_name="Lead(II) Iodide (PbI2)",
                precipitate_color=(0.95, 0.85, 0.10, 1.0),
                precipitate_mass_g=2.31,
                is_contained=True,
                safety_report="Gleaming golden spangles of lead iodide crystallized out.",
                mixture_color_rgba=(0.95, 0.82, 0.15, 1.0),
                details="Pb2+ (aq) + 2 I- (aq) -> PbI2 (s) ('Golden Rain').",
            )

        if (
            "copper_sulfate_pentahydrate" in reg_set or "copper_ii_chloride_dihydrate" in reg_set
        ) and ("sodium_hydroxide_sol" in reg_set or "potassium_hydroxide_pellets" in reg_set):
            return ConsequenceResult(
                consequence=ConsequenceType.PRECIPITATION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c + 1.8,
                temp_delta_c=1.8,
                effects=[ReactionEffect.PRECIPITATE, ReactionEffect.COLOR_CHANGE],
                precipitate_name="Copper(II) Hydroxide (Cu(OH)2)",
                precipitate_color=(0.10, 0.55, 0.85, 1.0),
                precipitate_mass_g=1.95,
                is_contained=True,
                safety_report="Gelatinous light blue copper hydroxide precipitate formed.",
                mixture_color_rgba=(0.15, 0.60, 0.90, 0.98),
                details="Cu2+ (aq) + 2 OH- (aq) -> Cu(OH)2 (s).",
            )
        return None

    def _check_gas_evolution(
        self, reg_set: set[str], initial_temp_c: float
    ) -> ConsequenceResult | None:
        carbonates = {
            "sodium_bicarbonate",
            "sodium_carbonate_anhydrous",
            "potassium_carbonate",
        }
        acids = {
            "hydrochloric_acid_37",
            "sulfuric_acid_conc",
            "nitric_acid_65",
            "sulfuric_acid_dilute",
        }
        if reg_set.intersection(carbonates) and reg_set.intersection(acids):
            return ConsequenceResult(
                consequence=ConsequenceType.GAS_EVOLUTION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c - 1.2,
                temp_delta_c=-1.2,
                effects=[ReactionEffect.EFFERVESCENCE, ReactionEffect.COOLING],
                gas_released_formula="CO2",
                gas_volume_liters=2.24,
                is_contained=True,
                safety_report="Vigorous effervescence with carbon dioxide gas release.",
                mixture_color_rgba=(0.95, 0.98, 1.0, 0.85),
                details="Acid decomposition of carbonate: H+ + HCO3- -> H2O + CO2 (g).",
            )

        if "zinc_granules" in reg_set and (
            "hydrochloric_acid_37" in reg_set or "sulfuric_acid_dilute" in reg_set
        ):
            return ConsequenceResult(
                consequence=ConsequenceType.GAS_EVOLUTION,
                initial_temp_c=initial_temp_c,
                final_temp_c=initial_temp_c + 8.5,
                temp_delta_c=8.5,
                effects=[ReactionEffect.EFFERVESCENCE, ReactionEffect.HEAT_RELEASE],
                gas_released_formula="H2",
                gas_volume_liters=1.80,
                is_contained=True,
                safety_report="Steady stream of highly flammable hydrogen gas evolved.",
                mixture_color_rgba=(0.95, 0.98, 1.0, 0.9),
                details="Zn (s) + 2 H+ (aq) -> Zn2+ (aq) + H2 (g).",
            )
        return None
