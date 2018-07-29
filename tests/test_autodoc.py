# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
from warnings import catch_warnings

import pytest
from docutils.statemachine import ViewList
from six import PY3

from sphinx.ext.autodoc import (
    AutoDirective, ModuleLevelDocumenter, FunctionDocumenter, cut_lines, between, ALL
)
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.testing.util import SphinxTestApp, Struct  # NOQA
from sphinx.util import logging
from sphinx.util.docutils import LoggingReporter

app = None


def do_autodoc(app, objtype, name, options={}):
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1)
    documenter = doccls(bridge, name)
    documenter.generate()

    return bridge.result


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir, sphinx_test_tempdir):
    try:
        global app
        srcdir = sphinx_test_tempdir / 'autodoc-root'
        if not srcdir.exists():
            (rootdir / 'test-root').copytree(srcdir)
        testroot = rootdir / 'test-ext-autodoc'
        sys.path.append(testroot)
        app = SphinxTestApp(srcdir=srcdir)
        app.builder.env.app = app
        app.builder.env.temp_data['docname'] = 'dummy'
        app.connect('autodoc-process-docstring', process_docstring)
        app.connect('autodoc-process-signature', process_signature)
        app.connect('autodoc-skip-member', skip_member)
        yield
    finally:
        app.cleanup()
        sys.path.remove(testroot)


directive = options = None


@pytest.fixture
def setup_test():
    global options, directive
    global processed_docstrings, processed_signatures

    options = Struct(
        inherited_members = False,
        undoc_members = False,
        private_members = False,
        special_members = False,
        imported_members = False,
        show_inheritance = False,
        noindex = False,
        annotation = None,
        synopsis = '',
        platform = '',
        deprecated = False,
        members = [],
        member_order = 'alphabetic',
        exclude_members = set(),
        ignore_module_all = False,
    )

    directive = Struct(
        env = app.builder.env,
        genopt = options,
        result = ViewList(),
        filename_set = set(),
    )

    processed_docstrings = []
    processed_signatures = []

    app._status.truncate(0)
    app._warning.truncate(0)

    yield

    AutoDirective._special_attrgetters.clear()


processed_docstrings = []
processed_signatures = []


def process_docstring(app, what, name, obj, options, lines):
    processed_docstrings.append((what, name))
    if name == 'bar':
        lines.extend(['42', ''])


def process_signature(app, what, name, obj, options, args, retann):
    processed_signatures.append((what, name))
    if name == 'bar':
        return '42', None


def skip_member(app, what, name, obj, skip, options):
    if name in ('__special1__', '__special2__'):
        return skip
    if name.startswith('__'):
        return True
    if name == 'skipmeth':
        return True


@pytest.mark.usefixtures('setup_test')
def test_parse_name():
    logging.setup(app, app._status, app._warning)

    def verify(objtype, name, result):
        inst = app.registry.documenters[objtype](directive, name)
        assert inst.parse_name()
        assert (inst.modname, inst.objpath, inst.args, inst.retann) == result

    # for modules
    verify('module', 'test_autodoc', ('test_autodoc', [], None, None))
    verify('module', 'test.test_autodoc', ('test.test_autodoc', [], None, None))
    verify('module', 'test(arg)', ('test', [], 'arg', None))
    assert 'signature arguments' in app._warning.getvalue()

    # for functions/classes
    verify('function', 'test_autodoc.raises',
           ('test_autodoc', ['raises'], None, None))
    verify('function', 'test_autodoc.raises(exc) -> None',
           ('test_autodoc', ['raises'], 'exc', 'None'))
    directive.env.temp_data['autodoc:module'] = 'test_autodoc'
    verify('function', 'raises', ('test_autodoc', ['raises'], None, None))
    del directive.env.temp_data['autodoc:module']
    directive.env.ref_context['py:module'] = 'test_autodoc'
    verify('function', 'raises', ('test_autodoc', ['raises'], None, None))
    verify('class', 'Base', ('test_autodoc', ['Base'], None, None))

    # for members
    directive.env.ref_context['py:module'] = 'foo'
    verify('method', 'util.SphinxTestApp.cleanup',
           ('util', ['SphinxTestApp', 'cleanup'], None, None))
    directive.env.ref_context['py:module'] = 'util'
    directive.env.ref_context['py:class'] = 'Foo'
    directive.env.temp_data['autodoc:class'] = 'SphinxTestApp'
    verify('method', 'cleanup', ('util', ['SphinxTestApp', 'cleanup'], None, None))
    verify('method', 'SphinxTestApp.cleanup',
           ('util', ['SphinxTestApp', 'cleanup'], None, None))

    # and clean up
    del directive.env.ref_context['py:module']
    del directive.env.ref_context['py:class']
    del directive.env.temp_data['autodoc:class']


