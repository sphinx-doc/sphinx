# -*- coding: utf-8 -*-
"""
    sphinx.builders.linkcheck
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The CheckExternalLinksBuilder class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import Queue
import socket
import threading
from os import path
from urllib2 import build_opener, Request

from docutils import nodes

from sphinx.builders import Builder
from sphinx.util.console import purple, red, darkgreen, darkgray

# create an opener that will simulate a browser user-agent
opener = build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


class HeadRequest(Request):
    """Subclass of urllib2.Request that sends a HEAD request."""
    def get_method(self):
        return 'HEAD'


class CheckExternalLinksBuilder(Builder):
    """
    Checks for broken external links.
    """
    name = 'linkcheck'

    def init(self):
        self.to_ignore = map(re.compile, self.app.config.linkcheck_ignore)
        self.good = set()
        self.broken = {}
        self.redirected = {}
        # set a timeout for non-responding servers
        socket.setdefaulttimeout(5.0)
        # create output file
        open(path.join(self.outdir, 'output.txt'), 'w').close()

        # create queues and worker threads
        self.wqueue = Queue.Queue()
        self.rqueue = Queue.Queue()
        self.workers = []
        for i in range(self.app.config.linkcheck_workers):
            thread = threading.Thread(target=self.check_thread)
            thread.setDaemon(True)
            thread.start()
            self.workers.append(thread)

    def check_thread(self):
        kwargs = {}
        if sys.version_info > (2, 5) and self.app.config.linkcheck_timeout:
            kwargs['timeout'] = self.app.config.linkcheck_timeout

        def check():
            # check for various conditions without bothering the network
            if len(uri) == 0 or uri[0:7] == 'mailto:' or uri[0:4] == 'ftp:':
                return 'unchecked', ''
            elif not (uri[0:5] == 'http:' or uri[0:6] == 'https:'):
                return 'local', ''
            elif uri in self.good:
                return 'working', ''
            elif uri in self.broken:
                return 'broken', self.broken[uri]
            elif uri in self.redirected:
                return 'redirected', self.redirected[uri]
            for rex in self.to_ignore:
                if rex.match(uri):
                    return 'ignored', ''

            # need to actually check the URI
            try:
                f = opener.open(HeadRequest(uri), **kwargs)
                f.close()
            except Exception, err:
                self.broken[uri] = str(err)
                return 'broken', str(err)
            if f.url.rstrip('/') == uri.rstrip('/'):
                self.good.add(uri)
                return 'working', 'new'
            else:
                self.redirected[uri] = f.url
                return 'redirected', f.url

        while True:
            uri, docname, lineno = self.wqueue.get()
            if uri is None:
                break
            status, info = check()
            self.rqueue.put((uri, docname, lineno, status, info))

    def process_result(self, result):
        uri, docname, lineno, status, info = result
        if status == 'unchecked':
            return
        if status == 'working' and info != 'new':
            return
        if lineno:
            self.info('(line %3d) ' % lineno, nonl=1)
        if status == 'ignored':
            self.info(uri + ' - ' + darkgray('ignored'))
        elif status == 'local':
            self.info(uri + ' - ' + darkgray('local'))
            self.write_entry('local', docname, lineno, uri)
        elif status == 'working':
            self.info(uri + ' - ' + darkgreen('working'))
        elif status == 'broken':
            self.info(uri + ' - ' + red('broken: ') + info)
            self.write_entry('broken', docname, lineno, uri + ': ' + info)
            if self.app.quiet:
                self.warn('broken link: %s' % uri,
                          '%s:%s' % (self.env.doc2path(docname), lineno))
        elif status == 'redirected':
            self.info(uri + ' - ' + purple('redirected') + ' to ' + info)
            self.write_entry('redirected', docname, lineno, uri + ' to ' + info)

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
            if '#' in uri:
                uri = uri.split('#')[0]
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
        output = open(path.join(self.outdir, 'output.txt'), 'a')
        output.write("%s:%s: [%s] %s\n" % (self.env.doc2path(docname, None),
                                           line, what, uri))
        output.close()

    def finish(self):
        for worker in self.workers:
            self.wqueue.put((None, None, None), False)
