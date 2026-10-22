"""Tests for the shared test helpers."""

from __future__ import annotations

import socket
from contextlib import closing
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler
from queue import Queue
from ssl import SSLSocket, create_default_context
from threading import Event, current_thread
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from tests.utils import CERT_FILE, HttpServerThread, HttpsServerThread, http_server

if TYPE_CHECKING:
    from threading import Thread


@pytest.mark.parametrize('tls_enabled', [False, True])
def test_http_server_readiness_without_connection(tls_enabled: bool) -> None:
    with (
        mock.patch('socket.socket.connect') as connect,
        http_server(BaseHTTPRequestHandler, tls_enabled=tls_enabled) as server,
    ):
        connect.assert_not_called()

    assert server.socket.fileno() == -1


def test_http_server_waits_until_serving() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    allow_start = Event()
    run = server_thread.run
    wait = server_thread.ready.wait

    def delayed_run() -> None:
        allow_start.wait(timeout=5)
        run()

    def wait_until_ready(timeout: float | None = None) -> bool:
        assert not server_thread.ready.is_set()
        allow_start.set()
        return wait(timeout)

    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        mock.patch.object(server_thread, 'run', side_effect=delayed_run),
        mock.patch.object(server_thread.ready, 'wait', side_effect=wait_until_ready),
        http_server(BaseHTTPRequestHandler),
    ):
        try:
            assert server_thread.ready.is_set()
        finally:
            # Release the server even if the helper yielded without waiting.
            allow_start.set()

    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1


def test_http_server_timeout_before_serving() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        mock.patch.object(server_thread, 'run', return_value=None),
        mock.patch.object(server_thread.ready, 'wait', return_value=False),
        # Fail immediately if cleanup tries to shut down an unstarted serving loop.
        mock.patch.object(server_thread.server, 'shutdown', side_effect=AssertionError),
        pytest.raises(
            TimeoutError,
            match='HTTP server did not enter its serving loop within 5 seconds',
        ),
        http_server(BaseHTTPRequestHandler),
    ):
        pytest.fail('HTTP server yielded before becoming ready')

    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1


def test_http_server_timeout_cancels_delayed_start() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    allow_start = Event()
    run = server_thread.run
    join = server_thread.join

    def delayed_run() -> None:
        allow_start.wait(timeout=5)
        run()

    def join_after_releasing_start(timeout: float | None = None) -> None:
        allow_start.set()
        join(timeout)

    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        mock.patch.object(server_thread, 'run', side_effect=delayed_run),
        mock.patch.object(
            server_thread, 'join', side_effect=join_after_releasing_start
        ),
        mock.patch.object(server_thread.ready, 'wait', return_value=False),
        mock.patch.object(server_thread.server, 'handle_request') as handle_request,
    ):
        try:
            with (
                pytest.raises(
                    TimeoutError,
                    match='HTTP server did not enter its serving loop within 5 seconds',
                ),
                http_server(BaseHTTPRequestHandler),
            ):
                pytest.fail('HTTP server yielded before becoming ready')
        finally:
            allow_start.set()
            join(timeout=5)
            server_thread.server.server_close()

    handle_request.assert_not_called()
    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1


def test_http_server_start_failure_closes_socket() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    try:
        with (
            mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
            mock.patch.object(
                server_thread, 'start', side_effect=RuntimeError('cannot start thread')
            ),
            pytest.raises(RuntimeError, match='cannot start thread'),
            http_server(BaseHTTPRequestHandler),
        ):
            pytest.fail('HTTP server yielded after failing to start')

        assert server_thread.server.socket.fileno() == -1
    finally:
        server_thread.server.server_close()


def test_http_server_termination_timeout_closes_socket() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    with mock.patch.object(server_thread, 'run', return_value=None):
        server_thread.start()
        server_thread.join(timeout=5)

    with (
        mock.patch.object(server_thread, 'join') as join,
        mock.patch.object(server_thread, 'is_alive', return_value=True),
        pytest.raises(
            TimeoutError, match='HTTP server thread did not stop within 5 seconds'
        ),
    ):
        server_thread.terminate()

    join.assert_called_once_with(timeout=5)
    assert server_thread.server.socket.fileno() == -1


@pytest.mark.parametrize('method', ['load_cert_chain', 'wrap_socket'])
def test_https_server_setup_failure_closes_socket(method: str) -> None:
    server = HttpServerThread(BaseHTTPRequestHandler).server
    try:
        with (
            mock.patch('tests.utils._HTTPServer', return_value=server),
            mock.patch(
                f'tests.utils.SSLContext.{method}',
                side_effect=ValueError('TLS setup failed'),
            ),
            pytest.raises(ValueError, match='TLS setup failed'),
        ):
            HttpsServerThread(BaseHTTPRequestHandler)

        assert server.socket.fileno() == -1
    finally:
        server.server_close()


def test_http_server_closes_after_exception() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    msg = 'test failed'
    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        pytest.raises(ValueError, match='test failed'),
        http_server(BaseHTTPRequestHandler),
    ):
        raise ValueError(msg)

    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1


@pytest.mark.parametrize('tls_enabled', [False, True])
def test_http_server_connection_timeout(tls_enabled: bool) -> None:
    server_cls = HttpsServerThread if tls_enabled else HttpServerThread
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(None)
    try:
        server = server_cls(BaseHTTPRequestHandler).server
        try:
            with (
                socket.create_connection(('localhost', server.server_port), timeout=5),
                # Accepting a TLS connection must not wait for a handshake.
                mock.patch.object(
                    SSLSocket, 'do_handshake', side_effect=AssertionError
                ),
            ):
                connection, _ = server.get_request()
                with connection:
                    assert connection.gettimeout() == 5
        finally:
            server.server_close()
    finally:
        socket.setdefaulttimeout(previous_timeout)


def test_https_server_idle_client_does_not_block() -> None:
    workers: Queue[Thread] = Queue()

    class Handler(BaseHTTPRequestHandler):
        def handle(self) -> None:
            workers.put(current_thread())
            super().handle()

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.end_headers()

    server_thread = HttpsServerThread(Handler)
    with (
        mock.patch('tests.utils.HttpsServerThread', return_value=server_thread),
        http_server(Handler, tls_enabled=True) as server,
        socket.create_connection(('localhost', server.server_port), timeout=5),
    ):
        worker = workers.get(timeout=5)
        with closing(
            HTTPSConnection(
                'localhost',
                server.server_port,
                timeout=5,
                context=create_default_context(cafile=CERT_FILE),
            )
        ) as client:
            client.request('GET', '/')
            assert client.getresponse().status == 200

        # Stop while the first client is still connected without sending TLS data.
        server_thread.terminate()
        assert not server_thread.is_alive()
        assert server.socket.fileno() == -1

    worker.join(timeout=5)
    assert not worker.is_alive()
