# -*- coding: utf-8 -*-
"""
    sphinx.websupport.search
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Server side search support for the web support package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

class BaseSearch(object):
    def create_index(self, path):
        raise NotImplemented

    def feed(self, pagename, title, doctree):
        self.add_document(pagename, title, doctree.astext())

    def add_document(self, path, title, text):
        raise NotImplemented

    def prune(self, keep):
        raise NotImplemented

    def query(self, q):
        self.context_re = re.compile(q, re.I)
        return self.handle_query(q)

    def handle_query(self, q):
        raise NotImplemented

    def extract_context(self, text, query_string):
        res = self.context_re.search(text)
        start = max(res.start() - 120, 0)
        end = start + 240
        context = ['...' if start > 0 else '',
                   text[start:end],
                   '...' if end < len(text) else '']
        return ''.join(context)
    
search_adapters = {
    'xapian': ('xapiansearch', 'XapianSearch'),
    'whoosh': ('whooshsearch', 'WhooshSearch'),
    }
