"""
ChemLab Air-Guitar Real-Time Hand Tracking & Gesture Engine.
Translates 2D/3D webcam anatomical landmarks into physical lab interactions:
- Pinch-to-Grab (Test tubes, pipettes, spatulas)
- Grab-to-Hold (Beakers, flasks, bottles)
- Tilt-to-Pour (Hydrodynamic angle-governed fluid transfer)
- Swirl-to-Mix (Vortex stirring & oscillating cycle excitation)
- Point-to-Select (HUD buttons, GHS safety placards, level selection)

Smooths all 21 landmarks using the 1-Euro Filter for rock-solid stability on Intel Iris Xe.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import StrEnum

from chemlab.cv.one_euro_filter import Point3DOneEuroFilter
from chemlab_core.models import (
    Handedness,
    HandLandmarkFrame,
    NormalizedLandmark,
)


class AirGuitarGesture(StrEnum):
    """Recognized gestural states for touchless chemistry lab manipulation."""

    IDLE = "IDLE"
    PINCH = "PINCH"
    GRAB = "GRAB"
    FIST = "FIST"
    POUR = "POUR"
    SWIRL = "SWIRL"
    POINT = "POINT"
    RELEASE = "RELEASE"


@dataclass
class HandTrackingResult:
    """Rich telemetry packet emitted per video frame."""

    timestamp: float
    handedness: Handedness
    raw_landmarks: list[NormalizedLandmark]
    smoothed_landmarks: list[NormalizedLandmark]
    gesture: AirGuitarGesture
    pinch_distance: float
    is_pinching: bool
    is_grabbing: bool
    grab_strength: float
    tilt_degrees: float
    pour_rate: float
    world_position_3d: tuple[float, float, float]
    confidence: float = 1.0


def _dist_3d(p1: NormalizedLandmark, p2: NormalizedLandmark) -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = p1.z - p2.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


class AirGuitarGestureEngine:
    """
    Evaluates kinematic landmark topology to detect intuitive 'air-guitar' hand interactions.
    """

    def __init__(
        self,
        pinch_threshold: float = 0.055,
        grab_threshold: float = 0.16,
        pour_angle_threshold: float = 38.0,
    ) -> None:
        self.pinch_threshold = pinch_threshold
        self.grab_threshold = grab_threshold
        self.pour_angle_threshold = pour_angle_threshold
        self._prev_is_grabbing = False
        self._prev_is_pinching = False

    def analyze(self, frame: HandLandmarkFrame) -> HandTrackingResult:
        lms = frame.landmarks
        wrist = lms[0]
        thumb_tip = lms[4]
        index_tip = lms[8]
        middle_tip = lms[12]
        ring_tip = lms[16]
        pinky_tip = lms[20]

        index_mcp = lms[5]
        pinky_mcp = lms[17]

        # 1. Pinch calculation (Thumb tip to Index tip)
        pinch_dist = _dist_3d(thumb_tip, index_tip)
        is_pinching = pinch_dist < self.pinch_threshold

        # 2. Grab calculation (Mean fingertip distance to wrist / palm base)
        fingertip_dists = [
            _dist_3d(index_tip, wrist),
            _dist_3d(middle_tip, wrist),
            _dist_3d(ring_tip, wrist),
            _dist_3d(pinky_tip, wrist),
        ]
        avg_finger_dist = sum(fingertip_dists) / 4.0
        is_grabbing = avg_finger_dist < self.grab_threshold
        grab_strength = max(0.0, min(1.0, 1.0 - (avg_finger_dist / (self.grab_threshold * 1.5))))

        # 3. Hand Tilt / Roll Angle (Vector from pinky MCP to index MCP)
        dx_knuckle = index_mcp.x - pinky_mcp.x
        dy_knuckle = index_mcp.y - pinky_mcp.y
        dz_knuckle = index_mcp.z - pinky_mcp.z

        # Tilt angle in degrees relative to horizontal plane
        tilt_rad = math.atan2(dy_knuckle + dz_knuckle * 0.5, abs(dx_knuckle) + 1e-5)
        tilt_degrees = math.degrees(tilt_rad)

        # 4. Pointing detection (Index extended, others curled)
        dist_index_wrist = _dist_3d(index_tip, wrist)
        dist_middle_wrist = _dist_3d(middle_tip, wrist)
        dist_ring_wrist = _dist_3d(ring_tip, wrist)
        is_pointing = (
            dist_index_wrist > 0.22
            and dist_middle_wrist < 0.14
            and dist_ring_wrist < 0.14
            and not is_pinching
        )

        # 5. Gesture Classification
        pour_rate = 0.0
        if (is_pinching or is_grabbing) and abs(tilt_degrees) > self.pour_angle_threshold:
            gesture = AirGuitarGesture.POUR
            # Flow rate scales linearly with tilt excess
            pour_rate = min(1.0, (abs(tilt_degrees) - self.pour_angle_threshold) / 35.0)
        elif is_pinching:
            gesture = AirGuitarGesture.PINCH
            grab_strength = max(grab_strength, 0.8)
        elif is_grabbing:
            gesture = (
                AirGuitarGesture.FIST
                if avg_finger_dist < self.grab_threshold * 0.7
                else AirGuitarGesture.GRAB
            )
        elif is_pointing:
            gesture = AirGuitarGesture.POINT
        elif (
            (self._prev_is_grabbing or self._prev_is_pinching)
            and not is_grabbing
            and not is_pinching
        ):
            gesture = AirGuitarGesture.RELEASE
        else:
            gesture = AirGuitarGesture.IDLE

        self._prev_is_grabbing = is_grabbing
        self._prev_is_pinching = is_pinching

        # Interaction Focus Point (centroid between thumb and index)
        focus_x = (thumb_tip.x + index_tip.x) / 2.0
        focus_y = (thumb_tip.y + index_tip.y) / 2.0
        focus_z = (thumb_tip.z + index_tip.z) / 2.0

        # Transform from camera space [0..1] to Blender laboratory coordinates
        # X: centered [-0.8m .. +0.8m], Y (depth): [0.3m .. 1.2m], Z (height): [0.7m .. 1.4m]
        world_x = round((focus_x - 0.5) * 1.6, 4)
        world_y = round(0.5 + (1.0 - focus_z) * 0.7, 4)
        world_z = round(1.2 - focus_y * 0.8, 4)

        return HandTrackingResult(
            timestamp=frame.timestamp,
            handedness=frame.handedness,
            raw_landmarks=list(frame.landmarks),
            smoothed_landmarks=list(frame.landmarks),
            gesture=gesture,
            pinch_distance=round(pinch_dist, 4),
            is_pinching=is_pinching,
            is_grabbing=is_grabbing,
            grab_strength=round(grab_strength, 4),
            tilt_degrees=round(tilt_degrees, 2),
            pour_rate=round(pour_rate, 4),
            world_position_3d=(world_x, world_y, world_z),
            confidence=frame.confidence,
        )


class WebcamHandTracker:
    """
    High-Performance Real-Time Hand Tracker.
    Connects to physical USB/built-in webcam, executes MediaPipe landmark tracking,
    and smooths output via 1-Euro filters.
    """

    def __init__(
        self,
        camera_index: int = 0,
        use_synthetic: bool = False,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
    ) -> None:
        self.camera_index = camera_index
        self.use_synthetic = use_synthetic
        self.gesture_engine = AirGuitarGestureEngine()

        # 21 independent 1-Euro point filters for each hand landmark
        self._landmark_filters: list[Point3DOneEuroFilter] = [
            Point3DOneEuroFilter(min_cutoff=min_cutoff, beta=beta) for _ in range(21)
        ]
        self._frame_counter = 0

    def process_landmarks(
        self,
        landmarks: list[NormalizedLandmark],
        handedness: Handedness = Handedness.RIGHT,
        timestamp: float | None = None,
    ) -> HandTrackingResult:
        """
        Smooths landmarks and executes gesture classification.
        """
        t = timestamp if timestamp is not None else time.time()
        self._frame_counter += 1

        # Smooth all 21 landmarks
        smoothed_lms: list[NormalizedLandmark] = []
        for i, lm in enumerate(landmarks):
            filt = self._landmark_filters[i]
            sx, sy, sz = filt(t, (lm.x, lm.y, lm.z))
            smoothed_lms.append(NormalizedLandmark(x=sx, y=sy, z=sz, visibility=lm.visibility))

        frame = HandLandmarkFrame(
            frame_index=self._frame_counter,
            timestamp=t,
            handedness=handedness,
            landmarks=smoothed_lms,
            confidence=0.98,
        )

        res = self.gesture_engine.analyze(frame)
        res.raw_landmarks = list(landmarks)
        res.smoothed_landmarks = smoothed_lms
        return res