@pytest.mark.usefixtures('setup_test')
def test_format_signature():
    def formatsig(objtype, name, obj, args, retann):
        inst = app.registry.documenters[objtype](directive, name)
        inst.fullname = name
        inst.doc_as_attr = False  # for class objtype
        inst.object = obj
        inst.objpath = [name]
        inst.args = args
        inst.retann = retann
        res = inst.format_signature()
        print(res)
        return res

    # no signatures for modules
    assert formatsig('module', 'test', None, None, None) == ''

    # test for functions
    def f(a, b, c=1, **d):
        pass

    def g(a='\n'):
        pass
    assert formatsig('function', 'f', f, None, None) == '(a, b, c=1, **d)'
    assert formatsig('function', 'f', f, 'a, b, c, d', None) == '(a, b, c, d)'
    assert formatsig('function', 'f', f, None, 'None') == '(a, b, c=1, **d) -> None'
    assert formatsig('function', 'g', g, None, None) == r"(a='\\n')"

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

    # __init__ have signature at first line of docstring
    directive.env.config.autoclass_content = 'both'

    class F2:
        '''some docstring for F2.'''
        def __init__(self, *args, **kw):
            '''
            __init__(a1, a2, kw1=True, kw2=False)

            some docstring for __init__.
            '''
    class G2(F2, object):
        pass

    assert formatsig('class', 'F2', F2, None, None) == \
        '(a1, a2, kw1=True, kw2=False)'
    assert formatsig('class', 'G2', G2, None, None) == \
        '(a1, a2, kw1=True, kw2=False)'

    # test for methods
    class H:
        def foo1(self, b, *c):
            pass

        def foo2(b, *c):
            pass

        def foo3(self, d='\n'):
            pass
    assert formatsig('method', 'H.foo', H.foo1, None, None) == '(b, *c)'
    assert formatsig('method', 'H.foo', H.foo1, 'a', None) == '(a)'
    assert formatsig('method', 'H.foo', H.foo2, None, None) == '(*c)'
    assert formatsig('method', 'H.foo', H.foo3, None, None) == r"(d='\\n')"

    # test exception handling (exception is caught and args is '')
    directive.env.config.autodoc_docstring_signature = False
    assert formatsig('function', 'int', int, None, None) == ''

    # test processing by event handler
    assert formatsig('method', 'bar', H.foo1, None, None) == '42'

    # test functions created via functools.partial
    from functools import partial
    curried1 = partial(lambda a, b, c: None, 'A')
    assert formatsig('function', 'curried1', curried1, None, None) == \
        '(b, c)'
    curried2 = partial(lambda a, b, c=42: None, 'A')
    assert formatsig('function', 'curried2', curried2, None, None) == \
        '(b, c=42)'
    curried3 = partial(lambda a, b, *c: None, 'A')
    assert formatsig('function', 'curried3', curried3, None, None) == \
        '(b, *c)'
    curried4 = partial(lambda a, b, c=42, *d, **e: None, 'A')
    assert formatsig('function', 'curried4', curried4, None, None) == \
        '(b, c=42, *d, **e)'


