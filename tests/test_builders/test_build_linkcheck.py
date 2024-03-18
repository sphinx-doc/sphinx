"""Test the build process with manpage builder with the test root."""

from __future__ import annotations

from contextlib import contextmanager
import http.server
import json
import re
import sys
import textwrap
import time
import wsgiref.handlers
from base64 import b64encode
from queue import Queue
from unittest import mock

import docutils
import pytest
from urllib3.poolmanager import PoolManager

import sphinx.util.http_date
from sphinx.builders.linkcheck import (
    CheckRequest,
    Hyperlink,
    HyperlinkAvailabilityCheckWorker,
    RateLimit,
    compile_linkcheck_allowed_redirects,
)
from sphinx.deprecation import RemovedInSphinx80Warning
from sphinx.testing.util import strip_escseq
from sphinx.util import requests

from tests.utils import CERT_FILE, http_server, https_server

ts_re = re.compile(r".*\[(?P<ts>.*)\].*")


@contextmanager
def overwrite_file(path, content):
    current_content = path.read_bytes() if path.exists() else None
    try:
        path.write_text(content, encoding='utf-8')
        yield
    finally:
        if current_content is not None:
            path.write_bytes(current_content)
        else:
            path.unlink()


class DefaultsHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        if self.path[1:].rstrip() in {"", "anchor.html"}:
            self.send_response(200, "OK")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404, "Not Found")
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_GET(self):
        if self.path[1:].rstrip() == "":
            content = b"ok\n\n"
        elif self.path[1:].rstrip() == "anchor.html":
            doc = '<!DOCTYPE html><html><body><a id="found"></a></body></html>'
            content = doc.encode("utf-8")
        else:
            content = b""

        if content:
            self.send_response(200, "OK")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404, "Not Found")
            self.send_header("Content-Length", "0")
            self.end_headers()


