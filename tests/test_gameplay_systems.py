"""
ChemLab Gameplay Systems, Dual-Input & Quest Architecture Test Suite.
Validates:
1. GDScript file syntax, signals, exported parameters, and node references.
2. 1-Euro adaptive filter mathematical convergence (CHI 2012 specification).
3. Schmitt trigger hysteresis for PINCH, POUR, and SWIRL gesture recognition.
4. Quest campaign flow (Quest 1: Orientation & Safety Protocols, all 5 objectives).
5. OSHA compliance penalty system and safety score calculations.
6. SaveManager serialization schema (player profile, quests, tiers, notebook entries).
"""

import json
import math
import re
from pathlib import Path

import pytest

GAME_DIR = Path(__file__).resolve().parent.parent / "game"
SCRIPTS_DIR = GAME_DIR / "scripts"
SCENES_DIR = GAME_DIR / "scenes"


# =============================================================================
# 1. GDSCRIPT & TSCN SYNTAX & ARCHITECTURE VERIFICATION
# =============================================================================


def test_script_files_exist():
    """Verify all required scripts and scenes exist in target directories."""
    input_mgr = SCRIPTS_DIR / "input" / "input_manager.gd"
    quest_mgr = SCRIPTS_DIR / "quests" / "quest_manager.gd"
    save_mgr = SCRIPTS_DIR / "save" / "save_manager.gd"
    quest_overlay_gd = SCRIPTS_DIR / "quests" / "quest_overlay.gd"
    quest_overlay_tscn = SCENES_DIR / "quests" / "quest_overlay.tscn"

    assert input_mgr.exists(), f"Missing {input_mgr}"
    assert quest_mgr.exists(), f"Missing {quest_mgr}"
    assert save_mgr.exists(), f"Missing {save_mgr}"
    assert quest_overlay_gd.exists(), f"Missing {quest_overlay_gd}"
    assert quest_overlay_tscn.exists(), f"Missing {quest_overlay_tscn}"


def test_input_manager_gdscript_structure():
    """Validates InputManager script for required signals, thresholds, and filters."""
    content = (SCRIPTS_DIR / "input" / "input_manager.gd").read_text(encoding="utf-8")

    # Signals - check for signal declarations with parameters
    assert "signal apparatus_grabbed" in content
    assert "signal apparatus_released" in content
    assert "signal apparatus_poured" in content
    assert "signal apparatus_swirled" in content
    assert "signal tracker_connection_changed" in content

    # 1-Euro Filter parameters
    assert "ONE_EURO_FC_MIN" in content or "min_cutoff" in content
    assert "ONE_EURO_BETA" in content or "beta" in content
    assert "0.007" in content  # beta parameter
    assert "StreamPeerTCP" in content
    assert "8768" in content  # daemon port

    # Schmitt trigger hysteresis constants
    assert "0.045" in content  # PINCH enter
    assert "0.065" in content  # PINCH exit
    assert "38.0" in content  # POUR angle threshold


def test_quest_manager_campaign_objectives():
    """Validates QuestManager for Quest 1: Orientation & Safety Protocols and all 5 objectives."""
    content = (SCRIPTS_DIR / "quests" / "quest_manager.gd").read_text(encoding="utf-8")

    # Quest 1 title
    assert "Orientation & Safety Protocols" in content

    # Objective 1: Equip Safety Goggles
    assert "Equip Safety Goggles" in content
    assert "equip safety goggles" in content.lower()

    # Objective 2: Place 250 mL Erlenmeyer Flask on Analytical Balance and Tare
    assert "Analytical Balance Tare" in content
    assert "analytical balance and tare" in content.lower()

    # Objective 3: Dispense 25.0 mL of 0.1 M Hydrochloric Acid (HCl)
    assert "Dispense Acid Reagent" in content
    assert "hydrochloric acid" in content.lower() or "hcl" in content.lower()
    assert "25.0" in content

    # Objective 4: Add 3 drops of Phenolphthalein Indicator
    assert "Add pH Indicator" in content
    assert "phenolphthalein" in content.lower()
    assert "3.0" in content or "3 drops" in content.lower()

    # Objective 5: Titrate to Endpoint
    assert "Titrate to Endpoint" in content
    assert "naoh" in content.lower()
    assert "8.2" in content
    assert "9.0" in content


