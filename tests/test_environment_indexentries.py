"""
    test_environment_indexentries
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the sphinx.environment.managers.indexentries.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import namedtuple
from unittest import mock

from sphinx import locale
from sphinx.environment.adapters.indexentries import IndexEntries

Environment = namedtuple('Environment', 'indexentries')

dummy_builder = mock.Mock()
dummy_builder.get_relative_uri.return_value = ''


def test_create_single_index():
    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('single', 'docutils', 'id1', '', None),
            ('single', 'Python', 'id2', '', None),
            ('single', 'pip; install', 'id3', '', None),
            ('single', 'pip; upgrade', 'id4', '', None),
            ('single', 'Sphinx', 'id5', '', None),
            ('single', 'Ель', 'id6', '', None),
            ('single', 'ёлка', 'id7', '', None),
            ('single', '‏תירבע‎', 'id8', '', None),
            ('single', '9-symbol', 'id9', '', None),
            ('single', '&-symbol', 'id10', '', None),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 6
    assert index[0] == ('Symbols', [('&-symbol', [[('', '#id10')], [], None]),
                                    ('9-symbol', [[('', '#id9')], [], None])])
    assert index[1] == ('D', [('docutils', [[('', '#id1')], [], None])])
    assert index[2] == ('P', [('pip', [[], [('install', [('', '#id3')]),
                                            ('upgrade', [('', '#id4')])], None]),
                              ('Python', [[('', '#id2')], [], None])])
    assert index[3] == ('S', [('Sphinx', [[('', '#id5')], [], None])])
    assert index[4] == ('Е', [('ёлка', [[('', '#id7')], [], None]),
                               ('Ель', [[('', '#id6')], [], None])])
    assert index[5] == ('ת', [('‏תירבע‎', [[('', '#id8')], [], None])])


def test_create_pair_index():
    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('pair', 'docutils; reStructuredText', 'id1', '', None),
            ('pair', 'Python; interpreter', 'id2', '', None),
            ('pair', 'Sphinx; documentation tool', 'id3', '', None),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 5
    assert index[0] == ('D',
                        [('documentation tool', [[], [('Sphinx', [('', '#id3')])], None]),
                         ('docutils', [[], [('reStructuredText', [('', '#id1')])], None])])
    assert index[1] == ('I', [('interpreter', [[], [('Python', [('', '#id2')])], None])])
    assert index[2] == ('P', [('Python', [[], [('interpreter', [('', '#id2')])], None])])
    assert index[3] == ('R',
                        [('reStructuredText', [[], [('docutils', [('', '#id1')])], None])])
    assert index[4] == ('S',
                        [('Sphinx', [[], [('documentation tool', [('', '#id3')])], None])])


def test_create_triple_index():
    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('triple', 'foo; bar; baz', 'id1', '', None),
            ('triple', 'Python; Sphinx; reST', 'id2', '', None),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 5
    assert index[0] == ('B', [('bar', [[], [('baz, foo', [('', '#id1')])], None]),
                              ('baz', [[], [('foo bar', [('', '#id1')])], None])])
    assert index[1] == ('F', [('foo', [[], [('bar baz', [('', '#id1')])], None])])
    assert index[2] == ('P', [('Python', [[], [('Sphinx reST', [('', '#id2')])], None])])
    assert index[3] == ('R', [('reST', [[], [('Python Sphinx', [('', '#id2')])], None])])
    assert index[4] == ('S', [('Sphinx', [[], [('reST, Python', [('', '#id2')])], None])])


def test_create_see_index():
    locale.init([], None)

    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('see', 'docutils; reStructuredText', 'id1', '', None),
            ('see', 'Python; interpreter', 'id2', '', None),
            ('see', 'Sphinx; documentation tool', 'id3', '', None),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[], [('see reStructuredText', [])], None])])
    assert index[1] == ('P', [('Python', [[], [('see interpreter', [])], None])])
    assert index[2] == ('S', [('Sphinx', [[], [('see documentation tool', [])], None])])


def test_create_seealso_index():
    locale.init([], None)

    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('seealso', 'docutils; reStructuredText', 'id1', '', None),
            ('seealso', 'Python; interpreter', 'id2', '', None),
            ('seealso', 'Sphinx; documentation tool', 'id3', '', None),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[], [('see also reStructuredText', [])], None])])
    assert index[1] == ('P', [('Python', [[], [('see also interpreter', [])], None])])
    assert index[2] == ('S', [('Sphinx', [[], [('see also documentation tool', [])], None])])


def test_create_index_by_key():
    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('single', 'docutils', 'id1', '', None),
            ('single', 'Python', 'id2', '', None),
            ('single', 'スフィンクス', 'id3', '', 'ス'),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[('', '#id1')], [], None])])
    assert index[1] == ('P', [('Python', [[('', '#id2')], [], None])])
    assert index[2] == ('ス', [('スフィンクス', [[('', '#id3')], [], 'ス'])])