class ConnectionMeasurement:
    """Measure the number of distinct host connections created during linkchecking"""

    def __init__(self):
        self.connections = set()
        self.urllib3_connection_from_url = PoolManager.connection_from_url
        self.patcher = mock.patch.object(
            target=PoolManager,
            attribute='connection_from_url',
            new=self._collect_connections(),
        )

    def _collect_connections(self):
        def connection_collector(obj, url):
            connection = self.urllib3_connection_from_url(obj, url)
            self.connections.add(connection)
            return connection
        return connection_collector

    def __enter__(self):
        self.patcher.start()
        return self

    def __exit__(self, *args, **kwargs):
        for connection in self.connections:
            connection.close()
        self.patcher.stop()

    @property
    def connection_count(self):
        return len(self.connections)


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults(app):
    with http_server(DefaultsHandler) as port:
        with ConnectionMeasurement() as m:
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()
        assert m.connection_count <= 5

    # Text output
    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" in content
    assert "Anchor 'does-not-exist' not found" in content
    # images should fail
    assert f"Not Found for url: http://localhost:{port}/image.png" in content
    assert f"Not Found for url: http://localhost:{port}/image2.png" in content
    # looking for local file should fail
    assert f"[broken] http://localhost:{port}/path/to/notfound" in content
    assert len(content.splitlines()) == 6

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    row = rows[0]
    for attr in ("filename", "lineno", "status", "code", "uri", "info"):
        assert attr in row

    assert len(content.splitlines()) == 9
    assert len(rows) == 9
    # the output order of the rows is not stable
    # due to possible variance in network latency
    rowsby = {row["uri"]: row for row in rows}
    assert rowsby[f"http://localhost:{port}/#!bar"] == {
        'filename': 'links.rst',
        'lineno': 4,
        'status': 'working',
        'code': 0,
        'uri': f'http://localhost:{port}/#!bar',
        'info': '',
    }

    def _missing_resource(filename: str, lineno: int):
        return {
            'filename': 'links.rst',
            'lineno': lineno,
            'status': 'broken',
            'code': 0,
            'uri': f'http://localhost:{port}/{filename}',
            'info': f'404 Client Error: Not Found for url: http://localhost:{port}/{filename}',
        }
    accurate_linenumbers = docutils.__version_info__[:2] >= (0, 21)
    image2_lineno = 12 if accurate_linenumbers else 13
    assert rowsby[f'http://localhost:{port}/image2.png'] == _missing_resource("image2.png", image2_lineno)
    # looking for '#top' and '#does-not-exist' not found should fail
    assert rowsby[f"http://localhost:{port}/#top"]["info"] == "Anchor 'top' not found"
    assert rowsby[f"http://localhost:{port}/#top"]["status"] == "broken"
    assert rowsby[f"http://localhost:{port}/#does-not-exist"]["info"] == "Anchor 'does-not-exist' not found"
    # images should fail
    assert f"Not Found for url: http://localhost:{port}/image.png" in rowsby[f"http://localhost:{port}/image.png"]["info"]
    # anchor should be found
    assert rowsby[f'http://localhost:{port}/anchor.html#found'] == {
        'filename': 'links.rst',
        'lineno': 14,
        'status': 'working',
        'code': 0,
        'uri': f'http://localhost:{port}/anchor.html#found',
        'info': '',
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_check_link_response_only(app):
    with http_server(DefaultsHandler) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_anchors = False
        app.build()

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    rowsby = {row["uri"]: row for row in rows}
    assert rowsby[f"http://localhost:{port}/#top"]["status"] == "working"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-too-many-retries', freshenv=True)
def test_too_many_retries(app):
    with http_server(DefaultsHandler) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"`Non-existing uri with localhost <https://localhost:{port}/doesnotexist>`_\n"):
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()

    # Text output
    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # looking for non-existent URL should fail
    # assert " Max retries exceeded with url: /doesnotexist" in content

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
    assert row['uri'] == f'https://localhost:{port}/doesnotexist'


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-raw-node', freshenv=True)
def test_raw_node(app):
    with http_server(OKHandler) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            ".. raw:: html\n"
                            f"  :url: http://localhost:{port}/\n"):
            app.config.html_baseurl = f'http://localhost:{port}/'
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
        'uri': f'http://localhost:{port}/',
        'info': '',
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-anchors-ignore', freshenv=True)
def test_anchors_ignored(app):
    with http_server(OKHandler) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"-* `Example Bar invalid <http://localhost:{port}/#!bar>`_\n"
                            f"-* `Example Bar invalid <http://localhost:{port}/#top>`_\n"):
            app.config.linkcheck_anchors_ignore = ["^!", "^top$"]
            app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # expect all ok when excluding #top
    assert not content


class AnchorsIgnoreForUrlHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path in {'/valid', '/ignored'}:
            self.send_response(200, "OK")
        else:
            self.send_response(404, "Not Found")
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        if self.path == '/valid':
            self.wfile.write(b"<h1 id='valid-anchor'>valid anchor</h1>\n")
        elif self.path == '/ignored':
            self.wfile.write(b"no anchor but page exists\n")


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-anchors-ignore-for-url', freshenv=True)
def test_anchors_ignored_for_url(app):
    with http_server(AnchorsIgnoreForUrlHandler) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_anchors_ignore_for_url = [
            f'http://localhost:{port}/ignored',  # existing page
            f'http://localhost:{port}/invalid',  # unknown page
        ]
        app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    attrs = ('filename', 'lineno', 'status', 'code', 'uri', 'info')
    data = [json.loads(x) for x in content.splitlines()]
    assert len(data) == 7
    assert all(all(attr in row for attr in attrs) for row in data)

    # rows may be unsorted due to network latency or
    # the order the threads are processing the links
    rows = {r['uri']: {'status': r['status'], 'info': r['info']} for r in data}

    assert rows[f'http://localhost:{port}/valid']['status'] == 'working'
    assert rows[f'http://localhost:{port}/valid#valid-anchor']['status'] == 'working'
    assert rows[f'http://localhost:{port}/valid#invalid-anchor'] == {
        'status': 'broken',
        'info': "Anchor 'invalid-anchor' not found",
    }

    assert rows[f'http://localhost:{port}/ignored']['status'] == 'working'
    assert rows[f'http://localhost:{port}/ignored#invalid-anchor']['status'] == 'working'

    assert rows[f'http://localhost:{port}/invalid'] == {
        'status': 'broken',
        'info': f'404 Client Error: Not Found for url: http://localhost:{port}/invalid',
    }
    assert rows[f'http://localhost:{port}/invalid#anchor'] == {
        'status': 'broken',
        'info': f'404 Client Error: Not Found for url: http://localhost:{port}/invalid',
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-anchor', freshenv=True)
def test_raises_for_invalid_status(app):
    class InternalServerErrorHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            self.send_error(500, "Internal Server Error")

    with http_server(InternalServerErrorHandler) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        f"index.rst:1: [broken] http://localhost:{port}/#anchor: "
        "500 Server Error: Internal Server Error "
        f"for url: http://localhost:{port}/\n"
    )


def custom_handler(valid_credentials=(), success_criteria=lambda _: True):
    """
    Returns an HTTP request handler that authenticates the client and then determines
    an appropriate HTTP response code, based on caller-provided credentials and optional
    success criteria, respectively.
    """
    expected_token = None
    if valid_credentials:
        assert len(valid_credentials) == 2, "expected a pair of strings as credentials"
        expected_token = b64encode(":".join(valid_credentials).encode()).decode("utf-8")
        del valid_credentials

    class CustomHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def authenticated(method):
            def method_if_authenticated(self):
                if expected_token is None:
                    return method(self)
                elif not self.headers["Authorization"]:
                    self.send_response(401, "Unauthorized")
                    self.end_headers()
                elif self.headers["Authorization"] == f"Basic {expected_token}":
                    return method(self)
                else:
                    self.send_response(403, "Forbidden")
                    self.send_header("Content-Length", "0")
                    self.end_headers()

            return method_if_authenticated

        @authenticated
        def do_HEAD(self):
            self.do_GET()

        @authenticated
        def do_GET(self):
            if success_criteria(self):
                self.send_response(200, "OK")
                self.send_header("Content-Length", "0")
            else:
                self.send_response(400, "Bad Request")
                self.send_header("Content-Length", "0")
            self.end_headers()

    return CustomHandler


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_auth_header_uses_first_match(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_auth = [
            (r'^$', ('no', 'match')),
            (fr'^http://localhost:{port}/$', ('user1', 'password')),
            (r'.*local.*', ('user2', 'hunter2')),
        ]
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.filterwarnings('ignore::sphinx.deprecation.RemovedInSphinx80Warning')
@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_unauthorized_broken(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"`local server <http://localhost:{port}/>`_"):
            app.config.linkcheck_allow_unauthorized = False
            app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["info"] == "unauthorized"
    assert content["status"] == "broken"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_auth_header_no_match(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"`local server <http://localhost:{port}/>`_"):
            with pytest.warns(RemovedInSphinx80Warning, match='linkcheck builder encountered an HTTP 401'):
                app.config.linkcheck_auth = [(r'^$', ('user1', 'password'))]
                app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    # This link is considered working based on the default linkcheck_allow_unauthorized=true
    assert content["info"] == "unauthorized"
    assert content["status"] == "working"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_linkcheck_request_headers(app):
    def check_headers(self):
        if "X-Secret" in self.headers:
            return False
        if self.headers["Accept"] != "text/html":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_request_headers = {
            f"http://localhost:{port}/": {"Accept": "text/html"},
            "*": {"X-Secret": "open sesami"},
        }
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_linkcheck_request_headers_no_slash(app):
    def check_headers(self):
        if "X-Secret" in self.headers:
            return False
        if self.headers["Accept"] != "application/json":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_request_headers = {
            f"http://localhost:{port}": {"Accept": "application/json"},
            "*": {"X-Secret": "open sesami"},
        }
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_linkcheck_request_headers_default(app):
    def check_headers(self):
        if self.headers["X-Secret"] != "open sesami":
            return False
        if self.headers["Accept"] == "application/json":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)):
        app.config.linkcheck_request_headers = {
            "http://do.not.match.org": {"Accept": "application/json"},
            "*": {"X-Secret": "open sesami"},
        }
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


