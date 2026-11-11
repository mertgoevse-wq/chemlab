"""
ChemLab Hand Tracker IPC Server — Real-Time CV Telemetry Stream (Port 8766).

Streams 3D skeletal hand landmarks, smoothed coordinates, and classified laboratory
gestures (PINCH, PINCH_DRAG, GRAB, SWIPE, POINT) from MediaPipe / AsyncHandTracker
to Godot's InputManager over a low-latency TCP socket.
"""

from __future__ import annotations

import contextlib
import json
import logging
import math
import socket
import threading
import time

from chemlab.cv.hand_tracker import (
    AsyncHandTracker,
    OptimizedGesture,
    OptimizedHandResult,
)
from chemlab_core.models import Handedness

logger = logging.getLogger(__name__)


class HandTrackerServer:
    """
    TCP streaming server broadcasting real-time hand tracking telemetry to Godot.
    Default port: 8766 (Godot InputManager).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8766,
        camera_index: int = 0,
        use_synthetic: bool = False,
        broadcast_rate_hz: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.camera_index = camera_index
        self.use_synthetic = use_synthetic
        self.broadcast_interval = 1.0 / max(1.0, broadcast_rate_hz)

        self._server_socket: socket.socket | None = None
        self._listen_thread: threading.Thread | None = None
        self._running = False
        self._clients: list[socket.socket] = []
        self._clients_lock = threading.Lock()

        # Initialize tracker
        self._tracker: AsyncHandTracker | None = None
        self._init_tracker()

    def _init_tracker(self) -> None:
        """Initialize AsyncHandTracker with graceful hardware fallback."""
        try:
            if not self.use_synthetic:
                # Try opening camera briefly or instantiate tracker
                self._tracker = AsyncHandTracker(
                    camera_index=self.camera_index,
                    use_synthetic=False,
                )
            else:
                self._tracker = AsyncHandTracker(use_synthetic=True)
        except Exception as e:
            logger.warning(
                "Failed to initialize physical camera (%s); falling back to synthetic tracker.", e
            )
            self.use_synthetic = True
            self._tracker = AsyncHandTracker(use_synthetic=True)

    @property
    def is_running(self) -> bool:
        return self._running and self._server_socket is not None

    def start(self) -> None:
        """Bind socket and begin broadcasting in a background thread."""
        if self._running:
            return

        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        self._server_socket.settimeout(0.5)

        if self._tracker:
            try:
                self._tracker.start()
            except Exception as e:
                logger.warning("Camera start error (%s); falling back to synthetic generator.", e)
                self.use_synthetic = True

        self._listen_thread = threading.Thread(
            target=self._accept_loop,
            name="HandTracker-AcceptLoop",
            daemon=True,
        )
        self._listen_thread.start()
        logger.info(
            "HandTrackerServer listening on %s:%d (synthetic=%s)",
            self.host,
            self.port,
            self.use_synthetic,
        )

    def stop(self) -> None:
        """Stop listening and disconnect all clients."""
        self._running = False

        if self._tracker:
            with contextlib.suppress(Exception):
                self._tracker.stop()

        with self._clients_lock:
            for client in self._clients:
                with contextlib.suppress(Exception):
                    client.close()
            self._clients.clear()

        if self._server_socket:
            with contextlib.suppress(Exception):
                self._server_socket.close()
            self._server_socket = None

        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None

        logger.info("HandTrackerServer stopped.")

    def _accept_loop(self) -> None:
        """Accept incoming Godot client connections."""
        while self._running:
            try:
                if not self._server_socket:
                    break
                client_sock, client_addr = self._server_socket.accept()
                logger.info("Godot client connected to hand tracker from %s", client_addr)
                with self._clients_lock:
                    self._clients.append(client_sock)

                worker = threading.Thread(
                    target=self._client_broadcast_loop,
                    args=(client_sock, client_addr),
                    name=f"HandTracker-Client-{client_addr}",
                    daemon=True,
                )
                worker.start()
            except TimeoutError:
                continue
            except OSError:
                break

    def _client_broadcast_loop(self, client_sock: socket.socket, client_addr: tuple) -> None:
        """Stream JSON-encoded telemetry packets to a connected client."""
        client_sock.settimeout(2.0)
        t_start = time.time()
        frame_idx = 0

        try:
            while self._running:
                t_now = time.time()
                result = None

                if self._tracker and not self.use_synthetic:
                    result = self._tracker.get_latest_result()

                if result is None:
                    # Generate smooth synthetic telemetry frame
                    elapsed = t_now - t_start
                    frame_idx += 1
                    result = self._generate_synthetic_result(elapsed, frame_idx)

                packet_dict = self._result_to_dict(result)
                payload = json.dumps(packet_dict) + "\n"
                client_sock.sendall(payload.encode("utf-8"))

                time.sleep(self.broadcast_interval)

        except (OSError, BrokenPipeError, ConnectionResetError):
            logger.info("Client %s disconnected from hand tracker.", client_addr)
        finally:
            with self._clients_lock:
                if client_sock in self._clients:
                    self._clients.remove(client_sock)
            with contextlib.suppress(Exception):
                client_sock.close()

    def _generate_synthetic_result(self, elapsed: float, frame_idx: int) -> OptimizedHandResult:
        """Generate smooth synthetic hand telemetry when no physical webcam is active."""
        # Gentle floating motion
        x = 0.5 + 0.08 * math.sin(elapsed * 0.8)
        y = 0.5 + 0.04 * math.cos(elapsed * 1.2)
        z = -0.2 + 0.02 * math.sin(elapsed * 0.5)

        # Periodic pinch cycle
        pinch_phase = math.sin(elapsed * 0.5)
        is_pinching = pinch_phase > 0.6
        pinch_dist = 0.02 if is_pinching else 0.08

        # Periodic tilt
        tilt = 25.0 * max(0.0, math.sin(elapsed * 0.4)) if is_pinching else 0.0
        pour_rate = (tilt / 45.0) * 10.0 if tilt > 5.0 else 0.0

        gesture = OptimizedGesture.IDLE
        if is_pinching and tilt > 5.0:
            gesture = OptimizedGesture.PINCH_DRAG
        elif is_pinching:
            gesture = OptimizedGesture.PINCH

        return OptimizedHandResult(
            timestamp=time.time(),
            frame_index=frame_idx,
            handedness=Handedness.RIGHT,
            gesture=gesture,
            pinch_distance=pinch_dist,
            is_pinching=is_pinching,
            is_grabbing=False,
            grab_strength=0.0,
            tilt_degrees=tilt,
            pour_rate=pour_rate,
            swipe_delta_x=0.0,
            swipe_delta_y=0.0,
            world_position_3d=(x, y, z),
            confidence=0.95,
        )

    def _result_to_dict(self, result: OptimizedHandResult) -> dict:
        """Convert OptimizedHandResult to dictionary matching Godot's schema."""
        return {
            "timestamp": result.timestamp,
            "frame_index": result.frame_index,
            "handedness": str(result.handedness),
            "gesture": str(result.gesture),
            "pinch_distance": float(result.pinch_distance),
            "is_pinching": bool(result.is_pinching),
            "is_grabbing": bool(result.is_grabbing),
            "grab_strength": float(result.grab_strength),
            "tilt_degrees": float(result.tilt_degrees),
            "pour_rate": float(result.pour_rate),
            "swipe_delta_x": float(result.swipe_delta_x),
            "swipe_delta_y": float(result.swipe_delta_y),
            "world_position_3d": list(result.world_position_3d),
            "confidence": float(result.confidence),
        }


def run_hand_tracker_server(
    host: str = "127.0.0.1",
    port: int = 8766,
    camera_index: int = 0,
    use_synthetic: bool = False,
) -> None:
    """CLI runner for standalone hand tracker server."""
    server = HandTrackerServer(
        host=host,
        port=port,
        camera_index=camera_index,
        use_synthetic=use_synthetic,
    )
    print(f"Starting ChemLab Hand Tracker Server on {host}:{port} (synthetic={use_synthetic})")
    print("Connecting to Godot InputManager. Press Ctrl+C to stop.")

    try:
        server.start()
        while server.is_running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping Hand Tracker Server...")
    finally:
        server.stop()


if __name__ == "__main__":
    import sys

    host = "127.0.0.1"
    port = 8766
    synthetic = False

    if "--synthetic" in sys.argv:
        synthetic = True
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        host = sys.argv[1]
    if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
        port = int(sys.argv[2])

    run_hand_tracker_server(host=host, port=port, use_synthetic=synthetic)
