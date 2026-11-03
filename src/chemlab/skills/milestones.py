"""
Milestone definitions for ChemLab skill progression.

A milestone unlocks at a specific skill level and grants apparatus,
reagents, abilities, or narrative credentials. Mirrors the node-unlock
structure from docs/STORY_AND_QUESTS.md §2 but generalized across all
levels 1-120 using Runescape-style thresholds.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Milestone:
    """A single unlockable milestone gated behind a skill level."""

    skill: str
    level: int
    title: str
    description: str
    unlocked_apparatus: list[str] = field(default_factory=list)
    unlocked_reagents: list[str] = field(default_factory=list)
    unlocked_abilities: list[str] = field(default_factory=list)
    narrative_unlock: str | None = None
    # Optional predicate: a callable(skill_manager) -> bool for dynamic gating.
    predicate: Callable[..., bool] | None = None


# All milestones across the five disciplines, levels 1-120.
MILESTONES: list[Milestone] = [
    # ── SAFETY ──────────────────────────────────────────────────────────────
    Milestone(
        skill="safety",
        level=1,
        title="PPE Protocol & Donning Discipline",
        description="Unlocks nitrile, neoprene, and butyl gloves; splash goggles; lab coat certification.",
        unlocked_apparatus=["Lab Coat", "Safety Goggles", "Nitrile Gloves"],
        unlocked_reagents=["water", "nacl", "universal_indicator"],
        unlocked_abilities=["Don Personal Protective Equipment"],
        narrative_unlock="KHI-ACS Level 0 General Lab Entry Clearance",
    ),
    Milestone(
        skill="safety",
        level=10,
        title="Aerodynamic Containment",
        description="Unlocks manual sash adjustment, face velocity diagnostics, and turbulent airflow visualization.",
        unlocked_apparatus=["Face Shield", "Chemical Apron", "Fume Hood Sash Control"],
        unlocked_reagents=["hcl", "naoh"],
        unlocked_abilities=["Fume Hood Sash Calibration"],
    ),
    Milestone(
        skill="safety",
        level=25,
        title="Cryogenic & Pyrophoric Containment",
        description="Unlocks liquid nitrogen dewars, argon atmosphere glovebox, and pyrophoric syringe-transfer techniques.",
        unlocked_apparatus=["HazMat Suit", "Full-Face Respirator"],
        unlocked_reagents=["h2so4", "h2o2"],
        unlocked_abilities=["Spill Neutralization Protocol", "Pyrophoric Substance Handling"],
    ),
    Milestone(
        skill="safety",
        level=50,
        title="Hazardous Spill Mitigation",
        description="Unlocks emergency spill kits, bicarbonate berm placement, and effervescence rate moderation.",
        unlocked_apparatus=["Emergency Shower Access", "Spill Containment Kit"],
        unlocked_reagents=["hf_acid", "br2", "cl2"],
        unlocked_abilities=["Emergency Eyewash Operation"],
    ),
    Milestone(
        skill="safety",
        level=75,
        title="High-Containment Operations",
        description="OSHA/ANSI Laboratory HazMat First-Responder Certification. Positive-pressure suit and incident command.",
        unlocked_apparatus=["Positive-Pressure HazMat Hood"],
        unlocked_reagents=["hcn", "phosgene"],
        unlocked_abilities=["Cryogenic Liquid Transfer", "HazMat Incident Command"],
    ),
    Milestone(
        skill="safety",
        level=100,
        title="Level-A Encapsulating Suit",
        description="Maximum-containment clearance for all chemical classes.",
        unlocked_apparatus=["Level-A Encapsulating Suit"],
        unlocked_reagents=["sarin_precursors", "vx_precursors"],
        unlocked_abilities=["HazMat Incident Command"],
        narrative_unlock="Educational/stoichiometric access only — no actionable synthesis routes",
    ),
    # ── ANALYTICAL ──────────────────────────────────────────────────────────
    Milestone(
        skill="analytical",
        level=1,
        title="Tare & Gravimetric Precision",
        description="Analytical balance 4-decimal stabilization, draft-shield auto-compensation.",
        unlocked_apparatus=["Analytical Balance", "Class A Volumetric Pipette"],
        unlocked_reagents=["water", "universal_indicator"],
        unlocked_abilities=["Don Personal Protective Equipment"],
        narrative_unlock="KHI-ACS Level 0 General Lab Entry Clearance",
    ),
    Milestone(
        skill="analytical",
        level=15,
        title="Volumetric Metrology (Class A)",
        description="Calibrated burets, volumetric pipettes, bubble purge detection, and drop-wise stopcock control.",
        unlocked_apparatus=["50 mL Precision Buret", "Porcelain Contrast Tile"],
        unlocked_reagents=["phenolphthalein", "bromothymol_blue"],
        unlocked_abilities=["Dropwise Titration Control"],
    ),
    Milestone(
        skill="analytical",
        level=30,
        title="Optical Spectrophotometry",
        description="UV-Vis absorption spectrum plotting, Beer-Lambert linearity calibration, and wavelength scans.",
        unlocked_apparatus=["UV-Vis Spectrophotometer", "pH Electrode"],
        unlocked_reagents=["ferroin_indicator", "silver_nitrate"],
        unlocked_abilities=["Endpoint Chromatic Recognition"],
    ),
    Milestone(
        skill="analytical",
        level=50,
        title="High-Throughput Analytical Suite",
        description="HPLC-DAD stacks and GC-MS quadrupoles for precise compound identification.",
        unlocked_apparatus=["HPLC-DAD Stack", "GC-MS Quadrupole"],
        unlocked_reagents=["k_permanganate", "iodine_solution"],
        unlocked_abilities=["Calibration Curve Fitting"],
    ),
    Milestone(
        skill="analytical",
        level=75,
        title="Nuclear Magnetic Resonance",
        description="400 MHz FT-NMR spectrometer access for structural elucidation.",
        unlocked_apparatus=["400 MHz FT-NMR Spectrometer"],
        unlocked_reagents=["nmr_solvent_cdcl3", "gc_derivatizing_agent"],
        unlocked_abilities=["Spectral Deconvolution"],
    ),
    Milestone(
        skill="analytical",
        level=100,
        title="High-Resolution Mass Spectrometry",
        description="Full elemental and isotopic analysis suite unlocked.",
        unlocked_apparatus=["High-Resolution Mass Spectrometer"],
        unlocked_reagents=["icp_ms_standard", "xrf_reference"],
        unlocked_abilities=["Multi-Element Quantification"],
    ),
    # ── THERMODYNAMICS ──────────────────────────────────────────────────────
    Milestone(
        skill="thermodynamics",
        level=1,
        title="Calorimetry & Heat Transfer",
        description="Thermocouple placement, water-bath PID stabilization (+/- 0.5°C), endo/exotherm anticipation.",
        unlocked_apparatus=["Digital Thermocouple", "Ice Bath Basin"],
        unlocked_reagents=["water", "ice_matrix"],
        unlocked_abilities=["Water-Bath PID Stabilization"],
    ),
    Milestone(
        skill="thermodynamics",
        level=15,
        title="Thermal Runaway Mitigation",
        description="Heat dissipation calculation, ice-bath quenching speed, activation energy barrier visualization.",
        unlocked_apparatus=["Circulating PID Water Bath", "Magnetic Hotplate"],
        unlocked_reagents=["salicylic_acid", "acetic_anhydride"],
        unlocked_abilities=["Thermal Runaway Mitigation"],
    ),
    Milestone(
        skill="thermodynamics",
        level=30,
        title="Non-Linear Chemical Oscillators",
        description="Autocatalytic cycle synchronization, Briggs-Rauscher / BZ wave tracking, redox potential logging.",
        unlocked_apparatus=["Jacketed Reaction Vessel", "Peltier Plate"],
        unlocked_reagents=["malonic_acid", "potassium_iodate"],
        unlocked_abilities=["Arrhenius Rate Prediction"],
    ),
    Milestone(
        skill="thermodynamics",
        level=50,
        title="Adiabatic Reaction Calorimetry",
        description="Differential scanning calorimetry and adiabatic runaway boundary modeling.",
        unlocked_apparatus=["Differential Scanning Calorimeter", "Flame Photometer"],
        unlocked_reagents=["benzene", "toluene", "diethyl_ether"],
        unlocked_abilities=["Non-Linear Oscillator Tuning"],
    ),
    Milestone(
        skill="thermodynamics",
        level=75,
        title="Cryogenic & Supercritical Systems",
        description="Liquid nitrogen/helium dewars, supercritical fluid control.",
        unlocked_apparatus=["Adiabatic Calorimeter", "Laser Spectroscopy Station"],
        unlocked_reagents=["liquid_nitrogen", "liquid_helium"],
        unlocked_abilities=["Adiabatic Runaway Modeling"],
    ),
    Milestone(
        skill="thermodynamics",
        level=100,
        title="Reaction Calorimeter RC1e",
        description="Full-scale adiabatic reaction calorimetry for process safety validation.",
        unlocked_apparatus=["Reaction Calorimeter RC1e"],
        unlocked_reagents=["liquid_hydrogen", "liquid_oxygen"],
        unlocked_abilities=["Supercritical Fluid Control"],
    ),
    # ── PREPARATIVE ─────────────────────────────────────────────────────────
    Milestone(
        skill="preparative",
        level=1,
        title="Reflux & Condensation Rigging",
        description="Liebig and Dimroth condenser assembly, silicone hose water routing, boiling chip addition.",
        unlocked_apparatus=["Erlenmeyer Flask", "Glass Stirring Rod"],
        unlocked_reagents=["water", "nacl", "salicylic_acid"],
        unlocked_abilities=["Reflux Condensation Rigging"],
    ),
    Milestone(
        skill="preparative",
        level=15,
        title="Vacuum Crystallization & Filtration",
        description="Büchner funnel clamping, aspirator vacuum tuning, mother liquor washing.",
        unlocked_apparatus=["Liebig Condenser", "Dimroth Condenser"],
        unlocked_reagents=["acetic_anhydride", "h2so4_cat"],
        unlocked_abilities=["Vacuum Crystallization & Filtration"],
    ),
    Milestone(
        skill="preparative",
        level=30,
        title="Esterification & Catalysis",
        description="Acid-catalyzed condensation, limiting reagent optimization, side-product minimization.",
        unlocked_apparatus=["Büchner Funnel", "Water Aspirator"],
        unlocked_reagents=["malonic_acid", "potassium_iodide"],
        unlocked_abilities=["Recrystallization Yield Optimization"],
    ),
    Milestone(
        skill="preparative",
        level=50,
        title="Inert Atmosphere Synthesis",
        description="Schlenk line manifolds, glovebox techniques, anhydrous conditions.",
        unlocked_apparatus=["Rotary Evaporator", "Schlenk Line"],
        unlocked_reagents=["benzaldehyde", "acetone", "ethanol"],
        unlocked_abilities=["Inert Atmosphere Schlenk Technique"],
    ),
    Milestone(
        skill="preparative",
        level=75,
        title="High-Containment Synthesis",
        description="Glovebox and high-vacuum manifold access for air-sensitive and pyrophoric compounds.",
        unlocked_apparatus=["Glovebox", "High-Vacuum Manifold"],
        unlocked_reagents=["dmso", "dcm", "thf"],
        unlocked_abilities=["Anhydrous Solvent Distillation"],
    ),
    Milestone(
        skill="preparative",
        level=100,
        title="Total Synthesis Design",
        description="Full laboratory autonomy for multi-step total synthesis design.",
        unlocked_apparatus=["Athanor Core Reactor"],
        unlocked_reagents=["all_preparative_reagents"],
        unlocked_abilities=["Total Synthesis Design"],
    ),
    # ── COMPUTATIONAL ───────────────────────────────────────────────────────
    Milestone(
        skill="computational",
        level=1,
        title="Stoichiometric Matrix Solver",
        description="Live molar mass auto-calculation, limiting reagent highlights on benchtop.",
        unlocked_apparatus=["Stoichiometric Matrix Solver", "Digital Lab Notebook"],
        unlocked_reagents=["water", "nacl"],
        unlocked_abilities=["Live Molar Mass Auto-Calculation"],
    ),
    Milestone(
        skill="computational",
        level=15,
        title="Kinetic Curve Fitting",
        description="Real-time sigmoidal curve generation, reaction rate order calculation.",
        unlocked_apparatus=["Kinetic Curve Fitting Station", "Reagent Computer Terminal"],
        unlocked_reagents=["hcl", "naoh"],
        unlocked_abilities=["Real-Time Sigmoidal Curve Fitting"],
    ),
    Milestone(
        skill="computational",
        level=30,
        title="Cantera Reaction Engine Integration",
        description="Arrhenius parameter estimation, NIST-calibrated thermodynamics.",
        unlocked_apparatus=["Cantera Reaction Engine Integration", "ODE Solver Workstation"],
        unlocked_reagents=["malonic_acid", "potassium_iodate"],
        unlocked_abilities=["Arrhenius Parameter Estimation"],
    ),
    Milestone(
        skill="computational",
        level=50,
        title="RDKit 3D Conformer Generation",
        description="UFF force field minimization, molecular visualization suite.",
        unlocked_apparatus=["RDKit 3D Conformer Generator", "Molecular Visualization Suite"],
        unlocked_reagents=["rdkit_benchmark_set", "cantera_mechanism_gri30"],
        unlocked_abilities=["Predictive Yield Display"],
    ),
    Milestone(
        skill="computational",
        level=75,
        title="Automated Reagent Computer Bridge",
        description="Live digital lab notebook auto-population, ML yield prediction.",
        unlocked_apparatus=[
            "Automated Reagent Computer Bridge",
            "Machine Learning Yield Predictor",
        ],
        unlocked_reagents=["nasa_cef_thermo_db", "kinetics_database"],
        unlocked_abilities=["Automated Lab Notebook Population"],
    ),
    Milestone(
        skill="computational",
        level=100,
        title="Quantum Chemistry Cluster Interface",
        description="Full in-silico reaction network synthesis planning.",
        unlocked_apparatus=["Quantum Chemistry Cluster Interface"],
        unlocked_reagents=["all_computational_databases"],
        unlocked_abilities=["Reaction Network Synthesis Planning"],
    ),
]


def milestones_for_level(skill: str, level: int) -> list[Milestone]:
    """Return all milestones for a skill that unlock exactly at `level`."""
    return [m for m in MILESTONES if m.skill == skill and m.level == level]


def milestones_up_to_level(skill: str, level: int) -> list[Milestone]:
    """Return all milestones for a skill with level <= `level`."""
    return [m for m in MILESTONES if m.skill == skill and m.level <= level]
