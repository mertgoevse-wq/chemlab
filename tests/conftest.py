"""
Pytest configuration and shared fixtures for ChemLab verification suite.
Enables headless CI testing with mock network sockets and synthetic landmarks.
"""

import socket
from collections.abc import Generator

import pytest

from chemlab_core.config import ChemLabSettings, IPCConfig, VisionConfig
from chemlab_core.models import (
    Handedness,
    IPCRequest,
    IPCResponse,
    IPCStatus,
)
from chemlab_core.transport.contracts import IPCClient
from chemlab_core.transport.server import ThreadedIPCServer
from chemlab_core.vision.synthetic import SyntheticLandmarkGenerator


def get_free_port() -> int:
    """Find an ephemeral free port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def test_settings() -> ChemLabSettings:
    """Provide isolated settings with high-speed timeouts for testing."""
    return ChemLabSettings(
        vision=VisionConfig(target_fps=60),
        ipc=IPCConfig(
            host="127.0.0.1",
            port=get_free_port(),
            connect_timeout_seconds=1.0,
            command_timeout_seconds=2.0,
        ),
    )


@pytest.fixture
def synthetic_generator() -> SyntheticLandmarkGenerator:
    """Fixture providing deterministic synthetic landmark frames."""
    return SyntheticLandmarkGenerator(handedness=Handedness.RIGHT)


class DummyMockIPCClient(IPCClient):
    """In-memory mock client recording dispatches without network I/O."""

    def __init__(self) -> None:
        self.dispatched_requests: list[IPCRequest] = []

    def send_request(self, request: IPCRequest) -> IPCResponse:
        self.dispatched_requests.append(request)
        return IPCResponse(
            request_id=request.request_id,
            status=IPCStatus.SUCCESS,
            result={"mock_executed": True, "type": request.type.value},
            duration_ms=0.5,
        )

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        pass


@pytest.fixture
def mock_ipc_client() -> DummyMockIPCClient:
    """In-memory mock client for scene controller unit testing."""
    return DummyMockIPCClient()


@pytest.fixture
def running_ipc_server(test_settings: ChemLabSettings) -> Generator[ThreadedIPCServer, None, None]:
    """Spawns an active ThreadedIPCServer on a free port and tears it down cleanly."""
    server = ThreadedIPCServer(config=test_settings.ipc)
    server.start()
    yield server
    server.stop()
