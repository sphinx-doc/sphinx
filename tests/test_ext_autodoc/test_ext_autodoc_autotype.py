"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import pytest

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_autotype_TypeAlias() -> None:
    actual = do_autodoc('type', 'target.typed_vars.Alias')
    assert actual == [
        '',
        '.. py:type:: Alias',
        '   :module: target.typed_vars',
        '   :canonical: ~target.typed_vars.Derived',
        '',
    ]


def test_autotype_GenericAlias() -> None:
    actual = do_autodoc('type', 'target.genericalias.T')
    assert actual == [
        '',
        '.. py:type:: T',
        '   :module: target.genericalias',
        '   :canonical: ~typing.List[int]',
        '',
        '   A list of int',
        '',
    ]
