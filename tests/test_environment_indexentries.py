# -*- coding: utf-8 -*-
"""
    test_environment_indexentries
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the sphinx.environment.managers.indexentries.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import namedtuple
from sphinx import locale
from sphinx.environment.managers.indexentries import IndexEntries

import mock

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
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 3
    assert index[0] == (u'D', [(u'docutils', [[('', '#id1')], [], None])])
    assert index[1] == (u'P', [(u'pip', [[], [(u'install', [('', '#id3')]),
                                              (u'upgrade', [('', '#id4')])], None]),
                               (u'Python', [[('', '#id2')], [], None])])
    assert index[2] == (u'S', [(u'Sphinx', [[('', '#id5')], [], None])])


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
    assert index[0] == (u'D',
                        [(u'documentation tool', [[], [(u'Sphinx', [('', '#id3')])], None]),
                         (u'docutils', [[], [(u'reStructuredText', [('', '#id1')])], None])])
    assert index[1] == (u'I', [(u'interpreter', [[], [(u'Python', [('', '#id2')])], None])])
    assert index[2] == (u'P', [(u'Python', [[], [(u'interpreter', [('', '#id2')])], None])])
    assert index[3] == (u'R',
                        [(u'reStructuredText', [[], [(u'docutils', [('', '#id1')])], None])])
    assert index[4] == (u'S',
                        [(u'Sphinx', [[], [(u'documentation tool', [('', '#id3')])], None])])


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
    assert index[0] == (u'B', [(u'bar', [[], [(u'baz, foo', [('', '#id1')])], None]),
                               (u'baz', [[], [(u'foo bar', [('', '#id1')])], None])])
    assert index[1] == (u'F', [(u'foo', [[], [(u'bar baz', [('', '#id1')])], None])])
    assert index[2] == (u'P', [(u'Python', [[], [(u'Sphinx reST', [('', '#id2')])], None])])
    assert index[3] == (u'R', [(u'reST', [[], [(u'Python Sphinx', [('', '#id2')])], None])])
    assert index[4] == (u'S', [(u'Sphinx', [[], [(u'reST, Python', [('', '#id2')])], None])])


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
    assert index[0] == (u'D', [(u'docutils', [[], [(u'see reStructuredText', [])], None])])
    assert index[1] == (u'P', [(u'Python', [[], [(u'see interpreter', [])], None])])
    assert index[2] == (u'S', [(u'Sphinx', [[], [(u'see documentation tool', [])], None])])


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
    assert index[0] == (u'D',
                        [(u'docutils', [[], [(u'see also reStructuredText', [])], None])])
    assert index[1] == (u'P',
                        [(u'Python', [[], [(u'see also interpreter', [])], None])])
    assert index[2] == (u'S',
                        [(u'Sphinx', [[], [(u'see also documentation tool', [])], None])])


def test_create_index_by_key():
    # type, value, tid, main, index_key
    env = Environment({
        'index': [
            ('single', 'docutils', 'id1', '', None),
            ('single', 'Python', 'id2', '', None),
            ('single', u'スフィンクス', 'id3', '', u'ス'),
        ],
    })
    index = IndexEntries(env).create_index(dummy_builder)
    assert len(index) == 3
    assert index[0] == (u'D', [(u'docutils', [[('', '#id1')], [], None])])
    assert index[1] == (u'P', [(u'Python', [[('', '#id2')], [], None])])
    assert index[2] == (u'ス', [(u'スフィンクス', [[('', '#id3')], [], u'ス'])])
