"""
Tests for ChemLab IPC Bridge Server.
Verifies the TCP server correctly handles Godot SimulationBridge protocol.
"""

import json
import socket
import threading
import time

import pytest

from chemlab.simulation.ipc_bridge_server import ThreadedIPCServer


@pytest.fixture
def ipc_server():
    """Create and start a test IPC server on a free port."""
    import socket as sock_module

    def get_free_port():
        with sock_module.socket(sock_module.AF_INET, sock_module.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return int(s.getsockname()[1])

    port = get_free_port()
    server = ThreadedIPCServer(host="127.0.0.1", port=port)
    server.start()
    time.sleep(0.3)  # Allow server to fully start
    yield server, port
    server.stop()


def _send_request(port: int, request: dict) -> dict:
    """Send a request to the IPC server and return parsed response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(("127.0.0.1", port))

    try:
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

        buffer = ""
        while "\n" not in buffer:
            chunk = sock.recv(8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8")

        return json.loads(buffer.strip())
    finally:
        sock.close()


class TestIPCBridgeServer:
    """Test the IPC Bridge Server functionality."""

    def test_handshake(self, ipc_server):
        """Test HANDSHAKE command returns server info and supported commands."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-handshake-1",
                "command": "HANDSHAKE",
                "payload": {"client": "test_client", "version": "1.0"},
            },
        )

        assert response["request_id"] == "test-handshake-1"
        assert response["status"] == "SUCCESS"
        assert "data" in response
        data = response["data"]
        assert data["status"] == "connected"
        assert data["server"] == "chemlab_ipc_bridge"
        assert "engines" in data
        assert data["engines"]["analytical"] is True
        assert data["engines"]["genetics"] is True
        assert data["engines"]["nuclear"] is True
        assert "supported_commands" in data
        assert "MIX_REAGENTS" in data["supported_commands"]
        assert "NMR" in data["supported_commands"]
        assert "PCR" in data["supported_commands"]
        assert "DECAY_CHAIN" in data["supported_commands"]

    def test_mix_reagents_acid_base_neutralization(self, ipc_server):
        """Test MIX_REAGENTS with HCl + NaOH neutralization."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-mix-1",
                "command": "MIX_REAGENTS",
                "payload": {
                    "vessel_id": "beaker_1",
                    "reagents": [{"id": "hcl", "moles": 0.05}, {"id": "naoh", "moles": 0.05}],
                    "temperature_c": 22.0,
                    "addition_order_correct": True,
                    "in_fume_hood": True,
                },
            },
        )

        assert response["request_id"] == "test-mix-1"
        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert data["vessel_id"] == "beaker_1"
        assert "HCl + NaOH" in data["reaction_name"]
        assert data["is_exothermic"] is True
        assert data["delta_h_kj_mol"] == -57.1
        # Temperature should rise but stay reasonable (< 100°C)
        assert 22.0 < data["temperature_c"] < 100.0
        assert data["color_rgba"][3] == 0.0  # Colorless after neutralization

    def test_mix_reagents_elephant_toothpaste(self, ipc_server):
        """Test MIX_REAGENTS with H2O2 + KI (elephant toothpaste)."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-mix-2",
                "command": "MIX_REAGENTS",
                "payload": {
                    "vessel_id": "beaker_2",
                    "reagents": [{"id": "h2o2", "moles": 0.1}, {"id": "ki", "moles": 0.02}],
                    "temperature_c": 22.0,
                    "addition_order_correct": True,
                    "in_fume_hood": True,
                },
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert (
            "Elephant Toothpaste" in data["reaction_name"] or "Catalytic" in data["reaction_name"]
        )
        assert data["is_exothermic"] is True
        assert data["bubbles_per_second"] > 0
        assert data["temperature_c"] > 22.0

    def test_mix_reagents_precipitation(self, ipc_server):
        """Test MIX_REAGENTS with Ag+ + Cl- precipitation."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-mix-3",
                "command": "MIX_REAGENTS",
                "payload": {
                    "vessel_id": "beaker_3",
                    "reagents": [{"id": "Ag+", "moles": 0.01}, {"id": "Cl-", "moles": 0.01}],
                    "temperature_c": 22.0,
                },
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert data["precipitate_formed"] is True
        assert "Silver Chloride" in data["precipitate_name"]
        assert data["turbidity"] > 0.0

    def test_mix_reagents_invalid_payload(self, ipc_server):
        """Test MIX_REAGENTS rejects invalid reagent format."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-mix-4",
                "command": "MIX_REAGENTS",
                "payload": {
                    "vessel_id": "beaker_4",
                    "reagents": [
                        {"id": "hcl"}  # Missing 'moles'
                    ],
                },
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert "error" in data
        assert "moles" in data["error"].lower()

    def test_unknown_command(self, ipc_server):
        """Test unknown command returns ERROR status."""
        server, port = ipc_server

        response = _send_request(
            port, {"request_id": "test-unknown-1", "command": "UNKNOWN_COMMAND_XYZ", "payload": {}}
        )

        assert response["request_id"] == "test-unknown-1"
        assert response["status"] == "ERROR"
        assert "unknown" in response.get("error", "").lower() or "unknown" in str(response).lower()

    def test_multiple_concurrent_clients(self, ipc_server):
        """Test server handles multiple concurrent client connections."""
        server, port = ipc_server

        def client_thread(client_id: int, results: list):
            try:
                response = _send_request(
                    port,
                    {
                        "request_id": f"concurrent-{client_id}",
                        "command": "HANDSHAKE",
                        "payload": {"client": f"client_{client_id}"},
                    },
                )
                results.append(("success", response))
            except Exception as e:
                results.append(("error", str(e)))

        threads = []
        results = []
        for i in range(5):
            t = threading.Thread(target=client_thread, args=(i, results))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=5.0)

        # All should succeed
        assert len(results) == 5
        for status, resp in results:
            assert status == "success"
            assert resp["status"] == "SUCCESS"

    def test_step_simulation(self, ipc_server):
        """Test STEP_SIMULATION command returns valid vessel state."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-step-1",
                "command": "STEP_SIMULATION",
                "payload": {"vessel_id": "vessel_1", "dt": 0.1},
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert "vessel" in data
        vessel = data["vessel"]
        assert vessel["vessel_id"] == "vessel_1"
        assert "volume_ml" in vessel
        assert "temperature_c" in vessel
        assert "ph" in vessel
        assert "species_moles" in vessel

    def test_nmr_command(self, ipc_server):
        """Test NMR spectroscopy command."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-nmr-1",
                "command": "NMR",
                "payload": {
                    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
                    "nucleus": "1H",
                    "field_mhz": 400.0,
                },
            },
        )

        assert response["status"] == "SUCCESS"
        assert "data" in response
        data = response["data"]
        assert "spectrum" in data

    def test_pcr_command(self, ipc_server):
        """Test PCR simulation command."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-pcr-1",
                "command": "PCR",
                "payload": {
                    "template": "ATCGATCGATCG",
                    "forward_primer": "ATCGAT",
                    "reverse_primer": "GATCGA",
                    "cycles": 30,
                    "annealing_temp_c": 60.0,
                },
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert "amplicon" in data

    def test_decay_chain_command(self, ipc_server):
        """Test nuclear decay chain simulation."""
        server, port = ipc_server

        response = _send_request(
            port,
            {
                "request_id": "test-decay-1",
                "command": "DECAY_CHAIN",
                "payload": {"isotope": "U-238", "time_steps": 10, "dt_s": 1.0},
            },
        )

        assert response["status"] == "SUCCESS"
        data = response["data"]
        assert "decay_chain" in data


class TestIPCServerLifecycle:
    """Test server start/stop lifecycle."""

    def test_server_start_stop(self):
        """Test server can be started and stopped cleanly."""
        import socket as sock_module

        def get_free_port():
            with sock_module.socket(sock_module.AF_INET, sock_module.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                return int(s.getsockname()[1])

        port = get_free_port()
        server = ThreadedIPCServer(host="127.0.0.1", port=port)

        assert not server.is_running

        server.start()
        time.sleep(0.2)
        assert server.is_running

        server.stop()
        time.sleep(0.1)
        assert not server.is_running

    def test_context_manager(self):
        """Test server works as context manager."""
        import socket as sock_module

        def get_free_port():
            with sock_module.socket(sock_module.AF_INET, sock_module.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                return int(s.getsockname()[1])

        port = get_free_port()

        with ThreadedIPCServer(host="127.0.0.1", port=port) as server:
            time.sleep(0.2)
            assert server.is_running

            # Verify we can connect
            response = _send_request(
                port, {"request_id": "ctx-test", "command": "HANDSHAKE", "payload": {}}
            )
            assert response["status"] == "SUCCESS"

        # Server should be stopped after context exit
        time.sleep(0.1)
        assert not server.is_running
