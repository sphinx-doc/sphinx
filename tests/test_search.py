# -*- coding: utf-8 -*-
"""
    test_search
    ~~~~~~~~~~~

    Test the search index builder.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os

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


def jsload(path):
    searchindex = path.text()
    assert searchindex.startswith('Search.setIndex(')

    return jsdump.loads(searchindex[16:-2])


def is_registered_term(index, keyword):
    return index['terms'].get(keyword, []) != []


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


@with_app(testroot='search')
def test_meta_keys_are_handled_for_language_en(app, status, warning):
    app.builder.build_all()
    searchindex = jsload(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'thisnoteith')
    assert is_registered_term(searchindex, 'thisonetoo')
    assert is_registered_term(searchindex, 'findthiskei')
    assert is_registered_term(searchindex, 'thistoo')
    assert not is_registered_term(searchindex, 'onlygerman')
    assert is_registered_term(searchindex, 'notgerman')
    assert not is_registered_term(searchindex, 'onlytoogerman')


@with_app(testroot='search', confoverrides={'html_search_language': 'de'})
def test_meta_keys_are_handled_for_language_de(app, status, warning):
    app.builder.build_all()
    searchindex = jsload(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'thisnoteith')
    assert is_registered_term(searchindex, 'thisonetoo')
    assert not is_registered_term(searchindex, 'findthiskei')
    assert not is_registered_term(searchindex, 'thistoo')
    assert is_registered_term(searchindex, 'onlygerman')
    assert not is_registered_term(searchindex, 'notgerman')
    assert is_registered_term(searchindex, 'onlytoogerman')
