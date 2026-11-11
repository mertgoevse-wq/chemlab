"""
Unit and integration tests for ChemLab Hand Tracker IPC Server (Port 8766).
Verifies TCP socket binding, client streaming, JSON-delimited protocol,
and graceful fallback when physical camera hardware is absent.
"""

import json
import socket
import time

import pytest

from chemlab.cv.hand_tracker_server import HandTrackerServer


def test_hand_tracker_server_initialization():
    server = HandTrackerServer(host="127.0.0.1", port=18766, use_synthetic=True)
    assert server.host == "127.0.0.1"
    assert server.port == 18766
    assert server.use_synthetic is True
    assert not server.is_running


def test_hand_tracker_server_lifecycle():
    server = HandTrackerServer(host="127.0.0.1", port=18767, use_synthetic=True)
    server.start()
    assert server.is_running

    # Verify socket is listening
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    sock.connect(("127.0.0.1", 18767))
    sock.close()

    server.stop()
    assert not server.is_running


def test_hand_tracker_server_streams_json_telemetry():
    server = HandTrackerServer(host="127.0.0.1", port=18768, use_synthetic=True)
    server.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2.0)
    client.connect(("127.0.0.1", 18768))

    # Read one or more lines of JSON telemetry
    buffer = ""
    start_time = time.time()
    packet = None

    while time.time() - start_time < 3.0:
        chunk = client.recv(1024).decode("utf-8")
        buffer += chunk
        if "\n" in buffer:
            line, _ = buffer.split("\n", 1)
            line = line.strip()
            if line:
                packet = json.loads(line)
                break

    client.close()
    server.stop()

    assert packet is not None, "Failed to receive telemetry packet from server"
    assert "gesture" in packet
    assert "confidence" in packet
    assert "is_pinching" in packet
    assert "is_grabbing" in packet
    assert "tilt_degrees" in packet
    assert "pour_rate" in packet
    assert "world_position_3d" in packet
