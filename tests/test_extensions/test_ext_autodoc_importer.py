from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from sphinx.ext.autodoc.importer import import_module

if TYPE_CHECKING:
    from pathlib import Path


def test_import_native_module_stubs(rootdir: Path) -> None:
    fish_licence_root = rootdir / 'test-ext-apidoc-duplicates'

    sys_path = list(sys.path)
    sys.path.insert(0, str(fish_licence_root))
    halibut = import_module('fish_licence.halibut')
    sys.path[:] = sys_path

    assert halibut.__file__.endswith('halibut.pyi')
    assert halibut.__spec__.origin.endswith('halibut.pyi')

    halibut_path = Path(halibut.__file__).resolve()
    assert halibut_path.is_file()
    assert halibut_path == fish_licence_root / 'fish_licence' / 'halibut.pyi'
