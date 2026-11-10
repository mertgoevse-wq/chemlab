"""
ChemLab Guided Synthesis Wizard & Measurement Confirmation Engine.
Enables players to manually measure, verify, and execute multi-stage chemical synthesis protocols.
Evaluates stoichiometric tolerances per difficulty tier and calculates yield degradation.
"""

from __future__ import annotations

from dataclasses import dataclass
from chemlab.compat import StrEnum, UTC

from chemlab.simulation.total_syntheses import SynthesisProtocol, SynthesisStage


class GuidanceTier(StrEnum):
    """Player guidance and tolerance difficulty tier."""

    STUDENT = "student"  # High guidance, ±15% tolerance window
    NOVICE = "novice"  # Moderate guidance, ±10% tolerance
    APPRENTICE = "apprentice"  # Standard guidance, ±5% tolerance
    ALCHEMIST = "alchemist"  # Minimal guidance, ±2.5% tolerance
    MASTER = "master"  # Expert blind synthesis, ±1.0% tolerance


class WizardStepState(StrEnum):
    """Current progression state within the active synthesis stage."""

    AWAITING_MEASUREMENTS = "awaiting_measurements"
    READY_TO_REACT = "ready_to_react"
    REACTING = "reacting"
    STAGE_COMPLETED = "stage_completed"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass(frozen=True)
class MeasurementInput:
    """User-measured quantity of a chemical reagent or solvent."""

    reagent_id: str
    measured_amount: float
    unit: str = "g"


# Reference standard amounts for known recipe stages
STAGE_REFERENCE_QUANTITIES: dict[tuple[str, int], dict[str, float]] = {
    # (protocol_id, stage_number) -> {reagent_id: standard_amount}
    ("aspirin", 1): {
        "salicylic_acid": 5.0,
        "acetic_anhydride": 7.0,
        "h2so4": 0.25,
    },
    ("aspirin", 2): {},
    ("aspirin", 3): {
        "ethanol": 10.0,
        "water": 20.0,
    },
    ("paracetamol", 1): {
        "aminophenol": 2.18,
        "acetic_anhydride": 2.17,
    },
    ("paracetamol", 2): {},
    ("indigo", 1): {
        "nitrobenzaldehyde": 1.0,
        "acetone": 10.0,
        "naoh": 5.0,
    },
}


class GuidedSynthesisSession:
    """
    Interactive session manager for guided multi-stage total syntheses.
    Handles player measurements, timing advances, temperature checkpoints, and final yield.
    """

    def __init__(
        self,
        protocol: SynthesisProtocol,
        tier: GuidanceTier = GuidanceTier.STUDENT,
    ) -> None:
        self.protocol = protocol
        self.tier = tier
        self.current_stage_index: int = 0
        self.step_state: WizardStepState = WizardStepState.AWAITING_MEASUREMENTS
        self.elapsed_time_s: float = 0.0
        self.overall_yield_percentage: float = 85.0
        self.yield_penalties: list[float] = []
        self.measurements_log: list[MeasurementInput] = []
        self._target_temp_c: float = 22.0

    @property
    def is_active(self) -> bool:
        return self.step_state not in (WizardStepState.FINISHED, WizardStepState.FAILED)

    @property
    def is_finished(self) -> bool:
        return self.step_state == WizardStepState.FINISHED

    @property
    def current_stage(self) -> SynthesisStage:
        return self.protocol.stages[self.current_stage_index]

    @property
    def current_step_name(self) -> str:
        return self.current_stage.name

    def get_tolerance_fraction(self) -> float:
        """Returns the allowable relative measurement error for the current tier."""
        match self.tier:
            case GuidanceTier.STUDENT:
                return 0.18
            case GuidanceTier.NOVICE:
                return 0.12
            case GuidanceTier.APPRENTICE:
                return 0.06
            case GuidanceTier.ALCHEMIST:
                return 0.03
            case GuidanceTier.MASTER:
                return 0.015

    def submit_measurements(
        self,
        measurements: list[MeasurementInput],
    ) -> tuple[bool, str]:
        """
        Validates the player's measured reagent inputs against the recipe standards.
        Grants passage to reaction state or issues targeted guidance.
        """
        self.measurements_log.extend(measurements)
        stage_num = self.current_stage.stage_number
        ref_dict = STAGE_REFERENCE_QUANTITIES.get((self.protocol.id, stage_num), {})

        # If stage requires no new reagents (e.g. ice-bath quench or filtration)
        if not ref_dict:
            self.step_state = WizardStepState.READY_TO_REACT
            return True, "Keine zusätzlichen Reagenzien erforderlich. Bereit für Prozessschritt."

        tolerance = self.get_tolerance_fraction()
        errors: list[str] = []
        measured_map = {m.reagent_id: m.measured_amount for m in measurements}

        # Check all required reagents
        for req_id, expected_val in ref_dict.items():
            if req_id not in measured_map:
                errors.append(f"Fehlendes Reagenz: {req_id}")
                continue

            actual_val = measured_map[req_id]
            deviation = abs(actual_val - expected_val) / max(0.001, expected_val)
            if deviation > tolerance:
                errors.append(
                    f"Menge von '{req_id}' ({actual_val}) weicht zu stark vom Sollwert ab (±{tolerance * 100:.1f}%)."
                )
            else:
                # Apply minor yield penalty for slight deviation
                penalty = deviation * 10.0
                self.yield_penalties.append(penalty)

        if errors:
            self.step_state = WizardStepState.AWAITING_MEASUREMENTS
            return False, f"Messfehler: {'; '.join(errors)}"

        self.step_state = WizardStepState.READY_TO_REACT
        return True, "Reagenzmengen präzise und korrekt abgewogen. Bereit zur Reaktion."

    def begin_reaction(self, temperature_c: float) -> None:
        """Sets target vessel temperature and begins chemical reaction timing."""
        self._target_temp_c = temperature_c
        self.elapsed_time_s = 0.0
        self.step_state = WizardStepState.REACTING

    def skip_time(self, seconds: float) -> bool:
        """
        Advances the simulation timeline for long reflux, stirring, or crystallization steps.
        Returns True once the stage's required duration is fulfilled.
        """
        if self.step_state != WizardStepState.REACTING:
            return False

        self.elapsed_time_s += max(0.0, seconds)
        req_duration = self.current_stage.duration_s

        if self.elapsed_time_s >= req_duration:
            self.step_state = WizardStepState.STAGE_COMPLETED
            return True

        return False

    def advance_to_next_stage(self) -> None:
        """Transitions to the subsequent stage or finalizes the synthesis protocol."""
        if self.step_state != WizardStepState.STAGE_COMPLETED:
            return

        self.current_stage_index += 1
        if self.current_stage_index >= len(self.protocol.stages):
            self.step_state = WizardStepState.FINISHED
            # Calculate final overall yield
            total_penalty = sum(self.yield_penalties)
            self.overall_yield_percentage = round(max(15.0, min(98.5, 88.0 - total_penalty)), 2)
        else:
            self.step_state = WizardStepState.AWAITING_MEASUREMENTS
