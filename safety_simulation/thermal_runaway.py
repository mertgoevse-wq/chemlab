"""
Thermal Runaway and Pressure Buildup Simulation Layer
Models thermodynamic heating, vapor-liquid equilibrium (Antoine equation),
Arrhenius reaction kinetics, pressure accumulation in closed vessels,
ground-glass stopper pop projectile mechanics, relief valve tripping,
and catastrophic BLEVE / glass shrapnel fragmentation events.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
from .ghs import ChemicalProfile, CHEMICAL_DATABASE, GHSClass


class VesselType(str, Enum):
    ERLENMEYER_FLASK_STOPPERED = "ERLENMEYER_FLASK_STOPPERED"
    SCREW_CAP_BOROSILICATE_VIAL = "SCREW_CAP_BOROSILICATE_VIAL"
    ROUND_BOTTOM_FLASK_STOPPERED = "ROUND_BOTTOM_FLASK_STOPPERED"
    AUTOCLAVE_PRESSURE_REACTOR = "AUTOCLAVE_PRESSURE_REACTOR"
    SEALED_TEST_TUBE = "SEALED_TEST_TUBE"


class ReliefType(str, Enum):
    GROUND_GLASS_STOPPER = "GROUND_GLASS_STOPPER"
    SPRING_RELIEF_VALVE = "SPRING_RELIEF_VALVE"
    SEALED_NO_RELIEF = "SEALED_NO_RELIEF"


class VesselState(str, Enum):
    NORMAL = "NORMAL"
    HEATING = "HEATING"
    OVERPRESSURE_WARNING = "OVERPRESSURE_WARNING"
    THERMAL_RUNAWAY = "THERMAL_RUNAWAY"
    STOPPER_POPPED = "STOPPER_POPPED"
    VALVE_VENTING = "VALVE_VENTING"
    CATASTROPHIC_EXPLOSION = "CATASTROPHIC_EXPLOSION"


@dataclass
class ShrapnelFragment:
    id: int
    velocity_mps: float
    trajectory_angle_deg: float
    travel_distance_m: float
    mass_grams: float


@dataclass
class RuptureReport:
    rupture_occurred: bool = False
    explosion_energy_joules: float = 0.0
    blast_radius_m: float = 0.0
    shrapnel_count: int = 0
    fragments: List[ShrapnelFragment] = field(default_factory=list)
    fire_flash_hazard: bool = False


@dataclass
class StopperPopReport:
    popped: bool = False
    pop_pressure_kpa: float = 0.0
    launch_velocity_mps: float = 0.0
    peak_height_m: float = 0.0
    trajectory: List[Tuple[float, float, float]] = field(default_factory=list)
    vapor_jet_volume_liters: float = 0.0


class ThermalVesselSimulation:
    """
    Physical simulation of a closed laboratory container undergoing external heating
    or self-accelerating exothermic reaction.
    """

    ATMOSPHERIC_PRESSURE_KPA: float = 101.325
    GAS_CONSTANT_R: float = 8.31446  # J/(mol*K)

    def __init__(
        self,
        vessel_id: str,
        vessel_type: VesselType = VesselType.ERLENMEYER_FLASK_STOPPERED,
        relief_type: ReliefType = ReliefType.GROUND_GLASS_STOPPER,
        total_volume_ml: float = 500.0,
        chemical_id: str = "acetone",
        liquid_volume_ml: float = 250.0,
        initial_temp_c: float = 20.0,
        burst_pressure_kpa: float = 350.0,  # ~3.5 bar for standard glassware
        stopper_pop_pressure_kpa: float = 145.0,  # ~1.45 bar (45 kPa gauge)
        valve_relief_pressure_kpa: float = 280.0,  # ~2.8 bar
        stopper_mass_grams: float = 35.0,
        joint_diameter_mm: float = 29.0  # NS 29/32 ground glass joint
    ):
        self.vessel_id = vessel_id
        self.vessel_type = vessel_type
        self.relief_type = relief_type
        self.total_volume_ml = total_volume_ml
        self.chemical_id = chemical_id
        self.liquid_volume_ml = liquid_volume_ml
        self.temp_c = initial_temp_c
        self.prev_temp_c = initial_temp_c
        self.burst_pressure_kpa = burst_pressure_kpa
        self.stopper_pop_pressure_kpa = stopper_pop_pressure_kpa
        self.valve_relief_pressure_kpa = valve_relief_pressure_kpa
        self.stopper_mass_grams = stopper_mass_grams
        self.joint_diameter_mm = joint_diameter_mm

        # Physical constants for chemical
        self.chem: ChemicalProfile = CHEMICAL_DATABASE.get(chemical_id, CHEMICAL_DATABASE["acetone"])
        self.liquid_mass_g = self.liquid_volume_ml * self.chem.density
        # Headspace volume in m^3
        self.headspace_volume_m3 = max(1e-6, (self.total_volume_ml - self.liquid_volume_ml) * 1e-6)

        # Initial moles of air sealed inside headspace at 20 C, 1 atm
        t_kelvin_init = initial_temp_c + 273.15
        p_init_pa = self.ATMOSPHERIC_PRESSURE_KPA * 1000.0
        self.moles_air = (p_init_pa * self.headspace_volume_m3) / (self.GAS_CONSTANT_R * t_kelvin_init)

        # Thermal and kinetic parameters
        self.external_heat_watts: float = 0.0  # Bunsen burner or heating mantle
        self.exothermic_delta_h_kj_mol: float = 0.0  # Heat of reaction (if decomposing/reacting)
        self.arrhenius_ea_j_mol: float = 85000.0  # Activation energy
        self.arrhenius_k0: float = 1e11  # Pre-exponential factor
        self.specific_heat_j_g_k: float = 2.16  # Approx specific heat capacity

        # Current state
        self.pressure_kpa: float = self.ATMOSPHERIC_PRESSURE_KPA
        self.state: VesselState = VesselState.NORMAL
        self.valve_open: bool = False
        self.stopper_popped: bool = False
        self.ruptured: bool = False
        self.runaway_detected: bool = False

        # Logs & Events
        self.last_pop_report: Optional[StopperPopReport] = None
        self.last_rupture_report: Optional[RuptureReport] = None

    def set_heat_source(self, watts: float) -> None:
        """Applies external heating (e.g. Bunsen burner 300W, heating mantle 150W)."""
        self.external_heat_watts = max(0.0, watts)

    def trigger_exothermic_reaction(self, delta_h_kj_mol: float = 150.0) -> None:
        """Injects an exothermic decomposition or runaway reaction trigger."""
        self.exothermic_delta_h_kj_mol = delta_h_kj_mol

    def update(self, dt: float = 0.1) -> VesselState:
        """
        Advances the thermodynamic simulation by dt seconds.
        Integrates heat balance, calculates vapor pressure via Antoine equation,
        gas pressure via Ideal Gas Law, evaluates runaway criteria, and checks
        relief / rupture thresholds.
        """
        if self.ruptured:
            return VesselState.CATASTROPHIC_EXPLOSION

        temp_k = self.temp_c + 273.15

        # 1. Reaction Heat Generation (Arrhenius equation)
        q_reaction_watts = 0.0
        if self.exothermic_delta_h_kj_mol > 0:
            k_rate = self.arrhenius_k0 * math.exp(-self.arrhenius_ea_j_mol / (self.GAS_CONSTANT_R * temp_k))
            moles_reactant = self.liquid_mass_g / self.chem.molar_mass
            # Heat generation = rate * moles * deltaH
            q_reaction_watts = min(5000.0, k_rate * moles_reactant * (self.exothermic_delta_h_kj_mol * 1000.0))

        # 2. Heat Loss to Ambient Air (Natural Convection: Q_loss = U * A * (T - T_amb))
        ambient_temp_c = 20.0
        surface_area_m2 = 0.04  # approx flask surface
        overall_u = 15.0  # W/(m^2*K)
        q_loss_watts = max(0.0, overall_u * surface_area_m2 * (self.temp_c - ambient_temp_c))

        # 3. Net Heat Balance -> dT/dt
        net_q_watts = self.external_heat_watts + q_reaction_watts - q_loss_watts
        total_heat_capacity = max(10.0, self.liquid_mass_g * self.specific_heat_j_g_k)
        dt_rate = net_q_watts / total_heat_capacity  # K/s or C/s

        self.prev_temp_c = self.temp_c
        self.temp_c += dt_rate * dt
        temp_k = self.temp_c + 273.15

        # Detect Thermal Runaway (heating rate > 2.0 C/s and accelerating)
        if dt_rate > 2.0:
            self.runaway_detected = True
            self.state = VesselState.THERMAL_RUNAWAY
        elif self.external_heat_watts > 0:
            self.state = VesselState.HEATING

        # 4. Pressure Calculation
        if self.stopper_popped:
            # Venting to atmosphere
            self.pressure_kpa = self.ATMOSPHERIC_PRESSURE_KPA
            return VesselState.STOPPER_POPPED

        # Antoine Vapor Pressure (kPa)
        p_vapor_kpa = self.chem.calculate_vapor_pressure_kpa(self.temp_c)

        # Ideal Gas Law for Air Headspace (P = nRT / V)
        p_air_pa = (self.moles_air * self.GAS_CONSTANT_R * temp_k) / self.headspace_volume_m3
        p_air_kpa = p_air_pa / 1000.0

        # Total Internal Pressure
        self.pressure_kpa = p_vapor_kpa + p_air_kpa

        # 5. Relief Valve Handling
        if self.relief_type == ReliefType.SPRING_RELIEF_VALVE:
            if self.pressure_kpa >= self.valve_relief_pressure_kpa:
                self.valve_open = True
                self.state = VesselState.VALVE_VENTING
                # Relieve excess gas flow
                excess_p = self.pressure_kpa - self.valve_relief_pressure_kpa
                self.pressure_kpa = max(self.valve_relief_pressure_kpa * 0.95, self.pressure_kpa - excess_p * 0.7)
                return self.state
            elif self.valve_open and self.pressure_kpa < self.valve_relief_pressure_kpa * 0.85:
                self.valve_open = False

        # 6. Stopper Pop Handling
        if self.relief_type == ReliefType.GROUND_GLASS_STOPPER:
            if self.pressure_kpa >= self.stopper_pop_pressure_kpa and not self.stopper_popped:
                return self._trigger_stopper_pop()

        # 7. Catastrophic Rupture / Explosion Check
        if self.pressure_kpa >= self.burst_pressure_kpa:
            return self._trigger_catastrophic_rupture()

        # State assessment
        if self.pressure_kpa > 130.0:
            self.state = VesselState.OVERPRESSURE_WARNING
        elif self.runaway_detected:
            self.state = VesselState.THERMAL_RUNAWAY
        elif self.external_heat_watts > 0:
            self.state = VesselState.HEATING
        else:
            self.state = VesselState.NORMAL

        return self.state

    def _trigger_stopper_pop(self) -> VesselState:
        """Simulates ground-glass stopper blowing out under excessive pressure."""
        self.stopper_popped = True
        self.state = VesselState.STOPPER_POPPED

        gauge_pressure_pa = (self.pressure_kpa - self.ATMOSPHERIC_PRESSURE_KPA) * 1000.0
        joint_radius_m = (self.joint_diameter_mm / 2.0) / 1000.0
        joint_area_m2 = math.pi * (joint_radius_m ** 2)

        # Work done on stopper by expanding gas: W = delta_P * Area * stroke_length (approx 0.03m)
        stroke_length_m = 0.03
        work_done_j = gauge_pressure_pa * joint_area_m2 * stroke_length_m

        # Kinetic energy of stopper: 0.5 * m * v^2 = work_done
        stopper_mass_kg = self.stopper_mass_grams / 1000.0
        v_launch = math.sqrt(max(0.1, (2.0 * work_done_j) / stopper_mass_kg))

        # Peak height: h = v^2 / (2 * g)
        peak_h = (v_launch ** 2) / (2.0 * 9.81)

        # Headspace vapor jet volume at atmospheric expansion (P1*V1 = P2*V2)
        v_jet_liters = (self.pressure_kpa / self.ATMOSPHERIC_PRESSURE_KPA) * (self.headspace_volume_m3 * 1000.0)

        # 3D trajectory calculation (launched vertically with slight random tilt)
        trajectory = []
        t_flight = 2.0 * (v_launch / 9.81)
        steps = 15
        for step in range(steps + 1):
            t = (step / steps) * t_flight
            z_pos = v_launch * t - 0.5 * 9.81 * (t ** 2)
            y_pos = 0.08 * t  # minor forward arc
            trajectory.append((0.0, round(y_pos, 3), round(max(0.0, z_pos), 3)))

        self.last_pop_report = StopperPopReport(
            popped=True,
            pop_pressure_kpa=round(self.pressure_kpa, 2),
            launch_velocity_mps=round(v_launch, 2),
            peak_height_m=round(peak_h, 2),
            trajectory=trajectory,
            vapor_jet_volume_liters=round(v_jet_liters, 2)
        )

        # Pressure is relieved instantly to atmospheric
        self.pressure_kpa = self.ATMOSPHERIC_PRESSURE_KPA
        return self.state

    def _trigger_catastrophic_rupture(self) -> VesselState:
        """Simulates catastrophic vessel failure / explosion and glass fragmentation."""
        self.ruptured = True
        self.state = VesselState.CATASTROPHIC_EXPLOSION

        gauge_pressure_pa = (self.pressure_kpa - self.ATMOSPHERIC_PRESSURE_KPA) * 1000.0
        gamma = 1.4  # diatomic gas ratio of specific heats

        # Brode's explosion energy equation: E = (P - P_0) * V / (gamma - 1)
        explosion_energy_j = (gauge_pressure_pa * self.headspace_volume_m3) / (gamma - 1.0)

        # Baker-Strehlow-Tang blast radius approximation
        blast_radius_m = 0.28 * (max(1.0, explosion_energy_j) ** 0.333)

        # Glass fragmentation dynamics
        total_glass_mass_g = 180.0  # standard flask tare
        num_fragments = 24
        frag_mass_g = total_glass_mass_g / num_fragments
        fragments: List[ShrapnelFragment] = []

        # Approx 20% of energy converts into fragment kinetic energy
        frag_ke_total = 0.20 * explosion_energy_j
        ke_per_frag = frag_ke_total / num_fragments
        frag_vel = math.sqrt(max(1.0, (2.0 * ke_per_frag) / (frag_mass_g / 1000.0)))

        for i in range(num_fragments):
            angle = (360.0 / num_fragments) * i
            dist = blast_radius_m * (0.8 + 0.4 * math.sin(i))
            fragments.append(ShrapnelFragment(
                id=i + 1,
                velocity_mps=round(frag_vel, 1),
                trajectory_angle_deg=round(angle, 1),
                travel_distance_m=round(dist, 2),
                mass_grams=round(frag_mass_g, 1)
            ))

        # Flammability flash risk
        fire_flash = (GHSClass.FLAMMABLE in self.chem.hazard_classes) and (
            self.chem.flash_point_c is not None and self.temp_c >= self.chem.flash_point_c
        )

        self.last_rupture_report = RuptureReport(
            rupture_occurred=True,
            explosion_energy_joules=round(explosion_energy_j, 2),
            blast_radius_m=round(blast_radius_m, 2),
            shrapnel_count=num_fragments,
            fragments=fragments,
            fire_flash_hazard=fire_flash
        )

        self.pressure_kpa = self.ATMOSPHERIC_PRESSURE_KPA
        return self.state
