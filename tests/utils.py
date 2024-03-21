from __future__ import annotations

__all__ = ('http_server',)

import socket
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from threading import Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from socketserver import BaseRequestHandler
    from typing import Final

# Generated with:
# $ openssl req -new -x509 -days 3650 -nodes -out cert.pem \
#     -keyout cert.pem -addext "subjectAltName = DNS:localhost"
TESTS_ROOT: Final[Path] = Path(__file__).parent
CERT_FILE: Final[str] = str(TESTS_ROOT / 'certs' / 'cert.pem')


class HttpServerThread(Thread):
    def __init__(self, handler: type[BaseRequestHandler]) -> None:
        super().__init__(daemon=True)
        self.server = ThreadingHTTPServer(("localhost", 0), handler)

    def run(self) -> None:
        self.server.serve_forever(poll_interval=0.001)

    def terminate(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.join()


class HttpsServerThread(HttpServerThread):
    def __init__(self, handler: type[BaseRequestHandler]) -> None:
        super().__init__(handler)
        sslcontext = SSLContext(PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain(CERT_FILE)
        self.server.socket = sslcontext.wrap_socket(self.server.socket, server_side=True)


@contextmanager
def http_server(handler: type[BaseRequestHandler], *, tls_enabled: bool = False) -> Iterator[int]:
    server_cls = HttpsServerThread if tls_enabled else HttpServerThread
    server_thread = server_cls(handler)
    server_thread.start()
    port = server_thread.server.server_port
    try:
        socket.create_connection(("localhost", port), timeout=0.5).close()
        yield port  # Connection has been confirmed possible; proceed.
    finally:
        server_thread.terminate()
