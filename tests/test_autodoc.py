# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *

from docutils.statemachine import ViewList

from sphinx.ext.autodoc import AutoDirective, Documenter, add_documenter, \
     ModuleLevelDocumenter, FunctionDocumenter, cut_lines, between, ALL


def setup_module():
    global app, lid, options, directive

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
        members = [],
        member_order = 'alphabetic',
        exclude_members = set(),
    )

    directive = Struct(
        env = app.builder.env,
        genopt = options,
        result = ViewList(),
        warn = warnfunc,
        filename_set = set(),
    )

def teardown_module():
    app.cleanup()


_warnings = []

def warnfunc(msg):
    _warnings.append(msg)


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


def test_parse_name():
    def verify(objtype, name, result):
        inst = AutoDirective._registry[objtype](directive, name)
        assert inst.parse_name()
        assert (inst.modname, inst.objpath, inst.args, inst.retann) == result

    # for modules
    verify('module', 'test_autodoc', ('test_autodoc', [], None, None))
    verify('module', 'test.test_autodoc', ('test.test_autodoc', [], None, None))
    verify('module', 'test(arg)', ('test', [], 'arg', None))
    assert 'signature arguments' in _warnings[0]
    del _warnings[:]

    # for functions/classes
    verify('function', 'util.raises', ('util', ['raises'], None, None))
    verify('function', 'util.raises(exc) -> None',
           ('util', ['raises'], 'exc', 'None'))
    directive.env.autodoc_current_module = 'util'
    verify('function', 'raises', ('util', ['raises'], None, None))
    directive.env.autodoc_current_module = None
    directive.env.currmodule = 'util'
    verify('function', 'raises', ('util', ['raises'], None, None))
    verify('class', 'TestApp', ('util', ['TestApp'], None, None))

    # for members
    directive.env.currmodule = 'foo'
    verify('method', 'util.TestApp.cleanup',
           ('util', ['TestApp', 'cleanup'], None, None))
    directive.env.currmodule = 'util'
    directive.env.currclass = 'Foo'
    directive.env.autodoc_current_class = 'TestApp'
    verify('method', 'cleanup', ('util', ['TestApp', 'cleanup'], None, None))
    verify('method', 'TestApp.cleanup',
           ('util', ['TestApp', 'cleanup'], None, None))

    # and clean up
    directive.env.currmodule = None
    directive.env.currclass = None
    directive.env.autodoc_current_class = None


def test_format_signature():
    def formatsig(objtype, name, obj, args, retann):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.fullname = name
        inst.doc_as_attr = False  # for class objtype
        inst.object = obj
        inst.args = args
        inst.retann = retann
        return inst.format_signature()

    # no signatures for modules
    assert formatsig('module', 'test', None, None, None) == ''

    # test for functions
    def f(a, b, c=1, **d):
        pass
    assert formatsig('function', 'f', f, None, None) == '(a, b, c=1, **d)'
    assert formatsig('function', 'f', f, 'a, b, c, d', None) == '(a, b, c, d)'
    assert formatsig('function', 'f', f, None, 'None') == \
           '(a, b, c=1, **d) -> None'

    # test for classes
    class D:
        pass
    class E(object):
        pass
    # no signature for classes without __init__
    for C in (D, E):
        assert formatsig('class', 'D', C, None, None) == ''
    class F:
        def __init__(self, a, b=None):
            pass
    class G(F, object):
        pass
    for C in (F, G):
        assert formatsig('class', 'C', C, None, None) == '(a, b=None)'
    assert formatsig('class', 'C', D, 'a, b', 'X') == '(a, b) -> X'

    # test for methods
    class H:
        def foo1(self, b, *c):
            pass
        def foo2(b, *c):
            pass
    assert formatsig('method', 'H.foo', H.foo1, None, None) == '(b, *c)'
    assert formatsig('method', 'H.foo', H.foo1, 'a', None) == '(a)'
    assert formatsig('method', 'H.foo', H.foo2, None, None) == '(b, *c)'

    # test exception handling (exception is caught and args is '')
    assert formatsig('function', 'int', int, None, None) == ''
    del _warnings[:]

    # test processing by event handler
    assert formatsig('method', 'bar', H.foo1, None, None) == '42'


def test_get_doc():
    def getdocl(objtype, obj, encoding=None):
        inst = AutoDirective._registry[objtype](directive, 'tmp')
        inst.object = obj
        ds = inst.get_doc(encoding)
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
    directive.env.config.autoclass_content = 'class'
    assert getdocl('class', C) == ['Class docstring']
    directive.env.config.autoclass_content = 'init'
    assert getdocl('class', C) == ['Init docstring']
    directive.env.config.autoclass_content = 'both'
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
    def process(objtype, name, obj):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.object = obj
        inst.fullname = name
        return list(inst.process_doc(inst.get_doc()))

    class E:
        def __init__(self):
            """Init docstring"""

    # docstring processing by event handler
    assert process('class', 'bar', E) == ['Init docstring', '', '42', '']

    lid = app.connect('autodoc-process-docstring',
                      cut_lines(1, 1, ['function']))
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


def test_new_documenter():
    class MyDocumenter(ModuleLevelDocumenter):
        objtype = 'integer'
        directivetype = 'data'
        priority = 100

        @classmethod
        def can_document_member(cls, member, membername, isattr, parent):
            return isinstance(member, int)

        def document_members(self, all_members=False):
            return

    add_documenter(MyDocumenter)

    def assert_result_contains(item, objtype, name, **kw):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.generate(**kw)
        #print '\n'.join(directive.result)
        assert len(_warnings) == 0, _warnings
        assert item in directive.result
        del directive.result[:]

    options.members = ['integer']
    assert_result_contains('.. data:: integer', 'module', 'test_autodoc')


