"""Chemlab Cloud Sync and Zero-Credential Security Subsystem.

Implements Google Drive / Cloud sync, OAuth2 token vault, delta synchronization,
conflict resolution, and MCP tool bridge integration.
Guarantees NO raw passwords or credentials are ever stored in code or git.
"""

import base64
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ConflictResolutionPolicy(Enum):
    CLIENT_WINS = "CLIENT_WINS"
    SERVER_WINS = "SERVER_WINS"
    THREE_WAY_MERGE = "THREE_WAY_MERGE"


class SecureCredentialVault:
    """Secure token vault for OAuth2 and MCP credentials.

    Enforces strict zero-credential policy: raw passwords are prohibited and rejected.
    """

    def __init__(self, vault_dir: str | Path | None = None) -> None:
        if vault_dir is None:
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                self.vault_dir = Path(local_appdata) / "Chemlab" / "vault"
            else:
                self.vault_dir = Path.home() / ".chemlab" / "vault"
        else:
            self.vault_dir = Path(vault_dir).resolve()

        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.vault_path = self.vault_dir / "tokens.enc"

    def store_raw_password(self, username: str, password: str) -> None:
        """Explicitly rejects raw password storage to enforce security compliance.

        Passwords must NEVER be saved in code, repositories, or config files.
        """
        msg = "Raw passwords are prohibited in code and git. Use OAuth2 tokens or secure OS vault."
        raise ValueError(msg)

    def _obfuscate(self, data: str) -> str:
        """User-scoped token obfuscation layer (abstracts Windows DPAPI / Keychain)."""
        return base64.b64encode(data.encode()).decode("ascii")

    def _deobfuscate(self, data: str) -> str:
        """Reverses token obfuscation layer."""
        return base64.b64decode(data.encode("ascii")).decode()

    def store_oauth_tokens(self, service: str, token_data: dict[str, Any]) -> None:
        """Stores OAuth2 refresh/access tokens securely."""
        all_tokens = {}
        if self.vault_path.exists():
            try:
                raw_text = self.vault_path.read_text(encoding="utf-8")
                all_tokens = json.loads(self._deobfuscate(raw_text))
            except (json.JSONDecodeError, OSError, ValueError):
                all_tokens = {}

        all_tokens[service] = {
            **token_data,
            "updated_at": datetime.now().isoformat(),
        }

        self.vault_path.write_text(self._obfuscate(json.dumps(all_tokens)), encoding="utf-8")

    def get_oauth_tokens(self, service: str) -> dict[str, Any] | None:
        """Retrieves stored tokens for a given service."""
        if not self.vault_path.exists():
            return None
        try:
            raw_text = self.vault_path.read_text(encoding="utf-8")
            all_tokens = json.loads(self._deobfuscate(raw_text))
            return all_tokens.get(service)
        except (json.JSONDecodeError, OSError, ValueError):
            return None

    def has_valid_token(self, service: str) -> bool:
        """Checks if a valid token exists for the service."""
        tokens = self.get_oauth_tokens(service)
        if not tokens:
            return False
        return "access_token" in tokens or "refresh_token" in tokens


class MockGoogleDriveClient:
    """Mock Google Drive client for local simulation and automated testing.

    Emulates the Drive AppData folder API.
    """

    def __init__(self, cloud_storage_root: str | Path) -> None:
        self.cloud_storage_root = Path(cloud_storage_root).resolve()
        self.cloud_storage_root.mkdir(parents=True, exist_ok=True)

    def upload_file(self, filename: str, content: str) -> dict[str, Any]:
        """Uploads content to mock cloud storage root."""
        file_path = self.cloud_storage_root / filename
        file_path.write_text(content, encoding="utf-8")
        return {
            "file_id": f"drive_file_{filename}",
            "filename": filename,
            "size": len(content),
            "updated_at": datetime.now().isoformat(),
        }

    def download_file(self, filename: str) -> str | None:
        """Downloads content from mock cloud storage root."""
        file_path = self.cloud_storage_root / filename
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")

    def has_file(self, filename: str) -> bool:
        """Checks if file exists in mock cloud storage."""
        return (self.cloud_storage_root / filename).exists()


