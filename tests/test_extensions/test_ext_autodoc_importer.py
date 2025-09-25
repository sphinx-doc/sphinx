from __future__ import annotations

import sys
from pathlib import Path

from sphinx.ext.autodoc.importer import (
    _autodoc_module_cache,
    _cache_module_info,
    _clear_module_cache,
    _get_cached_module_info,
    import_module,
)


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


def test_autodoc_module_cache():
    """Test the autodoc module cache functionality."""
    # Clear any existing cache
    _clear_module_cache()
    assert len(_autodoc_module_cache) == 0

    # Test caching module info
    test_info = {'module': 'test_module', 'loaded': True}
    _cache_module_info('test_module', test_info)

    # Verify it was cached
    cached_info = _get_cached_module_info('test_module')
    assert cached_info == test_info

    # Test clearing cache
    _clear_module_cache()
    cached_info = _get_cached_module_info('test_module')
    assert cached_info is None


def test_import_module_caching():
    """Test that import_module uses caching correctly."""
    _clear_module_cache()

    # First import should load and cache the module
    module1 = import_module('os')
    cached_info1 = _get_cached_module_info('os')
    assert cached_info1 is not None
    assert cached_info1['loaded'] is True
    assert cached_info1['module'] is module1

    # Second import should use cached version
    module2 = import_module('os')
    assert module2 is module1  # Should be the same object
