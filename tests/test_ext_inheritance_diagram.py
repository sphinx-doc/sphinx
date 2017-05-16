# -*- coding: utf-8 -*-
"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
from sphinx.ext.inheritance_diagram import InheritanceException, import_classes
import pytest


@pytest.mark.sphinx('html', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()

    pattern = ('<div class="figure" id="id1">\n'
               '<img src="_images/inheritance-\\w+.png" alt="Inheritance diagram of test.Foo" '
               'class="inheritance"/>\n<p class="caption"><span class="caption-text">'
               'Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


@pytest.mark.sphinx('latex', testroot='ext-inheritance_diagram')
@pytest.mark.usefixtures('if_graphviz_found')
def test_inheritance_diagram_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'Python.tex').text()

    pattern = ('\\\\begin{figure}\\[htbp]\n\\\\centering\n\\\\capstart\n\n'
               '\\\\includegraphics{inheritance-\\w+.pdf}\n'
               '\\\\caption{Test Foo!}\\\\label{\\\\detokenize{index:id1}}\\\\end{figure}')
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
