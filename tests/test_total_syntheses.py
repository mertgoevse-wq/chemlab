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
    expected = [
        "aspirin",
        "paracetamol",
        "caffeine_extraction",
        "indigo_dye",
        "benzocaine",
        "robinson_tropinone",
        "atropine",
        "triphenylmethanol_grignard",
        "anthracene_diels_alder",
        "belladonna_alkaloid_extraction",
        "scopolamine_datura_isolation",
        "fischer_tetrahydrocarbazole",
        "sandmeyer_chlorobenzene",
        "cannizzaro_benzaldehyde",
        "manske_harmala_extraction",
        "quinine_cinchona_extraction",
    ]
    for exp in expected:
        assert exp in recipes, f"Missing expected recipe: {exp}"


def test_robinson_tropinone_biomimetic_protocol() -> None:
    registry = SynthesisRegistry()
    tropinone = registry.get_protocol("robinson_tropinone")
    assert tropinone.target_molecule == "Tropinon"
    assert tropinone.cas_number == "532-24-1"
    assert tropinone.molar_mass_g_mol == pytest.approx(139.19, rel=1e-3)
    assert "succindialdehyde" in tropinone.initial_reagents
    assert "methylamine_hcl" in tropinone.initial_reagents
    assert "acetonedicarboxylic_acid" in tropinone.initial_reagents
    assert tropinone.theoretical_yield_g(moles_limiting=0.1) == pytest.approx(13.919, rel=1e-2)


def test_atropine_total_synthesis_protocol() -> None:
    registry = SynthesisRegistry()
    atropine = registry.get_protocol("atropine")
    assert atropine.molar_mass_g_mol == pytest.approx(289.37, rel=1e-3)
    assert len(atropine.stages) == 2  # Reduction to Tropine + Esterification
    assert atropine.stages[0].technique == "ice_bath_quenching"
    assert atropine.stages[1].technique == "reflux_heating"


def test_triphenylmethanol_grignard_protocol() -> None:
    registry = SynthesisRegistry()
    grignard = registry.get_protocol("triphenylmethanol_grignard")
    assert grignard.cas_number == "76-84-6"
    assert "bromobenzene" in grignard.initial_reagents
    assert "magnesium_turnings" in grignard.initial_reagents
    assert "benzophenone" in grignard.initial_reagents


def test_anthracene_diels_alder_cycloaddition() -> None:
    registry = SynthesisRegistry()
    da = registry.get_protocol("anthracene_diels_alder")
    assert da.cas_number == "5443-49-2"
    assert "anthracene" in da.initial_reagents
    assert "maleic_anhydride" in da.initial_reagents
    assert da.stages[0].temperature_target_c == pytest.approx(140.0, abs=5.0)


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


def test_belladonna_and_datura_tropane_extractions() -> None:
    registry = SynthesisRegistry()
    bella = registry.get_protocol("belladonna_alkaloid_extraction")
    assert bella.cas_number == "51-55-8"
    assert "belladonna_powder" in bella.initial_reagents
    assert len(bella.stages) == 2

    datura = registry.get_protocol("scopolamine_datura_isolation")
    assert datura.cas_number == "114-49-8"
    assert "datura_leaves" in datura.initial_reagents
    assert datura.molar_mass_g_mol == pytest.approx(438.31, rel=1e-3)


def test_classical_vogel_transformations() -> None:
    registry = SynthesisRegistry()
    fischer = registry.get_protocol("fischer_tetrahydrocarbazole")
    assert fischer.cas_number == "942-01-8"
    assert "phenylhydrazine" in fischer.initial_reagents

    sandmeyer = registry.get_protocol("sandmeyer_chlorobenzene")
    assert sandmeyer.cas_number == "108-90-7"
    assert "sodium_nitrite" in sandmeyer.initial_reagents
    assert sandmeyer.stages[0].temperature_target_c <= 5.0

    cannizzaro = registry.get_protocol("cannizzaro_benzaldehyde")
    assert cannizzaro.cas_number == "100-51-6"
    assert "benzaldehyde" in cannizzaro.initial_reagents


def test_natural_product_alkaloid_fractionations() -> None:
    registry = SynthesisRegistry()
    manske = registry.get_protocol("manske_harmala_extraction")
    assert manske.cas_number == "442-51-3"
    assert "harmala_seeds" in manske.initial_reagents
    assert manske.stages[1].temperature_target_c <= 10.0  # Cold salting-out

    quinine = registry.get_protocol("quinine_cinchona_extraction")
    assert quinine.cas_number == "6119-70-6"
    assert "cinchona_bark" in quinine.initial_reagents
    assert quinine.molar_mass_g_mol == pytest.approx(782.94, rel=1e-3)

