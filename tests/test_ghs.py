"""
Unit tests for GHS Hazard Classification, Chemical Profiles, and Incompatibility Engine.
"""

import pytest

from safety_simulation.ghs import (
    CHEMICAL_DATABASE,
    GHSClass,
    GHSPictogram,
    SignalWord,
    StorageGroup,
    check_chemical_compatibility,
    get_chemical_sds,
)


def test_required_ghs_classes_present():
    """Verify that all required GHS classes (Flammable, Corrosive, Toxic, Oxidizing) are represented."""
    flammables = [c for c in CHEMICAL_DATABASE.values() if GHSClass.FLAMMABLE in c.hazard_classes]
    corrosives = [c for c in CHEMICAL_DATABASE.values() if GHSClass.CORROSIVE in c.hazard_classes]
    toxics = [c for c in CHEMICAL_DATABASE.values() if GHSClass.TOXIC in c.hazard_classes]
    oxidizers = [c for c in CHEMICAL_DATABASE.values() if GHSClass.OXIDIZING in c.hazard_classes]

    assert len(flammables) >= 2, (
        "Must have multiple flammable chemicals (acetone, diethyl_ether, ethanol)"
    )
    assert len(corrosives) >= 3, "Must have corrosives (HCl, H2SO4, NaOH, HNO3)"
    assert len(toxics) >= 2, "Must have toxic chemicals (HCl, HNO3, chlorine)"
    assert len(oxidizers) >= 2, "Must have oxidizers (HNO3, KMnO4, H2O2, chlorine)"


def test_antoine_vapor_pressure_calculation():
    """Verify Antoine equation calculations for volatile solvents."""
    acetone = CHEMICAL_DATABASE["acetone"]
    # At 20 C, Antoine should return ~24-26 kPa for acetone
    vp_20 = acetone.calculate_vapor_pressure_kpa(20.0)
    assert 20.0 < vp_20 < 30.0

    # At boiling point (~56 C), vapor pressure should equal atmospheric (~101 kPa)
    vp_boil = acetone.calculate_vapor_pressure_kpa(acetone.boiling_point_c)
    assert 95.0 < vp_boil < 108.0

    # Diethyl ether (BP 34.6 C) should have high vapor pressure at 20 C (> 50 kPa)
    ether = CHEMICAL_DATABASE["diethyl_ether"]
    vp_ether_20 = ether.calculate_vapor_pressure_kpa(20.0)
    assert 50.0 < vp_ether_20 < 70.0


def test_chemical_incompatibility_oxidizer_and_flammable():
    """Verify that mixing an oxidizer with a flammable solvent triggers a CRITICAL incompatibility."""
    res = check_chemical_compatibility("nitric_acid", "acetone")
    assert not res.compatible
    assert res.risk_level == "CRITICAL"
    assert res.reaction_type == "EXPLOSIVE_OXIDATION"
    assert any("blast" in b.lower() or "thermal" in b.lower() for b in res.byproducts)


def test_chemical_incompatibility_acid_and_base():
    """Verify strong acid + strong base violent exothermic reaction detection."""
    res = check_chemical_compatibility("sulfuric_acid", "sodium_hydroxide")
    assert not res.compatible
    assert res.risk_level == "SEVERE"
    assert res.reaction_type == "VIOLENT_EXOTHERMIC_NEUTRALIZATION"


def test_chemical_compatibility_controlled_neutralizer():
    """Verify acid + sodium bicarbonate is recognized as a safe controlled neutralization."""
    res = check_chemical_compatibility("hydrochloric_acid", "sodium_bicarbonate")
    assert res.compatible
    assert res.risk_level == "LOW"
    assert res.reaction_type == "CONTROLLED_NEUTRALIZATION"
    assert "CO2(g)" in res.byproducts


def test_storage_segregation_violation():
    """Verify storage class incompatibility between flammable cabinet and oxidizers."""
    res = check_chemical_compatibility("diethyl_ether", "hydrogen_peroxide")
    assert not res.compatible
    # Ether + H2O2 is either EXPLOSIVE_OXIDATION or STORAGE_SEGREGATION_VIOLATION
    assert res.risk_level in ["CRITICAL", "MODERATE"]


def test_sds_generation():
    """Verify OSHA standard 16-section SDS generation."""
    sds = get_chemical_sds("hydrochloric_acid")
    assert sds["section_1_identification"]["cas_number"] == "7647-01-0"
    assert sds["section_2_hazard_identification"]["signal_word"] == "DANGER"
    assert "CORROSIVE" in sds["section_2_hazard_identification"]["hazard_classes"]
    assert len(sds["section_2_hazard_identification"]["hazard_statements"]) > 0
