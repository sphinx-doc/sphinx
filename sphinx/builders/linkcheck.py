# -*- coding: utf-8 -*-
"""
    sphinx.builders.linkcheck
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The CheckExternalLinksBuilder class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import socket
from os import path
from urllib2 import build_opener, HTTPError

from docutils import nodes

from sphinx.builders import Builder
from sphinx.util.console import purple, red, darkgreen, darkgray

# create an opener that will simulate a browser user-agent
opener = build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


class CheckExternalLinksBuilder(Builder):
    """
    Checks for broken external links.
    """
    name = 'linkcheck'

    def init(self):
        self.good = set()
        self.broken = {}
        self.redirected = {}
        # set a timeout for non-responding servers
        socket.setdefaulttimeout(5.0)
        # create output file
        open(path.join(self.outdir, 'output.txt'), 'w').close()

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        self.info()
        for node in doctree.traverse(nodes.reference):
            try:
                self.check(node, docname)
            except KeyError:
                continue

    def check(self, node, docname):
        uri = node['refuri']

        if '#' in uri:
            uri = uri.split('#')[0]

        if uri in self.good:
            return

        lineno = None
        while lineno is None:
            node = node.parent
            if node is None:
                break
            lineno = node.line

        if len(uri) == 0 or uri[0:7] == 'mailto:' or uri[0:4] == 'ftp:':
            return

        if lineno:
            self.info('(line %3d) ' % lineno, nonl=1)
        if uri[0:5] == 'http:' or uri[0:6] == 'https:':
            self.info(uri, nonl=1)

            if uri in self.broken:
                (r, s) = self.broken[uri]
            elif uri in self.redirected:
                (r, s) = self.redirected[uri]
            else:
                (r, s) = self.resolve(uri)

            if r == 0:
                self.info(' - ' + darkgreen('working'))
                self.good.add(uri)
            elif r == 2:
                self.info(' - ' + red('broken: ') + s)
                self.write_entry('broken', docname, lineno, uri + ': ' + s)
                self.broken[uri] = (r, s)
                if self.app.quiet:
                    self.warn('broken link: %s' % uri,
                              '%s:%s' % (self.env.doc2path(docname), lineno))
            else:
                self.info(' - ' + purple('redirected') + ' to ' + s)
                self.write_entry('redirected', docname,
                                 lineno, uri + ' to ' + s)
                self.redirected[uri] = (r, s)
        else:
            self.info(uri + ' - ' + darkgray('local'))
            self.write_entry('local', docname, lineno, uri)

        if self.broken:
            self.app.statuscode = 1

    def write_entry(self, what, docname, line, uri):
        output = open(path.join(self.outdir, 'output.txt'), 'a')
        output.write("%s:%s: [%s] %s\n" % (self.env.doc2path(docname, None),
                                           line, what, uri))
        output.close()

    def resolve(self, uri):
        try:
            f = opener.open(uri)
            f.close()
        except HTTPError, err:
            #if err.code == 403 and uri.startswith('http://en.wikipedia.org/'):
            #    # Wikipedia blocks requests from urllib User-Agent
            #    return (0, 0)
            return (2, str(err))
        except Exception, err:
            return (2, str(err))
        if f.url.rstrip('/') == uri.rstrip('/'):
            return (0, 0)
        else:
            return (1, f.url)

    def finish(self):
        return
