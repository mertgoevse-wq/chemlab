"""
Deterministic Synthetic Hand Landmark Generator.
Enables full automated CI/CD testing without physical webcam hardware.
Generates 21 Mediapipe-compliant 3D skeletal landmarks.
"""

import math
from typing import Final

from chemlab_core.config import VisionConfig
from chemlab_core.models import (
    Handedness,
    HandLandmarkFrame,
    NormalizedLandmark,
)
from chemlab_core.vision.contracts import LandmarkProvider

TOTAL_LANDMARKS: Final[int] = 21


class SyntheticLandmarkGenerator(LandmarkProvider):
    """Produces synthetic, mathematically coherent hand landmark frames for headless CI."""

    def __init__(
        self,
        config: VisionConfig | None = None,
        handedness: Handedness = Handedness.RIGHT,
    ) -> None:
        self._config = config or VisionConfig()
        self._handedness = handedness
        self._frame_index = 0
        self._time_elapsed = 0.0

    def reset(self) -> None:
        """Reset sequence counter to frame zero."""
        self._frame_index = 0
        self._time_elapsed = 0.0

    def generate_frame(
        self,
        pinch_factor: float = 0.0,
        grab_factor: float = 0.0,
        wrist_pos: tuple[float, float, float] = (0.5, 0.7, 0.0),
    ) -> HandLandmarkFrame:
        """Generate a single landmark frame with parameterized gesture parameters.

        Args:
            pinch_factor: 0.0 (open) to 1.0 (tips of thumb and index touching).
            grab_factor: 0.0 (open palm) to 1.0 (tight fist / grab).
            wrist_pos: (x, y, z) baseline wrist anchor.

        Returns:
            HandLandmarkFrame with 21 normalized 3D landmarks.
        """
        wx, wy, wz = wrist_pos
        landmarks: list[NormalizedLandmark] = []

        # 0: Wrist
        landmarks.append(NormalizedLandmark(x=wx, y=wy, z=wz, visibility=1.0))

        # Base offsets for finger rays relative to wrist
        finger_bases = [
            (-0.06, -0.04),  # Thumb CMC (1)
            (-0.03, -0.12),  # Index MCP (5)
            (0.00, -0.13),  # Middle MCP (9)
            (0.03, -0.12),  # Ring MCP (13)
            (0.06, -0.10),  # Pinky MCP (17)
        ]

        # 1-4: Thumb
        tx, ty = wx + finger_bases[0][0], wy + finger_bases[0][1]
        landmarks.append(NormalizedLandmark(x=tx, y=ty, z=wz - 0.01))  # 1: CMC
        landmarks.append(NormalizedLandmark(x=tx - 0.02, y=ty - 0.04, z=wz - 0.02))  # 2: MCP
        landmarks.append(NormalizedLandmark(x=tx - 0.03, y=ty - 0.08, z=wz - 0.03))  # 3: IP

        # If pinch is active, thumb tip moves toward index tip position
        target_thumb_tip_x = (wx - 0.03) * pinch_factor + (tx - 0.04) * (1.0 - pinch_factor)
        target_thumb_tip_y = (wy - 0.20) * pinch_factor + (ty - 0.12) * (1.0 - pinch_factor)
        landmarks.append(
            NormalizedLandmark(x=target_thumb_tip_x, y=target_thumb_tip_y, z=wz - 0.03)
        )  # 4: Tip

        # 5-20: Four Fingers (Index, Middle, Ring, Pinky)
        for i, (bx_off, by_off) in enumerate(finger_bases[1:], start=1):
            mcp_x = wx + bx_off
            mcp_y = wy + by_off
            landmarks.append(NormalizedLandmark(x=mcp_x, y=mcp_y, z=wz))  # MCP

            # Curl factor moves PIP, DIP, Tip inward and back toward wrist in a fist
            curl = grab_factor if i > 1 else max(grab_factor, pinch_factor * 0.7)

            if grab_factor > 0.5:
                # Fully curled fist: fingertips curl tightly into palm center/wrist
                pip_y = mcp_y + 0.04 * grab_factor
                dip_y = mcp_y + 0.07 * grab_factor
                tip_y = wy - 0.005
                tip_x = wx + bx_off * 0.4
                z_offset = -0.01
            else:
                pip_len = 0.05 * (1.0 - curl * 0.4)
                dip_len = 0.04 * (1.0 - curl * 0.6)
                tip_len = 0.03 * (1.0 - curl * 0.8)

                pip_y = mcp_y - pip_len
                dip_y = pip_y - dip_len
                tip_y = dip_y - tip_len
                tip_x = mcp_x
                z_offset = -0.05 * curl

            landmarks.append(NormalizedLandmark(x=mcp_x, y=pip_y, z=wz + z_offset * 0.5))
            landmarks.append(NormalizedLandmark(x=mcp_x, y=dip_y, z=wz + z_offset * 0.8))

            # Special case for Index tip if pinching: meet thumb tip
            if i == 1 and pinch_factor > 0.0:
                final_tip_x = (target_thumb_tip_x) * pinch_factor + mcp_x * (1.0 - pinch_factor)
                final_tip_y = (target_thumb_tip_y) * pinch_factor + tip_y * (1.0 - pinch_factor)
                landmarks.append(NormalizedLandmark(x=final_tip_x, y=final_tip_y, z=wz + z_offset))
            else:
                landmarks.append(NormalizedLandmark(x=tip_x, y=tip_y, z=wz + z_offset))

        frame = HandLandmarkFrame(
            frame_index=self._frame_index,
            timestamp=self._time_elapsed,
            handedness=self._handedness,
            landmarks=landmarks,
            confidence=0.98,
        )

        self._frame_index += 1
        self._time_elapsed += 1.0 / self._config.target_fps
        return frame

    def get_next_frame(self) -> HandLandmarkFrame:
        """Sequential generator yielding stationary open-hand landmarks."""
        return self.generate_frame(pinch_factor=0.0, grab_factor=0.0)

    def generate_pinch_sequence(self, num_frames: int = 10) -> list[HandLandmarkFrame]:
        """Generate a smooth transition from open palm to tight pinch."""
        frames: list[HandLandmarkFrame] = []
        for step in range(num_frames):
            factor = step / max(1, num_frames - 1)
            frames.append(self.generate_frame(pinch_factor=factor, grab_factor=0.0))
        return frames

    def generate_grab_sequence(self, num_frames: int = 10) -> list[HandLandmarkFrame]:
        """Generate a smooth transition from open palm to tight grab."""
        frames: list[HandLandmarkFrame] = []
        for step in range(num_frames):
            factor = step / max(1, num_frames - 1)
            frames.append(self.generate_frame(pinch_factor=0.0, grab_factor=factor))
        return frames

    def generate_rotation_sequence(
        self, num_frames: int = 15, clockwise: bool = True
    ) -> list[HandLandmarkFrame]:
        """Generate a sequence rotating wrist in circular trajectory."""
        frames: list[HandLandmarkFrame] = []
        direction = 1.0 if clockwise else -1.0
        for step in range(num_frames):
            angle = direction * (step / num_frames) * 2.0 * math.pi
            rx = 0.5 + 0.1 * math.cos(angle)
            ry = 0.7 + 0.1 * math.sin(angle)
            frames.append(self.generate_frame(grab_factor=0.8, wrist_pos=(rx, ry, 0.0)))
        return frames
