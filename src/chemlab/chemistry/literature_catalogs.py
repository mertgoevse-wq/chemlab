"""
ChemLab Literature Catalog — PiHKAL & TiHKAL Educational Simulation Data.
============================================================================

Complete literature reaction routes from PiHKAL (Phenethylamines I Have Known And Loved)
and TiHKAL (Tryptamines I Have Known And Loved) by Alexander & Ann Shulgin.

Provides:
- Simulation properties for thermodynamics, rendering, and safety. Fundamental
  species use published reference values where available; complex organics may
  use documented engineering estimates and must not be treated as calorimetry.
- Explicit reaction-system boundaries: closed equations are element-balanced,
  while abbreviated process/workup steps are marked as open systems.
- Exothermic/endothermic reaction energy profiles and activation barriers.
- Real-time Graphics Bridge mapping:
  - Concentration -> Beer-Lambert absorbance (A = eps * c * l) and transmission.
  - Gas emission rate -> bubble generation rate (dn_gas/dt) and volume expansion.
  - Suspension turbidity & Stokes' Law particulate sedimentation velocity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LiteratureSpecies:
    """Canonical chemical species with physical, thermodynamic, and safety constants."""

    id: str
    formula: str
    name: str
    molecular_weight_g_mol: float
    density_g_cm3: float
    delta_h_f_kj_mol: float  # Standard enthalpy of formation (kJ/mol)
    s_standard_j_mol_k: float  # Standard molar entropy (J/(mol·K))
    cp_j_mol_k: float  # Molar heat capacity (J/(mol·K))
    cas_number: str
    ghs_pictograms: tuple[str, ...]
    h_statements: tuple[str, ...]
    p_statements: tuple[str, ...]
    boiling_point_c: float
    melting_point_c: float
    is_volatile: bool = False
    is_controlled_precursor: bool = False
    extinction_coefficient_m_cm: float = 0.0  # M^-1 cm^-1 for Beer-Lambert
    particle_radius_um: float = 25.0  # Average crystal radius in micrometers for Stokes' Law


@dataclass(frozen=True)
class SynthesisStep:
    """Single balanced reaction step with precise stoichiometry and reaction conditions."""

    step_number: int
    name: str
    reactants: dict[str, float]  # species_id -> stoichiometric coefficient
    products: dict[str, float]  # species_id -> stoichiometric coefficient
    temperature_target_c: float
    activation_energy_kj_mol: float
    expected_yield_pct: float
    solvent: str
    reflux: bool = False
    fume_hood_required: bool = True
    inert_atmosphere: bool = False
    side_products: tuple[str, ...] = ()
    description: str = ""
    is_closed_system: bool = True
    balance_note: str = ""


@dataclass(frozen=True)
class LiteratureSynthesisRoute:
    """Multi-step synthesis pathway for a targeted psychoactive alkaloid or pharmaceutical."""

    id: str
    compound_id: str
    name: str
    literature_source: str
    target_smiles: str
    steps: tuple[SynthesisStep, ...]
    overall_yield_pct: float = 65.0


# =============================================================================
# 1. Authoritative Thermodynamic Database: PiHKAL & TiHKAL Chemical Species
# =============================================================================

PIHKAL_TIHKAL_SPECIES: dict[str, LiteratureSpecies] = {
    # ── Fundamental Inorganics, Hydrides & Gases ─────────────────────────────
    "H2O": LiteratureSpecies(
        id="H2O",
        formula="H2O",
        name="Water",
        molecular_weight_g_mol=18.015,
        density_g_cm3=1.000,
        delta_h_f_kj_mol=-285.83,
        s_standard_j_mol_k=69.91,
        cp_j_mol_k=75.38,
        cas_number="7732-18-5",
        ghs_pictograms=(),
        h_statements=(),
        p_statements=(),
        boiling_point_c=100.0,
        melting_point_c=0.0,
    ),
    "HCl_gas": LiteratureSpecies(
        id="HCl_gas",
        formula="HCl",
        name="Hydrogen chloride gas",
        molecular_weight_g_mol=36.461,
        density_g_cm3=0.00149,
        delta_h_f_kj_mol=-92.31,
        s_standard_j_mol_k=186.91,
        cp_j_mol_k=29.12,
        cas_number="7647-01-0",
        ghs_pictograms=("GHS04", "GHS05", "GHS06"),
        h_statements=("H280", "H314", "H330"),
        p_statements=("P260", "P280", "P304+P340"),
        boiling_point_c=-85.05,
        melting_point_c=-114.22,
        is_volatile=True,
    ),
    "HBr_gas": LiteratureSpecies(
        id="HBr_gas",
        formula="HBr",
        name="Hydrogen bromide gas",
        molecular_weight_g_mol=80.912,
        density_g_cm3=0.0033,
        delta_h_f_kj_mol=-36.29,
        s_standard_j_mol_k=198.70,
        cp_j_mol_k=29.14,
        cas_number="10035-10-6",
        ghs_pictograms=("GHS04", "GHS05", "GHS06"),
        h_statements=("H280", "H314", "H331"),
        p_statements=("P260", "P280", "P304+P340"),
        boiling_point_c=-66.38,
        melting_point_c=-86.80,
        is_volatile=True,
    ),
    "H2_gas": LiteratureSpecies(
        id="H2_gas",
        formula="H2",
        name="Hydrogen gas",
        molecular_weight_g_mol=2.016,
        density_g_cm3=0.000089,
        delta_h_f_kj_mol=0.0,
        s_standard_j_mol_k=130.68,
        cp_j_mol_k=28.84,
        cas_number="1333-74-0",
        ghs_pictograms=("GHS02", "GHS04"),
        h_statements=("H220", "H280"),
        p_statements=("P210", "P377", "P403"),
        boiling_point_c=-252.87,
        melting_point_c=-259.16,
        is_volatile=True,
    ),
    "bromine": LiteratureSpecies(
        id="bromine",
        formula="Br2",
        name="Bromine liquid",
        molecular_weight_g_mol=159.808,
        density_g_cm3=3.1028,
        delta_h_f_kj_mol=0.0,
        s_standard_j_mol_k=152.23,
        cp_j_mol_k=75.69,
        cas_number="7726-95-6",
        ghs_pictograms=("GHS05", "GHS06", "GHS09"),
        h_statements=("H314", "H330", "H400"),
        p_statements=("P260", "P280", "P304+P340"),
        boiling_point_c=58.8,
        melting_point_c=-7.2,
        is_volatile=True,
    ),
    "lialh4": LiteratureSpecies(
        id="lialh4",
        formula="LiAlH4",
        name="Lithium aluminium hydride",
        molecular_weight_g_mol=37.954,
        density_g_cm3=0.917,
        delta_h_f_kj_mol=-116.3,
        s_standard_j_mol_k=78.7,
        cp_j_mol_k=83.2,
        cas_number="16853-85-3",
        ghs_pictograms=("GHS02", "GHS05"),
        h_statements=("H260", "H314"),
        p_statements=("P223", "P231+P232", "P280", "P370+P378"),
        boiling_point_c=125.0,  # decomposes
        melting_point_c=125.0,
    ),
    "lialo2": LiteratureSpecies(
        id="lialo2",
        formula="LiAlO2",
        name="Lithium aluminate (LAH reduction byproduct)",
        molecular_weight_g_mol=65.920,
        density_g_cm3=2.61,
        delta_h_f_kj_mol=-1188.7,
        s_standard_j_mol_k=53.6,
        cp_j_mol_k=67.8,
        cas_number="12003-67-7",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=1700.0,
        melting_point_c=1625.0,
    ),
    "nabh4": LiteratureSpecies(
        id="nabh4",
        formula="NaBH4",
        name="Sodium borohydride",
        molecular_weight_g_mol=37.83,
        density_g_cm3=1.07,
        delta_h_f_kj_mol=-188.6,
        s_standard_j_mol_k=101.3,
        cp_j_mol_k=86.8,
        cas_number="16940-66-2",
        ghs_pictograms=("GHS02", "GHS06", "GHS05"),
        h_statements=("H260", "H301", "H314"),
        p_statements=("P223", "P231+P232", "P280", "P301+P310"),
        boiling_point_c=400.0,
        melting_point_c=300.0,
    ),
    "nabo2": LiteratureSpecies(
        id="nabo2",
        formula="NaBO2",
        name="Sodium metaborate",
        molecular_weight_g_mol=65.80,
        density_g_cm3=2.46,
        delta_h_f_kj_mol=-976.1,
        s_standard_j_mol_k=73.6,
        cp_j_mol_k=65.7,
        cas_number="7775-19-1",
        ghs_pictograms=("GHS07", "GHS08"),
        h_statements=("H319", "H361d"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=1434.0,
        melting_point_c=966.0,
    ),
    "ammonium_acetate": LiteratureSpecies(
        id="ammonium_acetate",
        formula="C2H7NO2",
        name="Ammonium acetate",
        molecular_weight_g_mol=77.082,
        density_g_cm3=1.17,
        delta_h_f_kj_mol=-626.8,
        s_standard_j_mol_k=138.0,
        cp_j_mol_k=125.0,
        cas_number="631-61-8",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319", "H335"),
        p_statements=("P261", "P280", "P305+P351+P338"),
        boiling_point_c=117.1,
        melting_point_c=114.0,
    ),
    # ── Starting Benzaldehydes & Precursors ──────────────────────────────────
    "3_4_5_trimethoxybenzaldehyde": LiteratureSpecies(
        id="3_4_5_trimethoxybenzaldehyde",
        formula="C10H12O4",
        name="3,4,5-Trimethoxybenzaldehyde",
        molecular_weight_g_mol=196.202,
        density_g_cm3=1.18,
        delta_h_f_kj_mol=-675.2,
        s_standard_j_mol_k=275.0,
        cp_j_mol_k=245.0,
        cas_number="86-81-7",
        ghs_pictograms=("GHS07",),
        h_statements=("H302", "H315", "H319"),
        p_statements=("P264", "P280", "P305+P351+P338"),
        boiling_point_c=170.0,
        melting_point_c=74.0,
        extinction_coefficient_m_cm=9800.0,
    ),
    "nitromethane": LiteratureSpecies(
        id="nitromethane",
        formula="CH3NO2",
        name="Nitromethane",
        molecular_weight_g_mol=61.040,
        density_g_cm3=1.137,
        delta_h_f_kj_mol=-113.1,
        s_standard_j_mol_k=171.8,
        cp_j_mol_k=106.3,
        cas_number="75-52-5",
        ghs_pictograms=("GHS02", "GHS07", "GHS08"),
        h_statements=("H226", "H302", "H351"),
        p_statements=("P210", "P280", "P301+P312"),
        boiling_point_c=101.2,
        melting_point_c=-29.0,
        is_volatile=True,
    ),
    "nitroethane": LiteratureSpecies(
        id="nitroethane",
        formula="C2H5NO2",
        name="Nitroethane",
        molecular_weight_g_mol=75.067,
        density_g_cm3=1.045,
        delta_h_f_kj_mol=-142.4,
        s_standard_j_mol_k=211.5,
        cp_j_mol_k=134.7,
        cas_number="79-24-3",
        ghs_pictograms=("GHS02", "GHS07"),
        h_statements=("H226", "H302", "H332"),
        p_statements=("P210", "P261", "P301+P312"),
        boiling_point_c=114.0,
        melting_point_c=-90.0,
        is_volatile=True,
    ),
    "piperonal": LiteratureSpecies(
        id="piperonal",
        formula="C8H6O3",
        name="Piperonal (Heliotropin)",
        molecular_weight_g_mol=150.13,
        density_g_cm3=1.28,
        delta_h_f_kj_mol=-452.0,
        s_standard_j_mol_k=220.0,
        cp_j_mol_k=190.0,
        cas_number="120-57-0",
        ghs_pictograms=("GHS07",),
        h_statements=("H317",),
        p_statements=("P280", "P302+P352"),
        boiling_point_c=263.0,
        melting_point_c=37.0,
        is_controlled_precursor=True,
        extinction_coefficient_m_cm=11200.0,
    ),
    "2_5_dimethoxybenzaldehyde": LiteratureSpecies(
        id="2_5_dimethoxybenzaldehyde",
        formula="C9H10O3",
        name="2,5-Dimethoxybenzaldehyde",
        molecular_weight_g_mol=166.176,
        density_g_cm3=1.16,
        delta_h_f_kj_mol=-512.4,
        s_standard_j_mol_k=248.0,
        cp_j_mol_k=210.0,
        cas_number="93-02-7",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319", "H335"),
        p_statements=("P261", "P280", "P305+P351+P338"),
        boiling_point_c=146.0,
        melting_point_c=50.0,
        extinction_coefficient_m_cm=8900.0,
    ),
    "2_5_dimethoxy_4_methylbenzaldehyde": LiteratureSpecies(
        id="2_5_dimethoxy_4_methylbenzaldehyde",
        formula="C10H12O3",
        name="2,5-Dimethoxy-4-methylbenzaldehyde",
        molecular_weight_g_mol=180.203,
        density_g_cm3=1.12,
        delta_h_f_kj_mol=-548.0,
        s_standard_j_mol_k=262.0,
        cp_j_mol_k=230.0,
        cas_number="13898-84-5",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=165.0,
        melting_point_c=84.0,
    ),
    # ── Nitrostyrene & Nitropropene Intermediates ─────────────────────────────
    "3_4_5_trimethoxynitrostyrene": LiteratureSpecies(
        id="3_4_5_trimethoxynitrostyrene",
        formula="C11H13NO5",
        name="1-(3,4,5-Trimethoxyphenyl)-2-nitroethene",
        molecular_weight_g_mol=239.227,
        density_g_cm3=1.31,
        delta_h_f_kj_mol=-525.0,
        s_standard_j_mol_k=305.0,
        cp_j_mol_k=285.0,
        cas_number="1806-00-4",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319", "H335"),
        p_statements=("P261", "P280", "P305+P351+P338"),
        boiling_point_c=220.0,
        melting_point_c=120.0,
        extinction_coefficient_m_cm=14200.0,  # intense yellow absorption
        particle_radius_um=35.0,
    ),
    "2_5_dimethoxynitrostyrene": LiteratureSpecies(
        id="2_5_dimethoxynitrostyrene",
        formula="C10H11NO4",
        name="1-(2,5-Dimethoxyphenyl)-2-nitroethene",
        molecular_weight_g_mol=209.201,
        density_g_cm3=1.28,
        delta_h_f_kj_mol=-365.0,
        s_standard_j_mol_k=278.0,
        cp_j_mol_k=250.0,
        cas_number="41589-94-6",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=195.0,
        melting_point_c=119.0,
        extinction_coefficient_m_cm=13500.0,
        particle_radius_um=40.0,
    ),
    "2_5_dimethoxy_4_methyl_nitropropene": LiteratureSpecies(
        id="2_5_dimethoxy_4_methyl_nitropropene",
        formula="C12H15NO4",
        name="1-(2,5-Dimethoxy-4-methylphenyl)-2-nitropropene",
        molecular_weight_g_mol=237.255,
        density_g_cm3=1.24,
        delta_h_f_kj_mol=-435.0,
        s_standard_j_mol_k=315.0,
        cp_j_mol_k=295.0,
        cas_number="63628-86-6",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=215.0,
        melting_point_c=87.0,
        extinction_coefficient_m_cm=12800.0,
    ),
    "mdp2np": LiteratureSpecies(
        id="mdp2np",
        formula="C10H9NO4",
        name="1-(3,4-Methylenedioxyphenyl)-2-nitropropene",
        molecular_weight_g_mol=207.182,
        density_g_cm3=1.35,
        delta_h_f_kj_mol=-270.5,
        s_standard_j_mol_k=268.0,
        cp_j_mol_k=242.0,
        cas_number="5438-41-5",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319", "H335"),
        p_statements=("P261", "P280", "P305+P351+P338"),
        boiling_point_c=210.0,
        melting_point_c=98.0,
        is_controlled_precursor=True,
        extinction_coefficient_m_cm=15000.0,
        particle_radius_um=30.0,
    ),
    # ── Phenethylamine Targets (PiHKAL) ──────────────────────────────────────
    "mescaline": LiteratureSpecies(
        id="mescaline",
        formula="C11H17NO3",
        name="Mescaline (3,4,5-trimethoxyphenethylamine)",
        molecular_weight_g_mol=211.26,
        density_g_cm3=1.12,
        delta_h_f_kj_mol=-542.4,
        s_standard_j_mol_k=312.0,
        cp_j_mol_k=295.0,
        cas_number="54-04-1",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H301", "H336"),
        p_statements=("P264", "P301+P310"),
        boiling_point_c=325.0,
        melting_point_c=36.0,
        is_controlled_precursor=True,
    ),
    "2c_h": LiteratureSpecies(
        id="2c_h",
        formula="C10H15NO2",
        name="2C-H (2,5-dimethoxyphenethylamine)",
        molecular_weight_g_mol=181.23,
        density_g_cm3=1.08,
        delta_h_f_kj_mol=-382.1,
        s_standard_j_mol_k=285.0,
        cp_j_mol_k=260.0,
        cas_number="3600-86-0",
        ghs_pictograms=("GHS07",),
        h_statements=("H302", "H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=290.0,
        melting_point_c=25.0,
    ),
    "2c_b": LiteratureSpecies(
        id="2c_b",
        formula="C10H14BrNO2",
        name="2C-B (4-bromo-2,5-dimethoxyphenethylamine)",
        molecular_weight_g_mol=260.126,
        density_g_cm3=1.42,
        delta_h_f_kj_mol=-418.5,
        s_standard_j_mol_k=310.0,
        cp_j_mol_k=288.0,
        cas_number="66142-81-2",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H301", "H312", "H336"),
        p_statements=("P261", "P280", "P301+P310"),
        boiling_point_c=340.0,
        melting_point_c=237.0,  # HCl salt
        is_controlled_precursor=True,
    ),
    "dom": LiteratureSpecies(
        id="dom",
        formula="C12H19NO2",
        name="DOM (2,5-dimethoxy-4-methylamphetamine)",
        molecular_weight_g_mol=209.284,
        density_g_cm3=1.05,
        delta_h_f_kj_mol=-448.2,
        s_standard_j_mol_k=324.0,
        cp_j_mol_k=305.0,
        cas_number="15588-95-1",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H300", "H330", "H336"),
        p_statements=("P260", "P280", "P301+P310"),
        boiling_point_c=310.0,
        melting_point_c=190.0,  # HCl salt
        is_controlled_precursor=True,
    ),
    "mdma": LiteratureSpecies(
        id="mdma",
        formula="C11H15NO2",
        name="MDMA (3,4-methylenedioxymethamphetamine)",
        molecular_weight_g_mol=193.242,
        density_g_cm3=1.11,
        delta_h_f_kj_mol=-330.0,
        s_standard_j_mol_k=298.0,
        cp_j_mol_k=280.0,
        cas_number="42542-10-9",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H301", "H311", "H331", "H336"),
        p_statements=("P261", "P280", "P301+P310"),
        boiling_point_c=305.0,
        melting_point_c=148.0,
        is_controlled_precursor=True,
    ),
    # ── Indole & Tryptamine Feedstocks (TiHKAL) ──────────────────────────────
    "indole": LiteratureSpecies(
        id="indole",
        formula="C8H7N",
        name="Indole",
        molecular_weight_g_mol=117.15,
        density_g_cm3=1.22,
        delta_h_f_kj_mol=89.5,
        s_standard_j_mol_k=162.0,
        cp_j_mol_k=154.0,
        cas_number="120-72-9",
        ghs_pictograms=("GHS06", "GHS09"),
        h_statements=("H302", "H311", "H319", "H411"),
        p_statements=("P273", "P280", "P301+P312", "P302+P352"),
        boiling_point_c=253.0,
        melting_point_c=52.5,
        extinction_coefficient_m_cm=5500.0,
    ),
    "indole_3_carboxaldehyde": LiteratureSpecies(
        id="indole_3_carboxaldehyde",
        formula="C9H7NO",
        name="Indole-3-carboxaldehyde",
        molecular_weight_g_mol=145.16,
        density_g_cm3=1.26,
        delta_h_f_kj_mol=-35.0,
        s_standard_j_mol_k=210.0,
        cp_j_mol_k=185.0,
        cas_number="487-89-8",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319", "H335"),
        p_statements=("P261", "P280", "P305+P351+P338"),
        boiling_point_c=310.0,
        melting_point_c=196.0,
    ),
    "oxalyl_chloride": LiteratureSpecies(
        id="oxalyl_chloride",
        formula="C2Cl2O2",
        name="Oxalyl chloride",
        molecular_weight_g_mol=126.93,
        density_g_cm3=1.48,
        delta_h_f_kj_mol=-360.5,
        s_standard_j_mol_k=285.0,
        cp_j_mol_k=130.0,
        cas_number="79-37-8",
        ghs_pictograms=("GHS05", "GHS06"),
        h_statements=("H314", "H331", "H335"),
        p_statements=("P260", "P280", "P304+P340"),
        boiling_point_c=63.5,
        melting_point_c=-9.0,
        is_volatile=True,
    ),
    "indole_3_glyoxyl_chloride": LiteratureSpecies(
        id="indole_3_glyoxyl_chloride",
        formula="C10H6ClNO2",
        name="Indole-3-glyoxyl chloride",
        molecular_weight_g_mol=207.61,
        density_g_cm3=1.38,
        delta_h_f_kj_mol=-195.0,
        s_standard_j_mol_k=295.0,
        cp_j_mol_k=245.0,
        cas_number="22980-09-2",
        ghs_pictograms=("GHS05", "GHS07"),
        h_statements=("H314", "H335"),
        p_statements=("P260", "P280", "P305+P351+P338"),
        boiling_point_c=315.0,
        melting_point_c=135.0,
    ),
    "dimethylamine": LiteratureSpecies(
        id="dimethylamine",
        formula="C2H7N",
        name="Dimethylamine gas",
        molecular_weight_g_mol=45.084,
        density_g_cm3=0.0019,
        delta_h_f_kj_mol=-18.4,
        s_standard_j_mol_k=273.2,
        cp_j_mol_k=70.0,
        cas_number="124-40-3",
        ghs_pictograms=("GHS02", "GHS04", "GHS05", "GHS07"),
        h_statements=("H220", "H280", "H314", "H332", "H335"),
        p_statements=("P210", "P260", "P280", "P304+P340"),
        boiling_point_c=6.9,
        melting_point_c=-92.2,
        is_volatile=True,
    ),
    "indole_3_dimethylglyoxylamide": LiteratureSpecies(
        id="indole_3_dimethylglyoxylamide",
        formula="C12H12N2O2",
        name="N,N-Dimethyl-2-(1H-indol-3-yl)-2-oxoacetamide",
        molecular_weight_g_mol=216.236,
        density_g_cm3=1.27,
        delta_h_f_kj_mol=-255.0,
        s_standard_j_mol_k=310.0,
        cp_j_mol_k=260.0,
        cas_number="10317-09-6",
        ghs_pictograms=("GHS07",),
        h_statements=("H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=360.0,
        melting_point_c=160.0,
        particle_radius_um=30.0,
    ),
    "tryptamine": LiteratureSpecies(
        id="tryptamine",
        formula="C10H12N2",
        name="Tryptamine",
        molecular_weight_g_mol=160.216,
        density_g_cm3=1.14,
        delta_h_f_kj_mol=45.2,
        s_standard_j_mol_k=240.0,
        cp_j_mol_k=220.0,
        cas_number="61-54-1",
        ghs_pictograms=("GHS07",),
        h_statements=("H302", "H315", "H319"),
        p_statements=("P264", "P280", "P305+P351+P338"),
        boiling_point_c=320.0,
        melting_point_c=118.0,
    ),
    "5_methoxytryptamine": LiteratureSpecies(
        id="5_methoxytryptamine",
        formula="C11H14N2O",
        name="5-Methoxytryptamine (Mexamine)",
        molecular_weight_g_mol=190.242,
        density_g_cm3=1.18,
        delta_h_f_kj_mol=-125.0,
        s_standard_j_mol_k=270.0,
        cp_j_mol_k=250.0,
        cas_number="608-07-1",
        ghs_pictograms=("GHS07",),
        h_statements=("H302", "H315", "H319"),
        p_statements=("P280", "P305+P351+P338"),
        boiling_point_c=350.0,
        melting_point_c=121.0,
    ),
    # ── Tryptamine Targets (TiHKAL) ──────────────────────────────────────────
    "dmt": LiteratureSpecies(
        id="dmt",
        formula="C12H16N2",
        name="N,N-Dimethyltryptamine (DMT)",
        molecular_weight_g_mol=188.269,
        density_g_cm3=1.09,
        delta_h_f_kj_mol=-12.5,
        s_standard_j_mol_k=295.0,
        cp_j_mol_k=272.0,
        cas_number="61-50-7",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H301", "H330", "H336"),
        p_statements=("P260", "P280", "P301+P310"),
        boiling_point_c=380.0,
        melting_point_c=46.0,
        is_controlled_precursor=True,
    ),
    "5_meo_dmt": LiteratureSpecies(
        id="5_meo_dmt",
        formula="C13H18N2O",
        name="5-Methoxy-N,N-dimethyltryptamine (5-MeO-DMT)",
        molecular_weight_g_mol=218.295,
        density_g_cm3=1.12,
        delta_h_f_kj_mol=-185.0,
        s_standard_j_mol_k=325.0,
        cp_j_mol_k=302.0,
        cas_number="1019-45-0",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H300", "H330", "H336"),
        p_statements=("P260", "P280", "P301+P310"),
        boiling_point_c=395.0,
        melting_point_c=69.0,
        is_controlled_precursor=True,
    ),
    "psilocin": LiteratureSpecies(
        id="psilocin",
        formula="C12H16N2O",
        name="Psilocin (4-hydroxy-N,N-dimethyltryptamine)",
        molecular_weight_g_mol=204.268,
        density_g_cm3=1.19,
        delta_h_f_kj_mol=-215.0,
        s_standard_j_mol_k=305.0,
        cp_j_mol_k=285.0,
        cas_number="520-53-6",
        ghs_pictograms=("GHS06", "GHS08"),
        h_statements=("H301", "H336"),
        p_statements=("P261", "P280", "P301+P310"),
        boiling_point_c=410.0,
        melting_point_c=174.0,
        is_controlled_precursor=True,
    ),
}


# =============================================================================
# 2. Multi-Step Synthesis Pathways with Exact Stoichiometric Conservation
# =============================================================================

LITERATURE_ROUTES: dict[str, LiteratureSynthesisRoute] = {
    # ── Mescaline Synthesis (Henry condensation + LAH reduction) ─────────────
    "mescaline_henry_lah": LiteratureSynthesisRoute(
        id="mescaline_henry_lah",
        compound_id="mescaline",
        name="PiHKAL #96: Henry Condensation followed by LAH reduction",
        literature_source="PiHKAL: A Chemical Love Story, Shulgin & Shulgin, 1991",
        target_smiles="COC1=CC(=CC(=C1OC)OC)CCN",
        overall_yield_pct=66.0,
        steps=(
            SynthesisStep(
                step_number=1,
                name="Henry Condensation to 3,4,5-Trimethoxynitrostyrene",
                reactants={
                    "3_4_5_trimethoxybenzaldehyde": 1.0,
                    "nitromethane": 1.0,
                },
                products={
                    "3_4_5_trimethoxynitrostyrene": 1.0,
                    "H2O": 1.0,
                },
                temperature_target_c=105.0,
                activation_energy_kj_mol=78.5,
                expected_yield_pct=84.0,
                solvent="acetic_acid",
                reflux=True,
                side_products=("polymeric_resins",),
                description="Condensation of benzaldehyde with nitromethane catalyzed by ammonium acetate.",
            ),
            SynthesisStep(
                step_number=2,
                name="Lithium Aluminium Hydride Reduction to Mescaline Freebase",
                reactants={
                    "3_4_5_trimethoxynitrostyrene": 1.0,
                    "lialh4": 2.0,
                },
                products={
                    "mescaline": 1.0,
                    "lialo2": 2.0,
                },
                temperature_target_c=66.0,
                activation_energy_kj_mol=42.0,
                expected_yield_pct=78.5,
                solvent="thf",
                reflux=True,
                inert_atmosphere=True,
                side_products=("hydroxylamines",),
                description="Complete reduction of the nitroalkene double bond and nitro group to primary amine.",
                is_closed_system=False,
                balance_note=(
                    "Abbreviated process boundary: hydrolysis/workup species and inorganic "
                    "hydride products are not represented as a closed reaction equation."
                ),
            ),
        ),
    ),
    # ── 2C-B Synthesis (Henry + LAH + Bromination) ───────────────────────────
    "2c_b_synthesis": LiteratureSynthesisRoute(
        id="2c_b_synthesis",
        compound_id="2c_b",
        name="PiHKAL #20: 2C-H synthesis followed by regioselective para-bromination",
        literature_source="PiHKAL: A Chemical Love Story, Shulgin & Shulgin, 1991",
        target_smiles="COC1=CC(=C(C=C1CCN)Br)OC",
        overall_yield_pct=70.0,
        steps=(
            SynthesisStep(
                step_number=1,
                name="Henry Condensation to 2,5-Dimethoxynitrostyrene",
                reactants={
                    "2_5_dimethoxybenzaldehyde": 1.0,
                    "nitromethane": 1.0,
                },
                products={
                    "2_5_dimethoxynitrostyrene": 1.0,
                    "H2O": 1.0,
                },
                temperature_target_c=100.0,
                activation_energy_kj_mol=80.0,
                expected_yield_pct=86.0,
                solvent="acetic_acid",
                reflux=True,
            ),
            SynthesisStep(
                step_number=2,
                name="LAH Reduction to 2C-H Freebase",
                reactants={
                    "2_5_dimethoxynitrostyrene": 1.0,
                    "lialh4": 2.0,
                },
                products={
                    "2c_h": 1.0,
                    "lialo2": 2.0,
                },
                temperature_target_c=66.0,
                activation_energy_kj_mol=45.0,
                expected_yield_pct=82.0,
                solvent="thf",
                reflux=True,
                inert_atmosphere=True,
                is_closed_system=False,
                balance_note=(
                    "Abbreviated process boundary: hydrolysis/workup species and inorganic "
                    "hydride products are not represented as a closed reaction equation."
                ),
            ),
            SynthesisStep(
                step_number=3,
                name="Electrophilic Aromatic Bromination to 2C-B",
                reactants={
                    "2c_h": 1.0,
                    "bromine": 1.0,
                },
                products={
                    "2c_b": 1.0,
                    "HBr_gas": 1.0,
                },
                temperature_target_c=25.0,
                activation_energy_kj_mol=32.0,
                expected_yield_pct=91.0,
                solvent="glacial_acetic_acid",
                side_products=("dibromo_impurities",),
                description="Para-bromination of 2C-H generating 2C-B hydrobromide precipitate.",
            ),
        ),
    ),
    # ── DOM Synthesis (Henry condensation of nitroethane + LAH) ──────────────
    "dom_synthesis": LiteratureSynthesisRoute(
        id="dom_synthesis",
        compound_id="dom",
        name="PiHKAL #68: 2,5-Dimethoxy-4-methylphenyl-2-nitropropene reduction",
        literature_source="PiHKAL: A Chemical Love Story, Shulgin & Shulgin, 1991",
        target_smiles="CC(CC1=CC(=C(C=C1OC)C)OC)N",
        overall_yield_pct=64.0,
        steps=(
            SynthesisStep(
                step_number=1,
                name="Henry Condensation with Nitroethane to Nitropropene",
                reactants={
                    "2_5_dimethoxy_4_methylbenzaldehyde": 1.0,
                    "nitroethane": 1.0,
                },
                products={
                    "2_5_dimethoxy_4_methyl_nitropropene": 1.0,
                    "H2O": 1.0,
                },
                temperature_target_c=105.0,
                activation_energy_kj_mol=82.0,
                expected_yield_pct=83.0,
                solvent="acetic_acid",
                reflux=True,
            ),
            SynthesisStep(
                step_number=2,
                name="LAH Reduction to DOM Freebase",
                reactants={
                    "2_5_dimethoxy_4_methyl_nitropropene": 1.0,
                    "lialh4": 2.0,
                },
                products={
                    "dom": 1.0,
                    "lialo2": 2.0,
                },
                temperature_target_c=66.0,
                activation_energy_kj_mol=44.0,
                expected_yield_pct=77.0,
                solvent="thf",
                reflux=True,
                inert_atmosphere=True,
                is_closed_system=False,
                balance_note=(
                    "Abbreviated process boundary: hydrolysis/workup species and inorganic "
                    "hydride products are not represented as a closed reaction equation."
                ),
            ),
        ),
    ),
    # ── DMT Speeter-Anthony Route (TiHKAL #6) ─────────────────────────────────
    "dmt_speeter_anthony": LiteratureSynthesisRoute(
        id="dmt_speeter_anthony",
        compound_id="dmt",
        name="TiHKAL #6: Speeter-Anthony Acylation followed by LAH reduction",
        literature_source="TiHKAL: The Continuation, Shulgin & Shulgin, 1997",
        target_smiles="CN(C)CCC1=CNC2=CC=CC=C12",
        overall_yield_pct=68.0,
        steps=(
            SynthesisStep(
                step_number=1,
                name="C-3 Friedel-Crafts Acylation of Indole with Oxalyl Chloride",
                reactants={
                    "indole": 1.0,
                    "oxalyl_chloride": 1.0,
                },
                products={
                    "indole_3_glyoxyl_chloride": 1.0,
                    "HCl_gas": 1.0,
                },
                temperature_target_c=0.0,
                activation_energy_kj_mol=28.0,
                expected_yield_pct=92.0,
                solvent="diethyl_ether",
                fume_hood_required=True,
                description="Electrophilic acylation yielding bright yellow indole-3-glyoxyl chloride.",
            ),
            SynthesisStep(
                step_number=2,
                name="Aminolysis with Dimethylamine to Glyoxylamide",
                reactants={
                    "indole_3_glyoxyl_chloride": 1.0,
                    "dimethylamine": 1.0,
                },
                products={
                    "indole_3_dimethylglyoxylamide": 1.0,
                    "HCl_gas": 1.0,
                },
                temperature_target_c=10.0,
                activation_energy_kj_mol=35.0,
                expected_yield_pct=88.0,
                solvent="diethyl_ether",
                fume_hood_required=True,
            ),
            SynthesisStep(
                step_number=3,
                name="Bis-Carbonyl LAH Reduction to N,N-DMT",
                reactants={
                    "indole_3_dimethylglyoxylamide": 1.0,
                    "lialh4": 2.0,
                },
                products={
                    "dmt": 1.0,
                    "lialo2": 2.0,
                },
                temperature_target_c=66.0,
                activation_energy_kj_mol=46.0,
                expected_yield_pct=84.0,
                solvent="thf",
                reflux=True,
                inert_atmosphere=True,
                description="Exothermic hydride reduction of both carbonyl functions to ethylene bridge.",
                is_closed_system=False,
                balance_note=(
                    "Abbreviated process boundary: hydrolysis/workup species and inorganic "
                    "hydride products are not represented as a closed reaction equation."
                ),
            ),
        ),
    ),
}


# =============================================================================
# 3. Graphics Bridge Parameters (Beer-Lambert, Bubbles, Stokes Settling)
# =============================================================================


def calculate_beer_lambert_absorption(
    extinction_coefficient_m_cm: float,
    concentration_molar: float,
    path_length_cm: float = 1.0,
) -> tuple[float, float]:
    """
    Computes optical absorbance A and transmission fraction T via Beer-Lambert Law:
      A = epsilon * c * l
      T = 10^(-A)
    Used by the rendering shader to modulate transmission alpha and volumetric color.
    """
    if concentration_molar <= 0.0 or extinction_coefficient_m_cm <= 0.0 or path_length_cm <= 0.0:
        return 0.0, 1.0

    absorbance = extinction_coefficient_m_cm * concentration_molar * path_length_cm
    # Guard against exponent overflow in transmission
    transmission = math.pow(10.0, -min(absorbance, 50.0))
    return absorbance, transmission


def calculate_stokes_settling_velocity(
    particle_radius_m: float,
    particle_density_kg_m3: float,
    fluid_density_kg_m3: float = 1000.0,
    fluid_viscosity_pa_s: float = 0.001,  # water at 20 C ~ 1 mPa*s
    gravity_m_s2: float = 9.80665,
) -> float:
    """
    Terminal settling velocity of suspension particles via Stokes' Law:
      v = (2 * r^2 * (rho_p - rho_f) * g) / (9 * eta)
    Used for sediment layer accumulation and particle descent VFX.
    """
    if particle_radius_m <= 0.0 or fluid_viscosity_pa_s <= 0.0:
        return 0.0

    delta_rho = particle_density_kg_m3 - fluid_density_kg_m3
    if delta_rho <= 0.0:
        return 0.0  # particles float or remain buoyant

    v_settle = (2.0 * (particle_radius_m**2) * delta_rho * gravity_m_s2) / (
        9.0 * fluid_viscosity_pa_s
    )
    return max(0.0, v_settle)


def calculate_gas_bubble_emission_rate(
    gas_generation_moles_per_sec: float,
    temperature_k: float = 298.15,
    pressure_pa: float = 101325.0,
    bubble_volume_ml: float = 0.05,
) -> float:
    """
    Calculates bubble emission rate (bubbles/second) via Ideal Gas Law:
      V_dot = (n_dot * R * T) / P
      rate = V_dot / V_bubble
    """
    if gas_generation_moles_per_sec <= 0.0:
        return 0.0

    r_gas = 8.314462618
    volume_m3_per_sec = (gas_generation_moles_per_sec * r_gas * temperature_k) / pressure_pa
    volume_ml_per_sec = volume_m3_per_sec * 1.0e6
    return max(0.0, volume_ml_per_sec / max(bubble_volume_ml, 1e-4))


# =============================================================================
# 4. Literature Catalog Facade
# =============================================================================


class LiteratureCatalog:
    """Central interface for PiHKAL and TiHKAL reaction pathways and thermodynamics."""

    def __init__(self) -> None:
        self._species = dict(PIHKAL_TIHKAL_SPECIES)
        self._routes = dict(LITERATURE_ROUTES)

    def get_species(self, species_id: str) -> LiteratureSpecies:
        sid = species_id.strip()
        if sid not in self._species:
            raise KeyError(f"Literature species '{species_id}' not found.")
        return self._species[sid]

    def has_species(self, species_id: str) -> bool:
        return species_id.strip() in self._species

    def get_route(self, route_id: str) -> LiteratureSynthesisRoute:
        rid = route_id.strip()
        if rid not in self._routes:
            raise KeyError(f"Synthesis route '{route_id}' not found.")
        return self._routes[rid]

    def get_all_synthesis_routes(self) -> list[LiteratureSynthesisRoute]:
        return list(self._routes.values())

    def list_routes_for_compound(self, compound_id: str) -> list[LiteratureSynthesisRoute]:
        cid = compound_id.lower().strip()
        return [r for r in self._routes.values() if r.compound_id == cid]
