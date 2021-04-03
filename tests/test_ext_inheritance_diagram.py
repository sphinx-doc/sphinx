"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys

import pytest

from sphinx.ext.inheritance_diagram import (InheritanceDiagram, InheritanceException,
                                            import_classes)
from sphinx.util import docutils


@pytest.mark.sphinx(buildername="html", testroot="inheritance")
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram(app, status, warning):
    # monkey-patch InheritaceDiagram.run() so we can get access to its
    # results.
    orig_run = InheritanceDiagram.run
    graphs = {}

    def new_run(self):
        result = orig_run(self)
        node = result[0]
        source = os.path.basename(node.document.current_source).replace(".rst", "")
        graphs[source] = node['graph']
        return result

    InheritanceDiagram.run = new_run

    try:
        app.builder.build_all()
    finally:
        InheritanceDiagram.run = orig_run

    assert app.statuscode == 0

    html_warnings = warning.getvalue()
    assert html_warnings == ""

    # note: it is better to split these asserts into separate test functions
    # but I can't figure out how to build only a specific .rst file

    # basic inheritance diagram showing all classes
    for cls in graphs['basic_diagram'].class_info:
        # use in b/c traversing order is different sometimes
        assert cls in [
            ('dummy.test.A', 'dummy.test.A', [], None),
            ('dummy.test.F', 'dummy.test.F', ['dummy.test.C'], None),
            ('dummy.test.C', 'dummy.test.C', ['dummy.test.A'], None),
            ('dummy.test.E', 'dummy.test.E', ['dummy.test.B'], None),
            ('dummy.test.D', 'dummy.test.D', ['dummy.test.B', 'dummy.test.C'], None),
            ('dummy.test.B', 'dummy.test.B', ['dummy.test.A'], None)
        ]

    # inheritance diagram using :parts: 1 option
    for cls in graphs['diagram_w_parts'].class_info:
        assert cls in [
            ('A', 'dummy.test.A', [], None),
            ('F', 'dummy.test.F', ['C'], None),
            ('C', 'dummy.test.C', ['A'], None),
            ('E', 'dummy.test.E', ['B'], None),
            ('D', 'dummy.test.D', ['B', 'C'], None),
            ('B', 'dummy.test.B', ['A'], None)
        ]

    # inheritance diagram with 1 top class
    # :top-classes: dummy.test.B
    # rendering should be
    #       A
    #        \
    #     B   C
    #    / \ / \
    #   E   D   F
    #
    for cls in graphs['diagram_w_1_top_class'].class_info:
        assert cls in [
            ('dummy.test.A', 'dummy.test.A', [], None),
            ('dummy.test.F', 'dummy.test.F', ['dummy.test.C'], None),
            ('dummy.test.C', 'dummy.test.C', ['dummy.test.A'], None),
            ('dummy.test.E', 'dummy.test.E', ['dummy.test.B'], None),
            ('dummy.test.D', 'dummy.test.D', ['dummy.test.B', 'dummy.test.C'], None),
            ('dummy.test.B', 'dummy.test.B', [], None)
        ]

    # inheritance diagram with 2 top classes
    # :top-classes: dummy.test.B, dummy.test.C
    # Note: we're specifying separate classes, not the entire module here
    # rendering should be
    #
    #     B   C
    #    / \ / \
    #   E   D   F
    #
    for cls in graphs['diagram_w_2_top_classes'].class_info:
        assert cls in [
            ('dummy.test.F', 'dummy.test.F', ['dummy.test.C'], None),
            ('dummy.test.C', 'dummy.test.C', [], None),
            ('dummy.test.E', 'dummy.test.E', ['dummy.test.B'], None),
            ('dummy.test.D', 'dummy.test.D', ['dummy.test.B', 'dummy.test.C'], None),
            ('dummy.test.B', 'dummy.test.B', [], None)
        ]

    # inheritance diagram with 2 top classes and specifying the entire module
    # rendering should be
    #
    #       A
    #     B   C
    #    / \ / \
    #   E   D   F
    #
    # Note: dummy.test.A is included in the graph before its descendants are even processed
    # b/c we've specified to load the entire module. The way InheritanceGraph works it is very
    # hard to exclude parent classes once after they have been included in the graph.
    # If you'd like to not show class A in the graph don't specify the entire module.
    # this is a known issue.
    for cls in graphs['diagram_module_w_2_top_classes'].class_info:
        assert cls in [
            ('dummy.test.F', 'dummy.test.F', ['dummy.test.C'], None),
            ('dummy.test.C', 'dummy.test.C', [], None),
            ('dummy.test.E', 'dummy.test.E', ['dummy.test.B'], None),
            ('dummy.test.D', 'dummy.test.D', ['dummy.test.B', 'dummy.test.C'], None),
            ('dummy.test.B', 'dummy.test.B', [], None),
            ('dummy.test.A', 'dummy.test.A', [], None),
        ]

    # inheritance diagram involving a base class nested within another class
    for cls in graphs['diagram_w_nested_classes'].class_info:
        assert cls in [
            ('dummy.test_nested.A', 'dummy.test_nested.A', [], None),
            ('dummy.test_nested.C', 'dummy.test_nested.C', ['dummy.test_nested.A.B'], None),
            ('dummy.test_nested.A.B', 'dummy.test_nested.A.B', [], None)
        ]


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_png_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()

    if docutils.__version_info__ < (0, 17):
        pattern = ('<div class="figure align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
                   'class="inheritance graphviz" /></div>\n<p class="caption">'
                   '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</div>\n')
    else:
        pattern = ('<figure class="align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
                   'class="inheritance graphviz" /></div>\n<figcaption>\n<p>'
                   '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</figcaption>\n</figure>\n')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram',
                    confoverrides={'graphviz_output_format': 'svg'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_svg_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()

    if docutils.__version_info__ < (0, 17):
        pattern = ('<div class="figure align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<object data="_images/inheritance-\\w+.svg" '
                   'type="image/svg\\+xml" class="inheritance graphviz">\n'
                   '<p class=\"warning\">Inheritance diagram of test.Foo</p>'
                   '</object></div>\n<p class="caption"><span class="caption-text">'
                   'Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</div>\n')
    else:
        pattern = ('<figure class="align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<object data="_images/inheritance-\\w+.svg" '
                   'type="image/svg\\+xml" class="inheritance graphviz">\n'
                   '<p class=\"warning\">Inheritance diagram of test.Foo</p>'
                   '</object></div>\n<figcaption>\n<p><span class="caption-text">'
                   'Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</figcaption>\n</figure>\n')

    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('latex', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text()

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

    content = (app.outdir / 'index.html').read_text()

    if docutils.__version_info__ < (0, 17):
        pattern = ('<div class="figure align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
                   'class="inheritance graphviz" /></div>\n<p class="caption">'
                   '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</div>\n')
    else:
        pattern = ('<figure class="align-default" id="id1">\n'
                   '<div class="graphviz">'
                   '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
                   'class="inheritance graphviz" /></div>\n<figcaption>\n<p>'
                   '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
                   'title="Permalink to this image">\xb6</a></p>\n</figcaption>\n</figure>\n')
    assert re.search(pattern, content, re.M)


def test_import_classes(rootdir):
    from sphinx.parsers import Parser, RSTParser
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
        classes = import_classes('sphinx.parsers', None)
        assert set(classes) == {Parser, RSTParser}

        # specified class in the module
        classes = import_classes('sphinx.parsers.Parser', None)
        assert classes == [Parser]

        # specified class in current module
        classes = import_classes('Parser', 'sphinx.parsers')
        assert classes == [Parser]

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
