"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import itertools
import logging
import pathlib
import sys
from typing import TYPE_CHECKING
from warnings import catch_warnings

import pytest

from sphinx.environment import _CurrentDocument
from sphinx.ext.autodoc._directive_options import (
    _AutoDocumenterOptions,
    inherited_members_option,
)
from sphinx.ext.autodoc._dynamic._docstrings import _get_docstring_lines
from sphinx.ext.autodoc._generate import _auto_document_object
from sphinx.ext.autodoc._legacy_class_based._documenters import Documenter
from sphinx.ext.autodoc._property_types import _ItemProperties
from sphinx.ext.autodoc._sentinels import ALL
from sphinx.ext.autodoc._shared import _AutodocAttrGetter, _AutodocConfig
from sphinx.util.inspect import safe_getattr

from tests.test_ext_autodoc.autodoc_util import FakeEvents, do_autodoc

try:
    # Enable pyximport to test cython module
    import pyximport

    pyximport.install()
except ImportError:
    pyximport = None

if TYPE_CHECKING:
    from typing import Any

    from sphinx.ext.autodoc._property_types import _AutodocObjType
    from sphinx.ext.autodoc._shared import _AttrGetter

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')

processed_signatures: list[tuple[str, str]] = []


def get_docstring_lines(obj_type, obj):
    config = _AutodocConfig()

    parent = object  # dummy
    props = _ItemProperties(
        obj_type=obj_type,
        module_name='',
        parts=(obj.__name__,),
        docstring_lines=(),
        _obj=obj,
        _obj___module__=getattr(obj, '__module__', None),
    )
    ds = _get_docstring_lines(
        props,
        class_doc_from=config.autoclass_content,
        get_attr=safe_getattr,
        inherit_docstrings=config.autodoc_inherit_docstrings,
        parent=parent,
        tab_width=8,
    )
    # for testing purposes, concat them and strip the empty line at the end
    res = list(itertools.chain.from_iterable(ds or ()))
    if res:
        res.pop()
    return tuple(res)


def test_get_docstring_lines():
    # objects without docstring
    def f():
        pass

    assert get_docstring_lines('function', f) == ()

    # standard function, diverse docstring styles...
    def f():
        """Docstring"""

    assert get_docstring_lines('function', f) == ('Docstring',)

    def f():
        """
        Docstring
        """  # NoQA: D212

    assert get_docstring_lines('function', f) == ('Docstring',)

    # first line vs. other lines indentation
    def f():
        """First line

        Other
          lines
        """

    assert get_docstring_lines('function', f) == (
        'First line',
        '',
        'Other',
        '  lines',
    )

    # charset guessing (this module is encoded in utf-8)
    def f():
        """Döcstring"""

    assert get_docstring_lines('function', f) == ('Döcstring',)

    # verify that method docstrings get extracted in both normal case
    # and in case of bound method posing as a function
    class J:
        def foo(self):
            """Method docstring"""

    expected = ('Method docstring',)
    assert get_docstring_lines('method', J.foo) == expected
    assert get_docstring_lines('function', J().foo) == expected


class _MyDocumenter(Documenter):
    objtype = 'integer'
    directivetype = 'integer'
    priority = 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, int)

    def document_members(self, all_members=False):
        return


def test_new_documenter():
    config = _AutodocConfig()
    # app.add_autodocumenter(_MyDocumenter)

    options = {'members': 'integer'}
    # TODO: Fix! Perhaps add a way to signal module/class-level?
    actual = do_autodoc('module', 'target', config=config, options=options)
    return
    assert actual == [
        '',
        '.. py:module:: target',
        '',
        '',
        '.. py:integer:: integer',
        '   :module: target',
        '',
        '   documentation for the integer',
        '',
    ]


getattr_spy = []


def test_attrgetter_using():
    attrs = []

    def _special_getattr(obj, attr_name, *defargs):
        if attr_name in attrs:
            getattr_spy.append((obj, attr_name))
            return None
        return getattr(obj, attr_name, *defargs)

    # See Sphinx.add_autodoc_attrgetter()
    autodoc_attrgetters = {type: _special_getattr}
    get_attr = _AutodocAttrGetter(autodoc_attrgetters)
    options = _AutoDocumenterOptions(members=ALL)

    options.inherited_members = inherited_members_option(False)
    attrs[:] = ['meth']
    with catch_warnings(record=True):
        _assert_getter_works(
            'class',
            'target.Class',
            *attrs,
            get_attr=get_attr,
            options=options,
        )

    options.inherited_members = inherited_members_option(True)
    attrs[:] = ['inheritedmeth']
    with catch_warnings(record=True):
        _assert_getter_works(
            'class',
            'target.inheritance.Derived',
            *attrs,
            get_attr=get_attr,
            options=options,
        )


def _assert_getter_works(
    objtype: _AutodocObjType,
    name: str,
    *attrs: str,
    get_attr: _AttrGetter,
    options: _AutoDocumenterOptions,
) -> None:
    getattr_spy.clear()

    config = _AutodocConfig()
    current_document = _CurrentDocument()
    events = FakeEvents()

    _auto_document_object(
        config=config,
        current_document=current_document,
        events=events,
        get_attr=get_attr,
        more_content=None,
        name=name,
        obj_type=objtype,
        options=options,
        record_dependencies=set(),
        ref_context={},
        reread_always=set(),
    )

    hooked_members = {s[1] for s in getattr_spy}
    documented_members = {s[1] for s in processed_signatures}
    for attr in attrs:
        fullname = f'{name}.{attr}'
        assert attr in hooked_members
        assert fullname not in documented_members, f'{fullname!r} not intercepted'


def test_py_module(caplog: pytest.LogCaptureFixture) -> None:
    # work around sphinx.util.logging.setup()
    logger = logging.getLogger('sphinx')
    logger.handlers[:] = [caplog.handler]
    caplog.set_level(logging.WARNING)

    # without py:module
    actual = do_autodoc('method', 'Class.meth', expect_import_error=True)
    assert actual == []
    assert len(set(caplog.messages)) == 1
    assert (
        "don't know which module to import for autodocumenting 'Class.meth'"
    ) in caplog.messages[0]
    caplog.clear()

    # with py:module
    ref_context: dict[str, Any] = {'py:module': 'target'}
    actual = do_autodoc('method', 'Class.meth', ref_context=ref_context)
    assert actual == [
        '',
        '.. py:method:: Class.meth()',
        '   :module: target',
        '',
        '   Function.',
        '',
    ]
    assert len(caplog.records) == 0


def test_autodoc_decorator() -> None:
    actual = do_autodoc('decorator', 'target.decorator.deco1')
    assert actual == [
        '',
        '.. py:decorator:: deco1',
        '   :module: target.decorator',
        '',
        '   docstring for deco1',
        '',
    ]

    actual = do_autodoc('decorator', 'target.decorator.deco2')
    assert actual == [
        '',
        '.. py:decorator:: deco2(condition, message)',
        '   :module: target.decorator',
        '',
        '   docstring for deco2',
        '',
    ]


def test_autodoc_exception() -> None:
    actual = do_autodoc('exception', 'target.CustomEx')
    assert actual == [
        '',
        '.. py:exception:: CustomEx',
        '   :module: target',
        '',
        '   My custom exception.',
        '',
    ]


