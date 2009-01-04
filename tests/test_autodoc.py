# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the RstGenerator; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *

from docutils.statemachine import ViewList

from sphinx.ext.autodoc import RstGenerator, cut_lines, between


def setup_module():
    global app, lid, options, gen

    app = TestApp()
    app.builder.env.app = app
    app.connect('autodoc-process-docstring', process_docstring)
    app.connect('autodoc-process-signature', process_signature)
    app.connect('autodoc-skip-member', skip_member)

    options = Struct(
        inherited_members = False,
        undoc_members = False,
        show_inheritance = False,
        noindex = False,
        synopsis = '',
        platform = '',
        deprecated = False,
    )

    gen = TestGenerator(options, app)

def teardown_module():
    app.cleanup()


class TestGenerator(RstGenerator):
    """Generator that handles warnings without a reporter."""

    def __init__(self, options, app):
        self.options = options
        self.env = app.builder.env
        self.lineno = 42
        self.filename_set = set()
        self.warnings = []
        self.result = ViewList()

    def warn(self, msg):
        self.warnings.append(msg)


processed_docstrings = []

def process_docstring(app, what, name, obj, options, lines):
    processed_docstrings.append((what, name))
    if name == 'bar':
        lines.extend(['42', ''])

processed_signatures = []

def process_signature(app, what, name, obj, options, args, retann):
    processed_signatures.append((what, name))
    if name == 'bar':
        return '42', None


def skip_member(app, what, name, obj, skip, options):
    if name.startswith('_'):
        return True
    if name == 'skipmeth':
        return True


def test_resolve_name():
    # for modules
    assert gen.resolve_name('module', 'test_autodoc') == \
           ('test_autodoc', [], None, None)
    assert gen.resolve_name('module', 'test.test_autodoc') == \
           ('test.test_autodoc', [], None, None)

    assert gen.resolve_name('module', 'test(arg)') == \
           ('test', [], None, None)
    assert 'ignoring signature arguments' in gen.warnings[0]
    del gen.warnings[:]

    # for functions/classes
    assert gen.resolve_name('function', 'util.raises') == \
           ('util', ['raises'], None, None)
    assert gen.resolve_name('function', 'util.raises(exc) -> None') == \
           ('util', ['raises'], 'exc', 'None')
    gen.env.autodoc_current_module = 'util'
    assert gen.resolve_name('function', 'raises') == \
           ('util', ['raises'], None, None)
    gen.env.autodoc_current_module = None
    gen.env.currmodule = 'util'
    assert gen.resolve_name('function', 'raises') == \
           ('util', ['raises'], None, None)
    assert gen.resolve_name('class', 'TestApp') == \
           ('util', ['TestApp'], None, None)

    # for members
    gen.env.currmodule = 'foo'
    assert gen.resolve_name('method', 'util.TestApp.cleanup') == \
           ('util', ['TestApp', 'cleanup'], None, None)
    gen.env.currmodule = 'util'
    gen.env.currclass = 'Foo'
    gen.env.autodoc_current_class = 'TestApp'
    assert gen.resolve_name('method', 'cleanup') == \
           ('util', ['TestApp', 'cleanup'], None, None)
    assert gen.resolve_name('method', 'TestApp.cleanup') == \
           ('util', ['TestApp', 'cleanup'], None, None)

    # and clean up
    gen.env.currmodule = None
    gen.env.currclass = None
    gen.env.autodoc_current_class = None


def test_format_signature():
    # no signatures for modules
    assert gen.format_signature('module', 'test', None, None, None) == ''

    # test for functions
    def f(a, b, c=1, **d):
        pass
    assert gen.format_signature('function', 'f', f, None, None) == '(a, b, c=1, **d)'
    assert gen.format_signature('function', 'f', f, 'a, b, c, d', None) == \
           '(a, b, c, d)'
    assert gen.format_signature('function', 'f', f, None, 'None') == \
           '(a, b, c=1, **d) -> None'

    # test for classes
    class D:
        pass
    class E(object):
        pass
    # no signature for classes without __init__
    for C in (D, E):
        assert gen.format_signature('class', 'D', C, None, None) == ''
    class F:
        def __init__(self, a, b=None):
            pass
    class G(F, object):
        pass
    for C in (F, G):
        assert gen.format_signature('class', 'C', C, None, None) == '(a, b=None)'
    assert gen.format_signature('class', 'C', D, 'a, b', 'X') == '(a, b) -> X'

    # test for methods
    class H:
        def foo1(self, b, *c):
            pass
        def foo2(b, *c):
            pass
    assert gen.format_signature('method', 'H.foo', H.foo1, None, None) == '(b, *c)'
    assert gen.format_signature('method', 'H.foo', H.foo1, 'a', None) == '(a)'
    assert gen.format_signature('method', 'H.foo', H.foo2, None, None) == '(b, *c)'

    # test exception handling
    raises(RuntimeError, gen.format_signature, 'function', 'int', int, None, None)

    # test processing by event handler
    assert gen.format_signature('method', 'bar', H.foo1, None, None) == '42'


