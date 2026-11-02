"""
Unit tests for the Worldwide Laboratory Taxonomy & Equipment Registry.
"""

import pytest

from chemlab.world.lab_taxonomy import (
    EQUIPMENT_CATALOG,
    LAB_REGISTRY,
    LABORATORY_ARCHETYPES,
    GlobalLabRegistry,
    SafetyContainmentLevel,
)


def test_lab_registry_singleton():
    assert isinstance(LAB_REGISTRY, GlobalLabRegistry)
    assert len(LAB_REGISTRY.list_all_archetypes()) >= 5


def test_academic_organic_lab_specifications():
    lab = LAB_REGISTRY.get_archetype("academic_organic")
    assert lab is not None
    assert lab.containment_level == SafetyContainmentLevel.CONTROLLED_CLASS_2
    assert "salicylic_acid" in lab.reagent_palette
    assert any(eq.item_id == "rotavapor_chiller" for eq in lab.key_equipment)


def test_clandestine_improvised_lab_specifications():
    lab = LAB_REGISTRY.get_archetype("clandestine_improvised")
    assert lab is not None
    assert lab.containment_level == SafetyContainmentLevel.IMPROVISED_UNREGULATED
    assert any("Runaway" in h for h in lab.hazard_profile)
    assert any(eq.item_id == "makeshift_heating_mantle" for eq in lab.key_equipment)


def test_equipment_catalog_specifications():
    nmr = LAB_REGISTRY.get_equipment("nmr_400mhz")
    assert nmr is not None
    assert nmr.power_watts > 1000.0
    assert "Superconducting" in nmr.name
    assert "nuclear magnetic resonance" in nmr.description
