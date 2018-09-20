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
import platform
import sys
from warnings import catch_warnings

import pytest
from docutils.statemachine import ViewList
from six import PY3

from sphinx.ext.autodoc import (
    AutoDirective, ModuleLevelDocumenter, cut_lines, between, ALL,
    merge_autodoc_default_flags, Options
)
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.testing.util import SphinxTestApp, Struct  # NOQA
from sphinx.util import logging
from sphinx.util.docutils import LoggingReporter

app = None

if PY3:
    ROGER_METHOD = '   .. py:classmethod:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)'
else:
    ROGER_METHOD = '   .. py:classmethod:: Class.roger(a, e=5, f=6)'

IS_PYPY = platform.python_implementation() == 'PyPy'


def do_autodoc(app, objtype, name, options=None):
    if options is None:
        options = {}
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

    options = Options(
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
    def assert_result_contains(item, objtype, name, **kw):
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)
        assert item in directive.result
        del directive.result[:]

    # test auto and given content mixing
    directive.env.ref_context['py:module'] = 'target'
    assert_result_contains('   Function.', 'method', 'Class.meth')
    add_content = ViewList()
    add_content.append('Content.', '', 0)
    assert_result_contains('   Function.', 'method',
                           'Class.meth', more_content=add_content)
    assert_result_contains('   Content.', 'method',
                           'Class.meth', more_content=add_content)


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_exception(app):
    actual = do_autodoc(app, 'exception', 'target.CustomEx')
    assert list(actual) == [
        '',
        '.. py:exception:: CustomEx',
        '   :module: target',
        '',
        '   My custom exception.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_warnings(app, warning):
    app.env.temp_data['docname'] = 'dummy'

    # can't import module
    do_autodoc(app, 'module', 'unknown')
    assert "failed to import module 'unknown'" in warning.getvalue()

    # missing function
    do_autodoc(app, 'function', 'unknown')
    assert "import for autodocumenting 'unknown'" in warning.getvalue()

    do_autodoc(app, 'function', 'target.unknown')
    assert "failed to import function 'unknown' from module 'target'" in warning.getvalue()

    # missing method
    do_autodoc(app, 'method', 'target.Class.unknown')
    assert "failed to import method 'Class.unknown' from module 'target'" in warning.getvalue()


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_attributes(app):
    options = {"synopsis": 'Synopsis',
               "platform": "Platform",
               "deprecated": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :synopsis: Synopsis',
        '   :platform: Platform',
        '   :deprecated:',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_members(app):
    # default (no-members)
    actual = do_autodoc(app, 'class', 'target.Base')
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
    ]

    # default ALL-members
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:classmethod:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:staticmethod:: Base.inheritedstaticmeth(cls)'
    ]

    # default specific-members
    options = {"members": "inheritedmeth,inheritedstaticmeth"}
    actual = do_autodoc(app, 'class', 'target.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:staticmethod:: Base.inheritedstaticmeth(cls)'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_exclude_members(app):
    options = {"members": None,
               "exclude-members": "inheritedmeth,inheritedstaticmeth"}
    actual = do_autodoc(app, 'class', 'target.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:classmethod:: Base.inheritedclassmeth()'
    ]

    # members vs exclude-members
    options = {"members": "inheritedmeth",
               "exclude-members": "inheritedmeth"}
    actual = do_autodoc(app, 'class', 'target.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_undoc_members(app):
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
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
        ROGER_METHOD,
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members(app):
    options = {"members": None,
               "inherited-members": None}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: 'method::' in l, actual)) == [
        '   .. py:method:: Class.excludemeth()',
        '   .. py:classmethod:: Class.inheritedclassmeth()',
        '   .. py:method:: Class.inheritedmeth()',
        '   .. py:staticmethod:: Class.inheritedstaticmeth(cls)',
        '   .. py:method:: Class.meth()',
        '   .. py:classmethod:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.skipmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_imported_members(app):
    options = {"members": None,
               "imported-members": None,
               "ignore-module-all": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert '.. py:function:: add_documenter(cls)' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_special_members(app):
    # specific special methods
    options = {"undoc-members": None,
               "special-members": "__init__,__special1__"}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # combination with specific members
    options = {"members": "attr,docattr",
               "undoc-members": None,
               "special-members": "__init__,__special1__"}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
    ]

    # all special methods
    options = {"members": None,
               "undoc-members": None,
               "special-members": None}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:attribute:: Class.__module__',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
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
        ROGER_METHOD,
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_ignore_module_all(app):
    # default (no-ignore-module-all)
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
    ]

    # ignore-module-all
    options = {"members": None,
               "ignore-module-all": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '.. py:class:: CustomDataDescriptor(doc)',
        '.. py:class:: CustomDataDescriptor2(doc)',
        '.. py:class:: CustomDataDescriptorMeta',
        '.. py:class:: CustomDict',
        '.. py:class:: InstAttCls()',
        '.. py:class:: Outer',
        '   .. py:class:: Outer.Inner',
        '.. py:class:: StrRepr'
    ]


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
        ROGER_METHOD,
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
        ROGER_METHOD,
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
        ROGER_METHOD,
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
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: EnumCls',
        '   :module: target.enum',
        '',
        '   this is enum class',
        '   ',
        '   ',
        '   .. py:method:: EnumCls.say_hello()',
        '      :module: target.enum',
        '   ',
        '      a method says hello to you.',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val1',
        '      :module: target.enum',
        '      :annotation: = 12',
        '   ',
        '      doc for val1',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val2',
        '      :module: target.enum',
        '      :annotation: = 23',
        '   ',
        '      doc for val2',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val3',
        '      :module: target.enum',
        '      :annotation: = 34',
        '   ',
        '      doc for val3',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val4',
        '      :module: target.enum',
        '      :annotation: = 34',
        '   '
    ]

    # checks for an attribute of EnumClass
    actual = do_autodoc(app, 'attribute', 'target.enum.EnumCls.val1')
    assert list(actual) == [
        '',
        '.. py:attribute:: EnumCls.val1',
        '   :module: target.enum',
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autofunction_for_callable(app):
    actual = do_autodoc(app, 'function', 'target.callable.function')
    assert list(actual) == [
        '',
        '.. py:function:: function(arg1, arg2, **kwargs)',
        '   :module: target.callable',
        '',
        '   A callable object that behaves like a function.',
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


@pytest.mark.usefixtures('setup_test')
def test_partialfunction():
    def call_autodoc(objtype, name):
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate()
        result = list(directive.result)
        del directive.result[:]
        return result

    options.members = ALL
    #options.undoc_members = True
    expected = [
        '',
        '.. py:module:: target.partialfunction',
        '',
        '',
        '.. py:function:: func1()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '   ',
        '',
        '.. py:function:: func2()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '   ',
        '',
        '.. py:function:: func3()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '   '
    ]

    assert call_autodoc('module', 'target.partialfunction') == expected


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
def test_merge_autodoc_default_flags1(app):
    app.config.autodoc_default_flags = ['members', 'undoc-members']
    merge_autodoc_default_flags(app, app.config)
    assert app.config.autodoc_default_options == {'members': None,
                                                  'undoc-members': None}


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_merge_autodoc_default_flags2(app):
    app.config.autodoc_default_flags = ['members', 'undoc-members']
    app.config.autodoc_default_options = {'members': 'this,that,order',
                                          'inherited-members': 'this'}
    merge_autodoc_default_flags(app, app.config)
    assert app.config.autodoc_default_options == {'members': None,
                                                  'undoc-members': None,
                                                  'inherited-members': 'this'}


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options(app):
    # no settings
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: target.CustomIter' not in actual

    # with :members:
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: and :undoc-members:
    app.config.autodoc_default_options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' in actual

    # with :special-members:
    # Note that :members: must be *on* for :special-members: to work.
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert '      list of weak references to the object (if defined)' in actual

    # :exclude-members: None - has no effect. Unlike :members:,
    # :special-members:, etc. where None == "include all", here None means
    # "no/false/off".
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert '      list of weak references to the object (if defined)' in actual
    assert '   .. py:method:: CustomIter.snafucate()' in actual
    assert '      Makes this snafucated.' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options_with_values(app):
    # with :members:
    app.config.autodoc_default_options = {'members': 'val1,val2'}
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :special-members:
    app.config.autodoc_default_options = {
        'special-members': '__init__,__iter__',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert '      list of weak references to the object (if defined)' not in actual

    # with :exclude-members:
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': 'val1'
    }
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': '__weakref__,snafucate',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert '      list of weak references to the object (if defined)' not in actual
    assert '   .. py:method:: CustomIter.snafucate()' not in actual
    assert '      Makes this snafucated.' not in actual


@pytest.mark.sphinx('html', testroot='pycode-egg')
def test_autodoc_for_egged_code(app):
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'sample', options)
    assert list(actual) == [
        '',
        '.. py:module:: sample',
        '',
        '',
        '.. py:data:: CONSTANT',
        '   :module: sample',
        '   :annotation: = 1',
        '',
        '   constant on sample.py',
        '   ',
        '',
        '.. py:function:: hello(s)',
        '   :module: sample',
        ''
    ]
