"""
ChemLab MediaPipe Holistic & Full-Body Locomotion Engine.
Tracks 33 anatomical body pose landmarks alongside arms, hands, and legs.
Translates alternating knee lifts into virtual walking locomotion,
lateral weight shifts into laboratory workstation switching,
and high arm reaches into reagent shelf selection.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chemlab.compat import StrEnum
from chemlab.cv.one_euro_filter import OneEuroFilter


class LocomotionState(StrEnum):
    """Current locomotion movement classification."""

    STATIONARY = "stationary"
    STEPPING_FORWARD = "stepping_forward"
    TURNING_LEFT = "turning_left"
    TURNING_RIGHT = "turning_right"


class LabWorkstation(StrEnum):
    """Zoned workstations in the ChemLab virtual laboratory room."""

    FUME_HOOD = "fume_hood"  # Left zone (X < 0.35)
    MAIN_BENCH = "main_bench"  # Center zone (0.35 <= X <= 0.65)
    ANALYTICAL_BENCH = "analytical_bench"  # Right zone (X > 0.65)
    SYNTHESIS_RIG = "synthesis_rig"  # Rear zone


@dataclass(frozen=True)
class PoseLandmarkPoint:
    """Single 3D coordinate point in normalized camera coordinates [0..1]."""

    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


@dataclass
class BodyPoseFrame:
    """Frame containing all 33 standard MediaPipe Pose skeletal landmarks."""

    timestamp_s: float
    landmarks: list[PoseLandmarkPoint]


@dataclass
class HolisticTrackingResult:
    """Full-body tracking output with locomotion, workstation, and arm gestures."""

    timestamp_s: float
    locomotion: LocomotionState
    step_cadence_hz: float
    current_workstation: LabWorkstation
    is_reaching_high_shelf: bool
    active_reaching_arm: str | None = None
    hip_center_x: float = 0.5
    filtered_landmarks: list[PoseLandmarkPoint] = field(default_factory=list)


class MediaPipeHolisticEngine:
    """
    Real-time analyzer for full-body tracking, arm kinematics, and leg stepping.
    Equipped with 1-Euro adaptive low-pass filtering on all skeletal nodes.
    """

    def __init__(self) -> None:
        self._filters_x: dict[int, OneEuroFilter] = {}
        self._filters_y: dict[int, OneEuroFilter] = {}
        self._last_knee_y: tuple[float, float] = (0.75, 0.75)
        self._step_timestamps: list[float] = []
        self._last_t: float = 0.0

    def analyze(self, frame: BodyPoseFrame) -> HolisticTrackingResult:
        """Processes one body pose frame and classifies locomotion and arm actions."""
        t = frame.timestamp_s
        lms = frame.landmarks

        if len(lms) < 33:
            return HolisticTrackingResult(
                timestamp_s=t,
                locomotion=LocomotionState.STATIONARY,
                step_cadence_hz=0.0,
                current_workstation=LabWorkstation.MAIN_BENCH,
                is_reaching_high_shelf=False,
            )

        # 1) 1-Euro filtering across core landmarks
        filtered_lms: list[PoseLandmarkPoint] = []
        for i, pt in enumerate(lms):
            if i not in self._filters_x:
                self._filters_x[i] = OneEuroFilter(t0=t, x0=pt.x, min_cutoff=1.5, beta=0.005)
                self._filters_y[i] = OneEuroFilter(t0=t, x0=pt.y, min_cutoff=1.5, beta=0.005)
            fx = self._filters_x[i](t, pt.x)
            fy = self._filters_y[i](t, pt.y)
            filtered_lms.append(PoseLandmarkPoint(x=fx, y=fy, z=pt.z, visibility=pt.visibility))

        # Core landmarks:
        # 11, 12: shoulders
        # 15, 16: wrists
        # 23, 24: hips
        # 25, 26: knees
        sh_l, sh_r = filtered_lms[11], filtered_lms[12]
        wr_l, wr_r = filtered_lms[15], filtered_lms[16]
        hip_l, hip_r = filtered_lms[23], filtered_lms[24]
        knee_l, knee_r = filtered_lms[25], filtered_lms[26]

        hip_mid_x = (hip_l.x + hip_r.x) / 2.0

        # 2) Workstation selection by lateral weight shift
        if hip_mid_x < 0.35:
            current_ws = LabWorkstation.FUME_HOOD
        elif hip_mid_x > 0.65:
            current_ws = LabWorkstation.ANALYTICAL_BENCH
        else:
            current_ws = LabWorkstation.MAIN_BENCH

        # 3) Stepping in place detection (knee lift velocity & cadence)
        delta_lk = self._last_knee_y[0] - knee_l.y
        delta_rk = self._last_knee_y[1] - knee_r.y
        self._last_knee_y = (knee_l.y, knee_r.y)

        # High knee elevation (y decreases when lifting upward)
        if delta_lk > 0.04 or delta_rk > 0.04:
            self._step_timestamps.append(t)

        # Clean old steps (> 2.0 seconds ago)
        self._step_timestamps = [ts for ts in self._step_timestamps if (t - ts) <= 2.0]
        step_count = len(self._step_timestamps)
        cadence_hz = step_count / 2.0 if step_count > 0 else 0.0

        loco = LocomotionState.STEPPING_FORWARD if cadence_hz >= 0.5 else LocomotionState.STATIONARY

        # 4) High shelf arm reach detection (wrist above shoulder height)
        # Note: In normalized camera coords, 0 is top, 1 is bottom.
        # Wrist is above shoulder when wrist.y < shoulder.y - 0.08
        reach_high = False
        active_arm = None
        if wr_l.y < (sh_l.y - 0.08):
            reach_high = True
            active_arm = "left"
        elif wr_r.y < (sh_r.y - 0.08):
            reach_high = True
            active_arm = "right"

        return HolisticTrackingResult(
            timestamp_s=t,
            locomotion=loco,
            step_cadence_hz=cadence_hz,
            current_workstation=current_ws,
            is_reaching_high_shelf=reach_high,
            active_reaching_arm=active_arm,
            hip_center_x=hip_mid_x,
            filtered_landmarks=filtered_lms,
        )
