# noqa: I002 as 'from __future__ import annotations' prevents Python 3.14
# forward references from causing issues, so we must skip it here.

import pytest

from sphinx.util import inspect
from sphinx.util.typing import stringify_annotation

try:
    from annotationlib import ForwardRef  # type: ignore[import-not-found]
except ImportError:
    pytest.skip('Requires annotationlib (Python 3.14+).', allow_module_level=True)


def forward_reference_in_args(x: Foo) -> None:  # type: ignore[name-defined] # noqa: F821
    pass


def forward_reference_in_return() -> Foo:  # type: ignore[name-defined] # noqa: F821
    pass


def test_signature_forwardref_in_args() -> None:
    sig = inspect.signature(forward_reference_in_args)

    assert sig.return_annotation is None

    assert len(sig.parameters)
    assert 'x' in sig.parameters
    param = sig.parameters['x']

    ann = param.annotation
    assert isinstance(ann, ForwardRef)
    assert ann.__arg__ == 'Foo'
    assert ann.__forward_is_class__ is False
    assert ann.__forward_module__ is None
    assert ann.__owner__ is not None
    assert stringify_annotation(ann) == 'Foo'


def test_signature_forwardref_in_return() -> None:
    sig = inspect.signature(forward_reference_in_return)

    assert sig.parameters == {}

    ann = sig.return_annotation
    assert isinstance(ann, ForwardRef)
    assert ann.__arg__ == 'Foo'
    assert ann.__forward_is_class__ is False
    assert ann.__forward_module__ is None
    assert ann.__owner__ is not None
    assert stringify_annotation(ann) == 'Foo'
