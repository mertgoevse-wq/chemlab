"""
Chemical Fume Hood Aerodynamics & Sash Safety Simulation Layer
Compliant with ANSI/AIHA Z9.5 (Laboratory Ventilation) and OSHA 29 CFR 1910.1450.
Simulates face velocity, sash position alarms, volatile solvent containment,
and 3D aerodynamic streamline draft fields for animation and real-time visualization.
"""

import math
from dataclasses import dataclass, field
from enum import Enum

from .ghs import CHEMICAL_DATABASE, ChemicalProfile


class FumeHoodMode(str, Enum):
    CAV = "CAV"  # Constant Air Volume
    VAV = "VAV"  # Variable Air Volume (dynamically throttles blower)


class FumeHoodAlarmState(str, Enum):
    SAFE = "SAFE"
    WARNING_SASH_ELEVATED = "WARNING_SASH_ELEVATED"
    ALARM_SASH_TOO_HIGH_VOLATILE = "ALARM_SASH_TOO_HIGH_VOLATILE"
    ALARM_LOW_AIRFLOW = "ALARM_LOW_AIRFLOW"
    ALARM_TURBULENT_LEAKAGE = "ALARM_TURBULENT_LEAKAGE"
    EMERGENCY_PURGE = "EMERGENCY_PURGE"


@dataclass
class AirflowVector3D:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    magnitude: float
    vorticity: float = 0.0


@dataclass
class StreamlineParticle:
    id: int
    trail: list[tuple[float, float, float]]
    active: bool = True
    escaped_into_room: bool = False
    age: float = 0.0


@dataclass
class FumeHoodState:
    sash_height_m: float = 0.35  # meters (0.0 to 0.85)
    blower_running: bool = True
    purge_active: bool = False
    face_velocity_mps: float = 0.50  # m/s (normal standard: 0.40 - 0.60 m/s)
    exhaust_flow_rate_m3s: float = 0.35  # m^3/s
    alarm_state: FumeHoodAlarmState = FumeHoodAlarmState.SAFE
    active_warnings: list[str] = field(default_factory=list)
    chemicals_inside: list[str] = field(default_factory=list)
    vapor_leakage_rate_g_s: float = 0.0
    containment_efficiency: float = 1.0  # 1.0 = 100% containment, <0.95 = hazardous leak


