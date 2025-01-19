from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from sphinx.ext.autodoc.importer import import_module

if TYPE_CHECKING:
    from pathlib import Path


def test_import_native_module_stubs(rootdir: Path) -> None:
    sys_path = list(sys.path)
    sys.path.insert(0, str(rootdir / 'test-ext-apidoc-duplicates'))
    halibut = import_module('fish_licence.halibut')
    assert halibut.__file__.endswith('halibut.pyi')
    assert halibut.__spec__.origin.endswith('halibut.pyi')
    sys.path[:] = sys_path
