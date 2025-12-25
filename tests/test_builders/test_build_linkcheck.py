"""Test the build process with manpage builder with the test root."""

from __future__ import annotations

import json
import re
import sys
import textwrap
import time
import wsgiref.handlers
from base64 import b64encode
from http.server import BaseHTTPRequestHandler
from io import StringIO
from queue import Queue
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from urllib3.poolmanager import PoolManager

import sphinx.util.http_date
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.builders.linkcheck import (
    CheckRequest,
    Hyperlink,
    HyperlinkAvailabilityCheckWorker,
    RateLimit,
    compile_linkcheck_allowed_redirects,
)
from sphinx.errors import ConfigError
from sphinx.testing.util import SphinxTestApp
from sphinx.util import requests
from sphinx.util._pathlib import _StrPath

from tests.utils import CERT_FILE, serve_application

ts_re = re.compile(r'.*\[(?P<ts>.*)\].*')

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path
    from typing import Any, Self

    from urllib3 import HTTPConnectionPool

    from sphinx.builders.linkcheck import (
        CheckResult,
    )
    from sphinx.testing.util import SphinxTestApp


class DefaultsHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_HEAD(self) -> None:
        if self.path[1:].rstrip() in {'', 'anchor.html'}:
            self.send_response(200, 'OK')
            self.send_header('Content-Length', '0')
            self.end_headers()
        else:
            self.send_response(404, 'Not Found')
            self.send_header('Content-Length', '0')
            self.end_headers()

    def do_GET(self) -> None:
        if self.path[1:].rstrip() == '':
            content = b'ok\n\n'
        elif self.path[1:].rstrip() == 'anchor.html':
            doc = '<!DOCTYPE html><html><body><a id="found"></a></body></html>'
            content = doc.encode('utf-8')
        else:
            content = b''

        if content:
            self.send_response(200, 'OK')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404, 'Not Found')
            self.send_header('Content-Length', '0')
            self.end_headers()


