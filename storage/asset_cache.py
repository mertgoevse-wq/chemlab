"""Chemlab Content-Addressable Storage (CAS) Asset Cache.

Caches 3D assets (.blend, .glb), textures, and reaction datasets locally.
Includes SHA-256 verification, LRU eviction, and offline file resolution.
Optimized for resource-constrained systems (Intel Iris Xe 128MB VRAM).
"""

import contextlib
import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class AssetCacheManager:
    """Manages local asset caching, integrity verification, and storage budgeting."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_cache_bytes: int = 500 * 1024 * 1024,  # Default 500 MB quota
    ) -> None:
        if cache_dir is None:
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                self.cache_dir = Path(local_appdata) / "Chemlab" / "asset_cache"
            else:
                self.cache_dir = Path.home() / ".chemlab" / "asset_cache"
        else:
            self.cache_dir = Path(cache_dir).resolve()

        self.objects_dir = self.cache_dir / "objects"
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_bytes = max_cache_bytes

        self.db_path = self.cache_dir / "cache_index.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_index()

    def _init_index(self) -> None:
        """Initializes asset cache metadata index in SQLite."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_cache_metadata (
                asset_id TEXT PRIMARY KEY,
                asset_uri TEXT UNIQUE NOT NULL,
                local_path TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                asset_type TEXT NOT NULL,
                mime_type TEXT,
                is_pinned INTEGER NOT NULL DEFAULT 0,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_uri ON asset_cache_metadata(asset_uri)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_accessed ON asset_cache_metadata(last_accessed_at ASC)"
        )
        self.conn.commit()

    def _compute_sha256(self, data: bytes) -> str:
        """Computes hexadecimal SHA-256 checksum."""
        return hashlib.sha256(data).hexdigest()

    def _get_total_cache_size(self) -> int:
        """Returns the total disk bytes used by cached assets."""
        cursor = self.conn.execute("SELECT SUM(file_size) FROM asset_cache_metadata")
        val = cursor.fetchone()[0]
        return val if val is not None else 0

    def _evict_if_needed(self, required_bytes: int) -> None:
        """Evicts unpinned assets using LRU policy if adding required_bytes exceeds max quota."""
        current_size = self._get_total_cache_size()
        target_size = self.max_cache_bytes - required_bytes

        if current_size <= target_size:
            return

        cursor = self.conn.execute(
            """
            SELECT asset_id, local_path, file_size
            FROM asset_cache_metadata
            WHERE is_pinned = 0
            ORDER BY last_accessed_at ASC
            """
        )
        candidates = cursor.fetchall()

        for row in candidates:
            if current_size <= target_size:
                break

            asset_id = row["asset_id"]
            local_path = Path(row["local_path"])
            file_size = row["file_size"]

            if local_path.exists():
                with contextlib.suppress(OSError):
                    local_path.unlink()

            self.conn.execute("DELETE FROM asset_cache_metadata WHERE asset_id = ?", (asset_id,))
            current_size -= file_size

        self.conn.commit()

    def put_asset(
        self,
        asset_uri: str,
        data: bytes,
        asset_type: str = "general",
        mime_type: str | None = None,
        is_pinned: bool = False,
    ) -> dict[str, Any]:
        """Stores binary asset into CAS, updates metadata, and triggers eviction if needed."""
        sha256 = self._compute_sha256(data)
        file_size = len(data)

        self._evict_if_needed(file_size)

        prefix = sha256[:2]
        dest_dir = self.objects_dir / prefix
        dest_dir.mkdir(parents=True, exist_ok=True)
        local_path = dest_dir / sha256

        local_path.write_bytes(data)

        now = datetime.now().isoformat()
        asset_id = f"asset_{sha256[:16]}"
        local_path_str = str(local_path)

        self.conn.execute(
            """
            INSERT INTO asset_cache_metadata (
                asset_id, asset_uri, local_path, sha256_hash, file_size,
                asset_type, mime_type, is_pinned, last_accessed_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_uri) DO UPDATE SET
                local_path = excluded.local_path,
                sha256_hash = excluded.sha256_hash,
                file_size = excluded.file_size,
                asset_type = excluded.asset_type,
                mime_type = excluded.mime_type,
                is_pinned = excluded.is_pinned,
                last_accessed_at = excluded.last_accessed_at
            """,
            (
                asset_id,
                asset_uri,
                local_path_str,
                sha256,
                file_size,
                asset_type,
                mime_type,
                1 if is_pinned else 0,
                now,
                now,
            ),
        )
        self.conn.commit()

        return {
            "asset_id": asset_id,
            "asset_uri": asset_uri,
            "local_path": local_path_str,
            "sha256_hash": sha256,
            "file_size": file_size,
            "is_pinned": is_pinned,
        }

    def get_asset(self, asset_uri: str) -> tuple[bytes, dict[str, Any]]:
        """Retrieves asset bytes and verifies SHA-256 integrity."""
        cursor = self.conn.execute(
            "SELECT * FROM asset_cache_metadata WHERE asset_uri = ?",
            (asset_uri,),
        )
        row = cursor.fetchone()
        if not row:
            msg = f"Asset '{asset_uri}' not found in local cache."
            raise KeyError(msg)

        local_path = Path(row["local_path"])
        if not local_path.exists():
            self.conn.execute("DELETE FROM asset_cache_metadata WHERE asset_uri = ?", (asset_uri,))
            self.conn.commit()
            msg = f"Cached asset file missing at: {local_path}"
            raise FileNotFoundError(msg)

        data = local_path.read_bytes()

        actual_hash = self._compute_sha256(data)
        if actual_hash != row["sha256_hash"]:
            with contextlib.suppress(OSError):
                local_path.unlink()
            self.conn.execute("DELETE FROM asset_cache_metadata WHERE asset_uri = ?", (asset_uri,))
            self.conn.commit()
            msg = f"Checksum mismatch for '{asset_uri}'. Expected {row['sha256_hash']}, got {actual_hash}"
            raise ValueError(msg)

        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE asset_cache_metadata SET last_accessed_at = ? WHERE asset_uri = ?",
            (now, asset_uri),
        )
        self.conn.commit()

        metadata = dict(row)
        return data, metadata

    def resolve_local_path(self, asset_uri: str) -> str | None:
        """Returns the local filesystem path for Godot or Blender if cached and valid."""
        try:
            _, metadata = self.get_asset(asset_uri)
            return metadata["local_path"]
        except (KeyError, FileNotFoundError, ValueError):
            return None

    def has_asset(self, asset_uri: str) -> bool:
        """Checks if asset exists in cache and has physical file on disk."""
        cursor = self.conn.execute(
            "SELECT local_path FROM asset_cache_metadata WHERE asset_uri = ?",
            (asset_uri,),
        )
        row = cursor.fetchone()
        if not row:
            return False
        return Path(row["local_path"]).exists()

    def close(self) -> None:
        """Closes index database."""
        if self.conn:
            self.conn.close()
