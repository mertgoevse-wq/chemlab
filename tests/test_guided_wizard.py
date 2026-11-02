"""
Unit tests for the ChemLab Guided Synthesis Wizard.
Tests player measurement entry, stoichiometric verification, phase transitions,
time-skip mechanics for multi-hour reactions, and guidance feedback.
"""

from __future__ import annotations

import pytest

from chemlab.simulation.total_syntheses import SynthesisRegistry
from chemlab.synthesis.guided_wizard import (
    GuidanceTier,
    GuidedSynthesisSession,
    MeasurementInput,
    WizardStepState,
)


def test_wizard_initialization_aspirin() -> None:
    registry = SynthesisRegistry()
    protocol = registry.get_protocol("aspirin")
    session = GuidedSynthesisSession(protocol=protocol, tier=GuidanceTier.STUDENT)

    assert session.current_stage_index == 0
    assert session.is_active
    assert not session.is_finished
    assert session.current_step_name == "Elektrophile O-Acylierung"


def test_player_measurement_confirmation_accurate() -> None:
    registry = SynthesisRegistry()
    protocol = registry.get_protocol("aspirin")
    session = GuidedSynthesisSession(protocol=protocol, tier=GuidanceTier.STUDENT)

    # Player measures 5.00 g salicylic acid (target: 5.0 g)
    measurements = [
        MeasurementInput(reagent_id="salicylic_acid", measured_amount=5.00, unit="g"),
        MeasurementInput(reagent_id="acetic_anhydride", measured_amount=7.00, unit="mL"),
        MeasurementInput(reagent_id="h2so4", measured_amount=0.25, unit="mL"),
    ]
    verified, feedback = session.submit_measurements(measurements)
    assert verified
    assert "präzise" in feedback.lower() or "korrekt" in feedback.lower()
    assert session.step_state == WizardStepState.READY_TO_REACT


def test_player_measurement_deviation_warning() -> None:
    registry = SynthesisRegistry()
    protocol = registry.get_protocol("aspirin")
    session = GuidedSynthesisSession(protocol=protocol, tier=GuidanceTier.STUDENT)

    # Player under-measures salicylic acid by 40%
    measurements = [
        MeasurementInput(reagent_id="salicylic_acid", measured_amount=3.00, unit="g"),
        MeasurementInput(reagent_id="acetic_anhydride", measured_amount=7.00, unit="mL"),
        MeasurementInput(reagent_id="h2so4", measured_amount=0.25, unit="mL"),
    ]
    verified, feedback = session.submit_measurements(measurements)
    assert not verified
    assert "weicht" in feedback.lower() or "fehler" in feedback.lower() or "ab" in feedback.lower()
    assert session.step_state == WizardStepState.AWAITING_MEASUREMENTS


def test_time_skip_mechanic_advances_reaction() -> None:
    registry = SynthesisRegistry()
    protocol = registry.get_protocol("aspirin")
    session = GuidedSynthesisSession(protocol=protocol, tier=GuidanceTier.STUDENT)

    # Submit valid measurements
    session.submit_measurements(
        [
            MeasurementInput(reagent_id="salicylic_acid", measured_amount=5.0, unit="g"),
            MeasurementInput(reagent_id="acetic_anhydride", measured_amount=7.0, unit="mL"),
            MeasurementInput(reagent_id="h2so4", measured_amount=0.25, unit="mL"),
        ]
    )

    # Start reaction
    session.begin_reaction(temperature_c=65.0)
    assert session.step_state == WizardStepState.REACTING

    # Skip 60 seconds (duration of stage 1)
    finished = session.skip_time(seconds=60.0)
    assert finished
    assert session.step_state == WizardStepState.STAGE_COMPLETED


def test_wizard_progression_through_all_stages() -> None:
    registry = SynthesisRegistry()
    protocol = registry.get_protocol("paracetamol")
    session = GuidedSynthesisSession(protocol=protocol, tier=GuidanceTier.STUDENT)

    # Stage 1: Acylation
    session.submit_measurements(
        [
            MeasurementInput(reagent_id="aminophenol", measured_amount=2.18, unit="g"),
            MeasurementInput(reagent_id="acetic_anhydride", measured_amount=2.17, unit="mL"),
        ]
    )
    session.begin_reaction(temperature_c=60.0)
    session.skip_time(seconds=50.0)
    session.advance_to_next_stage()

    # Stage 2: Ice bath quenching
    assert session.current_stage_index == 1
    session.submit_measurements([])  # No additional inputs for stage 2
    session.begin_reaction(temperature_c=0.0)
    session.skip_time(seconds=30.0)
    session.advance_to_next_stage()

    assert session.is_finished
    assert session.overall_yield_percentage > 70.0