class FumeHoodSimulation:
    """
    Physical Fume Hood Simulator modeled on standard laboratory chemical digestorium:
    Width = 1.90m, Depth = 0.95m, Working Height = 1.50m (Base = 0.90m, Total Top = 2.40m).
    Safe Sash Working Height <= 0.45m (~18 inches).
    """

    WIDTH: float = 1.90
    DEPTH: float = 0.95
    HEIGHT: float = 1.50
    BENCH_Z: float = 0.90
    MAX_SASH_HEIGHT: float = 0.85
    SAFE_SASH_LIMIT: float = 0.45  # Standard sash stop indicator
    BYPASS_AREA: float = 0.04  # m^2 built-in top aerodynamic bypass
    NOMINAL_FLOW_CAV: float = 0.38  # m^3/s
    MAX_BLOWER_FLOW: float = 0.75  # m^3/s
    PURGE_FLOW: float = 0.85  # m^3/s
    TARGET_FACE_VELOCITY_VAV: float = 0.50  # m/s (~100 fpm)

    def __init__(self, mode: FumeHoodMode = FumeHoodMode.VAV, center_x: float = -2.2, center_y: float = 3.35):
        self.mode = mode
        self.center_x = center_x
        self.center_y = center_y
        self.state = FumeHoodState()
        self.particles: list[StreamlineParticle] = []
        self._next_particle_id = 1
        self.update(dt=0.0)

    def set_sash_height(self, height_m: float) -> None:
        """Sets sash opening height clamped between 0.0 and MAX_SASH_HEIGHT."""
        self.state.sash_height_m = max(0.02, min(height_m, self.MAX_SASH_HEIGHT))

    def toggle_purge(self, enable: bool | None = None) -> bool:
        """Toggles or sets the Emergency Purge high-flow exhaust mode."""
        if enable is None:
            self.state.purge_active = not self.state.purge_active
        else:
            self.state.purge_active = enable
        return self.state.purge_active

    def add_chemical(self, chemical_id: str) -> None:
        """Places a chemical container inside the fume hood work deck."""
        if chemical_id in CHEMICAL_DATABASE and chemical_id not in self.state.chemicals_inside:
            self.state.chemicals_inside.append(chemical_id)

    def remove_chemical(self, chemical_id: str) -> None:
        """Removes a chemical container from the fume hood."""
        if chemical_id in self.state.chemicals_inside:
            self.state.chemicals_inside.remove(chemical_id)

    def has_volatile_chemicals(self) -> list[ChemicalProfile]:
        """Returns list of volatile or toxic chemicals currently in the fume hood."""
        found = []
        for cid in self.state.chemicals_inside:
            chem = CHEMICAL_DATABASE.get(cid)
            if chem and (chem.is_volatile or chem.vapor_pressure_kpa_20c > 2.0):
                found.append(chem)
        return found

    def update(self, dt: float = 0.016) -> FumeHoodState:
        """
        Advances the aerodynamic and safety simulation time step.
        Calculates face area, exhaust flow, face velocity, containment ratio,
        and triggers safety alarms.
        """
        st = self.state
        st.active_warnings.clear()

        if not st.blower_running:
            st.exhaust_flow_rate_m3s = 0.0
            st.face_velocity_mps = 0.0
            st.alarm_state = FumeHoodAlarmState.ALARM_LOW_AIRFLOW
            st.containment_efficiency = 0.0
            st.active_warnings.append("EXHAUST BLOWER OFF: Zero containment! Evacuate fume hood area.")
            return st

        # Face opening area (m^2)
        face_opening_area = (self.WIDTH * st.sash_height_m) + self.BYPASS_AREA

        # Determine exhaust volumetric flow rate Q (m^3/s)
        if st.purge_active:
            st.exhaust_flow_rate_m3s = self.PURGE_FLOW
        elif self.mode == FumeHoodMode.VAV:
            # VAV tries to maintain 0.50 m/s face velocity
            needed_flow = face_opening_area * self.TARGET_FACE_VELOCITY_VAV
            st.exhaust_flow_rate_m3s = min(self.MAX_BLOWER_FLOW, max(0.12, needed_flow))
        else:  # CAV
            st.exhaust_flow_rate_m3s = self.NOMINAL_FLOW_CAV

        # Face velocity v = Q / A (m/s)
        st.face_velocity_mps = st.exhaust_flow_rate_m3s / face_opening_area

        # Safety Evaluator
        volatiles = self.has_volatile_chemicals()
        volatile_names = [c.name for c in volatiles]

        # Check face velocity boundaries (ANSI Z9.5 standard: 0.40 - 0.60 m/s)
        if st.purge_active:
            st.alarm_state = FumeHoodAlarmState.EMERGENCY_PURGE
            st.active_warnings.append("EMERGENCY PURGE ENGAGED: Maximum ventilation active.")
            st.containment_efficiency = 1.0
            st.vapor_leakage_rate_g_s = 0.0

        elif st.sash_height_m > self.SAFE_SASH_LIMIT:
            # Sash is above 0.45m safe limit
            if volatiles:
                st.alarm_state = FumeHoodAlarmState.ALARM_SASH_TOO_HIGH_VOLATILE
                st.containment_efficiency = max(0.40, 1.0 - (st.sash_height_m - self.SAFE_SASH_LIMIT) * 1.5)
                # Leakage rate estimation (g/s)
                total_vp = sum(c.vapor_pressure_kpa_20c for c in volatiles)
                st.vapor_leakage_rate_g_s = round((1.0 - st.containment_efficiency) * (total_vp * 0.05), 3)
                st.active_warnings.append(
                    f"DANGER: Sash opened to {st.sash_height_m*100:.1f} cm (Limit: {self.SAFE_SASH_LIMIT*100:.1f} cm)! "
                    f"Volatile solvents present ({', '.join(volatile_names)}). Toxic vapor escape into room breathing zone!"
                )
            else:
                st.alarm_state = FumeHoodAlarmState.WARNING_SASH_ELEVATED
                st.containment_efficiency = 0.92
                st.vapor_leakage_rate_g_s = 0.0
                st.active_warnings.append(
                    f"WARNING: Sash height {st.sash_height_m*100:.1f} cm exceeds safe working line ({self.SAFE_SASH_LIMIT*100:.1f} cm). Lower sash to working line."
                )

        elif st.face_velocity_mps < 0.40:
            st.alarm_state = FumeHoodAlarmState.ALARM_LOW_AIRFLOW
            st.containment_efficiency = 0.65
            st.active_warnings.append(
                f"LOW FACE VELOCITY ALARM: {st.face_velocity_mps:.2f} m/s is below 0.40 m/s minimum. Hazardous fumes may reverse into room!"
            )
        elif st.face_velocity_mps > 0.75:
            st.alarm_state = FumeHoodAlarmState.ALARM_TURBULENT_LEAKAGE
            st.containment_efficiency = 0.88
            st.active_warnings.append(
                f"HIGH VELOCITY TURBULENCE: {st.face_velocity_mps:.2f} m/s generates vortex shedding behind glassware, causing potential spillover."
            )
        else:
            st.alarm_state = FumeHoodAlarmState.SAFE
            st.containment_efficiency = 0.999
            st.vapor_leakage_rate_g_s = 0.0

        return st

    def sample_velocity_field(self, x: float, y: float, z: float) -> AirflowVector3D:
        """
        Computes 3D aerodynamic vector [vx, vy, vz] at any coordinate inside or near the hood.
        Coordinates are relative to hood center (X=0, Y=0 at workdeck, Z=0 at deck).
        Air moves from room front (negative Y) into hood, across deck, and up rear baffles.
        """
        st = self.state
        v_face = st.face_velocity_mps

        # Hood interior bounds: X in [-W/2, W/2], Y in [-D/2, D/2], Z in [0, H]
        in_front = (y < -self.DEPTH / 2)
        inside = (-self.WIDTH / 2 <= x <= self.WIDTH / 2) and (-self.DEPTH / 2 <= y <= self.DEPTH / 2) and (0 <= z <= self.HEIGHT)

        if not st.blower_running:
            return AirflowVector3D(x=x, y=y, z=z, vx=0.0, vy=0.0, vz=0.0, magnitude=0.0)

        if in_front:
            # Ambient room air being pulled into the sash opening
            dist_to_opening = math.hypot(y - (-self.DEPTH / 2), z - st.sash_height_m / 2)
            vy_pull = v_face / max(1.0, (1.0 + 3.0 * dist_to_opening))
            vz_pull = (st.sash_height_m / 2 - z) * 0.3
            vx_pull = -x * 0.2
            mag = math.sqrt(vx_pull**2 + vy_pull**2 + vz_pull**2)
            return AirflowVector3D(x=x, y=y, z=z, vx=vx_pull, vy=vy_pull, vz=vz_pull, magnitude=mag)

        elif inside:
            # Air accelerates towards back wall baffles and up ductwork
            # Streamwise Y velocity
            vy = v_face * (1.0 - 0.2 * (y / (self.DEPTH / 2)))
            # Baffle suction draws air: lower baffle (Z ~ 0.1), middle (Z ~ 0.7), top (Z ~ 1.3)
            # Upward duct pull increases near top rear
            vz = 0.1 + (z / self.HEIGHT) * (v_face * 1.2) if y > 0 else (0.05 * v_face)
            # Wall boundary effect on X
            vx = -0.15 * (x / (self.WIDTH / 2)) * v_face

            # If sash too high, induce turbulent vortex near front lip
            vorticity = 0.0
            if st.sash_height_m > self.SAFE_SASH_LIMIT and y < -self.DEPTH / 4:
                vorticity = (st.sash_height_m - self.SAFE_SASH_LIMIT) * 2.5
                vy -= vorticity * 0.4  # reverse draft leak

            mag = math.sqrt(vx**2 + vy**2 + vz**2)
            return AirflowVector3D(x=x, y=y, z=z, vx=vx, vy=vy, vz=vz, magnitude=mag, vorticity=vorticity)

        else:
            return AirflowVector3D(x=x, y=y, z=z, vx=0.0, vy=0.0, vz=0.0, magnitude=0.0)

    def generate_draft_streamlines(self, num_streamlines: int = 24, steps: int = 50, dt: float = 0.04) -> list[list[tuple[float, float, float]]]:
        """
        Generates 3D streamline coordinate paths for animation keyframing in Blender or particle systems in Godot.
        Returns a list of streamline polylines (list of (x,y,z) points in world space).
        """
        streamlines = []
        st = self.state

        # Spawn seed points at face plane
        num_x = max(3, int(math.sqrt(num_streamlines * 2)))
        num_z = max(2, num_streamlines // num_x)

        x_coords = [(-self.WIDTH / 2 + 0.15) + i * ((self.WIDTH - 0.3) / max(1, num_x - 1)) for i in range(num_x)]
        z_coords = [0.05 + j * ((st.sash_height_m - 0.08) / max(1, num_z - 1)) for j in range(num_z)]

        for sx in x_coords:
            for sz in z_coords:
                pt_x = sx
                pt_y = -self.DEPTH / 2 - 0.2  # start slightly in front of sash
                pt_z = sz

                trail = [(round(pt_x + self.center_x, 3), round(pt_y + self.center_y, 3), round(pt_z + self.BENCH_Z, 3))]

                for _ in range(steps):
                    vec = self.sample_velocity_field(pt_x, pt_y, pt_z)
                    if vec.magnitude < 0.01:
                        break
                    pt_x += vec.vx * dt
                    pt_y += vec.vy * dt
                    pt_z += vec.vz * dt

                    trail.append((
                        round(pt_x + self.center_x, 3),
                        round(pt_y + self.center_y, 3),
                        round(pt_z + self.BENCH_Z, 3)
                    ))

                    # Terminate if entered exhaust duct or escaped
                    if pt_z > self.HEIGHT or pt_y > self.DEPTH / 2:
                        break
                    if pt_y < -self.DEPTH / 2 - 0.6:  # leaked far into lab
                        break

                if len(trail) > 2:
                    streamlines.append(trail)

        return streamlines
