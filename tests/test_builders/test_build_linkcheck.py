"""Test the build process with manpage builder with the test root."""

from __future__ import annotations

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
)
from sphinx.testing.util import strip_escseq
from sphinx.util import requests

from tests.utils import CERT_FILE, http_server, https_server

ts_re = re.compile(r".*\[(?P<ts>.*)\].*")


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
    with http_server(DefaultsHandler):
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
    assert "Not Found for url: http://localhost:7777/image.png" in content
    assert "Not Found for url: http://localhost:7777/image2.png" in content
    # looking for local file should fail
    assert "[broken] path/to/notfound" in content
    assert len(content.splitlines()) == 5

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    row = rows[0]
    for attr in ("filename", "lineno", "status", "code", "uri", "info"):
        assert attr in row

    assert len(content.splitlines()) == 10
    assert len(rows) == 10
    # the output order of the rows is not stable
    # due to possible variance in network latency
    rowsby = {row["uri"]: row for row in rows}
    assert rowsby["http://localhost:7777#!bar"] == {
        'filename': 'links.rst',
        'lineno': 5,
        'status': 'working',
        'code': 0,
        'uri': 'http://localhost:7777#!bar',
        'info': '',
    }

    def _missing_resource(filename: str, lineno: int):
        return {
            'filename': 'links.rst',
            'lineno': lineno,
            'status': 'broken',
            'code': 0,
            'uri': f'http://localhost:7777/{filename}',
            'info': f'404 Client Error: Not Found for url: http://localhost:7777/{filename}',
        }
    accurate_linenumbers = docutils.__version_info__[:2] >= (0, 21)
    image2_lineno = 12 if accurate_linenumbers else 13
    assert rowsby['http://localhost:7777/image2.png'] == _missing_resource("image2.png", image2_lineno)
    # looking for '#top' and '#does-not-exist' not found should fail
    assert rowsby["http://localhost:7777/#top"]["info"] == "Anchor 'top' not found"
    assert rowsby["http://localhost:7777/#top"]["status"] == "broken"
    assert rowsby["http://localhost:7777#does-not-exist"]["info"] == "Anchor 'does-not-exist' not found"
    # images should fail
    assert "Not Found for url: http://localhost:7777/image.png" in rowsby["http://localhost:7777/image.png"]["info"]
    # anchor should be found
    assert rowsby['http://localhost:7777/anchor.html#found'] == {
        'filename': 'links.rst',
        'lineno': 14,
        'status': 'working',
        'code': 0,
        'uri': 'http://localhost:7777/anchor.html#found',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck', freshenv=True,
    confoverrides={'linkcheck_anchors': False})
def test_check_link_response_only(app):
    with http_server(DefaultsHandler):
        app.build()

    # JSON output
    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')

    rows = [json.loads(x) for x in content.splitlines()]
    rowsby = {row["uri"]: row for row in rows}
    assert rowsby["http://localhost:7777/#top"]["status"] == "working"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-too-many-retries', freshenv=True)
def test_too_many_retries(app):
    with http_server(DefaultsHandler):
        app.build()

    # Text output
    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')

    # looking for non-existent URL should fail
    assert " Max retries exceeded with url: /doesnotexist" in content

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
    assert row['uri'] == 'https://localhost:7777/doesnotexist'


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-raw-node', freshenv=True)
def test_raw_node(app):
    with http_server(OKHandler):
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
        'uri': 'http://localhost:7777/',
        'info': '',
    }


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-anchors-ignore', freshenv=True,
    confoverrides={'linkcheck_anchors_ignore': ["^!", "^top$"]})
def test_anchors_ignored(app):
    with http_server(OKHandler):
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


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-anchors-ignore-for-url', freshenv=True,
    confoverrides={'linkcheck_anchors_ignore_for_url': [
        'http://localhost:7777/ignored',  # existing page
        'http://localhost:7777/invalid',  # unknown page
    ]})