def make_redirect_handler(*, support_head):
    class RedirectOnceHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_HEAD(self):
            if support_head:
                self.do_GET()
            else:
                self.send_response(405, "Method Not Allowed")
                self.send_header("Content-Length", "0")
                self.end_headers()

        def do_GET(self):
            if self.path == "/?redirected=1":
                self.send_response(204, "No content")
            else:
                self.send_response(302, "Found")
                self.send_header("Location", "/?redirected=1")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_date_time_string(self):
            """Strip date and time from logged messages for assertions."""
            return ""

    return RedirectOnceHandler


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_follows_redirects_on_HEAD(app, capsys, warning):
    with http_server(make_redirect_handler(support_head=True)) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()
    stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        "index.rst:1: [redirected with Found] "
        f"http://localhost:{port}/ to http://localhost:{port}/?redirected=1\n"
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 302 -
        127.0.0.1 - - [] "HEAD /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert warning.getvalue() == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_follows_redirects_on_GET(app, capsys, warning):
    with http_server(make_redirect_handler(support_head=False)) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()
    stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        "index.rst:1: [redirected with Found] "
        f"http://localhost:{port}/ to http://localhost:{port}/?redirected=1\n"
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 405 -
        127.0.0.1 - - [] "GET / HTTP/1.1" 302 -
        127.0.0.1 - - [] "GET /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert warning.getvalue() == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-warn-redirects')
def test_linkcheck_allowed_redirects(app, warning):
    with http_server(make_redirect_handler(support_head=False)) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.config.linkcheck_allowed_redirects = {f'http://localhost:{port}/.*1': '.*'}
        compile_linkcheck_allowed_redirects(app, app.config)
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        rows = [json.loads(l) for l in fp]

    assert len(rows) == 2
    records = {row["uri"]: row for row in rows}
    assert records[f"http://localhost:{port}/path1"]["status"] == "working"
    assert records[f"http://localhost:{port}/path2"] == {
        'filename': 'index.rst',
        'lineno': 3,
        'status': 'redirected',
        'code': 302,
        'uri': f'http://localhost:{port}/path2',
        'info': f'http://localhost:{port}/?redirected=1',
    }

    assert (f"index.rst:3: WARNING: redirect  http://localhost:{port}/path2 - with Found to "
            f"http://localhost:{port}/?redirected=1\n" in strip_escseq(warning.getvalue()))
    assert len(warning.getvalue().splitlines()) == 1


class OKHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self.send_response(200, "OK")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        content = b"ok\n"
        self.send_response(200, "OK")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@mock.patch("sphinx.builders.linkcheck.requests.get", wraps=requests.get)
