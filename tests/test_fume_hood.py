"""
Unit tests for Fume Hood Aerodynamics, Sash Height Detection, and Streamline Draft Animation.
"""

import pytest

from safety_simulation.fume_hood import (
    AirflowVector3D,
    FumeHoodAlarmState,
    FumeHoodMode,
    FumeHoodSimulation,
)


def test_fume_hood_nominal_operation():
    """Verify standard sash operating height maintains target face velocity and SAFE status."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.set_sash_height(0.35)  # 35 cm (below 45 cm limit)
    state = hood.update()

    assert state.sash_height_m == 0.35
    assert state.alarm_state == FumeHoodAlarmState.SAFE
    assert 0.40 <= state.face_velocity_mps <= 0.60
    assert state.containment_efficiency > 0.99
    assert state.vapor_leakage_rate_g_s == 0.0


def test_sash_elevated_warning_without_volatiles():
    """Verify warning triggered when sash is opened above 0.45m without volatile solvents."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.set_sash_height(0.60)  # 60 cm (above 45 cm limit)
    state = hood.update()

    assert state.alarm_state == FumeHoodAlarmState.WARNING_SASH_ELEVATED
    assert len(state.active_warnings) > 0
    assert "exceeds safe working line" in state.active_warnings[0].lower()


def test_sash_too_high_with_volatile_solvents_alarm():
    """Verify CRITICAL alarm and toxic vapor escape when sash opened high with volatile solvents."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.add_chemical("diethyl_ether")  # Highly volatile (VP = 58.9 kPa)
    hood.add_chemical("acetone")

    # Raise sash to 0.70m
    hood.set_sash_height(0.70)
    state = hood.update()

    assert state.alarm_state == FumeHoodAlarmState.ALARM_SASH_TOO_HIGH_VOLATILE
    assert state.containment_efficiency < 0.90
    assert state.vapor_leakage_rate_g_s > 0.0
    assert any("vapor escape" in w.lower() or "danger" in w.lower() for w in state.active_warnings)


def test_emergency_purge_mode():
    """Verify emergency purge button triggers maximum exhaust and overrides alarm state."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.add_chemical("diethyl_ether")
    hood.set_sash_height(0.75)
    hood.toggle_purge(True)
    state = hood.update()

    assert state.purge_active is True
    assert state.alarm_state == FumeHoodAlarmState.EMERGENCY_PURGE
    assert state.exhaust_flow_rate_m3s >= 0.80
    assert state.containment_efficiency == 1.0


def test_velocity_field_sampling():
    """Verify 3D aerodynamic velocity vector calculations."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.set_sash_height(0.35)
    hood.update()

    # Point in front of sash opening
    vec_front = hood.sample_velocity_field(0.0, -0.60, 0.20)
    assert vec_front.vy > 0.0, "Air in front of hood must be pulled inward towards +Y"

    # Point inside hood near rear baffle
    vec_inside = hood.sample_velocity_field(0.0, 0.20, 0.50)
    assert vec_inside.vy > 0.0, "Air inside must flow towards back wall"
    assert vec_inside.vz > 0.0, "Air near baffles must flow upward towards duct"


def test_generate_draft_streamlines():
    """Verify generation of 3D streamline paths for Blender / Godot animation."""
    hood = FumeHoodSimulation(mode=FumeHoodMode.VAV)
    hood.set_sash_height(0.40)
    hood.update()

    streamlines = hood.generate_draft_streamlines(num_streamlines=10, steps=30)
    assert len(streamlines) > 0
    for line in streamlines:
        assert len(line) >= 3, "Streamline must have multiple 3D coordinate points"
        # Each point is a 3-tuple (x, y, z)
        for pt in line:
            assert len(pt) == 3
            assert isinstance(pt[0], float)
