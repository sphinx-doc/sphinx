from __future__ import annotations

import contextlib
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

# File lock for tests
LOCK_PATH: Final[str] = str(TESTS_ROOT / 'test-server.lock')


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


_T_co = TypeVar('_T_co', bound=HttpServerThread, covariant=True)


def create_server(
    server_thread_class: type[_T_co],
) -> Callable[[type[BaseRequestHandler]], AbstractContextManager[_T_co]]:
    port_counter = AtomicInteger(7777)

    @contextlib.contextmanager
    def server(handler_class: type[BaseRequestHandler]) -> Generator[_T_co, None, None]:
        lock = filelock.FileLock(LOCK_PATH)
        with lock:
            port = port_counter.add_and_get(1)
            server_thread = server_thread_class(handler_class, port, daemon=True)
            server_thread.start()
            try:
                yield port
            finally:
                server_thread.terminate()
    return server


http_server = create_server(HttpServerThread)
https_server = create_server(HttpsServerThread)
