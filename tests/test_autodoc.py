# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from StringIO import StringIO

from util import *

from docutils.statemachine import ViewList

from sphinx.ext.autodoc import AutoDirective, add_documenter, \
     ModuleLevelDocumenter, FunctionDocumenter, cut_lines, between, ALL


def setup_module():
    global app, lid, options, directive

    app = TestApp()
    app.builder.env.app = app
    app.builder.env.temp_data['docname'] = 'dummy'
    app.connect('autodoc-process-docstring', process_docstring)
    app.connect('autodoc-process-signature', process_signature)
    app.connect('autodoc-skip-member', skip_member)

    options = Struct(
        inherited_members = False,
        undoc_members = False,
        private_members = False,
        special_members = False,
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
    directive.env.temp_data['autodoc:module'] = 'util'
    verify('function', 'raises', ('util', ['raises'], None, None))
    del directive.env.temp_data['autodoc:module']
    directive.env.temp_data['py:module'] = 'util'
    verify('function', 'raises', ('util', ['raises'], None, None))
    verify('class', 'TestApp', ('util', ['TestApp'], None, None))

    # for members
    directive.env.temp_data['py:module'] = 'foo'
    verify('method', 'util.TestApp.cleanup',
           ('util', ['TestApp', 'cleanup'], None, None))
    directive.env.temp_data['py:module'] = 'util'
    directive.env.temp_data['py:class'] = 'Foo'
    directive.env.temp_data['autodoc:class'] = 'TestApp'
    verify('method', 'cleanup', ('util', ['TestApp', 'cleanup'], None, None))
    verify('method', 'TestApp.cleanup',
           ('util', ['TestApp', 'cleanup'], None, None))

    # and clean up
    del directive.env.temp_data['py:module']
    del directive.env.temp_data['py:class']
    del directive.env.temp_data['autodoc:class']


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
    def g():
        """
        first line
        ---
        second line
        ---
        third line
        """
    assert process('function', 'g', g) == ['second line', '']
    app.disconnect(lid)

    lid = app.connect('autodoc-process-docstring', between('---', ['function'],
                                                           exclude=True))
    def h():
        """
        first line
        ---
        second line
        ---
        third line
        """
    assert process('function', 'h', h) == ['first line', 'third line', '']
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
    assert_result_contains('.. py:data:: integer', 'module', 'test_autodoc')


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
        #print '\n'.join(directive.result)
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

    def assert_order(items, objtype, name, member_order, **kw):
        inst = AutoDirective._registry[objtype](directive, name)
        inst.options.member_order = member_order
        inst.generate(**kw)
        assert len(_warnings) == 0, _warnings
        items = list(reversed(items))
        lineiter = iter(directive.result)
        #for line in directive.result:
        #    if line.strip():
        #        print repr(line)
        while items:
            item = items.pop()
            for line in lineiter:
                if line == item:
                    break
            else:  # ran out of items!
                assert False, 'item %r not found in result or not in the ' \
                       ' correct order' % item
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
    directive.env.temp_data['py:module'] = 'test_autodoc'
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
                   ('attribute', 'test_autodoc.Class.udocattr'),
                   ('attribute', 'test_autodoc.Class.mdocattr'),
                   ('attribute', 'test_autodoc.Class.inst_attr_comment'),
                   ('attribute', 'test_autodoc.Class.inst_attr_inline'),
                   ('attribute', 'test_autodoc.Class.inst_attr_string'),
                   ('method', 'test_autodoc.Class.moore'),
                   ])
    options.members = ALL
    assert_processes(should, 'class', 'Class')
    options.undoc_members = True
    should.extend((('attribute', 'test_autodoc.Class.skipattr'),
                   ('method', 'test_autodoc.Class.undocmeth'),
                   ('method', 'test_autodoc.Class.roger')))
    assert_processes(should, 'class', 'Class')
    options.inherited_members = True
    should.append(('method', 'test_autodoc.Class.inheritedmeth'))
    assert_processes(should, 'class', 'Class')

    options.members = []
    # test module flags
    assert_result_contains('.. py:module:: test_autodoc',
                           'module', 'test_autodoc')
    options.synopsis = 'Synopsis'
    assert_result_contains('   :synopsis: Synopsis', 'module', 'test_autodoc')
    options.deprecated = True
    assert_result_contains('   :deprecated:', 'module', 'test_autodoc')
    options.platform = 'Platform'
    assert_result_contains('   :platform: Platform', 'module', 'test_autodoc')
    # test if __all__ is respected for modules
    options.members = ALL
    assert_result_contains('.. py:class:: Class(arg)', 'module', 'test_autodoc')
    try:
        assert_result_contains('.. py:exception:: CustomEx',
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
    assert_result_contains('.. py:class:: CustomDict', 'class', 'CustomDict',
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
    directive.env.temp_data['py:module'] = 'time'
    assert_processes([('function', 'time.asctime')], 'function', 'asctime')
    assert_processes([('function', 'time.asctime')], 'function', 'asctime')

    # test autodoc_member_order == 'source'
    directive.env.temp_data['py:module'] = 'test_autodoc'
    assert_order(['.. py:class:: Class(arg)',
                  '   .. py:attribute:: Class.descr',
                  '   .. py:method:: Class.meth()',
                  '   .. py:method:: Class.undocmeth()',
                  '   .. py:attribute:: Class.attr',
                  '   .. py:attribute:: Class.prop',
                  '   .. py:attribute:: Class.docattr',
                  '   .. py:attribute:: Class.udocattr',
                  '   .. py:attribute:: Class.mdocattr',
                  '   .. py:classmethod:: Class.roger(a, e=5, f=6)',
                  '   .. py:classmethod:: Class.moore(a, e, f) -> happiness',
                  '   .. py:attribute:: Class.inst_attr_comment',
                  '   .. py:attribute:: Class.inst_attr_string',
                  '   .. py:method:: Class.inheritedmeth()',
                  ],
                 'class', 'Class', member_order='bysource', all_members=True)
    del directive.env.temp_data['py:module']

    # test attribute initialized to class instance from other module
    directive.env.temp_data['autodoc:class'] = 'test_autodoc.Class'
    assert_result_contains(u'   should be documented as well - s\xfc\xdf',
                           'attribute', 'mdocattr')
    del directive.env.temp_data['autodoc:class']

    # test autodoc_docstring_signature
    assert_result_contains(
        '.. py:method:: DocstringSig.meth(FOO, BAR=1) -> BAZ', 'method',
        'test_autodoc.DocstringSig.meth')
    assert_result_contains(
        '   rest of docstring', 'method', 'test_autodoc.DocstringSig.meth')
    assert_result_contains(
        '.. py:classmethod:: Class.moore(a, e, f) -> happiness', 'method',
        'test_autodoc.Class.moore')

    # test new attribute documenter behavior
    directive.env.temp_data['py:module'] = 'test_autodoc'
    options.undoc_members = True
    assert_processes([('class', 'test_autodoc.AttCls'),
                      ('attribute', 'test_autodoc.AttCls.a1'),
                      ('attribute', 'test_autodoc.AttCls.a2'),
                      ], 'class', 'AttCls')
    assert_result_contains(
        '   :annotation: = hello world', 'attribute', 'AttCls.a1')
    assert_result_contains(
        '   :annotation: = None', 'attribute', 'AttCls.a2')


# --- generate fodder ------------

__all__ = ['Class']

#: documentation for the integer
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

def _funky_classmethod(name, b, c, d, docstring=None):
    """Generates a classmethod for a class from a template by filling out
    some arguments."""
    def template(cls, a, b, c, d=4, e=5, f=6):
        return a, b, c, d, e, f
    if sys.version_info >= (2, 5):
        from functools import partial
        function = partial(template, b=b, c=c, d=d)
    else:
        def function(cls, a, e=5, f=6):
            return template(a, b, c, d, e, f)
    function.__name__ = name
    function.__doc__ = docstring
    return classmethod(function)

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

    # initialized to any class imported from another module
    mdocattr = StringIO()
    """should be documented as well - süß"""

    roger = _funky_classmethod("roger", 2, 3, 4)

    moore = _funky_classmethod("moore", 9, 8, 7,
        docstring="moore(a, e, f) -> happiness")

    def __init__(self, arg):
        self.inst_attr_inline = None #: an inline documented instance attr
        #: a documented instance attribute
        self.inst_attr_comment = None
        self.inst_attr_string = None
        """a documented instance attribute"""


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


class DocstringSig(object):
    def meth(self):
        """meth(FOO, BAR=1) -> BAZ
First line of docstring

        rest of docstring
        """

class StrRepr(str):
    def __repr__(self):
        return self

class AttCls(object):
    a1 = StrRepr('hello\nworld')
    a2 = None
