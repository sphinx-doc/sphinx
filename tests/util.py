# -*- coding: utf-8 -*-
"""
    Sphinx test suite utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import sys
import StringIO
import tempfile

from sphinx import application, builder

from path import path


__all__ = [
    'raises', 'raises_msg',
    'ErrorOutput', 'TestApp',
    'with_tempdir', 'write_file',
]


def _excstr(exc):
    if type(exc) is tuple:
        return str(tuple(map(_excstr, exc)))
    return exc.__name__

def raises(exc, func, *args, **kwds):
    """
    Raise :exc:`AssertionError` if ``func(*args, **kwds)`` does not
    raise *exc*.
    """
    try:
        func(*args, **kwds)
    except exc:
        pass
    else:
        raise AssertionError('%s did not raise %s' %
                             (func.__name__, _excstr(exc)))

def raises_msg(exc, msg, func, *args, **kwds):
    """
    Raise :exc:`AssertionError` if ``func(*args, **kwds)`` does not
    raise *exc*, and check if the message contains *msg*.
    """
    try:
        func(*args, **kwds)
    except exc, err:
        assert msg in str(err)
    else:
        raise AssertionError('%s did not raise %s' %
                             (func.__name__, _excstr(exc)))


class ErrorOutput(object):
    """
    File-like object that raises :exc:`AssertionError` on ``write()``.
    """
    def __init__(self, name):
        self.name = name

    def write(self, text):
        assert False, 'tried to write %r to %s' % (text, self.name)


class TestApp(application.Sphinx):
    """
    A subclass of :class:`Sphinx` that runs on the test root, with some
    better default values for the initialization parameters.
    """

    def __init__(self, srcdir=None, confdir=None, outdir=None, doctreedir=None,
                 buildername='html', confoverrides=None, status=None, warning=None,
                 freshenv=None, confname='conf.py'):

        application.CONFIG_FILENAME = confname

        if srcdir is None:
            srcdir = path(__file__).parent.joinpath('root').abspath()
        else:
            srcdir = path(srcdir)
        if confdir is None:
            confdir = srcdir
        if outdir is None:
            outdir = srcdir.joinpath('_build', buildername)
        if doctreedir is None:
            doctreedir = srcdir.joinpath(srcdir, '_build', 'doctrees')
        if confoverrides is None:
            confoverrides = {}
        if status is None:
            status = StringIO.StringIO()
        if warning is None:
            warning = ErrorOutput('stderr')
        if freshenv is None:
            freshenv = True

        application.Sphinx.__init__(self, srcdir, confdir, outdir, doctreedir,
                                    buildername, confoverrides, status, warning,
                                    freshenv)


def with_tempdir(func):
    def new_func():
        tempdir = path(tempfile.mkdtemp())
        func(tempdir)
        tempdir.rmtree()
    new_func.__name__ = func.__name__
    return new_func


def write_file(name, contents):
    f = open(str(name), 'wb')
    f.write(contents)
    f.close()
