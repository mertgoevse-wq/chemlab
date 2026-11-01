"""Tests for Chemlab Cloud Sync and Zero-Credential Security Subsystem.

Verifies OAuth2/MCP token vault, sync journaling, delta synchronization, and conflict resolution.
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.cloud_sync import (
    CloudSyncEngine,
    ConflictResolutionPolicy,
    MockGoogleDriveClient,
    SecureCredentialVault,
)
from storage.local_store import LocalStorageManager


@pytest.fixture
def sync_env():
    """Sets up local store, secure vault, mock drive client, and sync engine in isolated temp directories."""
    with (
        tempfile.TemporaryDirectory() as local_dir,
        tempfile.TemporaryDirectory() as cloud_mock_dir,
    ):
        local_store = LocalStorageManager(data_dir=local_dir)
        vault = SecureCredentialVault(vault_dir=local_dir)
        drive_client = MockGoogleDriveClient(cloud_storage_root=cloud_mock_dir)
        sync_engine = CloudSyncEngine(
            local_store=local_store,
            credential_vault=vault,
            cloud_client=drive_client,
        )
        yield {
            "local_store": local_store,
            "vault": vault,
            "drive_client": drive_client,
            "sync_engine": sync_engine,
        }
        local_store.close()


def test_zero_credential_token_vault(sync_env):
    """Test that authentication uses secure token storage and rejects raw plaintext passwords."""
    vault = sync_env["vault"]

    token_data = {
        "access_token": "ya29.a0AfH6SMD_mock_access_token",
        "refresh_token": "1//04_mock_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/drive.appdata",
    }

    vault.store_oauth_tokens("google_drive", token_data)
    assert vault.has_valid_token("google_drive") is True

    retrieved = vault.get_oauth_tokens("google_drive")
    assert retrieved["access_token"] == token_data["access_token"]
    assert retrieved["refresh_token"] == token_data["refresh_token"]

    with pytest.raises(ValueError, match="Raw passwords are prohibited"):
        vault.store_raw_password("user@gmail.com", "PlainPassword123!")


def test_offline_sync_journaling(sync_env):
    """Test that local mutations create sync journal entries while offline."""
    store = sync_env["local_store"]
    sync_engine = sync_env["sync_engine"]

    store.create_player_profile("player_001", "CurieLab", "hash123")
    store.record_level_completion("player_001", "lvl_1", 8500, 3, 45.0, 0.95)

    journal_entries = sync_engine.get_pending_journal_entries()
    assert len(journal_entries) >= 2

    entity_types = [e["entity_type"] for e in journal_entries]
    assert "player_profiles" in entity_types
    assert "unlocked_levels" in entity_types


def test_delta_sync_push_and_pull(sync_env):
    """Test packaging delta changes, pushing to cloud, and pulling updates."""
    store = sync_env["local_store"]
    sync_engine = sync_env["sync_engine"]
    drive_client = sync_env["drive_client"]

    store.create_player_profile("player_001", "CurieLab", "hash123")
    recipe = {
        "recipe_id": "rec_001",
        "player_id": "player_001",
        "name": "Oscillating Clock",
        "formula": "IO3- + H2O2 -> I2",
        "reactants": [{"name": "Hydrogen Peroxide", "concentration": 0.1}],
        "kinetics": {"rate": 0.05},
        "thermodynamics": {},
        "safety_notes": "Mild oxidant.",
    }
    store.save_reaction_recipe(recipe)

    result = sync_engine.sync_up()
    assert result["status"] == "success"
    assert result["pushed_count"] >= 2

    assert drive_client.has_file("chemlab_sync_player_001.json")
    assert len(sync_engine.get_pending_journal_entries()) == 0


def test_conflict_resolution_three_way_merge(sync_env):
    """Test resolving conflicts between local changes and cloud changes using intelligent merge."""
    store = sync_env["local_store"]
    sync_engine = sync_env["sync_engine"]

    store.create_player_profile("player_001", "CurieLab", "hash123", settings={"volume": 0.7})
    store.record_level_completion(
        "player_001", "lvl_1", score=8000, stars=2, best_time_seconds=50.0, reaction_accuracy=0.9
    )

    cloud_payload = {
        "player_profiles": [
            {
                "player_id": "player_001",
                "username": "CurieLab",
                "experience_points": 2000,
                "level": 2,
                "settings": {"volume": 0.9},
            }
        ],
        "unlocked_levels": [
            {
                "player_id": "player_001",
                "level_id": "lvl_1",
                "score": 9500,
                "stars": 3,
                "best_time_seconds": 40.0,
                "reaction_accuracy": 0.98,
            },
            {
                "player_id": "player_001",
                "level_id": "lvl_2",
                "score": 7200,
                "stars": 2,
                "best_time_seconds": 65.0,
                "reaction_accuracy": 0.88,
            },
        ],
        "custom_reaction_recipes": [],
        "saved_experiments": [],
    }

    merged = sync_engine.resolve_conflicts(
        remote_data=cloud_payload,
        policy=ConflictResolutionPolicy.THREE_WAY_MERGE,
    )

    assert merged["status"] == "resolved"
    lvl_1 = store.get_unlocked_levels("player_001")
    lvl_1_map = {lvl_record["level_id"]: lvl_record for lvl_record in lvl_1}
    assert lvl_1_map["lvl_1"]["score"] == 9500
    assert "lvl_2" in lvl_1_map
    assert lvl_1_map["lvl_2"]["score"] == 7200
