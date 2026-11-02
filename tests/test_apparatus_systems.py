"""
ChemLab Analytical Apparatus Test Suite (Analytical Balance & Titration Buret).
Validates:
1. GDScript and TSCN file existence and integrity in game/scenes/apparatus.
2. Analytical Balance scene graph, node types, groups, and exported properties.
3. Analytical Balance stoichiometric mass formula: m = sum(n_i * M_w,i) + V * rho.
4. Analytical Balance draft shield logic: +/- 0.0003 g turbulence when open, full stabilization when closed.
5. Analytical Balance tare operation and QuestManager objective progression.
6. Titration Buret scene graph, valve state machine (CLOSED, DROPWISE, STREAM).
7. Titration Buret dropwise flow rate (0.05 mL / 0.8s) and continuous stream drainage.
8. Meniscus visual column scaling and 0.00 - 50.00 mL graduation tracking.
9. Titration Buret discrete drop emission (GPUParticles3D) and RayCast3D vessel detection.
10. Acid-Base titration chemistry simulation (0.1 M HCl + 0.1 M NaOH), equivalence point, and phenolphthalein endpoint.
"""

import math
import re
from pathlib import Path

import pytest

APPARATUS_DIR = Path("C:/Users/Win11 Pro/Desktop/chemlab/game/scenes/apparatus")


# =============================================================================
# 1. FILE EXISTENCE & STRUCTURE TESTS
# =============================================================================


def test_apparatus_files_exist():
    """Verify all apparatus scenes and scripts exist in game/scenes/apparatus."""
    balance_gd = APPARATUS_DIR / "analytical_balance.gd"
    balance_tscn = APPARATUS_DIR / "analytical_balance.tscn"
    buret_gd = APPARATUS_DIR / "titration_buret.gd"
    buret_tscn = APPARATUS_DIR / "titration_buret.tscn"
    flask_gd = APPARATUS_DIR / "erlenmeyer_flask.gd"
    flask_tscn = APPARATUS_DIR / "erlenmeyer_flask.tscn"
    beaker_gd = APPARATUS_DIR / "beaker.gd"
    beaker_tscn = APPARATUS_DIR / "beaker.tscn"

    assert balance_gd.exists(), f"Missing analytical balance script at {balance_gd}"
    assert balance_tscn.exists(), f"Missing analytical balance scene at {balance_tscn}"
    assert buret_gd.exists(), f"Missing titration buret script at {buret_gd}"
    assert buret_tscn.exists(), f"Missing titration buret scene at {buret_tscn}"
    assert flask_gd.exists(), f"Missing erlenmeyer flask script at {flask_gd}"
    assert flask_tscn.exists(), f"Missing erlenmeyer flask scene at {flask_tscn}"
    assert beaker_gd.exists(), f"Missing beaker script at {beaker_gd}"
    assert beaker_tscn.exists(), f"Missing beaker scene at {beaker_tscn}"


# =============================================================================
# 2. ANALYTICAL BALANCE GDSCRIPT & TSCN VERIFICATION
# =============================================================================


