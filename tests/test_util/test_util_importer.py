"""Test sphinx.util._importer."""

from __future__ import annotations

import pytest

from sphinx.errors import ExtensionError
from sphinx.util._importer import import_object


def test_import_object() -> None:
    module = import_object('sphinx')
    assert module.__name__ == 'sphinx'

    module = import_object('sphinx.application')
    assert module.__name__ == 'sphinx.application'

    obj = import_object('sphinx.application.Sphinx')
    assert obj.__name__ == 'Sphinx'

    with pytest.raises(ExtensionError) as exc:
        import_object('sphinx.unknown_module')
    assert exc.value.args[0] == 'Could not import sphinx.unknown_module'

    with pytest.raises(ExtensionError) as exc:
        import_object('sphinx.unknown_module', 'my extension')
    expected = 'Could not import sphinx.unknown_module (needed for my extension)'
    assert exc.value.args[0] == expected
