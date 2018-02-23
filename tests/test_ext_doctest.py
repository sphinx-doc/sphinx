# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest
from packaging.specifiers import InvalidSpecifier
from packaging.version import InvalidVersion
from six import PY2

from sphinx.ext.doctest import is_allowed_version

cleanup_called = 0


@pytest.mark.sphinx('doctest', testroot='ext-doctest')
def test_build(app, status, warning):
    global cleanup_called
    cleanup_called = 0
    app.builder.build_all()
    if app.statuscode != 0:
        assert False, 'failures in doctests:' + status.getvalue()
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'


def test_is_allowed_version():
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.2', '3.3') is False
    assert is_allowed_version('<=3.4',  '3.3') is True
    assert is_allowed_version('<=3.2',  '3.3') is False
    assert is_allowed_version('==3.3',  '3.3') is True
    assert is_allowed_version('==3.4',  '3.3') is False
    assert is_allowed_version('>=3.2',  '3.3') is True
    assert is_allowed_version('>=3.4',  '3.3') is False
    assert is_allowed_version('>3.2', '3.3') is True
    assert is_allowed_version('>3.4', '3.3') is False
    assert is_allowed_version('~=3.4', '3.4.5') is True
    assert is_allowed_version('~=3.4', '3.5.0') is True

    # invalid spec
    with pytest.raises(InvalidSpecifier):
        is_allowed_version('&3.4', '3.5')

    # invalid version
    with pytest.raises(InvalidVersion):
        is_allowed_version('>3.4', 'Sphinx')


def cleanup_call():
    global cleanup_called
    cleanup_called += 1


@pytest.mark.xfail(
    PY2, reason='node.source points to document instead of filename',
)
@pytest.mark.sphinx('doctest', testroot='ext-doctest-with-autodoc')
def test_reporting_with_autodoc(app, status, warning, capfd):
    # Patch builder to get a copy of the output
    written = []
    app.builder._warn_out = written.append
    app.builder.build_all()
    lines = '\n'.join(written).split('\n')
    failures = [l for l in lines if l.startswith('File')]
    expected = [
        'File "dir/inner.rst", line 1, in default',
        'File "dir/bar.py", line ?, in default',
        'File "foo.py", line ?, in default',
        'File "index.rst", line 4, in default',
    ]
    for location in expected:
        assert location in failures