def test_anchors_ignored_for_url(app):
    with http_server(AnchorsIgnoreForUrlHandler):
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

    assert rows['http://localhost:7777/valid']['status'] == 'working'
    assert rows['http://localhost:7777/valid#valid-anchor']['status'] == 'working'
    assert rows['http://localhost:7777/valid#invalid-anchor'] == {
        'status': 'broken',
        'info': "Anchor 'invalid-anchor' not found",
    }

    assert rows['http://localhost:7777/ignored']['status'] == 'working'
    assert rows['http://localhost:7777/ignored#invalid-anchor']['status'] == 'working'

    assert rows['http://localhost:7777/invalid'] == {
        'status': 'broken',
        'info': '404 Client Error: Not Found for url: http://localhost:7777/invalid',
    }
    assert rows['http://localhost:7777/invalid#anchor'] == {
        'status': 'broken',
        'info': '404 Client Error: Not Found for url: http://localhost:7777/invalid',
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-anchor', freshenv=True)
def test_raises_for_invalid_status(app):
    class InternalServerErrorHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            self.send_error(500, "Internal Server Error")

    with http_server(InternalServerErrorHandler):
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        "index.rst:1: [broken] http://localhost:7777/#anchor: "
        "500 Server Error: Internal Server Error "
        "for url: http://localhost:7777/\n"
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


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_auth': [
        (r'^$', ('no', 'match')),
        (r'^http://localhost:7777/$', ('user1', 'password')),
        (r'.*local.*', ('user2', 'hunter2')),
    ]})
def test_auth_header_uses_first_match(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.filterwarnings('ignore::sphinx.deprecation.RemovedInSphinx80Warning')
@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_allow_unauthorized': False})
def test_unauthorized_broken(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["info"] == "unauthorized"
    assert content["status"] == "broken"


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_auth': [(r'^$', ('user1', 'password'))]})
def test_auth_header_no_match(app):
    with http_server(custom_handler(valid_credentials=("user1", "password"))):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    # This link is considered working based on the default linkcheck_allow_unauthorized=true
    assert content["info"] == "unauthorized"
    assert content["status"] == "working"


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://localhost:7777/": {
            "Accept": "text/html",
        },
        "*": {
            "X-Secret": "open sesami",
        },
    }})
def test_linkcheck_request_headers(app):
    def check_headers(self):
        if "X-Secret" in self.headers:
            return False
        if self.headers["Accept"] != "text/html":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://localhost:7777": {"Accept": "application/json"},
        "*": {"X-Secret": "open sesami"},
    }})
def test_linkcheck_request_headers_no_slash(app):
    def check_headers(self):
        if "X-Secret" in self.headers:
            return False
        if self.headers["Accept"] != "application/json":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "working"


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://do.not.match.org": {"Accept": "application/json"},
        "*": {"X-Secret": "open sesami"},
    }})
