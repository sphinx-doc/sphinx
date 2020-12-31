"""
    test_ext_autodoc_autocmodule
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_mock_imports': ['missing_module',
                                                            'missing_package1',
                                                            'missing_package2',
                                                            'missing_package3',
                                                            'sphinx.missing_module4']})
@pytest.mark.usefixtures("rollback_sysmodules")
def test_subclass_of_mocked_object(app):
    sys.modules.pop('target', None)  # unload target module to clear the module cache

    options = {'members': True}
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert '.. py:class:: Inherited(*args: Any, **kwargs: Any)' in actual