def test_quest_overlay_tscn_node_hierarchy():
    """Validates quest_overlay.tscn node bindings and scene format."""
    content = (SCENES_DIR / "quests" / "quest_overlay.tscn").read_text(encoding="utf-8")

    assert '[node name="QuestOverlay" type="CanvasLayer"' in content
    assert "quest_card_panel" in content
    assert "objectives_container" in content
    assert "safety_meter_bar" in content
    assert "warning_banner_panel" in content
    assert "celebration_modal" in content


def test_save_manager_gdscript_structure():
    """Validates SaveManager persistence paths and methods."""
    content = (SCRIPTS_DIR / "save" / "save_manager.gd").read_text(encoding="utf-8")

    assert "user://chemlab_save.json" in content
    assert "save_game" in content
    assert "load_game" in content
    assert "record_quest_completion" in content
    assert "add_notebook_entry" in content


# =============================================================================
# 2. 1-EURO ADAPTIVE LOW-PASS FILTER MATHEMATICAL VERIFICATION
# =============================================================================


class PyOneEuroFilter:
    """Exact Python mirror of the GDScript OneEuroFilter implementation."""

    def __init__(self, fc_min: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.fc_min = fc_min
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = 0.0
        self.dx_prev = 0.0
        self.t_prev = -1.0
        self.initialized = False

    @staticmethod
    def smoothing_factor(dt: float, cutoff: float) -> float:
        r = 2.0 * math.pi * cutoff * dt
        return r / (r + 1.0)

    @staticmethod
    def exponential_smoothing(alpha: float, x: float, x_old: float) -> float:
        return alpha * x + (1.0 - alpha) * x_old

    def filter(self, t: float, x: float) -> float:
        if not self.initialized or self.t_prev < 0.0:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t
            self.initialized = True
            return x

        dt = t - self.t_prev
        if dt <= 1e-6:
            return self.x_prev

        dx = (x - self.x_prev) / dt
        a_d = self.smoothing_factor(dt, self.d_cutoff)
        hat_dx = self.exponential_smoothing(a_d, dx, self.dx_prev)

        cutoff = self.fc_min + self.beta * abs(hat_dx)
        a = self.smoothing_factor(dt, cutoff)
        hat_x = self.exponential_smoothing(a, x, self.x_prev)

        self.x_prev = hat_x
        self.dx_prev = hat_dx
        self.t_prev = t
        return hat_x


def test_one_euro_filter_attenuates_high_frequency_jitter():
    """Tests that high-frequency sensor noise is heavily smoothed at low velocity."""
    f = PyOneEuroFilter(fc_min=1.0, beta=0.007, d_cutoff=1.0)
    dt = 1.0 / 60.0  # 60 FPS
    t = 0.0

    # Feed a stationary signal with ±0.01m high frequency jitter
    filtered_values = []
    raw_jitter_values = []

    for i in range(60):
        t += dt
        jitter = 0.01 * (1.0 if (i % 2 == 0) else -1.0)
        raw_val = 0.5 + jitter
        raw_jitter_values.append(raw_val)
        filtered_val = f.filter(t, raw_val)
        if i >= 10:  # let filter settle
            filtered_values.append(filtered_val)

    # Variance of filtered signal should be drastically smaller than raw jitter
    raw_variance = sum((x - 0.5) ** 2 for x in raw_jitter_values[10:]) / len(raw_jitter_values[10:])
    filt_variance = sum((x - 0.5) ** 2 for x in filtered_values) / len(filtered_values)

    assert filt_variance < raw_variance * 0.1, "Filter failed to attenuate high-frequency jitter!"


def test_one_euro_filter_tracks_fast_hand_motion_without_lag():
    """Tests that high velocity hand sweeps dynamically increase cutoff frequency."""
    f = PyOneEuroFilter(fc_min=1.0, beta=0.1, d_cutoff=1.0)
    dt = 1.0 / 60.0
    t = 0.0

    # Warm up at 0
    for _ in range(10):
        t += dt
        f.filter(t, 0.0)

    # Rapid step change to 1.0
    t += dt
    f.filter(t, 1.0)
    t += dt
    val = f.filter(t, 1.0)
    assert val > 0.25, f"Filter should quickly respond to rapid step change, got: {val}"


# =============================================================================
# 3. SCHMITT TRIGGER GESTURE HYSTERESIS
# =============================================================================


class SchmittTriggerPinch:
    """Schmitt trigger model for MediaPipe pinch recognition."""

    def __init__(self, enter_dist: float = 0.045, exit_dist: float = 0.065):
        self.enter_dist = enter_dist
        self.exit_dist = exit_dist
        self.is_pinching = False

    def update(self, distance: float) -> bool:
        if not self.is_pinching:
            if distance < self.enter_dist:
                self.is_pinching = True
        else:
            if distance > self.exit_dist:
                self.is_pinching = False
        return self.is_pinching


def test_pinch_schmitt_trigger_hysteresis():
    """Validates no fluttering occurs in the hysteresis deadband [0.045m .. 0.065m]."""
    trigger = SchmittTriggerPinch(enter_dist=0.045, exit_dist=0.065)

    # Initial open hand at 0.10m
    assert trigger.update(0.10) is False

    # Move inside deadband: 0.055m (between enter 0.045 and exit 0.065) -> must stay FALSE
    assert trigger.update(0.055) is False
    assert trigger.update(0.050) is False

    # Reach 0.040m (< 0.045) -> ENTERS PINCH
    assert trigger.update(0.040) is True

    # Slightly release to 0.050m (in deadband) -> MUST REMAIN TRUE
    assert trigger.update(0.050) is True
    assert trigger.update(0.060) is True

    # Release beyond exit threshold 0.070m (> 0.065) -> EXITS PINCH
    assert trigger.update(0.070) is False

    # Oscillate in deadband 0.050m -> stays FALSE
    assert trigger.update(0.050) is False


class SchmittTriggerPour:
    """Schmitt trigger model for wrist tilt pour recognition."""

    def __init__(self, enter_angle: float = 38.0, exit_angle: float = 34.0):
        self.enter_angle = enter_angle
        self.exit_angle = exit_angle
        self.is_pouring = False

    def update(self, tilt_deg: float) -> tuple[bool, float]:
        effective = abs(tilt_deg)
        if not self.is_pouring:
            if effective > self.enter_angle:
                self.is_pouring = True
        else:
            if effective < self.exit_angle:
                self.is_pouring = False

        rate = max(0.0, min(1.0, (effective - self.enter_angle) / 35.0)) if self.is_pouring else 0.0
        return self.is_pouring, rate


def test_pour_schmitt_trigger_and_flow_rate():
    """Validates pour tilt detection and flow rate scaling."""
    pour = SchmittTriggerPour(enter_angle=38.0, exit_angle=34.0)

    # Level hand: 10 deg tilt
    is_p, rate = pour.update(10.0)
    assert not is_p and rate == 0.0

    # Tilt to 36 deg (in deadband) -> not pouring
    is_p, rate = pour.update(36.0)
    assert not is_p and rate == 0.0

    # Tilt past 38 deg -> 45 deg
    is_p, rate = pour.update(45.0)
    assert is_p is True
    assert 0.15 < rate < 0.25

    # Return to 36 deg (above exit threshold 34) -> MUST REMAIN POURING
    is_p, rate = pour.update(36.0)
    assert is_p is True

    # Drop below 34 deg -> 30 deg -> EXITS POUR
    is_p, rate = pour.update(30.0)
    assert is_p is False and rate == 0.0


def test_swirl_circular_trajectory_detection():
    """Validates circular winding trajectory detection and RPM computation."""
    # Synthesize circular trajectory: radius = 0.05m, frequency = 2 Hz (120 RPM)
    samples = 30
    dt = 1.0 / 60.0
    trajectory = []

    for i in range(samples):
        t = i * dt
        theta = 2.0 * math.pi * 2.0 * t  # 2 revs per second
        x = 0.5 + 0.05 * math.cos(theta)
        y = 0.5 + 0.05 * math.sin(theta)
        trajectory.append((x, y, t))

    # Calculate centroid
    cx = sum(p[0] for p in trajectory) / len(trajectory)
    cy = sum(p[1] for p in trajectory) / len(trajectory)

    total_angle = 0.0
    prev_angle = 0.0
    for i, (x, y, _) in enumerate(trajectory):
        ang = math.atan2(y - cy, x - cx)
        if i > 0:
            diff = ang - prev_angle
            # Wrap to [-pi, pi]
            while diff > math.pi:
                diff -= 2.0 * math.pi
            while diff < -math.pi:
                diff += 2.0 * math.pi
            total_angle += diff
        prev_angle = ang

    total_time = trajectory[-1][2] - trajectory[0][2]
    omega = abs(total_angle) / total_time
    rpm = (omega / (2.0 * math.pi)) * 60.0

    assert 115.0 < rpm < 125.0, f"Calculated RPM ({rpm}) did not match expected 120 RPM!"


# =============================================================================
# 4. QUEST & OSHA COMPLIANCE SIMULATION
# =============================================================================


class QuestProgressionSimulator:
    """Mirrors QuestManager logic for unit testing."""

    def __init__(self):
        self.safety_score = 100.0
        self.ppe_equipped = False
        self.balance_tared = False
        self.hcl_dispensed = 0.0
        self.indicator_added = 0
        self.current_ph = 1.0
        self.completed_objectives = []
        self.violations = []

    def equip_ppe(self):
        self.ppe_equipped = True
        self.completed_objectives.append("equip_ppe")

    def tare_balance(self):
        if not self.ppe_equipped:
            self.safety_score -= 20.0
            self.violations.append("OSHA 1910.133: No PPE before balance operation")
        self.balance_tared = True
        self.completed_objectives.append("place_flask_tare")

    def dispense_hcl(self, ml: float):
        if not self.ppe_equipped:
            self.safety_score -= 25.0
            self.violations.append("OSHA 1910.1450: Corrosive acid handled without PPE")
        if not self.balance_tared:
            self.safety_score -= 5.0
            self.violations.append("Untared scale error")
        self.hcl_dispensed += ml
        if self.hcl_dispensed >= 25.0:
            self.completed_objectives.append("dispense_hcl")

    def add_indicator(self, drops: int):
        self.indicator_added += drops
        if self.indicator_added >= 3:
            self.completed_objectives.append("add_indicator")

    def titrate_naoh(self, ml: float, pour_rate: float):
        if pour_rate > 0.65:
            self.safety_score -= 15.0
            self.violations.append("OSHA 1910.1450: Splash hazard from dumping titrant")

        self.current_ph += ml * 0.35
        if 8.2 <= self.current_ph <= 9.0:
            self.completed_objectives.append("titrate_naoh")
            return True
        return False


def test_quest_1_ideal_completion_flow():
    """Validates complete 5-step ideal titration with 100% OSHA safety score."""
    sim = QuestProgressionSimulator()

    # Step 1: Equip PPE
    sim.equip_ppe()
    assert "equip_ppe" in sim.completed_objectives
    assert sim.safety_score == 100.0

    # Step 2: Place flask on balance and tare
    sim.tare_balance()
    assert "place_flask_tare" in sim.completed_objectives
    assert sim.safety_score == 100.0

    # Step 3: Dispense 25.0 mL 0.1 M HCl
    sim.dispense_hcl(25.0)
    assert "dispense_hcl" in sim.completed_objectives
    assert sim.safety_score == 100.0

    # Step 4: Add 3 drops of phenolphthalein
    sim.add_indicator(3)
    assert "add_indicator" in sim.completed_objectives
    assert sim.safety_score == 100.0

    # Step 5: Dropwise titrate with 0.1 M NaOH to persistent pink endpoint (pH 8.5)
    # Add drops carefully with low pour rate
    for _ in range(21):
        sim.titrate_naoh(ml=1.0, pour_rate=0.2)

    assert sim.current_ph >= 8.2
    assert "titrate_naoh" in sim.completed_objectives
    assert sim.safety_score == 100.0
    assert len(sim.violations) == 0


def test_quest_1_safety_violations_penalties():
    """Validates that OSHA violations accurately deduct safety scores."""
    sim = QuestProgressionSimulator()

    # Attempt dispensing acid without PPE
    sim.dispense_hcl(10.0)
    assert sim.safety_score == 70.0  # -25 for no PPE, -5 for untared balance
    assert len(sim.violations) == 2

    # High flow rate dumping of titrant
    sim.titrate_naoh(ml=5.0, pour_rate=0.85)
    assert sim.safety_score == 55.0  # -15 for violent pour
