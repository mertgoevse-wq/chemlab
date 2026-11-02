"""
Unit and integration tests for the Cantera Thermodynamics and Kinetics Engine.
Validates enthalpy, entropy, Gibbs energy, Arrhenius kinetics, and titration curves.
"""

import pytest

from chemlab.simulation.cantera_engine import THERMO_ENGINE, CanteraThermodynamicsEngine


def test_cantera_engine_singleton_exists():
    assert isinstance(THERMO_ENGINE, CanteraThermodynamicsEngine)
    assert THERMO_ENGINE.get_species("H2O") is not None
    assert THERMO_ENGINE.get_species("aspirin") is not None


def test_neutralization_thermodynamics_exothermic():
    """HCl + NaOH -> NaCl + H2O is strongly exothermic."""
    reactants = {"HCl_aq": 1.0, "NaOH_aq": 1.0}
    products = {"NaCl_aq": 1.0, "H2O": 1.0}

    result = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants,
        products=products,
        temperature_c=25.0,
        activation_energy_kj_mol=15.0,
    )

    assert result.is_exothermic is True
    assert result.delta_h_kj_mol < -50.0  # Approx -56 kJ/mol
    assert result.is_spontaneous is True
    assert result.delta_g_kj_mol < 0.0
    assert result.equilibrium_constant_k_eq > 1.0e5
    assert result.rate_constant_k > 0.0


def test_aspirin_synthesis_thermodynamics():
    """Salicylic acid + Acetic anhydride -> Aspirin + Acetic acid."""
    reactants = {"salicylic_acid": 1.0, "acetic_anhydride": 1.0}
    products = {"aspirin": 1.0, "acetic_acid": 1.0}

    # At room temperature (25°C), reaction is exothermic and spontaneous
    result_rt = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants,
        products=products,
        temperature_c=25.0,
        activation_energy_kj_mol=65.0,
    )
    assert result_rt.is_exothermic is True
    assert result_rt.is_spontaneous is True
    assert result_rt.delta_g_kj_mol < 0.0

    # At elevated temperature (85°C), entropy term (-T*ΔS) raises ΔG
    result_hot = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants,
        products=products,
        temperature_c=85.0,
        activation_energy_kj_mol=65.0,
    )
    assert result_hot.is_exothermic is True
    assert result_hot.temperature_k == 358.15
    assert result_hot.rate_constant_k > result_rt.rate_constant_k
    assert (
        result_hot.equation == "1 salicylic_acid + 1 acetic_anhydride -> 1 aspirin + 1 acetic_acid"
    )


def test_arrhenius_kinetics_temperature_acceleration():
    """Reaction rate must accelerate with higher temperature."""
    reactants = {"salicylic_acid": 1.0, "acetic_anhydride": 1.0}
    products = {"aspirin": 1.0, "acetic_acid": 1.0}

    res_room = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants, products=products, temperature_c=20.0
    )
    res_hot = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants, products=products, temperature_c=80.0
    )

    assert res_hot.rate_constant_k > res_room.rate_constant_k * 5.0


def test_titration_curve_generation():
    """Titration of 0.1 M acetic acid with 0.1 M NaOH."""
    curve = THERMO_ENGINE.calculate_titration_curve(
        analyte_conc_m=0.1,
        analyte_vol_ml=25.0,
        titrant_conc_m=0.1,
        pka=4.76,
        points=20,
    )

    assert len(curve) == 21
    # Initial pH of 0.1 M acetic acid is around 2.87
    v0, ph0 = curve[0]
    assert v0 == 0.0
    assert 2.5 <= ph0 <= 3.2

    # Equivalence point is at 25.0 ml -> pH should be mildly basic (> 7.0)
    equiv_points = [p for v, p in curve if 24.0 <= v <= 26.0]
    assert any(p > 7.0 for p in equiv_points)

    # Excess titrant pH should approach 12+
    v_end, ph_end = curve[-1]
    assert ph_end >= 11.5


def test_acetanilide_synthesis_thermodynamics():
    """Aniline + Acetic anhydride -> Acetanilide + Acetic acid."""
    reactants = {"aniline": 1.0, "acetic_anhydride": 1.0}
    products = {"acetanilide": 1.0, "acetic_acid": 1.0}

    result = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants,
        products=products,
        temperature_c=25.0,
        activation_energy_kj_mol=45.0,
    )
    assert result.is_exothermic is True
    assert result.delta_h_kj_mol < -50.0  # Strongly exothermic
    assert result.is_spontaneous is True
    assert result.rate_constant_k > 0.0


def test_bicarbonate_gas_evolution_thermodynamics():
    """NaHCO3 + HCl -> NaCl + H2O + CO2(g)"""
    reactants = {"sodium_bicarbonate": 1.0, "HCl_aq": 1.0}
    products = {"NaCl_aq": 1.0, "H2O": 1.0, "CO2_gas": 1.0}

    result = THERMO_ENGINE.calculate_reaction_thermodynamics(
        reactants=reactants,
        products=products,
        temperature_c=25.0,
    )
    # Gas evolution creates high positive entropy (ΔS > 0)
    assert result.delta_s_j_mol_k > 0.0
    assert result.is_spontaneous is True


def test_expanded_species_availability():
    """Validates existence of key laboratory reagents in the thermodynamic database."""
    species_to_check = [
        "toluene",
        "benzene",
        "diethyl_ether",
        "dichloromethane",
        "luminol",
        "caffeine",
        "silver_nitrate",
        "sodium_carbonate",
    ]
    for s in species_to_check:
        spec = THERMO_ENGINE.get_species(s)
        assert spec is not None
        assert spec.formula != ""
        assert spec.molecular_weight_g_mol > 0.0
