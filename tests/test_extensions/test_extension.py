"""Test sphinx.extension module."""

import pytest

from sphinx.errors import VersionRequirementError
from sphinx.extension import Extension, verify_needs_extensions


@pytest.mark.sphinx('html', testroot='root')
def test_needs_extensions(app):
    # empty needs_extensions
    assert app.config.needs_extensions == {}
    verify_needs_extensions(app, app.config)

    # needs_extensions fulfilled
    app.config.needs_extensions = {'test.extension': '3.9'}
    app.extensions['test.extension'] = Extension(
        'test.extension', 'test.extension', version='3.10'
    )
    verify_needs_extensions(app, app.config)

    # needs_extensions not fulfilled
    app.config.needs_extensions = {'test.extension': '3.11'}
    app.extensions['test.extension'] = Extension(
        'test.extension', 'test.extension', version='3.10'
    )
    with pytest.raises(VersionRequirementError):
        verify_needs_extensions(app, app.config)