def test_autodoc_warnings(caplog: pytest.LogCaptureFixture) -> None:
    # work around sphinx.util.logging.setup()
    logger = logging.getLogger('sphinx')
    logger.handlers[:] = [caplog.handler]
    caplog.set_level(logging.WARNING)

    current_document = _CurrentDocument(docname='dummy')

    # can't import module
    caplog.clear()
    do_autodoc(
        'module', 'unknown', current_document=current_document, expect_import_error=True
    )
    assert len(set(caplog.messages)) == 1
    assert "failed to import 'unknown'" in caplog.messages[0]

    # missing function
    caplog.clear()
    do_autodoc(
        'function',
        'unknown',
        current_document=current_document,
        expect_import_error=True,
    )
    assert len(set(caplog.messages)) == 1
    assert "import for autodocumenting 'unknown'" in caplog.messages[0]

    caplog.clear()
    do_autodoc(
        'function',
        'target.unknown',
        current_document=current_document,
        expect_import_error=True,
    )
    assert len(set(caplog.messages)) == 1
    assert "failed to import 'unknown' from module 'target'" in caplog.messages[0]

    # missing method
    caplog.clear()
    do_autodoc(
        'method',
        'target.Class.unknown',
        current_document=current_document,
        expect_import_error=True,
    )
    assert len(set(caplog.messages)) == 1
    assert "failed to import 'Class.unknown' from module 'target'" in caplog.messages[0]


def test_autodoc_attributes() -> None:
    options = {
        'synopsis': 'Synopsis',
        'platform': 'Platform',
        'deprecated': None,
    }
    actual = do_autodoc('module', 'target', options=options)
    assert actual == [
        '',
        '.. py:module:: target',
        '   :synopsis: Synopsis',
        '   :platform: Platform',
        '   :deprecated:',
        '',
    ]


def test_autodoc_members() -> None:
    options: dict[str, Any]

    # default (no-members)
    actual = do_autodoc('class', 'target.inheritance.Base')
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
    ]

    # default ALL-members
    options = {'members': None}
    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # default specific-members
    options = {'members': 'inheritedmeth,inheritedstaticmeth'}
    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # ALL-members override autodoc_default_options
    options = {'members': None}
    config = _AutodocConfig(autodoc_default_options={'members': 'inheritedstaticmeth'})
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # members override autodoc_default_options
    options = {'members': 'inheritedmeth'}
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
    ]

    # members extends autodoc_default_options
    options = {'members': '+inheritedmeth'}
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]


def test_autodoc_exclude_members() -> None:
    options = {
        'members': None,
        'exclude-members': 'inheritedmeth,inheritedstaticmeth',
    }
    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # members vs exclude-members
    options = {
        'members': 'inheritedmeth',
        'exclude-members': 'inheritedmeth',
    }
    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
    ]

    # + has no effect when autodoc_default_options are not present
    options = {
        'members': None,
        'exclude-members': '+inheritedmeth,inheritedstaticmeth',
    }
    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # exclude-members overrides autodoc_default_options
    options = {
        'members': None,
        'exclude-members': 'inheritedmeth',
    }
    config = _AutodocConfig(
        autodoc_default_options={'exclude-members': 'inheritedstaticmeth'}
    )
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # exclude-members extends autodoc_default_options
    options = {
        'members': None,
        'exclude-members': '+inheritedmeth',
    }
    config = _AutodocConfig(
        autodoc_default_options={'exclude-members': 'inheritedstaticmeth'}
    )
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # no exclude-members causes use autodoc_default_options
    options = {'members': None}
    config = _AutodocConfig(
        autodoc_default_options={'exclude-members': 'inheritedstaticmeth,inheritedmeth'}
    )
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # empty exclude-members cancels autodoc_default_options
    options = {
        'members': None,
        'exclude-members': None,
    }
    config = _AutodocConfig(
        autodoc_default_options={'exclude-members': 'inheritedstaticmeth,inheritedmeth'}
    )
    actual = do_autodoc(
        'class', 'target.inheritance.Base', config=config, options=options
    )
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]


