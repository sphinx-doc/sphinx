# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# "raises" imported for usage by autodoc
import sys

import pytest
import six
from docutils.statemachine import ViewList
from six import StringIO

from sphinx.ext.autodoc import add_documenter, FunctionDocumenter, ALL, Options  # NOQA
from sphinx.testing.util import SphinxTestApp, Struct
from sphinx.util import logging

app = None


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir, sphinx_test_tempdir):
    global app
    srcdir = sphinx_test_tempdir / 'autodoc-root'
    if not srcdir.exists():
        (rootdir / 'test-root').copytree(srcdir)
    app = SphinxTestApp(srcdir=srcdir)
    app.builder.env.app = app
    app.builder.env.temp_data['docname'] = 'dummy'
    app.connect('autodoc-process-docstring', process_docstring)
    app.connect('autodoc-process-signature', process_signature)
    app.connect('autodoc-skip-member', skip_member)
    yield
    app.cleanup()


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
    )

    directive = Struct(
        env = app.builder.env,
        genopt = options,
        result = ViewList(),
        filename_set = set(),
    )

    processed_docstrings = []
    processed_signatures = []


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
    if name.startswith('_'):
        return True
    if name == 'skipmeth':
        return True


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
    assert_warns("failed to import method 'Class.foobar' from module 'test_autodoc_py35';",
                 'method', 'test_autodoc_py35.Class.foobar', more_content=None)

    # test auto and given content mixing
    directive.env.ref_context['py:module'] = 'test_autodoc_py35'
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
    assert_works('exception', 'test_autodoc_py35.CustomEx', all_members=True)
    assert_works('exception', 'test_autodoc_py35.CustomEx')

    # test diverse inclusion settings for members
    should = [('class', 'test_autodoc_py35.Class')]
    assert_processes(should, 'class', 'Class')
    should.extend([('method', 'test_autodoc_py35.Class.meth')])
    options.members = ['meth']
    options.exclude_members = set(['excludemeth'])
    assert_processes(should, 'class', 'Class')
    should.extend([('attribute', 'test_autodoc_py35.Class.prop'),
                   ('attribute', 'test_autodoc_py35.Class.descr'),
                   ('attribute', 'test_autodoc_py35.Class.attr'),
                   ('attribute', 'test_autodoc_py35.Class.docattr'),
                   ('attribute', 'test_autodoc_py35.Class.udocattr'),
                   ('attribute', 'test_autodoc_py35.Class.mdocattr'),
                   ('attribute', 'test_autodoc_py35.Class.inst_attr_comment'),
                   ('attribute', 'test_autodoc_py35.Class.inst_attr_inline'),
                   ('attribute', 'test_autodoc_py35.Class.inst_attr_string'),
                   ('method', 'test_autodoc_py35.Class.moore'),
                   ])
    if six.PY3 and sys.version_info[:2] >= (3, 5):
        should.extend([
            ('method', 'test_autodoc_py35.Class.do_coroutine'),
        ])
    options.members = ALL
    assert_processes(should, 'class', 'Class')
    options.undoc_members = True
    should.extend((('attribute', 'test_autodoc_py35.Class.skipattr'),
                   ('method', 'test_autodoc_py35.Class.undocmeth'),
                   ('method', 'test_autodoc_py35.Class.roger')))
    assert_processes(should, 'class', 'Class')
    options.inherited_members = True
    should.append(('method', 'test_autodoc_py35.Class.inheritedmeth'))
    assert_processes(should, 'class', 'Class')

    # test special members
    options.special_members = ['__special1__']
    should.append(('method', 'test_autodoc_py35.Class.__special1__'))
    assert_processes(should, 'class', 'Class')
    options.special_members = ALL
    should.append(('method', 'test_autodoc_py35.Class.__special2__'))
    assert_processes(should, 'class', 'Class')
    options.special_members = False


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

    def meth(self):
        """Function."""
        return "The Answer"


def _funky_classmethod(name, b, c, d, docstring=None):
    """Generates a classmethod for a class from a template by filling out
    some arguments."""
    def template(cls, a, b, c, d=4, e=5, f=6):
        return a, b, c, d, e, f
    from functools import partial
    function = partial(template, b=b, c=c, d=d)
    function.__name__ = name
    function.__doc__ = docstring
    return classmethod(function)


class Base(object):
    def inheritedmeth(self):
        """Inherited function."""


if six.PY3 and sys.version_info[:2] >= (3, 5):
    async def _other_coro_func():
        return "run"


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

    @property
    def prop(self):
        """Property."""

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
        self.inst_attr_inline = None  #: an inline documented instance attr
        #: a documented instance attribute
        self.inst_attr_comment = None
        self.inst_attr_string = None
        """a documented instance attribute"""

    def __special1__(self):
        """documented special method"""

    def __special2__(self):
        # undocumented special method
        pass

    if six.PY3 and sys.version_info[:2] >= (3, 5):

        async def do_coroutine(self):
            """A documented coroutine function"""
            attr_coro_result = await _other_coro_func()  # NOQA
