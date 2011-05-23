# -*- coding: utf-8 -*-
"""
    Sphinx test suite utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import StringIO
import tempfile
import shutil
import re
from codecs import open

try:
    from functools import wraps
except ImportError:
    # functools is new in 2.4
    wraps = lambda f: (lambda w: w)

from sphinx import application
from sphinx.ext.autodoc import AutoDirective

from path import path

from nose import tools, SkipTest


__all__ = [
    'test_root', 'raises', 'raises_msg',
    'skip_if', 'skip_unless', 'skip_unless_importable', 'Struct',
    'ListOutput', 'TestApp', 'with_app', 'gen_with_app',
    'path', 'with_tempdir', 'write_file',
    'sprint', 'remove_unicode_literals',
]


test_root = path(__file__).parent.joinpath('root').abspath()


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
        assert msg in str(err), "\"%s\" not in \"%s\"" % (msg, err)
    else:
        raise AssertionError('%s did not raise %s' %
                             (func.__name__, _excstr(exc)))

def skip_if(condition, msg=None):
    """Decorator to skip test if condition is true."""
    def deco(test):
        @tools.make_decorator(test)
        def skipper(*args, **kwds):
            if condition:
                raise SkipTest(msg or 'conditional skip')
            return test(*args, **kwds)
        return skipper
    return deco

def skip_unless(condition, msg=None):
    """Decorator to skip test if condition is false."""
    return skip_if(not condition, msg)

def skip_unless_importable(module, msg=None):
    """Decorator to skip test if module is not importable."""
    try:
        __import__(module)
    except ImportError:
        return skip_if(True, msg)
    else:
        return skip_if(False, msg)


class Struct(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class ListOutput(object):
    """
    File-like object that collects written text in a list.
    """
    def __init__(self, name):
        self.name = name
        self.content = []

    def reset(self):
        del self.content[:]

    def write(self, text):
        self.content.append(text)


class TestApp(application.Sphinx):
    """
    A subclass of :class:`Sphinx` that runs on the test root, with some
    better default values for the initialization parameters.
    """

    def __init__(self, srcdir=None, confdir=None, outdir=None, doctreedir=None,
                 buildername='html', confoverrides=None,
                 status=None, warning=None, freshenv=None,
                 warningiserror=None, tags=None,
                 confname='conf.py', cleanenv=False):

        application.CONFIG_FILENAME = confname

        self.cleanup_trees = [test_root / 'generated']

        if srcdir is None:
            srcdir = test_root
        if srcdir == '(temp)':
            tempdir = path(tempfile.mkdtemp())
            self.cleanup_trees.append(tempdir)
            temproot = tempdir / 'root'
            test_root.copytree(temproot)
            srcdir = temproot
        else:
            srcdir = path(srcdir)
        self.builddir = srcdir.joinpath('_build')
        if confdir is None:
            confdir = srcdir
        if outdir is None:
            outdir = srcdir.joinpath(self.builddir, buildername)
            if not outdir.isdir():
                outdir.makedirs()
            self.cleanup_trees.insert(0, outdir)
        if doctreedir is None:
            doctreedir = srcdir.joinpath(srcdir, self.builddir, 'doctrees')
            if cleanenv:
                self.cleanup_trees.insert(0, doctreedir)
        if confoverrides is None:
            confoverrides = {}
        if status is None:
            status = StringIO.StringIO()
        if warning is None:
            warning = ListOutput('stderr')
        if freshenv is None:
            freshenv = False
        if warningiserror is None:
            warningiserror = False

        application.Sphinx.__init__(self, srcdir, confdir, outdir, doctreedir,
                                    buildername, confoverrides, status, warning,
                                    freshenv, warningiserror, tags)

    def cleanup(self, doctrees=False):
        AutoDirective._registry.clear()
        for tree in self.cleanup_trees:
            shutil.rmtree(tree, True)


def with_app(*args, **kwargs):
    """
    Make a TestApp with args and kwargs, pass it to the test and clean up
    properly.
    """
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            app = TestApp(*args, **kwargs)
            func(app, *args2, **kwargs2)
            # don't execute cleanup if test failed
            app.cleanup()
        return deco
    return generator


def gen_with_app(*args, **kwargs):
    """
    Decorate a test generator to pass a TestApp as the first argument to the
    test generator when it's executed.
    """
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            app = TestApp(*args, **kwargs)
            for item in func(app, *args2, **kwargs2):
                yield item
            # don't execute cleanup if test failed
            app.cleanup()
        return deco
    return generator


def with_tempdir(func):
    def new_func(*args, **kwds):
        tempdir = path(tempfile.mkdtemp())
        func(tempdir, *args, **kwds)
        tempdir.rmtree()
    new_func.__name__ = func.__name__
    return new_func


def write_file(name, contents, encoding=None):
    if encoding is None:
        mode = 'wb'
        if isinstance(contents, unicode):
            contents = contents.encode('ascii')
    else:
        mode = 'w'
    f = open(str(name), mode, encoding=encoding)
    f.write(contents)
    f.close()


def sprint(*args):
    sys.stderr.write(' '.join(map(str, args)) + '\n')

_unicode_literals_re = re.compile(r'u(".*?")|u(\'.*?\')')
def remove_unicode_literals(s):
    return _unicode_literals_re.sub(lambda x: x.group(1) or x.group(2), s)
