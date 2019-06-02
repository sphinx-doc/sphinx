"""
    test_ext_autodoc_configs
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly for config variables

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import platform

import pytest

from sphinx.ext.autodoc import merge_autodoc_default_flags
from test_autodoc import do_autodoc

IS_PYPY = platform.python_implementation() == 'PyPy'


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
        '   .. py:method:: DocstringSig.prop1',
        '      :module: target',
        '      :property:',
        '   ',
        '      First line of docstring',
        '      ',
        '   ',
        '   .. py:method:: DocstringSig.prop2',
        '      :module: target',
        '      :property:',
        '   ',
        '      First line of docstring',
        '      Second line of docstring',
        '      '
    ]

    # disable autodoc_docstring_signature
    app.config.autodoc_docstring_signature = False
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        '.. py:class:: DocstringSig',
        '   :module: target',
        '',
        '   ',
        '   .. py:method:: DocstringSig.meth()',
        '      :module: target',
        '   ',
        '      meth(FOO, BAR=1) -> BAZ',
        '      First line of docstring',
        '      ',
        '              rest of docstring',
        '              ',
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
        '   .. py:method:: DocstringSig.prop1',
        '      :module: target',
        '      :property:',
        '   ',
        '      DocstringSig.prop1(self)',
        '      First line of docstring',
        '      ',
        '   ',
        '   .. py:method:: DocstringSig.prop2',
        '      :module: target',
        '      :property:',
        '   ',
        '      First line of docstring',
        '      Second line of docstring',
        '      '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_mocked_module_imports(app, warning):
    # no autodoc_mock_imports
    options = {"members": 'TestAutodoc,decoratedFunction,func'}
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == []
    assert "autodoc: failed to import module 'need_mocks'" in warning.getvalue()

    # with autodoc_mock_imports
    app.config.autodoc_mock_imports = [
        'missing_module',
        'missing_package1',
        'missing_package2',
        'missing_package3',
        'sphinx.missing_module4',
    ]

    warning.truncate(0)
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.need_mocks',
        '',
        '',
        '.. py:class:: TestAutodoc',
        '   :module: target.need_mocks',
        '',
        '   TestAutodoc docstring.',
        '   ',
        '   ',
        '   .. py:method:: TestAutodoc.decoratedMethod()',
        '      :module: target.need_mocks',
        '   ',
        '      TestAutodoc::decoratedMethod docstring',
        '      ',
        '',
        '.. py:function:: decoratedFunction()',
        '   :module: target.need_mocks',
        '',
        '   decoratedFunction docstring',
        '   ',
        '',
        '.. py:function:: func(arg: missing_module.Class)',
        '   :module: target.need_mocks',
        '',
        '   a function takes mocked object as an argument',
        '   '
    ]
    assert warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_typehints_signature(app):
    app.config.autodoc_typehints = "signature"

    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:class:: Math(s: str, o: object = None)',
        '   :module: target.typehints',
        '',
        '   ',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '   ',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_typehints_none(app):
    app.config.autodoc_typehints = "none"

    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:class:: Math(s, o = None)',
        '   :module: target.typehints',
        '',
        '   ',
        '   .. py:method:: Math.incr(a, b = 1) -> int',
        '      :module: target.typehints',
        '   ',
        '',
        '.. py:function:: incr(a, b = 1) -> int',
        '   :module: target.typehints',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
@pytest.mark.filterwarnings('ignore:autodoc_default_flags is now deprecated.')
def test_merge_autodoc_default_flags1(app):
    app.config.autodoc_default_flags = ['members', 'undoc-members']
    merge_autodoc_default_flags(app, app.config)
    assert app.config.autodoc_default_options == {'members': None,
                                                  'undoc-members': None}


@pytest.mark.sphinx('html', testroot='ext-autodoc')
@pytest.mark.filterwarnings('ignore:autodoc_default_flags is now deprecated.')
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
    actual = do_autodoc(app, 'module', 'target')
    assert '.. py:function:: save_traceback(app: Sphinx) -> str' not in actual

    # with :members:
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: = True
    app.config.autodoc_default_options = {'members': True}
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

    # with :imported-members:
    app.config.autodoc_default_options = {
        'members': None,
        'imported-members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc(app, 'module', 'target')
    print('\n'.join(actual))
    assert '.. py:function:: save_traceback(app: Sphinx) -> str' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options_with_values(app):
    # with :members:
    app.config.autodoc_default_options = {'members': 'val1,val2'}
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :member-order:
    app.config.autodoc_default_options = {
        'members': None,
        'member-order': 'bysource',
    }
    actual = do_autodoc(app, 'class', 'target.Class')
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
    ]

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
