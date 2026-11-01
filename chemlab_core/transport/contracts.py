"""
Contracts for IPC Network Transport.
Decouples socket I/O from domain gesture events and Blender API.
"""

from typing import Protocol, runtime_checkable

from chemlab_core.models import IPCRequest, IPCResponse


@runtime_checkable
class IPCClient(Protocol):
    """Protocol for sending structured requests to the Blender IPC bridge."""

    def send_request(self, request: IPCRequest) -> IPCResponse:
        """Send an IPCRequest and block until IPCResponse or timeout."""
        ...

    def ping(self) -> bool:
        """Verify bridge connectivity."""
        ...

    def close(self) -> None:
        """Release underlying socket resources."""
        ...


@runtime_checkable
class IPCServer(Protocol):
    """Protocol for the receiving server (Blender add-on or test harness)."""

    def start(self) -> None:
        """Start listening on the configured port."""
        ...

    def stop(self) -> None:
        """Gracefully terminate the server and close all client connections."""
        ...

    @property
    def is_running(self) -> bool:
        """Return True if the server is actively listening."""
        ...
