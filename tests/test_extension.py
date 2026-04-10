"""
    test_extension
    ~~~~~~~~~~~~~~

    Test sphinx.extension module.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest import mock

import pytest

from sphinx.errors import VersionRequirementError
from sphinx.extension import Extension, verify_needs_extensions


def test_verify_needs_extensions_version_comparison():
    """Test that needs_extensions compares versions properly, not as strings.

    This is a regression test for the bug where '0.10.0' was considered
    less than '0.6.0' because string comparison was used instead of
    proper version comparison.
    """
    extension = Extension('test_ext', mock.Mock(), version='0.10.0')

    app = mock.Mock()
    app.extensions = {'test_ext': extension}

    config = mock.Mock()

    # Should pass: installed 0.10.0 >= required 0.6.0
    config.needs_extensions = {'test_ext': '0.6.0'}
    verify_needs_extensions(app, config)

    # Should pass: installed 0.10.0 >= required 0.10.0 (equal)
    config.needs_extensions = {'test_ext': '0.10.0'}
    verify_needs_extensions(app, config)

    # Should fail: installed 0.10.0 < required 0.11.0
    config.needs_extensions = {'test_ext': '0.11.0'}
    with pytest.raises(VersionRequirementError):
        verify_needs_extensions(app, config)


def test_verify_needs_extensions_unknown_version():
    """Test that unknown version always raises."""
    extension = Extension('test_ext', mock.Mock(), version='unknown version')

    app = mock.Mock()
    app.extensions = {'test_ext': extension}

    config = mock.Mock()
    config.needs_extensions = {'test_ext': '0.1'}

    with pytest.raises(VersionRequirementError):
        verify_needs_extensions(app, config)


def test_verify_needs_extensions_missing_extension():
    """Test that missing extension logs a warning but doesn't raise."""
    app = mock.Mock()
    app.extensions = {}

    config = mock.Mock()
    config.needs_extensions = {'missing_ext': '0.1'}

    # Should not raise, just warn
    verify_needs_extensions(app, config)
