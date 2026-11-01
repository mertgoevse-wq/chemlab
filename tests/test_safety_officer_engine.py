"""
Unit tests for Chemical Safety Officer coordinator engine and telemetry.
"""

import pytest

from safety_simulation.fume_hood import FumeHoodAlarmState
from safety_simulation.neutralization_drill import ExposureType
from safety_simulation.safety_officer_engine import ChemicalSafetyOfficerEngine, SafetyIncidentEvent
from safety_simulation.thermal_runaway import ReliefType, VesselState, VesselType


def test_safety_officer_engine_initialization_and_events():
    """Verify engine initializes subsystems and dispatches events to subscribers."""
    engine = ChemicalSafetyOfficerEngine()
    events_received = []

    def on_event(ev: SafetyIncidentEvent):
        events_received.append(ev)

    engine.subscribe_events(on_event)

    # Incompatibility test
    incomp = engine.audit_chemical_interaction("nitric_acid", "ethanol")
    assert not incomp.compatible
    assert len(events_received) == 1
    assert events_received[0].event_type == "GHS_INCOMPATIBILITY_ALERT"


def test_engine_fume_hood_and_vessel_tick():
    """Verify engine tick advances state, triggers stopper pop event, and exports telemetry."""
    engine = ChemicalSafetyOfficerEngine()
    events = []
    engine.subscribe_events(lambda ev: events.append(ev))

    # Add chemical to hood and open sash high
    hood = engine.fume_hoods["hood_primary"]
    hood.add_chemical("diethyl_ether")
    state = engine.set_fume_hood_sash("hood_primary", 0.65)
    assert state.alarm_state == FumeHoodAlarmState.ALARM_SASH_TOO_HIGH_VOLATILE

    # Register heated stoppered vessel
    vessel = engine.register_vessel(
        vessel_id="test_flask_1",
        chemical_id="acetone",
        relief_type=ReliefType.GROUND_GLASS_STOPPER,
        burst_pressure_kpa=400.0,
    )
    engine.heat_vessel("test_flask_1", watts=600.0)

    # Tick simulation until stopper pops
    popped = False
    for _ in range(250):
        telem = engine.tick(dt=0.1)
        if vessel.stopper_popped:
            popped = True
            break

    assert popped
    assert any(ev.event_type == "STOPPER_POPPED_PRESSURE_RELIEF" for ev in events)

    # Telemetry verification
    telemetry = engine.get_telemetry()
    assert "hood_primary" in telemetry["fume_hoods"]
    assert "test_flask_1" in telemetry["pressure_vessels"]
    assert telemetry["pressure_vessels"]["test_flask_1"]["stopper_popped"] is True


def test_engine_acid_spill_and_neutralization_lifecycle():
    """Verify acid spill drill creation, step-by-step NaHCO3 treatment, and completion through engine."""
    engine = ChemicalSafetyOfficerEngine()
    drill = engine.create_acid_spill(
        spill_id="spill_bench_01", acid_id="hydrochloric_acid", volume_liters=0.25, molarity=1.0
    )

    assert "spill_bench_01" in engine.active_spills
    assert drill.grams_needed > 0

    # Neutralize
    report = engine.neutralize_spill("spill_bench_01", drill.grams_needed * 1.05)
    assert report.passed is True
    telem = engine.get_telemetry()
    assert telem["active_spills"]["spill_bench_01"]["is_neutralized"] is True
    assert telem["active_spills"]["spill_bench_01"]["safe_for_cleanup"] is True
