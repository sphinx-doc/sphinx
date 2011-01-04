# -*- coding: utf-8 -*-
"""
    test_search
    ~~~~~~~~~~~

    Test the search index builder.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import frontend, utils
from docutils.parsers import rst

from sphinx.search import IndexBuilder
from sphinx.util.pycompat import b


settings = parser = None

def setup_module():
    global settings, parser
    optparser = frontend.OptionParser(components=(rst.Parser,))
    settings = optparser.get_default_values()
    parser = rst.Parser()


FILE_CONTENTS = '''\
.. test that comments are not indexed: boson

test that non-comments are indexed: fermion
'''

def test_wordcollector():
    doc = utils.new_document(b('test data'), settings)
    doc['file'] = 'dummy'
    parser.parse(FILE_CONTENTS, doc)

    ix = IndexBuilder(None, 'en', {})
    ix.feed('filename', 'title', doc)
    assert 'boson' not in ix._mapping
    assert 'fermion' in ix._mapping
