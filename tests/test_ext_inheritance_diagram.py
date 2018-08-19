# -*- coding: utf-8 -*-
"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys

import pytest

from sphinx.ext.inheritance_diagram import InheritanceException, import_classes


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_png_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()

    pattern = ('<div class="figure" id="id1">\n'
               '<div class="graphviz">'
               '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
               'class="inheritance graphviz" /></div>\n<p class="caption">'
               '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram',
                    confoverrides={'graphviz_output_format': 'svg'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_svg_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()

    pattern = ('<div class="figure" id="id1">\n'
               '<div class="graphviz">'
               '<object data="_images/inheritance-\\w+.svg" '
               'type="image/svg\\+xml" class="inheritance graphviz">\n'
               '<p class=\"warning\">Inheritance diagram of test.Foo</p>'
               '</object></div>\n<p class="caption"><span class="caption-text">'
               'Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('latex', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'Python.tex').text()

    pattern = ('\\\\begin{figure}\\[htbp]\n\\\\centering\n\\\\capstart\n\n'
               '\\\\sphinxincludegraphics\\[\\]{inheritance-\\w+.pdf}\n'
               '\\\\caption{Test Foo!}\\\\label{\\\\detokenize{index:id1}}\\\\end{figure}')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram',
                    srcdir='ext-inheritance_diagram-alias')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_latex_alias(app, status, warning):
    app.config.inheritance_alias = {'test.Foo': 'alias.Foo'}
    app.builder.build_all()

    doc = app.env.get_and_resolve_doctree('index', app)
    aliased_graph = doc.children[0].children[3]['graph'].class_info
    assert len(aliased_graph) == 3
    assert ('test.Baz', 'test.Baz', ['test.Bar'], None) in aliased_graph
    assert ('test.Bar', 'test.Bar', ['alias.Foo'], None) in aliased_graph
    assert ('alias.Foo', 'alias.Foo', [], None) in aliased_graph

    content = (app.outdir / 'index.html').text()

    pattern = ('<div class="figure" id="id1">\n'
               '<div class="graphviz">'
               '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
               'class="inheritance graphviz" /></div>\n<p class="caption">'
               '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


def test_import_classes(rootdir):
    from sphinx.application import Sphinx, TemplateBridge
    from sphinx.util.i18n import CatalogInfo

    try:
        sys.path.append(rootdir / 'test-ext-inheritance_diagram')
        from example.sphinx import DummyClass

        # got exception for unknown class or module
        with pytest.raises(InheritanceException):
            import_classes('unknown', None)
        with pytest.raises(InheritanceException):
            import_classes('unknown.Unknown', None)

        # got exception InheritanceException for wrong class or module
        # not AttributeError (refs: #4019)
        with pytest.raises(InheritanceException):
            import_classes('unknown', '.')
        with pytest.raises(InheritanceException):
            import_classes('unknown.Unknown', '.')
        with pytest.raises(InheritanceException):
            import_classes('.', None)

        # a module having no classes
        classes = import_classes('sphinx', None)
        assert classes == []

        classes = import_classes('sphinx', 'foo')
        assert classes == []

        # all of classes in the module
        classes = import_classes('sphinx.application', None)
        assert set(classes) == set([Sphinx, TemplateBridge])

        # specified class in the module
        classes = import_classes('sphinx.application.Sphinx', None)
        assert classes == [Sphinx]

        # specified class in current module
        classes = import_classes('Sphinx', 'sphinx.application')
        assert classes == [Sphinx]

        # relative module name to current module
        classes = import_classes('i18n.CatalogInfo', 'sphinx.util')
        assert classes == [CatalogInfo]

        # got exception for functions
        with pytest.raises(InheritanceException):
            import_classes('encode_uri', 'sphinx.util')

        # import submodule on current module (refs: #3164)
        classes = import_classes('sphinx', 'example')
        assert classes == [DummyClass]
    finally:
        sys.path.pop()
