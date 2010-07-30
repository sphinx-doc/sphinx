# -*- coding: utf-8 -*-
"""
    sphinx.websupport.search.nullsearch
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The default search adapter, does nothing.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.websupport.search import BaseSearch

class NullSearchException(Exception):
    pass

class NullSearch(BaseSearch):
    def feed(self, pagename, title, doctree):
        pass

    def query(self, q):
        raise NullSearchException('No search adapter specified.')
