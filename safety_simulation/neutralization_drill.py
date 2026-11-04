"""
Chemical Spill Neutralization & Emergency Eyewash/Shower Drill Layer
Implements stoichiometric neutralization drills (Acid spill + Sodium Bicarbonate)
and ANSI Z358.1 compliant Emergency Eyewash and Safety Deluge Shower drills.
"""

import math
from dataclasses import dataclass, field
from enum import StrEnum

from .ghs import CHEMICAL_DATABASE


class SpillLocation(StrEnum):
    WORKBENCH = "WORKBENCH"
    FUME_HOOD_DECK = "FUME_HOOD_DECK"
    LAB_FLOOR = "LAB_FLOOR"


class StationType(StrEnum):
    EYEWASH = "EYEWASH"
    DELUGE_SHOWER = "DELUGE_SHOWER"
    BOTH = "BOTH"


class ExposureType(StrEnum):
    EYE_SPLASH = "EYE_SPLASH"
    SKIN_SPLASH = "SKIN_SPLASH"
    WHOLE_BODY_CLOTHING = "WHOLE_BODY_CLOTHING"


@dataclass
class NeutralizationState:
    acid_id: str
    initial_volume_liters: float
    acid_molarity: float  # mol/L
    initial_moles_h: float
    moles_h_remaining: float
    bicarbonate_added_grams: float = 0.0
    stoichiometric_grams_needed: float = 0.0
    current_ph: float = 1.0
    co2_gas_generated_liters: float = 0.0
    is_effervescing: bool = False
    reaction_temp_c: float = 20.0
    is_neutralized: bool = False  # pH between 6.0 and 8.5, effervescence ceased
    safe_for_cleanup: bool = False


@dataclass
class DrillScoreReport:
    drill_name: str
    passed: bool
    score_percentage: float
    ansi_compliant: bool
    feedback_notes: list[str] = field(default_factory=list)
    injury_severity_score: float = 0.0  # 0.0 = completely unharmed, 100.0 = irreversible necrosis/blindness