class ConnectionMeasurement:
    """Measure the number of distinct host connections created during linkchecking"""

    def __init__(self) -> None:
        self.connections: set[HTTPConnectionPool] = set()
        self.urllib3_connection_from_url = PoolManager.connection_from_url
        self.patcher = mock.patch.object(
            target=PoolManager,
            attribute='connection_from_url',
            new=self._collect_connections(),
        )

    def _collect_connections(self) -> Callable[[PoolManager, str], HTTPConnectionPool]:
        def connection_collector(obj: PoolManager, url: str) -> HTTPConnectionPool:
            connection = self.urllib3_connection_from_url(obj, url)  # type: ignore[no-untyped-call]
            self.connections.add(connection)
            return connection

        return connection_collector

    def __enter__(self) -> Self:
        self.patcher.start()
        return self

    def __exit__(self, *args: object, **kwargs: Any) -> None:
        for connection in self.connections:
            connection.close()
        self.patcher.stop()

    @property
    def connection_count(self) -> int:
        return len(self.connections)


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck',
    freshenv=True,
)
def test_defaults(app: SphinxTestApp) -> None:
    with serve_application(app, DefaultsHandler) as address:
        with ConnectionMeasurement() as m:
            app.build()
        assert m.connection_count <= 5

    # Text output
    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" in content
    assert "Anchor 'does-not-exist' not found" in content
    # images should fail
    assert f'Not Found for url: http://{address}/image.png' in content
    assert f'Not Found for url: http://{address}/image2.png' in content
    # looking for missing local file should fail
    assert '[broken] path/to/notfound' in content
    assert len(content.splitlines()) == 5

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    row = rows[0]
    for attr in ('filename', 'lineno', 'status', 'code', 'uri', 'info'):
        assert attr in row

    assert len(content.splitlines()) == 10
    assert len(rows) == 10
    # the output order of the rows is not stable
    # due to possible variance in network latency
    rowsby = {row['uri']: row for row in rows}
    # looking for local file that exists should succeed
    assert rowsby['conf.py']['status'] == 'working'
    assert rowsby[f'http://{address}#!bar'] == {
        'filename': 'links.rst',
        'lineno': 5,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}#!bar',
        'info': '',
    }

    def _missing_resource(filename: str, lineno: int) -> dict[str, str | int]:
        return {
            'filename': 'links.rst',
            'lineno': lineno,
            'status': 'broken',
            'code': 0,
            'uri': f'http://{address}/{filename}',
            'info': f'404 Client Error: Not Found for url: http://{address}/{filename}',
        }

    assert rowsby[f'http://{address}/image2.png'] == _missing_resource('image2.png', 12)
    # looking for '#top' and '#does-not-exist' not found should fail
    assert rowsby[f'http://{address}/#top']['info'] == "Anchor 'top' not found"
    assert rowsby[f'http://{address}/#top']['status'] == 'broken'
    assert (
        rowsby[f'http://{address}#does-not-exist']['info']
        == "Anchor 'does-not-exist' not found"
    )
    # images should fail
    assert (
        f'Not Found for url: http://{address}/image.png'
        in rowsby[f'http://{address}/image.png']['info']
    )
    # anchor should be found
    assert rowsby[f'http://{address}/anchor.html#found'] == {
        'filename': 'links.rst',
        'lineno': 14,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/anchor.html#found',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck',
    freshenv=True,
    confoverrides={'linkcheck_anchors': False},
)
def test_check_link_response_only(app: SphinxTestApp) -> None:
    with serve_application(app, DefaultsHandler) as address:
        app.build()

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    rowsby = {row['uri']: row for row in rows}
    assert rowsby[f'http://{address}/#top']['status'] == 'working'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-too-many-retries',
    freshenv=True,
)
def test_too_many_retries(app: SphinxTestApp) -> None:
    with serve_application(app, DefaultsHandler) as address:
        app.build()

    # Text output
    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # looking for non-existent URL should fail
    assert ' Max retries exceeded with url: /doesnotexist' in content

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    assert len(content.splitlines()) == 1
    row = json.loads(content)
    # the output order of the rows is not stable
    # due to possible variance in network latency

    # looking for non-existent URL should fail
    assert row['filename'] == 'index.rst'
    assert row['lineno'] == 1
    assert row['status'] == 'broken'
    assert row['code'] == 0
    assert row['uri'] == f'https://{address}/doesnotexist'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-raw-node',
    freshenv=True,
    copy_test_root=True,
)
def test_raw_node(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler) as address:
        # write an index file that contains a link back to this webserver's root
        # URL.  docutils will replace the raw node with the contents retrieved..
        # ..and then the linkchecker will check that the root URL is available.
        index = app.srcdir / 'index.rst'
        index.write_text(
            f".. raw:: 'html'\n   :url: http://{address}/",
            encoding='utf-8',
        )
        app.build()

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    assert len(content.splitlines()) == 1
    row = json.loads(content)

    # raw nodes' url should be checked too
    assert row == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/',  # the received rST contains a link to its' own URL
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-anchors-ignore',
    freshenv=True,
    confoverrides={'linkcheck_anchors_ignore': ['^!', '^top$']},
)
def test_anchors_ignored(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler):
        app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # expect all ok when excluding #top
    assert not content


class AnchorsIgnoreForUrlHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _chunk_content(self, content: str, *, max_chunk_size: int) -> Iterable[bytes]:
        def _encode_chunk(chunk: bytes) -> Iterable[bytes]:
            """Encode a bytestring into a format suitable for HTTP chunked-transfer.

            https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Transfer-Encoding
            """
            yield f'{len(chunk):X}'.encode('ascii')
            yield b'\r\n'
            yield chunk
            yield b'\r\n'

        buffer = b''
        for char in content:
            buffer += char.encode('utf-8')
            if len(buffer) >= max_chunk_size:
                chunk, buffer = buffer[:max_chunk_size], buffer[max_chunk_size:]
                yield from _encode_chunk(chunk)

        # Flush remaining bytes, if any
        if buffer:
            yield from _encode_chunk(buffer)

        # Emit a final empty chunk to close the stream
        yield from _encode_chunk(b'')

    def _send_chunked(self, content: str) -> bool:
        for chunk in self._chunk_content(content, max_chunk_size=20):
            try:
                self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError) as e:
                self.log_message(str(e))
                return False
        return True

    def do_HEAD(self) -> None:
        if self.path in {'/valid', '/ignored'}:
            self.send_response(200, 'OK')
        else:
            self.send_response(404, 'Not Found')
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == '/valid':
            self.send_response(200, 'OK')
            content = "<h1 id='valid-anchor'>valid anchor</h1>\n"
        elif self.path == '/ignored':
            self.send_response(200, 'OK')
            content = 'no anchor but page exists\n'
        else:
            self.send_response(404, 'Not Found')
            content = 'not found\n'
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        self._send_chunked(content)


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-anchors-ignore-for-url',
    freshenv=True,
)
def test_anchors_ignored_for_url(app: SphinxTestApp) -> None:
    with serve_application(app, AnchorsIgnoreForUrlHandler) as address:
        app.config.linkcheck_anchors_ignore_for_url = [
            f'http://{address}/ignored',  # existing page
            f'http://{address}/invalid',  # unknown page
        ]
        app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    attrs = ('filename', 'lineno', 'status', 'code', 'uri', 'info')
    data = [json.loads(x) for x in content.splitlines()]
    assert len(data) == 8
    assert all(all(attr in row for attr in attrs) for row in data)

    # rows may be unsorted due to network latency or
    # the order the threads are processing the links
    rows = {r['uri']: {'status': r['status'], 'info': r['info']} for r in data}

    assert rows[f'http://{address}/valid']['status'] == 'working'
    assert rows[f'http://{address}/valid#valid-anchor']['status'] == 'working'
    assert rows[f'http://{address}/valid#py:module::urllib.parse']['status'] == 'broken'
    assert rows[f'http://{address}/valid#invalid-anchor'] == {
        'status': 'broken',
        'info': "Anchor 'invalid-anchor' not found",
    }

    assert rows[f'http://{address}/ignored']['status'] == 'working'
    assert rows[f'http://{address}/ignored#invalid-anchor']['status'] == 'working'

    assert rows[f'http://{address}/invalid'] == {
        'status': 'broken',
        'info': f'404 Client Error: Not Found for url: http://{address}/invalid',
    }
    assert rows[f'http://{address}/invalid#anchor'] == {
        'status': 'broken',
        'info': f'404 Client Error: Not Found for url: http://{address}/invalid',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-anchor',
    freshenv=True,
)
def test_raises_for_invalid_status(app: SphinxTestApp) -> None:
    class InternalServerErrorHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_GET(self) -> None:
            self.send_error(500, 'Internal Server Error')

    with serve_application(app, InternalServerErrorHandler) as address:
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        f'index.rst:1: [broken] http://{address}/#anchor: '
        '500 Server Error: Internal Server Error '
        f'for url: http://{address}/\n'
    )


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-anchor',
    freshenv=True,
)
def test_incomplete_html_anchor(app: SphinxTestApp) -> None:
    class IncompleteHTMLDocumentHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_GET(self) -> None:
            content = b'this is <div id="anchor">not</div> a valid HTML document'
            self.send_response(200, 'OK')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    with serve_application(app, IncompleteHTMLDocumentHandler):
        app.build()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert len(content.splitlines()) == 1

    row = json.loads(content)
    assert row['status'] == 'working'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-anchor',
    freshenv=True,
)
def test_decoding_error_anchor_ignored(app: SphinxTestApp) -> None:
    class NonASCIIHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_GET(self) -> None:
            content = b'\x80\x00\x80\x00'  # non-ASCII byte-string
            self.send_response(200, 'OK')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    with serve_application(app, NonASCIIHandler):
        app.build()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert len(content.splitlines()) == 1

    row = json.loads(content)
    assert row['status'] == 'ignored'


