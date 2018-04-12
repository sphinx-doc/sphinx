# -*- coding: utf-8 -*-
"""
    test_directive_other
    ~~~~~~~~~~~~~~~~~~~~

    Test the other directives.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from docutils import nodes
from docutils.core import publish_doctree

from sphinx import addnodes
from sphinx.io import SphinxStandaloneReader
from sphinx.parsers import RSTParser
from sphinx.testing.util import assert_node


def parse(app, docname, text):
    app.env.temp_data['docname'] = docname
    return publish_doctree(text, app.srcdir / docname + '.rst',
                           reader=SphinxStandaloneReader(app),
                           parser=RSTParser(),
                           settings_overrides={'env': app.env,
                                               'gettext_compact': True})


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree(app):
    text = (".. toctree::\n"
            "\n"
            "   foo\n"
            "   bar/index\n"
            "   baz\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'foo'), (None, 'bar/index'), (None, 'baz')],
                includefiles=['foo', 'bar/index', 'baz'])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_relative_toctree(app):
    text = (".. toctree::\n"
            "\n"
            "   bar_1\n"
            "   bar_2\n"
            "   bar_3\n"
            "   ../quux\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'bar/index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'bar/bar_1'), (None, 'bar/bar_2'), (None, 'bar/bar_3'),
                         (None, 'quux')],
                includefiles=['bar/bar_1', 'bar/bar_2', 'bar/bar_3', 'quux'])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree_urls_and_titles(app):
    text = (".. toctree::\n"
            "\n"
            "   Sphinx <https://www.sphinx-doc.org/>\n"
            "   https://readthedocs.org/\n"
            "   The BAR <bar/index>\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[('Sphinx', 'https://www.sphinx-doc.org/'),
                         (None, 'https://readthedocs.org/'),
                         ('The BAR', 'bar/index')],
                includefiles=['bar/index'])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree_glob(app):
    text = (".. toctree::\n"
            "   :glob:\n"
            "\n"
            "   *\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'baz'), (None, 'foo'), (None, 'quux')],
                includefiles=['baz', 'foo', 'quux'])

    # give both docname and glob (case1)
    text = (".. toctree::\n"
            "   :glob:\n"
            "\n"
            "   foo\n"
            "   *\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'foo'), (None, 'baz'), (None, 'quux')],
                includefiles=['foo', 'baz', 'quux'])

    # give both docname and glob (case2)
    text = (".. toctree::\n"
            "   :glob:\n"
            "\n"
            "   *\n"
            "   foo\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'baz'), (None, 'foo'), (None, 'quux'), (None, 'foo')],
                includefiles=['baz', 'foo', 'quux', 'foo'])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree_glob_and_url(app):
    text = (".. toctree::\n"
            "   :glob:\n"
            "\n"
            "   https://example.com/?q=sphinx\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'https://example.com/?q=sphinx')],
                includefiles=[])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree_twice(app):
    text = (".. toctree::\n"
            "\n"
            "   foo\n"
            "   foo\n")

    app.env.find_files(app.config, app.builder)
    doctree = parse(app, 'index', text)
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'foo'), (None, 'foo')],
                includefiles=['foo', 'foo'])
