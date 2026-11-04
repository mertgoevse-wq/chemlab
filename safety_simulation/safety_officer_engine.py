"""
Industrial Chemical Safety Officer & Systems Architecture Engine
Coordinates GHS hazard management, fume hood ventilation, thermal runaway & pressure vessel dynamics,
neutralization drills, emergency eyewash/shower stations, and real-time laboratory telemetry.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .fume_hood import FumeHoodAlarmState, FumeHoodMode, FumeHoodSimulation, FumeHoodState
from .ghs import IncompatibilityResult, check_chemical_compatibility, get_chemical_sds
from .neutralization_drill import (
    AcidSpillNeutralizationDrill,
    DrillScoreReport,
    EmergencyShowerEyewashDrill,
    ExposureType,
    SpillLocation,
)
from .thermal_runaway import ReliefType, ThermalVesselSimulation, VesselState, VesselType


@dataclass
class SafetyIncidentEvent:
    timestamp: float
    event_type: str
    severity: str  # "INFO", "WARNING", "CRITICAL", "CATASTROPHIC"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class ChemicalSafetyOfficerEngine:
    """
    Central Systems Architecture for the Chemical Safety & Hazard Simulation.
    Acts as the simulated Industrial Chemical Safety Officer (EHS Director).
    """

    def __init__(self):
        # Subsystems
        self.fume_hoods: dict[str, FumeHoodSimulation] = {
            "hood_primary": FumeHoodSimulation(mode=FumeHoodMode.VAV, center_x=-2.2, center_y=3.35)
        }
        self.vessels: dict[str, ThermalVesselSimulation] = {}
        self.active_spills: dict[str, AcidSpillNeutralizationDrill] = {}
        self.active_drills: dict[str, EmergencyShowerEyewashDrill] = {}

        # Event bus & Incident log
        self.event_log: list[SafetyIncidentEvent] = []
        self._listeners: list[Callable[[SafetyIncidentEvent], None]] = []

        # Overall Laboratory Safety Status
        self.emergency_alarm_active: bool = False
        self.evacuation_order: bool = False

    def subscribe_events(self, listener: Callable[[SafetyIncidentEvent], None]) -> None:
        """Subscribes a callback to safety events (alarms, pop events, spills, etc.)."""
        self._listeners.append(listener)

    def dispatch_event(self, event_type: str, severity: str, message: str, details: dict[str, Any] | None = None) -> SafetyIncidentEvent:
        event = SafetyIncidentEvent(
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            message=message,
            details=details or {}
        )
        self.event_log.append(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Error in event listener: {e}")
        return event

    # =========================================================================
    # 1. GHS HAZARD EVALUATION
    # =========================================================================
    def audit_chemical_interaction(self, chem_a_id: str, chem_b_id: str) -> IncompatibilityResult:
        """Audits compatibility between two chemicals before mixing or co-storing."""
        result = check_chemical_compatibility(chem_a_id, chem_b_id)
        if not result.compatible:
            severity = "CATASTROPHIC" if result.risk_level == "CRITICAL" else "WARNING"
            self.dispatch_event(
                event_type="GHS_INCOMPATIBILITY_ALERT",
                severity=severity,
                message=f"Incompatible combination: {chem_a_id} + {chem_b_id} -> {result.reaction_type}",
                details={"risk_level": result.risk_level, "hazard": result.hazard_description, "byproducts": result.byproducts}
            )
        return result

    def get_sds(self, chemical_id: str) -> dict[str, Any]:
        """Returns standard OSHA Safety Data Sheet summary."""
        return get_chemical_sds(chemical_id)

    # =========================================================================
    # 2. FUME HOOD MANAGEMENT
    # =========================================================================
    def set_fume_hood_sash(self, hood_id: str, height_meters: float) -> FumeHoodState:
        """Sets fume hood sash height and evaluates face velocity / alarms."""
        hood = self.fume_hoods.get(hood_id)
        if not hood:
            raise ValueError(f"Fume hood {hood_id} not found.")

        hood.set_sash_height(height_meters)
        state = hood.update(dt=0.016)

        if state.alarm_state == FumeHoodAlarmState.ALARM_SASH_TOO_HIGH_VOLATILE:
            self.dispatch_event(
                event_type="FUME_HOOD_SASH_DANGER",
                severity="CRITICAL",
                message=f"Sash too high ({state.sash_height_m*100:.0f}cm) with volatile chemicals inside! Vapor leak: {state.vapor_leakage_rate_g_s} g/s",
                details={"hood_id": hood_id, "sash_height_m": state.sash_height_m, "leakage_g_s": state.vapor_leakage_rate_g_s}
            )
        elif state.alarm_state == FumeHoodAlarmState.WARNING_SASH_ELEVATED:
            self.dispatch_event(
                event_type="FUME_HOOD_SASH_WARNING",
                severity="WARNING",
                message=f"Sash elevated above safe working threshold: {state.sash_height_m*100:.0f}cm",
                details={"hood_id": hood_id, "sash_height_m": state.sash_height_m}
            )

        return state

    def trigger_fume_hood_purge(self, hood_id: str) -> bool:
        """Triggers emergency high-volume purge exhaust."""
        hood = self.fume_hoods.get(hood_id)
        if not hood:
            raise ValueError(f"Fume hood {hood_id} not found.")
        active = hood.toggle_purge(True)
        self.dispatch_event(
            event_type="FUME_HOOD_PURGE_ACTIVATED",
            severity="WARNING",
            message=f"Emergency purge activated on {hood_id}. Exhaust flow: {hood.state.exhaust_flow_rate_m3s} m^3/s",
            details={"hood_id": hood_id}
        )
        return active

    # =========================================================================
    # 3. THERMAL RUNAWAY & PRESSURE VESSELS
    # =========================================================================
    def register_vessel(
        self,
        vessel_id: str,
        chemical_id: str,
        vessel_type: VesselType = VesselType.ERLENMEYER_FLASK_STOPPERED,
        relief_type: ReliefType = ReliefType.GROUND_GLASS_STOPPER,
        total_volume_ml: float = 500.0,
        liquid_volume_ml: float = 250.0,
        burst_pressure_kpa: float = 350.0
    ) -> ThermalVesselSimulation:
        """Registers a new reaction container in the lab simulation."""
        vessel = ThermalVesselSimulation(
            vessel_id=vessel_id,
            vessel_type=vessel_type,
            relief_type=relief_type,
            total_volume_ml=total_volume_ml,
            chemical_id=chemical_id,
            liquid_volume_ml=liquid_volume_ml,
            burst_pressure_kpa=burst_pressure_kpa
        )
        self.vessels[vessel_id] = vessel
        return vessel

    def heat_vessel(self, vessel_id: str, watts: float) -> None:
        """Applies external heating to a vessel."""
        vessel = self.vessels.get(vessel_id)
        if not vessel:
            raise ValueError(f"Vessel {vessel_id} not found.")
        vessel.set_heat_source(watts)

    def trigger_runaway_reaction(self, vessel_id: str, delta_h_kj_mol: float = 180.0) -> None:
        """Initiates an exothermic chemical runaway reaction inside the vessel."""
        vessel = self.vessels.get(vessel_id)
        if not vessel:
            raise ValueError(f"Vessel {vessel_id} not found.")
        vessel.trigger_exothermic_reaction(delta_h_kj_mol)
        self.dispatch_event(
            event_type="EXOTHERMIC_RUNAWAY_INITIATED",
            severity="CRITICAL",
            message=f"Exothermic runaway initiated in {vessel_id} ({vessel.chem.name})",
            details={"vessel_id": vessel_id, "delta_h": delta_h_kj_mol}
        )

    # =========================================================================
    # 4. NEUTRALIZATION & DRILL SIMULATION
    # =========================================================================
    def create_acid_spill(
        self,
        spill_id: str,
        acid_id: str = "hydrochloric_acid",
        volume_liters: float = 0.50,
        molarity: float = 2.0,
        location: SpillLocation = SpillLocation.WORKBENCH
    ) -> AcidSpillNeutralizationDrill:
        """Spills acid and initializes neutralization drill."""
        drill = AcidSpillNeutralizationDrill(
            acid_id=acid_id,
            volume_liters=volume_liters,
            molarity=molarity,
            location=location
        )
        self.active_spills[spill_id] = drill
        self.dispatch_event(
            event_type="CHEMICAL_SPILL_OCCURRED",
            severity="CRITICAL",
            message=f"Acid spill: {volume_liters}L of {molarity}M {drill.acid_chem.name} at {location.value}. Neutralization required!",
            details={
                "spill_id": spill_id,
                "ph": drill.state.current_ph,
                "nahco3_needed_g": drill.grams_needed,
                "spread_area_m2": drill.spill_spread_area_m2
            }
        )
        return drill

    def neutralize_spill(self, spill_id: str, bicarbonate_grams: float) -> DrillScoreReport:
        """Applies sodium bicarbonate powder to an active spill."""
        drill = self.active_spills.get(spill_id)
        if not drill:
            raise ValueError(f"Spill {spill_id} not found.")

        state = drill.apply_sodium_bicarbonate(bicarbonate_grams)
        report = drill.evaluate_drill_performance()

        if state.is_neutralized:
            self.dispatch_event(
                event_type="SPILL_NEUTRALIZATION_COMPLETE",
                severity="INFO",
                message=f"Spill {spill_id} successfully neutralized! Final pH: {state.current_ph:.2f}. Safe for cleanup.",
                details={"score": report.score_percentage, "ph": state.current_ph}
            )
        else:
            self.dispatch_event(
                event_type="NEUTRALIZATION_IN_PROGRESS",
                severity="WARNING" if state.current_ph < 4.0 else "INFO",
                message=f"Applied {bicarbonate_grams}g NaHCO3 to {spill_id}. Current pH: {state.current_ph:.2f}. CO2 evolved: {state.co2_gas_generated_liters}L",
                details={"ph": state.current_ph, "effervescing": state.is_effervescing}
            )

        return report

    def start_eyewash_shower_drill(
        self,
        drill_id: str,
        exposure_type: ExposureType = ExposureType.EYE_SPLASH,
        chemical_id: str = "hydrochloric_acid",
        distance_meters: float = 6.0
    ) -> EmergencyShowerEyewashDrill:
        """Starts an emergency eyewash/shower drill."""
        drill = EmergencyShowerEyewashDrill(
            exposure_type=exposure_type,
            chemical_id=chemical_id,
            initial_distance_meters=distance_meters
        )
        self.active_drills[drill_id] = drill
        self.dispatch_event(
            event_type="PERSONNEL_CONTAMINATION_EMERGENCY",
            severity="CRITICAL",
            message=f"Worker exposed! Type: {exposure_type.value}, Substance: {drill.chem.name}. Proceed to safety station immediately!",
            details={"drill_id": drill_id, "distance_m": distance_meters}
        )
        return drill

    # =========================================================================
    # 5. SIMULATION TICK LOOP & TELEMETRY
    # =========================================================================
    def tick(self, dt: float = 0.1) -> dict[str, Any]:
        """
        Advances the global lab simulation by dt seconds.
        Updates all vessels, fume hoods, and drills.
        Dispatches any critical events (stopper pops, explosions, alarms).
        """
        # 1. Update Fume Hoods
        for _hood_id, hood in self.fume_hoods.items():
            hood.update(dt)

        # 2. Update Vessels
        for v_id, vessel in self.vessels.items():
            prev_state = vessel.state
            new_state = vessel.update(dt)

            if new_state == VesselState.STOPPER_POPPED and prev_state != VesselState.STOPPER_POPPED:
                pop_info = vessel.last_pop_report
                self.dispatch_event(
                    event_type="STOPPER_POPPED_PRESSURE_RELIEF",
                    severity="WARNING",
                    message=(
                        f"Stopper blew out of {v_id}! Pop pressure: {pop_info.pop_pressure_kpa if pop_info else 0} kPa. "
                        f"Launch velocity: {pop_info.launch_velocity_mps if pop_info else 0} m/s, Peak height: {pop_info.peak_height_m if pop_info else 0}m"
                    ),
                    details={"vessel_id": v_id, "pop_report": pop_info.__dict__ if pop_info else {}}
                )

            elif new_state == VesselState.CATASTROPHIC_EXPLOSION and prev_state != VesselState.CATASTROPHIC_EXPLOSION:
                self.emergency_alarm_active = True
                self.evacuation_order = True
                rx = vessel.last_rupture_report
                self.dispatch_event(
                    event_type="VESSEL_CATASTROPHIC_EXPLOSION",
                    severity="CATASTROPHIC",
                    message=(
                        f"BOILING LIQUID / EXPANDING VAPOR EXPLOSION: Vessel {v_id} shattered violently! "
                        f"Energy: {rx.explosion_energy_joules if rx else 0} J, Blast radius: {rx.blast_radius_m if rx else 0} m, "
                        f"Shrapnel fragments: {rx.shrapnel_count if rx else 0}. Fire flash: {rx.fire_flash_hazard if rx else False}"
                    ),
                    details={"vessel_id": v_id, "rupture_report": rx.__dict__ if rx else {}}
                )

        return self.get_telemetry()

    def get_telemetry(self) -> dict[str, Any]:
        """Returns complete serializable snapshot of the chemical laboratory safety state."""
        hood_data = {}
        for h_id, h in self.fume_hoods.items():
            st = h.state
            hood_data[h_id] = {
                "sash_height_m": round(st.sash_height_m, 3),
                "face_velocity_mps": round(st.face_velocity_mps, 2),
                "alarm_state": st.alarm_state.value,
                "containment_efficiency": round(st.containment_efficiency, 3),
                "vapor_leakage_rate_g_s": st.vapor_leakage_rate_g_s,
                "purge_active": st.purge_active,
                "chemicals_inside": st.chemicals_inside,
                "active_warnings": st.active_warnings
            }

        vessel_data = {}
        for v_id, v in self.vessels.items():
            vessel_data[v_id] = {
                "vessel_type": v.vessel_type.value,
                "chemical": v.chem.name,
                "temperature_c": round(v.temp_c, 1),
                "pressure_kpa": round(v.pressure_kpa, 1),
                "state": v.state.value,
                "relief_type": v.relief_type.value,
                "stopper_popped": v.stopper_popped,
                "ruptured": v.ruptured,
                "runaway_detected": v.runaway_detected
            }

        spills_data = {}
        for s_id, s in self.active_spills.items():
            spills_data[s_id] = {
                "acid": s.acid_chem.name,
                "volume_liters": s.state.initial_volume_liters,
                "current_ph": s.state.current_ph,
                "bicarbonate_added_g": round(s.state.bicarbonate_added_grams, 1),
                "grams_needed": round(s.grams_needed, 1),
                "is_neutralized": s.state.is_neutralized,
                "is_effervescing": s.state.is_effervescing,
                "safe_for_cleanup": s.state.safe_for_cleanup
            }

        return {
            "laboratory_status": {
                "emergency_alarm": self.emergency_alarm_active,
                "evacuation_ordered": self.evacuation_order,
                "total_incidents": len(self.event_log)
            },
            "fume_hoods": hood_data,
            "pressure_vessels": vessel_data,
            "active_spills": spills_data
        }
