"""
Unit tests for Authentic Total Syntheses & Pharmaceutical Reaction Protocols.
Tests Aspirin, Paracetamol, Caffeine, Indigo Dye, and Benzocaine synthesis recipes,
stoichiometric calculations, multi-stage yields, and recrystallization.
"""

from __future__ import annotations

import pytest

from chemlab.simulation.total_syntheses import (
    SynthesisProtocol,
    SynthesisRegistry,
    SynthesisStage,
)


def test_synthesis_registry_contains_pharmaceuticals() -> None:
    registry = SynthesisRegistry()
    recipes = registry.list_available_protocols()
    expected = ["aspirin", "paracetamol", "caffeine_extraction", "indigo_dye", "benzocaine"]
    for exp in expected:
        assert exp in recipes, f"Missing expected recipe: {exp}"


def test_aspirin_synthesis_protocol_structure() -> None:
    registry = SynthesisRegistry()
    aspirin = registry.get_protocol("aspirin")
    assert aspirin.target_molecule == "Acetylsalicylsäure (Aspirin)"
    assert aspirin.cas_number == "50-78-2"
    assert len(aspirin.stages) >= 3  # Acylation, Quenching, Recrystallization
    assert "salicylic_acid" in aspirin.initial_reagents
    assert "acetic_anhydride" in aspirin.initial_reagents
    assert "h2so4" in aspirin.catalysts


def test_paracetamol_stoichiometry_and_yield() -> None:
    registry = SynthesisRegistry()
    paracetamol = registry.get_protocol("paracetamol")
    assert paracetamol.theoretical_yield_g(moles_limiting=0.1) == pytest.approx(15.116, rel=1e-2)
    # Stage verification
    stage1 = paracetamol.stages[0]
    assert stage1.temperature_target_c >= 50.0
    assert "aminophenol" in stage1.required_inputs


def test_indigo_dye_color_and_precipitation() -> None:
    registry = SynthesisRegistry()
    indigo = registry.get_protocol("indigo_dye")
    assert indigo.produces_colored_precipitate
    assert indigo.final_color_rgb == (0.08, 0.12, 0.52)  # Deep royal indigo blue


def test_caffeine_extraction_sublimation_temperature() -> None:
    registry = SynthesisRegistry()
    caffeine = registry.get_protocol("caffeine_extraction")
    assert caffeine.sublimation_point_c == pytest.approx(178.0, abs=2.0)
    assert any(s.technique == "sublimation" for s in caffeine.stages)
