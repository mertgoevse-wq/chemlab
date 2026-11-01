"""
ChemLab Android & Mobile WLAN Companion Server.
Provides a zero-install mobile remote control and live telemetry dashboard.
Accessible from any smartphone browser on the local Wi-Fi network.
Enables real-time workstation switching, temperature regulation, magnetic stirring,
and live adjustment of No Man's Sky planetary matrix parameters.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from chemlab.sandbox.no_mans_sky_matrix import LaboratoryEnvironmentMatrix

logger = logging.getLogger("chemlab.companion")


@dataclass
class LabTelemetryState:
    """Current real-time laboratory telemetry streamed to mobile devices."""

    active_reaction: str = "Bereit (Keine Reaktion)"
    temperature_c: float = 22.0
    ph: float = 7.0
    volume_ml: float = 100.0
    current_workstation: str = "main_bench"
    safety_score: float = 100.0
    time_dilation: float = 1.0
    magnetic_stirrer_rpm: int = 0
    fume_hood_active: bool = False
    last_safety_message: str = "Laborstatus normal. Alle Grenzwerte im grünen Bereich."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompanionActionRequest:
    """Action payload dispatched from the mobile companion app."""

    action: str  # 'heat', 'cool', 'stir', 'switch_station', 'emergency_wash'
    parameter: Any = None


class CompanionRemoteServer:
    """
    Handles mobile companion interaction, state broadcasting, and parameter tuning.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8766) -> None:
        self.host = host
        self.port = port
        self.telemetry = LabTelemetryState()
        self.environment = LaboratoryEnvironmentMatrix()

    def get_status(self) -> dict[str, Any]:
        return {
            "telemetry": self.telemetry.to_dict(),
            "environment": {
                "gravity_g": self.environment.gravity_g,
                "ambient_pressure_atm": self.environment.ambient_pressure_atm,
                "ambient_temperature_c": self.environment.ambient_temperature_c,
                "time_warp": self.environment.time_warp,
                "boiling_point_water_c": self.environment.boiling_point_water_c,
                "hazard_difficulty": self.environment.hazard_difficulty.value,
            },
        }

    def handle_action(self, request: CompanionActionRequest) -> dict[str, Any]:
        """Processes remote control inputs dispatched from smartphone."""
        act = request.action.lower()

        if act == "heat":
            delta = float(request.parameter or 10.0)
            self.telemetry.temperature_c = round(self.telemetry.temperature_c + delta, 2)
            return {"status": "ok", "new_temperature_c": self.telemetry.temperature_c}

        if act == "cool":
            delta = float(request.parameter or 10.0)
            self.telemetry.temperature_c = round(
                max(-20.0, self.telemetry.temperature_c - delta), 2
            )
            return {"status": "ok", "new_temperature_c": self.telemetry.temperature_c}

        if act == "stir":
            rpm = int(request.parameter or 500)
            self.telemetry.magnetic_stirrer_rpm = rpm
            return {"status": "ok", "magnetic_stirrer_rpm": rpm}

        if act == "switch_station":
            station = str(request.parameter)
            self.telemetry.current_workstation = station
            return {"status": "ok", "current_workstation": station}

        if act == "emergency_wash":
            self.telemetry.temperature_c = 20.0
            self.telemetry.ph = 7.0
            self.telemetry.last_safety_message = (
                "NOTFALL-DUSCHE AKTIVIERT: Reagenzien verdünnt, Brandherd gelöscht."
            )
            return {"status": "ok", "message": "Emergency wash cycle executed"}

        return {"status": "error", "error": f"Unknown action: {request.action}"}

    def update_environment(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Live adjustment of No Man's Sky planetary matrix parameters."""
        if "gravity_g" in updates:
            self.environment.gravity_g = float(updates["gravity_g"])
        if "ambient_pressure_atm" in updates:
            self.environment.ambient_pressure_atm = float(updates["ambient_pressure_atm"])
        if "ambient_temperature_c" in updates:
            self.environment.ambient_temperature_c = float(updates["ambient_temperature_c"])
        if "time_warp" in updates:
            self.environment.time_warp = float(updates["time_warp"])

        return {
            "status": "ok",
            "environment": {
                "gravity_g": self.environment.gravity_g,
                "ambient_pressure_atm": self.environment.ambient_pressure_atm,
                "ambient_temperature_c": self.environment.ambient_temperature_c,
                "time_warp": self.environment.time_warp,
                "boiling_point_water_c": self.environment.boiling_point_water_c,
            },
        }

    def render_companion_html(self) -> str:
        """Renders mobile PWA web application for smartphone touchscreens."""
        return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>ChemLab Android Remote & Telemetrie</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card: #151d30;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.35);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 16px; min-height: 100vh; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
    .title { font-size: 1.25rem; font-weight: 700; color: var(--accent); display: flex; align-items: center; gap: 8px; }
    .status-badge { font-size: 0.75rem; background: rgba(16, 185, 129, 0.2); color: var(--success); padding: 4px 8px; border-radius: 9999px; font-weight: 600; }

    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
    .card { background: var(--card); border: 1px solid #1e293b; border-radius: 12px; padding: 14px; }
    .card-label { font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; margin-bottom: 4px; }
    .card-val { font-size: 1.5rem; font-weight: 700; }

    .section-title { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 10px; font-weight: 700; }

    .btn-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 20px; }
    .btn { background: #1e293b; color: var(--text); border: 1px solid #334155; border-radius: 8px; padding: 12px 6px; font-size: 0.8rem; font-weight: 600; text-align: center; cursor: pointer; transition: all 0.15s; }
    .btn:active { transform: scale(0.96); background: var(--accent); color: #000; }
    .btn-danger { background: rgba(239, 68, 68, 0.2); border-color: var(--danger); color: var(--danger); }
    .btn-danger:active { background: var(--danger); color: #fff; }

    .slider-box { background: var(--card); border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 20px; }
    .slider-group { margin-bottom: 14px; }
    .slider-header { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 6px; }
    input[type=range] { width: 100%; accent-color: var(--accent); }

    .log-box { background: #000; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 0.75rem; color: #38bdf8; max-height: 100px; overflow-y: auto; }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">🧪 ChemLab Remote</div>
    <div class="status-badge" id="conn-status">WLAN ONLINE</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-label">Temperatur</div>
      <div class="card-val" id="val-temp">25.0 °C</div>
    </div>
    <div class="card">
      <div class="card-label">pH-Wert</div>
      <div class="card-val" id="val-ph">7.0</div>
    </div>
    <div class="card">
      <div class="card-label">Volumen</div>
      <div class="card-val" id="val-vol">100 ml</div>
    </div>
    <div class="card">
      <div class="card-label">Sicherheit</div>
      <div class="card-val" id="val-safety" style="color:var(--success)">100%</div>
    </div>
  </div>

  <div class="section-title">Schnellaktionen</div>
  <div class="btn-row">
    <button class="btn" onclick="sendAction('heat', 15)">🔥 +15°C</button>
    <button class="btn" onclick="sendAction('cool', 10)">❄️ -10°C</button>
    <button class="btn" onclick="sendAction('stir', 600)">🔄 Rühren</button>
    <button class="btn btn-danger" onclick="sendAction('emergency_wash')">🚨 Not-Aus</button>
  </div>

  <div class="section-title">Labor-Workstation Wechseln</div>
  <div class="btn-row">
    <button class="btn" onclick="sendAction('switch_station', 'main_bench')">Laborbank</button>
    <button class="btn" onclick="sendAction('switch_station', 'fume_hood')">Abzug</button>
    <button class="btn" onclick="sendAction('switch_station', 'analytical_bench')">Analytik</button>
    <button class="btn" onclick="sendAction('switch_station', 'synthesis_rig')">Synthese</button>
  </div>

  <div class="section-title">No Man's Sky Matrix (Sandbox)</div>
  <div class="slider-box">
    <div class="slider-group">
      <div class="slider-header">
        <span>Gravitation:</span>
        <span id="label-gravity">1.00 g</span>
      </div>
      <input type="range" min="0" max="3" step="0.05" value="1" oninput="updateEnv('gravity_g', this.value, 'label-gravity', ' g')">
    </div>

    <div class="slider-group">
      <div class="slider-header">
        <span>Zeitraffer (Kinetik):</span>
        <span id="label-warp">1.0x</span>
      </div>
      <input type="range" min="0.1" max="50" step="0.5" value="1" oninput="updateEnv('time_warp', this.value, 'label-warp', 'x')">
    </div>

    <div class="slider-group">
      <div class="slider-header">
        <span>Druck (Atmosphäre):</span>
        <span id="label-pressure">1.00 atm</span>
      </div>
      <input type="range" min="0.01" max="10" step="0.1" value="1" oninput="updateEnv('ambient_pressure_atm', this.value, 'label-pressure', ' atm')">
    </div>
  </div>

  <div class="section-title">AI Sicherheits-Offizier Log</div>
  <div class="log-box" id="ai-log">
    Dr. Evelyn Vance: Laborbetrieb ordnungsgemäß initialisiert. Bereit für Versuche.
  </div>

  <script>
    function sendAction(action, param) {
      fetch('/api/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action, parameter: param})
      }).then(r => r.json()).then(data => {
        document.getElementById('ai-log').innerText = "Aktion '" + action + "' ausgeführt: " + JSON.stringify(data);
      }).catch(err => console.error(err));
    }

    function updateEnv(key, val, labelId, unit) {
      document.getElementById(labelId).innerText = parseFloat(val).toFixed(2) + unit;
      let payload = {};
      payload[key] = parseFloat(val);
      fetch('/api/environment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
    }

    // Polling status
    setInterval(() => {
      fetch('/api/status').then(r => r.json()).then(data => {
        if(data && data.telemetry) {
          document.getElementById('val-temp').innerText = data.telemetry.temperature_c.toFixed(1) + ' °C';
          document.getElementById('val-ph').innerText = data.telemetry.ph.toFixed(1);
          document.getElementById('val-vol').innerText = data.telemetry.volume_ml.toFixed(0) + ' ml';
          document.getElementById('val-safety').innerText = data.telemetry.safety_score.toFixed(0) + '%';
        }
      }).catch(() => {});
    }, 1000);
  </script>
</body>
</html>"""
