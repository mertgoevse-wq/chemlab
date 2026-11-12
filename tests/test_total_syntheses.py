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
        "cocaine_semisynthesis",
        "scopolamine_total_synthesis",
        "triphenylmethanol_grignard",
        "anthracene_diels_alder",
        "belladonna_alkaloid_extraction",
        "scopolamine_datura_isolation",
        "fischer_tetrahydrocarbazole",
        "sandmeyer_chlorobenzene",
        "cannizzaro_benzaldehyde",
        "manske_harmala_extraction",
        "quinine_cinchona_extraction",
        "acetanilide",
        "benzoic_acid_oxidation",
        "aniline_reduction",
        "adipic_acid_oxidation",
        "dibenzalacetone_aldol",
        "benzoin_condensation",
        "benzil_oxidation",
        "benzilic_acid_rearrangement",
        "cinnamic_acid_perkin",
        "luminol",
        "fluorescein",
        "eosin_y",
        "methyl_orange",
        "sudan_i",
        "sulfanilamide",
        "piperine_extraction",
        "limonene_extraction",
        "eugenol_extraction",
        "capsaicin_extraction",
        "nicotine_extraction",
        "morphine_gregory_isolation",
        "salvinorin_a_extraction",
        "mescaline",
        "2c_b",
        "dom",
        "mdma",
        "dmt",
        "5_meo_dmt",
        "psilocin",
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


def test_vogel_extended_organic_syntheses() -> None:
    registry = SynthesisRegistry()
    acetanilide = registry.get_protocol("acetanilide")
    assert acetanilide.cas_number == "103-84-4"
    assert "aniline" in acetanilide.initial_reagents
    assert "acetic_anhydride" in acetanilide.initial_reagents
    assert acetanilide.molar_mass_g_mol == pytest.approx(135.17, rel=1e-3)

    benzoic = registry.get_protocol("benzoic_acid_oxidation")
    assert benzoic.cas_number == "65-85-0"
    assert "toluene" in benzoic.initial_reagents
    assert "potassium_permanganate" in benzoic.initial_reagents

    aniline = registry.get_protocol("aniline_reduction")
    assert aniline.cas_number == "62-53-3"
    assert "nitrobenzene" in aniline.initial_reagents

    adipic = registry.get_protocol("adipic_acid_oxidation")
    assert adipic.cas_number == "124-04-9"
    assert "cyclohexanol" in adipic.initial_reagents

    dba = registry.get_protocol("dibenzalacetone_aldol")
    assert dba.cas_number == "538-58-9"
    assert "benzaldehyde" in dba.initial_reagents
    assert "acetone" in dba.initial_reagents

    benzoin = registry.get_protocol("benzoin_condensation")
    assert benzoin.cas_number == "119-53-9"

    benzil = registry.get_protocol("benzil_oxidation")
    assert benzil.cas_number == "134-81-6"

    benzilic = registry.get_protocol("benzilic_acid_rearrangement")
    assert benzilic.cas_number == "76-93-7"

    cinnamic = registry.get_protocol("cinnamic_acid_perkin")
    assert cinnamic.cas_number == "140-10-3"

    luminol = registry.get_protocol("luminol")
    assert luminol.cas_number == "521-31-3"
    assert luminol.molar_mass_g_mol == pytest.approx(177.16, rel=1e-3)

    fluorescein = registry.get_protocol("fluorescein")
    assert fluorescein.cas_number == "2321-07-5"
    assert "phthalic_anhydride" in fluorescein.initial_reagents
    assert "resorcinol" in fluorescein.initial_reagents

    eosin = registry.get_protocol("eosin_y")
    assert eosin.cas_number == "17372-87-1"

    mo = registry.get_protocol("methyl_orange")
    assert mo.cas_number == "547-58-0"
    assert "sulfanilic_acid" in mo.initial_reagents

    sudan = registry.get_protocol("sudan_i")
    assert sudan.cas_number == "842-07-9"
    assert "aniline" in sudan.initial_reagents

    sulfa = registry.get_protocol("sulfanilamide")
    assert sulfa.cas_number == "63-74-1"


def test_tropane_alkaloid_suite_extensions() -> None:
    registry = SynthesisRegistry()
    cocaine = registry.get_protocol("cocaine_semisynthesis")
    assert cocaine.cas_number == "50-36-2"
    assert cocaine.molar_mass_g_mol == pytest.approx(303.35, rel=1e-3)
    assert len(cocaine.stages) >= 2
    assert "tropinone" in cocaine.initial_reagents

    scopolamine = registry.get_protocol("scopolamine_total_synthesis")
    assert scopolamine.cas_number == "51-34-3"
    assert scopolamine.molar_mass_g_mol == pytest.approx(303.35, rel=1e-3)


def test_natural_product_extractions_extended() -> None:
    registry = SynthesisRegistry()
    piperine = registry.get_protocol("piperine_extraction")
    assert piperine.cas_number == "94-62-2"
    assert "black_pepper" in piperine.initial_reagents

    limonene = registry.get_protocol("limonene_extraction")
    assert limonene.cas_number == "5989-27-5"
    assert "citrus_peel" in limonene.initial_reagents

    eugenol = registry.get_protocol("eugenol_extraction")
    assert eugenol.cas_number == "97-53-0"
    assert "cloves" in eugenol.initial_reagents

    capsaicin = registry.get_protocol("capsaicin_extraction")
    assert capsaicin.cas_number == "404-86-4"

    nicotine = registry.get_protocol("nicotine_extraction")
    assert nicotine.cas_number == "54-11-5"

    morphine = registry.get_protocol("morphine_gregory_isolation")
    assert morphine.cas_number == "57-27-2"

    salvinorin = registry.get_protocol("salvinorin_a_extraction")
    assert salvinorin.cas_number == "83725-44-0"


def test_shulgin_pihkal_and_tihkal_registry_entries() -> None:
    registry = SynthesisRegistry()
    mescaline = registry.get_protocol("mescaline")
    assert mescaline.cas_number == "54-04-1"
    assert mescaline.molar_mass_g_mol == pytest.approx(211.26, rel=1e-3)

    twocb = registry.get_protocol("2c_b")
    assert twocb.cas_number == "66142-81-2"

    dom = registry.get_protocol("dom")
    assert dom.cas_number == "15588-95-1"

    mdma = registry.get_protocol("mdma")
    assert mdma.cas_number == "42542-10-9"

    dmt = registry.get_protocol("dmt")
    assert dmt.cas_number == "61-50-7"
    assert dmt.molar_mass_g_mol == pytest.approx(188.27, rel=1e-3)

    five_meo = registry.get_protocol("5_meo_dmt")
    assert five_meo.cas_number == "1019-45-0"

    psilocin = registry.get_protocol("psilocin")
    assert psilocin.cas_number == "520-53-6"


