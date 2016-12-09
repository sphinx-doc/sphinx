# -*- coding: utf-8 -*-
"""
    Sphinx test suite utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import tempfile
from functools import wraps

from six import StringIO, string_types

from nose import tools, SkipTest

from docutils import nodes
from docutils.parsers.rst import directives, roles

from sphinx import application
from sphinx.builders.latex import LaTeXBuilder
from sphinx.theming import Theme
from sphinx.ext.autodoc import AutoDirective
from sphinx.pycode import ModuleAnalyzer

from path import path, repr_as  # NOQA


__all__ = [
    'rootdir', 'tempdir', 'raises', 'raises_msg',
    'skip_if', 'skip_unless', 'skip_unless_importable', 'Struct',
    'ListOutput', 'TestApp', 'with_app', 'gen_with_app',
    'path', 'with_tempdir',
    'sprint', 'remove_unicode_literals',
]


rootdir = path(os.path.dirname(__file__) or '.').abspath()
tempdir = path(os.environ['SPHINX_TEST_TEMPDIR']).abspath()


def _excstr(exc):
    if type(exc) is tuple:
        return str(tuple(map(_excstr, exc)))
    return exc.__name__


def raises(exc, func, *args, **kwds):
    """Raise AssertionError if ``func(*args, **kwds)`` does not raise *exc*."""
    try:
        func(*args, **kwds)
    except exc:
        pass
    else:
        raise AssertionError('%s did not raise %s' %
                             (func.__name__, _excstr(exc)))


def raises_msg(exc, msg, func, *args, **kwds):
    """Raise AssertionError if ``func(*args, **kwds)`` does not raise *exc*,
    and check if the message contains *msg*.
    """
    try:
        func(*args, **kwds)
    except exc as err:
        assert msg in str(err), "\"%s\" not in \"%s\"" % (msg, err)
    else:
        raise AssertionError('%s did not raise %s' %
                             (func.__name__, _excstr(exc)))


def assert_re_search(regex, text, flags=0):
    if not re.search(regex, text, flags):
        assert False, '%r did not match %r' % (regex, text)


def assert_not_re_search(regex, text, flags=0):
    if re.search(regex, text, flags):
        assert False, '%r did match %r' % (regex, text)


def assert_startswith(thing, prefix):
    if not thing.startswith(prefix):
        assert False, '%r does not start with %r' % (thing, prefix)


def assert_node(node, cls=None, xpath="", **kwargs):
    if cls:
        if isinstance(cls, list):
            assert_node(node, cls[0], xpath=xpath, **kwargs)
            if cls[1:]:
                if isinstance(cls[1], tuple):
                    assert_node(node, cls[1], xpath=xpath, **kwargs)
                else:
                    assert len(node) == 1, \
                        'The node%s has %d child nodes, not one' % (xpath, len(node))
                    assert_node(node[0], cls[1:], xpath=xpath + "[0]", **kwargs)
        elif isinstance(cls, tuple):
            assert len(node) == len(cls), \
                'The node%s has %d child nodes, not %r' % (xpath, len(node), len(cls))
            for i, nodecls in enumerate(cls):
                path = xpath + "[%d]" % i
                assert_node(node[i], nodecls, xpath=path, **kwargs)
        elif isinstance(cls, string_types):
            assert node == cls, 'The node %r is not %r: %r' % (xpath, cls, node)
        else:
            assert isinstance(node, cls), \
                'The node%s is not subclass of %r: %r' % (xpath, cls, node)

    for key, value in kwargs.items():
        assert key in node, 'The node%s does not have %r attribute: %r' % (xpath, key, node)
        assert node[key] == value, \
            'The node%s[%s] is not %r: %r' % (xpath, key, value, node[key])


try:
    from nose.tools import assert_in, assert_not_in
except ImportError:
    def assert_in(x, thing, msg=''):
        if x not in thing:
            assert False, msg or '%r is not in %r' % (x, thing)

    def assert_not_in(x, thing, msg=''):
        if x in thing:
            assert False, msg or '%r is in %r' % (x, thing)


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

    def __init__(self, buildername='html', testroot=None, srcdir=None,
                 freshenv=False, confoverrides=None, status=None, warning=None,
                 tags=None, docutilsconf=None):
        if testroot is None:
            defaultsrcdir = 'root'
            testroot = rootdir / 'root'
        else:
            defaultsrcdir = 'test-' + testroot
            testroot = rootdir / 'roots' / ('test-' + testroot)
        if srcdir is None:
            srcdir = tempdir / defaultsrcdir
        else:
            srcdir = tempdir / srcdir

        if not srcdir.exists():
            testroot.copytree(srcdir)

        if docutilsconf is not None:
            (srcdir / 'docutils.conf').write_text(docutilsconf)

        builddir = srcdir / '_build'
#        if confdir is None:
        confdir = srcdir
#        if outdir is None:
        outdir = builddir.joinpath(buildername)
        if not outdir.isdir():
            outdir.makedirs()
#        if doctreedir is None:
        doctreedir = builddir.joinpath('doctrees')
        if not doctreedir.isdir():
            doctreedir.makedirs()
        if confoverrides is None:
            confoverrides = {}
        if status is None:
            status = StringIO()
        if warning is None:
            warning = ListOutput('stderr')
#        if warningiserror is None:
        warningiserror = False

        self._saved_path = sys.path[:]
        self._saved_directives = directives._directives.copy()
        self._saved_roles = roles._roles.copy()

        self._saved_nodeclasses = set(v for v in dir(nodes.GenericNodeVisitor)
                                      if v.startswith('visit_'))

        try:
            application.Sphinx.__init__(self, srcdir, confdir, outdir, doctreedir,
                                        buildername, confoverrides, status, warning,
                                        freshenv, warningiserror, tags)
        except:
            self.cleanup()
            raise

    def cleanup(self, doctrees=False):
        Theme.themes.clear()
        AutoDirective._registry.clear()
        ModuleAnalyzer.cache.clear()
        LaTeXBuilder.usepackages = []
        sys.path[:] = self._saved_path
        sys.modules.pop('autodoc_fodder', None)
        directives._directives = self._saved_directives
        roles._roles = self._saved_roles
        for method in dir(nodes.GenericNodeVisitor):
            if method.startswith('visit_') and \
               method not in self._saved_nodeclasses:
                delattr(nodes.GenericNodeVisitor, 'visit_' + method[6:])
                delattr(nodes.GenericNodeVisitor, 'depart_' + method[6:])

    def __repr__(self):
        return '<%s buildername=%r>' % (self.__class__.__name__, self.builder.name)


def with_app(*args, **kwargs):
    """
    Make a TestApp with args and kwargs, pass it to the test and clean up
    properly.
    """
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            status, warning = StringIO(), StringIO()
            kwargs['status'] = status
            kwargs['warning'] = warning
            app = TestApp(*args, **kwargs)
            try:
                func(app, status, warning, *args2, **kwargs2)
            finally:
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
            status, warning = StringIO(), StringIO()
            kwargs['status'] = status
            kwargs['warning'] = warning
            app = TestApp(*args, **kwargs)
            try:
                for item in func(app, status, warning, *args2, **kwargs2):
                    yield item
            finally:
                app.cleanup()
        return deco
    return generator


def with_tempdir(func):
    def new_func(*args, **kwds):
        new_tempdir = path(tempfile.mkdtemp(dir=tempdir))
        func(new_tempdir, *args, **kwds)
    new_func.__name__ = func.__name__
    return new_func


def sprint(*args):
    sys.stderr.write(' '.join(map(str, args)) + '\n')


_unicode_literals_re = re.compile(r'u(".*?")|u(\'.*?\')')


def remove_unicode_literals(s):
    return _unicode_literals_re.sub(lambda x: x.group(1) or x.group(2), s)


def find_files(root, suffix=None):
    for dirpath, dirs, files in os.walk(root, followlinks=True):
        dirpath = path(dirpath)
        for f in [f for f in files if not suffix or f.endswith(suffix)]:
            fpath = dirpath / f
            yield os.path.relpath(fpath, root)


def strip_escseq(text):
    return re.sub('\x1b.*?m', '', text)
