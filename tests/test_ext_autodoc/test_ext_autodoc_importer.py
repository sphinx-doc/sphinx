from __future__ import annotations

import sys
from pathlib import Path

from sphinx.ext.autodoc._dynamic._importer import _import_module


def test_import_native_module_stubs(rootdir: Path) -> None:
    fish_licence_root = rootdir / 'test-ext-apidoc-duplicates'

    sys_path = list(sys.path)
    sys.path.insert(0, str(fish_licence_root))
    halibut = _import_module('fish_licence.halibut')
    sys.path[:] = sys_path

    assert halibut.__file__.endswith('halibut.pyi')
    assert halibut.__spec__.origin.endswith('halibut.pyi')

    halibut_path = Path(halibut.__file__).resolve()
    assert halibut_path.is_file()
    assert halibut_path == fish_licence_root / 'fish_licence' / 'halibut.pyi'


def test_import_native_module_stubs_defer_annotations(rootdir: Path) -> None:
    # PEP 484: stub files are compiled as if they began with
    # ``from __future__ import annotations``, so forward references in
    # annotations must not fail at import time (issue #14354).
    fish_licence_root = rootdir / 'test-ext-apidoc-duplicates'

    sys_path = list(sys.path)
    sys.path.insert(0, str(fish_licence_root))
    try:
        halibut = _import_module('fish_licence.halibut')
    finally:
        sys.path[:] = sys_path

    annotations = halibut.Fish.__init__.__annotations__
    assert annotations['other'] == 'Fish'
