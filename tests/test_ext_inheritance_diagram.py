# -*- coding: utf-8 -*-
"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from util import with_app, rootdir, raises
from sphinx.ext.inheritance_diagram import InheritanceException, import_classes


@with_app('html', testroot='ext-inheritance_diagram')
def test_inheritance_diagram_html(app, status, warning):
    app.builder.build_all()


def test_import_classes():
    from sphinx.application import Sphinx, TemplateBridge
    from sphinx.util.i18n import CatalogInfo

    try:
        sys.path.append(rootdir / 'roots/test-ext-inheritance_diagram')
        from example.sphinx import DummyClass

        # got exception for unknown class or module
        raises(InheritanceException, import_classes, 'unknown', None)
        raises(InheritanceException, import_classes, 'unknown.Unknown', None)

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
        raises(InheritanceException, import_classes, 'encode_uri', 'sphinx.util')

        # import submodule on current module (refs: #3164)
        classes = import_classes('sphinx', 'example')
        assert classes == [DummyClass]
    finally:
        sys.path.pop()
