"""Test the autodoc extension.  This mainly tests the signature utilities."""

from __future__ import annotations

from typing import Generic, TypeVar

import pytest

from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
from sphinx.ext.autodoc._dynamic._docstrings import _get_docstring_lines
from sphinx.ext.autodoc._dynamic._signatures import _format_signatures
from sphinx.ext.autodoc._property_types import (
    _ClassDefProperties,
    _FunctionDefProperties,
)
from sphinx.ext.autodoc._shared import _AutodocConfig
from sphinx.util.inspect import safe_getattr

from tests.test_ext_autodoc.autodoc_util import FakeEvents

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx
    from sphinx.events import EventManager
    from sphinx.ext.autodoc._property_types import _AutodocObjType

processed_signatures = []


def format_sig(
    obj_type: _AutodocObjType,
    name: str,
    obj: Any,
    *,
    config: _AutodocConfig | None = None,
    events: EventManager | None = None,
    args: str | None = None,
    retann: str | None = None,
) -> tuple[str, str] | tuple[()]:
    if config is None:
        config = _AutodocConfig()
    if events is None:
        events = FakeEvents()
    options = _AutoDocumenterOptions()

    parent = object  # dummy
    props = _ClassDefProperties(
        obj_type=obj_type,  # type: ignore[arg-type]
        module_name='',
        parts=(name,),
        docstring_lines=(),
        bases=getattr(obj, '__bases__', None),
        _obj=obj,
        _obj___module__=getattr(obj, '__module__', None),
        _obj___qualname__=getattr(obj, '__qualname__', None),
        _obj___name__=name,
        _obj_bases=(),
        _obj_is_new_type=False,
        _obj_is_typevar=False,
    )
    docstrings = _get_docstring_lines(
        props,
        class_doc_from=config.autoclass_content,
        get_attr=safe_getattr,
        inherit_docstrings=config.autodoc_inherit_docstrings,
        parent=parent,
        tab_width=8,
    )
    signatures = _format_signatures(
        autodoc_annotations={},
        config=config,
        docstrings=docstrings,
        events=events,
        get_attr=safe_getattr,
        options=options,
        parent=parent,
        props=props,
        args=args,
        retann=retann,
    )
    if not signatures:
        return ()
    assert len(signatures) == 1
    return signatures[0]


def _process_signature(
    _app: Sphinx,
    what: str,
    name: str,
    _obj: Any,
    _options: Any,
    _args: str,
    _retann: str,
) -> tuple[str | None, str | None] | None:
    processed_signatures.append((what, name))
    if name == '.bar':
        return '42', None
    return None


def test_format_module_signatures() -> None:
    # no signatures for modules
    assert format_sig('module', 'test', None) == ()


def test_format_function_signatures() -> None:
    # test for functions
    def f(a, b, c=1, **d):  # type: ignore[no-untyped-def]
        pass

    def g(a='\n'):  # type: ignore[no-untyped-def]
        pass

    assert format_sig('function', 'f', f) == ('(a, b, c=1, **d)', '')
    assert format_sig('function', 'f', f, args='(a, b, c, d)') == ('(a, b, c, d)', '')
    assert format_sig('function', 'g', g) == (r"(a='\n')", '')


@pytest.mark.parametrize(
    ('params', 'expect'),
    [
        ('(a=1)', '(a=1)'),
        ('(a: int=1)', '(a: int = 1)'),  # auto whitespace formatting
        ('(a:list[T]   =[], b=None)', '(a: list[T] = [], b=None)'),  # idem
    ],
)
def test_format_function_signatures_pep695(params: str, expect: str) -> None:
    ns: dict[str, Any] = {}
    exec(f'def f[T]{params}: pass', ns)  # NoQA: S102
    f = ns['f']
    assert format_sig('function', 'f', f) == (expect, '')
    assert format_sig('function', 'f', f, args='(...)') == ('(...)', '')
    assert format_sig('function', 'f', f, args='(...)', retann='...') == (
        '(...)',
        '...',
    )

    exec(f'def f[T]{params} -> list[T]: return []', ns)  # NoQA: S102
    f = ns['f']
    assert format_sig('function', 'f', f) == (expect, 'list[T]')
    assert format_sig('function', 'f', f, args='(...)') == ('(...)', '')
    assert format_sig('function', 'f', f, args='(...)', retann='...') == (
        '(...)',
        '...',
    )

    # TODO(picnixz): add more test cases for PEP-695 classes as well (though
    # complex cases are less likely to appear and are painful to test).


def test_format_class_signatures() -> None:
    # test for classes
    class D:
        pass

    class E:
        def __init__(self):  # type: ignore[no-untyped-def]
            pass

    # an empty init and no init are the same
    for C in (D, E):
        assert format_sig('class', 'D', C) == ('()', '')

    class SomeMeta(type):
        def __call__(cls, a, b=None):  # type: ignore[no-untyped-def]
            return type.__call__(cls, a, b)

    # these three are all equivalent
    class F:
        def __init__(self, a, b=None):  # type: ignore[no-untyped-def]
            pass

    class FNew:
        def __new__(cls, a, b=None):  # type: ignore[no-untyped-def]  # NoQA: ARG004
            return super().__new__(cls)

    class FMeta(metaclass=SomeMeta):
        pass

    # and subclasses should always inherit
    class G(F):
        pass

    class GNew(FNew):
        pass

    class GMeta(FMeta):
        pass

    # subclasses inherit
    assert format_sig('class', 'C', F) == ('(a, b=None)', '')
    assert format_sig('class', 'C', FNew) == ('(a, b=None)', '')
    assert format_sig('class', 'C', FMeta) == ('(a, b=None)', '')
    assert format_sig('class', 'C', G) == ('(a, b=None)', '')
    assert format_sig('class', 'C', GNew) == ('(a, b=None)', '')
    assert format_sig('class', 'C', GMeta) == ('(a, b=None)', '')
    assert format_sig('class', 'C', D, args='(a, b)', retann='X') == ('(a, b)', 'X')


