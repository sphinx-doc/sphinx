"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import os
import sys
import pytest

from sphinx.ext import inheritance_diagram as ext


CACHE = None


@pytest.fixture
def diagram_lookup():
    """Monkey-patch InheritaceDiagram.run() and InheritanceGraph.generate_dot()
    so we can get access to generated dot content.
    """
    class Lookup():
        def __init__(self):
            self.dots = {}  # type: Dict[str, str]
            """Store each dot result per graph name which was generate"""

    lookup = Lookup()
    
    orig_run = ext.InheritanceDiagram.run
    orig_generate_dot = ext.InheritanceGraph.generate_dot

    def new_run(self):
        result = orig_run(self)
        node = result[0]
        if not isinstance(node, ext.inheritance_diagram):
            node = node[0]
        if not isinstance(node, ext.inheritance_diagram):
            node = None
        if node is not None:            
            source = os.path.basename(node.document.current_source).replace(".rst", "")
            node['graph']._source = source
        return result

    def new_generate_dot(self, *args, **kwargs):
        result = orig_generate_dot(self, *args, **kwargs)
        lookup.dots[self._source] = result
        return result

    ext.InheritanceDiagram.run = new_run
    ext.InheritanceGraph.generate_dot = new_generate_dot
    try:
        yield lookup
    finally:
        ext.InheritanceDiagram.run = orig_run
        ext.InheritanceGraph.generate_dot = orig_generate_dot


@pytest.fixture
def build_context(make_app, diagram_lookup, app_params, warning):
    """Build the whole sphinx rst for this extension a single time.

    It's a kind of module scope fixture but it uses function scope fixture.
    """
    global CACHE
    if CACHE is not None:
        return CACHE

    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    app.builder.build_all()

    assert app.statuscode == 0

    html_warnings = warning.getvalue()
    assert html_warnings == ""

    CACHE = diagram_lookup
    return diagram_lookup


def get_label(class_name, dot):
    """Returns the label from a class name of a dot format"""
    try:
        template = r"^\s*\"%s\"\s*\[.*label=\"((?:\w|\.)+)\"" % re.escape(class_name)
        return re.search(template, dot, re.MULTILINE).groups()[0]
    except:
        raise RuntimeError("Classname label not found for %s" % class_name)


def edge(classname1, classname2):
    return '"%s" -> "%s"' % (classname1, classname2)


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_basic_diagram(status, build_context):
    """Basic inheritance diagram showing all classes"""
    dot = build_context.dots['basic_diagram']
    assert dot.count("->") == 6
    assert dot.count("label=") == 6
    assert edge("dummy.test.A", "dummy.test.B") in dot
    assert edge("dummy.test.A", "dummy.test.C") in dot
    assert edge("dummy.test.B", "dummy.test.D") in dot
    assert edge("dummy.test.B", "dummy.test.E") in dot
    assert edge("dummy.test.C", "dummy.test.D") in dot
    assert edge("dummy.test.C", "dummy.test.F") in dot
    assert get_label("dummy.test.A", dot) == "dummy.test.A"


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_parts(status, build_context):
    """Inheritance diagram using :parts: 1 option"""
    dot = build_context.dots['diagram_w_parts']
    assert dot.count("->") == 6
    assert dot.count("label=") == 6
    assert get_label("dummy.test.A", dot) == "A"
    assert get_label("dummy.test.B", dot) == "B"
    assert get_label("dummy.test.C", dot) == "C"
    assert get_label("dummy.test.D", dot) == "D"
    assert get_label("dummy.test.E", dot) == "E"
    assert get_label("dummy.test.F", dot) == "F"


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_1_top_class(status, build_context):
    """Inheritance diagram with 1 top class"""
    # :top-classes: dummy.test.B
    # rendering should be
    #
    #     B
    #    / \
    #   E   D
    #
    dot = build_context.dots['diagram_w_1_top_class']
    assert dot.count("->") == 2
    assert dot.count("label=") == 3
    assert edge("dummy.test.B", "dummy.test.D") in dot
    assert edge("dummy.test.B", "dummy.test.E") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_2_top_classes(status, build_context):
    """Inheritance diagram with 2 top classes"""
    # :top-classes: dummy.test.B, dummy.test.C
    # Note: we're specifying separate classes, not the entire module here
    # rendering should be
    #
    #     B   C
    #    / \ / \
    #   E   D   F
    #
    dot = build_context.dots['diagram_w_2_top_classes']
    assert dot.count("->") == 4
    assert dot.count("label=") == 5
    assert edge("dummy.test.B", "dummy.test.D") in dot
    assert edge("dummy.test.C", "dummy.test.D") in dot
    assert edge("dummy.test.B", "dummy.test.E") in dot
    assert edge("dummy.test.C", "dummy.test.F") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_module_w_2_top_classes(status, build_context):
    """Inheritance diagram with 2 top classes and specifying the entire
    module"""
    # rendering should be
    #
    #     B   C
    #    / \ / \
    #   E   D   F
    #
    dot = build_context.dots['diagram_module_w_2_top_classes']
    assert dot.count("->") == 4
    assert dot.count("label=") == 5
    assert edge("dummy.test.B", "dummy.test.D") in dot
    assert edge("dummy.test.C", "dummy.test.D") in dot
    assert edge("dummy.test.B", "dummy.test.E") in dot
    assert edge("dummy.test.C", "dummy.test.F") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_nested_classes(status, build_context):
    """Inheritance diagram involving a base class nested within another class
    """
    dot = build_context.dots['diagram_w_nested_classes']
    assert dot.count("->") == 1
    assert dot.count("label=") == 3
    assert edge("dummy.test_nested.A.B", "dummy.test_nested.C") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_classe(status, build_context):
    """Inheritance diagram from a complex module
    where a specific class is designed

    Private classes are not displayed.
    """
    #
    #       A
    #      / \
    #     B   C
    #      \ /
    #       D
    #
    dot = build_context.dots['diagram_class']
    assert dot.count("->") == 4
    assert dot.count("label=") == 4
    assert edge("dummy.test.B", "dummy.test.D") in dot
    assert edge("dummy.test.C", "dummy.test.D") in dot
    assert edge("dummy.test.A", "dummy.test.B") in dot
    assert edge("dummy.test.A", "dummy.test.C") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_module_w_top_and_private(status, build_context):
    """Inheritance diagram from a complex module
    where a top class is specified and private classes displayed.
    """
    #
    #       G
    #      / \
    #    _H   I
    #    /
    #   F
    #
    dot = build_context.dots['diagram_module_w_top_and_private']
    assert dot.count("->") == 3
    assert dot.count("label=") == 4
    assert edge("dummy.test_module.G", "dummy.test_module._H") in dot
    assert edge("dummy.test_module._H", "dummy.test_module.F") in dot
    assert edge("dummy.test_module.G", "dummy.test_module.I") in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_uml(status, build_context):
    """Check that the empty arrow is part of the UML diagram
    """
    dot = build_context.dots['diagram_w_uml']
    assert 'arrowtail="empty"' in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_direction(status, build_context):
    """Check that the empty arrow is part of the UML diagram
    """
    dot = build_context.dots['diagram_w_direction']
    assert 'rankdir=TB' in dot