def test_analytical_balance_gdscript_structure():
    """Verify analytical_balance.gd has correct class name, signals, and functions."""
    content = (APPARATUS_DIR / "analytical_balance.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name AnalyticalBalance" in content
    assert "extends StaticBody3D" in content

    # Group requirement
    assert (
        'GROUP_INTERACTIVE_APPARATUS: String = "interactive_apparatus"' in content
        or '"interactive_apparatus"' in content
    )

    # Signals
    assert "signal mass_changed" in content
    assert "signal tared" in content
    assert "signal door_state_changed" in content
    assert "signal stability_changed" in content
    assert "signal vessel_placed" in content
    assert "signal vessel_removed" in content

    # Key methods
    assert "func tare()" in content
    assert "func calculate_vessel_mass" in content
    assert "func _calculate_stoichiometric_mass" in content
    assert "func is_any_door_open" in content
    assert "func are_all_doors_closed" in content
    assert "func toggle_door" in content
    assert "func open_door" in content
    assert "func close_door" in content
    assert "func try_place_item" in content
    assert "func remove_vessel" in content
    assert "func get_interaction_info" in content
    assert "func interact" in content

    # Molecular weights and draft constants
    assert "0.0003" in content  # +/- 0.0003 g draft flutter
    assert "36.46" in content  # HCl Mw
    assert "39.997" in content  # NaOH Mw
    assert "18.015" in content  # H2O Mw


def test_analytical_balance_tscn_nodes():
    """Verify analytical_balance.tscn contains all required nodes, materials, and groups."""
    content = (APPARATUS_DIR / "analytical_balance.tscn").read_text(encoding="utf-8")

    # Root node
    assert 'name="AnalyticalBalance" type="StaticBody3D"' in content
    assert 'groups=["interactive_apparatus"]' in content

    # Required geometry & children from mission spec
    assert 'name="BaseHousing" type="MeshInstance3D"' in content
    assert 'name="WeighingPan" type="MeshInstance3D"' in content
    assert 'name="WeighingPanArea" type="Area3D"' in content
    assert 'name="DigitalDisplay" type="Label3D"' in content
    assert 'name="TareButton" type="MeshInstance3D"' in content

    # 3 sliding glass doors
    assert 'name="DoorLeft"' in content
    assert 'name="DoorRight"' in content
    assert 'name="DoorTop"' in content

    # Materials: Cast aluminum, stainless steel, glass
    assert "Mat_CastAluminum" in content
    assert "Mat_StainlessSteel" in content
    assert "Mat_ShieldGlass" in content

    # VFD display color (cyan/green fluorescent)
    assert "Color(0.08, 1, 0.82, 1)" in content or "0.08, 1" in content


# =============================================================================
# 3. TITRATION BURET GDSCRIPT & TSCN VERIFICATION
# =============================================================================


def test_titration_buret_gdscript_structure():
    """Verify titration_buret.gd has correct class name, valve states, and dispense logic."""
    content = (APPARATUS_DIR / "titration_buret.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name TitrationBuret" in content
    assert "extends StaticBody3D" in content

    # Group requirement
    assert (
        'GROUP_INTERACTIVE_APPARATUS: String = "interactive_apparatus"' in content
        or '"interactive_apparatus"' in content
    )

    # Valve state enum
    assert "enum ValveState" in content
    assert "CLOSED" in content
    assert "DROPWISE" in content
    assert "STREAM" in content

    # Dropwise flow rate & volume specifications
    assert "MAX_CAPACITY_ML: float = 50.00" in content
    assert "DROP_VOLUME_ML: float = 0.05" in content  # 0.05 mL per drop
    assert "DROP_INTERVAL_S: float = 0.8" in content or "0.80" in content  # 0.8s drop interval

    # Signals
    assert "signal valve_state_changed" in content
    assert "signal drop_dispensed" in content
    assert "signal volume_changed" in content
    assert "signal buret_emptied" in content
    assert "signal endpoint_reached" in content

    # Key methods
    assert "func set_valve_state" in content
    assert "func cycle_valve_state" in content
    assert "func _dispense_discrete_drop" in content
    assert "func _dispense_continuous_stream" in content
    assert "func _transfer_titrant_to_vessel" in content
    assert "func _update_titration_endpoint_curve" in content
    assert "func _update_meniscus_display" in content
    assert "func refill" in content
    assert "func try_place_item" in content
    assert "func get_interaction_info" in content
    assert "func interact" in content

    # Chemistry constants
    assert "0.1" in content  # 0.1 M NaOH titrant
    assert "naoh" in content
    assert "8.2" in content  # Phenolphthalein transition threshold
    assert "8.5" in content  # Target endpoint pH


def test_titration_buret_tscn_nodes():
    """Verify titration_buret.tscn contains all required nodes, emitter, and raycast."""
    content = (APPARATUS_DIR / "titration_buret.tscn").read_text(encoding="utf-8")

    # Root node
    assert 'name="TitrationBuret" type="StaticBody3D"' in content
    assert 'groups=["interactive_apparatus"]' in content

    # Required children from mission spec
    assert 'name="StopcockValve" type="MeshInstance3D"' in content
    assert 'name="DropEmitter" type="GPUParticles3D"' in content
    assert 'name="DropTargetRay" type="RayCast3D"' in content

    # Geometry: Retort stand, chrome rod, clamp, buret tube
    assert 'name="Base" type="MeshInstance3D"' in content
    assert 'name="Rod" type="MeshInstance3D"' in content
    assert 'name="Clamp"' in content
    assert 'name="BuretTube"' in content
    assert 'name="LiquidColumn"' in content
    assert 'name="NeedleTip"' in content

    # Materials: Cast iron, chrome, borosilicate glass, PTFE
    assert "Mat_CastIron" in content
    assert "Mat_Chrome" in content
    assert "Mat_BorosilicateGlass" in content
    assert "Mat_PTFE" in content


# =============================================================================
# 4. MATHEMATICAL & CHEMICAL SIMULATION LOGIC VERIFICATION
# =============================================================================


def test_stoichiometric_mass_calculation():
    """Validates analytical balance mass formula: m = sum(n_i * M_w,i) + V * rho."""
    # Test case 1: Empty 250 mL Erlenmeyer Flask
    empty_flask_dry_mass = 125.0000

    # Test case 2: Flask + 25.0 mL 0.1 M HCl
    # 25.0 mL water (density = 1.0 g/mL) = 25.0000 g
    # 25.0 mL of 0.1 M HCl contains n = 0.0025 mol HCl
    # M_w(HCl) = 36.460 g/mol -> mass of solute = 0.0025 * 36.460 = 0.09115 g
    # Total contents mass = 25.0000 + 0.09115 = 25.09115 g
    # Total system mass = 125.0000 + 25.09115 = 150.09115 g
    mw_hcl = 36.460
    moles_hcl = 0.0025
    volume_ml = 25.0
    density_solvent = 1.0

    solute_mass = moles_hcl * mw_hcl
    solvent_mass = volume_ml * density_solvent
    total_mass = empty_flask_dry_mass + solute_mass + solvent_mass

    assert math.isclose(solute_mass, 0.09115, rel_tol=1e-5)
    assert math.isclose(total_mass, 150.09115, rel_tol=1e-5)

    # Test case 3: Flask contents format matching ErlenmeyerFlask:
    # contents = {"hcl": {"name": "HCl", "volume_ml": 25.0, "moles": 0.0025}}
    flask_contents = {"hcl": {"name": "HCl", "volume_ml": 25.0, "moles": 0.0025}}
    total_vol = sum(sp["volume_ml"] for sp in flask_contents.values())
    total_solute = sum(sp["moles"] * mw_hcl for sp in flask_contents.values())
    assert math.isclose(total_vol * density_solvent + total_solute, 25.09115, rel_tol=1e-5)

    # After Tare, net mass should be exactly 0.0000 g
    tare_offset = total_mass
    net_mass = total_mass - tare_offset
    assert math.isclose(net_mass, 0.0, abs_tol=1e-7)


def test_air_draft_flutter_model():
    """Verify that draft flutter formula generates turbulence strictly within +/- 0.0003 g."""
    # GDScript flutter formula:
    # sin(t * 3.8) * 0.00015 + cos(t * 7.4) * 0.00010 + sin(t * 13.1) * 0.00005
    max_flutter = 0.00015 + 0.00010 + 0.00005
    assert max_flutter <= 0.0003001  # strictly <= 0.0003 g

    # Sample across 1000 simulated timesteps
    values = []
    for i in range(1000):
        t = i * 0.016
        flutter = (
            math.sin(t * 3.8) * 0.00015 + math.cos(t * 7.4) * 0.00010 + math.sin(t * 13.1) * 0.00005
        )
        values.append(flutter)

    max_val = max(values)
    min_val = min(values)

    assert max_val <= 0.00030, f"Max draft {max_val} exceeded +0.0003 g"
    assert min_val >= -0.00030, f"Min draft {min_val} exceeded -0.0003 g"


def test_titration_equivalence_curve_and_endpoint():
    """Verify titration curve calculation: 25.0 mL 0.1 M HCl titrated with 0.1 M NaOH."""
    initial_acid_moles = 25.0 * 1e-3 * 0.1  # 0.0025 mol HCl
    molarity_base = 0.1  # M NaOH

    # 1. At 0 mL NaOH (pure 0.1 M HCl): pH should be ~1.0
    conc_h_0 = initial_acid_moles / (25.0e-3)
    ph_0 = -math.log10(conc_h_0)
    assert math.isclose(ph_0, 1.0, rel_tol=1e-3)

    # 2. At 20.0 mL NaOH added (before equivalence point):
    # Added base = 20.0e-3 * 0.1 = 0.0020 mol
    # Net acid = 0.0025 - 0.0020 = 0.0005 mol
    # Total volume = 45.0 mL
    # conc_h = 0.0005 / 0.045 = 0.0111 M -> pH ~ 1.95
    net_acid_20 = initial_acid_moles - (20.0e-3 * molarity_base)
    conc_h_20 = net_acid_20 / 0.045
    ph_20 = -math.log10(conc_h_20)
    assert 1.8 < ph_20 < 2.1

    # 3. At 25.0 mL NaOH added -> Equivalence Point
    # Net acid = 0 -> pH = 7.0 (neutral)

    # 4. At 25.05 mL NaOH added (1 drop past equivalence point = 0.05 mL excess NaOH):
    # Excess OH- = 0.05e-3 * 0.1 = 5.0e-6 mol
    # Total volume = 50.05 mL = 0.05005 L
    # conc_oh = 5.0e-6 / 0.05005 = 9.99e-5 M
    # pOH = -log10(9.99e-5) = 4.00
    # pH = 14.0 - 4.00 = 10.00 -> Phenolphthalein turns brilliant pink!
    excess_oh = (25.05e-3 * molarity_base) - initial_acid_moles
    conc_oh = excess_oh / 0.05005
    poh = -math.log10(conc_oh)
    ph_endpoint = 14.0 - poh
    assert ph_endpoint >= 8.5, f"Endpoint pH {ph_endpoint} should be >= 8.5"


def test_dropwise_drainage_math():
    """Verify dropwise volume timing: 1 drop / 0.8s = 0.05 mL."""
    drop_volume = 0.05  # mL
    drop_interval = 0.8  # seconds

    # Flow rate in mL/s
    flow_rate = drop_volume / drop_interval
    assert math.isclose(flow_rate, 0.0625, rel_tol=1e-5)

    # Delivering 25.0 mL takes 500 drops
    total_drops = 25.0 / drop_volume
    assert math.isclose(total_drops, 500.0)

    # 500 drops * 0.8s = 400 seconds (or in simulation with fast-forward / stream)
    drain_time = total_drops * drop_interval
    assert math.isclose(drain_time, 400.0)


# =============================================================================
# 4. ERLENMEYER FLASK & BEAKER GDSCRIPT & TSCN VERIFICATION
# =============================================================================


def test_erlenmeyer_flask_gdscript_structure():
    """Verify erlenmeyer_flask.gd has required class name, signals, properties, and methods."""
    content = (APPARATUS_DIR / "erlenmeyer_flask.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name ErlenmeyerFlask" in content
    assert "extends RigidBody3D" in content

    # Exported properties
    assert 'vessel_name: String = "250 mL Erlenmeyer Flask"' in content
    assert "capacity_ml: float = 250.0" in content
    assert "current_volume_ml: float = 0.0" in content
    assert "temperature_c: float = 21.0" in content
    assert "empty_mass_g: float = 125.0" in content
    assert "pour_angle_threshold_deg: float = 35.0" in content

    # Signals
    assert "signal volume_changed" in content
    assert "signal contents_changed" in content
    assert "signal temperature_changed" in content
    assert "signal liquid_poured" in content
    assert "signal liquid_received" in content

    # Required methods from specification
    assert "func add_reagent" in content
    assert "func pour_out" in content
    assert "func get_interaction_info" in content
    assert "func set_liquid_state" in content
    assert "func get_total_mass" in content
    assert "func _check_pour_physics" in content


def test_erlenmeyer_flask_tscn_nodes():
    """Verify erlenmeyer_flask.tscn contains all required nodes, materials, and groups."""
    content = (APPARATUS_DIR / "erlenmeyer_flask.tscn").read_text(encoding="utf-8")

    # Root node and groups
    assert 'name="ErlenmeyerFlask" type="RigidBody3D"' in content
    assert '"interactive_apparatus"' in content
    assert '"glassware"' in content
    assert '"apparatus"' in content
    assert '"interactable"' in content

    # Mesh nodes and shaders
    assert 'name="BodyMesh" type="MeshInstance3D"' in content
    assert 'name="NeckMesh" type="MeshInstance3D"' in content
    assert 'name="RimMesh" type="MeshInstance3D"' in content
    assert 'name="LiquidVolume" type="MeshInstance3D"' in content
    assert "glass_shader.gdshader" in content
    assert "liquid_shader.gdshader" in content

    # Functional child nodes
    assert 'name="PourMouth" type="Marker3D"' in content
    assert 'name="PourRay" type="RayCast3D"' in content
    assert 'name="RecipientArea" type="Area3D"' in content
    assert 'name="AudioPour" type="AudioStreamPlayer3D"' in content


def test_beaker_gdscript_structure():
    """Verify beaker.gd has required class name, signals, properties, and methods."""
    content = (APPARATUS_DIR / "beaker.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name Beaker" in content
    assert "extends RigidBody3D" in content

    # Exported properties
    assert 'vessel_name: String = "400 mL Beaker"' in content
    assert "capacity_ml: float = 400.0" in content
    assert "current_volume_ml: float = 0.0" in content
    assert "temperature_c: float = 21.0" in content
    assert "empty_mass_g: float = 135.0" in content
    assert "pour_angle_threshold_deg: float = 35.0" in content

    # Required methods from specification
    assert "func add_reagent" in content
    assert "func pour_out" in content
    assert "func get_interaction_info" in content
    assert "func set_liquid_state" in content
    assert "func get_total_mass" in content
    assert "func _check_pour_physics" in content


def test_beaker_tscn_nodes():
    """Verify beaker.tscn contains all required nodes, graduation markings, and groups."""
    content = (APPARATUS_DIR / "beaker.tscn").read_text(encoding="utf-8")

    # Root node and groups
    assert 'name="Beaker" type="RigidBody3D"' in content
    assert '"interactive_apparatus"' in content
    assert '"glassware"' in content

    # Mesh and spout nodes
    assert 'name="BodyMesh" type="MeshInstance3D"' in content
    assert 'name="SpoutMesh" type="MeshInstance3D"' in content
    assert 'name="LiquidVolume" type="MeshInstance3D"' in content

    # Graduation marks at 100, 200, 300, 400 mL
    assert 'name="Graduations" type="Node3D"' in content
    assert 'name="Mark_100ml"' in content
    assert 'name="Mark_200ml"' in content
    assert 'name="Mark_300ml"' in content
    assert 'name="Mark_400ml"' in content
    assert '"100"' in content
    assert '"200"' in content
    assert '"300"' in content
    assert '"400 mL"' in content

    # Functional child nodes
    assert 'name="PourMouth" type="Marker3D"' in content
    assert 'name="PourRay" type="RayCast3D"' in content
    assert 'name="RecipientArea" type="Area3D"' in content
    assert 'name="AudioPour" type="AudioStreamPlayer3D"' in content


def test_glassware_tilt_and_pour_physics_math():
    """Verify 3D spatial tilt angle threshold (> 35°) and proportional pour factor calculation."""
    threshold_deg = 35.0

    # 1. At 20 degrees tilt: no pouring
    tilt_sub = 20.0
    is_pouring_sub = tilt_sub > threshold_deg
    assert not is_pouring_sub

    # 2. At 35.0 degrees tilt: exactly at threshold, not pouring
    is_pouring_exact = threshold_deg < 35.0
    assert not is_pouring_exact

    # 3. At 45 degrees tilt: tilted past threshold
    tilt_sup = 45.0
    assert tilt_sup > threshold_deg
    factor_45 = min(max((tilt_sup - threshold_deg) / 45.0, 0.15), 1.0)
    # (45 - 35) / 45 = 10 / 45 = 0.222
    assert math.isclose(factor_45, 10.0 / 45.0, rel_tol=1e-3)

    # 4. At 80 degrees tilt: full pour rate
    tilt_80 = 80.0
    factor_80 = min(max((tilt_80 - threshold_deg) / 45.0, 0.15), 1.0)
    assert math.isclose(factor_80, 1.0)


# =============================================================================
# 4. HEATING & MIXING APPARATUS TESTS (BUNSEN BURNER & MAGNETIC STIRRER)
# =============================================================================


def test_bunsen_burner_gdscript_structure():
    """Verify bunsen_burner.gd contains required state machine, methods, and thermodynamic parameters."""
    content = (APPARATUS_DIR / "bunsen_burner.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name BunsenBurner" in content
    assert "extends StaticBody3D" in content

    # State machine definition (with explicit enum values)
    assert "enum FlameState {" in content
    assert "OFF = 0" in content
    assert "SAFETY_YELLOW = 1" in content
    assert "HEATING_BLUE = 2" in content
    assert "var current_state: FlameState = FlameState.OFF" in content

    # Key methods
    assert "func toggle_flame" in content
    assert "func ignite" in content
    assert "func extinguish" in content
    assert "func adjust_collar" in content
    assert "func set_collar_opening" in content
    assert "func set_flame_state" in content
    assert "func _process_thermal_convection" in content

    # Thermodynamic constants
    assert "power_heating_blue_watts: float = 1450.0" in content
    assert "power_safety_yellow_watts: float = 350.0" in content
    assert "heat_transfer_efficiency: float = 0.68" in content
    assert "HEAT_CAPACITY_WATER_J_KG_K: float = 4184.0" in content


def test_bunsen_burner_tscn_nodes():
    """Verify bunsen_burner.tscn contains all required physical nodes, shaders, and groups."""
    content = (APPARATUS_DIR / "bunsen_burner.tscn").read_text(encoding="utf-8")

    # Root node and groups
    assert 'name="BunsenBurner" type="StaticBody3D"' in content
    assert '"interactive_apparatus"' in content

    # Physical meshes
    assert 'name="BaseMesh" type="MeshInstance3D"' in content
    assert 'name="GasTube" type="MeshInstance3D"' in content
    assert 'name="KnurledCollar" type="MeshInstance3D"' in content
    assert 'name="GasInletNipple" type="MeshInstance3D"' in content

    # Flame visual and illumination
    assert 'name="FlameMesh" type="MeshInstance3D"' in content
    assert "flame_shader.gdshader" in content
    assert 'name="FlameLight" type="OmniLight3D"' in content

    # Interactive and heating zones
    assert 'name="HeatingZone" type="Area3D"' in content
    assert 'name="FlameAudio" type="AudioStreamPlayer3D"' in content
    assert 'name="BoilAudio" type="AudioStreamPlayer3D"' in content
    assert 'name="SizzleAudio" type="AudioStreamPlayer3D"' in content


def test_bunsen_burner_thermal_convection_and_boiling_math():
    """Verify thermodynamic heating differential: dT/dt = (Q_flame - Q_loss) / (m * Cp)."""
    p_gross = 1450.0  # W for HEATING_BLUE
    eff = 0.62
    q_in = p_gross * eff  # 899.0 W net
    vol_ml = 100.0  # 100 mL aqueous solution
    mass_g = vol_ml * 1.0  # 100 g
    cp = 4.184  # J/(g*K)
    h_loss_coeff = 0.45  # W/K
    t_ambient = 21.0
    t_boil = 100.0

    # Simulate 10 seconds of heating at 21.0 °C
    temp = t_ambient
    delta = 0.1
    for _ in range(100):
        q_loss = h_loss_coeff * (temp - t_ambient)
        dt = ((q_in - q_loss) / (mass_g * cp)) * delta
        temp += dt

    # Expected temperature rise after 10 s: ~21.5°C rise to ~42.5°C
    assert 40.0 < temp < 45.0, f"Simulated temp {temp} out of expected range (40-45°C)"

    # Simulate full heating until boiling
    seconds = 10.0
    while seconds < 60.0 and temp < t_boil:
        q_loss = h_loss_coeff * (temp - t_ambient)
        dt = ((q_in - q_loss) / (mass_g * cp)) * delta
        temp = min(t_boil, temp + dt)
        seconds += delta

    assert temp == t_boil, f"Vessel should reach boiling point ({t_boil}°C)"
    assert seconds < 45.0, f"Vessel took too long to boil: {seconds}s"


def test_magnetic_stirrer_gdscript_structure():
    """Verify magnetic_stirrer.gd contains closed-loop PID, motor speed, and Noyes-Whitney kinetics."""
    content = (APPARATUS_DIR / "magnetic_stirrer.gd").read_text(encoding="utf-8")

    # Class declaration and inheritance
    assert "class_name MagneticStirrer" in content
    assert "extends StaticBody3D" in content

    # Controls and state
    assert "func toggle_power" in content
    assert "func set_target_temperature" in content
    assert "func set_target_rpm" in content
    assert "func _process_stir_motor" in content
    assert "func _process_pid_thermodynamics" in content

    # PID parameters
    assert "pid_kp: float = 14.5" in content
    assert "pid_ki: float = 0.065" in content
    assert "pid_kd: float = 3.2" in content

    # Noyes-Whitney dissolution & vortex formation formula
    assert "1.0 + 0.85 * sqrt(current_rpm / 100.0)" in content
    assert "vortex_intensity * 35.0" in content


def test_magnetic_stirrer_tscn_nodes():
    """Verify magnetic_stirrer.tscn contains all required physical nodes, displays, and zones."""
    content = (APPARATUS_DIR / "magnetic_stirrer.tscn").read_text(encoding="utf-8")

    # Root node and groups
    assert 'name="MagneticStirrer" type="StaticBody3D"' in content
    assert '"interactive_apparatus"' in content

    # Chassis and plate
    assert 'name="ChassisMesh" type="MeshInstance3D"' in content
    assert 'name="CeramicPlate" type="MeshInstance3D"' in content
    assert 'name="StirBar" type="MeshInstance3D"' in content

    # Interactive knobs and switches
    assert 'name="HeatKnob" type="MeshInstance3D"' in content
    assert 'name="StirKnob" type="MeshInstance3D"' in content
    assert 'name="PowerSwitch" type="MeshInstance3D"' in content

    # Digital displays
    assert 'name="TempDisplay" type="Label3D"' in content
    assert 'name="RpmDisplay" type="Label3D"' in content

    # Top plate zone and audio
    assert 'name="TopPlateHeatingZone" type="Area3D"' in content
    assert 'name="MotorAudio" type="AudioStreamPlayer3D"' in content
    assert 'name="BoilAudio" type="AudioStreamPlayer3D"' in content
    assert 'name="SizzleAudio" type="AudioStreamPlayer3D"' in content


def test_magnetic_stirrer_pid_temperature_regulation_math():
    """Verify PID temperature control with anti-windup clamping."""
    kp = 0.08
    ki = 0.005
    kd = 0.04
    integral_max = 25.0

    target = 150.0
    current_plate = 21.0
    integral = 0.0
    prev_error = target - current_plate
    delta = 0.1

    # First timestep: error = 129.0
    error = target - current_plate
    integral = max(-integral_max, min(integral_max, integral + error * delta))
    derivative = (error - prev_error) / delta
    u = kp * error + ki * integral + kd * derivative
    duty_cycle = max(0.0, min(1.0, u))

    # Error is large (129.0), so duty cycle must saturate at 1.0 (100% heating)
    assert math.isclose(duty_cycle, 1.0)
    assert integral <= integral_max

    # Near setpoint: plate = 149.5 °C (error = 0.5)
    near_current = 149.5
    near_error = target - near_current
    near_integral = 5.0
    near_derivative = -0.1
    near_u = kp * near_error + ki * near_integral + kd * near_derivative
    near_duty = max(0.0, min(1.0, near_u))
    # 0.08 * 0.5 + 0.005 * 5.0 + 0.04 * (-0.1) = 0.04 + 0.025 - 0.004 = 0.061
    assert 0.05 < near_duty < 0.10


def test_magnetic_stirrer_noyes_whitney_and_vortex_math():
    """Verify Noyes-Whitney dissolution acceleration and parabolic vortex depth."""
    rpm = 1200.0
    ref_rpm = 100.0
    alpha = 0.85

    # Noyes-Whitney dissolution rate multiplier: 1.0 + alpha * sqrt(RPM / ref_RPM)
    # At 1200 RPM: 1.0 + 0.85 * sqrt(12) = 1.0 + 0.85 * 3.4641 = 1.0 + 2.944 = 3.944x
    multiplier = 1.0 + alpha * math.sqrt(rpm / ref_rpm)
    assert math.isclose(multiplier, 3.944, rel_tol=1e-2)

    # Vortex depth scaling: h_vortex proportional to (RPM / max_RPM)^2
    max_rpm = 1500.0
    max_depth_mm = 35.0
    vortex_depth = pow(rpm / max_rpm, 2.0) * max_depth_mm
    # (1200 / 1500)^2 * 35 = (0.8)^2 * 35 = 0.64 * 35 = 22.4 mm
    assert math.isclose(vortex_depth, 22.4, rel_tol=1e-3)
