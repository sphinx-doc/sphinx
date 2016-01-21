# -*- coding: utf-8 -*-
"""
    test_inheritance
    ~~~~~~~~~~~~~~~~

    Tests for :mod:`sphinx.ext.inheritance_diagram` module.

    :copyright: Copyright 2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import pytest
from sphinx.ext.inheritance_diagram import InheritanceDiagram

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
