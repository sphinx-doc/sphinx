# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest
from sphinx.ext.doctest import compare_version

cleanup_called = 0


@pytest.mark.sphinx('doctest', testroot='doctest')
def test_build(app, status, warning):
    global cleanup_called
    cleanup_called = 0
    app.builder.build_all()
    if app.statuscode != 0:
        assert False, 'failures in doctests:' + status.getvalue()
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'


def test_compare_version():
    assert compare_version('3.3', '3.4', '<') is True
    assert compare_version('3.3', '3.2', '<') is False
    assert compare_version('3.3', '3.4', '<=') is True
    assert compare_version('3.3', '3.2', '<=') is False
    assert compare_version('3.3', '3.3', '==') is True
    assert compare_version('3.3', '3.4', '==') is False
    assert compare_version('3.3', '3.2', '>=') is True
    assert compare_version('3.3', '3.4', '>=') is False
    assert compare_version('3.3', '3.2', '>') is True
    assert compare_version('3.3', '3.4', '>') is False
    with pytest.raises(ValueError):
        compare_version('3.3', '3.4', '+')


def cleanup_call():
    global cleanup_called
    cleanup_called += 1
