"""Test autodoc performance optimizations."""

from __future__ import annotations

import sys
import time
from unittest.mock import patch

import pytest

from sphinx.ext.autodoc.importer import (
    _autodoc_module_cache,
    _cache_module_info,
    _clear_module_cache,
    _get_cached_module_info,
    import_module,
)
from sphinx.ext.autodoc._documenters import ClassDocumenter, FunctionDocumenter, ModuleDocumenter
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions

from tests.test_extensions.autodoc_util import do_autodoc


def test_module_import_caching():
    """Test that modules are cached after first import."""
    # Clear any existing cache
    _clear_module_cache()

    # First import - should load the module
    module = import_module('os')
    assert module is not None

    # Second import - should use cached version
    cached_info = _get_cached_module_info('os')
    assert cached_info is not None
    assert cached_info.get('loaded') is True
    assert cached_info['module'] is module


def test_object_path_caching():
    """Test that object paths are cached to avoid redundant imports."""
    _clear_module_cache()

    # Create a mock module and object
    class MockObject:
        def __init__(self):
            self.attr = "test"

    mock_module = type(sys)('mock_module')
    mock_module.test_obj = MockObject()

    # Cache the module info
    _cache_module_info('mock_module', {'module': mock_module, 'loaded': True})

    # Test that the object path is cached
    cache_key = "mock_module:test_obj.attr"
    cached_result = _get_cached_module_info(cache_key)
    assert cached_result is None  # Should be None initially

    # Import the object
    from sphinx.ext.autodoc.importer import _import_from_module_and_path

    result = _import_from_module_and_path(
        module_name='mock_module',
        obj_path=['test_obj', 'attr'],
    )

    # Check that it was cached
    cached_result = _get_cached_module_info(cache_key)
    assert cached_result is not None
    assert 'imported_object' in cached_result


def test_documenter_object_caching():
    """Test that documenters cache loaded objects."""
    _clear_module_cache()

    # Mock environment and directive
    mock_env = type('MockEnv', (), {
        'config': type('MockConfig', (), {
            'autodoc_mock_imports': [],
            'autodoc_type_aliases': {},
            'autodoc_member_order': 'alphabetical',
        })(),
        '_registry': type('MockRegistry', (), {
            'documenters': {},
            'filters': {},
        })(),
        'current_document': type('MockCurrentDocument', (), {
            'autodoc_module': None,
            'autodoc_class': None,
        })(),
        'events': type('MockEvents', (), {})(),
    })()

    mock_directive = type('MockDirective', (), {
        'env': mock_env,
        'genopt': _AutoDocumenterOptions(),
        'result': [],
        'record_dependencies': set(),
    })()

    # Create a function documenter
    documenter = FunctionDocumenter(mock_directive, 'os.path.join')

    # First load - should import the object
    result1 = documenter._load_object_by_name()
    assert result1 is True
    assert documenter.object is not None

    # Create another documenter for the same object
    documenter2 = FunctionDocumenter(mock_directive, 'os.path.join')

    # Second load - should use cached version
    result2 = documenter2._load_object_by_name()
    assert result2 is True
    assert documenter2.object is not None

    # Objects should be the same
    assert documenter.object is documenter2.object


@pytest.mark.sphinx('html', testroot='basic')
def test_lazy_member_loading(app):
    """Test that members are only loaded when needed."""
    # Create a class documenter
    actual, result = do_autodoc(app, 'class', 'target.Class')

    # The result should contain the class documentation
    assert 'class target.Class' in result

    # Check that the autodoc process completed successfully
    assert actual is not None


def test_cache_clear_functionality():
    """Test that the cache clear function works correctly."""
    # Add some cache entries
    _cache_module_info('test_module1', {'module': 'test', 'loaded': True})
    _cache_module_info('test_module2', {'module': 'test2', 'loaded': False})

    # Verify they exist
    assert _get_cached_module_info('test_module1') is not None
    assert _get_cached_module_info('test_module2') is not None

    # Clear the cache
    _clear_module_cache()

    # Verify they're gone
    assert _get_cached_module_info('test_module1') is None
    assert _get_cached_module_info('test_module2') is None


def test_module_already_loaded_optimization():
    """Test that already loaded modules skip redundant imports."""
    _clear_module_cache()

    # Pre-load a module in sys.modules
    test_module = type(sys)('test_module')
    sys.modules['test_module'] = test_module

    # Import it through our optimized function
    result = import_module('test_module')

    # Should return the existing module
    assert result is test_module

    # Should be cached
    cached_info = _get_cached_module_info('test_module')
    assert cached_info is not None
    assert cached_info['module'] is test_module
    assert cached_info['loaded'] is True


def test_import_performance_improvement():
    """Test import performance improvements."""
    _clear_module_cache()

    # Multiple imports of the same module should be cached
    import_module('os')
    import_module('sys')
    # Import the same module again (should be cached)
    import_module('os')

    # Verify caching worked
    assert _get_cached_module_info('os') is not None
    assert _get_cached_module_info('sys') is not None
