from __future__ import annotations

__all__ = (
    'http_server',
    'extract_node',
    'extract_element',
)

import os
import socket
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from threading import Thread
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from docutils import nodes

if TYPE_CHECKING:
    from collections.abc import Iterator
    from http.server import HTTPServer
    from socketserver import BaseRequestHandler
    from typing import Final

    from docutils.nodes import Element, Node

    from sphinx.application import Sphinx

TESTS_ROOT: Final[Path] = Path(__file__).resolve().parent
TEST_ROOTS_DIR: Final[Path] = TESTS_ROOT / (
    'roots-read-only'
    if 'CI' in os.environ and (TESTS_ROOT / 'roots-read-only').is_dir()
    else 'roots'
)

# Generated with:
# $ openssl req -new -x509 -days 3650 -nodes -out cert.pem \
#     -keyout cert.pem -addext "subjectAltName = DNS:localhost"
CERT_FILE: Final[str] = str(TESTS_ROOT / 'certs' / 'cert.pem')


class HttpServerThread(Thread):
    def __init__(self, handler: type[BaseRequestHandler], *, port: int = 0) -> None:
        """Constructs a threaded HTTP server.

        The default port number of ``0`` delegates selection of a port number
        to bind to Python.
        See: https://docs.python.org/3/library/socketserver.html#asynchronous-mixins
        """
        super().__init__(daemon=True)
        self.server = ThreadingHTTPServer(('localhost', port), handler)

    def run(self) -> None:
        self.server.serve_forever(poll_interval=0.001)

    def terminate(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.join()


class HttpsServerThread(HttpServerThread):
    def __init__(self, handler: type[BaseRequestHandler], *, port: int = 0) -> None:
        super().__init__(handler, port=port)
        sslcontext = SSLContext(PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain(CERT_FILE)
        self.server.socket = sslcontext.wrap_socket(
            self.server.socket, server_side=True
        )


@contextmanager
def http_server(
    handler: type[BaseRequestHandler],
    *,
    tls_enabled: bool = False,
    port: int = 0,
) -> Iterator[HTTPServer]:
    server_cls = HttpsServerThread if tls_enabled else HttpServerThread
    server_thread = server_cls(handler, port=port)
    server_thread.start()
    server_port = server_thread.server.server_port
    assert port in {0, server_port}
    try:
        socket.create_connection(('localhost', server_port), timeout=0.5).close()
        yield server_thread.server  # Connection has been confirmed possible; proceed.
    finally:
        server_thread.terminate()


@contextmanager
def rewrite_hyperlinks(app: Sphinx, server: HTTPServer) -> Iterator[None]:
    """Rewrite hyperlinks that refer to network location 'localhost:7777',
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
    port: int = 0,
) -> Iterator[str]:
    """Prepare a temporary server to handle HTTP requests related to the links
    found in a Sphinx application project.

    :param app: The Sphinx application.
    :param handler: Determines how each request will be handled.
    :param tls_enabled: Whether TLS (SSL) should be enabled for the server.
    :param port: Optional server port (default: auto).

    :return: The address of the temporary HTTP server.
    """
    with (
        http_server(handler, tls_enabled=tls_enabled, port=port) as server,
        rewrite_hyperlinks(app, server),
    ):
        yield f'localhost:{server.server_port}'


def extract_node(node: Node, /, *indices: int) -> Node:
    """Walk down a docutils node tree by repeatedly indexing children.

    Returns a Node (could be Element, Text, etc.)

    Example::

        extract_node(doc, 0, 2, 1) == doc[0][2][1]
    """
    current: Node = node

    for depth, i in enumerate(indices):
        path = ''.join(f'[{i}]' for i in indices[:depth])
        assert isinstance(current, nodes.Element), (
            f'Expected node{path} (at depth {depth}) to be an Element '
            f'before indexing with [{i}], got {type(current).__name__!r}'
        )
        try:
            current = current[i]
        except IndexError as exc:
            msg = (
                f'Index {i} out of range for node{path} (at depth {depth}) '
                f'for {type(current).__name__!r}'
            )
            raise AssertionError(msg) from exc

    return current


def extract_element(node: Node, /, *indices: int) -> Element:
    """Walk down a docutils node tree and return an Element.

    Asserts the final result is an Element (for attribute/dict access).

    Example::

        node = extract_node(doc, 0, 2, 1)
        node['uri']  # Safe: guaranteed to be docutils.nodes.Element
    """
    result = extract_node(node, *indices)
    if isinstance(result, nodes.Element):
        return result
    path = ''.join(f'[{i}]' for i in indices)
    msg = f'Expected node{path} to be an Element, got {type(result).__name__!r}'
    raise AssertionError(msg)