@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_invalid_ssl(get_request, app):
    # Link indicates SSL should be used (https) but the server does not handle it.
    with http_server(OKHandler) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"-`HTTPS server <https://localhost:{port}/>`_\n"):
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()
            assert not get_request.called

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content["status"] == "broken"
    assert content["filename"] == "index.rst"
    assert content["lineno"] == 1
    assert content["uri"] == f"https://localhost:{port}/"
    assert "SSLError" in content["info"]


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_fails(app):
    with https_server(OKHandler) as port:
        app.config.html_baseurl = f'https://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content["status"] == "broken"
    assert content["filename"] == "index.rst"
    assert content["lineno"] == 1
    assert content["uri"] == f"https://localhost:{port}/"
    assert "[SSL: CERTIFICATE_VERIFY_FAILED]" in content["info"]


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_tls_verify_false(app):
    app.config.tls_verify = False
    with https_server(OKHandler) as port:
        app.config.html_baseurl = f'https://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": f'https://localhost:{port}/',
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_tls_cacerts(app):
    app.config.tls_cacerts = CERT_FILE
    with https_server(OKHandler) as port:
        app.config.html_baseurl = f'https://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": f'https://localhost:{port}/',
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_requests_env_var(monkeypatch, app):
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", CERT_FILE)
    with https_server(OKHandler) as port:
        app.config.html_baseurl = f'https://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": f'https://localhost:{port}/',
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_nonexistent_cert_file(app):
    app.config.tls_cacerts = "does/not/exist"
    with https_server(OKHandler) as port:
        app.config.html_baseurl = f'https://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "broken",
        "filename": "index.rst",
        "lineno": 1,
        "uri": f'https://localhost:{port}/',
        "info": "Could not find a suitable TLS CA certificate bundle, invalid path: does/not/exist",
    }


class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        content = b"ok\n"
        self.send_response(200, "OK")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
        self.close_connection = True  # we don't expect the client to read this response body


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_TooManyRedirects_on_HEAD(app, monkeypatch):
    import requests.sessions

    monkeypatch.setattr(requests.sessions, "DEFAULT_REDIRECT_LIMIT", 5)

    with http_server(InfiniteRedirectOnHeadHandler) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": f'http://localhost:{port}/',
        "info": "",
    }