def test_autodoc_undoc_members() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # use autodoc_default_options
    options = {'members': None}
    config = _AutodocConfig(autodoc_default_options={'undoc-members': True})
    actual = do_autodoc('class', 'target.Class', config=config, options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # options negation work check
    options = {
        'members': None,
        'no-undoc-members': None,
    }
    actual = do_autodoc('class', 'target.Class', config=config, options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
    ]


def test_autodoc_undoc_members_for_metadata_only() -> None:
    # metadata only member is not displayed
    options = {'members': None}
    actual = do_autodoc('module', 'target.metadata', options=options)
    assert actual == [
        '',
        '.. py:module:: target.metadata',
        '',
    ]

    # metadata only member is displayed when undoc-member given
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.metadata', options=options)
    assert actual == [
        '',
        '.. py:module:: target.metadata',
        '',
        '',
        '.. py:function:: foo()',
        '   :module: target.metadata',
        '',
        '   :meta metadata-only-docstring:',
        '',
    ]


def test_autodoc_inherited_members() -> None:
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc('class', 'target.inheritance.Derived', options=options)
    assert [line for line in actual if 'method::' in line] == [
        '   .. py:method:: Derived.another_inheritedmeth()',
        '   .. py:method:: Derived.inheritedclassmeth()',
        '   .. py:method:: Derived.inheritedmeth()',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
    ]


def test_autodoc_inherited_members_Base() -> None:
    options = {
        'members': None,
        'inherited-members': 'Base',
        'special-members': None,
    }

    # check methods for object class are shown
    actual = do_autodoc('class', 'target.inheritance.Derived', options=options)
    assert '   .. py:method:: Derived.inheritedmeth()' in actual
    assert '   .. py:method:: Derived.inheritedclassmeth' not in actual


def test_autodoc_inherited_members_None() -> None:
    options = {
        'members': None,
        'inherited-members': 'None',
        'special-members': None,
    }

    # check methods for object class are shown
    actual = do_autodoc('class', 'target.inheritance.Derived', options=options)
    assert '   .. py:method:: Derived.__init__()' in actual
    assert '   .. py:method:: Derived.__str__()' in actual


def test_autodoc_imported_members() -> None:
    options = {
        'members': None,
        'imported-members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc('module', 'target', options=options)
    assert (
        '.. py:function:: function_to_be_imported(app: ~sphinx.application.Sphinx | None) -> str'
    ) in actual


def test_autodoc_special_members() -> None:
    # specific special methods
    options = {
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # combination with specific members
    options = {
        'members': 'attr,docattr',
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
    ]

    # all special methods
    options = {
        'members': None,
        'undoc-members': None,
        'special-members': None,
    }
    if sys.version_info >= (3, 13, 0, 'alpha', 5):
        options['exclude-members'] = '__static_attributes__,__firstlineno__'
    if sys.version_info >= (3, 14, 0, 'alpha', 7):
        ann_attrs: tuple[str, ...] = (
            '   .. py:attribute:: Class.__annotate_func__',
            '   .. py:attribute:: Class.__annotations_cache__',
        )
    else:
        ann_attrs = ('   .. py:attribute:: Class.__annotations__',)
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        *ann_attrs,
        '   .. py:attribute:: Class.__dict__',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:attribute:: Class.__module__',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
        '   .. py:attribute:: Class.__weakref__',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # specific special methods from autodoc_default_options
    options = {'undoc-members': None}
    config = _AutodocConfig(autodoc_default_options={'special-members': '__special2__'})
    actual = do_autodoc('class', 'target.Class', config=config, options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__special2__()',
    ]

    # specific special methods option with autodoc_default_options
    options = {
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    actual = do_autodoc('class', 'target.Class', config=config, options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # specific special methods merge with autodoc_default_options
    options = {
        'undoc-members': None,
        'special-members': '+__init__,__special1__',
    }
    actual = do_autodoc('class', 'target.Class', config=config, options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
    ]


def test_autodoc_ignore_module_all() -> None:
    # default (no-ignore-module-all)
    options = {'members': None}
    actual = do_autodoc('module', 'target', options=options)
    assert [line for line in actual if 'class::' in line] == [
        '.. py:class:: Class(arg)',
    ]

    # ignore-module-all
    options = {
        'members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc('module', 'target', options=options)
    assert [line for line in actual if 'class::' in line] == [
        '.. py:class:: Class(arg)',
        '.. py:class:: CustomDict',
        '.. py:class:: InnerChild()',
        '.. py:class:: InstAttCls()',
        '.. py:class:: Outer()',
        '   .. py:class:: Outer.Inner()',
        '.. py:class:: StrRepr',
    ]


def test_autodoc_noindex() -> None:
    options = {'no-index': None}
    actual = do_autodoc('module', 'target', options=options)
    assert actual == [
        '',
        '.. py:module:: target',
        '   :no-index:',
        '',
    ]

    # TODO: :no-index: should be propagated to children of target item.

    actual = do_autodoc('class', 'target.inheritance.Base', options=options)
    assert actual == [
        '',
        '.. py:class:: Base()',
        '   :no-index:',
        '   :module: target.inheritance',
        '',
    ]


def test_autodoc_subclass_of_builtin_class() -> None:
    options = {'members': None}
    actual = do_autodoc('class', 'target.CustomDict', options=options)
    assert actual == [
        '',
        '.. py:class:: CustomDict',
        '   :module: target',
        '',
        '   Docstring.',
        '',
    ]


def test_autodoc_inner_class() -> None:
    options = {'members': None}
    actual = do_autodoc('class', 'target.Outer', options=options)
    assert actual == [
        '',
        '.. py:class:: Outer()',
        '   :module: target',
        '',
        '   Foo',
        '',
        '',
        '   .. py:class:: Outer.Inner()',
        '      :module: target',
        '',
        '      Foo',
        '',
        '',
        '      .. py:method:: Outer.Inner.meth()',
        '         :module: target',
        '',
        '         Foo',
        '',
        '',
        '   .. py:attribute:: Outer.factory',
        '      :module: target',
        '',
        '      alias of :py:class:`dict`',
    ]

    actual = do_autodoc('class', 'target.Outer.Inner', options=options)
    assert actual == [
        '',
        '.. py:class:: Inner()',
        '   :module: target.Outer',
        '',
        '   Foo',
        '',
        '',
        '   .. py:method:: Inner.meth()',
        '      :module: target.Outer',
        '',
        '      Foo',
        '',
    ]

    options['show-inheritance'] = None
    actual = do_autodoc('class', 'target.InnerChild', options=options)
    assert actual == [
        '',
        '.. py:class:: InnerChild()',
        '   :module: target',
        '',
        '   Bases: :py:class:`~target.Outer.Inner`',
        '',
        '   InnerChild docstring',
        '',
    ]


def test_autodoc_classmethod() -> None:
    actual = do_autodoc('method', 'target.inheritance.Base.inheritedclassmeth')
    assert actual == [
        '',
        '.. py:method:: Base.inheritedclassmeth()',
        '   :module: target.inheritance',
        '   :classmethod:',
        '',
        '   Inherited class method.',
        '',
    ]


def test_autodoc_staticmethod() -> None:
    actual = do_autodoc('method', 'target.inheritance.Base.inheritedstaticmeth')
    assert actual == [
        '',
        '.. py:method:: Base.inheritedstaticmeth(cls)',
        '   :module: target.inheritance',
        '   :staticmethod:',
        '',
        '   Inherited static method.',
        '',
    ]


def test_autodoc_descriptor() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.descriptor.Class', options=options)
    assert actual == [
        '',
        '.. py:class:: Class()',
        '   :module: target.descriptor',
        '',
        '',
        '   .. py:attribute:: Class.descr',
        '      :module: target.descriptor',
        '',
        '      Descriptor instance docstring.',
        '',
        '',
        '   .. py:property:: Class.prop',
        '      :module: target.descriptor',
        '',
        '      Property.',
        '',
    ]


def test_autodoc_cached_property() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.cached_property.Foo', options=options)
    assert actual == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.cached_property',
        '',
        '',
        '   .. py:property:: Foo.prop',
        '      :module: target.cached_property',
        '      :type: int',
        '',
        '',
        '   .. py:property:: Foo.prop_with_type_comment',
        '      :module: target.cached_property',
        '      :type: int',
        '',
    ]


def test_autodoc_member_order() -> None:
    # case member-order='bysource'
    options = {
        'members': None,
        'member-order': 'bysource',
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class._private_inst_attr',
    ]

    # case member-order='groupwise'
    options = {
        'members': None,
        'member-order': 'groupwise',
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        # class methods
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        # static methods
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:method:: Class.b_staticmeth()',
        # regular methods
        '   .. py:method:: Class.excludemeth()',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.udocattr',
    ]

    # case member-order=None
    options = {
        'members': None,
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc('class', 'target.Class', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]


def test_autodoc_module_member_order() -> None:
    # case member-order='bysource'
    options = {
        'members': 'foo, Bar, baz, qux, Quux, foobar',
        'member-order': 'bysource',
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.sort_by_all', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:module:: target.sort_by_all',
        '.. py:function:: baz()',
        '.. py:function:: foo()',
        '.. py:class:: Bar()',
        '.. py:class:: Quux()',
        '.. py:function:: foobar()',
        '.. py:function:: qux()',
    ]

    # case member-order='bysource' and ignore-module-all
    options = {
        'members': 'foo, Bar, baz, qux, Quux, foobar',
        'member-order': 'bysource',
        'undoc-members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc('module', 'target.sort_by_all', options=options)
    assert [line for line in actual if '::' in line] == [
        '.. py:module:: target.sort_by_all',
        '.. py:function:: foo()',
        '.. py:class:: Bar()',
        '.. py:function:: baz()',
        '.. py:function:: qux()',
        '.. py:class:: Quux()',
        '.. py:function:: foobar()',
    ]


def test_autodoc_module_scope() -> None:
    current_document = _CurrentDocument(docname='index')
    current_document.autodoc_module = 'target'
    actual = do_autodoc(
        'attribute', 'Class.mdocattr', current_document=current_document
    )
    assert actual == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '',
    ]


def test_autodoc_class_scope() -> None:
    current_document = _CurrentDocument(docname='index')
    current_document.autodoc_module = 'target'
    current_document.autodoc_class = 'Class'
    actual = do_autodoc('attribute', 'mdocattr', current_document=current_document)
    assert actual == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '',
    ]


def test_class_attributes() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.AttCls', options=options)
    assert actual == [
        '',
        '.. py:class:: AttCls()',
        '   :module: target',
        '',
        '',
        '   .. py:attribute:: AttCls.a1',
        '      :module: target',
        '      :value: hello world',
        '',
        '',
        '   .. py:attribute:: AttCls.a2',
        '      :module: target',
        '      :value: None',
        '',
    ]


def test_autoclass_instance_attributes() -> None:
    options: dict[str, Any]
    options = {'members': None}
    actual = do_autodoc('class', 'target.InstAttCls', options=options)
    assert actual == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca2',
        '      :module: target',
        "      :value: 'b'",
        '',
        '      Doc comment for InstAttCls.ca2. One line only.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca3',
        '      :module: target',
        "      :value: 'c'",
        '',
        '      Docstring for class attribute InstAttCls.ca3.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia2',
        '      :module: target',
        '',
        '      Docstring for instance attribute InstAttCls.ia2.',
        '',
    ]

    # pick up arbitrary attributes
    options = {'members': 'ca1,ia1'}
    actual = do_autodoc('class', 'target.InstAttCls', options=options)
    assert actual == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '',
    ]


def test_autoattribute_instance_attributes() -> None:
    actual = do_autodoc('attribute', 'target.InstAttCls.ia1')
    assert actual == [
        '',
        '.. py:attribute:: InstAttCls.ia1',
        '   :module: target',
        '',
        '   Doc comment for instance attribute InstAttCls.ia1',
        '',
    ]


def test_slots() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.slots', options=options)
    assert actual == [
        '',
        '.. py:module:: target.slots',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.slots',
        '      :type: int',
        '',
        '      docstring of attr1',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.slots',
        '',
        '      docstring of instance attr2',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.slots',
        '',
        '',
        '.. py:class:: Baz()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Baz.attr',
        '      :module: target.slots',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr',
        '      :module: target.slots',
        '',
    ]


class _EnumFormatter:
    def __init__(self, name: str, *, module: str = 'target.enums') -> None:
        self.name = name
        self.module = module

    @property
    def target(self) -> str:
        """The autodoc target class."""
        return f'{self.module}.{self.name}'

    def subtarget(self, name: str) -> str:
        """The autodoc sub-target (an attribute, method, etc)."""
        return f'{self.target}.{name}'

    def _node(
        self,
        role: str,
        name: str,
        doc: str,
        *,
        args: str,
        indent: int,
        **options: Any,
    ) -> list[str]:
        prefix = indent * ' '
        tab = ' ' * 3

        def rst_option(name: str, value: Any) -> str:
            value = '' if value == 1 else value  # note True == 1.
            return f'{prefix}{tab}:{name}: {value!s}'.rstrip()

        lines = [
            '',
            f'{prefix}.. py:{role}:: {name}{args}',
            f'{prefix}{tab}:module: {self.module}',
            *itertools.starmap(rst_option, options.items()),
        ]
        if doc:
            lines.extend(['', f'{prefix}{tab}{doc}'])
        lines.append('')
        return lines

    def entry(
        self,
        entry_name: str,
        doc: str = '',
        *,
        role: str,
        args: str = '',
        indent: int = 3,
        **rst_options: Any,
    ) -> list[str]:
        """Get the RST lines for a named attribute, method, etc."""
        qualname = f'{self.name}.{entry_name}'
        return self._node(role, qualname, doc, args=args, indent=indent, **rst_options)

    def preamble_lookup(
        self, doc: str, *, indent: int = 0, **options: Any
    ) -> list[str]:
        assert doc, (
            f'enumeration class {self.target!r} should have an explicit docstring'
        )

        args = self._preamble_args(functional_constructor=False)
        return self._preamble(doc=doc, args=args, indent=indent, **options)

    def preamble_constructor(
        self, doc: str, *, indent: int = 0, **options: Any
    ) -> list[str]:
        assert doc, (
            f'enumeration class {self.target!r} should have an explicit docstring'
        )

        args = self._preamble_args(functional_constructor=True)
        return self._preamble(doc=doc, args=args, indent=indent, **options)

    def _preamble(
        self, *, doc: str, args: str, indent: int = 0, **options: Any
    ) -> list[str]:
        """Generate the preamble of the class being documented."""
        return self._node('class', self.name, doc, args=args, indent=indent, **options)

    @staticmethod
    def _preamble_args(functional_constructor: bool = False) -> str:
        """EnumType.__call__() is a dual-purpose method:

        * Look an enum member (valid only if the enum has members)
        * Create a new enum class (functional API)
        """
        if sys.version_info[:2] >= (3, 14):
            if functional_constructor:
                return (
                    '(new_class_name, /, names, *, module=None, '
                    'qualname=None, type=None, start=1, boundary=None)'
                )
            else:
                return '(*values)'
        if sys.version_info[:2] >= (3, 13) or sys.version_info[:3] >= (3, 12, 3):
            if functional_constructor:
                return (
                    '(new_class_name, /, names, *, module=None, '
                    'qualname=None, type=None, start=1, boundary=None)'
                )
            else:
                return '(*values)'
        return (
            '(value, names=None, *values, module=None, '
            'qualname=None, type=None, start=1, boundary=None)'
        )

    def method(
        self,
        name: str,
        doc: str,
        *flags: str,
        args: str = '()',
        indent: int = 3,
    ) -> list[str]:
        rst_options = dict.fromkeys(flags, '')
        return self.entry(
            name, doc, role='method', args=args, indent=indent, **rst_options
        )

    def member(self, name: str, value: Any, doc: str, *, indent: int = 3) -> list[str]:
        rst_options = {'value': repr(value)}
        return self.entry(name, doc, role='attribute', indent=indent, **rst_options)


@pytest.fixture
def autodoc_enum_options() -> dict[str, object]:
    """Default autodoc options to use when testing enum's documentation."""
    return {'members': None, 'undoc-members': None}


def test_enum_class(autodoc_enum_options):
    fmt = _EnumFormatter('EnumCls')
    options = autodoc_enum_options | {'private-members': None}

    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method(
            'say_goodbye', 'a classmethod says good-bye to you.', 'classmethod'
        ),
        *fmt.method('say_hello', 'a method says hello to you.'),
        *fmt.member('val1', 12, 'doc for val1'),
        *fmt.member('val2', 23, 'doc for val2'),
        *fmt.member('val3', 34, 'doc for val3'),
        *fmt.member('val4', 34, ''),  # val4 is alias of val3
    ]

    # Inherited members exclude the native Enum API (in particular
    # the 'name' and 'value' properties), unless they were explicitly
    # redefined by the user in one of the bases.
    actual = do_autodoc(
        'class', fmt.target, options=options | {'inherited-members': None}
    )
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method(
            'say_goodbye', 'a classmethod says good-bye to you.', 'classmethod'
        ),
        *fmt.method('say_hello', 'a method says hello to you.'),
        *fmt.member('val1', 12, 'doc for val1'),
        *fmt.member('val2', 23, 'doc for val2'),
        *fmt.member('val3', 34, 'doc for val3'),
        *fmt.member('val4', 34, ''),  # val4 is alias of val3
    ]

    # checks for an attribute of EnumCls
    actual = do_autodoc('attribute', fmt.subtarget('val1'))
    assert actual == fmt.member('val1', 12, 'doc for val1', indent=0)


def test_enum_class_with_data_type(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithDataType')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'x', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'x', ''),
    ]


def test_enum_class_with_mixin_type(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinType')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


def test_enum_class_with_mixin_type_and_inheritence(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinTypeInherit')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


def test_enum_class_with_mixin_enum_type(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinEnumType')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        # override() is overridden at the class level so it should be rendered
        *fmt.method('override', 'overridden'),
        # say_goodbye() and say_hello() are not rendered since they are inherited
        *fmt.member('x', 'x', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('override', 'overridden'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.member('x', 'x', ''),
    ]


def test_enum_class_with_mixin_and_data_type(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinAndDataType')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    # add the special member __str__ (but not the inherited members)
    options = autodoc_enum_options | {'special-members': '__str__'}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('__str__', 'overridden'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


def test_enum_with_parent_enum(autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithParentEnum')

    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('isupper', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    # add the special member __str__ (but not the inherited members)
    options = autodoc_enum_options | {'special-members': '__str__'}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('__str__', 'overridden'),
        *fmt.method('isupper', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('override', 'inherited'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


def test_enum_sunder_method(autodoc_enum_options):
    PRIVATE = {'private-members': None}  # sunder methods are recognized as private

    fmt = _EnumFormatter('EnumSunderMissingInNonEnumMixin')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options | PRIVATE)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInEnumMixin')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options | PRIVATE)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInDataType')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options | PRIVATE)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInClass')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options | PRIVATE)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'docstring', 'classmethod', args='(value)'),
    ]


def test_enum_inherited_sunder_method(autodoc_enum_options):
    options = autodoc_enum_options | {
        'private-members': None,
        'inherited-members': None,
    }

    fmt = _EnumFormatter('EnumSunderMissingInNonEnumMixin')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInEnumMixin')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInDataType')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInClass')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'docstring', 'classmethod', args='(value)'),
    ]


def test_enum_custom_name_property(autodoc_enum_options):
    fmt = _EnumFormatter('EnumNamePropertyInNonEnumMixin')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInEnumMixin')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInDataType')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInClass')
    actual = do_autodoc('class', fmt.target, options=autodoc_enum_options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'docstring', role='property'),
    ]


def test_enum_inherited_custom_name_property(autodoc_enum_options):
    options = autodoc_enum_options | {'inherited-members': None}

    fmt = _EnumFormatter('EnumNamePropertyInNonEnumMixin')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInEnumMixin')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInDataType')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInClass')
    actual = do_autodoc('class', fmt.target, options=options)
    assert actual == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'docstring', role='property'),
    ]


