"""Test the search index builder."""

import json
import warnings
from collections import namedtuple
from io import BytesIO

import pytest
from docutils import frontend, utils
from docutils.parsers import rst

from sphinx.search import IndexBuilder


class DummyEnvironment(namedtuple('DummyEnvironment', ['version', 'domains'])):
    def __getattr__(self, name):
        if name.startswith('_search_index_'):
            setattr(self, name, {})
        return getattr(self, name, {})


class DummyDomain:
    def __init__(self, data):
        self.data = data
        self.object_types = {}

    def get_objects(self):
        return self.data


settings = parser = None


def setup_module():
    global settings, parser
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        # DeprecationWarning: The frontend.OptionParser class will be replaced
        # by a subclass of argparse.ArgumentParser in Docutils 0.21 or later.
        optparser = frontend.OptionParser(components=(rst.Parser,))
    settings = optparser.get_default_values()
    parser = rst.Parser()


def load_searchindex(path):
    searchindex = path.read_text(encoding='utf8')
    assert searchindex.startswith('Search.setIndex(')
    assert searchindex.endswith(')')

    return json.loads(searchindex[16:-1])


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
    index = load_searchindex(app.outdir / 'searchindex.js')
    for item in index.get('objects').get(''):
        if item[-1] == 'n::Array&lt;T, d&gt;':  # n::Array<T,d> is escaped
            break
    else:
        raise AssertionError(index.get('objects').get(''))


@pytest.mark.sphinx(testroot='search')
def test_meta_keys_are_handled_for_language_en(app, status, warning):
    app.builder.build_all()
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
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
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
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
    searchindex = (app.outdir / 'searchindex.js').read_text(encoding='utf8')
    assert 'zfs' in searchindex


@pytest.mark.sphinx(testroot='search')
def test_stemmer(app, status, warning):
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    print(searchindex)
    assert is_registered_term(searchindex, 'findthisstemmedkei')
    assert is_registered_term(searchindex, 'intern')


@pytest.mark.sphinx(testroot='search')
def test_term_in_heading_and_section(app, status, warning):
    searchindex = (app.outdir / 'searchindex.js').read_text(encoding='utf8')
    # if search term is in the title of one doc and in the text of another
    # both documents should be a hit in the search index as a title,
    # respectively text hit
    assert '"textinhead": 2' in searchindex
    assert '"textinhead": 0' in searchindex


@pytest.mark.sphinx(testroot='search')
def test_term_in_raw_directive(app, status, warning):
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'raw')
    assert is_registered_term(searchindex, 'rawword')
    assert not is_registered_term(searchindex, 'latex_keyword')


