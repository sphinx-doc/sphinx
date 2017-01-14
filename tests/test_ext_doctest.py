# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import platform
import pytest
from sphinx.ext.doctest import TestDirective as _TestDirective

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


def test_pyversion(monkeypatch):
    def python_version():
        return '3.3'
    monkeypatch.setattr(platform, 'python_version', python_version)
    td = _TestDirective(*([None] * 9))
    assert td.proper_pyversion('<', '3.4') is True
    assert td.proper_pyversion('<', '3.2') is False
    assert td.proper_pyversion('<=', '3.4') is True
    assert td.proper_pyversion('<=', '3.3') is True
    assert td.proper_pyversion('==', '3.3') is True
    assert td.proper_pyversion('>=', '3.4') is False
    assert td.proper_pyversion('>=', '3.2') is True
    assert td.proper_pyversion('>', '3.4') is False
    assert td.proper_pyversion('>', '3.2') is True
    assert td.proper_pyversion('>', '3.3a0') is True


def cleanup_call():
    global cleanup_called
    cleanup_called += 1