def test_linkcheck_request_headers_default(app):
    def check_headers(self):
        if self.headers["X-Secret"] != "open sesami":
            return False
        if self.headers["Accept"] == "application/json":
            return False
        return True

    with http_server(custom_handler(success_criteria=check_headers)):
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
                self.send_header("Location", "http://localhost:7777/?redirected=1")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_date_time_string(self):
            """Strip date and time from logged messages for assertions."""
            return ""

    return RedirectOnceHandler


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_follows_redirects_on_HEAD(app, capsys, warning):
    with http_server(make_redirect_handler(support_head=True)):
        app.build()
    stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        "index.rst:1: [redirected with Found] "
        "http://localhost:7777/ to http://localhost:7777/?redirected=1\n"
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
    with http_server(make_redirect_handler(support_head=False)):
        app.build()
    stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert content == (
        "index.rst:1: [redirected with Found] "
        "http://localhost:7777/ to http://localhost:7777/?redirected=1\n"
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 405 -
        127.0.0.1 - - [] "GET / HTTP/1.1" 302 -
        127.0.0.1 - - [] "GET /?redirected=1 HTTP/1.1" 204 -
        """,
    )
    assert warning.getvalue() == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-warn-redirects',
                    freshenv=True, confoverrides={
                        'linkcheck_allowed_redirects': {'http://localhost:7777/.*1': '.*'},
                    })
def test_linkcheck_allowed_redirects(app, warning):
    with http_server(make_redirect_handler(support_head=False)):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        rows = [json.loads(l) for l in fp.readlines()]

    assert len(rows) == 2
    records = {row["uri"]: row for row in rows}
    assert records["http://localhost:7777/path1"]["status"] == "working"
    assert records["http://localhost:7777/path2"] == {
        'filename': 'index.rst',
        'lineno': 3,
        'status': 'redirected',
        'code': 302,
        'uri': 'http://localhost:7777/path2',
        'info': 'http://localhost:7777/?redirected=1',
    }

    assert ("index.rst:3: WARNING: redirect  http://localhost:7777/path2 - with Found to "
            "http://localhost:7777/?redirected=1\n" in strip_escseq(warning.getvalue()))
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
    with http_server(OKHandler):
        app.build()
        assert not get_request.called

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content["status"] == "broken"
    assert content["filename"] == "index.rst"
    assert content["lineno"] == 1
    assert content["uri"] == "https://localhost:7777/"
    assert "SSLError" in content["info"]


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_fails(app):
    with https_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content["status"] == "broken"
    assert content["filename"] == "index.rst"
    assert content["lineno"] == 1
    assert content["uri"] == "https://localhost:7777/"
    assert "[SSL: CERTIFICATE_VERIFY_FAILED]" in content["info"]


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_tls_verify_false(app):
    app.config.tls_verify = False
    with https_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "https://localhost:7777/",
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_tls_cacerts(app):
    app.config.tls_cacerts = CERT_FILE
    with https_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "https://localhost:7777/",
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_with_requests_env_var(monkeypatch, app):
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", CERT_FILE)
    with https_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "https://localhost:7777/",
        "info": "",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_connect_to_selfsigned_nonexistent_cert_file(app):
    app.config.tls_cacerts = "does/not/exist"
    with https_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "broken",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "https://localhost:7777/",
        "info": "Could not find a suitable TLS CA certificate bundle, invalid path: does/not/exist",
    }


class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "http://localhost:7777/")
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

    with http_server(InfiniteRedirectOnHeadHandler):
        app.build()

    with open(app.outdir / 'output.json', encoding='utf-8') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "working",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "http://localhost:7777/",
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
    with http_server(make_retry_after_handler([(429, "0"), (200, None)])), \
         mock.patch("sphinx.builders.linkcheck.DEFAULT_DELAY", 0), \
         mock.patch("sphinx.builders.linkcheck.QUEUE_POLL_SECS", 0.01):
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": "http://localhost:7777/",
        "info": "",
    }
    rate_limit_log = "-rate limited-   http://localhost:7777/ | sleeping...\n"
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

        with http_server(make_retry_after_handler([(429, retry_after), (200, None)])):
            app.build()

    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": "http://localhost:7777/",
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
    with http_server(make_retry_after_handler([(429, None), (200, None)])), \
         mock.patch("sphinx.builders.linkcheck.DEFAULT_DELAY", 0):
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": "http://localhost:7777/",
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
    with http_server(DelayedResponseHandler):
        app.build()

    with open(app.outdir / "output.json", encoding="utf-8") as fp:
        content = json.load(fp)

    assert content["status"] == "timeout"


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_user_timeout(app):
    app.config.linkcheck_rate_limit_timeout = 0.0
    with http_server(make_retry_after_handler([(429, None)])):
        app.build()
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "broken",
        "code": 0,
        "uri": "http://localhost:7777/",
        "info": "429 Client Error: Too Many Requests for url: http://localhost:7777/",
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

    # Place a workload into the linkcheck queue
    link_count = 10
    rqueue, wqueue = Queue(), Queue()
    for _ in range(link_count):
        wqueue.put(CheckRequest(0, Hyperlink("http://localhost:7777", "test", "test.rst", 1)))

    # Create parallel consumer threads
    with http_server(make_redirect_handler(support_head=True)):
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
    with http_server(ConnectionResetHandler):
        app.build()
    content = (app.outdir / 'output.txt').read_text(encoding='utf8')
    assert not content
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": "http://localhost:7777/",
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