def test_IndexBuilder():
    domain1 = DummyDomain([('objname1', 'objdispname1', 'objtype1', 'docname1_1', '#anchor', 1),
                          ('objname2', 'objdispname2', 'objtype2', 'docname1_2', '', -1)])
    domain2 = DummyDomain([('objname1', 'objdispname1', 'objtype1', 'docname2_1', '#anchor', 1),
                           ('objname2', 'objdispname2', 'objtype2', 'docname2_2', '', -1)])
    env = DummyEnvironment('1.0', {'dummy1': domain1, 'dummy2': domain2})
    doc = utils.new_document(b'test data', settings)
    doc['file'] = 'dummy'
    parser.parse(FILE_CONTENTS, doc)

    # feed
    index = IndexBuilder(env, 'en', {}, None)
    index.feed('docname1_1', 'filename1_1', 'title1_1', doc)
    index.feed('docname1_2', 'filename1_2', 'title1_2', doc)
    index.feed('docname2_1', 'filename2_1', 'title2_1', doc)
    index.feed('docname2_2', 'filename2_2', 'title2_2', doc)
    assert index._titles == {'docname1_1': 'title1_1', 'docname1_2': 'title1_2',
                             'docname2_1': 'title2_1', 'docname2_2': 'title2_2'}
    assert index._filenames == {'docname1_1': 'filename1_1', 'docname1_2': 'filename1_2',
                                'docname2_1': 'filename2_1', 'docname2_2': 'filename2_2'}
    assert index._mapping == {
        'ar': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'fermion': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'comment': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'non': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'index': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'test': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
    }
    assert index._title_mapping == {'section_titl': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'}}
    assert index._objtypes == {}
    assert index._objnames == {}

    # freeze
    assert index.freeze() == {
        'docnames': ('docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'),
        'envversion': '1.0',
        'filenames': ['filename1_1', 'filename1_2', 'filename2_1', 'filename2_2'],
        'objects': {'': [(0, 0, 1, '#anchor', 'objdispname1'),
                         (2, 1, 1, '#anchor', 'objdispname1')]},
        'objnames': {0: ('dummy1', 'objtype1', 'objtype1'), 1: ('dummy2', 'objtype1', 'objtype1')},
        'objtypes': {0: 'dummy1:objtype1', 1: 'dummy2:objtype1'},
        'terms': {'ar': [0, 1, 2, 3],
                  'comment': [0, 1, 2, 3],
                  'fermion': [0, 1, 2, 3],
                  'index': [0, 1, 2, 3],
                  'non': [0, 1, 2, 3],
                  'test': [0, 1, 2, 3]},
        'titles': ('title1_1', 'title1_2', 'title2_1', 'title2_2'),
        'titleterms': {'section_titl': [0, 1, 2, 3]},
        'alltitles': {'section_title': [(0, 'section-title'), (1, 'section-title'), (2, 'section-title'), (3, 'section-title')]},
        'indexentries': {},
    }
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {0: ('dummy1', 'objtype1', 'objtype1'),
                               1: ('dummy2', 'objtype1', 'objtype1')}

    env = DummyEnvironment('1.0', {'dummy1': domain1, 'dummy2': domain2})

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
    index.prune(['docname1_2', 'docname2_2'])
    assert index._titles == {'docname1_2': 'title1_2', 'docname2_2': 'title2_2'}
    assert index._filenames == {'docname1_2': 'filename1_2', 'docname2_2': 'filename2_2'}
    assert index._mapping == {
        'ar': {'docname1_2', 'docname2_2'},
        'fermion': {'docname1_2', 'docname2_2'},
        'comment': {'docname1_2', 'docname2_2'},
        'non': {'docname1_2', 'docname2_2'},
        'index': {'docname1_2', 'docname2_2'},
        'test': {'docname1_2', 'docname2_2'},
    }
    assert index._title_mapping == {'section_titl': {'docname1_2', 'docname2_2'}}
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {0: ('dummy1', 'objtype1', 'objtype1'), 1: ('dummy2', 'objtype1', 'objtype1')}

    # freeze after prune
    assert index.freeze() == {
        'docnames': ('docname1_2', 'docname2_2'),
        'envversion': '1.0',
        'filenames': ['filename1_2', 'filename2_2'],
        'objects': {},
        'objnames': {0: ('dummy1', 'objtype1', 'objtype1'), 1: ('dummy2', 'objtype1', 'objtype1')},
        'objtypes': {0: 'dummy1:objtype1', 1: 'dummy2:objtype1'},
        'terms': {'ar': [0, 1],
                  'comment': [0, 1],
                  'fermion': [0, 1],
                  'index': [0, 1],
                  'non': [0, 1],
                  'test': [0, 1]},
        'titles': ('title1_2', 'title2_2'),
        'titleterms': {'section_titl': [0, 1]},
        'alltitles': {'section_title': [(0, 'section-title'), (1, 'section-title')]},
        'indexentries': {},
    }
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {0: ('dummy1', 'objtype1', 'objtype1'),
                               1: ('dummy2', 'objtype1', 'objtype1')}


def test_IndexBuilder_lookup():
    env = DummyEnvironment('1.0', {})

    # zh
    index = IndexBuilder(env, 'zh', {}, None)
    assert index.lang.lang == 'zh'

    # zh_CN
    index = IndexBuilder(env, 'zh_CN', {}, None)
    assert index.lang.lang == 'zh'


@pytest.mark.sphinx(
    testroot='search',
    confoverrides={'html_search_language': 'zh'},
    srcdir='search_zh',
)
def test_search_index_gen_zh(app, status, warning):
    app.builder.build_all()
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert 'chinesetest ' not in index['terms']
    assert 'chinesetest' in index['terms']
    assert 'chinesetesttwo' in index['terms']
    assert 'cas' in index['terms']


@pytest.mark.sphinx(testroot='search')
def test_nosearch(app):
    app.build()
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert index['docnames'] == ['index', 'nosearch', 'tocitem']
    assert 'latex' not in index['terms']
    assert 'zfs' in index['terms']
    assert index['terms']['zfs'] == []  # zfs on nosearch.rst is not registered to index


@pytest.mark.sphinx(testroot='search', parallel=3, freshenv=True)
def test_parallel(app):
    app.build()
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert index['docnames'] == ['index', 'nosearch', 'tocitem']
