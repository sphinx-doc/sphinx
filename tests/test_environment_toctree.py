# -*- coding: utf-8 -*-
"""
    test_environment_toctree
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test the sphinx.environment.managers.toctree.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.nodes import bullet_list, list_item, caption, comment, reference
from sphinx import addnodes
from sphinx.addnodes import compact_paragraph, only
from sphinx.builders.html import StandaloneHTMLBuilder

from util import with_app, gen_with_app, assert_node


@gen_with_app('xml', testroot='toctree')
def test_basic(app, status, warning):
    app.build()
    yield _test_process_doc, app
    yield _test_get_toc_for, app
    yield _test_get_toc_for_only, app
    yield _test_get_toc_for_tocdepth, app
    yield _test_get_toctree_for, app
    yield _test_get_toctree_for_collapse, app
    yield _test_get_toctree_for_maxdepth, app
    yield _test_get_toctree_for_includehidden, app


def _test_process_doc(app):
    # tocs
    toctree = app.env.tocs['index']
    assert_node(toctree,
                [bullet_list, ([list_item, (compact_paragraph,  # [0][0]
                                            [bullet_list, (addnodes.toctree,  # [0][1][0]
                                                           only,  # [0][1][1]
                                                           list_item)])],  # [0][1][2]
                               [list_item, (compact_paragraph,  # [1][0]
                                            [bullet_list, (addnodes.toctree,  # [1][1][0]
                                                           addnodes.toctree)])],  # [1][1][1]
                               list_item)])

    assert_node(toctree[0][0],
                [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"])
    assert_node(toctree[0][0][0], reference, anchorname='')
    assert_node(toctree[0][1][0], addnodes.toctree,
                caption="Table of Contents", glob=False, hidden=False,
                titlesonly=False, maxdepth=2, numbered=999,
                entries=[(None, 'foo'), (None, 'bar'), (None, 'http://sphinx-doc.org/')],
                includefiles=['foo', 'bar'])

    # only branch
    assert_node(toctree[0][1][1], addnodes.only, expr="html")
    assert_node(toctree[0][1][1],
                [only, list_item, ([compact_paragraph, reference, "Section for HTML"],
                                   [bullet_list, addnodes.toctree])])
    assert_node(toctree[0][1][1][0][0][0], reference, anchorname='#section-for-html')
    assert_node(toctree[0][1][1][0][1][0], addnodes.toctree,
                caption=None, glob=False, hidden=False, entries=[(None, 'baz')],
                includefiles=['baz'], titlesonly=False, maxdepth=-1, numbered=0)
    assert_node(toctree[0][1][2],
                ([compact_paragraph, reference, "subsection"],
                 [bullet_list, list_item, compact_paragraph, reference, "subsubsection"]))

    assert_node(toctree[1][0],
                [compact_paragraph, reference, "Test for issue #1157"])
    assert_node(toctree[1][0][0], reference, anchorname='#test-for-issue-1157')
    assert_node(toctree[1][1][0], addnodes.toctree,
                caption=None, entries=[], glob=False, hidden=False,
                titlesonly=False, maxdepth=-1, numbered=0)
    assert_node(toctree[1][1][1], addnodes.toctree,
                caption=None, glob=False, hidden=True,
                titlesonly=False, maxdepth=-1, numbered=0,
                entries=[('Latest reference', 'http://sphinx-doc.org/latest/'),
                         ('Python', 'http://python.org/')])

    assert_node(toctree[2][0],
                [compact_paragraph, reference, "Indices and tables"])

    # other collections
    assert app.env.toc_num_entries['index'] == 6
    assert app.env.toctree_includes['index'] == ['foo', 'bar', 'baz']
    assert app.env.files_to_rebuild['foo'] == set(['index'])
    assert app.env.files_to_rebuild['bar'] == set(['index'])
    assert app.env.files_to_rebuild['baz'] == set(['index'])
    assert app.env.glob_toctrees == set()
    assert app.env.numbered_toctrees == set(['index'])

    # qux has no section title
    assert len(app.env.tocs['qux']) == 0
    assert_node(app.env.tocs['qux'], nodes.bullet_list)
    assert app.env.toc_num_entries['qux'] == 0
    assert 'qux' not in app.env.toctree_includes


@with_app('dummy', testroot='toctree-glob')
def test_glob(app, status, warning):
    includefiles = ['foo', 'bar/index', 'bar/bar_1', 'bar/bar_2',
                    'bar/bar_3', 'baz', 'qux/index']

    app.build()

    # tocs
    toctree = app.env.tocs['index']
    assert_node(toctree,
                [bullet_list, list_item, (compact_paragraph,  # [0][0]
                                          [bullet_list, (list_item,  # [0][1][0]
                                                         list_item)])])  # [0][1][1]

    assert_node(toctree[0][0],
                [compact_paragraph, reference, "test-toctree-glob"])
    assert_node(toctree[0][1][0],
                [list_item, ([compact_paragraph, reference, "normal order"],
                             [bullet_list, addnodes.toctree])])  # [0][1][0][1][0]
    assert_node(toctree[0][1][0][1][0], addnodes.toctree, caption=None,
                glob=True, hidden=False, titlesonly=False,
                maxdepth=-1, numbered=0, includefiles=includefiles,
                entries=[(None, 'foo'), (None, 'bar/index'), (None, 'bar/bar_1'),
                         (None, 'bar/bar_2'), (None, 'bar/bar_3'), (None, 'baz'),
                         (None, 'qux/index')])
    assert_node(toctree[0][1][1],
                [list_item, ([compact_paragraph, reference, "reversed order"],
                             [bullet_list, addnodes.toctree])])  # [0][1][1][1][0]
    assert_node(toctree[0][1][1][1][0], addnodes.toctree, caption=None,
                glob=True, hidden=False, titlesonly=False,
                maxdepth=-1, numbered=0, includefiles=includefiles,
                entries=[(None, 'qux/index'), (None, 'baz'), (None, 'bar/bar_3'),
                         (None, 'bar/bar_2'), (None, 'bar/bar_1'), (None, 'bar/index'),
                         (None, 'foo')])
    includefiles = ['foo', 'bar/index', 'bar/bar_1', 'bar/bar_2',
                    'bar/bar_3', 'baz', 'qux/index']

    # other collections
    assert app.env.toc_num_entries['index'] == 3
    assert app.env.toctree_includes['index'] == includefiles + includefiles
    for file in includefiles:
        assert 'index' in app.env.files_to_rebuild[file]
    assert 'index' in app.env.glob_toctrees
    assert app.env.numbered_toctrees == set()


def _test_get_toc_for(app):
    toctree = app.env.get_toc_for('index', app.builder)

    assert_node(toctree,
                [bullet_list, ([list_item, (compact_paragraph,  # [0][0]
                                            [bullet_list, (addnodes.toctree,  # [0][1][0]
                                                           comment,  # [0][1][1]
                                                           list_item)])],  # [0][1][2]
                               [list_item, (compact_paragraph,  # [1][0]
                                            [bullet_list, (addnodes.toctree,
                                                           addnodes.toctree)])],
                               [list_item, compact_paragraph])])  # [2][0]
    assert_node(toctree[0][0],
                [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"])
    assert_node(toctree[0][1][2],
                ([compact_paragraph, reference, "subsection"],
                 [bullet_list, list_item, compact_paragraph, reference, "subsubsection"]))
    assert_node(toctree[1][0],
                [compact_paragraph, reference, "Test for issue #1157"])
    assert_node(toctree[2][0],
                [compact_paragraph, reference, "Indices and tables"])


def _test_get_toc_for_only(app):
    builder = StandaloneHTMLBuilder(app)
    toctree = app.env.get_toc_for('index', builder)

    assert_node(toctree,
                [bullet_list, ([list_item, (compact_paragraph,  # [0][0]
                                            [bullet_list, (addnodes.toctree,  # [0][1][0]
                                                           list_item,  # [0][1][1]
                                                           list_item)])],  # [0][1][2]
                               [list_item, (compact_paragraph,  # [1][0]
                                            [bullet_list, (addnodes.toctree,
                                                           addnodes.toctree)])],
                               [list_item, compact_paragraph])])  # [2][0]
    assert_node(toctree[0][0],
                [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"])
    assert_node(toctree[0][1][1],
                ([compact_paragraph, reference, "Section for HTML"],
                 [bullet_list, addnodes.toctree]))
    assert_node(toctree[0][1][2],
                ([compact_paragraph, reference, "subsection"],
                 [bullet_list, list_item, compact_paragraph, reference, "subsubsection"]))
    assert_node(toctree[1][0],
                [compact_paragraph, reference, "Test for issue #1157"])
    assert_node(toctree[2][0],
                [compact_paragraph, reference, "Indices and tables"])


def _test_get_toc_for_tocdepth(app):
    toctree = app.env.get_toc_for('tocdepth', app.builder)

    assert_node(toctree,
                [bullet_list, list_item, (compact_paragraph,  # [0][0]
                                          bullet_list)])  # [0][1]
    assert_node(toctree[0][0],
                [compact_paragraph, reference, "level 1"])
    assert_node(toctree[0][1],
                [bullet_list, list_item, compact_paragraph, reference, "level 2"])


def _test_get_toctree_for(app):
    toctree = app.env.get_toctree_for('index', app.builder, collapse=False)
    assert_node(toctree,
                [compact_paragraph, ([caption, "Table of Contents"],
                                     bullet_list,
                                     bullet_list,
                                     bullet_list)])

    assert_node(toctree[1],
                ([list_item, ([compact_paragraph, reference, "foo"],
                              bullet_list)],
                 [list_item, compact_paragraph, reference, "bar"],
                 [list_item, compact_paragraph, reference, "http://sphinx-doc.org/"]))
    assert_node(toctree[1][0][1],
                ([list_item, compact_paragraph, reference, "quux"],
                 [list_item, compact_paragraph, reference, "foo.1"],
                 [list_item, compact_paragraph, reference, "foo.2"]))

    assert_node(toctree[1][0][0][0], reference, refuri="foo", secnumber=(1,))
    assert_node(toctree[1][0][1][0][0][0], reference, refuri="quux", secnumber=(1, 1))
    assert_node(toctree[1][0][1][1][0][0], reference, refuri="foo#foo-1", secnumber=(1, 2))
    assert_node(toctree[1][0][1][2][0][0], reference, refuri="foo#foo-2", secnumber=(1, 3))
    assert_node(toctree[1][1][0][0], reference, refuri="bar", secnumber=(2,))
    assert_node(toctree[1][2][0][0], reference, refuri="http://sphinx-doc.org/")

    assert_node(toctree[2],
                [bullet_list, list_item, compact_paragraph, reference, "baz"])
    assert_node(toctree[3],
                ([list_item, compact_paragraph, reference, "Latest reference"],
                 [list_item, compact_paragraph, reference, "Python"]))
    assert_node(toctree[3][0][0][0], reference, refuri="http://sphinx-doc.org/latest/")
    assert_node(toctree[3][1][0][0], reference, refuri="http://python.org/")


def _test_get_toctree_for_collapse(app):
    toctree = app.env.get_toctree_for('index', app.builder, collapse=True)
    assert_node(toctree,
                [compact_paragraph, ([caption, "Table of Contents"],
                                     bullet_list,
                                     bullet_list,
                                     bullet_list)])

    assert_node(toctree[1],
                ([list_item, compact_paragraph, reference, "foo"],
                 [list_item, compact_paragraph, reference, "bar"],
                 [list_item, compact_paragraph, reference, "http://sphinx-doc.org/"]))
    assert_node(toctree[1][0][0][0], reference, refuri="foo", secnumber=(1,))
    assert_node(toctree[1][1][0][0], reference, refuri="bar", secnumber=(2,))
    assert_node(toctree[1][2][0][0], reference, refuri="http://sphinx-doc.org/")

    assert_node(toctree[2],
                [bullet_list, list_item, compact_paragraph, reference, "baz"])
    assert_node(toctree[3],
                ([list_item, compact_paragraph, reference, "Latest reference"],
                 [list_item, compact_paragraph, reference, "Python"]))
    assert_node(toctree[3][0][0][0], reference, refuri="http://sphinx-doc.org/latest/")
    assert_node(toctree[3][1][0][0], reference, refuri="http://python.org/")


def _test_get_toctree_for_maxdepth(app):
    toctree = app.env.get_toctree_for('index', app.builder, collapse=False, maxdepth=3)
    assert_node(toctree,
                [compact_paragraph, ([caption, "Table of Contents"],
                                     bullet_list,
                                     bullet_list,
                                     bullet_list)])

    assert_node(toctree[1],
                ([list_item, ([compact_paragraph, reference, "foo"],
                              bullet_list)],
                 [list_item, compact_paragraph, reference, "bar"],
                 [list_item, compact_paragraph, reference, "http://sphinx-doc.org/"]))
    assert_node(toctree[1][0][1],
                ([list_item, compact_paragraph, reference, "quux"],
                 [list_item, ([compact_paragraph, reference, "foo.1"],
                              bullet_list)],
                 [list_item, compact_paragraph, reference, "foo.2"]))
    assert_node(toctree[1][0][1][1][1],
                [bullet_list, list_item, compact_paragraph, reference, "foo.1-1"])

    assert_node(toctree[1][0][0][0], reference, refuri="foo", secnumber=(1,))
    assert_node(toctree[1][0][1][0][0][0], reference, refuri="quux", secnumber=(1, 1))
    assert_node(toctree[1][0][1][1][0][0], reference, refuri="foo#foo-1", secnumber=(1, 2))
    assert_node(toctree[1][0][1][1][1][0][0][0],
                reference, refuri="foo#foo-1-1", secnumber=(1, 2, 1))
    assert_node(toctree[1][0][1][2][0][0], reference, refuri="foo#foo-2", secnumber=(1, 3))
    assert_node(toctree[1][1][0][0], reference, refuri="bar", secnumber=(2,))
    assert_node(toctree[1][2][0][0], reference, refuri="http://sphinx-doc.org/")

    assert_node(toctree[2],
                [bullet_list, list_item, compact_paragraph, reference, "baz"])
    assert_node(toctree[3],
                ([list_item, compact_paragraph, reference, "Latest reference"],
                 [list_item, compact_paragraph, reference, "Python"]))
    assert_node(toctree[3][0][0][0], reference, refuri="http://sphinx-doc.org/latest/")
    assert_node(toctree[3][1][0][0], reference, refuri="http://python.org/")


def _test_get_toctree_for_includehidden(app):
    toctree = app.env.get_toctree_for('index', app.builder, collapse=False,
                                      includehidden=False)
    assert_node(toctree,
                [compact_paragraph, ([caption, "Table of Contents"],
                                     bullet_list,
                                     bullet_list)])

    assert_node(toctree[1],
                ([list_item, ([compact_paragraph, reference, "foo"],
                              bullet_list)],
                 [list_item, compact_paragraph, reference, "bar"],
                 [list_item, compact_paragraph, reference, "http://sphinx-doc.org/"]))
    assert_node(toctree[1][0][1],
                ([list_item, compact_paragraph, reference, "quux"],
                 [list_item, compact_paragraph, reference, "foo.1"],
                 [list_item, compact_paragraph, reference, "foo.2"]))

    assert_node(toctree[1][0][0][0], reference, refuri="foo", secnumber=(1,))
    assert_node(toctree[1][0][1][0][0][0], reference, refuri="quux", secnumber=(1, 1))
    assert_node(toctree[1][0][1][1][0][0], reference, refuri="foo#foo-1", secnumber=(1, 2))
    assert_node(toctree[1][0][1][2][0][0], reference, refuri="foo#foo-2", secnumber=(1, 3))
    assert_node(toctree[1][1][0][0], reference, refuri="bar", secnumber=(2,))
    assert_node(toctree[1][2][0][0], reference, refuri="http://sphinx-doc.org/")

    assert_node(toctree[2],
                [bullet_list, list_item, compact_paragraph, reference, "baz"])
