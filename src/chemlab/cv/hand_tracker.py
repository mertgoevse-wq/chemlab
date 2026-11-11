"""
ChemLab Optimized Hand Tracking for Intel Iris Xe (128MB VRAM, 16GB RAM, Dell Latitude 5530).
Optimized: MediaPipe Hands only (not Holistic), 320x240 input, frame skipping (every 2nd frame),
async pipeline (capture → process → apply), GDScript-side prediction (OneEuroFilter + Kalman),
fallback to mouse/keyboard seamlessly.

Gesture mapping:
- pinch = pickup (test tubes, pipettes, spatulas)
- pinch + drag = pour (tilt-governed fluid transfer)
- swipe = turn knob (stir plate dials, burner valves)
- grab = move vessel (beakers, flasks, bottles)
- point = raycast select (HUD buttons, GHS placards, balances)
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from queue import Empty, Queue

from chemlab.compat import StrEnum
from chemlab.cv.one_euro_filter import Point3DOneEuroFilter
from chemlab_core.models import (
    Handedness,
    HandLandmarkFrame,
    NormalizedLandmark,
)

# =============================================================================
# PERFORMANCE CONSTANTS (tuned for Intel Iris Xe, Dell Latitude 5530)
# =============================================================================

# Input resolution - reduced from 640x480/720p for 3-4x inference speedup
TARGET_INPUT_WIDTH = 320
TARGET_INPUT_HEIGHT = 240

# Frame processing - process every Nth frame (2 = 15 FPS tracking on 30 FPS webcam)
FRAME_SKIP_INTERVAL = 2

# MediaPipe Hands model complexity: 0=lite, 1=full, 2=heavy
# 0 = ~1.5ms inference, 1 = ~3ms, 2 = ~6ms on Iris Xe
MODEL_COMPLEXITY = 0

# Max hands to track (1 = half the computation)
MAX_NUM_HANDS = 1

# Min detection/tracking confidence
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Target performance budgets (from TRACKING_ARCHITECTURE.md)
# CPU: <10% on i5-1240U, Pipeline: 30 FPS render + 15-30 FPS tracking
# Inference: <12ms per frame, Smoothing: <0.8ms


class OptimizedGesture(StrEnum):
    """Optimized gesture set for chemistry lab interactions."""

    IDLE = "IDLE"
    PINCH = "PINCH"  # Pickup small apparatus (test tubes, pipettes)
    PINCH_DRAG = "PINCH_DRAG"  # Pinch + move = pour
    POUR = "PINCH_DRAG"  # Backward compatibility alias
    SWIRL = "SWIRL"  # Backward compatibility alias
    GRAB = "GRAB"  # Move vessel (beakers, flasks)
    FIST = "FIST"  # Firm lock on vessel
    SWIPE = "SWIPE"  # Turn knob (stir plate, valve)
    POINT = "POINT"  # Raycast select (UI, balances)
    RELEASE = "RELEASE"


@dataclass
class OptimizedHandResult:
    """Lightweight telemetry packet for optimized pipeline."""

    timestamp: float
    frame_index: int
    handedness: Handedness
    gesture: OptimizedGesture
    pinch_distance: float
    is_pinching: bool
    is_grabbing: bool
    grab_strength: float
    tilt_degrees: float
    pour_rate: float
    swipe_delta_x: float = 0.0
    swipe_delta_y: float = 0.0
    world_position_3d: tuple[float, float, float] = (0.0, 0.0, 0.0)
    confidence: float = 1.0
    landmarks_smoothed: list[NormalizedLandmark] = field(default_factory=list)


def _dist_3d(p1: NormalizedLandmark, p2: NormalizedLandmark) -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = p1.z - p2.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _dist_2d(p1: NormalizedLandmark, p2: NormalizedLandmark) -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return math.sqrt(dx * dx + dy * dy)


class OptimizedGestureEngine:
    """
    Lightweight gesture engine for MediaPipe Hands (21 landmarks only).
    No holistic body tracking - pure hand gestures for chemistry interactions.
    """

    def __init__(
        self,
        pinch_enter: float = 0.045,
        pinch_exit: float = 0.065,
        grab_enter: float = 0.16,
        grab_exit: float = 0.20,
        pour_angle_enter: float = 48.0,
        pour_angle_exit: float = 42.0,
        swipe_threshold: float = 0.03,
    ) -> None:
        # Schmitt trigger hysteresis thresholds
        self.pinch_enter = pinch_enter
        self.pinch_exit = pinch_exit
        self.grab_enter = grab_enter
        self.grab_exit = grab_exit
        self.pour_angle_enter = pour_angle_enter
        self.pour_angle_exit = pour_angle_exit
        self.swipe_threshold = swipe_threshold

        # State memory for hysteresis
        self._prev_is_pinching = False
        self._prev_is_grabbing = False
        self._prev_is_pouring = False
        self._prev_pinch_center: tuple[float, float] = (0.5, 0.5)
        self._swipe_accumulator_x = 0.0
        self._swipe_accumulator_y = 0.0

    def analyze(self, frame: HandLandmarkFrame) -> OptimizedHandResult:
        lms = frame.landmarks
        wrist = lms[0]
        thumb_tip = lms[4]
        index_tip = lms[8]
        middle_tip = lms[12]
        ring_tip = lms[16]
        pinky_tip = lms[20]
        index_mcp = lms[5]
        pinky_mcp = lms[17]
        thumb_mcp = lms[2]

        # 1. PINCH (Thumb tip to Index tip) - for pickup
        pinch_dist = _dist_3d(thumb_tip, index_tip)
        is_pinching = (
            pinch_dist < self.pinch_enter
            if not self._prev_is_pinching
            else pinch_dist < self.pinch_exit
        )

        # 2. GRAB (Mean fingertip to wrist distance) - for move vessel
        fingertip_dists = [
            _dist_3d(index_tip, wrist),
            _dist_3d(middle_tip, wrist),
            _dist_3d(ring_tip, wrist),
            _dist_3d(pinky_tip, wrist),
        ]
        avg_finger_dist = sum(fingertip_dists) / 4.0
        is_grabbing = (
            avg_finger_dist < self.grab_enter
            if not self._prev_is_grabbing
            else avg_finger_dist < self.grab_exit
        )
        grab_strength = max(0.0, min(1.0, 1.0 - (avg_finger_dist / (self.grab_exit * 1.2))))

        # 3. HAND TILT (Pinky MCP to Index MCP vector) - for pour
        dx_knuckle = index_mcp.x - pinky_mcp.x
        dy_knuckle = index_mcp.y - pinky_mcp.y
        dz_knuckle = index_mcp.z - pinky_mcp.z
        tilt_rad = math.atan2(dy_knuckle + dz_knuckle * 0.5, abs(dx_knuckle) + 1e-5)
        tilt_degrees = math.degrees(tilt_rad)

        # 4. POINTING (Index extended, others curled) - for raycast select
        dist_index_wrist = _dist_3d(index_tip, wrist)
        dist_middle_wrist = _dist_3d(middle_tip, wrist)
        dist_ring_wrist = _dist_3d(ring_tip, wrist)
        is_pointing = (
            dist_index_wrist > 0.20
            and dist_middle_wrist < 0.13
            and dist_ring_wrist < 0.13
            and not is_pinching
        )

        # 5. SWIPE detection (Pinch + horizontal movement) - for turn knob
        pinch_center_x = (thumb_tip.x + index_tip.x) * 0.5
        pinch_center_y = (thumb_tip.y + index_tip.y) * 0.5
        swipe_delta_x = 0.0
        swipe_delta_y = 0.0
        is_swiping = False
        if is_pinching and self._prev_is_pinching:
            swipe_delta_x = pinch_center_x - self._prev_pinch_center[0]
            swipe_delta_y = pinch_center_y - self._prev_pinch_center[1]
            swipe_magnitude = math.hypot(swipe_delta_x, swipe_delta_y)
            is_swiping = swipe_magnitude > self.swipe_threshold

        # 6. GESTURE CLASSIFICATION with priority
        pour_rate = 0.0
        gesture = OptimizedGesture.IDLE

        if is_swiping:
            gesture = OptimizedGesture.SWIPE
            self._swipe_accumulator_x += swipe_delta_x
            self._swipe_accumulator_y += swipe_delta_y
        elif is_pinching and abs(tilt_degrees) > self.pour_angle_enter:
            gesture = OptimizedGesture.PINCH_DRAG
            is_pouring = True
            pour_rate = min(1.0, (abs(tilt_degrees) - self.pour_angle_enter) / 30.0)
        elif is_pinching:
            gesture = OptimizedGesture.PINCH
            is_pouring = False
        elif is_grabbing:
            gesture = (
                OptimizedGesture.FIST
                if avg_finger_dist < self.grab_enter * 0.7
                else OptimizedGesture.GRAB
            )
        elif is_pointing:
            gesture = OptimizedGesture.POINT
        elif (
            (self._prev_is_pinching or self._prev_is_grabbing)
            and not is_pinching
            and not is_grabbing
        ):
            gesture = OptimizedGesture.RELEASE

        # Update state memory
        self._prev_is_pinching = is_pinching
        self._prev_is_grabbing = is_grabbing
        self._prev_pinch_center = (pinch_center_x, pinch_center_y)

        # World position (centroid of pinch or grab)
        if is_pinching:
            focus_x = pinch_center_x
            focus_y = pinch_center_y
            focus_z = (thumb_tip.z + index_tip.z) * 0.5
        else:
            focus_x = wrist.x
            focus_y = wrist.y
            focus_z = wrist.z

        # Camera space [0..1] → Blender lab coordinates
        # X: [-0.8, +0.8], Y (depth): [0.3, 1.2], Z (height): [0.7, 1.4]
        world_x = round((focus_x - 0.5) * 1.6, 4)
        world_y = round(0.5 + (1.0 - focus_z) * 0.7, 4)
        world_z = round(1.2 - focus_y * 0.8, 4)

        return OptimizedHandResult(
            timestamp=frame.timestamp,
            frame_index=frame.frame_index,
            handedness=frame.handedness,
            gesture=gesture,
            pinch_distance=round(pinch_dist, 4),
            is_pinching=is_pinching,
            is_grabbing=is_grabbing,
            grab_strength=round(grab_strength, 4),
            tilt_degrees=round(tilt_degrees, 2),
            pour_rate=round(pour_rate, 4),
            swipe_delta_x=round(swipe_delta_x, 4),
            swipe_delta_y=round(swipe_delta_y, 4),
            world_position_3d=(world_x, world_y, world_z),
            confidence=frame.confidence,
            landmarks_smoothed=list(frame.landmarks),
        )


class AsyncHandTracker:
    """
    High-performance async hand tracker for Intel Iris Xe.
    Architecture:
    - Thread 1: Camera capture (30 FPS, 320x240)
    - Thread 2: MediaPipe inference (process every 2nd frame = 15 FPS)
    - Thread 3: Gesture classification + 1-Euro smoothing (< 1ms)
    - Main thread: Consumes results, applies Kalman prediction for 60 FPS rendering
    """

    def __init__(
        self,
        camera_index: int = 0,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
        use_synthetic: bool = False,
    ) -> None:
        self.camera_index = camera_index
        self.use_synthetic = use_synthetic
        self.gesture_engine = OptimizedGestureEngine()

        # 21 independent 1-Euro filters for landmarks
        self._landmark_filters: list[Point3DOneEuroFilter] = [
            Point3DOneEuroFilter(min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff)
            for _ in range(21)
        ]

        # Async pipeline queues
        self._capture_queue: Queue = Queue(maxsize=2)  # Latest frame only
        self._result_queue: Queue = Queue(maxsize=4)  # Processed results
        self._running = False
        self._capture_thread: threading.Thread | None = None
        self._process_thread: threading.Thread | None = None
        self._frame_counter = 0
        self._process_every_n = FRAME_SKIP_INTERVAL

        # MediaPipe Hands (lazy init)
        self._mp_hands = None
        self._hands = None

        # Performance stats
        self._last_inference_ms = 0.0
        self._last_process_ms = 0.0

    def _init_mediapipe(self) -> None:
        """Lazy init MediaPipe Hands only (not Holistic)."""
        import mediapipe as mp

        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            model_complexity=MODEL_COMPLEXITY,
            max_num_hands=MAX_NUM_HANDS,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

    def start(self) -> None:
        """Start async capture and processing threads."""
        if self._running:
            return
        self._running = True

        if not self.use_synthetic:
            self._init_mediapipe()
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self._capture_thread.start()
            self._process_thread.start()
        else:
            # Synthetic mode: single-threaded for testing
            self._process_thread = threading.Thread(target=self._synthetic_loop, daemon=True)
            self._process_thread.start()

    def stop(self) -> None:
        """Stop all threads."""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=1.0)
        if self._process_thread:
            self._process_thread.join(timeout=1.0)
        if self._hands:
            self._hands.close()

    def _capture_loop(self) -> None:
        """Camera capture thread - runs at 30 FPS, pushes to queue."""
        import cv2

        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_INPUT_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_INPUT_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.001)
                continue

            # Drop old frames, keep only latest
            try:
                self._capture_queue.put_nowait((frame, time.time()))
            except:
                try:
                    self._capture_queue.get_nowait()
                    self._capture_queue.put_nowait((frame, time.time()))
                except:
                    pass

        cap.release()

    def _process_loop(self) -> None:
        """MediaPipe inference + gesture thread - runs at ~15 FPS (frame skip)."""
        import cv2

        frame_skip_counter = 0

        while self._running:
            try:
                frame, capture_time = self._capture_queue.get(timeout=0.1)
            except Empty:
                continue

            frame_skip_counter += 1
            if frame_skip_counter < self._process_every_n:
                continue
            frame_skip_counter = 0

            # MediaPipe inference
            infer_start = time.perf_counter()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = self._hands.process(rgb)
            self._last_inference_ms = (time.perf_counter() - infer_start) * 1000

            if not results.multi_hand_landmarks:
                continue

            # Process first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness = Handedness.RIGHT
            if results.multi_handedness:
                h = results.multi_handedness[0].classification[0].label
                handedness = Handedness.LEFT if h == "Left" else Handedness.RIGHT

            # Extract normalized landmarks
            raw_landmarks = []
            for lm in hand_landmarks.landmark:
                raw_landmarks.append(
                    NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)
                )

            # 1-Euro smoothing
            process_start = time.perf_counter()
            t = time.time()
            self._frame_counter += 1

            smoothed_lms = []
            for i, lm in enumerate(raw_landmarks):
                filt = self._landmark_filters[i]
                sx, sy, sz = filt(t, (lm.x, lm.y, lm.z))
                smoothed_lms.append(NormalizedLandmark(x=sx, y=sy, z=sz, visibility=lm.visibility))

            frame_obj = HandLandmarkFrame(
                frame_index=self._frame_counter,
                timestamp=t,
                handedness=handedness,
                landmarks=smoothed_lms,
                confidence=0.98,
            )

            result = self.gesture_engine.analyze(frame_obj)
            self._last_process_ms = (time.perf_counter() - process_start) * 1000

            # Push result (non-blocking, drop old if full)
            try:
                self._result_queue.put_nowait(result)
            except:
                try:
                    self._result_queue.get_nowait()
                    self._result_queue.put_nowait(result)
                except:
                    pass

    def _synthetic_loop(self) -> None:
        """Synthetic mode for testing without camera."""
        while self._running:
            time.sleep(1 / 30)  # Simulate 30 FPS

    def get_latest_result(self) -> OptimizedHandResult | None:
        """Non-blocking get latest tracking result. Returns None if no new data."""
        try:
            return self._result_queue.get_nowait()
        except Empty:
            return None

    def process_landmarks(
        self,
        landmarks: list[NormalizedLandmark],
        handedness: Handedness = Handedness.RIGHT,
        timestamp: float | None = None,
    ) -> OptimizedHandResult:
        """Synchronous processing for synthetic/testing mode."""
        t = timestamp if timestamp is not None else time.time()
        self._frame_counter += 1

        # Smooth landmarks
        smoothed_lms = []
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

        return self.gesture_engine.analyze(frame)

    def get_performance_stats(self) -> dict:
        """Return performance metrics for monitoring."""
        return {
            "inference_ms": round(self._last_inference_ms, 2),
            "process_ms": round(self._last_process_ms, 2),
            "total_ms": round(self._last_inference_ms + self._last_process_ms, 2),
            "queue_depth": self._result_queue.qsize(),
        }


# Backward compatibility aliases
AirGuitarGesture = OptimizedGesture
HandTrackingResult = OptimizedHandResult
AirGuitarGestureEngine = OptimizedGestureEngine
WebcamHandTracker = AsyncHandTracker
