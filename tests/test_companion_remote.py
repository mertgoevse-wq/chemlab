"""
Unit tests for the ChemLab Android Companion WLAN / WebSocket Remote Server.
Tests REST status retrieval, action dispatching, sandbox environmental tuning,
and HTML5 mobile companion asset generation.
"""

from __future__ import annotations

import json

import pytest

from chemlab.companion.remote_server import (
    CompanionActionRequest,
    CompanionRemoteServer,
    LabTelemetryState,
)


def test_companion_telemetry_state_serialization() -> None:
    telemetry = LabTelemetryState(
        active_reaction="Aspirin-Totalsynthese",
        temperature_c=65.4,
        ph=3.2,
        volume_ml=120.0,
        current_workstation="main_bench",
        safety_score=100.0,
        time_dilation=2.0,
    )
    data = telemetry.to_dict()
    assert data["temperature_c"] == 65.4
    assert data["ph"] == 3.2
    assert data["active_reaction"] == "Aspirin-Totalsynthese"


def test_companion_action_dispatch() -> None:
    server = CompanionRemoteServer(host="127.0.0.1", port=8766)
    # Test heat action
    act = CompanionActionRequest(action="heat", parameter=15.0)
    res = server.handle_action(act)
    assert res["status"] == "ok"
    assert res["new_temperature_c"] > 20.0

    # Test workstation switch action
    act_station = CompanionActionRequest(action="switch_station", parameter="fume_hood")
    res_station = server.handle_action(act_station)
    assert res_station["status"] == "ok"
    assert res_station["current_workstation"] == "fume_hood"


def test_companion_environment_tuning() -> None:
    server = CompanionRemoteServer(host="127.0.0.1", port=8766)
    env_update = {"gravity_g": 0.38, "time_warp": 5.0, "ambient_pressure_atm": 0.5}
    res = server.update_environment(env_update)
    assert res["status"] == "ok"
    assert server.environment.gravity_g == 0.38
    assert server.environment.time_warp == 5.0
    assert server.environment.ambient_pressure_atm == 0.5


def test_companion_html_page_generation() -> None:
    server = CompanionRemoteServer(host="127.0.0.1", port=8766)
    html = server.render_companion_html()
    assert "<!DOCTYPE html>" in html
    assert "ChemLab Android Remote" in html
    assert "Workstation" in html
    assert "Zeitraffer" in html
