"""
    test_build_linkcheck
    ~~~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import http.server
import json
import re
import textwrap
import time
import wsgiref.handlers
from datetime import datetime
from queue import Queue
from typing import Dict
from unittest import mock

import pytest
import requests

from sphinx.builders.linkcheck import HyperlinkAvailabilityCheckWorker, RateLimit
from sphinx.testing.util import strip_escseq
from sphinx.util.console import strip_colors

from .utils import CERT_FILE, http_server, https_server

ts_re = re.compile(r".*\[(?P<ts>.*)\].*")


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults(app):
    app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text()

    print(content)
    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" in content
    assert "Anchor 'does-not-exist' not found" in content
    # looking for non-existent URL should fail
    assert " Max retries exceeded with url: /doesnotexist" in content
    # images should fail
    assert "Not Found for url: https://www.google.com/image.png" in content
    assert "Not Found for url: https://www.google.com/image2.png" in content
    # looking for local file should fail
    assert "[broken] path/to/notfound" in content
    assert len(content.splitlines()) == 6


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults_json(app):
    app.build()

    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text()
    print(content)

    rows = [json.loads(x) for x in content.splitlines()]
    row = rows[0]
    for attr in ["filename", "lineno", "status", "code", "uri",
                 "info"]:
        assert attr in row

    assert len(content.splitlines()) == 11
    assert len(rows) == 11
    # the output order of the rows is not stable
    # due to possible variance in network latency
    rowsby = {row["uri"]: row for row in rows}
    assert rowsby["https://www.google.com#!bar"] == {
        'filename': 'links.txt',
        'lineno': 10,
        'status': 'working',
        'code': 0,
        'uri': 'https://www.google.com#!bar',
        'info': ''
    }
    # looking for non-existent URL should fail
    dnerow = rowsby['https://localhost:7777/doesnotexist']
    assert dnerow['filename'] == 'links.txt'
    assert dnerow['lineno'] == 13
    assert dnerow['status'] == 'broken'
    assert dnerow['code'] == 0
    assert dnerow['uri'] == 'https://localhost:7777/doesnotexist'
    assert rowsby['https://www.google.com/image2.png'] == {
        'filename': 'links.txt',
        'lineno': 19,
        'status': 'broken',
        'code': 0,
        'uri': 'https://www.google.com/image2.png',
        'info': '404 Client Error: Not Found for url: https://www.google.com/image2.png'
    }
    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" == \
        rowsby["https://www.google.com/#top"]["info"]
    assert "Anchor 'does-not-exist' not found" == \
        rowsby["http://www.sphinx-doc.org/en/master/index.html#does-not-exist"]["info"]
    # images should fail
    assert "Not Found for url: https://www.google.com/image.png" in \
        rowsby["https://www.google.com/image.png"]["info"]


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck', freshenv=True,
    confoverrides={'linkcheck_anchors_ignore': ["^!", "^top$"],
                   'linkcheck_ignore': [
                       'https://localhost:7777/doesnotexist',
                       'http://www.sphinx-doc.org/en/master/index.html#',
                       'https://www.google.com/image.png',
                       'https://www.google.com/image2.png',
                       'path/to/notfound']
                   })
def test_anchors_ignored(app):
    app.build()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text()

    # expect all ok when excluding #top
    assert not content


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-anchor', freshenv=True)
def test_raises_for_invalid_status(app):
    class InternalServerErrorHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_error(500, "Internal Server Error")

    with http_server(InternalServerErrorHandler):
        app.build()
    content = (app.outdir / 'output.txt').read_text()
    assert content == (
        "index.rst:1: [broken] http://localhost:7777/#anchor: "
        "500 Server Error: Internal Server Error "
        "for url: http://localhost:7777/\n"
    )


class HeadersDumperHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.send_response(200, "OK")
        self.end_headers()
        print(self.headers.as_string())


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_auth': [
        (r'^$', ('no', 'match')),
        (r'^http://localhost:7777/$', ('user1', 'password')),
        (r'.*local.*', ('user2', 'hunter2')),
    ]})
def test_auth_header_uses_first_match(app, capsys):
    with http_server(HeadersDumperHandler):
        app.build()
    stdout, stderr = capsys.readouterr()
    auth = requests.auth._basic_auth_str('user1', 'password')
    assert "Authorization: %s\n" % auth in stdout


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_auth': [(r'^$', ('user1', 'password'))]})
def test_auth_header_no_match(app, capsys):
    with http_server(HeadersDumperHandler):
        app.build()
    stdout, stderr = capsys.readouterr()
    assert "Authorization" not in stdout


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://localhost:7777/": {
            "Accept": "text/html",
        },
        "*": {
            "X-Secret": "open sesami",
        }
    }})
def test_linkcheck_request_headers(app, capsys):
    with http_server(HeadersDumperHandler):
        app.build()

    stdout, _stderr = capsys.readouterr()
    assert "Accept: text/html\n" in stdout
    assert "X-Secret" not in stdout
    assert "sesami" not in stdout


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://localhost:7777": {"Accept": "application/json"},
        "*": {"X-Secret": "open sesami"}
    }})
def test_linkcheck_request_headers_no_slash(app, capsys):
    with http_server(HeadersDumperHandler):
        app.build()

    stdout, _stderr = capsys.readouterr()
    assert "Accept: application/json\n" in stdout
    assert "X-Secret" not in stdout
    assert "sesami" not in stdout


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck-localserver', freshenv=True,
    confoverrides={'linkcheck_request_headers': {
        "http://do.not.match.org": {"Accept": "application/json"},
        "*": {"X-Secret": "open sesami"}
    }})
def test_linkcheck_request_headers_default(app, capsys):
    with http_server(HeadersDumperHandler):
        app.build()

    stdout, _stderr = capsys.readouterr()
    assert "Accepts: application/json\n" not in stdout
    assert "X-Secret: open sesami\n" in stdout


def make_redirect_handler(*, support_head):
    class RedirectOnceHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            if support_head:
                self.do_GET()
            else:
                self.send_response(405, "Method Not Allowed")
                self.end_headers()

        def do_GET(self):
            if self.path == "/?redirected=1":
                self.send_response(204, "No content")
            else:
                self.send_response(302, "Found")
                self.send_header("Location", "http://localhost:7777/?redirected=1")
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
    content = (app.outdir / 'output.txt').read_text()
    assert content == (
        "index.rst:1: [redirected with Found] "
        "http://localhost:7777/ to http://localhost:7777/?redirected=1\n"
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 302 -
        127.0.0.1 - - [] "HEAD /?redirected=1 HTTP/1.1" 204 -
        """
    )
    assert warning.getvalue() == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_follows_redirects_on_GET(app, capsys, warning):
    with http_server(make_redirect_handler(support_head=False)):
        app.build()
    stdout, stderr = capsys.readouterr()
    content = (app.outdir / 'output.txt').read_text()
    assert content == (
        "index.rst:1: [redirected with Found] "
        "http://localhost:7777/ to http://localhost:7777/?redirected=1\n"
    )
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 405 -
        127.0.0.1 - - [] "GET / HTTP/1.1" 302 -
        127.0.0.1 - - [] "GET /?redirected=1 HTTP/1.1" 204 -
        """
    )
    assert warning.getvalue() == ''


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-warn-redirects',
                    freshenv=True, confoverrides={
                        'linkcheck_allowed_redirects': {'http://localhost:7777/.*1': '.*'}
                    })
def test_linkcheck_allowed_redirects(app, warning):
    with http_server(make_redirect_handler(support_head=False)):
        app.build()

    with open(app.outdir / 'output.json') as fp:
        records = [json.loads(l) for l in fp.readlines()]

    assert len(records) == 2
    result = {r["uri"]: r["status"] for r in records}
    assert result["http://localhost:7777/path1"] == "working"
    assert result["http://localhost:7777/path2"] == "redirected"

    assert ("index.rst:1: WARNING: redirect  http://localhost:7777/path2 - with Found to "
            "http://localhost:7777/?redirected=1\n" in strip_escseq(warning.getvalue()))
    assert len(warning.getvalue().splitlines()) == 1


class OKHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write(b"ok\n")


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver-https', freshenv=True)
def test_invalid_ssl(app):
    # Link indicates SSL should be used (https) but the server does not handle it.
    with http_server(OKHandler):
        app.build()

    with open(app.outdir / 'output.json') as fp:
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

    with open(app.outdir / 'output.json') as fp:
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

    with open(app.outdir / 'output.json') as fp:
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

    with open(app.outdir / 'output.json') as fp:
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

    with open(app.outdir / 'output.json') as fp:
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

    with open(app.outdir / 'output.json') as fp:
        content = json.load(fp)
    assert content == {
        "code": 0,
        "status": "broken",
        "filename": "index.rst",
        "lineno": 1,
        "uri": "https://localhost:7777/",
        "info": "Could not find a suitable TLS CA certificate bundle, invalid path: does/not/exist",
    }


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_TooManyRedirects_on_HEAD(app):
    class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(302, "Found")
            self.send_header("Location", "http://localhost:7777/")
            self.end_headers()

        def do_GET(self):
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(b"ok\n")

    with http_server(InfiniteRedirectOnHeadHandler):
        app.build()

    with open(app.outdir / 'output.json') as fp:
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
        def do_HEAD(self):
            status, retry_after = responses.pop(0)
            self.send_response(status)
            if retry_after:
                self.send_header('Retry-After', retry_after)
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
    content = (app.outdir / 'output.json').read_text()
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "working",
        "code": 0,
        "uri": "http://localhost:7777/",
        "info": "",
    }
    rate_limit_log = "-rate limited-   http://localhost:7777/ | sleeping...\n"
    assert rate_limit_log in strip_colors(status.getvalue())
    _stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent(
        """\
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 429 -
        127.0.0.1 - - [] "HEAD / HTTP/1.1" 200 -
        """
    )


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_retry_after_HTTP_date(app, capsys):
    now = datetime.now().timetuple()
    retry_after = wsgiref.handlers.format_date_time(time.mktime(now))
    with http_server(make_retry_after_handler([(429, retry_after), (200, None)])):
        app.build()
    content = (app.outdir / 'output.json').read_text()
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
        """
    )


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_retry_after_without_header(app, capsys):
    with http_server(make_retry_after_handler([(429, None), (200, None)])),\
         mock.patch("sphinx.builders.linkcheck.DEFAULT_DELAY", 0):
        app.build()
    content = (app.outdir / 'output.json').read_text()
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
        """
    )


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_too_many_requests_user_timeout(app, capsys):
    app.config.linkcheck_rate_limit_timeout = 0.0
    with http_server(make_retry_after_handler([(429, None)])):
        app.build()
    content = (app.outdir / 'output.json').read_text()
    assert json.loads(content) == {
        "filename": "index.rst",
        "lineno": 1,
        "status": "broken",
        "code": 0,
        "uri": "http://localhost:7777/",
        "info": "429 Client Error: Too Many Requests for url: http://localhost:7777/",
    }


class FakeResponse:
    headers = {}  # type: Dict[str, str]
    url = "http://localhost/"


def test_limit_rate_default_sleep(app):
    worker = HyperlinkAvailabilityCheckWorker(app.env, app.config, Queue(), Queue(), {})
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse())
    assert next_check == 60.0


def test_limit_rate_user_max_delay(app):
    app.config.linkcheck_rate_limit_timeout = 0.0
    worker = HyperlinkAvailabilityCheckWorker(app.env, app.config, Queue(), Queue(), {})
    next_check = worker.limit_rate(FakeResponse())
    assert next_check is None


def test_limit_rate_doubles_previous_wait_time(app):
    rate_limits = {"localhost": RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.env, app.config, Queue(), Queue(),
                                              rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse())
    assert next_check == 120.0


def test_limit_rate_clips_wait_time_to_max_time(app):
    app.config.linkcheck_rate_limit_timeout = 90.0
    rate_limits = {"localhost": RateLimit(60.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.env, app.config, Queue(), Queue(),
                                              rate_limits)
    with mock.patch('time.time', return_value=0.0):
        next_check = worker.limit_rate(FakeResponse())
    assert next_check == 90.0


def test_limit_rate_bails_out_after_waiting_max_time(app):
    app.config.linkcheck_rate_limit_timeout = 90.0
    rate_limits = {"localhost": RateLimit(90.0, 0.0)}
    worker = HyperlinkAvailabilityCheckWorker(app.env, app.config, Queue(), Queue(),
                                              rate_limits)
    next_check = worker.limit_rate(FakeResponse())
    assert next_check is None


class ConnectionResetHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.connection.close()

    def do_GET(self):
        self.send_response(200, "OK")
        self.end_headers()


@pytest.mark.sphinx('linkcheck', testroot='linkcheck-localserver', freshenv=True)
def test_get_after_head_raises_connection_error(app):
    with http_server(ConnectionResetHandler):
        app.build()
    content = (app.outdir / 'output.txt').read_text()
    assert not content
    content = (app.outdir / 'output.json').read_text()
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
    app.build()

    with open(app.outdir / 'output.json') as fp:
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
