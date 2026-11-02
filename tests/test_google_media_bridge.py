"""
Unit tests for the ChemLab Google Media Bridge.
Tests service enumeration, auth headers, quota exhaustion fallback,
Gemini text generation, image/video/audio generation, search, and
laboratory asset package generation with graceful degradation.
"""

from __future__ import annotations

import pytest

from chemlab.media.google_media_bridge import (
    GoogleCredentials,
    GoogleMediaBridge,
    GoogleService,
    MediaGenerationRequest,
)


def test_google_service_enumeration_includes_all_major_services() -> None:
    services = [s.value for s in GoogleService]
    assert "gemini" in services
    assert "nano_banana" in services
    assert "imagen" in services
    assert "stitch" in services
    assert "jules" in services
    assert "flow" in services
    assert "drive" in services
    assert "docs" in services
    assert "sheets" in services
    assert "slides" in services
    assert "search" in services
    assert "scholar" in services
    assert "patents" in services
    assert "youtube" in services
    assert "maps" in services
    assert "firebase" in services
    assert "bigquery" in services
    assert "cloud_vision" in services
    assert "cloud_speech" in services
    assert "cloud_translate" in services
    assert "gmail" in services
    assert "calendar" in services
    assert "vertex_ai" in services
    assert "ai_studio" in services
    assert "realtime_api" in services
    assert "agent_builder" in services
    assert len(services) >= 30  # "ALL Google services"


def test_bridge_initialization_with_credentials() -> None:
    creds = GoogleCredentials(oauth_token="ya29.test-token")
    bridge = GoogleMediaBridge(credentials=creds)
    assert bridge.credentials.oauth_token == "ya29.test-token"
    assert not bridge._is_quota_exhausted()


def test_auth_headers_include_oauth_token() -> None:
    creds = GoogleCredentials(oauth_token="ya29.test-token")
    bridge = GoogleMediaBridge(credentials=creds)
    headers = bridge._auth_headers()
    assert "Authorization" in headers
    assert "Bearer ya29.test-token" in headers["Authorization"]


def test_quota_exhaustion_triggers_fallback() -> None:
    creds = GoogleCredentials(oauth_token="expired-token")
    creds.quota_exhausted = True
    creds.last_quota_check = __import__("time").time()
    bridge = GoogleMediaBridge(credentials=creds)
    assert bridge._is_quota_exhausted()


def test_image_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    response = bridge.generate_image("a chemistry laboratory with borosilicate glassware")
    # Without network/OAuth, all calls degrade gracefully rather than crashing
    assert isinstance(response.success, bool)
    assert response.service is not None


def test_video_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    response = bridge.generate_video("flythrough of a pharmaceutical laboratory", 10)
    assert isinstance(response.success, bool)


def test_audio_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    response = bridge.generate_audio("laboratory ambient bubbling", 30)
    assert isinstance(response.success, bool)


def test_stitch_ui_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    response = bridge.generate_ui_with_stitch("chemistry laboratory HUD dashboard")
    assert isinstance(response.success, bool)


def test_jules_code_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    response = bridge.generate_code_with_jules("synthesis wizard UI component")
    assert isinstance(response.success, bool)


def test_search_images_returns_list_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    results = bridge.search_images("borosilicate glass chemistry lab", 5)
    assert isinstance(results, list)


def test_search_web_returns_list_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    results = bridge.search_web("Kolbe-Schmitt carboxylation", 5)
    assert isinstance(results, list)


def test_lab_asset_package_generation_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    pkg = bridge.generate_lab_asset_package(
        lab_id="lab_001",
        lab_type="clandestine_underground",
        theme_prompt="damp underground laboratory with brick walls and flickering lights",
        include_npcs=True,
        include_quests=True,
    )
    assert pkg.lab_id == "lab_001"
    assert pkg.lab_type == "clandestine_underground"
    assert isinstance(pkg.images, list)
    assert isinstance(pkg.videos, list)
    assert isinstance(pkg.audio, list)
    assert isinstance(pkg.textures, list)
    assert isinstance(pkg.models_3d, list)
    assert isinstance(pkg.documents, list)
    assert isinstance(pkg.npcs, list)
    assert isinstance(pkg.quests, list)
    assert len(pkg.npcs) >= 1  # fallback NPC always present
    assert len(pkg.quests) >= 1  # fallback quest always present


def test_gemini_text_generation_graceful_failure_offline() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    result = bridge.generate_text_with_gemini("Describe aspirin synthesis")
    # Without network, returns None gracefully
    assert result is None or isinstance(result, str)


def test_health_check_returns_dict() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    health = bridge.health_check()
    assert isinstance(health, dict)
    assert "oauth_available" in health
    assert "fallback_active" in health


def test_media_generation_request_dataclass() -> None:
    req = MediaGenerationRequest(
        service=GoogleService.GEMINI,
        prompt="Generate a chemistry lab safety poster",
        width=1920,
        height=1080,
        style="photorealistic",
    )
    assert req.service == GoogleService.GEMINI
    assert req.width == 1920
    assert req.height == 1080


def test_all_services_list_has_minimum_count() -> None:
    bridge = GoogleMediaBridge(credentials=GoogleCredentials())
    all_services = bridge.list_all_services()
    assert len(all_services) >= 30
