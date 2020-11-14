"""
    test_ext_autodoc_autoattribute
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute(app):
    actual = do_autodoc(app, 'attribute', 'target.Class.attr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        "   :value: 'bar'",
        '',
        '   should be documented -- süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_novalue(app):
    options = {'no-value': True}
    actual = do_autodoc(app, 'attribute', 'target.Class.attr', options)
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        "   :value: 'bar'",
        '',
        '   should be documented -- süß',
        '',
    ]
