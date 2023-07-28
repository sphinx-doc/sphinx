"""Test the other directives."""

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree(app):
    text = (".. toctree::\n"
            "\n"
            "   foo\n"
            "   bar/index\n"
            "   baz\n")

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
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
    doctree = restructuredtext.parse(app, text, 'bar/index')
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
    doctree = restructuredtext.parse(app, text, 'index')
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
    doctree = restructuredtext.parse(app, text, 'index')
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
    doctree = restructuredtext.parse(app, text, 'index')
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
    doctree = restructuredtext.parse(app, text, 'index')
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
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'https://example.com/?q=sphinx')],
                includefiles=[])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_reversed_toctree(app):
    text = (".. toctree::\n"
            "   :reversed:\n"
            "\n"
            "   foo\n"
            "   bar/index\n"
            "   baz\n")

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'baz'), (None, 'bar/index'), (None, 'foo')],
                includefiles=['baz', 'bar/index', 'foo'])


@pytest.mark.sphinx(testroot='toctree-glob')
def test_toctree_twice(app):
    text = (".. toctree::\n"
            "\n"
            "   foo\n"
            "   foo\n")

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert_node(doctree, [nodes.document, nodes.compound, addnodes.toctree])
    assert_node(doctree[0][0],
                entries=[(None, 'foo'), (None, 'foo')],
                includefiles=['foo', 'foo'])


@pytest.mark.sphinx(testroot='toctree-hidden')
def test_toctree_hidden_section_order(app):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert """\
<ul>
<li class="toctree-l1"><a class="reference internal" href="part.html">Part</a><ul>
<li class="toctree-l2"><a class="reference internal" href="part.html#section-1">Section 1</a></li>
<li class="toctree-l2"><a class="reference internal" href="part.html#section-2">Section 2</a></li>
<li class="toctree-l2"><a class="reference internal" href="doc1.html">Document 1</a></li>
<li class="toctree-l2"><a class="reference internal" href="doc2.html">Document 2</a></li>
</ul>""" in content
