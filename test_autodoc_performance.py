#!/usr/bin/env python3
"""Simple performance test for autodoc optimizations."""

import time
import sys
from pathlib import Path

# Add the bengal directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sphinx.ext.autodoc.importer import (
    _clear_module_cache,
    _get_cached_module_info,
    import_module,
)


def test_import_performance():
    """Test that multiple imports of the same module are cached."""
    _clear_module_cache()

    print("Testing autodoc import performance improvements...")

    # First import - should load the module
    start_time = time.time()
    module1 = import_module('os')
    first_import_time = time.time() - start_time

    # Second import - should use cached version
    start_time = time.time()
    module2 = import_module('os')
    second_import_time = time.time() - start_time

    # Third import - should be even faster due to caching
    start_time = time.time()
    module3 = import_module('os')
    third_import_time = time.time() - start_time

    print(f"First import:  {first_import_time:.4f}s")
    print(f"Second import: {second_import_time:.4f}s")
    print(f"Third import:  {third_import_time:.4f}s")

    # Verify caching is working
    cached_info = _get_cached_module_info('os')
    assert cached_info is not None, "Module should be cached"
    assert cached_info['loaded'] is True, "Module should be marked as loaded"
    assert cached_info['module'] is module1, "Cached module should be the same object"

    # Verify all imports return the same module object
    assert module1 is module2 is module3, "All imports should return the same module object"

    print("✅ Import caching is working correctly!")
    print(f"✅ Speedup: {first_import_time / max(second_import_time, 0.0001):.1f}x faster on subsequent imports")

    return True


def test_multiple_modules():
    """Test caching with multiple different modules."""
    _clear_module_cache()

    modules_to_test = ['os', 'sys', 'json', 'pathlib']

    print(f"\nTesting import of {len(modules_to_test)} different modules...")

    start_time = time.time()
    for module_name in modules_to_test:
        module = import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"
    total_time = time.time() - start_time

    print(f"Imported {len(modules_to_test)} modules in {total_time:.4f}s")

    # Verify all modules are cached
    for module_name in modules_to_test:
        cached_info = _get_cached_module_info(module_name)
        assert cached_info is not None, f"Module {module_name} should be cached"
        assert cached_info['loaded'] is True, f"Module {module_name} should be marked as loaded"

    print("✅ Multiple module caching is working correctly!")
    return True


if __name__ == "__main__":
    try:
        test_import_performance()
        test_multiple_modules()
        print("\n🎉 All performance tests passed! Autodoc optimizations are working.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