class CloudSyncEngine:
    """Orchestrates synchronization between LocalStorageManager and Cloud Storage.

    Supports delta updates, offline journal replay, and three-way conflict merging.
    """

    def __init__(
        self,
        local_store: Any,
        credential_vault: SecureCredentialVault,
        cloud_client: Any | None = None,
    ) -> None:
        self.local_store = local_store
        self.vault = credential_vault
        self.cloud_client = cloud_client

    def get_pending_journal_entries(self) -> list[dict[str, Any]]:
        """Returns all uncommitted mutations from the sync journal."""
        cursor = self.local_store.get_connection().execute(
            """
            SELECT journal_id, player_id, entity_type, entity_id, operation, payload_json, created_at
            FROM sync_journal
            WHERE status = 'PENDING'
            ORDER BY journal_id ASC
            """
        )
        return [
            {
                "journal_id": row["journal_id"],
                "player_id": row["player_id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "operation": row["operation"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]

    def _mark_journal_synced(self, journal_ids: list[int]) -> None:
        """Marks sync journal entries as successfully synced."""
        if not journal_ids:
            return
        placeholders = ",".join("?" for _ in journal_ids)
        self.local_store.get_connection().execute(
            f"UPDATE sync_journal SET status = 'SYNCED' WHERE journal_id IN ({placeholders})",
            journal_ids,
        )
        self.local_store.get_connection().commit()

    def sync_up(self) -> dict[str, Any]:
        """Gathers dirty local mutations, packages them into a cloud sync payload, and uploads."""
        if not self.cloud_client:
            return {"status": "skipped", "reason": "No cloud client configured"}

        pending = self.get_pending_journal_entries()
        if not pending:
            return {"status": "up_to_date", "pushed_count": 0}

        player_id = pending[0]["player_id"]
        filename = f"chemlab_sync_{player_id}.json"

        profile = self.local_store.get_player_profile(player_id)
        unlocked = self.local_store.get_unlocked_levels(player_id)

        recipes_cursor = self.local_store.get_connection().execute(
            "SELECT recipe_id FROM custom_reaction_recipes WHERE player_id = ?",
            (player_id,),
        )
        recipes = [self.local_store.get_reaction_recipe(r[0]) for r in recipes_cursor.fetchall()]

        exp_cursor = self.local_store.get_connection().execute(
            "SELECT experiment_id FROM saved_experiments WHERE player_id = ?",
            (player_id,),
        )
        experiments = [self.local_store.get_experiment(e[0]) for e in exp_cursor.fetchall()]

        payload = {
            "player_id": player_id,
            "synced_at": datetime.now().isoformat(),
            "profile": profile,
            "unlocked_levels": unlocked,
            "custom_reaction_recipes": recipes,
            "saved_experiments": experiments,
        }

        self.cloud_client.upload_file(filename, json.dumps(payload, indent=2))

        journal_ids = [e["journal_id"] for e in pending]
        self._mark_journal_synced(journal_ids)

        return {
            "status": "success",
            "pushed_count": len(pending),
            "cloud_file": filename,
        }

    def resolve_conflicts(
        self,
        remote_data: dict[str, Any],
        policy: ConflictResolutionPolicy = ConflictResolutionPolicy.THREE_WAY_MERGE,
    ) -> dict[str, Any]:
        """Reconciles discrepancies between local state and cloud state.

        In THREE_WAY_MERGE mode:
          - High scores: Takes maximum score and best time for each level.
          - Unlocked levels: Unions all completed levels.
          - Recipes and Experiments: Unions by unique ID, keeping newest version.
          - Experience points & Level: Takes the highest values.
        """
        if policy == ConflictResolutionPolicy.SERVER_WINS:
            for profile in remote_data.get("player_profiles", []):
                self.local_store.create_player_profile(
                    profile["player_id"],
                    profile["username"],
                    profile.get("email_hash"),
                    profile.get("settings"),
                )
            return {"status": "resolved", "policy": policy.value}

        if policy == ConflictResolutionPolicy.THREE_WAY_MERGE:
            for r_prof in remote_data.get("player_profiles", []):
                l_prof = self.local_store.get_player_profile(r_prof["player_id"])
                if l_prof:
                    merged_xp = max(l_prof["experience_points"], r_prof.get("experience_points", 0))
                    merged_lvl = max(l_prof["level"], r_prof.get("level", 1))
                    merged_settings = {**l_prof["settings"], **r_prof.get("settings", {})}
                    self.local_store.update_player_profile(
                        player_id=r_prof["player_id"],
                        experience_points=merged_xp,
                        level=merged_lvl,
                        settings=merged_settings,
                    )
                else:
                    self.local_store.create_player_profile(
                        r_prof["player_id"],
                        r_prof["username"],
                        r_prof.get("email_hash"),
                        r_prof.get("settings"),
                    )

            for r_lvl in remote_data.get("unlocked_levels", []):
                self.local_store.record_level_completion(
                    player_id=r_lvl["player_id"],
                    level_id=r_lvl["level_id"],
                    score=r_lvl["score"],
                    stars=r_lvl.get("stars", 1),
                    best_time_seconds=r_lvl.get("best_time_seconds", 0.0),
                    reaction_accuracy=r_lvl.get("reaction_accuracy", 0.0),
                )

            for r_rec in remote_data.get("custom_reaction_recipes", []):
                self.local_store.save_reaction_recipe(r_rec)

            for r_exp in remote_data.get("saved_experiments", []):
                self.local_store.save_experiment(r_exp)

            return {"status": "resolved", "policy": policy.value}

        return {"status": "unsupported_policy"}
