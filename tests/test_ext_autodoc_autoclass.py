"""
    test_ext_autodoc_autoclass
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_generic_class(app):
    actual = do_autodoc(app, 'class', 'target.classes.Qux')
    assert list(actual) == [
        '',
        '.. py:class:: Qux(x, y)',
        '   :module: target.classes',
        '',
    ]
