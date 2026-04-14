"""
    test_extension
    ~~~~~~~~~~~~~~

    Test the sphinx.extension module.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest import mock

import pytest

from sphinx.errors import VersionRequirementError
from sphinx.extension import Extension, verify_needs_extensions


def test_verify_needs_extensions_accepted():
    """Extension with version satisfying the requirement should be accepted."""
    app = mock.Mock()
    app.extensions = {
        'some_ext': Extension('some_ext', mock.Mock(), version='0.10.0'),
    }
    config = mock.Mock()
    config.needs_extensions = {'some_ext': '0.6'}

    # Should not raise
    verify_needs_extensions(app, config)


def test_verify_needs_extensions_rejected():
    """Extension with version below the requirement should be rejected."""
    app = mock.Mock()
    app.extensions = {
        'some_ext': Extension('some_ext', mock.Mock(), version='0.5'),
    }
    config = mock.Mock()
    config.needs_extensions = {'some_ext': '0.6'}

    with pytest.raises(VersionRequirementError):
        verify_needs_extensions(app, config)


def test_verify_needs_extensions_unknown_version():
    """Extension with unknown version should be rejected."""
    app = mock.Mock()
    app.extensions = {
        'some_ext': Extension('some_ext', mock.Mock()),
    }
    config = mock.Mock()
    config.needs_extensions = {'some_ext': '0.6'}

    with pytest.raises(VersionRequirementError):
        verify_needs_extensions(app, config)


def test_verify_needs_extensions_version_equal():
    """Extension with version exactly matching the requirement should be accepted."""
    app = mock.Mock()
    app.extensions = {
        'some_ext': Extension('some_ext', mock.Mock(), version='0.6.0'),
    }
    config = mock.Mock()
    config.needs_extensions = {'some_ext': '0.6.0'}

    # Should not raise
    verify_needs_extensions(app, config)


def test_verify_needs_extensions_not_loaded():
    """Missing extension should produce a warning, not an error."""
    app = mock.Mock()
    app.extensions = {}
    config = mock.Mock()
    config.needs_extensions = {'some_ext': '0.6'}

    # Should not raise, just warn
    verify_needs_extensions(app, config)


def test_verify_needs_extensions_none():
    """When needs_extensions is None, nothing should happen."""
    app = mock.Mock()
    config = mock.Mock()
    config.needs_extensions = None

    # Should not raise
    verify_needs_extensions(app, config)


def test_verify_needs_extensions_double_digit_version():
    """Version 0.10.0 should be greater than 0.6.0 (the exact bug from #9711)."""
    app = mock.Mock()
    app.extensions = {
        'sphinx_gallery.gen_gallery': Extension(
            'sphinx_gallery.gen_gallery', mock.Mock(), version='0.10.0'),
    }
    config = mock.Mock()
    config.needs_extensions = {'sphinx_gallery.gen_gallery': '0.6.0'}

    # Should not raise - 0.10.0 > 0.6.0
    verify_needs_extensions(app, config)