def test_get_doc():
    def getdocl(*args):
        ds = gen.get_doc(*args)
        # for testing purposes, concat them and strip the empty line at the end
        return sum(ds, [])[:-1]

    # objects without docstring
    def f():
        pass
    assert getdocl('function', f) == []

    # standard function, diverse docstring styles...
    def f():
        """Docstring"""
    def g():
        """
        Docstring
        """
    for func in (f, g):
        assert getdocl('function', func) == ['Docstring']

    # first line vs. other lines indentation
    def f():
        """First line

        Other
          lines
        """
    assert getdocl('function', f) == ['First line', '', 'Other', '  lines']

    # charset guessing (this module is encoded in utf-8)
    def f():
        """Döcstring"""
    assert getdocl('function', f) == [u'Döcstring']

    # already-unicode docstrings must be taken literally
    def f():
        u"""Döcstring"""
    assert getdocl('function', f) == [u'Döcstring']

    # class docstring: depends on config value which one is taken
    class C:
        """Class docstring"""
        def __init__(self):
            """Init docstring"""
    gen.env.config.autoclass_content = 'class'
    assert getdocl('class', C) == ['Class docstring']
    gen.env.config.autoclass_content = 'init'
    assert getdocl('class', C) == ['Init docstring']
    gen.env.config.autoclass_content = 'both'
    assert getdocl('class', C) == ['Class docstring', '', 'Init docstring']

    class D:
        """Class docstring"""
        def __init__(self):
            """Init docstring

            Other
             lines
            """

    # Indentation is normalized for 'both'
    assert getdocl('class', D) == ['Class docstring', '', 'Init docstring',
                                   '', 'Other', ' lines']


def test_docstring_processing():
    def process(what, name, obj):
        return list(gen.process_doc(gen.get_doc(what, obj), what, name, obj))

    class E:
        def __init__(self):
            """Init docstring"""

    # docstring processing by event handler
    assert process('class', 'bar', E) == ['Init docstring', '', '42', '']

    lid = app.connect('autodoc-process-docstring', cut_lines(1, 1, ['function']))
    def f():
        """
        first line
        second line
        third line
        """
    assert process('function', 'f', f) == ['second line', '']
    app.disconnect(lid)

    lid = app.connect('autodoc-process-docstring', between('---', ['function']))
    def f():
        """
        first line
        ---
        second line
        ---
        third line
        """
    assert process('function', 'f', f) == ['second line', '']
    app.disconnect(lid)