def custom_handler(
    valid_credentials: tuple[str, str] | None = None,
    success_criteria: Callable[[BaseHTTPRequestHandler], bool] = lambda _: True,
) -> type[BaseHTTPRequestHandler]:
    """Returns an HTTP request handler that authenticates the client and then determines
    an appropriate HTTP response code, based on caller-provided credentials and optional
    success criteria, respectively.
    """
    expected_token = None
    if valid_credentials:
        assert len(valid_credentials) == 2, 'expected a pair of strings as credentials'
        expected_token = b64encode(':'.join(valid_credentials).encode()).decode('utf-8')
        del valid_credentials

    def authenticated(
        method: Callable[[CustomHandler], None],
    ) -> Callable[[CustomHandler], None]:
        def method_if_authenticated(self: CustomHandler) -> None:
            if expected_token is None:
                return method(self)
            elif not self.headers['Authorization']:
                self.send_response(401, 'Unauthorized')
                self.end_headers()
            elif self.headers['Authorization'] == f'Basic {expected_token}':
                return method(self)
            else:
                self.send_response(403, 'Forbidden')
                self.send_header('Content-Length', '0')
                self.end_headers()
            return None

        return method_if_authenticated

    class CustomHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        @authenticated
        def do_HEAD(self) -> None:
            self.do_GET()

        @authenticated
        def do_GET(self) -> None:
            if success_criteria(self):
                self.send_response(200, 'OK')
                self.send_header('Content-Length', '0')
            else:
                self.send_response(400, 'Bad Request')
                self.send_header('Content-Length', '0')
            self.end_headers()

    return CustomHandler


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_auth_header_uses_first_match(app: SphinxTestApp) -> None:
    with serve_application(
        app, custom_handler(valid_credentials=('user1', 'password'))
    ) as address:
        app.config.linkcheck_auth = [
            (r'^$', ('no', 'match')),
            (rf'^http://{re.escape(address)}/$', ('user1', 'password')),
            (r'.*local.*', ('user2', 'hunter2')),
        ]
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['status'] == 'working'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={'linkcheck_allow_unauthorized': False},
)
def test_unauthorized_broken(app: SphinxTestApp) -> None:
    with serve_application(
        app, custom_handler(valid_credentials=('user1', 'password'))
    ):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['info'] == 'unauthorized'
    assert content['status'] == 'broken'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={'linkcheck_auth': [(r'^$', ('user1', 'password'))]},
)
def test_auth_header_no_match(app: SphinxTestApp) -> None:
    with serve_application(
        app, custom_handler(valid_credentials=('user1', 'password'))
    ):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['info'] == 'unauthorized'
    assert content['status'] == 'broken'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_linkcheck_request_headers(app: SphinxTestApp) -> None:
    def check_headers(self: BaseHTTPRequestHandler) -> bool:
        if 'X-Secret' in self.headers:
            return False
        return self.headers['Accept'] == 'text/html'

    with serve_application(
        app, custom_handler(success_criteria=check_headers)
    ) as address:
        app.config.linkcheck_request_headers = {
            f'http://{address}/': {'Accept': 'text/html'},
            '*': {'X-Secret': 'open sesami'},
        }
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['status'] == 'working'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_linkcheck_request_headers_no_slash(app: SphinxTestApp) -> None:
    def check_headers(self: BaseHTTPRequestHandler) -> bool:
        if 'X-Secret' in self.headers:
            return False
        return self.headers['Accept'] == 'application/json'

    with serve_application(
        app, custom_handler(success_criteria=check_headers)
    ) as address:
        app.config.linkcheck_request_headers = {
            f'http://{address}': {'Accept': 'application/json'},
            '*': {'X-Secret': 'open sesami'},
        }
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['status'] == 'working'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={
        'linkcheck_request_headers': {
            'http://do.not.match.org': {'Accept': 'application/json'},
            '*': {'X-Secret': 'open sesami'},
        }
    },
)
def test_linkcheck_request_headers_default(app: SphinxTestApp) -> None:
    def check_headers(self: BaseHTTPRequestHandler) -> bool:
        if self.headers['X-Secret'] != 'open sesami':
            return False
        return self.headers['Accept'] != 'application/json'

    with serve_application(app, custom_handler(success_criteria=check_headers)):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['status'] == 'working'