@pytest.mark.usefixtures('if_graphviz_found')
@pytest.mark.sphinx(buildername="html", testroot="inheritance")
def test_diagram_w_homonyms(status, build_context):
    """Test that homonymous classes are not merged together
    """
    dot = build_context.dots['diagram_w_homonyms']
    assert dot.count("->") == 1
    assert dot.count("label=") == 3
    assert edge("dummy.test_homonyms.A", "dummy.test_homonyms.B.A") in dot
    assert get_label("dummy.test_homonyms.A", dot) == "A"
    assert get_label("dummy.test_homonyms.B.A", dot) == "A"


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_png_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()

    pattern = ('<div class="figure align-default" id="id1">\n'
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

    content = (app.outdir / 'index.html').read_text()

    pattern = ('<div class="figure align-default" id="id1">\n'
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

    content = (app.outdir / 'python.tex').read_text()

    pattern = ('\\\\begin{figure}\\[htbp]\n\\\\centering\n\\\\capstart\n\n'
               '\\\\sphinxincludegraphics\\[\\]{inheritance-\\w+.pdf}\n'
               '\\\\caption{Test Foo!}\\\\label{\\\\detokenize{index:id1}}\\\\end{figure}')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram',
                    srcdir='ext-inheritance_diagram-alias')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_html_alias(app, diagram_lookup, status, warning):
    app.config.inheritance_alias = {'test.Foo': 'alias.Foo'}
    app.builder.build_all()

    dot = diagram_lookup.dots["index"]
    assert dot.count("->") == 2
    assert dot.count("label=") == 3
    assert edge("test.Foo", "test.Bar") in dot
    assert edge("test.Bar", "test.Baz") in dot
    assert get_label("test.Foo", dot) == "alias.Foo"
    assert get_label("test.Baz", dot) == "test.Baz"
    assert get_label("test.Bar", dot) == "test.Bar"

    content = (app.outdir / 'index.html').read_text()
    pattern = ('<div class="figure align-default" id="id1">\n'
               '<div class="graphviz">'
               '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
               'class="inheritance graphviz" /></div>\n<p class="caption">'
               '<span class="caption-text">Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


def test_import_classes(rootdir):
    from sphinx.parsers import Parser, RSTParser
    from sphinx.util.i18n import CatalogInfo

    try:
        sys.path.append(rootdir / 'test-ext-inheritance_diagram')
        from example.sphinx import DummyClass

        # got exception for unknown class or module
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('unknown', None)
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('unknown.Unknown', None)

        # got exception InheritanceException for wrong class or module
        # not AttributeError (refs: #4019)
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('unknown', '.')
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('unknown.Unknown', '.')
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('.', None)

        # a module having no classes
        classes = ext.import_classes('sphinx', None)
        assert classes == []

        classes = ext.import_classes('sphinx', 'foo')
        assert classes == []

        # all of classes in the module
        classes = ext.import_classes('sphinx.parsers', None)
        assert set(classes) == {Parser, RSTParser}

        # specified class in the module
        classes = ext.import_classes('sphinx.parsers.Parser', None)
        assert classes == [Parser]

        # specified class in current module
        classes = ext.import_classes('Parser', 'sphinx.parsers')
        assert classes == [Parser]

        # relative module name to current module
        classes = ext.import_classes('i18n.CatalogInfo', 'sphinx.util')
        assert classes == [CatalogInfo]

        # got exception for functions
        with pytest.raises(ext.InheritanceException):
            ext.import_classes('encode_uri', 'sphinx.util')

        # import submodule on current module (refs: #3164)
        classes = ext.import_classes('sphinx', 'example')
        assert classes == [DummyClass]
    finally:
        sys.path.pop()
