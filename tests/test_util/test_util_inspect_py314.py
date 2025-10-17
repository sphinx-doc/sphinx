# noqa: I002 as 'from __future__ import annotations' prevents Python 3.14
# forward references from causing issues, so we must skip it here.

import sys

import pytest

from sphinx.util import inspect

if sys.version_info[0:2] < (3, 14):
    pytest.skip('These tests are for Python 3.14+', allow_module_level=True)


def forward_reference_in_args(x: Foo) -> None:  # type: ignore[name-defined] # noqa: F821
    pass


def forward_reference_in_return() -> Foo:  # type: ignore[name-defined] # noqa: F821
    pass


def test_signature_forwardref() -> None:
    sig = inspect.stringify_signature(inspect.signature(forward_reference_in_args))
    assert sig == '(x: Foo) -> None'

    sig = inspect.stringify_signature(inspect.signature(forward_reference_in_return))
    assert sig == '() -> Foo'