def make_retry_after_handler(responses):
    class RetryAfterHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_HEAD(self):
            status, retry_after = responses.pop(0)
            self.send_response(status)
            if retry_after:
                self.send_header('Retry-After', retry_after)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_date_time_string(self):
            """Strip date and time from logged messages for assertions."""
            return ""

    return RetryAfterHandler


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_retry_after_int_delay(app, capsys, status):
    with http_server(make_retry_after_handler([(429, "0"), (200, None)])) as port:
        with mock.patch("sphinx.builders.linkcheck.DEFAULT_DELAY", 0), \
             mock.patch("sphinx.builders.linkcheck.QUEUE_POLL_SECS", 0.01):
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": f'http://localhost:{port}/',
        "info": "",
    }
    rate_limit_log = f"-rate limited-   http://localhost:{port}/ | sleeping...\n"
    assert rate_limit_log in strip_escseq(status.getvalue())
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.parametrize('tz', [None, 'GMT', 'GMT+3', 'GMT-3'])
@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_retry_after_HTTP_date(tz, app, monkeypatch, capsys):
    retry_after = wsgiref.handlers.format_date_time(time.time())

    with monkeypatch.context() as m:
        if tz is not None:
            m.setenv('TZ', tz)
            if sys.platform != "win32":
                time.tzset()
            m.setattr(sphinx.util.http_date, '_GMT_OFFSET',
                      float(time.localtime().tm_gmtoff))

        with http_server(make_retry_after_handler([(429, retry_after), (200, None)])) as port:
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": f'http://localhost:{port}/',
        "info": "",
    }
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_retry_after_without_header(app, capsys):
    with http_server(make_retry_after_handler([(429, None), (200, None)])) as port:
        with mock.patch("sphinx.builders.linkcheck.DEFAULT_DELAY", 0):
            app.config.html_baseurl = f'http://localhost:{port}/'
            app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": f'http://localhost:{port}/',
        "info": "",
    }
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """,
    )


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_requests_timeout(app):
    class DelayedResponseHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            time.sleep(0.2)  # wait before sending any response data
            self.send_response(200, "OK")
            self.send_header("Content-Length", "0")
            self.end_headers()

    app.config.linkcheck_timeout = 0.01
    with http_server(DelayedResponseHandler) as port:
        with overwrite_file(app.srcdir / "index.rst",
                            f"`local server <http://localhost:{port}/>`_"):
            app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "timeout"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_user_timeout(app):
    app.config.linkcheck_rate_limit_timeout = 0.0
    with http_server(make_retry_after_handler([(429, None)])) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "broken",
        "code": 0,
        "uri": f'http://localhost:{port}/',
        "info": f"429 Client Error: Too Many Requests for url: http://localhost:{port}/",
    }


class FakeResponse:
    headers: dict[str, str] = {}
    url = "http://localhost/"


def test_limit_rate_default_sleep(app):
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), {})
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse.url, FakeResponse.headers.get("Retry-After"))
    assert next_check == 60.0


def test_limit_rate_user_max_delay(app):
    app.config.linkcheck_rate_limit_timeout = 0.0
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), {})
    next_check = worker.limit_rate(FakeResponse.url, FakeResponse.headers.get("Retry-After"))
    assert next_check is None


def test_limit_rate_doubles_previous_wait_time(app):
    rate_limits = {"localhost": RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse.url, FakeResponse.headers.get("Retry-After"))
    assert next_check == 120.0


def test_limit_rate_clips_wait_time_to_max_time(app):
    app.config.linkcheck_rate_limit_timeout = 90.0
    rate_limits = {"localhost": RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse.url, FakeResponse.headers.get("Retry-After"))
    assert next_check == 90.0


def test_limit_rate_bails_out_after_waiting_max_time(app):
    app.config.linkcheck_rate_limit_timeout = 90.0
    rate_limits = {"localhost": RateLimit(90.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.config, Queue(), Queue(), rate_limits)
    next_check = worker.limit_rate(FakeResponse.url, FakeResponse.headers.get("Retry-After"))
    assert next_check is None


@mock.patch('sphinx.util.requests.requests.Session.get_adapter')
def test_connection_contention(get_adapter, app, capsys):
    # Create a shared, but limited-size, connection pool
    import requests
    get_adapter.return_value = requests.adapters.HTTPAdapter(pool_maxsize=1)

    # Set an upper-bound on socket timeouts globally
    import socket
    socket.setdefaulttimeout(5)

    # Create parallel consumer threads
    with http_server(make_redirect_handler(support_head=True)) as port:

        # Place a workload into the linkcheck queue
        link_count = 10
        rqueue, wqueue = Queue(), Queue()
        for _ in range(link_count):
            wqueue.put(CheckRequest(0, Hyperlink(f"http://localhost:{port}", "test", "test.rst", 1)))

        begin, checked = time.time(), []
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
    assert "TimeoutError" not in stderr


class ConnectionResetHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self.close_connection = True

    def do_GET(self):
        self.send_response(200, "OK")
        self.send_header("Content-Length", "0")
        self.end_headers()


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_get_after_head_raises_connection_error(app):
    with http_server(ConnectionResetHandler) as port:
        app.config.html_baseurl = f'http://localhost:{port}/'
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert not content
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": f'http://localhost:{port}/',
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-documents_exclude', freshenv=True)
def test_linkcheck_exclude_documents(app):
    with http_server(DefaultsHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = [json.loads(record) for record in fp]

    assert content == [
        {
            'filename': 'broken_link.rst',
            'lineno': 4,
            'status': 'ignored',
            'code': 0,
            'uri': 'https://www.sphinx-doc.org/this-is-a-broken-link',
            'info': 'broken_link matched ^broken_link$ from linkcheck_exclude_documents',
        },
        {
            'filename': 'br0ken_link.rst',
            'lineno': 4,
            'status': 'ignored',
            'code': 0,
            'uri': 'https://www.sphinx-doc.org/this-is-another-broken-link',
            'info': 'br0ken_link matched br[0-9]ken_link from linkcheck_exclude_documents',
        },
    ]
