"""
    sphinx.builders.linkcheck
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The CheckExternalLinksBuilder class.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import json
import queue
import re
import socket
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from os import path
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple
from urllib.parse import unquote, urlparse

from docutils import nodes
from docutils.nodes import Element, Node
from requests import Response
from requests.exceptions import HTTPError, TooManyRedirects

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.locale import __
from sphinx.util import encode_uri, logging, requests
from sphinx.util.console import darkgray, darkgreen, purple, red, turquoise  # type: ignore
from sphinx.util.nodes import get_node_line

logger = logging.getLogger(__name__)

uri_re = re.compile('([a-z]+:)?//')  # matches to foo:// and // (a protocol relative URL)

RateLimit = NamedTuple('RateLimit', (('delay', float), ('next_check', float)))

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
}
CHECK_IMMEDIATELY = 0
QUEUE_POLL_SECS = 1
DEFAULT_DELAY = 60.0


def node_line_or_0(node: Element) -> int:
    """
    PriorityQueue items must be comparable. The line number is part of the
    tuple used by the PriorityQueue, keep an homogeneous type for comparison.
    """
    return get_node_line(node) or 0


class AnchorCheckParser(HTMLParser):
    """Specialized HTML parser that looks for a specific anchor."""

    def __init__(self, search_anchor: str) -> None:
        super().__init__()

        self.search_anchor = search_anchor
        self.found = False

    def handle_starttag(self, tag: Any, attrs: Any) -> None:
        for key, value in attrs:
            if key in ('id', 'name') and value == self.search_anchor:
                self.found = True
                break


def check_anchor(response: requests.requests.Response, anchor: str) -> bool:
    """Reads HTML data from a response object `response` searching for `anchor`.
    Returns True if anchor was found, False otherwise.
    """
    parser = AnchorCheckParser(anchor)
    # Read file in chunks. If we find a matching anchor, we break
    # the loop early in hopes not to have to download the whole thing.
    for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
        if isinstance(chunk, bytes):    # requests failed to decode
            chunk = chunk.decode()      # manually try to decode it

        parser.feed(chunk)
        if parser.found:
            break
    parser.close()
    return parser.found


class CheckExternalLinksBuilder(Builder):
    """
    Checks for broken external links.
    """
    name = 'linkcheck'
    epilog = __('Look for any errors in the above output or in '
                '%(outdir)s/output.txt')

    def init(self) -> None:
        self.to_ignore = [re.compile(x) for x in self.app.config.linkcheck_ignore]
        self.anchors_ignore = [re.compile(x)
                               for x in self.app.config.linkcheck_anchors_ignore]
        self.auth = [(re.compile(pattern), auth_info) for pattern, auth_info
                     in self.app.config.linkcheck_auth]
        self.good = set()       # type: Set[str]
        self.broken = {}        # type: Dict[str, str]
        self.redirected = {}    # type: Dict[str, Tuple[str, int]]
        # set a timeout for non-responding servers
        socket.setdefaulttimeout(5.0)
        # create output file
        open(path.join(self.outdir, 'output.txt'), 'w').close()
        # create JSON output file
        open(path.join(self.outdir, 'output.json'), 'w').close()

        # create queues and worker threads
        self.rate_limits = {}  # type: Dict[str, RateLimit]
        self.wqueue = queue.PriorityQueue()  # type: queue.PriorityQueue
        self.rqueue = queue.Queue()  # type: queue.Queue
        self.workers = []  # type: List[threading.Thread]
        for i in range(self.app.config.linkcheck_workers):
            thread = threading.Thread(target=self.check_thread, daemon=True)
            thread.start()
            self.workers.append(thread)

    def check_thread(self) -> None:
        kwargs = {}
        if self.app.config.linkcheck_timeout:
            kwargs['timeout'] = self.app.config.linkcheck_timeout

        def get_request_headers() -> Dict:
            url = urlparse(uri)
            candidates = ["%s://%s" % (url.scheme, url.netloc),
                          "%s://%s/" % (url.scheme, url.netloc),
                          uri,
                          "*"]

            for u in candidates:
                if u in self.config.linkcheck_request_headers:
                    headers = dict(DEFAULT_REQUEST_HEADERS)
                    headers.update(self.config.linkcheck_request_headers[u])
                    return headers

            return {}

        def check_uri() -> Tuple[str, str, int]:
            # split off anchor
            if '#' in uri:
                req_url, anchor = uri.split('#', 1)
                for rex in self.anchors_ignore:
                    if rex.match(anchor):
                        anchor = None
                        break
            else:
                req_url = uri
                anchor = None

            # handle non-ASCII URIs
            try:
                req_url.encode('ascii')
            except UnicodeError:
                req_url = encode_uri(req_url)

            # Get auth info, if any
            for pattern, auth_info in self.auth:
                if pattern.match(uri):
                    break
            else:
                auth_info = None

            # update request headers for the URL
            kwargs['headers'] = get_request_headers()

            try:
                if anchor and self.app.config.linkcheck_anchors:
                    # Read the whole document and see if #anchor exists
                    response = requests.get(req_url, stream=True, config=self.app.config,
                                            auth=auth_info, **kwargs)
                    response.raise_for_status()
                    found = check_anchor(response, unquote(anchor))

                    if not found:
                        raise Exception(__("Anchor '%s' not found") % anchor)
                else:
                    try:
                        # try a HEAD request first, which should be easier on
                        # the server and the network
                        response = requests.head(req_url, allow_redirects=True,
                                                 config=self.app.config, auth=auth_info,
                                                 **kwargs)
                        response.raise_for_status()
                    except (HTTPError, TooManyRedirects) as err:
                        if isinstance(err, HTTPError) and err.response.status_code == 429:
                            raise
                        # retry with GET request if that fails, some servers
                        # don't like HEAD requests.
                        response = requests.get(req_url, stream=True,
                                                config=self.app.config,
                                                auth=auth_info, **kwargs)
                        response.raise_for_status()
            except HTTPError as err:
                if err.response.status_code == 401:
                    # We'll take "Unauthorized" as working.
                    return 'working', ' - unauthorized', 0
                elif err.response.status_code == 429:
                    next_check = self.limit_rate(err.response)
                    if next_check is not None:
                        self.wqueue.put((next_check, uri, docname, lineno), False)
                        return 'rate-limited', '', 0
                    return 'broken', str(err), 0
                elif err.response.status_code == 503:
                    # We'll take "Service Unavailable" as ignored.
                    return 'ignored', str(err), 0
                else:
                    return 'broken', str(err), 0
            except Exception as err:
                return 'broken', str(err), 0
            else:
                netloc = urlparse(req_url).netloc
                try:
                    del self.rate_limits[netloc]
                except KeyError:
                    pass
            if response.url.rstrip('/') == req_url.rstrip('/'):
                return 'working', '', 0
            else:
                new_url = response.url
                if anchor:
                    new_url += '#' + anchor
                # history contains any redirects, get last
                if response.history:
                    code = response.history[-1].status_code
                    return 'redirected', new_url, code
                else:
                    return 'redirected', new_url, 0

        def check(docname: str) -> Tuple[str, str, int]:
            # check for various conditions without bothering the network
            if len(uri) == 0 or uri.startswith(('#', 'mailto:', 'tel:')):
                return 'unchecked', '', 0
            elif not uri.startswith(('http:', 'https:')):
                if uri_re.match(uri):
                    # non supported URI schemes (ex. ftp)
                    return 'unchecked', '', 0
                else:
                    srcdir = path.dirname(self.env.doc2path(docname))
                    if path.exists(path.join(srcdir, uri)):
                        return 'working', '', 0
                    else:
                        for rex in self.to_ignore:
                            if rex.match(uri):
                                return 'ignored', '', 0
                        else:
                            self.broken[uri] = ''
                            return 'broken', '', 0
            elif uri in self.good:
                return 'working', 'old', 0
            elif uri in self.broken:
                return 'broken', self.broken[uri], 0
            elif uri in self.redirected:
                return 'redirected', self.redirected[uri][0], self.redirected[uri][1]
            for rex in self.to_ignore:
                if rex.match(uri):
                    return 'ignored', '', 0

            # need to actually check the URI
            for _ in range(self.app.config.linkcheck_retries):
                status, info, code = check_uri()
                if status != "broken":
                    break

            if status == "working":
                self.good.add(uri)
            elif status == "broken":
                self.broken[uri] = info
            elif status == "redirected":
                self.redirected[uri] = (info, code)

            return (status, info, code)

        while True:
            next_check, uri, docname, lineno = self.wqueue.get()
            if uri is None:
                break
            netloc = urlparse(uri).netloc
            try:
                # Refresh rate limit.
                # When there are many links in the queue, workers are all stuck waiting
                # for responses, but the builder keeps queuing. Links in the queue may
                # have been queued before rate limits were discovered.
                next_check = self.rate_limits[netloc].next_check
            except KeyError:
                pass
            if next_check > time.time():
                # Sleep before putting message back in the queue to avoid
                # waking up other threads.
                time.sleep(QUEUE_POLL_SECS)
                self.wqueue.put((next_check, uri, docname, lineno), False)
                self.wqueue.task_done()
                continue
            status, info, code = check(docname)
            if status == 'rate-limited':
                logger.info(darkgray('-rate limited-   ') + uri + darkgray(' | sleeping...'))
            else:
                self.rqueue.put((uri, docname, lineno, status, info, code))
            self.wqueue.task_done()

    def limit_rate(self, response: Response) -> Optional[float]:
        next_check = None
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                # Integer: time to wait before next attempt.
                delay = float(retry_after)
            except ValueError:
                try:
                    # An HTTP-date: time of next attempt.
                    until = parsedate_to_datetime(retry_after)
                except (TypeError, ValueError):
                    # TypeError: Invalid date format.
                    # ValueError: Invalid date, e.g. Oct 52th.
                    pass
                else:
                    next_check = datetime.timestamp(until)
                    delay = (until - datetime.now(timezone.utc)).total_seconds()
            else:
                next_check = time.time() + delay
        netloc = urlparse(response.url).netloc
        if next_check is None:
            max_delay = self.app.config.linkcheck_rate_limit_timeout
            try:
                rate_limit = self.rate_limits[netloc]
            except KeyError:
                delay = DEFAULT_DELAY
            else:
                last_wait_time = rate_limit.delay
                delay = 2.0 * last_wait_time
                if delay > max_delay and last_wait_time < max_delay:
                    delay = max_delay
            if delay > max_delay:
                return None
            next_check = time.time() + delay
        self.rate_limits[netloc] = RateLimit(delay, next_check)
        return next_check

    def process_result(self, result: Tuple[str, str, int, str, str, int]) -> None:
        uri, docname, lineno, status, info, code = result

        filename = self.env.doc2path(docname, None)
        linkstat = dict(filename=filename, lineno=lineno,
                        status=status, code=code, uri=uri,
                        info=info)
        if status == 'unchecked':
            self.write_linkstat(linkstat)
            return
        if status == 'working' and info == 'old':
            self.write_linkstat(linkstat)
            return
        if lineno:
            logger.info('(line %4d) ', lineno, nonl=True)
        if status == 'ignored':
            if info:
                logger.info(darkgray('-ignored- ') + uri + ': ' + info)
            else:
                logger.info(darkgray('-ignored- ') + uri)
            self.write_linkstat(linkstat)
        elif status == 'local':
            logger.info(darkgray('-local-   ') + uri)
            self.write_entry('local', docname, filename, lineno, uri)
            self.write_linkstat(linkstat)
        elif status == 'working':
            logger.info(darkgreen('ok        ') + uri + info)
            self.write_linkstat(linkstat)
        elif status == 'broken':
            if self.app.quiet or self.app.warningiserror:
                logger.warning(__('broken link: %s (%s)'), uri, info,
                               location=(filename, lineno))
            else:
                logger.info(red('broken    ') + uri + red(' - ' + info))
            self.write_entry('broken', docname, filename, lineno, uri + ': ' + info)
            self.write_linkstat(linkstat)
        elif status == 'redirected':
            try:
                text, color = {
                    301: ('permanently', purple),
                    302: ('with Found', purple),
                    303: ('with See Other', purple),
                    307: ('temporarily', turquoise),
                    308: ('permanently', purple),
                }[code]
            except KeyError:
                text, color = ('with unknown code', purple)
            linkstat['text'] = text
            logger.info(color('redirect  ') + uri + color(' - ' + text + ' to ' + info))
            self.write_entry('redirected ' + text, docname, filename,
                             lineno, uri + ' to ' + info)
            self.write_linkstat(linkstat)

    def get_target_uri(self, docname: str, typ: str = None) -> str:
        return ''

    def get_outdated_docs(self) -> Set[str]:
        return self.env.found_docs

    def prepare_writing(self, docnames: Set[str]) -> None:
        return

    def write_doc(self, docname: str, doctree: Node) -> None:
        logger.info('')
        n = 0

        # reference nodes
        for refnode in doctree.traverse(nodes.reference):
            if 'refuri' not in refnode:
                continue
            uri = refnode['refuri']
            lineno = node_line_or_0(refnode)
            uri_info = (CHECK_IMMEDIATELY, uri, docname, lineno)
            self.wqueue.put(uri_info, False)
            n += 1

        # image nodes
        for imgnode in doctree.traverse(nodes.image):
            uri = imgnode['candidates'].get('?')
            if uri and '://' in uri:
                lineno = node_line_or_0(imgnode)
                uri_info = (CHECK_IMMEDIATELY, uri, docname, lineno)
                self.wqueue.put(uri_info, False)
                n += 1

        done = 0
        while done < n:
            self.process_result(self.rqueue.get())
            done += 1

        if self.broken:
            self.app.statuscode = 1

    def write_entry(self, what: str, docname: str, filename: str, line: int,
                    uri: str) -> None:
        with open(path.join(self.outdir, 'output.txt'), 'a') as output:
            output.write("%s:%s: [%s] %s\n" % (filename, line, what, uri))

    def write_linkstat(self, data: dict) -> None:
        with open(path.join(self.outdir, 'output.json'), 'a') as output:
            output.write(json.dumps(data))
            output.write('\n')

    def finish(self) -> None:
        self.wqueue.join()
        # Shutdown threads.
        for worker in self.workers:
            self.wqueue.put((CHECK_IMMEDIATELY, None, None, None), False)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_builder(CheckExternalLinksBuilder)

    app.add_config_value('linkcheck_ignore', [], None)
    app.add_config_value('linkcheck_auth', [], None)
    app.add_config_value('linkcheck_request_headers', {}, None)
    app.add_config_value('linkcheck_retries', 1, None)
    app.add_config_value('linkcheck_timeout', None, None, [int])
    app.add_config_value('linkcheck_workers', 5, None)
    app.add_config_value('linkcheck_anchors', True, None)
    # Anchors starting with ! are ignored since they are
    # commonly used for dynamic pages
    app.add_config_value('linkcheck_anchors_ignore', ["^!"], None)
    app.add_config_value('linkcheck_rate_limit_timeout', 300.0, None)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