def make_redirect_handler(*, support_head: bool = True) -> type[BaseHTTPRequestHandler]:
    class RedirectOnceHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_HEAD(self) -> None:
            if support_head:
                self.do_GET()
            else:
                self.send_response(405, 'Method Not Allowed')
                self.send_header('Content-Length', '0')
                self.end_headers()

        def do_GET(self) -> None:
            if self.path == '/?redirected=1':
                self.send_response(204, 'No content')
            else:
                self.send_response(302, 'Found')
                self.send_header('Location', '/?redirected=1')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def log_date_time_string(self) -> str:
            """Strip date and time from logged messages for assertions."""
            return ''

    return RedirectOnceHandler


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_follows_redirects_on_HEAD(
    app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    with serve_application(app, make_redirect_handler(support_head=True)) as address:
        compile_linkcheck_allowed_redirects(app, app.config)
        app.build()
    _stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        'index.rst:1: [redirected with Found] '
        f'http://{address}/ to http://{address}/?redirected=1\n'
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 302 -
        127.0.0.1 - - [] "HEAD /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert (
        f'redirect  http://{address}/ - with Found to http://{address}/?redirected=1\n'
    ) in strip_escape_sequences(app.status.getvalue())
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_follows_redirects_on_GET(
    app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    with serve_application(app, make_redirect_handler(support_head=False)) as address:
        compile_linkcheck_allowed_redirects(app, app.config)
        app.build()
    _stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        'index.rst:1: [redirected with Found] '
        f'http://{address}/ to http://{address}/?redirected=1\n'
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 405 -
        127.0.0.1 - - [] "GET / HTTP/1.1" 302 -
        127.0.0.1 - - [] "GET /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert (
        f'redirect  http://{address}/ - with Found to http://{address}/?redirected=1\n'
    ) in strip_escape_sequences(app.status.getvalue())
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={'linkcheck_allowed_redirects': {}},  # warn about any redirects
)
def test_warns_disallowed_redirects(
    app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    with serve_application(app, make_redirect_handler()) as address:
        compile_linkcheck_allowed_redirects(app, app.config)
        app.build()
    _stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        'index.rst:1: [redirected with Found] '
        f'http://{address}/ to http://{address}/?redirected=1\n'
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 302 -
        127.0.0.1 - - [] "HEAD /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert len(app.warning.getvalue().splitlines()) == 1


def test_linkcheck_allowed_redirects_config(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').touch()

    # ``linkcheck_allowed_redirects = None`` is rejected
    warning_stream = StringIO()
    with pytest.raises(ConfigError):
        make_app(
            'linkcheck',
            srcdir=tmp_path,
            confoverrides={'linkcheck_allowed_redirects': None},
            warning=warning_stream,
        )
    assert strip_escape_sequences(warning_stream.getvalue()).splitlines() == [
        "WARNING: The config value `linkcheck_allowed_redirects' has type `NoneType'; expected `dict'."
    ]

    # ``linkcheck_allowed_redirects = {}`` is permitted
    app = make_app(
        'linkcheck',
        srcdir=tmp_path,
        confoverrides={'linkcheck_allowed_redirects': {}},
    )
    assert strip_escape_sequences(app.warning.getvalue()) == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-warn-redirects')
def test_linkcheck_allowed_redirects(app: SphinxTestApp) -> None:
    with serve_application(app, make_redirect_handler(support_head=False)) as address:
        app.config.linkcheck_allowed_redirects = {f'http://{address}/.*1': '.*'}
        compile_linkcheck_allowed_redirects(app, app.config)
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        rows = [json.loads(l) for l in fp]

    assert len(rows) == 2
    records = {row['uri']: row for row in rows}
    assert records[f'http://{address}/path1']['status'] == 'working'
    assert records[f'http://{address}/path2'] == {
        'filename': 'index.rst',
        'lineno': 3,
        'status': 'redirected',
        'code': 302,
        'uri': f'http://{address}/path2',
        'info': f'http://{address}/?redirected=1',
    }

    assert (
        f'index.rst:3: WARNING: redirect  http://{address}/path2 - with Found to '
        f'http://{address}/?redirected=1\n'
    ) in strip_escape_sequences(app.warning.getvalue())
    assert len(app.warning.getvalue().splitlines()) == 1


class OKHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_HEAD(self) -> None:
        self.send_response(200, 'OK')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self) -> None:
        content = b'ok\n'
        self.send_response(200, 'OK')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@mock.patch('sphinx.builders.linkcheck.requests.get', wraps=requests.get)
@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
)
def test_invalid_ssl(get_request: mock.Mock, app: SphinxTestApp) -> None:
    # Link indicates SSL should be used (https) but the server does not handle it.
    with serve_application(app, OKHandler) as address:
        app.build()
        assert not get_request.called

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content['status'] == 'broken'
    assert content['filename'] == 'index.rst'
    assert content['lineno'] == 1
    assert content['uri'] == f'https://{address}/'
    assert 'SSLError' in content['info']


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
)
def test_connect_to_selfsigned_fails(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler, tls_enabled=True) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content['status'] == 'broken'
    assert content['filename'] == 'index.rst'
    assert content['lineno'] == 1
    assert content['uri'] == f'https://{address}/'
    assert '[SSL: CERTIFICATE_VERIFY_FAILED]' in content['info']


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
    confoverrides={'tls_verify': False},
)
def test_connect_to_selfsigned_with_tls_verify_false(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler, tls_enabled=True) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 0,
        'status': 'working',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'https://{address}/',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
    confoverrides={'tls_cacerts': CERT_FILE},
)
def test_connect_to_selfsigned_with_tls_cacerts(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler, tls_enabled=True) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 0,
        'status': 'working',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'https://{address}/',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
)
def test_connect_to_selfsigned_with_requests_env_var(
    monkeypatch: pytest.MonkeyPatch, app: SphinxTestApp
) -> None:
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', CERT_FILE)
    with serve_application(app, OKHandler, tls_enabled=True) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 0,
        'status': 'working',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'https://{address}/',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver-https',
    freshenv=True,
    confoverrides={'tls_cacerts': 'does/not/exist'},
)
def test_connect_to_selfsigned_nonexistent_cert_file(app: SphinxTestApp) -> None:
    with serve_application(app, OKHandler, tls_enabled=True) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 0,
        'status': 'broken',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'https://{address}/',
        'info': 'Could not find a suitable TLS CA certificate bundle, invalid path: does/not/exist',
    }


class InfiniteRedirectOnHeadHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_HEAD(self) -> None:
        self.send_response(302, 'Found')
        self.send_header('Location', '/redirected')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self) -> None:
        content = b'ok\n'
        self.send_response(200, 'OK')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)
        self.close_connection = (
            True  # we don't expect the client to read this response body
        )


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_TooManyRedirects_on_HEAD(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    import requests.sessions

    monkeypatch.setattr(requests.sessions, 'DEFAULT_REDIRECT_LIMIT', 5)

    with serve_application(app, InfiniteRedirectOnHeadHandler) as address:
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 0,
        'status': 'working',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'http://{address}/',
        'info': '',
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver')
def test_ignore_local_redirection(app: SphinxTestApp) -> None:
    with serve_application(app, InfiniteRedirectOnHeadHandler) as address:
        app.config.linkcheck_ignore = [f'http://{address}/redirected']
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 302,
        'status': 'ignored',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'http://{address}/',
        'info': f'ignored redirect: http://{address}/redirected',
    }


class RemoteDomainRedirectHandler(InfiniteRedirectOnHeadHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self) -> None:
        self.send_response(301, 'Found')
        if self.path == '/':
            self.send_header('Location', '/local')
        elif self.path == '/local':
            self.send_header('Location', 'http://example.test/migrated')
        self.send_header('Content-Length', '0')
        self.end_headers()


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver')
def test_ignore_remote_redirection(app: SphinxTestApp) -> None:
    with serve_application(app, RemoteDomainRedirectHandler) as address:
        app.config.linkcheck_ignore = ['http://example.test']
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        'code': 301,
        'status': 'ignored',
        'filename': 'index.rst',
        'lineno': 1,
        'uri': f'http://{address}/',
        'info': 'ignored redirect: http://example.test/migrated',
    }