def test_descriptor_class() -> None:
    options = {'members': 'CustomDataDescriptor,CustomDataDescriptor2'}
    actual = do_autodoc('module', 'target.descriptor', options=options)
    assert actual == [
        '',
        '.. py:module:: target.descriptor',
        '',
        '',
        '.. py:class:: CustomDataDescriptor(doc)',
        '   :module: target.descriptor',
        '',
        '   Descriptor class docstring.',
        '',
        '',
        '   .. py:method:: CustomDataDescriptor.meth()',
        '      :module: target.descriptor',
        '',
        '      Function.',
        '',
        '',
        '.. py:class:: CustomDataDescriptor2(doc)',
        '   :module: target.descriptor',
        '',
        '   Descriptor class with custom metaclass docstring.',
        '',
    ]


def test_automethod_for_builtin() -> None:
    actual = do_autodoc('method', 'builtins.int.__add__')
    assert actual == [
        '',
        '.. py:method:: int.__add__(value, /)',
        '   :module: builtins',
        '',
        '   Return self+value.',
        '',
    ]


def test_automethod_for_decorated() -> None:
    actual = do_autodoc('method', 'target.decorator.Bar.meth')
    assert actual == [
        '',
        '.. py:method:: Bar.meth(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


def test_abstractmethods() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.abstractmethods', options=options)
    assert actual == [
        '',
        '.. py:module:: target.abstractmethods',
        '',
        '',
        '.. py:class:: Base()',
        '   :module: target.abstractmethods',
        '',
        '',
        '   .. py:method:: Base.abstractmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '',
        '',
        '   .. py:method:: Base.classmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :classmethod:',
        '',
        '',
        '   .. py:method:: Base.coroutinemeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :async:',
        '',
        '',
        '   .. py:method:: Base.meth()',
        '      :module: target.abstractmethods',
        '',
        '',
        '   .. py:property:: Base.prop',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '',
        '',
        '   .. py:method:: Base.staticmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :staticmethod:',
        '',
    ]


def test_partialfunction() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.partialfunction', options=options)
    assert actual == [
        '',
        '.. py:module:: target.partialfunction',
        '',
        '',
        '.. py:function:: func1(a, b, c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '',
        '',
        '.. py:function:: func2(b, c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '',
        '',
        '.. py:function:: func3(c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '',
        '',
        '.. py:function:: func4()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '',
    ]


def test_imported_partialfunction_should_not_shown_without_imported_members() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.imported_members', options=options)
    assert actual == [
        '',
        '.. py:module:: target.imported_members',
        '',
    ]


def test_bound_method() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.bound_method', options=options)
    assert actual == [
        '',
        '.. py:module:: target.bound_method',
        '',
        '',
        '.. py:function:: bound_method()',
        '   :module: target.bound_method',
        '',
        '   Method docstring',
        '',
    ]


def test_partialmethod() -> None:
    expected = [
        '',
        '.. py:class:: Cell()',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '',
        '   refs: https://docs.python.org/3/library/functools.html#functools.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '',
        '      Make a cell alive.',
        '',
        '',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '',
        '      Update state of cell to *state*.',
        '',
    ]

    options = {'members': None}
    actual = do_autodoc('class', 'target.partialmethod.Cell', options=options)
    assert actual == expected


def test_partialmethod_undoc_members() -> None:
    expected = [
        '',
        '.. py:class:: Cell()',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '',
        '   refs: https://docs.python.org/3/library/functools.html#functools.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '',
        '      Make a cell alive.',
        '',
        '',
        '   .. py:method:: Cell.set_dead()',
        '      :module: target.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '',
        '      Update state of cell to *state*.',
        '',
    ]

    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.partialmethod.Cell', options=options)
    assert actual == expected


def test_autodoc_typed_instance_variables() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    # First compute autodoc of a `Derived` member to verify that it
    # doesn't result in inherited members in
    # `Derived.__annotations__`.
    # https://github.com/sphinx-doc/sphinx/issues/13934
    do_autodoc('attribute', 'target.typed_vars.Derived.attr2')
    actual = do_autodoc('module', 'target.typed_vars', options=options)
    assert actual == [
        '',
        '.. py:module:: target.typed_vars',
        '',
        '',
        '.. py:attribute:: Alias',
        '   :module: target.typed_vars',
        '',
        '   alias of :py:class:`~target.typed_vars.Derived`',
        '',
        '.. py:class:: Class()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Class.attr1',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Class.attr2',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Class.attr3',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Class.attr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr4',
        '',
        '',
        '   .. py:attribute:: Class.attr5',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr5',
        '',
        '',
        '   .. py:attribute:: Class.attr6',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr6',
        '',
        '',
        '   .. py:attribute:: Class.descr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      This is descr4',
        '',
        '',
        '.. py:class:: Derived()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Derived.attr7',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '.. py:data:: attr1',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr1',
        '',
        '',
        '.. py:data:: attr2',
        '   :module: target.typed_vars',
        '   :type: str',
        '',
        '   attr2',
        '',
        '',
        '.. py:data:: attr3',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr3',
        '',
    ]


def test_autodoc_typed_inherited_instance_variables() -> None:
    options = {
        'members': None,
        'undoc-members': None,
        'inherited-members': None,
    }
    actual = do_autodoc('class', 'target.typed_vars.Derived', options=options)
    assert actual == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Derived.attr2',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Derived.attr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr4',
        '',
        '',
        '   .. py:attribute:: Derived.attr5',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr5',
        '',
        '',
        '   .. py:attribute:: Derived.attr6',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr6',
        '',
        '',
        '   .. py:attribute:: Derived.attr7',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Derived.descr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
    ]


