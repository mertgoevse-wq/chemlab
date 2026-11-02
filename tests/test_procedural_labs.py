"""
Unit tests for ChemLab Procedural Open-World Laboratory Matrix.
Tests procedural lab generation across clandestine underground, industrial pharma,
CRISPR biotech, academic, orbital, and planetary archetypes, along with resident NPCs,
dynamic quest generation, starting lab selection, and environmental synchronization.
"""

from __future__ import annotations

import pytest

from chemlab.sandbox.no_mans_sky_matrix import HazardDifficulty, LaboratoryEnvironmentMatrix
from chemlab.world.procedural_labs import (
    LabEquipment,
    LabNPC,
    LabQuest,
    LabQuestObjective,
    LabType,
    NPCRole,
    ProceduralLab,
    ProceduralLabGenerator,
    QuestCategory,
    WorldMatrixHub,
)


def test_lab_type_enumeration() -> None:
    """Verifies that all requested laboratory archetypes are supported."""
    assert LabType.CLANDESTINE_UNDERGROUND.value == "clandestine_underground"
    assert LabType.INDUSTRIAL_PHARMA.value == "industrial_pharma"
    assert LabType.CRISPR_BIOTECH.value == "crispr_biotech"
    assert LabType.ACADEMIC_RESEARCH.value == "academic_research"
    assert LabType.ORBITAL_ZERO_G.value == "orbital_zero_g"
    assert LabType.EXTREME_PLANETARY.value == "extreme_planetary"


def test_procedural_lab_generator_seed_reproducibility() -> None:
    """Tests that identical seeds produce identical procedural laboratories."""
    gen1 = ProceduralLabGenerator(seed=42)
    gen2 = ProceduralLabGenerator(seed=42)

    lab1 = gen1.generate_lab(LabType.CLANDESTINE_UNDERGROUND)
    lab2 = gen2.generate_lab(LabType.CLANDESTINE_UNDERGROUND)

    assert lab1.name == lab2.name
    assert lab1.room_count == lab2.room_count
    assert len(lab1.equipment) == len(lab2.equipment)
    assert len(lab1.npcs) == len(lab2.npcs)
    assert len(lab1.quests) == len(lab2.quests)


def test_clandestine_underground_lab_characteristics() -> None:
    """Tests generation and specific features of clandestine underground labs."""
    generator = ProceduralLabGenerator(seed=101)
    lab = generator.generate_lab(LabType.CLANDESTINE_UNDERGROUND)

    assert lab.lab_type == LabType.CLANDESTINE_UNDERGROUND
    assert lab.security_level in ("clandestine_covert", "improvised", "reinforced_bunker")
    assert any(
        "fume" in eq.name.lower() or "abzug" in eq.name.lower() or "improvised" in eq.name.lower()
        for eq in lab.equipment
    )
    # Underground labs should have NPCs with clandestine roles
    assert any(
        npc.role in (NPCRole.COVERT_OPERATOR, NPCRole.CONTRABAND_CHEMIST, NPCRole.FACILITY_FIXER)
        for npc in lab.npcs
    )
    # Quests should reflect underground themes
    assert any(q.category == QuestCategory.COVERT_SYNTHESIS for q in lab.quests)


def test_industrial_pharma_lab_characteristics() -> None:
    """Tests generation and features of industrial GMP pharma laboratories."""
    generator = ProceduralLabGenerator(seed=202)
    lab = generator.generate_lab(LabType.INDUSTRIAL_PHARMA)

    assert lab.lab_type == LabType.INDUSTRIAL_PHARMA
    assert lab.gmp_certified
    # Equipment must include analytical validation gear
    equipment_names = [e.name.lower() for e in lab.equipment]
    assert any(
        "hplc" in name or "chromatograph" in name or "spektrometer" in name or "reaktor" in name
        for name in equipment_names
    )
    # Quests should require high analytical purity
    assert any(q.category == QuestCategory.GMP_VALIDATION for q in lab.quests)


def test_crispr_biotech_lab_characteristics() -> None:
    """Tests generation of CRISPR genetic editing biotechnology facilities."""
    generator = ProceduralLabGenerator(seed=303)
    lab = generator.generate_lab(LabType.CRISPR_BIOTECH)

    assert lab.lab_type == LabType.CRISPR_BIOTECH
    assert lab.biosafety_level in (2, 3)
    equipment_names = [e.name.lower() for e in lab.equipment]
    assert any(
        "pcr" in name or "sequenzer" in name or "flow" in name or "incubator" in name
        for name in equipment_names
    )
    # Genetic research quests
    assert any(q.category == QuestCategory.GENETIC_ENGINEERING for q in lab.quests)


def test_orbital_zero_g_lab_has_microgravity_environment() -> None:
    """Tests that orbital labs configure 0.0g environmental matrix."""
    generator = ProceduralLabGenerator(seed=404)
    lab = generator.generate_lab(LabType.ORBITAL_ZERO_G)

    assert lab.environment.gravity_g == 0.0
    assert lab.environment.pour_velocity_multiplier == 0.0


