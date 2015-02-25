# -*- coding: utf-8 -*-
"""
    sphinx.builders.linkcheck
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The CheckExternalLinksBuilder class.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import socket
import codecs
import threading
from os import path

from six.moves import queue
from six.moves.urllib.request import build_opener, Request, HTTPRedirectHandler
from six.moves.urllib.parse import unquote, urlsplit, quote
from six.moves.urllib.error import HTTPError
from six.moves.html_parser import HTMLParser, HTMLParseError
from docutils import nodes

from sphinx.builders import Builder
from sphinx.util.console import purple, red, darkgreen, darkgray, \
    darkred, turquoise
from sphinx.util.pycompat import TextIOWrapper


class RedirectHandler(HTTPRedirectHandler):
    """A RedirectHandler that records the redirect code we got."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = HTTPRedirectHandler.redirect_request(self, req, fp, code,
                                                       msg, headers, newurl)
        req.redirect_code = code
        return new_req

# create an opener that will simulate a browser user-agent
opener = build_opener(RedirectHandler)
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) '
                      'Gecko/20100101 Firefox/25.0')]


class HeadRequest(Request):
    """Subclass of urllib2.Request that sends a HEAD request."""
    def get_method(self):
        return 'HEAD'


class AnchorCheckParser(HTMLParser):
    """Specialized HTML parser that looks for a specific anchor."""

    def __init__(self, search_anchor):
        HTMLParser.__init__(self)

        self.search_anchor = search_anchor
        self.found = False

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('id', 'name') and value == self.search_anchor:
                self.found = True


def check_anchor(f, hash):
    """Reads HTML data from a filelike object 'f' searching for anchor 'hash'.
    Returns True if anchor was found, False otherwise.
    """
    parser = AnchorCheckParser(hash)
    try:
        # Read file in chunks of 8192 bytes. If we find a matching anchor, we
        # break the loop early in hopes not to have to download the whole thing.
        chunk = f.read(8192)
        while chunk and not parser.found:
            parser.feed(chunk)
            chunk = f.read(8192)
        parser.close()
    except HTMLParseError:
        # HTMLParser is usually pretty good with sloppy HTML, but it tends to
        # choke on EOF. But we're done then anyway.
        pass
    return parser.found