def test_generate():
    def assert_warns(warn_str, *args):
        gen.generate(*args)
        assert len(gen.result) == 0, gen.result
        assert len(gen.warnings) == 1, gen.warnings
        assert warn_str in gen.warnings[0], gen.warnings
        del gen.warnings[:]

    def assert_works(*args):
        gen.generate(*args)
        assert gen.result
        assert len(gen.warnings) == 0, gen.warnings
        del gen.result[:]

    def assert_processes(items, *args):
        del processed_docstrings[:]
        del processed_signatures[:]
        assert_works(*args)
        assert set(processed_docstrings) | set(processed_signatures) == set(items)

    def assert_result_contains(item, *args):
        gen.generate(*args)
        #print '\n'.join(gen.result)
        assert len(gen.warnings) == 0, gen.warnings
        assert item in gen.result
        del gen.result[:]

    # no module found?
    assert_warns("import for autodocumenting 'foobar'",
                 'function', 'foobar', None, None)
    # importing
    assert_warns("import/find module 'test_foobar'",
                 'module', 'test_foobar', None, None)
    # attributes missing
    assert_warns("import/find function 'util.foobar'",
                 'function', 'util.foobar', None, None)

    # test auto and given content mixing
    gen.env.currmodule = 'test_autodoc'
    assert_result_contains('   Function.', 'method', 'Class.meth', [], None)
    add_content = ViewList()
    add_content.append('Content.', '', 0)
    assert_result_contains('   Function.', 'method', 'Class.meth', [], add_content)
    assert_result_contains('   Content.', 'method', 'Class.meth', [], add_content)

    # test check_module
    gen.generate('function', 'raises', None, None, check_module=True)
    assert len(gen.result) == 0

    # assert that exceptions can be documented
    assert_works('exception', 'test_autodoc.CustomEx', ['__all__'], None)
    assert_works('exception', 'test_autodoc.CustomEx', [], None)

    # test diverse inclusion settings for members
    should = [('class', 'test_autodoc.Class')]
    assert_processes(should, 'class', 'Class', [], None)
    should.extend([('method', 'test_autodoc.Class.meth')])
    assert_processes(should, 'class', 'Class', ['meth'], None)
    should.extend([('attribute', 'test_autodoc.Class.prop'),
                   ('attribute', 'test_autodoc.Class.attr'),
                   ('attribute', 'test_autodoc.Class.docattr'),
                   ('attribute', 'test_autodoc.Class.udocattr')])
    assert_processes(should, 'class', 'Class', ['__all__'], None)
    options.undoc_members = True
    should.append(('method', 'test_autodoc.Class.undocmeth'))
    assert_processes(should, 'class', 'Class', ['__all__'], None)
    options.inherited_members = True
    should.append(('method', 'test_autodoc.Class.inheritedmeth'))
    assert_processes(should, 'class', 'Class', ['__all__'], None)

    # test module flags
    assert_result_contains('.. module:: test_autodoc', 'module',
                           'test_autodoc', [], None)
    options.synopsis = 'Synopsis'
    assert_result_contains('   :synopsis: Synopsis', 'module', 'test_autodoc', [], None)
    options.deprecated = True
    assert_result_contains('   :deprecated:', 'module', 'test_autodoc', [], None)
    options.platform = 'Platform'
    assert_result_contains('   :platform: Platform', 'module', 'test_autodoc', [], None)
    # test if __all__ is respected for modules
    assert_result_contains('.. class:: Class', 'module', 'test_autodoc',
                           ['__all__'], None)
    try:
        assert_result_contains('.. exception:: CustomEx', 'module', 'test_autodoc',
                               ['__all__'], None)
    except AssertionError:
        pass
    else:
        assert False, 'documented CustomEx which is not in __all__'

    # test noindex flag
    options.noindex = True
    assert_result_contains('   :noindex:', 'module', 'test_autodoc', [], None)
    assert_result_contains('   :noindex:', 'class', 'Base', [], None)

    # okay, now let's get serious about mixing Python and C signature stuff
    assert_result_contains('.. class:: CustomDict', 'class', 'CustomDict',
                           ['__all__'], None)

    # test inner class handling
    assert_processes([('class', 'test_autodoc.Outer'),
                      ('class', 'test_autodoc.Outer.Inner'),
                      ('method', 'test_autodoc.Outer.Inner.meth')],
                     'class', 'Outer', ['__all__'], None)

    # test generation for C modules (which have no source file)
    gen.env.currmodule = 'time'
    assert_processes([('function', 'time.asctime')], 'function', 'asctime', [], None)
    assert_processes([('function', 'time.asctime')], 'function', 'asctime', [], None)


# --- generate fodder ------------

__all__ = ['Class']

class CustomEx(Exception):
    """My custom exception."""

    def f(self):
        """Exception method."""


class Base(object):
    def inheritedmeth(self):
        """Inherited function."""

class Class(Base):
    """Class to document."""

    def meth(self):
        """Function."""

    def undocmeth(self):
        pass

    def skipmeth(self):
        """Method that should be skipped."""
        pass

    # should not be documented
    skipattr = 'foo'

    #: should be documented -- süß
    attr = 'bar'

    @property
    def prop(self):
        """Property."""

    docattr = 'baz'
    """should likewise be documented -- süß"""

    udocattr = 'quux'
    u"""should be documented as well - süß"""

class CustomDict(dict):
    """Docstring."""

def function(foo, *args, **kwds):
    """
    Return spam.
    """
    pass


class Outer(object):
    """Foo"""

    class Inner(object):
        """Foo"""

        def meth(self):
            """Foo"""

    # should be documented as an alias
    factory = dict
