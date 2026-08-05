"""Test the other directives."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

from tests.utils import extract_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree(app):
    text = '.. toctree::\n\n   foo\n   bar/index\n   baz\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'foo'), (None, 'bar/index'), (None, 'baz')],
        includefiles=['foo', 'bar/index', 'baz'],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_relative_toctree(app):
    text = '.. toctree::\n\n   bar_1\n   bar_2\n   bar_3\n   ../quux\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'bar/index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[
            (None, 'bar/bar_1'),
            (None, 'bar/bar_2'),
            (None, 'bar/bar_3'),
            (None, 'quux'),
        ],
        includefiles=['bar/bar_1', 'bar/bar_2', 'bar/bar_3', 'quux'],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree_urls_and_titles(app):
    text = (
        '.. toctree::\n'
        '\n'
        '   Sphinx <https://www.sphinx-doc.org/>\n'
        '   https://readthedocs.org/\n'
        '   The BAR <bar/index>\n'
    )

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[
            ('Sphinx', 'https://www.sphinx-doc.org/'),
            (None, 'https://readthedocs.org/'),
            ('The BAR', 'bar/index'),
        ],
        includefiles=['bar/index'],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree_glob(app):
    text = '.. toctree::\n   :glob:\n\n   *\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'baz'), (None, 'foo'), (None, 'quux')],
        includefiles=['baz', 'foo', 'quux'],
    )

    # give both docname and glob (case1)
    text = '.. toctree::\n   :glob:\n\n   foo\n   *\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'foo'), (None, 'baz'), (None, 'quux')],
        includefiles=['foo', 'baz', 'quux'],
    )

    # give both docname and glob (case2)
    text = '.. toctree::\n   :glob:\n\n   *\n   foo\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'baz'), (None, 'foo'), (None, 'quux'), (None, 'foo')],
        includefiles=['baz', 'foo', 'quux', 'foo'],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree_glob_and_url(app):
    text = '.. toctree::\n   :glob:\n\n   https://example.com/?q=sphinx\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'https://example.com/?q=sphinx')],
        includefiles=[],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_reversed_toctree(app):
    text = '.. toctree::\n   :reversed:\n\n   foo\n   bar/index\n   baz\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'baz'), (None, 'bar/index'), (None, 'foo')],
        includefiles=['baz', 'bar/index', 'foo'],
    )


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree_class(app):
    text = '.. toctree::\n   :class: custom-toc\n\n   foo\n'
    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert isinstance(doctree[0], nodes.compound)
    assert doctree[0].attributes['classes'] == ['toctree-wrapper', 'custom-toc']


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_toctree_twice(app):
    text = '.. toctree::\n\n   foo\n   foo\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(
        extract_node(doctree, 0, 0),
        entries=[(None, 'foo'), (None, 'foo')],
        includefiles=['foo', 'foo'],
    )


@pytest.mark.sphinx('html', testroot='directive-include')
def test_include_include_read_event(app: SphinxTestApp) -> None:
    sources_reported = []

    def source_read_handler(_app, relative_path, parent_docname, source):
        sources_reported.append((relative_path, parent_docname, source[0]))

    app.connect('include-read', source_read_handler)
    text = """\
.. include:: baz/baz.rst
   :start-line: 4
.. include:: text.txt
   :literal:
.. include:: bar.txt
"""
    app.env.find_files(app.config, app.builder)
    restructuredtext.parse(app, text, 'index')

    included_files = {filename.as_posix() for filename, p, s in sources_reported}
    # sources don't emit 'include-read'
    assert 'index.rst' not in included_files

    assert 'baz/baz.rst' in included_files

    # text was included as literal, no rst parsing
    assert 'text.txt' not in included_files

    # suffix not in source-suffixes
    assert 'bar.txt' in included_files

    assert (Path('baz/baz.rst'), 'index', '\nBaz was here.') in sources_reported


@pytest.mark.sphinx('html', testroot='directive-include')
def test_include_include_read_event_nested_includes(app):
    def source_read_handler(_app, _relative_path, _parent_docname, source):
        text = source[0].replace('#magical', 'amazing')
        source[0] = text

    app.connect('include-read', source_read_handler)
    text = '.. include:: baz/baz.rst\n'
    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, addnodes.document)
    assert len(doctree.children) == 3
    assert isinstance(doctree.children[1], nodes.paragraph)
    assert doctree.children[1].rawsource == 'The amazing foo.'