def test_generate():
    def assert_warns(warn_str, objtype, name, **kw):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.generate(**kw)
        assert len(directive.result) == 0, directive.result
        assert len(_warnings) == 1, _warnings
        assert warn_str in _warnings[0], _warnings
        del _warnings[:]

    def assert_works(objtype, name, **kw):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.generate(**kw)
        assert directive.result
        assert len(_warnings) == 0, _warnings
        del directive.result[:]

    def assert_processes(items, objtype, name, **kw):
        del processed_docstrings[:]
        del processed_signatures[:]
        assert_works(objtype, name, **kw)
        assert set(processed_docstrings) | set(processed_signatures) == \
               set(items)

    def assert_result_contains(item, objtype, name, **kw):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.generate(**kw)
        #print '\n'.join(directive.result)
        assert len(_warnings) == 0, _warnings
        assert item in directive.result
        del directive.result[:]

    options.members = []

    # no module found?
    assert_warns("import for autodocumenting 'foobar'",
                 'function', 'foobar', more_content=None)
    # importing
    assert_warns("import/find module 'test_foobar'",
                 'module', 'test_foobar', more_content=None)
    # attributes missing
    assert_warns("import/find function 'util.foobar'",
                 'function', 'util.foobar', more_content=None)

    # test auto and given content mixing
    directive.env.currmodule = 'test_autodoc'
    assert_result_contains('   Function.', 'method', 'Class.meth')
    add_content = ViewList()
    add_content.append('Content.', '', 0)
    assert_result_contains('   Function.', 'method',
                           'Class.meth', more_content=add_content)
    assert_result_contains('   Content.', 'method',
                           'Class.meth', more_content=add_content)

    # test check_module
    inst = FunctionDocumenter(directive, 'raises')
    inst.generate(check_module=True)
    assert len(directive.result) == 0

    # assert that exceptions can be documented
    assert_works('exception', 'test_autodoc.CustomEx', all_members=True)
    assert_works('exception', 'test_autodoc.CustomEx')

    # test diverse inclusion settings for members
    should = [('class', 'test_autodoc.Class')]
    assert_processes(should, 'class', 'Class')
    should.extend([('method', 'test_autodoc.Class.meth')])
    options.members = ['meth']
    options.exclude_members = set(['excludemeth'])
    assert_processes(should, 'class', 'Class')
    should.extend([('attribute', 'test_autodoc.Class.prop'),
                   ('attribute', 'test_autodoc.Class.descr'),
                   ('attribute', 'test_autodoc.Class.attr'),
                   ('attribute', 'test_autodoc.Class.docattr'),
                   ('attribute', 'test_autodoc.Class.udocattr')])
    options.members = ALL
    assert_processes(should, 'class', 'Class')
    options.undoc_members = True
    should.append(('method', 'test_autodoc.Class.undocmeth'))
    assert_processes(should, 'class', 'Class')
    options.inherited_members = True
    should.append(('method', 'test_autodoc.Class.inheritedmeth'))
    assert_processes(should, 'class', 'Class')

    options.members = []
    # test module flags
    assert_result_contains('.. module:: test_autodoc', 'module', 'test_autodoc')
    options.synopsis = 'Synopsis'
    assert_result_contains('   :synopsis: Synopsis', 'module', 'test_autodoc')
    options.deprecated = True
    assert_result_contains('   :deprecated:', 'module', 'test_autodoc')
    options.platform = 'Platform'
    assert_result_contains('   :platform: Platform', 'module', 'test_autodoc')
    # test if __all__ is respected for modules
    options.members = ALL
    assert_result_contains('.. class:: Class', 'module', 'test_autodoc')
    try:
        assert_result_contains('.. exception:: CustomEx',
                               'module', 'test_autodoc')
    except AssertionError:
        pass
    else:
        assert False, 'documented CustomEx which is not in __all__'

    # test noindex flag
    options.members = []
    options.noindex = True
    assert_result_contains('   :noindex:', 'module', 'test_autodoc')
    assert_result_contains('   :noindex:', 'class', 'Base')

    # okay, now let's get serious about mixing Python and C signature stuff
    assert_result_contains('.. class:: CustomDict', 'class', 'CustomDict',
                           all_members=True)

    # test inner class handling
    assert_processes([('class', 'test_autodoc.Outer'),
                      ('class', 'test_autodoc.Outer.Inner'),
                      ('method', 'test_autodoc.Outer.Inner.meth')],
                     'class', 'Outer', all_members=True)

    # test descriptor docstrings
    assert_result_contains('   Descriptor instance docstring.',
                           'attribute', 'test_autodoc.Class.descr')

    # test generation for C modules (which have no source file)
    directive.env.currmodule = 'time'
    assert_processes([('function', 'time.asctime')], 'function', 'asctime')
    assert_processes([('function', 'time.asctime')], 'function', 'asctime')


# --- generate fodder ------------

__all__ = ['Class']

integer = 1

class CustomEx(Exception):
    """My custom exception."""

    def f(self):
        """Exception method."""

class CustomDataDescriptor(object):
    """Descriptor class docstring."""

    def __init__(self, doc):
        self.__doc__ = doc

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return 42

class Base(object):
    def inheritedmeth(self):
        """Inherited function."""

class Class(Base):
    """Class to document."""

    descr = CustomDataDescriptor("Descriptor instance docstring.")

    def meth(self):
        """Function."""

    def undocmeth(self):
        pass

    def skipmeth(self):
        """Method that should be skipped."""

    def excludemeth(self):
        """Method that should be excluded."""

    # should not be documented
    skipattr = 'foo'

    #: should be documented -- süß
    attr = 'bar'

    def prop(self):
        """Property."""
    # stay 2.4 compatible (docstring!)
    prop = property(prop, doc="Property.")

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
