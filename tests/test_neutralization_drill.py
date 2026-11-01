"""
Unit tests for Acid Spill Neutralization Drills (NaHCO3) and ANSI Z358.1 Emergency Eyewash & Shower.
"""

import pytest

from safety_simulation.neutralization_drill import (
    AcidSpillNeutralizationDrill,
    EmergencyShowerEyewashDrill,
    ExposureType,
    SpillLocation,
    StationType,
)


def test_acid_spill_initial_state():
    """Verify acid spill sets proper initial molarity, stoichiometric NaHCO3 needed, and acidic pH."""
    drill = AcidSpillNeutralizationDrill(
        acid_id="hydrochloric_acid", volume_liters=0.50, molarity=2.0
    )

    # 0.50 L * 2.0 mol/L = 1.0 mole HCl
    # 1.0 mole * 84.007 g/mol = 84.01 g NaHCO3 needed
    assert abs(drill.grams_needed - 84.01) < 0.1
    assert drill.state.current_ph <= 0.5
    assert not drill.state.is_neutralized
    assert not drill.state.safe_for_cleanup


def test_stepwise_sodium_bicarbonate_neutralization():
    """Verify incremental addition of NaHCO3 neutralizes acid and generates CO2 effervescence."""
    drill = AcidSpillNeutralizationDrill(
        acid_id="hydrochloric_acid", volume_liters=0.50, molarity=2.0
    )

    # Step 1: Add 40g (approx half)
    state_1 = drill.apply_sodium_bicarbonate(40.0)
    assert state_1.is_effervescing is True
    assert state_1.co2_gas_generated_liters > 5.0
    assert state_1.current_ph < 3.0  # still strongly acidic
    assert not state_1.is_neutralized

    # Step 2: Add remaining ~45g (total 85g)
    state_2 = drill.apply_sodium_bicarbonate(45.0)
    assert 6.5 <= state_2.current_ph <= 8.5
    assert state_2.is_neutralized is True
    assert state_2.safe_for_cleanup is True


def test_diprotic_sulfuric_acid_stoichiometry():
    """Verify H2SO4 requires 2 equivalents of NaHCO3 per mole of acid."""
    drill = AcidSpillNeutralizationDrill(
        acid_id="sulfuric_acid",
        volume_liters=0.50,
        molarity=1.0,  # 0.50 moles H2SO4 -> 1.0 mole H+
    )

    # Needs 1.0 mole NaHCO3 = 84.01 g
    assert abs(drill.grams_needed - 84.01) < 0.1


def test_neutralization_drill_performance_evaluation():
    """Verify performance scoring grades optimal application vs under-addition."""
    drill = AcidSpillNeutralizationDrill(
        acid_id="hydrochloric_acid", volume_liters=0.20, molarity=1.0
    )
    # 0.2 mole -> 16.8 g needed

    # Proper 2-step application
    drill.apply_sodium_bicarbonate(10.0)
    drill.apply_sodium_bicarbonate(7.0)

    report = drill.evaluate_drill_performance()
    assert report.passed is True
    assert report.score_percentage >= 80.0
    assert report.injury_severity_score == 0.0


def test_eyewash_drill_perfect_compliance():
    """Verify ANSI Z358.1 compliant execution of eyewash drill: reach < 10s, correct fixture, 15 min flush."""
    drill = EmergencyShowerEyewashDrill(
        exposure_type=ExposureType.EYE_SPLASH,
        chemical_id="hydrochloric_acid",
        initial_distance_meters=6.0,  # 6m / 1.2 m/s = 5s
    )

    drill.travel_to_station(walking_speed_mps=1.2)
    assert drill.time_to_reach_station_s <= 10.0

    # Activate eyewash
    drill.activate_eyewash()
    assert drill.activated_station == StationType.EYEWASH

    # Flush full 15 minutes (900 seconds)
    drill.run_flush(900.0)
    assert drill.flush_duration_seconds == 900.0

    report = drill.evaluate_drill()
    assert report.passed is True
    assert report.score_percentage == 100.0
    assert report.ansi_compliant is True
    assert report.injury_severity_score == 0.0


def test_shower_drill_failure_delayed_and_wrong_fixture():
    """Verify non-compliance penalties for delayed transit, wrong fixture, or insufficient flush."""
    drill = EmergencyShowerEyewashDrill(
        exposure_type=ExposureType.WHOLE_BODY_CLOTHING,
        chemical_id="sulfuric_acid",
        initial_distance_meters=20.0,
    )

    # Slow walking -> takes > 10 seconds
    drill.travel_to_station(walking_speed_mps=1.0)
    assert drill.time_to_reach_station_s > 10.0

    # User accidentally activated eyewash instead of deluge shower
    drill.activate_eyewash()

    # Flushed only 2 minutes (120s) instead of 15 min
    drill.run_flush(120.0)

    report = drill.evaluate_drill()
    assert report.passed is False
    assert report.ansi_compliant is False
    assert report.injury_severity_score > 30.0
    assert any("critical error" in note.lower() for note in report.feedback_notes)
