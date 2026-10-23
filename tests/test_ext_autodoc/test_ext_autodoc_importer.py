from __future__ import annotations

import sys
from pathlib import Path

from sphinx.ext.autodoc._dynamic._importer import _import_module, _mangle_name


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


def test_mangle_name() -> None:
    # Tuples are class name, attribute name, mangled name
    names = [
        ('Foo', 'bar', 'bar'),
        ('Foo', '_bar', '_bar'),
        ('Foo', '__bar__', '__bar__'),
        ('Foo', '__bar', '_Foo__bar'),
        ('_Foo', '__bar', '_Foo__bar'),
        ('__Foo', '__bar', '_Foo__bar'),
        ('_', '__bar', '__bar'),
        ('__', '__bar', '__bar'),
    ]
    # Need a real class object for isclass check in _mangle_name
    cls = type('', (), {})
    for cls_name, attr_name, mangled_name in names:
        cls.__name__ = cls_name
        assert _mangle_name(cls, attr_name) == mangled_name