@pytest.mark.usefixtures('setup_test')
def test_get_doc():
    def getdocl(objtype, obj, encoding=None):
        inst = app.registry.documenters[objtype](directive, 'tmp')
        inst.object = obj
        inst.objpath = [obj.__name__]
        inst.doc_as_attr = False
        inst.format_signature()  # handle docstring signatures!
        ds = inst.get_doc(encoding)
        # for testing purposes, concat them and strip the empty line at the end
        res = sum(ds, [])[:-1]
        print(res)
        return res

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

        def __new__(cls):
            """New docstring"""
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

    # __init__ have signature at first line of docstring
    class E:
        """Class docstring"""
        def __init__(self, *args, **kw):
            """
            __init__(a1, a2, kw1=True, kw2=False)

            Init docstring
            """

    # signature line in the docstring will be kept when
    # autodoc_docstring_signature == False
    directive.env.config.autodoc_docstring_signature = False
    directive.env.config.autoclass_content = 'class'
    assert getdocl('class', E) == ['Class docstring']
    directive.env.config.autoclass_content = 'init'
    assert getdocl('class', E) == ['__init__(a1, a2, kw1=True, kw2=False)',
                                   '', 'Init docstring']
    directive.env.config.autoclass_content = 'both'
    assert getdocl('class', E) == ['Class docstring', '',
                                   '__init__(a1, a2, kw1=True, kw2=False)',
                                   '', 'Init docstring']

    # signature line in the docstring will be removed when
    # autodoc_docstring_signature == True
    directive.env.config.autodoc_docstring_signature = True  # default
    directive.env.config.autoclass_content = 'class'
    assert getdocl('class', E) == ['Class docstring']
    directive.env.config.autoclass_content = 'init'
    assert getdocl('class', E) == ['Init docstring']
    directive.env.config.autoclass_content = 'both'
    assert getdocl('class', E) == ['Class docstring', '', 'Init docstring']

    # class does not have __init__ method
    class F(object):
        """Class docstring"""

    # docstring in the __init__ method of base class will be discard
    for f in (False, True):
        directive.env.config.autodoc_docstring_signature = f
        directive.env.config.autoclass_content = 'class'
        assert getdocl('class', F) == ['Class docstring']
        directive.env.config.autoclass_content = 'init'
        assert getdocl('class', F) == ['Class docstring']
        directive.env.config.autoclass_content = 'both'
        assert getdocl('class', F) == ['Class docstring']

    # class has __init__ method with no docstring
    class G(object):
        """Class docstring"""
        def __init__(self):
            pass

    # docstring in the __init__ method of base class will not be used
    for f in (False, True):
        directive.env.config.autodoc_docstring_signature = f
        directive.env.config.autoclass_content = 'class'
        assert getdocl('class', G) == ['Class docstring']
        directive.env.config.autoclass_content = 'init'
        assert getdocl('class', G) == ['Class docstring']
        directive.env.config.autoclass_content = 'both'
        assert getdocl('class', G) == ['Class docstring']

    # class has __new__ method with docstring
    # class docstring: depends on config value which one is taken
    class H:
        """Class docstring"""
        def __init__(self):
            pass

        def __new__(cls):
            """New docstring"""
    directive.env.config.autoclass_content = 'class'
    assert getdocl('class', H) == ['Class docstring']
    directive.env.config.autoclass_content = 'init'
    assert getdocl('class', H) == ['New docstring']
    directive.env.config.autoclass_content = 'both'
    assert getdocl('class', H) == ['Class docstring', '', 'New docstring']

    # class has __init__ method without docstring and
    # __new__ method with docstring
    # class docstring: depends on config value which one is taken
    class I:  # NOQA
        """Class docstring"""
        def __new__(cls):
            """New docstring"""
    directive.env.config.autoclass_content = 'class'
    assert getdocl('class', I) == ['Class docstring']
    directive.env.config.autoclass_content = 'init'
    assert getdocl('class', I) == ['New docstring']
    directive.env.config.autoclass_content = 'both'
    assert getdocl('class', I) == ['Class docstring', '', 'New docstring']

    from target import Base, Derived

    # NOTE: inspect.getdoc seems not to work with locally defined classes
    directive.env.config.autodoc_inherit_docstrings = False
    assert getdocl('method', Base.inheritedmeth) == ['Inherited function.']
    assert getdocl('method', Derived.inheritedmeth) == []
    directive.env.config.autodoc_inherit_docstrings = True
    assert getdocl('method', Derived.inheritedmeth) == ['Inherited function.']