def test_autodoc_GenericAlias() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.genericalias', options=options)
    assert actual == [
        '',
        '.. py:module:: target.genericalias',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.genericalias',
        '',
        '',
        '   .. py:attribute:: Class.T',
        '      :module: target.genericalias',
        '',
        '      A list of int',
        '',
        '      alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
        '',
        '.. py:data:: L',
        '   :module: target.genericalias',
        '',
        '   A list of Class',
        '',
        '   alias of :py:class:`~typing.List`\\ '
        '[:py:class:`~target.genericalias.Class`]',
        '',
        '',
        '.. py:data:: T',
        '   :module: target.genericalias',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


def test_autodoc_pep695_type_alias() -> None:
    config = _AutodocConfig(
        autodoc_type_aliases={
            'buffer_like': 'buffer_like',
            'pathlike': 'pathlike',
            'Handler': 'Handler',
        }
    )
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.pep695', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.pep695',
        '',
        '',
        '.. py:class:: Bar',
        '   :module: target.pep695',
        '',
        '   This is newtype of Pep695Alias.',
        '',
        '   alias of :py:type:`~target.pep695.Pep695Alias`',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.pep695',
        '',
        '   This is class Foo.',
        '',
        '',
        '.. py:data:: Handler',
        '   :module: target.pep695',
        '',
        '   A generic type alias',
        '',
        '   alias of :py:class:`type`\\ [:py:class:`Exception`]',
        '',
        '',
        '.. py:type:: HandlerTypeAliasType',
        '   :module: target.pep695',
        '   :canonical: type[Exception]',
        '',
        '   This is an explicitly constructed generic alias typing.TypeAlias.',
        '',
        '',
        '.. py:type:: Pep695Alias',
        '   :module: target.pep695',
        '   :canonical: ~target.pep695.Foo',
        '',
        '   This is PEP695 type alias.',
        '',
        '',
        '.. py:type:: Pep695AliasC',
        '   :module: target.pep695',
        '   :canonical: dict[str, ~target.pep695.Foo]',
        '',
        '   This is PEP695 complex type alias with doc comment.',
        '',
        '',
        '.. py:type:: Pep695AliasOfAlias',
        '   :module: target.pep695',
        '   :canonical: ~target.pep695.Pep695AliasC',
        '',
        '   This is PEP695 type alias of PEP695 alias.',
        '',
        '',
        # Undocumented alias should not inherit any documentation
        '.. py:type:: Pep695AliasUndocumented',
        '   :module: target.pep695',
        '   :canonical: ~target.pep695.Foo',
        '',
        '',
        '.. py:type:: Pep695AliasUnion',
        '   :module: target.pep695',
        '   :canonical: str | int',
        '',
        '   This is PEP695 type alias for union.',
        '',
        '',
        '.. py:type:: TypeAliasTypeExplicit',
        '   :module: target.pep695',
        '   :canonical: ~target.pep695.Foo',
        '',
        '   This is an explicitly constructed typing.TypeAlias.',
        '',
        '',
        '.. py:type:: TypeAliasTypeExtension',
        '   :module: target.pep695',
        '   :canonical: ~target.pep695.Foo',
        '',
        '   This is an explicitly constructed typing_extensions.TypeAlias.',
        '',
        '',
        '.. py:function:: buffer_len(data: buffer_like) -> int',
        '   :module: target.pep695',
        '',
        '   Return length of a buffer-like object.',
        '',
        '   Tests Union type alias cross-reference resolution.',
        '',
        '',
        '.. py:data:: buffer_like',
        '   :module: target.pep695',
        '   :value: bytes | bytearray | memoryview',
        '',
        '   Some buffer-like object',
        '',
        '',
        '.. py:data:: pathlike',
        '   :module: target.pep695',
        f'   :value: str | {pathlib.Path.__module__}.Path',
        '',
        '   Any type of path',
        '',
        '',
        '.. py:function:: process_error(handler: Handler, other: ~target.pep695.HandlerTypeAliasType) -> str',
        '   :module: target.pep695',
        '',
        '   Process an error with a custom handler type.',
        '',
        '   Tests generic type alias cross-reference resolution.',
        '',
        '',
        '.. py:function:: read_file(path: pathlike) -> bytes',
        '   :module: target.pep695',
        '',
        '   Read a file and return its contents.',
        '',
        '   Tests Union type alias cross-reference resolution.',
        '',
        '',
        '.. py:function:: ret_pep695(a: ~target.pep695.Pep695Alias) -> ~target.pep695.Pep695Alias',
        '   :module: target.pep695',
        '',
        '   This fn accepts and returns PEP695 alias.',
        '',
    ]


