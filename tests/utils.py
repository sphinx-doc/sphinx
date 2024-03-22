from __future__ import annotations

__all__ = ('http_server',)

import socket
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from threading import Thread
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from http.server import HTTPServer
    from socketserver import BaseRequestHandler
    from typing import Final

    from sphinx.application import Sphinx

# Generated with:
# $ openssl req -new -x509 -days 3650 -nodes -out cert.pem \
#     -keyout cert.pem -addext "subjectAltName = DNS:localhost"
TESTS_ROOT: Final[Path] = Path(__file__).parent
CERT_FILE: Final[str] = str(TESTS_ROOT / 'certs' / 'cert.pem')


class HttpServerThread(Thread):
    def __init__(self, handler: type[BaseRequestHandler]) -> None:
        """
        Constructs a threaded HTTP server that will bind to an arbitrary unused
        port when it runs.

        The selection of port ``0`` delegates the selection of port to Python.

        Ref: https://docs.python.org/3.11/library/socketserver.html#asynchronous-mixins
        """
        super().__init__(daemon=True)
        self.server = ThreadingHTTPServer(('localhost', 0), handler)

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
def http_server(
    handler: type[BaseRequestHandler], *, tls_enabled: bool = False
) -> Iterator[HTTPServer]:
    server_cls = HttpsServerThread if tls_enabled else HttpServerThread
    server_thread = server_cls(handler)
    server_thread.start()
    port = server_thread.server.server_port
    try:
        socket.create_connection(('localhost', port), timeout=0.5).close()
        yield server_thread.server  # Connection has been confirmed possible; proceed.
    finally:
        server_thread.terminate()


@contextmanager
def rewrite_hyperlinks(app: Sphinx, server: HTTPServer) -> Generator[None, None, None]:
    """
    Rewrite hyperlinks that refer to network location 'localhost:7777',
    allowing that location to vary dynamically with the arbitrary test HTTP
    server port assigned during unit testing.

    :param app: The Sphinx application where link replacement is to occur.
    :param server: Destination server to redirect the hyperlinks to.
    """
    match_netloc, replacement_netloc = (
        'localhost:7777',
        f'localhost:{server.server_port}',
    )

    def rewrite_hyperlink(_app: Sphinx, uri: str) -> str | None:
        parsed_uri = urlparse(uri)
        if parsed_uri.netloc != match_netloc:
            return uri
        return parsed_uri._replace(netloc=replacement_netloc).geturl()

    listener_id = app.connect('linkcheck-process-uri', rewrite_hyperlink)
    yield
    app.disconnect(listener_id)


@contextmanager
def serve_application(
    app: Sphinx,
    handler: type[BaseRequestHandler],
    *,
    tls_enabled: bool = False,
) -> Iterator[str]:
    """
    Prepare a temporary server to handle HTTP requests related to the links
    found in a Sphinx application project.

    :param app: The Sphinx application.
    :param handler: Determines how each request will be handled.
    :param tls_enabled: Whether TLS (SSL) should be enabled for the server.

    :return: The address of the temporary HTTP server.
    """
    with (
        http_server(handler, tls_enabled=tls_enabled) as server,
        rewrite_hyperlinks(app, server),
    ):
        yield f'localhost:{server.server_port}'