class CheckExternalLinksBuilder(Builder):
    """
    Checks for broken external links.
    """
    name = 'linkcheck'

    def init(self):
        self.to_ignore = [re.compile(x) for x in self.app.config.linkcheck_ignore]
        self.good = set()
        self.broken = {}
        self.redirected = {}
        # set a timeout for non-responding servers
        socket.setdefaulttimeout(5.0)
        # create output file
        open(path.join(self.outdir, 'output.txt'), 'w').close()

        # create queues and worker threads
        self.wqueue = queue.Queue()
        self.rqueue = queue.Queue()
        self.workers = []
        for i in range(self.app.config.linkcheck_workers):
            thread = threading.Thread(target=self.check_thread)
            thread.setDaemon(True)
            thread.start()
            self.workers.append(thread)

    def check_thread(self):
        kwargs = {}
        if self.app.config.linkcheck_timeout:
            kwargs['timeout'] = self.app.config.linkcheck_timeout

        def check():
            # check for various conditions without bothering the network
            if len(uri) == 0 or uri[0] == '#' or \
               uri[0:7] == 'mailto:' or uri[0:4] == 'ftp:':
                return 'unchecked', '', 0
            elif not (uri[0:5] == 'http:' or uri[0:6] == 'https:'):
                return 'local', '', 0
            elif uri in self.good:
                return 'working', 'old', 0
            elif uri in self.broken:
                return 'broken', self.broken[uri], 0
            elif uri in self.redirected:
                return 'redirected', self.redirected[uri][0], self.redirected[uri][1]
            for rex in self.to_ignore:
                if rex.match(uri):
                    return 'ignored', '', 0

            # split off anchor
            if '#' in uri:
                req_url, hash = uri.split('#', 1)
            else:
                req_url = uri
                hash = None

            # handle non-ASCII URIs
            try:
                req_url.encode('ascii')
            except UnicodeError:
                split = urlsplit(req_url)
                req_url = (split[0].encode() + '://' +       # scheme
                           split[1].encode('idna') +         # netloc
                           quote(split[2].encode('utf-8')))  # path
                if split[3]:  # query
                    req_url += '?' + quote(split[3].encode('utf-8'))
                # go back to Unicode strings which is required by Python 3
                # (but now all parts are pure ascii)
                req_url = req_url.decode('ascii')

            # need to actually check the URI
            try:
                if hash and self.app.config.linkcheck_anchors:
                    # Read the whole document and see if #hash exists
                    req = Request(req_url)
                    f = opener.open(req, **kwargs)
                    encoding = 'utf-8'
                    if hasattr(f.headers, 'get_content_charset'):
                        encoding = f.headers.get_content_charset() or encoding
                    found = check_anchor(TextIOWrapper(f, encoding), unquote(hash))
                    f.close()

                    if not found:
                        raise Exception("Anchor '%s' not found" % hash)
                else:
                    try:
                        # try a HEAD request, which should be easier on
                        # the server and the network
                        req = HeadRequest(req_url)
                        f = opener.open(req, **kwargs)
                        f.close()
                    except HTTPError as err:
                        if err.code != 405:
                            raise
                        # retry with GET if that fails, some servers
                        # don't like HEAD requests and reply with 405
                        req = Request(req_url)
                        f = opener.open(req, **kwargs)
                        f.close()
            except HTTPError as err:
                if err.code == 401:
                    # We'll take "Unauthorized" as working.
                    self.good.add(uri)
                    return 'working', ' - unauthorized', 0
                else:
                    self.broken[uri] = str(err)
                    return 'broken', str(err), 0
            except Exception as err:
                self.broken[uri] = str(err)
                return 'broken', str(err), 0
            if f.url.rstrip('/') == req_url.rstrip('/'):
                self.good.add(uri)
                return 'working', '', 0
            else:
                new_url = f.url
                if hash:
                    new_url += '#' + hash
                code = getattr(req, 'redirect_code', 0)
                self.redirected[uri] = (new_url, code)
                return 'redirected', new_url, code

        while True:
            uri, docname, lineno = self.wqueue.get()
            if uri is None:
                break
            status, info, code = check()
            self.rqueue.put((uri, docname, lineno, status, info, code))

    def process_result(self, result):
        uri, docname, lineno, status, info, code = result
        if status == 'unchecked':
            return
        if status == 'working' and info == 'old':
            return
        if lineno:
            self.info('(line %4d) ' % lineno, nonl=1)
        if status == 'ignored':
            self.info(darkgray('-ignored- ') + uri)
        elif status == 'local':
            self.info(darkgray('-local-   ') + uri)
            self.write_entry('local', docname, lineno, uri)
        elif status == 'working':
            self.info(darkgreen('ok        ')  + uri + info)
        elif status == 'broken':
            self.info(red('broken    ') + uri + red(' - ' + info))
            self.write_entry('broken', docname, lineno, uri + ': ' + info)
            if self.app.quiet:
                self.warn('broken link: %s' % uri,
                          '%s:%s' % (self.env.doc2path(docname), lineno))
        elif status == 'redirected':
            text, color = {
                301: ('permanently', darkred),
                302: ('with Found', purple),
                303: ('with See Other', purple),
                307: ('temporarily', turquoise),
                0:   ('with unknown code', purple),
            }[code]
            self.write_entry('redirected ' + text, docname, lineno,
                             uri + ' to ' + info)
            self.info(color('redirect  ') + uri + color(' - ' + text + ' to '  + info))

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        self.info()
        n = 0
        for node in doctree.traverse(nodes.reference):
            if 'refuri' not in node:
                continue
            uri = node['refuri']
            lineno = None
            while lineno is None:
                node = node.parent
                if node is None:
                    break
                lineno = node.line
            self.wqueue.put((uri, docname, lineno), False)
            n += 1
        done = 0
        while done < n:
            self.process_result(self.rqueue.get())
            done += 1

        if self.broken:
            self.app.statuscode = 1

    def write_entry(self, what, docname, line, uri):
        output = codecs.open(path.join(self.outdir, 'output.txt'), 'a', 'utf-8')
        output.write("%s:%s: [%s] %s\n" % (self.env.doc2path(docname, None),
                                           line, what, uri))
        output.close()

    def finish(self):
        for worker in self.workers:
            self.wqueue.put((None, None, None), False)
