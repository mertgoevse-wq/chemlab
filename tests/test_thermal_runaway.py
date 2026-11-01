"""
Unit tests for Thermal Runaway, Vapor Pressure Buildup, Stopper Pop, and Relief Valve Mechanics.
"""

import pytest

from safety_simulation.thermal_runaway import (
    ReliefType,
    ThermalVesselSimulation,
    VesselState,
    VesselType,
)


def test_pressure_buildup_and_stopper_pop():
    """Verify closed stoppered vessel builds pressure when heated until ground-glass stopper pops."""
    vessel = ThermalVesselSimulation(
        vessel_id="test_flask",
        vessel_type=VesselType.ERLENMEYER_FLASK_STOPPERED,
        relief_type=ReliefType.GROUND_GLASS_STOPPER,
        chemical_id="acetone",
        total_volume_ml=500.0,
        liquid_volume_ml=200.0,
        stopper_pop_pressure_kpa=140.0,
    )

    # Initial state at 20 C
    assert vessel.state == VesselState.NORMAL
    assert vessel.pressure_kpa < 130.0
    assert not vessel.stopper_popped

    # Apply 400W heat from Bunsen burner
    vessel.set_heat_source(400.0)

    popped = False
    for step in range(300):  # simulate 30 seconds
        state = vessel.update(dt=0.1)
        if state == VesselState.STOPPER_POPPED:
            popped = True
            break

    assert popped, "Stopper must pop when pressure reaches pop limit"
    assert vessel.stopper_popped is True
    assert vessel.last_pop_report is not None
    assert vessel.last_pop_report.launch_velocity_mps > 0.0
    assert vessel.last_pop_report.peak_height_m > 0.0
    assert len(vessel.last_pop_report.trajectory) > 5
    # Pressure relieved to atmospheric after pop
    assert vessel.pressure_kpa == vessel.ATMOSPHERIC_PRESSURE_KPA


def test_spring_relief_valve_venting():
    """Verify pressure vessel with spring relief valve vents gas without exploding."""
    vessel = ThermalVesselSimulation(
        vessel_id="test_autoclave",
        vessel_type=VesselType.AUTOCLAVE_PRESSURE_REACTOR,
        relief_type=ReliefType.SPRING_RELIEF_VALVE,
        chemical_id="acetone",
        liquid_volume_ml=100.0,
        burst_pressure_kpa=800.0,
        valve_relief_pressure_kpa=220.0,
    )

    vessel.set_heat_source(600.0)

    vented = False
    for _ in range(400):
        state = vessel.update(dt=0.1)
        if state == VesselState.VALVE_VENTING or vessel.valve_open:
            vented = True
            break

    assert vented, "Spring relief valve must open when setpoint is exceeded"
    assert not vessel.ruptured, "Vessel with relief valve must not explode"


def test_catastrophic_rupture_on_sealed_vessel_without_relief():
    """Verify sealed vessel with no relief mechanism suffers catastrophic BLEVE explosion."""
    vessel = ThermalVesselSimulation(
        vessel_id="test_sealed_tube",
        vessel_type=VesselType.SEALED_TEST_TUBE,
        relief_type=ReliefType.SEALED_NO_RELIEF,
        chemical_id="acetone",
        burst_pressure_kpa=220.0,  # low burst rating for thin glass
    )

    vessel.set_heat_source(600.0)

    exploded = False
    for _ in range(300):
        state = vessel.update(dt=0.1)
        if state == VesselState.CATASTROPHIC_EXPLOSION:
            exploded = True
            break

    assert exploded, "Sealed rigid container must explode when exceeding burst pressure"
    assert vessel.ruptured is True
    report = vessel.last_rupture_report
    assert report is not None
    assert report.rupture_occurred is True
    assert report.explosion_energy_joules > 0.0
    assert report.blast_radius_m > 0.0
    assert report.shrapnel_count > 0
    assert len(report.fragments) == report.shrapnel_count


def test_exothermic_thermal_runaway_acceleration():
    """Verify self-accelerating Arrhenius reaction triggers THERMAL_RUNAWAY state."""
    vessel = ThermalVesselSimulation(
        vessel_id="runaway_reactor",
        vessel_type=VesselType.AUTOCLAVE_PRESSURE_REACTOR,
        relief_type=ReliefType.SPRING_RELIEF_VALVE,
        chemical_id="nitric_acid",
        initial_temp_c=55.0,  # already warm
    )

    # Inject high exothermic heat of decomposition
    vessel.trigger_exothermic_reaction(delta_h_kj_mol=220.0)

    runaway_seen = False
    for _ in range(200):
        state = vessel.update(dt=0.05)
        if vessel.runaway_detected or state == VesselState.THERMAL_RUNAWAY:
            runaway_seen = True
            break

    assert runaway_seen, "Exothermic reaction must trigger THERMAL_RUNAWAY acceleration"
