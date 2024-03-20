from __future__ import annotations

import contextlib
import socket
from http.server import ThreadingHTTPServer
from pathlib import Path
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from threading import Thread
from typing import TYPE_CHECKING, TypeVar

import filelock
from atomos.atomic import AtomicInteger

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from contextlib import AbstractContextManager
    from socketserver import BaseRequestHandler
    from typing import Any, Final

# Generated with:
# $ openssl req -new -x509 -days 3650 -nodes -out cert.pem \
#     -keyout cert.pem -addext "subjectAltName = DNS:localhost"
TESTS_ROOT: Final[Path] = Path(__file__).parent
CERT_FILE: Final[str] = str(TESTS_ROOT / "certs" / "cert.pem")

# File locks for tests
LOCKS_ROOT: Final[Path] = TESTS_ROOT / "locks"


class HttpServerThread(Thread):
    def __init__(self, handler: type[BaseRequestHandler], port: int, /, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.server = ThreadingHTTPServer(("localhost", port), handler)

    def run(self) -> None:
        self.server.serve_forever(poll_interval=0.001)

    def terminate(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.join()


class HttpsServerThread(HttpServerThread):
    def __init__(
        self, handler: type[BaseRequestHandler], port: int, /, *args: Any, **kwargs: Any,
    ) -> None:
        super().__init__(handler, port, *args, **kwargs)
        sslcontext = SSLContext(PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain(CERT_FILE)
        self.server.socket = sslcontext.wrap_socket(self.server.socket, server_side=True)


def _n_to_port(n: int) -> int:
    """Provided with an integer 7..64, returns a port number 7777 to 64444"""
    prefix: str = str(n)
    last_digit: str = prefix[-1]
    port: str = prefix + (last_digit * 3)
    return int(port)


_T_co = TypeVar('_T_co', bound=HttpServerThread, covariant=True)


def create_server(
    server_thread_class: type[_T_co],
) -> Callable[[type[BaseRequestHandler]], AbstractContextManager[_T_co]]:
    counter = AtomicInteger(7)  # start from port 7777

    @contextlib.contextmanager
    def server(handler_class: type[BaseRequestHandler]) -> Generator[_T_co, None, None]:
        port = _n_to_port(counter.add_and_get(1))
        lock = filelock.FileLock(LOCKS_ROOT / f"test-server.{port}.lock")
        with lock:
            server_thread = server_thread_class(handler_class, port, daemon=True)
            server_thread.start()
            try:
                socket.create_connection(("localhost", port), timeout=0.5).close()  # Attempt connection.
                yield port  # Connection has been confirmed possible; proceed.
            finally:
                server_thread.terminate()
    return server


http_server = create_server(HttpServerThread)
https_server = create_server(HttpsServerThread)