def test_format_class_signatures_text_signature() -> None:
    class ListSubclass(list):  # type: ignore[type-arg]  # NoQA: FURB189
        pass

    # only supported if the python implementation decides to document it
    if getattr(list, '__text_signature__', None) is not None:
        assert format_sig('class', 'C', ListSubclass) == ('(iterable=(), /)', '')
    else:
        assert format_sig('class', 'C', ListSubclass) == ()


def test_format_class_signatures_no_text_signature() -> None:
    class ExceptionSubclass(Exception):
        pass

    # Exception has no __text_signature__ as at Python 3.14
    if getattr(Exception, '__text_signature__', None) is not None:
        pytest.xfail('Exception.__text_signature__ exists!')
    assert format_sig('class', 'C', ExceptionSubclass) == ()


def test_format_class_signatures_init_both() -> None:
    # __init__ have signature at first line of docstring
    config = _AutodocConfig(autoclass_content='both')

    class F2:
        """some docstring for F2."""

        def __init__(self, *args, **kw):  # type: ignore[no-untyped-def]
            """
            __init__(a1, a2, kw1=True, kw2=False)

            some docstring for __init__.
            """  # NoQA: D212

    class G2(F2):
        pass

    assert format_sig('class', 'F2', F2, config=config) == (
        '(a1, a2, kw1=True, kw2=False)',
        '',
    )
    assert format_sig('class', 'G2', G2, config=config) == (
        '(a1, a2, kw1=True, kw2=False)',
        '',
    )


def test_format_method_signatures() -> None:
    # test for methods
    class H:
        def foo1(self, b, *c):  # type: ignore[no-untyped-def]
            pass

        def foo2(b, *c):  # type: ignore[no-untyped-def]  # NoQA: N805
            pass

        def foo3(self, d='\n'):  # type: ignore[no-untyped-def]
            pass

    assert format_sig('method', 'H.foo', H.foo1) == ('(b, *c)', '')
    assert format_sig('method', 'H.foo', H.foo1, args='(a)') == ('(a)', '')
    assert format_sig('method', 'H.foo', H.foo2) == ('(*c)', '')
    assert format_sig('method', 'H.foo', H.foo3) == (r"(d='\n')", '')

    # test bound methods interpreted as functions
    assert format_sig('function', 'foo', H().foo1) == ('(b, *c)', '')
    assert format_sig('function', 'foo', H().foo2) == ('(*c)', '')
    assert format_sig('function', 'foo', H().foo3) == (r"(d='\n')", '')


def test_format_method_signatures_error_handling() -> None:
    # test exception handling (exception is caught and args is '')
    config = _AutodocConfig(autodoc_docstring_signature=False)
    assert format_sig('function', 'int', int, config=config) == ()


def test_format_signatures_event_handler() -> None:
    events = FakeEvents()
    events.connect('autodoc-process-signature', _process_signature)

    class H:
        def foo1(self, b, *c):  # type: ignore[no-untyped-def]
            pass

    # test processing by event handler
    assert format_sig('method', 'bar', H.foo1, events=events) == ('42', '')


def test_format_functools_partial_signatures() -> None:
    # test functions created via functools.partial
    from functools import partial

    curried1 = partial(lambda a, b, c: None, 'A')
    assert format_sig('function', 'curried1', curried1) == ('(b, c)', '')
    curried2 = partial(lambda a, b, c=42: None, 'A')
    assert format_sig('function', 'curried2', curried2) == ('(b, c=42)', '')
    curried3 = partial(lambda a, b, *c: None, 'A')
    assert format_sig('function', 'curried3', curried3) == ('(b, *c)', '')
    curried4 = partial(lambda a, b, c=42, *d, **e: None, 'A')
    assert format_sig('function', 'curried4', curried4) == ('(b, c=42, *d, **e)', '')


def test_autodoc_process_signature_typing_generic() -> None:
    T = TypeVar('T')

    class A(Generic[T]):
        def __init__(self, a, b=None):  # type: ignore[no-untyped-def]
            pass

    # Test that typing.Generic's __new__ method does not mask
    # the class's __init__ signature.
    assert format_sig('class', 'A', A) == ('(a, b=None)', '')


def test_autodoc_process_signature_typehints() -> None:
    captured = []

    def process_signature(*args: Any) -> None:
        captured.append(args)

    events = FakeEvents()
    events.connect('autodoc-process-signature', process_signature)

    def func(x: int, y: int) -> int:  # type: ignore[empty-body]
        pass

    props = _FunctionDefProperties(
        obj_type='function',
        module_name='',
        parts=('func',),
        docstring_lines=(),
        _obj=func,
        _obj___module__=None,
        _obj___qualname__=None,
        _obj___name__=None,
        properties=frozenset(),
    )

    options = _AutoDocumenterOptions()
    _format_signatures(
        autodoc_annotations={},
        config=_AutodocConfig(),
        docstrings=None,
        events=events,
        get_attr=safe_getattr,
        options=options,
        parent=None,
        props=props,
    )

    app = events._app
    assert captured == [
        (app, 'function', '.func', func, options, '(x: int, y: int)', 'int')
    ]