def test_autodoc_TypeVar() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.typevar', options=options)
    assert actual == [
        '',
        '.. py:module:: target.typevar',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.typevar',
        '',
        '',
        '   .. py:class:: Class.T1',
        '      :module: target.typevar',
        '',
        '      T1',
        '',
        "      alias of TypeVar('T1')",
        '',
        '',
        '   .. py:class:: Class.T6',
        '      :module: target.typevar',
        '',
        '      T6',
        '',
        '      alias of :py:class:`~datetime.date`',
        '',
        '',
        '.. py:class:: T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
        '',
        '.. py:class:: T3',
        '   :module: target.typevar',
        '',
        '   T3',
        '',
        "   alias of TypeVar('T3', int, str)",
        '',
        '',
        '.. py:class:: T4',
        '   :module: target.typevar',
        '',
        '   T4',
        '',
        "   alias of TypeVar('T4', covariant=True)",
        '',
        '',
        '.. py:class:: T5',
        '   :module: target.typevar',
        '',
        '   T5',
        '',
        "   alias of TypeVar('T5', contravariant=True)",
        '',
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
        '',
        '.. py:class:: T7',
        '   :module: target.typevar',
        '',
        '   T7',
        '',
        "   alias of TypeVar('T7', bound=\\ :py:class:`int`)",
        '',
    ]


def test_autodoc_Annotated() -> None:
    options = {
        'members': None,
        'member-order': 'bysource',
    }
    actual = do_autodoc('module', 'target.annotated', options=options)
    assert actual == [
        '',
        '.. py:module:: target.annotated',
        '',
        '',
        '.. py:class:: FuncValidator(func: function)',
        '   :module: target.annotated',
        '',
        '',
        '.. py:class:: MaxLen(max_length: int, whitelisted_words: list[str])',
        '   :module: target.annotated',
        '',
        '',
        '.. py:data:: ValidatedString',
        '   :module: target.annotated',
        '',
        '   Type alias for a validated string.',
        '',
        '   alias of :py:class:`~typing.Annotated`\\ [:py:class:`str`, '
        ':py:class:`~target.annotated.FuncValidator`\\ (func=\\ :py:class:`~target.annotated.validate`)]',
        '',
        '',
        ".. py:function:: hello(name: ~typing.Annotated[str, 'attribute']) -> None",
        '   :module: target.annotated',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: AnnotatedAttributes()',
        '   :module: target.annotated',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.name',
        '      :module: target.annotated',
        "      :type: ~typing.Annotated[str, 'attribute']",
        '',
        '      Docstring about the ``name`` attribute.',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.max_len',
        '      :module: target.annotated',
        "      :type: list[~typing.Annotated[str, ~target.annotated.MaxLen(max_length=10, whitelisted_words=['word_one', 'word_two'])]]",
        '',
        '      Docstring about the ``max_len`` attribute.',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.validated',
        '      :module: target.annotated',
        '      :type: ~typing.Annotated[str, ~target.annotated.FuncValidator(func=~target.annotated.validate)]',
        '',
        '      Docstring about the ``validated`` attribute.',
        '',
    ]