def test_npc_dialogue_and_trading() -> None:
    """Tests NPC interaction, dialogue retrieval, and reagent trading."""
    npc = LabNPC(
        npc_id="npc_walter_01",
        name="Walter Blackwood",
        role=NPCRole.CONTRABAND_CHEMIST,
        reputation=50.0,
        dialog_lines=[
            "Reines Produkt erfordert absolute Geduld, Kollege.",
            "Pass auf die Säuredämpfe auf – mein Abzug zieht nicht mehr richtig.",
        ],
        trade_inventory={"nitroethane": 250.0, "benzaldehyde": 500.0},
    )

    greeting = npc.get_random_dialog()
    assert greeting in npc.dialog_lines

    # Successful trade
    success, msg = npc.buy_reagent("nitroethane", 100.0)
    assert success
    assert npc.trade_inventory["nitroethane"] == 150.0

    # Insufficient stock trade
    fail, fail_msg = npc.buy_reagent("nitroethane", 500.0)
    assert not fail
    assert "Unzureichender Vorrat" in fail_msg


def test_npc_reputation_impacts_dialogue() -> None:
    """Tests reputation tier adjustments for NPCs."""
    npc = LabNPC(
        npc_id="npc_elena_02",
        name="Dr. Elena Vance",
        role=NPCRole.CHIEF_SCIENTIST,
        reputation=25.0,
    )
    assert npc.reputation_tier == "suspicious"

    npc.adjust_reputation(50.0)
    assert npc.reputation == 75.0
    assert npc.reputation_tier == "friendly"

    npc.adjust_reputation(15.0)
    assert npc.reputation == 90.0
    assert npc.reputation_tier == "trusted"


def test_quest_evaluation_success() -> None:
    """Tests validating quest objectives for successful completion."""
    quest = LabQuest(
        quest_id="quest_aspirin_01",
        title="Synthese von Acetylsalicylsäure nach GMP",
        category=QuestCategory.GMP_VALIDATION,
        briefing="Synthetisiere Aspirin mit mindestens 95% Reinheit.",
        objective=LabQuestObjective(
            target_compound="aspirin",
            min_purity_percent=95.0,
            min_yield_grams=10.0,
            requires_fume_hood=True,
        ),
        reward_reputation=15.0,
        reward_credits=500.0,
    )

    assert not quest.completed

    # Submit valid reaction
    success, feedback = quest.evaluate_submission(
        compound="aspirin",
        purity_percent=98.2,
        yield_grams=12.5,
        used_fume_hood=True,
    )

    assert success
    assert quest.completed
    assert "Erfolgreich" in feedback


def test_quest_evaluation_fails_when_unmet_purity() -> None:
    """Tests quest rejection when purity threshold is not met."""
    quest = LabQuest(
        quest_id="quest_aspirin_02",
        title="Reinst-Aspirin",
        category=QuestCategory.GMP_VALIDATION,
        briefing="Aspirin mit 95% Reinheit gefordert.",
        objective=LabQuestObjective(
            target_compound="aspirin",
            min_purity_percent=95.0,
            min_yield_grams=10.0,
        ),
    )

    success, feedback = quest.evaluate_submission(
        compound="aspirin",
        purity_percent=88.0,  # Below 95%
        yield_grams=15.0,
        used_fume_hood=True,
    )

    assert not success
    assert not quest.completed
    assert "Reinheit unzureichend" in feedback


def test_world_matrix_hub_initialization() -> None:
    """Tests WorldMatrixHub creation with player starting lab customization."""
    hub = WorldMatrixHub(player_name="Alchemist_One")
    assert hub.player_lab is None
    assert len(hub.discovered_labs) == 0

    # Player chooses to start in Clandestine Underground Lab
    player_lab = hub.setup_player_starting_lab(LabType.CLANDESTINE_UNDERGROUND, lab_name="Bunker-7")
    assert hub.player_lab is not None
    assert hub.player_lab.lab_type == LabType.CLANDESTINE_UNDERGROUND
    assert hub.player_lab.name == "Bunker-7"
    assert hub.player_lab.lab_id in hub.discovered_labs


def test_world_matrix_hub_generates_neighboring_labs() -> None:
    """Tests procedural population of world with diverse neighboring laboratories."""
    hub = WorldMatrixHub(player_name="Researcher_X")
    hub.setup_player_starting_lab(LabType.INDUSTRIAL_PHARMA)

    neighboring = hub.discover_nearby_labs(count=5)
    assert len(neighboring) == 5
    # Should contain different laboratory types across the open world
    types_present = {lab.lab_type for lab in neighboring}
    assert len(types_present) >= 3


def test_world_matrix_hub_quest_log() -> None:
    """Tests global quest aggregation across all discovered laboratories."""
    hub = WorldMatrixHub(player_name="Novice")
    hub.setup_player_starting_lab(LabType.CRISPR_BIOTECH)
    hub.discover_nearby_labs(count=3)

    all_quests = hub.get_available_world_quests()
    assert len(all_quests) >= 3
    for q in all_quests:
        assert isinstance(q, LabQuest)


def test_environment_matrix_binding_in_procedural_labs() -> None:
    """Tests that environmental matrix propagates correctly into procedural labs."""
    generator = ProceduralLabGenerator(seed=777)
    custom_env = LaboratoryEnvironmentMatrix(
        gravity_g=0.38,  # Mars
        ambient_pressure_atm=0.006,
        ambient_temperature_c=-63.0,
        hazard_difficulty=HazardDifficulty.HARDCORE_REALISTIC,
    )
    lab = generator.generate_lab(LabType.EXTREME_PLANETARY, environment_override=custom_env)

    assert lab.environment.gravity_g == 0.38
    assert lab.environment.ambient_pressure_atm == 0.006
    assert lab.environment.allow_glass_shattering  # hardcore
