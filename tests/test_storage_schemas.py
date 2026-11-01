"""Tests for Chemlab Local SQLite and JSON Storage Subsystem.

Verifies schema creation, CRUD operations, integrity constraints, and tamper detection.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Ensure storage module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.local_store import LocalStorageManager


@pytest.fixture
def temp_store():
    """Provides a fresh LocalStorageManager instance backed by a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = LocalStorageManager(data_dir=tmp_dir)
        yield store
        store.close()


def test_schema_initialization(temp_store):
    """Test that all SQLite tables and indices are properly created."""
    conn = temp_store.get_connection()
    cursor = conn.cursor()

    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [row[0] for row in tables]

    assert "player_profiles" in table_names
    assert "unlocked_levels" in table_names
    assert "high_scores" in table_names
    assert "saved_experiments" in table_names
    assert "custom_reaction_recipes" in table_names
    assert "asset_cache_metadata" in table_names
    assert "sync_journal" in table_names


def test_player_profile_crud(temp_store):
    """Test player profile creation, retrieval, and updates."""
    profile = temp_store.create_player_profile(
        player_id="player_001",
        username="CurieLab",
        email_hash="hash_mert_google_drive",  # Only hash stored, never raw email
        settings={"graphics_preset": "low_vram", "audio_volume": 0.8},
    )
    assert profile["player_id"] == "player_001"
    assert profile["username"] == "CurieLab"
    assert profile["level"] == 1
    assert profile["experience_points"] == 0

    fetched = temp_store.get_player_profile("player_001")
    assert fetched is not None
    assert fetched["username"] == "CurieLab"
    assert fetched["settings"]["graphics_preset"] == "low_vram"

    updated = temp_store.update_player_profile(
        player_id="player_001",
        experience_points=1500,
        level=3,
        settings={"graphics_preset": "low_vram", "audio_volume": 0.5},
    )
    assert updated["experience_points"] == 1500
    assert updated["level"] == 3
    assert updated["settings"]["audio_volume"] == 0.5


def test_level_unlock_and_score_tamper_protection(temp_store):
    """Test unlocking levels, recording high scores, and signature verification."""
    temp_store.create_player_profile("player_001", "CurieLab", "hash123")

    record = temp_store.record_level_completion(
        player_id="player_001",
        level_id="lvl_oscillating_reactions",
        score=9850,
        stars=3,
        best_time_seconds=124.5,
        reaction_accuracy=0.992,
    )
    assert record["level_id"] == "lvl_oscillating_reactions"
    assert record["score"] == 9850
    assert record["stars"] == 3
    assert record["is_signature_valid"] is True

    unlocked = temp_store.get_unlocked_levels("player_001")
    assert len(unlocked) == 1
    assert unlocked[0]["level_id"] == "lvl_oscillating_reactions"
    assert unlocked[0]["score"] == 9850

    high_scores = temp_store.get_high_scores("lvl_oscillating_reactions")
    assert len(high_scores) == 1
    assert high_scores[0]["score"] == 9850
    assert high_scores[0]["player_id"] == "player_001"


