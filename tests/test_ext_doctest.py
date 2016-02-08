# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app

cleanup_called = 0


@with_app(buildername='doctest', testroot='doctest')
def test_build(app, status, warning):
    global cleanup_called
    cleanup_called = 0
    app.builder.build_all()
    if app.statuscode != 0:
        assert False, 'failures in doctests:' + status.getvalue()
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'


def cleanup_call():
    global cleanup_called
    cleanup_called += 1