@pytest.mark.usefixtures('setup_test')
def test_docstring_processing():
    def process(objtype, name, obj):
        inst = app.registry.documenters[objtype](directive, name)
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

    lid = app.connect('autodoc-process-docstring',
                      between('---', ['function'], exclude=True))

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


@pytest.mark.usefixtures('setup_test')
def test_docstring_property_processing():
    def genarate_docstring(objtype, name, **kw):
        del processed_docstrings[:]
        del processed_signatures[:]
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        results = list(directive.result)
        docstrings = inst.get_doc()[0]
        del directive.result[:]
        return results, docstrings

    directive.env.config.autodoc_docstring_signature = False
    results, docstrings = \
        genarate_docstring('attribute', 'target.DocstringSig.prop1')
    assert '.. py:attribute:: DocstringSig.prop1' in results
    assert 'First line of docstring' in docstrings
    assert 'DocstringSig.prop1(self)' in docstrings
    results, docstrings = \
        genarate_docstring('attribute', 'target.DocstringSig.prop2')
    assert '.. py:attribute:: DocstringSig.prop2' in results
    assert 'First line of docstring' in docstrings
    assert 'Second line of docstring' in docstrings

    directive.env.config.autodoc_docstring_signature = True
    results, docstrings = \
        genarate_docstring('attribute', 'target.DocstringSig.prop1')
    assert '.. py:attribute:: DocstringSig.prop1' in results
    assert 'First line of docstring' in docstrings
    assert 'DocstringSig.prop1(self)' not in docstrings
    results, docstrings = \
        genarate_docstring('attribute', 'target.DocstringSig.prop2')
    assert '.. py:attribute:: DocstringSig.prop2' in results
    assert 'First line of docstring' in docstrings
    assert 'Second line of docstring' in docstrings


@pytest.mark.usefixtures('setup_test')
def test_new_documenter():
    logging.setup(app, app._status, app._warning)

    class MyDocumenter(ModuleLevelDocumenter):
        objtype = 'integer'
        directivetype = 'data'
        priority = 100

        @classmethod
        def can_document_member(cls, member, membername, isattr, parent):
            return isinstance(member, int)

        def document_members(self, all_members=False):
            return

    app.add_autodocumenter(MyDocumenter)

    def assert_result_contains(item, objtype, name, **kw):
        app._warning.truncate(0)
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        # print '\n'.join(directive.result)
        assert app._warning.getvalue() == ''
        assert item in directive.result
        del directive.result[:]

    options.members = ['integer']
    assert_result_contains('.. py:data:: integer', 'module', 'target')


@pytest.mark.usefixtures('setup_test')
def test_attrgetter_using():
    from target import Class

    def assert_getter_works(objtype, name, obj, attrs=[], **kw):
        getattr_spy = []

        def special_getattr(obj, name, *defargs):
            if name in attrs:
                getattr_spy.append((obj, name))
                return None
            return getattr(obj, name, *defargs)
        AutoDirective._special_attrgetters[type] = special_getattr

        del getattr_spy[:]
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)

        hooked_members = [s[1] for s in getattr_spy]
        documented_members = [s[1] for s in processed_signatures]
        for attr in attrs:
            fullname = '.'.join((name, attr))
            assert attr in hooked_members
            assert fullname not in documented_members, \
                '%r was not hooked by special_attrgetter function' % fullname

    with catch_warnings(record=True):
        options.members = ALL
        options.inherited_members = False
        assert_getter_works('class', 'target.Class', Class, ['meth'])

        options.inherited_members = True
        assert_getter_works('class', 'target.Class', Class, ['meth', 'inheritedmeth'])