def test_autodoc_TYPE_CHECKING() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.TYPE_CHECKING', options=options)
    assert actual == [
        '',
        '.. py:module:: target.TYPE_CHECKING',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.TYPE_CHECKING',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.TYPE_CHECKING',
        '      :type: ~io.StringIO',
        '',
        '',
        '.. py:function:: spam(ham: ~collections.abc.Iterable[str]) -> tuple[~gettext.NullTranslations, bool]',
        '   :module: target.TYPE_CHECKING',
        '',
    ]


def test_autodoc_TYPE_CHECKING_circular_import() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'circular_import', options=options)
    assert actual == [
        '',
        '.. py:module:: circular_import',
        '',
    ]
    assert sys.modules['circular_import'].a is sys.modules['circular_import.a']


def test_singledispatch() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.singledispatch', options=options)
    assert actual == [
        '',
        '.. py:module:: target.singledispatch',
        '',
        '',
        '.. py:function:: func(arg, kwarg=None)',
        '                 func(arg: float, kwarg=None)',
        '                 func(arg: int, kwarg=None)',
        '                 func(arg: str, kwarg=None)',
        '                 func(arg: dict, kwarg=None)',
        '   :module: target.singledispatch',
        '',
        '   A function for general use.',
        '',
    ]


def test_singledispatchmethod() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.singledispatchmethod', options=options)
    assert actual == [
        '',
        '.. py:module:: target.singledispatchmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.meth(arg, kwarg=None)',
        '                  Foo.meth(arg: float, kwarg=None)',
        '                  Foo.meth(arg: int, kwarg=None)',
        '                  Foo.meth(arg: str, kwarg=None)',
        '                  Foo.meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod',
        '',
        '      A method for general use.',
        '',
    ]


def test_singledispatchmethod_automethod() -> None:
    actual = do_autodoc('method', 'target.singledispatchmethod.Foo.meth')
    assert actual == [
        '',
        '.. py:method:: Foo.meth(arg, kwarg=None)',
        '               Foo.meth(arg: float, kwarg=None)',
        '               Foo.meth(arg: int, kwarg=None)',
        '               Foo.meth(arg: str, kwarg=None)',
        '               Foo.meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod',
        '',
        '   A method for general use.',
        '',
    ]


def test_singledispatchmethod_classmethod() -> None:
    options = {'members': None}
    actual = do_autodoc(
        'module', 'target.singledispatchmethod_classmethod', options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.singledispatchmethod_classmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod_classmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.class_meth(arg, kwarg=None)',
        '                  Foo.class_meth(arg: float, kwarg=None)',
        '                  Foo.class_meth(arg: int, kwarg=None)',
        '                  Foo.class_meth(arg: str, kwarg=None)',
        '                  Foo.class_meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod_classmethod',
        '      :classmethod:',
        '',
        '      A class method for general use.',
        '',
    ]


def test_singledispatchmethod_classmethod_automethod() -> None:
    actual = do_autodoc(
        'method', 'target.singledispatchmethod_classmethod.Foo.class_meth'
    )
    assert actual == [
        '',
        '.. py:method:: Foo.class_meth(arg, kwarg=None)',
        '               Foo.class_meth(arg: float, kwarg=None)',
        '               Foo.class_meth(arg: int, kwarg=None)',
        '               Foo.class_meth(arg: str, kwarg=None)',
        '               Foo.class_meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod_classmethod',
        '   :classmethod:',
        '',
        '   A class method for general use.',
        '',
    ]


@pytest.mark.skipif(
    sys.version_info[:2] >= (3, 13),
    reason='Cython does not support Python 3.13 yet.',
)
@pytest.mark.skipif(pyximport is None, reason='cython is not installed')
def test_cython() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.cython', options=options)
    assert actual == [
        '',
        '.. py:module:: target.cython',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.cython',
        '',
        '   Docstring.',
        '',
        '',
        '   .. py:method:: Class.meth(name: str, age: int = 0) -> None',
        '      :module: target.cython',
        '',
        '      Docstring.',
        '',
        '',
        '.. py:function:: foo(x: int, *args, y: str, **kwargs)',
        '   :module: target.cython',
        '',
        '   Docstring.',
        '',
    ]


def test_final() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.final', options=options)
    assert actual == [
        '',
        '.. py:module:: target.final',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.final',
        '   :final:',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Class.meth1()',
        '      :module: target.final',
        '      :final:',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Class.meth2()',
        '      :module: target.final',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Class.meth3()',
        '      :module: target.final',
        '      :final:',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Class.meth4()',
        '      :module: target.final',
        '      :final:',
        '',
        '      docstring',
        '',
    ]


def test_overload() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.overload', options=options)
    assert actual == [
        '',
        '.. py:module:: target.overload',
        '',
        '',
        '.. py:class:: Bar(x: int, y: int)',
        '              Bar(x: str, y: str)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Baz(x: int, y: int)',
        '              Baz(x: str, y: str)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo(x: int, y: int)',
        '              Foo(x: str, y: str)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math()',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Math.sum(x: int, y: int = 0) -> int',
        '                  Math.sum(x: float, y: float = 0.0) -> float',
        '                  Math.sum(x: str, y: str = None) -> str',
        '      :module: target.overload',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: sum(x: int, y: int = 0) -> int',
        '                 sum(x: float, y: float = 0.0) -> float',
        '                 sum(x: str, y: str = None) -> str',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
    ]


def test_overload2() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.overload2', options=options)
    assert actual == [
        '',
        '.. py:module:: target.overload2',
        '',
        '',
        '.. py:class:: Baz(x: int, y: int)',
        '              Baz(x: str, y: str)',
        '   :module: target.overload2',
        '',
    ]


def test_overload3() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.overload3', options=options)
    assert actual == [
        '',
        '.. py:module:: target.overload3',
        '',
        '',
        '.. py:function:: test(x: int) -> int',
        '                 test(x: list[int]) -> list[int]',
        '                 test(x: str) -> str',
        '                 test(x: float) -> float',
        '   :module: target.overload3',
        '',
        '   Documentation.',
        '',
    ]


def test_pymodule_for_ModuleLevelDocumenter() -> None:
    ref_context: dict[str, Any] = {'py:module': 'target.classes'}
    actual = do_autodoc('class', 'Foo', ref_context=ref_context)
    assert actual == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.classes',
        '',
    ]


def test_pymodule_for_ClassLevelDocumenter() -> None:
    ref_context: dict[str, Any] = {'py:module': 'target.methods'}
    actual = do_autodoc('method', 'Base.meth', ref_context=ref_context)
    assert actual == [
        '',
        '.. py:method:: Base.meth()',
        '   :module: target.methods',
        '',
    ]


def test_pyclass_for_ClassLevelDocumenter() -> None:
    ref_context: dict[str, Any] = {'py:module': 'target.methods', 'py:class': 'Base'}
    actual = do_autodoc('method', 'meth', ref_context=ref_context)
    assert actual == [
        '',
        '.. py:method:: Base.meth()',
        '   :module: target.methods',
        '',
    ]


