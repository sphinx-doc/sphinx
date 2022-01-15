"""
    test_ext_autodoc_preserve_defaults
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_preserve_defaults': True})
def test_preserve_defaults(app):
    if sys.version_info < (3, 8):
        color = "16777215"
    else:
        color = "0xFFFFFF"

    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.preserve_defaults', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.preserve_defaults',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Class.meth(name: str = CONSTANT, sentinel: typing.Any = '
        'SENTINEL, now: datetime.datetime = datetime.now(), color: int = %s) -> None' % color,
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: foo(name: str = CONSTANT, sentinel: typing.Any = SENTINEL, '
        'now: datetime.datetime = datetime.now(), color: int = %s) -> None' % color,
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
    ]
