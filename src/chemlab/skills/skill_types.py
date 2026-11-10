"""
Skill type definitions for the ChemLab Runescape-style progression system.

Defines the five scientific disciplines (SAFETY, ANALYTICAL, THERMODYNAMICS,
PREPARATIVE, COMPUTATIONAL) matching the disciplines documented in
docs/STORY_AND_QUESTS.md §2, plus helper data for milestone unlocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from chemlab.compat import StrEnum, UTC


class SkillType(StrEnum):
    """The five scientific disciplines of ChemLab skill progression."""

    SAFETY = "safety"
    ANALYTICAL = "analytical"
    THERMODYNAMICS = "thermodynamics"
    PREPARATIVE = "preparative"
    COMPUTATIONAL = "computational"


@dataclass(frozen=True)
class SkillDefinition:
    """Static metadata for a single skill discipline."""

    skill_type: SkillType
    display_name: str
    short_name: str
    description: str
    # The German-localized rank titles used in-story (Trainee → Grandmaster).
    rank_titles: tuple[str, ...] = field(default_factory=tuple)
    # Unlockable apparatus per level, e.g. {5: ["Face Shield"], 25: ["Glovebox"]}.
    apparatus_unlocks: dict[int, list[str]] = field(default_factory=dict)
    # Unlockable reagents per level.
    reagent_unlocks: dict[int, list[str]] = field(default_factory=dict)
    # Unlockable abilities per level (free-form strings consumed by game logic).
    ability_unlocks: dict[int, list[str]] = field(default_factory=dict)


# Rank titles per skill (10 ranks from Trainee to Grandmaster).
_RANKS = (
    "Trainee",
    "Apprentice",
    "Journeyman",
    "Expert",
    "Specialist",
    "Master",
    "Grandmaster",
    "Archmage",
    "Legend",
    "Transcendent",
)


def _rank_titles() -> tuple[str, ...]:
    return _RANKS


ALL_SKILLS: dict[SkillType, SkillDefinition] = {
    SkillType.SAFETY: SkillDefinition(
        skill_type=SkillType.SAFETY,
        display_name="Laboratory Safety",
        short_name="Safety",
        description=(
            "Personal protection, environmental containment, chemical hygiene, "
            "toxicity management, and crisis drills. Governs the player safety "
            "multiplier and unlocks higher hazard reagent classes."
        ),
        rank_titles=_rank_titles(),
        apparatus_unlocks={
            1: ["Lab Coat", "Safety Goggles", "Nitrile Gloves"],
            10: ["Face Shield", "Chemical Apron"],
            25: ["HazMat Suit", "Full-Face Respirator"],
            50: ["Emergency Shower Access", "Spill Containment Kit"],
            75: ["Positive-Pressure HazMat Hood"],
            100: ["Level-A Encapsulating Suit"],
        },
        reagent_unlocks={
            1: ["water", "nacl", "universal_indicator"],
            10: ["hcl", "naoh"],
            25: ["h2so4", "h2o2"],
            50: ["hf_acid", "br2", "cl2"],
            75: ["hcn", "phosgene"],
            100: ["sarin_precursors", "vx_precursors"],  # educational/stoichiometric only
        },
        ability_unlocks={
            5: ["Emergency Eyewash Operation"],
            15: ["Fume Hood Sash Calibration"],
            30: ["Spill Neutralization Protocol"],
            50: ["Pyrophoric Substance Handling"],
            75: ["Cryogenic Liquid Transfer"],
            100: ["HazMat Incident Command"],
        },
    ),
    SkillType.ANALYTICAL: SkillDefinition(
        skill_type=SkillType.ANALYTICAL,
        display_name="Analytical Chemistry",
        short_name="Analytical",
        description=(
            "Quantitative metrology, volumetric precision, calibration curves, "
            "pH stat analysis, and spectroscopy. Reduces meniscus parallax error "
            "and unlocks high-resolution data readouts."
        ),
        rank_titles=_rank_titles(),
        apparatus_unlocks={
            1: ["Analytical Balance", "Class A Volumetric Pipette"],
            15: ["50 mL Precision Buret", "Porcelain Contrast Tile"],
            30: ["UV-Vis Spectrophotometer", "pH Electrode"],
            50: ["HPLC-DAD Stack", "GC-MS Quadrupole"],
            75: ["400 MHz FT-NMR Spectrometer"],
            100: ["High-Resolution Mass Spectrometer"],
        },
        reagent_unlocks={
            1: ["water", "universal_indicator"],
            10: ["phenolphthalein", "bromothymol_blue"],
            25: ["ferroin_indicator", "silver_nitrate"],
            50: ["k_permanganate", "iodine_solution"],
            75: ["nmr_solvent_cdcl3", "gc_derivatizing_agent"],
            100: ["icp_ms_standard", "xrf_reference"],
        },
        ability_unlocks={
            5: ["Meniscus Parallax Compensation"],
            15: ["Dropwise Titration Control"],
            30: ["Endpoint Chromatic Recognition"],
            50: ["Calibration Curve Fitting"],
            75: ["Spectral Deconvolution"],
            100: ["Multi-Element Quantification"],
        },
    ),
    SkillType.THERMODYNAMICS: SkillDefinition(
        skill_type=SkillType.THERMODYNAMICS,
        display_name="Thermodynamics & Kinetics",
        short_name="Thermo",
        description=(
            "Reaction rates, activation energy, Arrhenius relationships, heat "
            "exchange, and non-equilibrium oscillatory dynamics. Unlocks thermal "
            "prediction HUD overlays and kinetic limit-cycle timers."
        ),
        rank_titles=_rank_titles(),
        apparatus_unlocks={
            1: ["Digital Thermocouple", "Ice Bath Basin"],
            15: ["Circulating PID Water Bath", "Magnetic Hotplate"],
            30: ["Jacketed Reaction Vessel", "Peltier Plate"],
            50: ["Differential Scanning Calorimeter", "Flame Photometer"],
            75: ["Adiabatic Calorimeter", "Laser Spectroscopy Station"],
            100: ["Reaction Calorimeter RC1e"],
        },
        reagent_unlocks={
            1: ["water", "ice_matrix"],
            10: ["salicylic_acid", "acetic_anhydride"],
            25: ["malonic_acid", "potassium_iodate"],
            50: ["benzene", "toluene", "diethyl_ether"],
            75: ["liquid_nitrogen", "liquid_helium"],
            100: ["liquid_hydrogen", "liquid_oxygen"],
        },
        ability_unlocks={
            5: ["Water-Bath PID Stabilization"],
            15: ["Thermal Runaway Mitigation"],
            30: ["Arrhenius Rate Prediction"],
            50: ["Non-Linear Oscillator Tuning"],
            75: ["Adiabatic Runaway Modeling"],
            100: ["Supercritical Fluid Control"],
        },
    ),
    SkillType.PREPARATIVE: SkillDefinition(
        skill_type=SkillType.PREPARATIVE,
        display_name="Preparative Synthesis",
        short_name="Synthesis",
        description=(
            "Organic and inorganic synthesis, esterification, reflux assemblies, "
            "vacuum filtration, and recrystallization yield maximization. Controls "
            "crystallization crystal habit and molecular purity yields."
        ),
        rank_titles=_rank_titles(),
        apparatus_unlocks={
            1: ["Erlenmeyer Flask", "Glass Stirring Rod"],
            15: ["Liebig Condenser", "Dimroth Condenser"],
            30: ["Büchner Funnel", "Water Aspirator"],
            50: ["Rotary Evaporator", "Schlenk Line"],
            75: ["Glovebox", "High-Vacuum Manifold"],
            100: ["Athanor Core Reactor"],
        },
        reagent_unlocks={
            1: ["water", "nacl", "salicylic_acid"],
            10: ["acetic_anhydride", "h2so4_cat"],
            25: ["malonic_acid", "potassium_iodide"],
            50: ["benzaldehyde", "acetone", "ethanol"],
            75: ["dmso", "dcm", "thf"],
            100: ["all_preparative_reagents"],
        },
        ability_unlocks={
            5: ["Reflux Condensation Rigging"],
            15: ["Vacuum Crystallization & Filtration"],
            30: ["Recrystallization Yield Optimization"],
            50: ["Inert Atmosphere Schlenk Technique"],
            75: ["Anhydrous Solvent Distillation"],
            100: ["Total Synthesis Design"],
        },
    ),
    SkillType.COMPUTATIONAL: SkillDefinition(
        skill_type=SkillType.COMPUTATIONAL,
        display_name="Computational Modeling",
        short_name="Computational",
        description=(
            "In-silico ODE reaction solving, stoichiometry calculations, RDKit "
            "3D conformer minimization, and automated reagent computer bridging. "
            "Unlocks predictive yield displays and live digital lab notebooks."
        ),
        rank_titles=_rank_titles(),
        apparatus_unlocks={
            1: ["Stoichiometric Matrix Solver", "Digital Lab Notebook"],
            15: ["Kinetic Curve Fitting Station", "Reagent Computer Terminal"],
            30: ["Cantera Reaction Engine Integration", "ODE Solver Workstation"],
            50: ["RDKit 3D Conformer Generator", "Molecular Visualization Suite"],
            75: ["Automated Reagent Computer Bridge", "Machine Learning Yield Predictor"],
            100: ["Quantum Chemistry Cluster Interface"],
        },
        reagent_unlocks={
            1: ["water", "nacl"],
            10: ["hcl", "naoh"],
            25: ["malonic_acid", "potassium_iodate"],
            50: ["rdkit_benchmark_set", "cantera_mechanism_gri30"],
            75: ["nasa_cef_thermo_db", "kinetics_database"],
            100: ["all_computational_databases"],
        },
        ability_unlocks={
            5: ["Live Molar Mass Auto-Calculation"],
            15: ["Real-Time Sigmoidal Curve Fitting"],
            30: ["Arrhenius Parameter Estimation"],
            50: ["Predictive Yield Display"],
            75: ["Automated Lab Notebook Population"],
            100: ["Reaction Network Synthesis Planning"],
        },
    ),
}


def get_skill(skill_type: SkillType) -> SkillDefinition:
    """Return the static definition for a skill discipline."""
    return ALL_SKILLS[skill_type]