def make_retry_after_handler(
    responses: list[tuple[int, str | None]],
) -> type[BaseHTTPRequestHandler]:
    class RetryAfterHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_HEAD(self) -> None:
            status, retry_after = responses.pop(0)
            self.send_response(status)
            if retry_after:
                self.send_header('Retry-After', retry_after)
            self.send_header('Content-Length', '0')
            self.end_headers()

        def log_date_time_string(self) -> str:
            """Strip date and time from logged messages for assertions."""
            return ''

    return RetryAfterHandler


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_too_many_requests_retry_after_int_delay(
    app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    with (
        serve_application(
            app, make_retry_after_handler([(429, '0'), (200, None)])
        ) as address,
        mock.patch('sphinx.builders.linkcheck.DEFAULT_DELAY', 0),
        mock.patch('sphinx.builders.linkcheck.QUEUE_POLL_SECS', 0.01),
    ):
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/',
        'info': '',
    }
    rate_limit_log = f'-rate limited-   http://{address}/ | sleeping...\n'
    assert rate_limit_log in strip_escape_sequences(app.status.getvalue())
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.parametrize('tz', [None, 'GMT', 'GMT+3', 'GMT-3'])
@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_too_many_requests_retry_after_HTTP_date(
    tz: str | None,
    app: SphinxTestApp,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    retry_after = wsgiref.handlers.format_date_time(time.time())

    with monkeypatch.context() as m:
        if tz is not None:
            m.setenv('TZ', tz)
            if sys.platform != 'win32':
                time.tzset()
            m.setattr(
                sphinx.util.http_date, '_GMT_OFFSET', float(time.localtime().tm_gmtoff)
            )

        with serve_application(
            app, make_retry_after_handler([(429, retry_after), (200, None)])
        ) as address:
            app.build()

    # Undo side-effects: the monkeypatch context manager clears the TZ environment
    # variable, but we also need to reset Python's internal notion of the current
    # timezone.
    if sys.platform != 'win32':
        time.tzset()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/',
        'info': '',
    }
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_too_many_requests_retry_after_without_header(
    app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    with (
        serve_application(
            app, make_retry_after_handler([(429, None), (200, None)])
        ) as address,
        mock.patch('sphinx.builders.linkcheck.DEFAULT_DELAY', 0),
    ):
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/',
        'info': '',
    }
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={
        'linkcheck_report_timeouts_as_broken': False,
        'linkcheck_timeout': 0.01,
    },
)
def test_requests_timeout(app: SphinxTestApp) -> None:
    class DelayedResponseHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def do_GET(self) -> None:
            time.sleep(0.2)  # wait before sending any response data
            self.send_response(200, 'OK')
            self.send_header('Content-Length', '0')
            self.end_headers()

    with serve_application(app, DelayedResponseHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)

    assert content['status'] == 'timeout'


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
    confoverrides={'linkcheck_rate_limit_timeout': 0.0},
)
def test_too_many_requests_user_timeout(app: SphinxTestApp) -> None:
    with serve_application(app, make_retry_after_handler([(429, None)])) as address:
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'broken',
        'code': 0,
        'uri': f'http://{address}/',
        'info': f'429 Client Error: Too Many Requests for url: http://{address}/',
    }


class FakeResponse:
    headers: dict[str, str] = {}
    url = 'http://localhost/'


@pytest.mark.sphinx('html', testroot='root')
def test_limit_rate_default_sleep(app: SphinxTestApp) -> None:
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), {})
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(
            FakeResponse.url, FakeResponse.headers.get('Retry-After')
        )
    assert next_check == 60.0


@pytest.mark.sphinx(
    'html', testroot='root', confoverrides={'linkcheck_rate_limit_timeout': 0.0}
)
def test_limit_rate_user_max_delay(app: SphinxTestApp) -> None:
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), {})
    next_check = worker.limit_rate(
        FakeResponse.url, FakeResponse.headers.get('Retry-After')
    )
    assert next_check is None