class AcidSpillNeutralizationDrill:
    """
    Simulation drill of an acid chemical spill and step-by-step
    stoichiometric neutralization using Sodium Bicarbonate (NaHCO3) powder.
    """

    MOLAR_MASS_NAHCO3: float = 84.007  # g/mol
    ENTHALPY_NEUTRALIZATION_KJ_MOL: float = -12.5  # mild exothermic heat

    def __init__(
        self,
        acid_id: str = "hydrochloric_acid",
        volume_liters: float = 0.50,
        molarity: float = 2.0,
        location: SpillLocation = SpillLocation.WORKBENCH
    ):
        self.acid_chem = CHEMICAL_DATABASE.get(acid_id, CHEMICAL_DATABASE["hydrochloric_acid"])
        self.volume_liters = volume_liters
        self.molarity = molarity
        self.location = location

        # Equivalence factor (HCl = 1, H2SO4 = 2, HNO3 = 1)
        self.proticity = 2 if acid_id == "sulfuric_acid" else 1

        initial_moles_acid = self.volume_liters * self.molarity
        initial_moles_h = initial_moles_acid * self.proticity

        # Theoretical mass of NaHCO3 required: moles_H * 84.007 g/mol
        self.grams_needed = initial_moles_h * self.MOLAR_MASS_NAHCO3

        # Initial pH
        initial_h_conc = initial_moles_h / self.volume_liters
        initial_ph = max(0.0, -math.log10(max(1e-7, initial_h_conc)))

        self.state = NeutralizationState(
            acid_id=acid_id,
            initial_volume_liters=volume_liters,
            acid_molarity=molarity,
            initial_moles_h=initial_moles_h,
            moles_h_remaining=initial_moles_h,
            bicarbonate_added_grams=0.0,
            stoichiometric_grams_needed=round(self.grams_needed, 2),
            current_ph=round(initial_ph, 2),
            co2_gas_generated_liters=0.0,
            is_effervescing=False,
            reaction_temp_c=20.0,
            is_neutralized=False,
            safe_for_cleanup=False
        )

        self.spill_spread_area_m2 = round(self.volume_liters * 1.8, 2)
        self.powder_dispersion_steps: list[float] = []

    def apply_sodium_bicarbonate(self, grams: float) -> NeutralizationState:
        """
        Dispenses a dose of sodium bicarbonate powder into the spill.
        Updates stoichiometry, reaction temperature, effervescence, and pH.
        """
        if grams <= 0:
            return self.state

        self.powder_dispersion_steps.append(grams)
        self.state.bicarbonate_added_grams += grams

        moles_nahco3_total = self.state.bicarbonate_added_grams / self.MOLAR_MASS_NAHCO3
        moles_h_init = self.state.initial_moles_h

        # Reactions:
        # HCl + NaHCO3 -> NaCl + H2O + CO2(g)
        # H2SO4 + 2 NaHCO3 -> Na2SO4 + 2 H2O + 2 CO2(g)
        moles_reacted = min(moles_h_init, moles_nahco3_total)
        self.state.moles_h_remaining = max(0.0, moles_h_init - moles_reacted)

        # CO2 gas generated: 1 mole CO2 per mole of H+ neutralized (24.45 L/mol at 20 C, 1 atm)
        self.state.co2_gas_generated_liters = round(moles_reacted * 24.45, 2)

        # Effervescence (active bubbling while acid is still being neutralized by new powder)
        if self.state.moles_h_remaining > 0.01:
            self.state.is_effervescing = True
        else:
            self.state.is_effervescing = False

        # Heat of reaction: delta T = (moles_reacted * delta_H) / (m_water * Cp)
        liquid_mass_g = self.volume_liters * 1000.0
        temp_rise_c = (moles_reacted * abs(self.ENTHALPY_NEUTRALIZATION_KJ_MOL) * 1000.0) / (liquid_mass_g * 4.184)
        self.state.reaction_temp_c = round(20.0 + min(35.0, temp_rise_c), 1)

        # pH Calculation curve
        if self.state.moles_h_remaining > 0.001:
            h_conc = self.state.moles_h_remaining / self.volume_liters
            ph = -math.log10(max(1e-7, h_conc))
        else:
            # Acid consumed. Excess NaHCO3 creates bicarbonate/carbonic acid buffer
            moles_excess_base = moles_nahco3_total - moles_h_init
            if moles_excess_base <= 0.01:
                ph = 7.0  # Perfectly neutral
            else:
                # Henderson-Hasselbalch buffer equation caps at approx 8.3 for pure NaHCO3
                ph = 7.0 + 1.3 * (1.0 - math.exp(-moles_excess_base * 5.0))

        self.state.current_ph = round(ph, 2)

        # Evaluation of complete neutralization
        if 6.0 <= self.state.current_ph <= 8.5 and not self.state.is_effervescing:
            self.state.is_neutralized = True
            self.state.safe_for_cleanup = True
        else:
            self.state.is_neutralized = False
            self.state.safe_for_cleanup = False

        return self.state

    def evaluate_drill_performance(self) -> DrillScoreReport:
        """Evaluates student/technician spill response performance."""
        feedback = []
        score = 100.0

        ratio = self.state.bicarbonate_added_grams / max(1.0, self.grams_needed)

        if ratio < 0.95:
            score -= 40.0
            feedback.append(
                f"UNDER-NEUTRALIZED: Added {self.state.bicarbonate_added_grams:.1f}g, needed {self.grams_needed:.1f}g. "
                f"Current pH {self.state.current_ph:.2f} remains corrosive!"
            )
        elif ratio > 2.0:
            score -= 15.0
            feedback.append(
                f"EXCESSIVE REAGENT: Added {self.state.bicarbonate_added_grams:.1f}g ({ratio*100:.0f}% of requirement). "
                "Wasteful chemical utilization, though pH stabilized safely."
            )
        else:
            feedback.append(f"OPTIMAL DOSAGE: {self.state.bicarbonate_added_grams:.1f}g accurately neutralized the spill.")

        if len(self.powder_dispersion_steps) < 2:
            score -= 10.0
            feedback.append("TECHNIQUE: Powder applied in a single dump. Recommended: Ring perimeter first, then neutralize inward.")
        else:
            feedback.append("TECHNIQUE: Incremental controlled application prevented boiling/splatter.")

        passed = self.state.safe_for_cleanup and score >= 70.0
        return DrillScoreReport(
            drill_name="Acid Spill Neutralization (NaHCO3)",
            passed=passed,
            score_percentage=max(0.0, round(score, 1)),
            ansi_compliant=passed,
            feedback_notes=feedback,
            injury_severity_score=0.0 if passed else 25.0
        )