def test_autodoc(caplog: pytest.LogCaptureFixture) -> None:
    # work around sphinx.util.logging.setup()
    logger = logging.getLogger('sphinx')
    logger.handlers[:] = [caplog.handler]
    caplog.set_level(logging.WARNING)

    config = _AutodocConfig(autodoc_mock_imports=['dummy'])
    options = {'members': None}
    actual = do_autodoc(
        'module', 'autodoc_dummy_module', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: autodoc_dummy_module',
        '',
        '',
        '.. py:function:: test()',
        '   :module: autodoc_dummy_module',
        '',
        '   Dummy function using dummy.*',
        '',
    ]

    # See: https://github.com/sphinx-doc/sphinx/issues/2437
    do_autodoc('module', 'bug2437.autodoc_dummy_foo', options=options)
    actual = do_autodoc('module', 'autodoc_dummy_bar', options=options)
    assert actual == [
        '',
        '.. py:module:: autodoc_dummy_bar',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: autodoc_dummy_bar',
        '',
        '   Dummy class Bar with alias.',
        '',
        '',
        '   .. py:attribute:: Bar.my_name',
        '      :module: autodoc_dummy_bar',
        '',
        '      alias of :py:class:`~bug2437.autodoc_dummy_foo.Foo`',
    ]

    assert not caplog.records


def test_name_conflict() -> None:
    actual = do_autodoc('class', 'target.name_conflict.foo')
    assert actual == [
        '',
        '.. py:class:: foo()',
        '   :module: target.name_conflict',
        '',
        '   docstring of target.name_conflict::foo.',
        '',
    ]

    actual = do_autodoc('class', 'target.name_conflict.foo.bar')
    assert actual == [
        '',
        '.. py:class:: bar()',
        '   :module: target.name_conflict.foo',
        '',
        '   docstring of target.name_conflict.foo::bar.',
        '',
    ]


def test_name_mangling() -> None:
    options = {
        'members': None,
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc('module', 'target.name_mangling', options=options)
    assert actual == [
        '',
        '.. py:module:: target.name_mangling',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.name_mangling',
        '',
        '',
        '   .. py:attribute:: Bar._Baz__email',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '      a member having mangled-like name',
        '',
        '',
        '   .. py:attribute:: Bar.__address',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.name_mangling',
        '',
        '',
        '   .. py:attribute:: Foo.__age',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '',
        '   .. py:attribute:: Foo.__name',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '      name of Foo',
        '',
    ]


def test_type_union_operator() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.pep604', options=options)
    assert actual == [
        '',
        '.. py:module:: target.pep604',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.pep604',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr',
        '      :module: target.pep604',
        '      :type: int | str',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Foo.meth(x: int | str, y: int | str) -> int | str',
        '      :module: target.pep604',
        '',
        '      docstring',
        '',
        '',
        '.. py:data:: attr',
        '   :module: target.pep604',
        '   :type: int | str',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: int | str, y: int | str) -> int | str',
        '   :module: target.pep604',
        '',
        '   docstring',
        '',
    ]


def test_hide_value() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.hide_value', options=options)
    assert actual == [
        '',
        '.. py:module:: target.hide_value',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.SENTINEL1',
        '      :module: target.hide_value',
        '',
        '      docstring',
        '',
        '      :meta hide-value:',
        '',
        '',
        '   .. py:attribute:: Foo.SENTINEL2',
        '      :module: target.hide_value',
        '',
        '      :meta hide-value:',
        '',
        '',
        '.. py:data:: SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
        '',
        '.. py:data:: SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]


def test_canonical() -> None:
    options = {
        'members': None,
        'imported-members': None,
    }
    actual = do_autodoc('module', 'target.canonical', options=options)
    assert actual == [
        '',
        '.. py:module:: target.canonical',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.canonical',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.canonical',
        '   :canonical: target.canonical.original.Foo',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.meth()',
        '      :module: target.canonical',
        '',
        '      docstring',
        '',
    ]


def bounded_typevar_rst(name, bound):
    return [
        '',
        f'.. py:class:: {name}',
        '   :module: target.literal',
        '',
        '   docstring',
        '',
        f'   alias of TypeVar({name!r}, bound={bound})',
        '',
    ]


def function_rst(name, sig):
    return [
        '',
        f'.. py:function:: {name}({sig})',
        '   :module: target.literal',
        '',
        '   docstring',
        '',
    ]


def test_literal_render() -> None:
    config = _AutodocConfig(autodoc_typehints_format='short')

    # autodoc_typehints_format can take 'short' or 'fully-qualified' values
    # and this will be interpreted as 'smart' or 'fully-qualified-except-typing' by restify()
    # and 'smart' or 'fully-qualified' by stringify_annotation().

    options = {
        'members': None,
        'exclude-members': 'MyEnum',
    }
    actual = do_autodoc('module', 'target.literal', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`~target.literal.MyEnum.a`, '
            r':py:attr:`~target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: ~typing.Literal[1234, 'abcd']"),
        *function_rst('foo', 'x: ~typing.Literal[MyEnum.a, MyEnum.b]'),
    ]

    # restify() assumes that 'fully-qualified' is 'fully-qualified-except-typing'
    # because it is more likely that a user wants to suppress 'typing.*'
    config = _AutodocConfig(autodoc_typehints_format='fully-qualified')
    actual = do_autodoc('module', 'target.literal', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`target.literal.MyEnum.a`, '
            r':py:attr:`target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: typing.Literal[1234, 'abcd']"),
        *function_rst(
            'foo',
            'x: typing.Literal[target.literal.MyEnum.a, target.literal.MyEnum.b]',
        ),
    ]


def test_literal_render_pep604() -> None:
    config = _AutodocConfig(
        python_display_short_literal_types=True,
        autodoc_typehints_format='short',
    )
    options = {
        'members': None,
        'exclude-members': 'MyEnum',
    }
    actual = do_autodoc('module', 'target.literal', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`~target.literal.MyEnum.a`, '
            r':py:attr:`~target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: 1234 | 'abcd'"),
        *function_rst('foo', 'x: MyEnum.a | MyEnum.b'),
    ]

    # restify() assumes that 'fully-qualified' is 'fully-qualified-except-typing'
    # because it is more likely that a user wants to suppress 'typing.*'
    config = _AutodocConfig(
        python_display_short_literal_types=True,
        autodoc_typehints_format='fully-qualified',
    )
    actual = do_autodoc('module', 'target.literal', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`target.literal.MyEnum.a`, '
            r':py:attr:`target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: 1234 | 'abcd'"),
        *function_rst('foo', 'x: target.literal.MyEnum.a | target.literal.MyEnum.b'),
    ]


def test_no_index_entry() -> None:
    # modules can use no-index-entry
    options = {'no-index-entry': None}
    actual = do_autodoc('module', 'target.module', options=options)
    assert '   :no-index-entry:' in actual

    # classes can use no-index-entry
    actual = do_autodoc('class', 'target.classes.Foo', options=options)
    assert '   :no-index-entry:' in actual

    # functions can use no-index-entry
    actual = do_autodoc('function', 'target.functions.func', options=options)
    assert '   :no-index-entry:' in actual

    # modules respect no-index-entry in autodoc_default_options
    config = _AutodocConfig(autodoc_default_options={'no-index-entry': True})
    actual = do_autodoc('module', 'target.module', config=config)
    assert '   :no-index-entry:' in actual

    # classes respect config-level no-index-entry
    actual = do_autodoc('class', 'target.classes.Foo', config=config)
    assert '   :no-index-entry:' in actual

    # functions respect config-level no-index-entry
    actual = do_autodoc('function', 'target.functions.func', config=config)
    assert '   :no-index-entry:' in actual
