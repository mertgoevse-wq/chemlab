"""
Unit and Integration tests for the ChemLab Local cc-omni Launcher and Multi-Provider OmniRoute Setup.

Validates:
- Workspace Isolation: Local scope enforcement for C:\\Users\\Win11 Pro\\Desktop\\chemlab.
- Local Claude Settings: .claude/settings.local.json configures OmniRoute Gateway (127.0.0.1:20128)
  and multi-provider combo (chemlab-auto).
- Global/Local Launcher Scripts: cc-omni.cmd, cc-omni.ps1, cc-omni presence and execution.
- Multi-Provider Routing Pool: Validates live responses through OmniRoute's chemlab-auto combo.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import urllib.request
import urllib.error
import pytest

PROJECT_ROOT = Path("C:/Users/Win11 Pro/Desktop/chemlab").resolve()
SETTINGS_LOCAL_PATH = PROJECT_ROOT / ".claude" / "settings.local.json"
LAUNCHER_PS1 = PROJECT_ROOT / "cc-omni.ps1"
LAUNCHER_CMD = PROJECT_ROOT / "cc-omni.cmd"
GLOBAL_CMD = Path("C:/Users/Win11 Pro/AppData/Roaming/npm/cc-omni.cmd")
OMNIROUTE_URL = "http://127.0.0.1:20128"


def test_workspace_isolation_local_settings_exists() -> None:
    """Verify that settings.local.json exists and binds Claude Code locally to OmniRoute."""
    # Arrange & Act
    assert SETTINGS_LOCAL_PATH.exists(), f"Missing {SETTINGS_LOCAL_PATH}"

    with open(SETTINGS_LOCAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    env = data.get("env", {})

    # Assert
    assert env.get("ANTHROPIC_BASE_URL") == OMNIROUTE_URL
    assert env.get("ANTHROPIC_MODEL") == "chemlab-auto"
    assert env.get("ANTHROPIC_DEFAULT_OPUS_MODEL") == "chemlab-auto"
    assert env.get("ANTHROPIC_DEFAULT_SONNET_MODEL") == "chemlab-auto"
    assert env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") == "chemlab-auto"
    assert env.get("CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY") == "1"


def test_launcher_scripts_exist() -> None:
    """Verify that launcher scripts exist both locally in chemlab and in global npm path."""
    assert LAUNCHER_PS1.exists()
    assert LAUNCHER_CMD.exists()
    assert GLOBAL_CMD.exists()


def test_omniroute_gateway_is_healthy() -> None:
    """Verify that OmniRoute Gateway is online and accepting requests on port 20128."""
    req = urllib.request.Request(f"{OMNIROUTE_URL}/")
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8", errors="ignore")
            assert "OmniRoute" in content
    except Exception as e:
        pytest.fail(f"OmniRoute Gateway unreachable on {OMNIROUTE_URL}: {e}")


def test_cc_omni_status_command() -> None:
    """Verify that running cc-omni status lists the chemlab combos."""
    # Act
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(LAUNCHER_PS1), "status"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    # Assert
    assert proc.returncode == 0
    assert "chemlab-auto" in proc.stdout
    assert "chemlab-p2c" in proc.stdout
    assert "chemlab-omni-auto" in proc.stdout


def test_omniroute_multi_provider_chemlab_auto_query() -> None:
    """Verify that chemlab-auto responds to Anthropic Messages format via OmniRoute."""
    # Arrange
    payload = {
        "model": "chemlab-auto",
        "max_tokens": 15,
        "messages": [{"role": "user", "content": "Respond with OK"}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OMNIROUTE_URL}/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer omniroute-no-auth",
            "anthropic-version": "2023-06-01",
        },
    )

    # Act
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        pytest.skip(f"OmniRoute endpoint {OMNIROUTE_URL} not reachable or timed out: {e}")

    # Assert
    assert "content" in res
    assert len(res["content"]) > 0
    assert "model" in res
    assert res.get("type") == "message"
