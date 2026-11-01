"""Tests for Chemlab Asset Caching Subsystem.

Verifies CAS storage, SHA-256 checksum integrity, LRU eviction, and offline availability.
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.asset_cache import AssetCacheManager


@pytest.fixture
def temp_cache():
    """Provides a fresh AssetCacheManager with a 10MB quota for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = AssetCacheManager(cache_dir=tmp_dir, max_cache_bytes=10 * 1024 * 1024)
        yield cache
        cache.close()


def test_put_and_get_asset(temp_cache):
    """Test storing an asset, verifying SHA-256 hash, and retrieving it."""
    asset_data = b"Simulated Blender 3D Mesh Data for Beaker and Fume Hood"
    asset_uri = "models/lab/apparatus_beaker_500ml.glb"

    entry = temp_cache.put_asset(
        asset_uri=asset_uri,
        data=asset_data,
        asset_type="model_3d",
        mime_type="model/gltf-binary",
        is_pinned=True,
    )

    assert entry["asset_uri"] == asset_uri
    assert entry["sha256_hash"] is not None
    assert entry["file_size"] == len(asset_data)
    assert Path(entry["local_path"]).exists()

    retrieved_data, metadata = temp_cache.get_asset(asset_uri)
    assert retrieved_data == asset_data
    assert metadata["asset_uri"] == asset_uri
    assert metadata["sha256_hash"] == entry["sha256_hash"]


def test_integrity_check_detects_corruption(temp_cache):
    """Test that a tampered file is detected and rejected."""
    asset_data = b"Reaction dataset for Belousov-Zhabotinsky kinetic rate constants"
    asset_uri = "datasets/kinetics/bz_fkn_model.json"

    entry = temp_cache.put_asset(
        asset_uri=asset_uri,
        data=asset_data,
        asset_type="dataset",
        mime_type="application/json",
    )

    Path(entry["local_path"]).write_bytes(b"Corrupted binary stream!")

    with pytest.raises(ValueError, match="Checksum mismatch"):
        temp_cache.get_asset(asset_uri)


def test_lru_eviction_under_storage_budget(temp_cache):
    """Test that unpinned assets are evicted when cache quota is exceeded."""
    temp_cache.max_cache_bytes = 50 * 1024

    temp_cache.put_asset("assets/texture_a.png", b"A" * (20 * 1024), "texture", is_pinned=False)
    temp_cache.put_asset("assets/model_b.glb", b"B" * (20 * 1024), "model_3d", is_pinned=True)
    temp_cache.put_asset("assets/dataset_c.json", b"C" * (25 * 1024), "dataset", is_pinned=False)

    assert temp_cache.has_asset("assets/texture_a.png") is False
    assert temp_cache.has_asset("assets/model_b.glb") is True
    assert temp_cache.has_asset("assets/dataset_c.json") is True


def test_offline_asset_resolution(temp_cache):
    """Test that cached assets can be resolved offline without network access."""
    dataset_content = b'{"reagents": ["Ce(SO4)2", "CH2(COOH)2", "KBrO3"]}'
    temp_cache.put_asset("datasets/offline/bz_reagents.json", dataset_content, "dataset")

    local_path = temp_cache.resolve_local_path("datasets/offline/bz_reagents.json")
    assert local_path is not None
    local_path_obj = Path(local_path)
    assert local_path_obj.exists()
    assert local_path_obj.read_bytes() == dataset_content
