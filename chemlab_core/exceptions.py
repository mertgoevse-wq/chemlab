"""
Structured Exception Hierarchy.
Prevents silent exception swallowing and enforces explicit error categorization.
"""

from typing import Any


class ChemLabError(Exception):
    """Base exception for all chemistry lab domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class VisionTrackingError(ChemLabError):
    """Raised when landmark extraction or camera feed fails."""


class GestureClassificationError(VisionTrackingError):
    """Raised when gesture classification encounters invalid landmark structures."""


class IPCTransportError(ChemLabError):
    """Base exception for network and IPC communication faults."""


class ConnectionRefusedError(IPCTransportError):
    """Raised when the Blender socket server is offline or unreachable."""


class SocketTimeoutError(IPCTransportError):
    """Raised when socket write or read exceeds configured timeout."""


class ProtocolSerializationError(IPCTransportError):
    """Raised when JSON-RPC or IPC payload fails schema validation."""


class BlenderControllerError(ChemLabError):
    """Base exception for Blender 3D scene manipulation faults."""


class SceneExecutionError(BlenderControllerError):
    """Raised when Blender fails to execute a Python operator or script."""


class AssetLoadError(BlenderControllerError):
    """Raised when a chemical apparatus or .blend asset fails to link/import."""
