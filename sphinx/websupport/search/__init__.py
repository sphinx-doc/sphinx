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

    def add_document(self, path, title, text):
        raise NotImplemented

    def query(self, q):
        raise NotImplemented

    def extract_context(self, text, query_string):
        # From GSOC 2009
        with_context_re = '([\W\w]{0,80})(%s)([\W\w]{0,80})' % (query_string)
        try:
            res = re.findall(with_context_re, text, re.I|re.U)[0]
            return tuple((unicode(i, errors='ignore') for i in res))
        except IndexError:
            return '', '', ''

search_adapters = {
    'xapian': ('xapiansearch', 'XapianSearch'),
    'whoosh': ('whooshsearch', 'WhooshSearch'),
    }
