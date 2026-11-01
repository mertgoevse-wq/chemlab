"""
Pure Geometric and Kinematic Gesture Classifier.
Decoupled from camera hardware and rendering. Uses 3D skeletal distances.
"""

import math
from collections import deque

from chemlab_core.config import VisionConfig
from chemlab_core.exceptions import GestureClassificationError
from chemlab_core.models import (
    GestureEvent,
    GestureType,
    HandLandmarkFrame,
    NormalizedLandmark,
)
from chemlab_core.vision.contracts import GestureClassifier


def euclidean_distance_3d(p1: NormalizedLandmark, p2: NormalizedLandmark) -> float:
    """Compute 3D Euclidean distance between two skeletal landmarks."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = p1.z - p2.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


class GeometricGestureClassifier(GestureClassifier):
    """Classifies physical interaction gestures using anatomical landmark distances."""

    def __init__(self, config: VisionConfig | None = None) -> None:
        self._config = config or VisionConfig()
        self._history: deque[HandLandmarkFrame] = deque(maxlen=self._config.max_history_frames)

    def classify(self, frame: HandLandmarkFrame) -> GestureEvent:
        """Analyze landmark topology and classify the active gesture."""
        if len(frame.landmarks) < 21:
            raise GestureClassificationError(
                f"Expected 21 landmarks, received {len(frame.landmarks)}",
                details={"frame_index": frame.frame_index},
            )

        landmarks = frame.landmarks
        wrist = landmarks[0]

        # Landmark Indices (Mediapipe Standard):
        # 4: Thumb Tip, 8: Index Tip, 12: Middle Tip, 16: Ring Tip, 20: Pinky Tip
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Midpoint of thumb and index tips (interaction anchor)
        focus_x = (thumb_tip.x + index_tip.x) / 2.0
        focus_y = (thumb_tip.y + index_tip.y) / 2.0
        focus_z = (thumb_tip.z + index_tip.z) / 2.0

        # Distance 1: Pinch (Thumb tip to Index tip)
        pinch_dist = euclidean_distance_3d(thumb_tip, index_tip)

        # Distance 2: Grab (Average distance from 4 fingertips to palm center/wrist)
        finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
        avg_dist_to_wrist = sum(euclidean_distance_3d(tip, wrist) for tip in finger_tips) / 4.0

        # Update kinematic history
        self._history.append(frame)

        # Evaluate Gestures
        # 1. Pinch detection (fine motor grip on test tubes / pipettes)
        if pinch_dist < self._config.pinch_threshold_distance:
            strength = max(
                0.0, min(1.0, 1.0 - (pinch_dist / self._config.pinch_threshold_distance))
            )
            return GestureEvent(
                gesture=GestureType.PINCH,
                handedness=frame.handedness,
                position=(focus_x, focus_y, focus_z),
                strength=strength,
            )

        # 2. Grab detection (holding beakers / flasks with entire hand)
        if avg_dist_to_wrist < self._config.grab_threshold_distance:
            strength = max(
                0.0, min(1.0, 1.0 - (avg_dist_to_wrist / self._config.grab_threshold_distance))
            )
            return GestureEvent(
                gesture=GestureType.GRAB,
                handedness=frame.handedness,
                position=(focus_x, focus_y, focus_z),
                strength=strength,
            )

        # 3. Kinematic rotation detection if grabbing earlier
        if len(self._history) >= 5:
            past_frame = self._history[0]
            past_wrist = past_frame.landmarks[0]
            dx = wrist.x - past_wrist.x
            dy = wrist.y - past_wrist.y

            # Check for tangential sweep
            if math.hypot(dx, dy) > 0.08:
                if dx > 0.05:
                    return GestureEvent(
                        gesture=GestureType.SWIPE_RIGHT,
                        handedness=frame.handedness,
                        position=(focus_x, focus_y, focus_z),
                        strength=0.85,
                    )
                if dx < -0.05:
                    return GestureEvent(
                        gesture=GestureType.SWIPE_LEFT,
                        handedness=frame.handedness,
                        position=(focus_x, focus_y, focus_z),
                        strength=0.85,
                    )

        # 4. Point detection (only index extended, middle/ring/pinky curled)
        dist_middle_wrist = euclidean_distance_3d(middle_tip, wrist)
        dist_index_wrist = euclidean_distance_3d(index_tip, wrist)
        if dist_index_wrist > 0.18 and dist_middle_wrist < 0.11:
            return GestureEvent(
                gesture=GestureType.POINT,
                handedness=frame.handedness,
                position=(index_tip.x, index_tip.y, index_tip.z),
                strength=0.9,
            )

        # Default: Idle / open palm
        return GestureEvent(
            gesture=GestureType.IDLE,
            handedness=frame.handedness,
            position=(focus_x, focus_y, focus_z),
            strength=0.0,
        )
