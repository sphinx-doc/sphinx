# -*- coding: utf-8 -*-
"""
    test_search
    ~~~~~~~~~~~

    Test the search index builder.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import frontend, utils
from docutils.parsers import rst

from sphinx.search import IndexBuilder
from sphinx.util import jsdump

from util import with_app


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
    doc = utils.new_document(b'test data', settings)
    doc['file'] = 'dummy'
    parser.parse(FILE_CONTENTS, doc)

    ix = IndexBuilder(None, 'en', {}, None)
    ix.feed('filename', 'title', doc)
    assert 'boson' not in ix._mapping
    assert 'fermion' in ix._mapping


@with_app(testroot='ext-viewcode')
def test_objects_are_escaped(app, status, warning):
    app.builder.build_all()
    searchindex = (app.outdir / 'searchindex.js').text()
    assert searchindex.startswith('Search.setIndex(')

    index = jsdump.loads(searchindex[16:-2])
    assert 'n::Array&lt;T, d&gt;' in index.get('objects').get('')  # n::Array<T,d> is escaped

def assert_lang_agnostic_key_words(searchindex):
    assert 'findnotthiskey' not in searchindex
    assert 'thisnoteith' not in searchindex
    assert 'thistoo' in searchindex
    assert 'thisonetoo' in searchindex

@with_app(testroot='search')
def test_meta_keys_are_handled_for_language_en(app, status, warning):
    app.builder.build_all()
    searchindex = (app.outdir / 'searchindex.js').text()
    assert_lang_agnostic_key_words(searchindex)
    assert 'findthiskei' in searchindex

@with_app(testroot='search-de')
def test_meta_keys_are_handled_for_language_de(app, status, warning):
    app.builder.build_all()
    searchindex = (app.outdir / 'searchindex.js').text()
    assert_lang_agnostic_key_words(searchindex)
    assert 'findthiskey' in searchindex