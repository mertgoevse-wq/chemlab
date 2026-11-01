"""
Decoupled IPC Server and Mock Test Harness.
Features deterministic shutdown semantics via threading.Event to prevent zombie threads.
"""

import contextlib
import json
import logging
import socket
import threading
from collections.abc import Callable
from types import TracebackType

from chemlab_core.config import IPCConfig
from chemlab_core.exceptions import IPCTransportError
from chemlab_core.models import (
    IPCRequest,
    IPCResponse,
    IPCStatus,
)
from chemlab_core.transport.contracts import IPCServer

logger = logging.getLogger(__name__)

RequestHandler = Callable[[IPCRequest], IPCResponse]


def default_mock_handler(req: IPCRequest) -> IPCResponse:
    """Default mock request handler for automated CI testing."""
    return IPCResponse(
        request_id=req.request_id,
        status=IPCStatus.SUCCESS,
        result={"mock_echo": req.type.value, "params": req.params},
        duration_ms=1.2,
    )


class ThreadedIPCServer(IPCServer):
    """Threaded IPC Socket Server with explicit lifecycle and zero zombie threads."""

    def __init__(
        self,
        config: IPCConfig | None = None,
        handler: RequestHandler | None = None,
    ) -> None:
        self._config = config or IPCConfig()
        self._handler = handler or default_mock_handler
        self._shutdown_event = threading.Event()
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def __enter__(self) -> "ThreadedIPCServer":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()

    @property
    def is_running(self) -> bool:
        """Check if server accept loop is running."""
        return not self._shutdown_event.is_set() and self._server_socket is not None

    def start(self) -> None:
        """Bind socket and start background listening thread with clean shutdown coordination."""
        with self._lock:
            if self.is_running:
                logger.warning("IPC Server is already running")
                return

            self._shutdown_event.clear()

            try:
                self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._server_socket.bind((self._config.host, self._config.port))
                self._server_socket.listen(5)
                # 0.5s timeout on accept allows clean checking of shutdown_event
                self._server_socket.settimeout(0.5)

                self._thread = threading.Thread(
                    target=self._accept_loop,
                    name="ChemLab-IPC-ServerThread",
                    daemon=True,
                )
                self._thread.start()
                logger.info("IPC Server listening on %s:%s", self._config.host, self._config.port)

            except OSError as exc:
                if self._server_socket:
                    self._server_socket.close()
                    self._server_socket = None
                raise IPCTransportError(
                    f"Failed to bind socket on {self._config.host}:{self._config.port}: {exc}",
                    details={"host": self._config.host, "port": self._config.port},
                ) from exc

    def _accept_loop(self) -> None:
        """Main listening loop polling for connections until shutdown_event is set."""
        while not self._shutdown_event.is_set():
            if not self._server_socket:
                break
            try:
                client_sock, client_addr = self._server_socket.accept()
                logger.debug("Client connected from %s", client_addr)
                self._handle_client(client_sock)
            except TimeoutError:
                continue
            except OSError:
                # Socket was closed during shutdown
                break

    def _handle_client(self, client_sock: socket.socket) -> None:
        """Process incoming client message, invoke handler, and return JSON."""
        buffer = ""
        client_sock.settimeout(self._config.command_timeout_seconds)
        try:
            while not self._shutdown_event.is_set():
                chunk = client_sock.recv(self._config.buffer_size)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                if "\n" in buffer:
                    raw_line = buffer.strip().split("\n")[0]
                    parsed_json = json.loads(raw_line)
                    request = IPCRequest.model_validate(parsed_json)
                    response = self._handler(request)
                    client_sock.sendall((response.model_dump_json() + "\n").encode("utf-8"))
                    break
        except Exception as exc:
            logger.error("Error servicing client connection: %s", exc)
            err_resp = IPCResponse(
                status=IPCStatus.ERROR,
                error=str(exc),
                duration_ms=0.0,
            )
            with contextlib.suppress(OSError):
                client_sock.sendall((err_resp.model_dump_json() + "\n").encode("utf-8"))
        finally:
            client_sock.close()

    def stop(self) -> None:
        """Coordinately shutdown the accept thread and close sockets."""
        with self._lock:
            self._shutdown_event.set()
            if self._server_socket:
                try:
                    self._server_socket.close()
                except OSError as exc:
                    logger.debug("Ignored socket close error during shutdown: %s", exc)
                self._server_socket = None

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
                self._thread = None
            logger.info("IPC Server cleanly stopped")
