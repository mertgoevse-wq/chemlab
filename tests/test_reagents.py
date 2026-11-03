"""
Tests for the consolidated ChemLab chemical reagent database.

Verifies organic & inorganic substances, physical & chemical properties,
particle/color data, GHS hazards, and lookup by ID / formula / CAS number.
"""

import pytest

from chemlab.simulation.reagents import (
    Reagent,
    ReagentCategory,
    REAGENT_REGISTRY,
    get_reagent,
    list_reagents,
    search_by_formula,
    search_by_category,
)


def test_registry_contains_inorganic_and_organic_substances():
    """The registry must span both inorganic and organic chemical space."""
    ids = set(REAGENT_REGISTRY.keys())
    # Inorganic classics
    assert "water" in ids
    assert "hcl" in ids
    assert "naoh" in ids
    # Organic building blocks
    assert "malonic_acid" in ids
    assert "salicylic_acid" in ids
    assert "ethanol" in ids


def test_reagent_properties_are_authentic():
    """Physical properties must be populated with real-world values."""
    water = get_reagent("water")
    assert water.formula == "H2O"
    assert pytest.approx(water.molar_mass_g_per_mol, rel=1e-2) == 18.015
    assert pytest.approx(water.density_g_per_ml, rel=1e-2) == 1.0
    assert pytest.approx(water.ph, abs=0.5) == 7.0

    hcl = get_reagent("hcl")
    assert hcl.formula == "HCl"
    assert hcl.ph < 2.0  # Strong acid


def test_ghs_hazards_are_assigned():
    """Every hazardous reagent carries GHS pictogram and statement data."""
    hcl = get_reagent("hcl")
    assert len(hcl.ghs_pictograms) > 0
    assert len(hcl.hazard_statements) > 0
    assert hcl.storage_note != ""

    # Water is benign: no mandatory GHS pictograms
    water = get_reagent("water")
    assert water.ghs_pictograms == ()


def test_particle_and_color_data_present():
    """Each reagent must carry particle type and RGB color for rendering."""
    for reagent in REAGENT_REGISTRY.values():
        assert reagent.default_color_rgba is not None
        assert len(reagent.default_color_rgba) == 4  # RGBA
        assert all(0.0 <= c <= 1.0 for c in reagent.default_color_rgba[:3])
        assert reagent.particle_type is not None
        assert reagent.particle_type != ""


def test_lookup_by_id_case_insensitive():
    """Lookup by reagent ID must be case-insensitive and whitespace-tolerant."""
    assert get_reagent("HCL") == get_reagent("hcl")
    assert get_reagent("  NaOH  ") == get_reagent("naoh")


def test_lookup_unknown_reagent_raises():
    """Requesting an unknown reagent must raise KeyError."""
    with pytest.raises(KeyError):
        get_reagent("definitely_not_a_chemical")


def test_search_by_formula():
    """Searching by molecular formula must return matching reagents."""
    results = search_by_formula("H2O")
    assert any(r.id == "water" for r in results)

    results = search_by_formula("NaCl")
    assert any("sodium_chloride" in r.id or "nacl" in r.id for r in results)


def test_search_by_category():
    """Category search must return only reagents of that class."""
    acids = search_by_category(ReagentCategory.ACID)
    assert all(r.category == ReagentCategory.ACID for r in acids)
    assert any(r.id == "hcl" for r in acids)

    bases = search_by_category(ReagentCategory.BASE)
    assert all(r.category == ReagentCategory.BASE for r in bases)
    assert any(r.id == "naoh" for r in bases)


def test_list_reagents_returns_all():
    """list_reagents must return every registered entry."""
    all_reagents = list_reagents()
    assert len(all_reagents) == len(REAGENT_REGISTRY)
    assert all(isinstance(r, Reagent) for r in all_reagents)


def test_organic_reagents_have_cas_numbers():
    """Organic substances relevant to synthesis must carry CAS registry numbers."""
    salicylic = get_reagent("salicylic_acid")
    assert salicylic.cas_number is not None
    assert salicylic.cas_number != ""

    ethanol = get_reagent("ethanol")
    assert ethanol.cas_number is not None
