"""
Robust IPC Network Client for Blender MCP communication.
Enforces typed schemas, explicit timeouts, and zero silent exception swallowing.
"""

import json
import logging
import socket
import time
from types import TracebackType

from pydantic import ValidationError

from chemlab_core.config import IPCConfig
from chemlab_core.exceptions import (
    ConnectionRefusedError as ChemLabConnRefused,
)
from chemlab_core.exceptions import (
    ProtocolSerializationError,
    SocketTimeoutError,
)
from chemlab_core.models import (
    IPCRequest,
    IPCRequestType,
    IPCResponse,
    IPCStatus,
)
from chemlab_core.transport.contracts import IPCClient

logger = logging.getLogger(__name__)


class SocketIPCClient(IPCClient):
    """Thread-safe TCP client for bidirectional communication with Blender MCP."""

    def __init__(self, config: IPCConfig | None = None) -> None:
        self._config = config or IPCConfig()

    def __enter__(self) -> "SocketIPCClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def send_request(self, request: IPCRequest) -> IPCResponse:
        """Transmit an IPCRequest and parse the validated IPCResponse."""
        start_time = time.perf_counter()
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(self._config.command_timeout_seconds)

        try:
            raw_sock.connect((self._config.host, self._config.port))
            serialized_payload = request.model_dump_json() + "\n"
            raw_sock.sendall(serialized_payload.encode("utf-8"))

            # Receive buffer until complete newline-delimited JSON
            buffer = ""
            while True:
                chunk = raw_sock.recv(self._config.buffer_size)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                if "\n" in buffer:
                    break

            if not buffer.strip():
                duration = (time.perf_counter() - start_time) * 1000.0
                return IPCResponse(
                    request_id=request.request_id,
                    status=IPCStatus.ERROR,
                    error="Empty response received from Blender bridge",
                    duration_ms=duration,
                )

            # Parse JSON
            raw_data = json.loads(buffer.strip().split("\n")[0])
            duration = (time.perf_counter() - start_time) * 1000.0

            # Map raw response fields to typed IPCResponse
            status_str = raw_data.get("status", "error")
            status = IPCStatus.SUCCESS if status_str in ("success", "executed") else IPCStatus.ERROR

            result_payload = raw_data.get("result")
            if result_payload is None and "scene" in raw_data:
                result_payload = raw_data.get("scene")
            elif result_payload is None and status == IPCStatus.SUCCESS:
                # If server returned arbitrary dictionary without top-level 'result' key
                result_payload = {
                    k: v
                    for k, v in raw_data.items()
                    if k not in ("status", "request_id", "error", "duration_ms")
                }

            return IPCResponse(
                request_id=raw_data.get("request_id", request.request_id),
                status=status,
                result=result_payload,
                error=raw_data.get("error"),
                duration_ms=duration,
            )

        except TimeoutError as exc:
            logger.error(
                "IPC command timed out after %s seconds", self._config.command_timeout_seconds
            )
            raise SocketTimeoutError(
                f"Command timed out after {self._config.command_timeout_seconds}s",
                details={"request_id": request.request_id},
            ) from exc

        except ConnectionRefusedError as exc:
            logger.warning(
                "Connection refused on %s:%s. Blender MCP bridge offline",
                self._config.host,
                self._config.port,
            )
            raise ChemLabConnRefused(
                f"Cannot connect to Blender MCP on {self._config.host}:{self._config.port}",
                details={"host": self._config.host, "port": self._config.port},
            ) from exc

        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("IPC Protocol serialization error: %s", exc)
            raise ProtocolSerializationError(
                f"Failed to decode or validate response: {exc}",
                details={"raw_buffer": buffer if "buffer" in locals() else None},
            ) from exc

        finally:
            raw_sock.close()

    def ping(self) -> bool:
        """Check if Blender MCP bridge is reachable."""
        try:
            req = IPCRequest(type=IPCRequestType.PING)
            res = self.send_request(req)
            return res.status in (IPCStatus.SUCCESS, IPCStatus.EXECUTED)
        except (ChemLabConnRefused, SocketTimeoutError):
            return False

    def close(self) -> None:
        """Client does not hold persistent connections (per-command connection pooling)."""
        pass