@pytest.mark.sphinx('html', testroot='root')
def test_limit_rate_doubles_previous_wait_time(app: SphinxTestApp) -> None:
    rate_limits = {'localhost': RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(
            FakeResponse.url, FakeResponse.headers.get('Retry-After')
        )
    assert next_check == 120.0


@pytest.mark.sphinx(
    'html', testroot='root', confoverrides={'linkcheck_rate_limit_timeout': 90}
)
def test_limit_rate_clips_wait_time_to_max_time(app: SphinxTestApp) -> None:
    rate_limits = {'localhost': RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(
            FakeResponse.url, FakeResponse.headers.get('Retry-After')
        )
    assert next_check == 90.0
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx(
    'html', testroot='root', confoverrides={'linkcheck_rate_limit_timeout': 90.0}
)
def test_limit_rate_bails_out_after_waiting_max_time(app: SphinxTestApp) -> None:
    rate_limits = {'localhost': RateLimit(90.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    next_check = worker.limit_rate(
        FakeResponse.url, FakeResponse.headers.get('Retry-After')
    )
    assert next_check is None
    assert app.warning.getvalue() == ''


@mock.patch('sphinx.util.requests.requests.Session.get_adapter')
@pytest.mark.sphinx('html', testroot='root')
def test_connection_contention(
    get_adapter: mock.Mock, app: SphinxTestApp, capsys: pytest.CaptureFixture[str]
) -> None:
    # Create a shared, but limited-size, connection pool
    import requests

    get_adapter.return_value = requests.adapters.HTTPAdapter(pool_maxsize=1)

    # Set an upper-bound on socket timeouts globally
    import socket

    socket.setdefaulttimeout(5)

    # Create parallel consumer threads
    with serve_application(app, make_redirect_handler(support_head=True)) as address:
        # Place a workload into the linkcheck queue
        link_count = 10
        wqueue: Queue[CheckRequest] = Queue()
        rqueue: Queue[CheckResult] = Queue()
        for _ in range(link_count):
            wqueue.put(
                CheckRequest(
                    0, Hyperlink(f'http://{address}', 'test', _StrPath('test.rst'), 1)
                )
            )

        begin = time.time()
        checked: list[CheckResult] = []
        threads = [
            HyperlinkAvailabilityCheckWorker(
                config=app.config,
                rqueue=rqueue,
                wqueue=wqueue,
                rate_limits={},
            )
            for _ in range(10)
        ]
        for thread in threads:
            thread.start()
        while time.time() < begin + 5 and len(checked) < link_count:
            checked.append(rqueue.get(timeout=5))
        for thread in threads:
            thread.join(timeout=0)

    # Ensure that all items were consumed within the time limit
    _, stderr = capsys.readouterr()
    assert len(checked) == link_count
    assert 'TimeoutError' not in stderr


class ConnectionResetHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_HEAD(self) -> None:
        self.close_connection = True

    def do_GET(self) -> None:
        self.send_response(200, 'OK')
        self.send_header('Content-Length', '0')
        self.end_headers()


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-localserver',
    freshenv=True,
)
def test_get_after_head_raises_connection_error(app: SphinxTestApp) -> None:
    with serve_application(app, ConnectionResetHandler) as address:
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert not content
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        'filename': 'index.rst',
        'lineno': 1,
        'status': 'working',
        'code': 0,
        'uri': f'http://{address}/',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-documents_exclude',
    freshenv=True,
)
def test_linkcheck_exclude_documents(app: SphinxTestApp) -> None:
    with serve_application(app, DefaultsHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = [json.loads(record) for record in fp]

    assert len(content) == 2
    assert {
        'filename': 'broken_link.rst',
        'lineno': 4,
        'status': 'ignored',
        'code': 0,
        'uri': 'https://www.sphinx-doc.org/this-is-a-broken-link',
        'info': 'broken_link matched ^broken_link$ from linkcheck_exclude_documents',
    } in content
    assert {
        'filename': 'br0ken_link.rst',
        'lineno': 4,
        'status': 'ignored',
        'code': 0,
        'uri': 'https://www.sphinx-doc.org/this-is-another-broken-link',
        'info': 'br0ken_link matched br[0-9]ken_link from linkcheck_exclude_documents',
    } in content


class CapitalisePathHandler(BaseHTTPRequestHandler):
    """Test server that uppercases URL paths via redirects."""

    protocol_version = 'HTTP/1.1'

    def do_GET(self) -> None:
        if self.path.islower():
            # Redirect lowercase paths to uppercase versions
            self.send_response(301, 'Moved Permanently')
            self.send_header('Location', self.path.upper())
            self.send_header('Content-Length', '0')
            self.end_headers()
        else:
            # Serve uppercase paths
            content = b'ok\n\n'
            self.send_response(200, 'OK')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-case-check',
    freshenv=True,
)
@pytest.mark.parametrize(
    ('case_insensitive_pattern', 'expected_path1', 'expected_path2', 'expected_path3'),
    [
        ([], 'redirected', 'redirected', 'working'),  # default: case-sensitive
        (
            [r'http://localhost:\d+/.*'],
            'working',
            'working',
            'working',
        ),  # all URLs case-insensitive
        (
            [r'http://localhost:\d+/path1'],
            'working',
            'redirected',
            'working',
        ),  # only path1 case-insensitive
    ],
)
def test_linkcheck_case_sensitivity(
    app: SphinxTestApp,
    case_insensitive_pattern: list[str],
    expected_path1: str,
    expected_path2: str,
    expected_path3: str,
) -> None:
    """Test case-sensitive and case-insensitive URL checking."""
    app.config.linkcheck_case_insensitive_urls = case_insensitive_pattern

    with serve_application(app, CapitalisePathHandler) as address:
        app.build()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    rows = [json.loads(x) for x in content.splitlines()]
    rowsby = {row['uri']: row for row in rows}

    # Verify expected status for each path
    assert rowsby[f'http://{address}/path1']['status'] == expected_path1
    assert rowsby[f'http://{address}/path2']['status'] == expected_path2
    assert rowsby[f'http://{address}/PATH3']['status'] == expected_path3
