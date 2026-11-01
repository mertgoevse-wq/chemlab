"""Chemlab Local SQLite and JSON Storage Subsystem.

Handles local player profiles, progress, unlocked levels, high scores,
saved experiments, and custom reaction recipes with cryptographic integrity.
"""

import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class LocalStorageManager:
    """Manages local persistent SQLite storage and JSON backups for Chemlab."""

    SECRET_SALT = b"chemlab_tamper_prevention_salt_2026_iris_xe"

    def __init__(self, data_dir: str | Path | None = None) -> None:
        if data_dir is None:
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                self.data_dir = Path(local_appdata) / "Chemlab" / "data"
            else:
                self.data_dir = Path.home() / ".chemlab" / "data"
        else:
            self.data_dir = Path(data_dir).resolve()

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "chemlab_local.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns the active SQLite connection."""
        return self.conn

    def _init_schema(self) -> None:
        """Initializes database schema from schema.sql."""
        schema_file = Path(__file__).resolve().parent / "schema.sql"
        if schema_file.exists():
            schema_sql = schema_file.read_text(encoding="utf-8")
            self.conn.executescript(schema_sql)
            self.conn.commit()

    def _generate_signature(self, payload: str) -> str:
        """Generates HMAC-SHA256 signature to verify progress authenticity."""
        return hmac.new(self.SECRET_SALT, payload.encode(), hashlib.sha256).hexdigest()

    def _record_journal(
        self,
        player_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: dict[str, Any],
    ) -> None:
        """Records an entry in the offline sync journal for cloud sync."""
        self.conn.execute(
            """
            INSERT INTO sync_journal (player_id, entity_type, entity_id, operation, payload_json, status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')
            """,
            (player_id, entity_type, entity_id, operation, json.dumps(payload)),
        )

    # ---------------- Player Profile ----------------

    def create_player_profile(
        self,
        player_id: str,
        username: str,
        email_hash: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Creates a new player profile."""
        settings_json = json.dumps(settings or {})
        now = datetime.now().isoformat()
        self.conn.execute(
            """
            INSERT INTO player_profiles (player_id, username, email_hash, level, experience_points, settings_json, created_at, updated_at, version)
            VALUES (?, ?, ?, 1, 0, ?, ?, ?, 1)
            """,
            (player_id, username, email_hash, settings_json, now, now),
        )
        profile_data = {
            "player_id": player_id,
            "username": username,
            "email_hash": email_hash,
            "level": 1,
            "experience_points": 0,
            "settings": settings or {},
            "version": 1,
        }
        self._record_journal(player_id, "player_profiles", player_id, "INSERT", profile_data)
        self.conn.commit()
        return profile_data

    def get_player_profile(self, player_id: str) -> dict[str, Any] | None:
        """Retrieves a player profile by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM player_profiles WHERE player_id = ?",
            (player_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "player_id": row["player_id"],
            "username": row["username"],
            "email_hash": row["email_hash"],
            "level": row["level"],
            "experience_points": row["experience_points"],
            "settings": json.loads(row["settings_json"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "version": row["version"],
        }

    def update_player_profile(
        self,
        player_id: str,
        experience_points: int | None = None,
        level: int | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Updates progress, stats, and settings for a player profile."""
        existing = self.get_player_profile(player_id)
        if not existing:
            msg = f"Player profile {player_id} not found."
            raise ValueError(msg)

        new_xp = (
            experience_points if experience_points is not None else existing["experience_points"]
        )
        new_level = level if level is not None else existing["level"]
        new_settings = settings if settings is not None else existing["settings"]
        new_version = existing["version"] + 1
        now = datetime.now().isoformat()

        self.conn.execute(
            """
            UPDATE player_profiles
            SET experience_points = ?, level = ?, settings_json = ?, updated_at = ?, version = ?
            WHERE player_id = ?
            """,
            (new_xp, new_level, json.dumps(new_settings), now, new_version, player_id),
        )
        updated_data = {
            "player_id": player_id,
            "username": existing["username"],
            "email_hash": existing["email_hash"],
            "level": new_level,
            "experience_points": new_xp,
            "settings": new_settings,
            "version": new_version,
        }
        self._record_journal(player_id, "player_profiles", player_id, "UPDATE", updated_data)
        self.conn.commit()
        return updated_data

    # ---------------- Unlocked Levels & High Scores ----------------

    def record_level_completion(
        self,
        player_id: str,
        level_id: str,
        score: int,
        stars: int = 1,
        best_time_seconds: float = 0.0,
        reaction_accuracy: float = 0.0,
    ) -> dict[str, Any]:
        """Records a completed level, calculates anti-tamper signature, and updates high scores."""
        now = datetime.now().isoformat()
        payload = f"{player_id}:{level_id}:{score}:{stars}:{reaction_accuracy:.4f}"
        signature = self._generate_signature(payload)

        # Upsert into unlocked_levels
        self.conn.execute(
            """
            INSERT INTO unlocked_levels (player_id, level_id, score, stars, best_time_seconds, reaction_accuracy, completed_at, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, level_id) DO UPDATE SET
                score = MAX(unlocked_levels.score, excluded.score),
                stars = MAX(unlocked_levels.stars, excluded.stars),
                best_time_seconds = CASE
                    WHEN unlocked_levels.best_time_seconds = 0.0 THEN excluded.best_time_seconds
                    ELSE MIN(unlocked_levels.best_time_seconds, excluded.best_time_seconds)
                END,
                reaction_accuracy = MAX(unlocked_levels.reaction_accuracy, excluded.reaction_accuracy),
                completed_at = excluded.completed_at,
                signature = excluded.signature
            """,
            (
                player_id,
                level_id,
                score,
                stars,
                best_time_seconds,
                reaction_accuracy,
                now,
                signature,
            ),
        )

        # Insert high score record
        self.conn.execute(
            """
            INSERT INTO high_scores (level_id, player_id, score, reaction_accuracy, recorded_at, signature)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (level_id, player_id, score, reaction_accuracy, now, signature),
        )

        level_data = {
            "player_id": player_id,
            "level_id": level_id,
            "score": score,
            "stars": stars,
            "best_time_seconds": best_time_seconds,
            "reaction_accuracy": reaction_accuracy,
            "signature": signature,
            "is_signature_valid": True,
        }
        self._record_journal(
            player_id, "unlocked_levels", f"{player_id}_{level_id}", "UPSERT", level_data
        )
        self.conn.commit()
        return level_data

    def get_unlocked_levels(self, player_id: str) -> list[dict[str, Any]]:
        """Returns all unlocked levels for a player with signature validation."""
        cursor = self.conn.execute(
            "SELECT * FROM unlocked_levels WHERE player_id = ? ORDER BY level_id ASC",
            (player_id,),
        )
        results = []
        for row in cursor.fetchall():
            payload = f"{row['player_id']}:{row['level_id']}:{row['score']}:{row['stars']}:{row['reaction_accuracy']:.4f}"
            expected_sig = self._generate_signature(payload)
            results.append(
                {
                    "player_id": row["player_id"],
                    "level_id": row["level_id"],
                    "score": row["score"],
                    "stars": row["stars"],
                    "best_time_seconds": row["best_time_seconds"],
                    "reaction_accuracy": row["reaction_accuracy"],
                    "completed_at": row["completed_at"],
                    "is_signature_valid": (row["signature"] == expected_sig),
                }
            )
        return results

    def get_high_scores(self, level_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Returns the top high scores for a given level."""
        cursor = self.conn.execute(
            """
            SELECT player_id, score, reaction_accuracy, recorded_at
            FROM high_scores
            WHERE level_id = ?
            ORDER BY score DESC, reaction_accuracy DESC
            LIMIT ?
            """,
            (level_id, limit),
        )
        return [
            {
                "player_id": row["player_id"],
                "score": row["score"],
                "reaction_accuracy": row["reaction_accuracy"],
                "recorded_at": row["recorded_at"],
            }
            for row in cursor.fetchall()
        ]

    # ---------------- Custom Reaction Recipes ----------------

    def save_reaction_recipe(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Saves a custom reaction recipe with reactants, kinetics, and thermodynamics."""
        now = datetime.now().isoformat()
        recipe_id = recipe["recipe_id"]
        player_id = recipe["player_id"]
        name = recipe["name"]
        formula = recipe.get("formula", "")
        reactants_json = json.dumps(recipe.get("reactants", []))
        kinetics_json = json.dumps(recipe.get("kinetics", {}))
        thermodynamics_json = json.dumps(recipe.get("thermodynamics", {}))
        safety_notes = recipe.get("safety_notes", "")
        is_verified = 1 if recipe.get("is_verified", False) else 0

        self.conn.execute(
            """
            INSERT INTO custom_reaction_recipes (
                recipe_id, player_id, name, formula, reactants_json,
                kinetics_json, thermodynamics_json, safety_notes, is_verified,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(recipe_id) DO UPDATE SET
                name = excluded.name,
                formula = excluded.formula,
                reactants_json = excluded.reactants_json,
                kinetics_json = excluded.kinetics_json,
                thermodynamics_json = excluded.thermodynamics_json,
                safety_notes = excluded.safety_notes,
                is_verified = excluded.is_verified,
                updated_at = excluded.updated_at
            """,
            (
                recipe_id,
                player_id,
                name,
                formula,
                reactants_json,
                kinetics_json,
                thermodynamics_json,
                safety_notes,
                is_verified,
                now,
                now,
            ),
        )
        self._record_journal(player_id, "custom_reaction_recipes", recipe_id, "UPSERT", recipe)
        self.conn.commit()
        return recipe

    def get_reaction_recipe(self, recipe_id: str) -> dict[str, Any] | None:
        """Retrieves a recipe by its unique ID."""
        cursor = self.conn.execute(
            "SELECT * FROM custom_reaction_recipes WHERE recipe_id = ?",
            (recipe_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "recipe_id": row["recipe_id"],
            "player_id": row["player_id"],
            "name": row["name"],
            "formula": row["formula"],
            "reactants": json.loads(row["reactants_json"]),
            "kinetics": json.loads(row["kinetics_json"] or "{}"),
            "thermodynamics": json.loads(row["thermodynamics_json"] or "{}"),
            "safety_notes": row["safety_notes"],
            "is_verified": bool(row["is_verified"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # ---------------- Saved Experiments & Simulation States ----------------

    def save_experiment(self, experiment: dict[str, Any]) -> dict[str, Any]:
        """Saves a snapshot of active lab apparatus, chemicals, and oscillation state."""
        now = datetime.now().isoformat()
        exp_id = experiment["experiment_id"]
        player_id = experiment["player_id"]
        name = experiment["name"]
        apparatus_json = json.dumps(experiment.get("apparatus_config", {}))
        chem_json = json.dumps(experiment.get("chemical_state", {}))
        oscillation_json = json.dumps(experiment.get("oscillation_state", {}))
        timestep = experiment.get("simulation_timestep", 0.01)
        thumb = experiment.get("thumbnail_path", "")

        self.conn.execute(
            """
            INSERT INTO saved_experiments (
                experiment_id, player_id, name, apparatus_config_json,
                chemical_state_json, oscillation_state_json, simulation_timestep,
                thumbnail_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(experiment_id) DO UPDATE SET
                name = excluded.name,
                apparatus_config_json = excluded.apparatus_config_json,
                chemical_state_json = excluded.chemical_state_json,
                oscillation_state_json = excluded.oscillation_state_json,
                simulation_timestep = excluded.simulation_timestep,
                thumbnail_path = excluded.thumbnail_path,
                updated_at = excluded.updated_at
            """,
            (
                exp_id,
                player_id,
                name,
                apparatus_json,
                chem_json,
                oscillation_json,
                timestep,
                thumb,
                now,
                now,
            ),
        )
        self._record_journal(player_id, "saved_experiments", exp_id, "UPSERT", experiment)
        self.conn.commit()
        return experiment

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        """Retrieves a saved experiment state by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM saved_experiments WHERE experiment_id = ?",
            (experiment_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "experiment_id": row["experiment_id"],
            "player_id": row["player_id"],
            "name": row["name"],
            "apparatus_config": json.loads(row["apparatus_config_json"]),
            "chemical_state": json.loads(row["chemical_state_json"]),
            "oscillation_state": json.loads(row["oscillation_state_json"] or "{}"),
            "simulation_timestep": row["simulation_timestep"],
            "thumbnail_path": row["thumbnail_path"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # ---------------- JSON Backup & Migration ----------------

    def export_to_json(self, player_id: str, file_path: str | Path) -> None:
        """Exports player profile, unlocked levels, high scores, experiments, and recipes to JSON."""
        profile = self.get_player_profile(player_id)
        if not profile:
            msg = f"Player {player_id} not found."
            raise ValueError(msg)

        unlocked = self.get_unlocked_levels(player_id)
        recipes_cursor = self.conn.execute(
            "SELECT recipe_id FROM custom_reaction_recipes WHERE player_id = ?", (player_id,)
        )
        recipes = [self.get_reaction_recipe(r[0]) for r in recipes_cursor.fetchall()]

        exp_cursor = self.conn.execute(
            "SELECT experiment_id FROM saved_experiments WHERE player_id = ?", (player_id,)
        )
        experiments = [self.get_experiment(e[0]) for e in exp_cursor.fetchall()]

        data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "profile": profile,
            "unlocked_levels": unlocked,
            "custom_reaction_recipes": recipes,
            "saved_experiments": experiments,
        }

        path_obj = Path(file_path)
        path_obj.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def import_from_json(self, file_path: str | Path) -> None:
        """Imports user data from an exported JSON document into the local SQLite store."""
        path_obj = Path(file_path)
        data = json.loads(path_obj.read_text(encoding="utf-8"))

        profile = data["profile"]
        self.conn.execute(
            """
            INSERT OR REPLACE INTO player_profiles (player_id, username, email_hash, level, experience_points, settings_json, version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile["player_id"],
                profile["username"],
                profile.get("email_hash"),
                profile["level"],
                profile["experience_points"],
                json.dumps(profile.get("settings", {})),
                profile.get("version", 1),
            ),
        )

        for lvl in data.get("unlocked_levels", []):
            self.record_level_completion(
                player_id=lvl["player_id"],
                level_id=lvl["level_id"],
                score=lvl["score"],
                stars=lvl.get("stars", 1),
                best_time_seconds=lvl.get("best_time_seconds", 0.0),
                reaction_accuracy=lvl.get("reaction_accuracy", 0.0),
            )

        for rec in data.get("custom_reaction_recipes", []):
            self.save_reaction_recipe(rec)

        for exp in data.get("saved_experiments", []):
            self.save_experiment(exp)

        self.conn.commit()

    def close(self) -> None:
        """Closes the underlying database connection."""
        if self.conn:
            self.conn.close()
