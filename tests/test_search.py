# -*- coding: utf-8 -*-
"""
    test_search
    ~~~~~~~~~~~

    Test the search index builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import namedtuple

import pytest
from docutils import frontend, utils
from docutils.parsers import rst
from six import BytesIO

from sphinx.search import IndexBuilder
from sphinx.util import jsdump

DummyEnvironment = namedtuple('DummyEnvironment', ['version', 'domains'])


class DummyDomain(object):
    def __init__(self, data):
        self.data = data
        self.object_types = {}

    def get_objects(self):
        return self.data


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
section_title
=============

.. test that comments are not indexed: boson

test that non-comments are indexed: fermion
'''


@pytest.mark.sphinx(testroot='ext-viewcode')
def test_objects_are_escaped(app, status, warning):
    app.builder.build_all()
    searchindex = (app.outdir / 'searchindex.js').text()
    assert searchindex.startswith('Search.setIndex(')

    index = jsdump.loads(searchindex[16:-2])
    assert 'n::Array&lt;T, d&gt;' in index.get('objects').get('')  # n::Array<T,d> is escaped


@pytest.mark.sphinx(testroot='search')
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


@pytest.mark.sphinx(testroot='search', confoverrides={'html_search_language': 'de'})
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


@pytest.mark.sphinx(testroot='search')
def test_stemmer_does_not_remove_short_words(app, status, warning):
    app.builder.build_all()
    searchindex = (app.outdir / 'searchindex.js').text()
    assert 'zfs' in searchindex


@pytest.mark.sphinx(testroot='search')
def test_stemmer(app, status, warning):
    searchindex = jsload(app.outdir / 'searchindex.js')
    print(searchindex)
    assert is_registered_term(searchindex, 'findthisstemmedkei')
    assert is_registered_term(searchindex, 'intern')


@pytest.mark.sphinx(testroot='search')
def test_term_in_heading_and_section(app, status, warning):
    searchindex = (app.outdir / 'searchindex.js').text()
    # if search term is in the title of one doc and in the text of another
    # both documents should be a hit in the search index as a title,
    # respectively text hit
    assert 'textinhead:1' in searchindex
    assert 'textinhead:0' in searchindex


@pytest.mark.sphinx(testroot='search')
def test_term_in_raw_directive(app, status, warning):
    searchindex = jsload(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'raw')
    assert is_registered_term(searchindex, 'rawword')
    assert not is_registered_term(searchindex, 'latex_keyword')


def test_IndexBuilder():
    domain = DummyDomain([('objname', 'objdispname', 'objtype', 'docname', '#anchor', 1),
                          ('objname2', 'objdispname2', 'objtype2', 'docname2', '', -1)])
    env = DummyEnvironment('1.0', {'dummy': domain})
    doc = utils.new_document(b'test data', settings)
    doc['file'] = 'dummy'
    parser.parse(FILE_CONTENTS, doc)

    # feed
    index = IndexBuilder(env, 'en', {}, None)
    index.feed('docname', 'filename', 'title', doc)
    index.feed('docname2', 'filename2', 'title2', doc)
    assert index._titles == {'docname': 'title', 'docname2': 'title2'}
    assert index._filenames == {'docname': 'filename', 'docname2': 'filename2'}
    assert index._mapping == {
        'fermion': {'docname', 'docname2'},
        'comment': {'docname', 'docname2'},
        'non': {'docname', 'docname2'},
        'index': {'docname', 'docname2'},
        'test': {'docname', 'docname2'}
    }
    assert index._title_mapping == {'section_titl': {'docname', 'docname2'}}
    assert index._objtypes == {}
    assert index._objnames == {}

    # freeze
    assert index.freeze() == {
        'docnames': ('docname', 'docname2'),
        'envversion': '1.0',
        'filenames': ['filename', 'filename2'],
        'objects': {'': {'objdispname': (0, 0, 1, '#anchor')}},
        'objnames': {0: ('dummy', 'objtype', 'objtype')},
        'objtypes': {0: 'dummy:objtype'},
        'terms': {'comment': [0, 1],
                  'fermion': [0, 1],
                  'index': [0, 1],
                  'non': [0, 1],
                  'test': [0, 1]},
        'titles': ('title', 'title2'),
        'titleterms': {'section_titl': [0, 1]}
    }
    assert index._objtypes == {('dummy', 'objtype'): 0}
    assert index._objnames == {0: ('dummy', 'objtype', 'objtype')}

    # dump / load
    stream = BytesIO()
    index.dump(stream, 'pickle')
    stream.seek(0)

    index2 = IndexBuilder(env, 'en', {}, None)
    index2.load(stream, 'pickle')

    assert index2._titles == index._titles
    assert index2._filenames == index._filenames
    assert index2._mapping == index._mapping
    assert index2._title_mapping == index._title_mapping
    assert index2._objtypes == {}
    assert index2._objnames == {}

    # freeze after load
    assert index2.freeze() == index.freeze()
    assert index2._objtypes == index._objtypes
    assert index2._objnames == index._objnames

    # prune
    index.prune(['docname2'])
    assert index._titles == {'docname2': 'title2'}
    assert index._filenames == {'docname2': 'filename2'}
    assert index._mapping == {
        'fermion': {'docname2'},
        'comment': {'docname2'},
        'non': {'docname2'},
        'index': {'docname2'},
        'test': {'docname2'}
    }
    assert index._title_mapping == {'section_titl': {'docname2'}}
    assert index._objtypes == {('dummy', 'objtype'): 0}
    assert index._objnames == {0: ('dummy', 'objtype', 'objtype')}

    # freeze after prune
    assert index.freeze() == {
        'docnames': ('docname2',),
        'envversion': '1.0',
        'filenames': ['filename2'],
        'objects': {},
        'objnames': {0: ('dummy', 'objtype', 'objtype')},
        'objtypes': {0: 'dummy:objtype'},
        'terms': {'comment': 0,
                  'fermion': 0,
                  'index': 0,
                  'non': 0,
                  'test': 0},
        'titles': ('title2',),
        'titleterms': {'section_titl': 0}
    }
    assert index._objtypes == {('dummy', 'objtype'): 0}
    assert index._objnames == {0: ('dummy', 'objtype', 'objtype')}


def test_IndexBuilder_lookup():
    env = DummyEnvironment('1.0', {})

    # zh
    index = IndexBuilder(env, 'zh', {}, None)
    assert index.lang.lang == 'zh'

    # zh_CN
    index = IndexBuilder(env, 'zh_CN', {}, None)
    assert index.lang.lang == 'zh'