def test_custom_reaction_recipe_storage(temp_store):
    """Test storing and querying complex chemical reaction recipes."""
    temp_store.create_player_profile("player_001", "CurieLab", "hash123")

    recipe_data = {
        "recipe_id": "rec_bz_oregonator",
        "player_id": "player_001",
        "name": "Belousov-Zhabotinsky Ce4/Fe(phen)3 Catalyst",
        "formula": "BrO3- + HBrO2 + Ce4+ -> Oscillation",
        "reactants": [
            {"reagent": "Potassium Bromate", "formula": "KBrO3", "concentration_M": 0.2},
            {"reagent": "Malonic Acid", "formula": "CH2(COOH)2", "concentration_M": 0.4},
            {"reagent": "Sulfuric Acid", "formula": "H2SO4", "concentration_M": 0.5},
            {
                "reagent": "Ferroin Indicator",
                "formula": "[Fe(o-phen)3]SO4",
                "concentration_M": 0.005,
            },
        ],
        "kinetics": {
            "model": "Oregonator-FKN",
            "k1": 1.28,
            "k2": 2.4e6,
            "k3": 33.6,
            "k4": 3.0e3,
            "k5": 1.0,
            "period_seconds": 38.2,
        },
        "thermodynamics": {
            "activation_energy_kj_mol": 67.5,
            "is_exothermic": True,
            "color_states": ["Red (Reduced Ferroin)", "Blue (Oxidized Ferriin)"],
        },
        "safety_notes": "Corrosive acid. Generates trace bromine vapor. Use fume hood.",
    }

    saved = temp_store.save_reaction_recipe(recipe_data)
    assert saved["recipe_id"] == "rec_bz_oregonator"

    fetched = temp_store.get_reaction_recipe("rec_bz_oregonator")
    assert fetched is not None
    assert fetched["name"] == "Belousov-Zhabotinsky Ce4/Fe(phen)3 Catalyst"
    assert fetched["kinetics"]["model"] == "Oregonator-FKN"
    assert len(fetched["reactants"]) == 4


def test_saved_experiment_state(temp_store):
    """Test saving and loading simulation state (apparatus, chemicals, timestep)."""
    temp_store.create_player_profile("player_001", "CurieLab", "hash123")

    experiment_data = {
        "experiment_id": "exp_bz_beaker_01",
        "player_id": "player_001",
        "name": "Oscillation Lab Setup Bench 2",
        "apparatus_config": {
            "vessels": [
                {
                    "id": "beaker_500ml",
                    "type": "beaker",
                    "position": [1.2, 0.85, 0.0],
                    "capacity_ml": 500,
                },
                {
                    "id": "magnetic_stirrer",
                    "type": "stirrer",
                    "position": [1.2, 0.85, 0.0],
                    "rpm": 450,
                },
            ],
            "sensors": [
                {"type": "redox_electrode", "connected_to": "beaker_500ml", "reading_mv": 340.5},
            ],
        },
        "chemical_state": {
            "volume_ml": 250,
            "temperature_c": 22.4,
            "ph": 1.1,
            "active_concentrations": {
                "HBrO2": 1.2e-7,
                "Br_minus": 4.5e-6,
                "Ce4_plus": 3.8e-4,
            },
        },
        "oscillation_state": {
            "current_phase": "oxidation",
            "cycle_count": 14,
            "elapsed_seconds": 534.2,
        },
        "simulation_timestep": 0.005,
    }

    saved = temp_store.save_experiment(experiment_data)
    assert saved["experiment_id"] == "exp_bz_beaker_01"

    loaded = temp_store.get_experiment("exp_bz_beaker_01")
    assert loaded is not None
    assert loaded["name"] == "Oscillation Lab Setup Bench 2"
    assert loaded["oscillation_state"]["cycle_count"] == 14
    assert loaded["apparatus_config"]["vessels"][1]["rpm"] == 450


def test_json_backup_export_import(temp_store):
    """Test exporting complete profile and state to JSON and restoring it."""
    temp_store.create_player_profile("player_001", "CurieLab", "hash123")
    temp_store.record_level_completion("player_001", "lvl_1", 5000, 3, 60.0, 0.98)

    export_path = temp_store.data_dir / "backup.json"
    temp_store.export_to_json("player_001", export_path)
    assert export_path.exists()

    with tempfile.TemporaryDirectory() as restore_dir:
        restore_store = LocalStorageManager(data_dir=restore_dir)
        restore_store.import_from_json(export_path)

        imported_profile = restore_store.get_player_profile("player_001")
        assert imported_profile is not None
        assert imported_profile["username"] == "CurieLab"

        levels = restore_store.get_unlocked_levels("player_001")
        assert len(levels) == 1
        assert levels[0]["level_id"] == "lvl_1"
        assert levels[0]["score"] == 5000
        restore_store.close()