@pytest.mark.usefixtures('setup_test')
def test_generate():
    logging.setup(app, app._status, app._warning)

    def assert_warns(warn_str, objtype, name, **kw):
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        assert len(directive.result) == 0, directive.result

        assert warn_str in app._warning.getvalue()
        app._warning.truncate(0)

    def assert_works(objtype, name, **kw):
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        assert directive.result
        # print '\n'.join(directive.result)
        assert app._warning.getvalue() == ''
        del directive.result[:]

    def assert_processes(items, objtype, name, **kw):
        del processed_docstrings[:]
        del processed_signatures[:]
        assert_works(objtype, name, **kw)
        assert set(processed_docstrings) | set(processed_signatures) == set(items)

    def assert_result_contains(item, objtype, name, **kw):
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        # print '\n'.join(directive.result)
        assert app._warning.getvalue() == ''
        assert item in directive.result
        del directive.result[:]

    def assert_order(items, objtype, name, member_order, **kw):
        inst = app.registry.documenters[objtype](directive, name)
        inst.options.member_order = member_order
        inst.generate(**kw)
        assert app._warning.getvalue() == ''
        items = list(reversed(items))
        lineiter = iter(directive.result)
        # for line in directive.result:
        #     if line.strip():
        #         print repr(line)
        while items:
            item = items.pop()
            for line in lineiter:
                if line == item:
                    break
            else:  # ran out of items!
                assert False, ('item %r not found in result or not in the '
                               ' correct order' % item)
        del directive.result[:]

    options.members = []

    # no module found?
    assert_warns("import for autodocumenting 'foobar'",
                 'function', 'foobar', more_content=None)
    # importing
    assert_warns("failed to import module 'test_foobar'",
                 'module', 'test_foobar', more_content=None)
    # attributes missing
    assert_warns("failed to import function 'foobar' from module 'util'",
                 'function', 'util.foobar', more_content=None)
    # method missing
    assert_warns("failed to import method 'Class.foobar' from module 'target';",
                 'method', 'target.Class.foobar', more_content=None)

    # test auto and given content mixing
    directive.env.ref_context['py:module'] = 'target'
    assert_result_contains('   Function.', 'method', 'Class.meth')
    add_content = ViewList()
    add_content.append('Content.', '', 0)
    assert_result_contains('   Function.', 'method',
                           'Class.meth', more_content=add_content)
    assert_result_contains('   Content.', 'method',
                           'Class.meth', more_content=add_content)

    # test check_module
    inst = FunctionDocumenter(directive, 'add_documenter')
    inst.generate(check_module=True)
    assert len(directive.result) == 0

    # assert that exceptions can be documented
    assert_works('exception', 'target.CustomEx', all_members=True)
    assert_works('exception', 'target.CustomEx')

    # test diverse inclusion settings for members
    should = [('class', 'target.Class')]
    assert_processes(should, 'class', 'Class')
    should.extend([('method', 'target.Class.meth')])
    options.members = ['meth']
    options.exclude_members = set(['excludemeth'])
    assert_processes(should, 'class', 'Class')
    should.extend([('attribute', 'target.Class.prop'),
                   ('attribute', 'target.Class.descr'),
                   ('attribute', 'target.Class.attr'),
                   ('attribute', 'target.Class.docattr'),
                   ('attribute', 'target.Class.udocattr'),
                   ('attribute', 'target.Class.mdocattr'),
                   ('attribute', 'target.Class.inst_attr_comment'),
                   ('attribute', 'target.Class.inst_attr_inline'),
                   ('attribute', 'target.Class.inst_attr_string'),
                   ('method', 'target.Class.moore'),
                   ])
    options.members = ALL
    assert_processes(should, 'class', 'Class')
    options.undoc_members = True
    should.extend((('attribute', 'target.Class.skipattr'),
                   ('method', 'target.Class.undocmeth'),
                   ('method', 'target.Class.roger')))
    assert_processes(should, 'class', 'Class')
    options.inherited_members = True
    should.append(('method', 'target.Class.inheritedmeth'))
    should.append(('method', 'target.Class.inheritedclassmeth'))
    should.append(('method', 'target.Class.inheritedstaticmeth'))
    assert_processes(should, 'class', 'Class')

    # test special members
    options.special_members = ['__special1__']
    should.append(('method', 'target.Class.__special1__'))
    assert_processes(should, 'class', 'Class')
    options.special_members = ALL
    should.append(('method', 'target.Class.__special2__'))
    assert_processes(should, 'class', 'Class')
    options.special_members = False

    options.members = []
    # test module flags
    assert_result_contains('.. py:module:: target',
                           'module', 'target')
    options.synopsis = 'Synopsis'
    assert_result_contains('   :synopsis: Synopsis', 'module', 'target')
    options.deprecated = True
    assert_result_contains('   :deprecated:', 'module', 'target')
    options.platform = 'Platform'
    assert_result_contains('   :platform: Platform', 'module', 'target')
    # test if __all__ is respected for modules
    options.members = ALL
    assert_result_contains('.. py:class:: Class(arg)', 'module', 'target')
    try:
        assert_result_contains('.. py:exception:: CustomEx',
                               'module', 'target')
    except AssertionError:
        pass
    else:
        assert False, 'documented CustomEx which is not in __all__'

    # test ignore-module-all
    options.ignore_module_all = True
    assert_result_contains('.. py:class:: Class(arg)', 'module', 'target')
    assert_result_contains('.. py:exception:: CustomEx', 'module', 'target')


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_noindex(app):
    options = {"noindex": True}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :noindex:',
        ''
    ]

    # TODO: :noindex: should be propagated to children of target item.

    actual = do_autodoc(app, 'class', 'target.Base', options)
    assert list(actual) == [
        '',
        '.. py:class:: Base',
        '   :noindex:',
        '   :module: target',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_subclass_of_builtin_class(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.CustomDict', options)
    assert list(actual) == [
        '',
        '.. py:class:: CustomDict',
        '   :module: target',
        '',
        '   Docstring.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inner_class(app):
    if PY3:
        builtins = '      alias of :class:`builtins.dict`'
    else:
        builtins = '      alias of :class:`__builtin__.dict`'

    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.Outer', options)
    assert list(actual) == [
        '',
        '.. py:class:: Outer',
        '   :module: target',
        '',
        '   Foo',
        '   ',
        '   ',
        '   .. py:class:: Outer.Inner',
        '      :module: target',
        '   ',
        '      Foo',
        '      ',
        '      ',
        '      .. py:method:: Outer.Inner.meth()',
        '         :module: target',
        '      ',
        '         Foo',
        '         ',
        '   ',
        '   .. py:attribute:: Outer.factory',
        '      :module: target',
        '   ',
        builtins
    ]

    actual = do_autodoc(app, 'class', 'target.Outer.Inner', options)
    assert list(actual) == [
        '',
        '.. py:class:: Inner',
        '   :module: target.Outer',
        '',
        '   Foo',
        '   ',
        '   ',
        '   .. py:method:: Inner.meth()',
        '      :module: target.Outer',
        '   ',
        '      Foo',
        '      ',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_descriptor(app):
    actual = do_autodoc(app, 'attribute', 'target.Class.descr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.descr',
        '   :module: target',
        '',
        '   Descriptor instance docstring.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_c_module(app):
    actual = do_autodoc(app, 'function', 'time.asctime')
    assert list(actual) == [
        '',
        '.. py:function:: asctime([tuple]) -> string',
        '   :module: time',
        '',
        "   Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.",
        '   When the time tuple is not present, current time as returned by localtime()',
        '   is used.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_member_order(app):
    if PY3:
        roger_method = '   .. py:classmethod:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)'
    else:
        roger_method = '   .. py:classmethod:: Class.roger(a, e=5, f=6)'

    # case member-order='bysource'
    options = {"members": None,
               'member-order': 'bysource',
               "undoc-members": True,
               'private-members': True}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class.descr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.prop',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        roger_method,
        '   .. py:classmethod:: Class.moore(a, e, f) -> happiness',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class._private_inst_attr'
    ]

    # case member-order='groupwise'
    options = {"members": None,
               'member-order': 'groupwise',
               "undoc-members": True,
               'private-members': True}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:method:: Class.meth()',
        '   .. py:classmethod:: Class.moore(a, e, f) -> happiness',
        roger_method,
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.descr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:attribute:: Class.prop',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.udocattr'
    ]

    # case member-order=None
    options = {"members": None,
               "undoc-members": True,
               'private-members': True}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.descr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:classmethod:: Class.moore(a, e, f) -> happiness',
        '   .. py:attribute:: Class.prop',
        roger_method,
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_module_scope(app):
    def convert(s):
        return re.sub('<.*>', '<FILTERED>', s)  # for py2/py3

    app.env.temp_data['autodoc:module'] = 'target'
    actual = do_autodoc(app, 'attribute', 'Class.mdocattr')
    assert list(map(convert, actual)) == [
        u'',
        u'.. py:attribute:: Class.mdocattr',
        u'   :module: target',
        u'   :annotation: = <FILTERED>',
        u'',
        u'   should be documented as well - süß',
        u'   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_scope(app):
    def convert(s):
        return re.sub('<.*>', '<FILTERED>', s)  # for py2/py3

    app.env.temp_data['autodoc:module'] = 'target'
    app.env.temp_data['autodoc:class'] = 'Class'
    actual = do_autodoc(app, 'attribute', 'mdocattr')
    assert list(map(convert, actual)) == [
        u'',
        u'.. py:attribute:: Class.mdocattr',
        u'   :module: target',
        u'   :annotation: = <FILTERED>',
        u'',
        u'   should be documented as well - süß',
        u'   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_docstring_signature(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        '.. py:class:: DocstringSig',
        '   :module: target',
        '',
        '   ',
        '   .. py:method:: DocstringSig.meth(FOO, BAR=1) -> BAZ',
        '      :module: target',
        '   ',
        '      First line of docstring',
        '      ',
        '      rest of docstring',
        '      ',
        '   ',
        '   .. py:method:: DocstringSig.meth2()',
        '      :module: target',
        '   ',
        '      First line, no signature',
        '      Second line followed by indentation::',
        '      ',
        '          indented line',
        '      ',
        '   ',
        '   .. py:attribute:: DocstringSig.prop1',
        '      :module: target',
        '   ',
        '      First line of docstring',
        '      ',
        '   ',
        '   .. py:attribute:: DocstringSig.prop2',
        '      :module: target',
        '   ',
        '      First line of docstring',
        '      Second line of docstring',
        '      '
    ]

    # disable autodoc_docstring_signature
    app.config.autodoc_docstring_signature = False
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        u'',
        u'.. py:class:: DocstringSig',
        u'   :module: target',
        u'',
        u'   ',
        u'   .. py:method:: DocstringSig.meth()',
        u'      :module: target',
        u'   ',
        u'      meth(FOO, BAR=1) -> BAZ',
        u'      First line of docstring',
        u'      ',
        u'              rest of docstring',
        u'              ',
        u'      ',
        u'   ',
        u'   .. py:method:: DocstringSig.meth2()',
        u'      :module: target',
        u'   ',
        u'      First line, no signature',
        u'      Second line followed by indentation::',
        u'      ',
        u'          indented line',
        u'      ',
        u'   ',
        u'   .. py:attribute:: DocstringSig.prop1',
        u'      :module: target',
        u'   ',
        u'      DocstringSig.prop1(self)',
        u'      First line of docstring',
        u'      ',
        u'   ',
        u'   .. py:attribute:: DocstringSig.prop2',
        u'      :module: target',
        u'   ',
        u'      First line of docstring',
        u'      Second line of docstring',
        u'      '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_attributes(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'class', 'target.AttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: AttCls',
        '   :module: target',
        '',
        '   ',
        '   .. py:attribute:: AttCls.a1',
        '      :module: target',
        '      :annotation: = hello world',
        '   ',
        '   ',
        '   .. py:attribute:: AttCls.a2',
        '      :module: target',
        '      :annotation: = None',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_instance_attributes(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '   ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :annotation: = 'a'",
        '   ',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca2',
        '      :module: target',
        "      :annotation: = 'b'",
        '   ',
        '      Doc comment for InstAttCls.ca2. One line only.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca3',
        '      :module: target',
        "      :annotation: = 'c'",
        '   ',
        '      Docstring for class attribute InstAttCls.ca3.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '      :annotation: = None',
        '   ',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia2',
        '      :module: target',
        '      :annotation: = None',
        '   ',
        '      Docstring for instance attribute InstAttCls.ia2.',
        '      '
    ]

    # pick up arbitrary attributes
    options = {"members": 'ca1,ia1'}
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '   ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :annotation: = 'a'",
        '   ',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '      :annotation: = None',
        '   ',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '      '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'class', 'target.EnumCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: EnumCls',
        '   :module: target',
        '',
        '   this is enum class',
        '   ',
        '   ',
        '   .. py:attribute:: EnumCls.val1',
        '      :module: target',
        '      :annotation: = 12',
        '   ',
        '      doc for val1',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val2',
        '      :module: target',
        '      :annotation: = 23',
        '   ',
        '      doc for val2',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val3',
        '      :module: target',
        '      :annotation: = 34',
        '   ',
        '      doc for val3',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val4',
        '      :module: target',
        '      :annotation: = 34',
        '   '
    ]

    # checks for an attribute of EnumClass
    actual = do_autodoc(app, 'attribute', 'target.EnumCls.val1')
    assert list(actual) == [
        '',
        '.. py:attribute:: EnumCls.val1',
        '   :module: target',
        '   :annotation: = 12',
        '',
        '   doc for val1',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_descriptor_class(app):
    options = {"members": 'CustomDataDescriptor,CustomDataDescriptor2'}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '',
        '',
        '.. py:class:: CustomDataDescriptor(doc)',
        '   :module: target',
        '',
        '   Descriptor class docstring.',
        '   ',
        '   ',
        '   .. py:method:: CustomDataDescriptor.meth()',
        '      :module: target',
        '   ',
        '      Function.',
        '      ',
        '',
        '.. py:class:: CustomDataDescriptor2(doc)',
        '   :module: target',
        '',
        '   Descriptor class with custom metaclass docstring.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='root')
def test_mocked_module_imports(app):
    options = {"members": 'TestAutodoc,decoratedFunction'}
    actual = do_autodoc(app, 'module', 'autodoc_missing_imports', options)
    assert list(actual) == [
        '',
        '.. py:module:: autodoc_missing_imports',
        '',
        '',
        '.. py:class:: TestAutodoc',
        '   :module: autodoc_missing_imports',
        '',
        '   TestAutodoc docstring.',
        '   ',
        '   ',
        '   .. py:method:: TestAutodoc.decoratedMethod()',
        '      :module: autodoc_missing_imports',
        '   ',
        '      TestAutodoc::decoratedMethod docstring',
        '      ',
        '',
        '.. py:function:: decoratedFunction()',
        '   :module: autodoc_missing_imports',
        '',
        '   decoratedFunction docstring',
        '   '
    ]


@pytest.mark.skipif(sys.version_info < (3, 4),
                    reason='functools.partialmethod is available on py34 or above')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialmethod(app):
    expected = [
        '',
        '.. py:class:: Cell',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '   ',
        '   refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod',
        '   ',
        '   ',
        '   .. py:method:: Cell.set_alive() -> None',
        '      :module: target.partialmethod',
        '   ',
        '      Make a cell alive.',
        '      ',
        '   ',
        '   .. py:method:: Cell.set_dead() -> None',
        '      :module: target.partialmethod',
        '   ',
        '      Make a cell dead.',
        '      ',
        '   ',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '   ',
        '      Update state of cell to *state*.',
        '      ',
    ]
    if (sys.version_info < (3, 5, 4) or
            (3, 6, 5) <= sys.version_info < (3, 7) or
            (3, 7, 0, 'beta', 3) <= sys.version_info):
        # TODO: this condition should be updated after 3.7-final release.
        expected = '\n'.join(expected).replace(' -> None', '').split('\n')

    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.partialmethod.Cell', options)
    assert list(actual) == expected


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_flags(app):
    # no settings
    actual = do_autodoc(app, 'class', 'target.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members:
    app.config.autodoc_default_flags = ['members']
    actual = do_autodoc(app, 'class', 'target.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: and :undoc-members:
    app.config.autodoc_default_flags = ['members',
                                        'undoc-members']
    actual = do_autodoc(app, 'class', 'target.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' in actual