class EmergencyShowerEyewashDrill:
    """
    Simulates ANSI Z358.1 Emergency Eyewash and Deluge Shower operation
    during a chemical exposure incident.
    """

    ANSI_REQUIRED_FLUSH_SECONDS: float = 900.0  # 15 minutes continuous flush
    ANSI_MAX_RESPONSE_TIME_SECONDS: float = 10.0  # Must reach station within 10s
    SHOWER_FLOW_RATE_LPM: float = 76.0  # 20 gpm
    EYEWASH_FLOW_RATE_LPM: float = 2.0  # 0.5 gpm

    def __init__(
        self,
        exposure_type: ExposureType = ExposureType.EYE_SPLASH,
        chemical_id: str = "hydrochloric_acid",
        initial_distance_meters: float = 6.0
    ):
        self.exposure_type = exposure_type
        self.chem = CHEMICAL_DATABASE.get(chemical_id, CHEMICAL_DATABASE["hydrochloric_acid"])
        self.initial_distance_meters = initial_distance_meters

        # Incident status
        self.time_to_reach_station_s: float = 0.0
        self.activated_station: StationType | None = None
        self.flush_duration_seconds: float = 0.0
        self.clothing_removed: bool = False
        self.water_temp_c: float = 21.0  # Tepid water range (16 - 38 C)
        self.alarm_sounded: bool = False

    def travel_to_station(self, walking_speed_mps: float = 1.2) -> float:
        """Simulates worker transit from incident site to safety station."""
        self.time_to_reach_station_s = round(self.initial_distance_meters / max(0.5, walking_speed_mps), 1)
        return self.time_to_reach_station_s

    def activate_eyewash(self) -> None:
        """Engages push flag plate to activate dual aerated eyewash spray."""
        self.activated_station = StationType.EYEWASH
        self.alarm_sounded = True

    def activate_shower(self) -> None:
        """Pulls triangular overhead rod to activate deluge emergency shower."""
        self.activated_station = StationType.DELUGE_SHOWER
        self.alarm_sounded = True

    def remove_contaminated_clothing(self) -> None:
        """Removes chemical-soaked laboratory coat and garments under shower stream."""
        self.clothing_removed = True

    def run_flush(self, seconds: float) -> float:
        """Flushes eyes/body for specified seconds."""
        if self.activated_station is not None:
            self.flush_duration_seconds += seconds
        return self.flush_duration_seconds

    def evaluate_drill(self) -> DrillScoreReport:
        """
        Audits performance against ANSI Z358.1 guidelines and computes
        physiological injury severity score.
        """
        feedback = []
        score = 100.0
        injury_score = 0.0

        # 1. Travel Time Audit (ANSI < 10 seconds)
        if self.time_to_reach_station_s > self.ANSI_MAX_RESPONSE_TIME_SECONDS:
            penalty = min(40.0, (self.time_to_reach_station_s - 10.0) * 4.0)
            score -= penalty
            injury_score += (self.time_to_reach_station_s - 10.0) * 3.5
            feedback.append(
                f"TRANSIT DELAY: Reached station in {self.time_to_reach_station_s}s (ANSI Z358.1 limit: 10s). "
                "Corrosive chemical had extended dwell time on tissue!"
            )
        else:
            feedback.append(f"RAPID RESPONSE: Reached safety station in {self.time_to_reach_station_s}s (< 10s compliance).")

        # 2. Appropriate Station Selection
        if self.exposure_type == ExposureType.EYE_SPLASH:
            if self.activated_station not in [StationType.EYEWASH, StationType.BOTH]:
                score -= 50.0
                injury_score += 45.0
                feedback.append("CRITICAL ERROR: High-pressure overhead shower used for ocular chemical splash! Aerated eyewash required to prevent mechanical corneal trauma.")
            else:
                feedback.append("CORRECT FIXTURE: Dual aerated eyewash activated for eye decontamination.")
        elif self.exposure_type in [ExposureType.WHOLE_BODY_CLOTHING, ExposureType.SKIN_SPLASH]:
            if self.activated_station not in [StationType.DELUGE_SHOWER, StationType.BOTH]:
                score -= 50.0
                injury_score += 50.0
                feedback.append("CRITICAL ERROR: Small eyewash basin selected for torso chemical exposure! Deluge shower required.")
            else:
                feedback.append("CORRECT FIXTURE: 76 L/min Deluge shower engaged.")

        # 3. Clothing Removal Audit
        if self.exposure_type == ExposureType.WHOLE_BODY_CLOTHING and not self.clothing_removed:
            score -= 25.0
            injury_score += 25.0
            feedback.append("CONTAMINATION RETENTION: Chemical-soaked clothing was not removed under shower. Garment trapped corrosive acid against skin.")
        elif self.clothing_removed:
            feedback.append("PROPER PROTOCOL: Contaminated garments stripped immediately under deluge flow.")

        # 4. Flush Duration Audit (ANSI 15 minutes = 900 seconds)
        if self.flush_duration_seconds < self.ANSI_REQUIRED_FLUSH_SECONDS:
            flush_pct = (self.flush_duration_seconds / self.ANSI_REQUIRED_FLUSH_SECONDS)
            penalty = (1.0 - flush_pct) * 40.0
            score -= penalty
            injury_score += (1.0 - flush_pct) * 30.0
            feedback.append(
                f"INSUFFICIENT FLUSH: Flushed for {self.flush_duration_seconds/60:.1f} min (ANSI standard: 15.0 min / 900s). "
                "Subsurface caustic absorption may continue without full 15-minute irrigation."
            )
        else:
            feedback.append("FULL IRRIGATION: Completed required 15-minute (900s) continuous flush.")

        injury_score = max(0.0, min(100.0, round(injury_score, 1)))
        final_score = max(0.0, min(100.0, round(score, 1)))
        ansi_pass = (final_score >= 80.0 and injury_score <= 10.0)

        return DrillScoreReport(
            drill_name=f"ANSI Z358.1 {self.exposure_type.value} Response",
            passed=ansi_pass,
            score_percentage=final_score,
            ansi_compliant=ansi_pass,
            feedback_notes=feedback,
            injury_severity_score=injury_score
        )
