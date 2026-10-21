"""Tests for the shared test helpers."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from threading import Event
from unittest import mock

import pytest

from tests.utils import HttpServerThread, http_server


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
    wait = server_thread.server.ready.wait

    def delayed_run() -> None:
        allow_start.wait(timeout=5)
        run()

    def wait_until_ready(timeout: float | None = None) -> bool:
        assert not server_thread.server.ready.is_set()
        allow_start.set()
        return wait(timeout)

    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        mock.patch.object(server_thread, 'run', side_effect=delayed_run),
        mock.patch.object(
            server_thread.server.ready, 'wait', side_effect=wait_until_ready
        ),
        http_server(BaseHTTPRequestHandler),
    ):
        try:
            assert server_thread.server.ready.is_set()
        finally:
            # Release the server even if the helper yielded without waiting.
            allow_start.set()

    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1


def test_http_server_readiness_timeout() -> None:
    server_thread = HttpServerThread(BaseHTTPRequestHandler)
    with (
        mock.patch('tests.utils.HttpServerThread', return_value=server_thread),
        mock.patch.object(server_thread.server.ready, 'wait', return_value=False),
        pytest.raises(
            TimeoutError,
            match='HTTP server did not enter its serving loop within 5 seconds',
        ),
        http_server(BaseHTTPRequestHandler),
    ):
        pytest.fail('HTTP server yielded before becoming ready')

    assert not server_thread.is_alive()
    assert server_thread.server.socket.fileno() == -1
