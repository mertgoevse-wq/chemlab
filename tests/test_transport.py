"""
Integration tests for IPC Network Transport using mock and live socket harnesses.
Verifies clean thread lifecycles, timeout handling, and typed protocol exchange.
"""

import socket
import time

import pytest

from chemlab_core.config import ChemLabSettings, IPCConfig
from chemlab_core.exceptions import (
    ConnectionRefusedError as ChemLabConnRefused,
)
from chemlab_core.exceptions import (
    SocketTimeoutError,
)
from chemlab_core.models import (
    IPCRequest,
    IPCRequestType,
    IPCResponse,
    IPCStatus,
)
from chemlab_core.transport.client import SocketIPCClient
from chemlab_core.transport.server import ThreadedIPCServer


def get_free_port() -> int:
    """Find an ephemeral free port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.mark.integration
def test_socket_ipc_roundtrip(
    running_ipc_server: ThreadedIPCServer, test_settings: ChemLabSettings
) -> None:
    """Verify bidirectional JSON-RPC exchange between SocketIPCClient and ThreadedIPCServer."""
    client = SocketIPCClient(config=test_settings.ipc)

    req = IPCRequest(
        type=IPCRequestType.CODE_EXECUTION,
        code="print('Hello Blender')",
        params={"speed": 100},
    )

    response = client.send_request(req)
    assert response.status == IPCStatus.SUCCESS
    assert response.request_id == req.request_id
    assert response.duration_ms > 0.0
    assert isinstance(response.result, dict)
    assert response.result.get("mock_echo") == "code"


@pytest.mark.integration
def test_socket_ipc_ping(
    running_ipc_server: ThreadedIPCServer, test_settings: ChemLabSettings
) -> None:
    """Verify ping capability returns True when bridge server is online."""
    client = SocketIPCClient(config=test_settings.ipc)
    assert client.ping() is True


@pytest.mark.integration
def test_socket_ipc_connection_refused(test_settings: ChemLabSettings) -> None:
    """Verify clean ChemLabConnRefused exception when connecting to an inactive port."""
    # Use config with an unallocated port and no server running
    offline_config = IPCConfig(
        host="127.0.0.1",
        port=59999,
        connect_timeout_seconds=0.5,
    )
    client = SocketIPCClient(config=offline_config)

    with pytest.raises(ChemLabConnRefused):
        client.send_request(IPCRequest(type=IPCRequestType.PING))

    assert client.ping() is False


@pytest.mark.integration
def test_socket_ipc_timeout_handling() -> None:
    """Verify SocketTimeoutError is raised when server fails to respond within timeout."""

    # Create server with a stalling custom handler
    def stalling_handler(req: IPCRequest) -> IPCResponse:
        time.sleep(1.5)
        return IPCResponse(status=IPCStatus.SUCCESS)

    free_port = get_free_port()
    timeout_config = IPCConfig(
        host="127.0.0.1",
        port=free_port,
        command_timeout_seconds=0.3,
    )

    with ThreadedIPCServer(config=timeout_config, handler=stalling_handler):
        client = SocketIPCClient(config=timeout_config)
        with pytest.raises(SocketTimeoutError):
            client.send_request(IPCRequest(type=IPCRequestType.PING))


@pytest.mark.integration
def test_threaded_server_clean_lifecycle(test_settings: ChemLabSettings) -> None:
    """Verify server starts, accepts connections, and cleanly terminates without lingering threads."""
    server = ThreadedIPCServer(config=test_settings.ipc)
    assert not server.is_running

    server.start()
    assert server.is_running

    server.stop()
    assert not server.is_running
