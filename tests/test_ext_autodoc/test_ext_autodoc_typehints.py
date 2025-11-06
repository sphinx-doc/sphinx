"""Test the autodoc extension."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from sphinx.ext.autodoc._shared import _AutodocConfig
from sphinx.testing import restructuredtext

from tests.test_ext_autodoc.autodoc_util import do_autodoc

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


@contextmanager
def overwrite_file(path: Path, content: str) -> Iterator[None]:
    current_content = path.read_bytes() if path.exists() else None
    try:
        path.write_text(content, encoding='utf-8')
        yield
    finally:
        if current_content is not None:
            path.write_bytes(current_content)
        else:
            path.unlink()


def test_autodoc_typehints_signature() -> None:
    config = _AutodocConfig(autodoc_typehints='signature')

    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.typehints', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '   :type: int',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :type: int',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        '   :type: ~pathlib.PurePosixPath',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s: str, o: ~typing.Any = None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :type: int',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        '      :type: ~pathlib.PurePosixPath',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a: str, b: int) -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing() -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '      :type: ~pathlib.PurePosixPath',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '.. py:class:: NewAnnotation(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`~pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1: str, arg2: List[int], arg3: Tuple[int, '
        'Union[str, Unknown]] = None, *args: str, **kwargs: str) -> None',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a: str, b: Optional[str] = None) -> str',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x: tuple[int, int | str]) -> tuple[int, int]',
        '   :module: target.typehints',
        '',
    ]


def test_autodoc_typehints_none() -> None:
    config = _AutodocConfig(autodoc_typehints='none')

    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.typehints', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s, o=None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a, b)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing()',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '',
        '',
        '.. py:class:: NewAnnotation(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`~pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1, arg2, arg3=None, *args, **kwargs)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a, b=None)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x)',
        '   :module: target.typehints',
        '',
    ]


def test_autodoc_typehints_none_for_overload() -> None:
    config = _AutodocConfig(autodoc_typehints='none')

    options = {'members': None}
    actual = do_autodoc('module', 'target.overload', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.overload',
        '',
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Baz(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo(x, y)',
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
        '   .. py:method:: Math.sum(x, y=None)',
        '      :module: target.overload',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: sum(x, y=None)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('text', testroot='ext-autodoc', freshenv=True)
def test_autodoc_typehints_description(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'

    app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    expect = '\n'.join((  # NoQA: FLY002
        'target.typehints.incr(a, b=1)',
        '',
        '   Parameters:',
        '      * **a** (*int*)',
        '',
        '      * **b** (*int*)',
        '',
        '   Return type:',
        '      int',
        '',
    ))
    assert expect in context
    expect = '\n'.join((  # NoQA: FLY002
        'target.typehints.tuple_args(x)',
        '',
        '   Parameters:',
        '      **x** (*tuple**[**int**, **int** | **str**]*)',
        '',
        '   Return type:',
        '      tuple[int, int]',
        '',
    ))
    assert expect in context

    # Overloads still get displayed in the signature
    expect = '\n'.join((  # NoQA: FLY002
        'target.overload.sum(x: int, y: int = 0) -> int',
        'target.overload.sum(x: float, y: float = 0.0) -> float',
        'target.overload.sum(x: str, y: str = None) -> str',
        '',
        '   docstring',
        '',
    ))
    assert expect in context


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_no_undoc(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'
    app.config.autodoc_typehints_description_target = 'documented'

    # No :type: or :rtype: will be injected for `incr`, which does not have
    # a description for its parameters or its return. `tuple_args` does
    # describe them, so :type: and :rtype: will be added.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.decr\n'
        '\n'
        '   :returns: decremented number\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '   :param x: arg\n'
        '   :return: another tuple\n',
    ):
        app.build()
    # Restore the original content of the file
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    expect = '\n'.join((  # NoQA: FLY002
        'target.typehints.incr(a, b=1)',
        '',
        'target.typehints.decr(a, b=1)',
        '',
        '   Returns:',
        '      decremented number',
        '',
        '   Return type:',
        '      int',
        '',
        'target.typehints.tuple_args(x)',
        '',
        '   Parameters:',
        '      **x** (*tuple**[**int**, **int** | **str**]*) -- arg',
        '',
        '   Returns:',
        '      another tuple',
        '',
        '   Return type:',
        '      tuple[int, int]',
        '',
    ))
    assert expect in context


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_no_undoc_doc_rtype(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'
    app.config.autodoc_typehints_description_target = 'documented_params'

    # No :type: will be injected for `incr`, which does not have a description
    # for its parameters or its return, just :rtype: will be injected due to
    # autodoc_typehints_description_target. `tuple_args` does describe both, so
    # :type: and :rtype: will be added. `nothing` has no parameters but a return
    # type of None, which will be added.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.decr\n'
        '\n'
        '   :returns: decremented number\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '   :param x: arg\n'
        '   :return: another tuple\n'
        '\n'
        '.. autofunction:: target.typehints.Math.nothing\n'
        '\n'
        '.. autofunction:: target.typehints.Math.horse\n'
        '\n'
        '   :return: nothing\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'target.typehints.incr(a, b=1)\n'
        '\n'
        '   Return type:\n'
        '      int\n'
        '\n'
        'target.typehints.decr(a, b=1)\n'
        '\n'
        '   Returns:\n'
        '      decremented number\n'
        '\n'
        '   Return type:\n'
        '      int\n'
        '\n'
        'target.typehints.tuple_args(x)\n'
        '\n'
        '   Parameters:\n'
        '      **x** (*tuple**[**int**, **int** | **str**]*) -- arg\n'
        '\n'
        '   Returns:\n'
        '      another tuple\n'
        '\n'
        '   Return type:\n'
        '      tuple[int, int]\n'
        '\n'
        'target.typehints.Math.nothing(self)\n'
        '\n'
        'target.typehints.Math.horse(self, a, b)\n'
        '\n'
        '   Returns:\n'
        '      nothing\n'
        '\n'
        '   Return type:\n'
        '      None\n'
    )


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_with_documented_init(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'

    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*int*)\n'
        '\n'
        '      * **args** (*int*)\n'
        '\n'
        '      * **kwargs** (*int*)\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
        '\n'
        '      Return type:\n'
        '         None\n'
    )


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_with_documented_init_no_undoc(
    app: SphinxTestApp,
) -> None:
    app.config.autodoc_typehints = 'description'
    app.config.autodoc_typehints_description_target = 'documented'

    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
    )


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_with_documented_init_no_undoc_doc_rtype(
    app: SphinxTestApp,
) -> None:
    app.config.autodoc_typehints = 'description'
    app.config.autodoc_typehints_description_target = 'documented_params'

    # see test_autodoc_typehints_description_with_documented_init_no_undoc
    # returnvalue_and_documented_params should not change class or method
    # docstring.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
    )


@pytest.mark.sphinx('text', testroot='ext-autodoc')
def test_autodoc_typehints_description_for_invalid_node(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'

    text = '.. py:function:: hello; world'
    restructuredtext.parse(app, text)  # raises no error


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_both(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'both'

    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '.. autofunction:: target.overload.sum\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    expect = '\n'.join((  # NoQA: FLY002
        'target.typehints.incr(a: int, b: int = 1) -> int',
        '',
        '   Parameters:',
        '      * **a** (*int*)',
        '',
        '      * **b** (*int*)',
        '',
        '   Return type:',
        '      int',
        '',
    ))
    assert expect in context
    expect = '\n'.join((  # NoQA: FLY002
        'target.typehints.tuple_args(x: tuple[int, int | str]) -> tuple[int, int]',
        '',
        '   Parameters:',
        '      **x** (*tuple**[**int**, **int** | **str**]*)',
        '',
        '   Return type:',
        '      tuple[int, int]',
        '',
    ))
    assert expect in context

    # Overloads still get displayed in the signature
    expect = '\n'.join((  # NoQA: FLY002
        'target.overload.sum(x: int, y: int = 0) -> int',
        'target.overload.sum(x: float, y: float = 0.0) -> float',
        'target.overload.sum(x: str, y: str = None) -> str',
        '',
        '   docstring',
        '',
    ))
    assert expect in context


@pytest.mark.sphinx('text', testroot='ext-autodoc', copy_test_root=True)
def test_autodoc_typehints_description_and_type_aliases(app: SphinxTestApp) -> None:
    app.config.autodoc_typehints = 'description'
    app.config.autodoc_type_aliases = {'myint': 'myint'}

    with overwrite_file(
        app.srcdir / 'autodoc_type_aliases.rst',
        '.. autofunction:: target.autodoc_type_aliases.sum',
    ):
        app.build()
    context = (app.outdir / 'autodoc_type_aliases.txt').read_text(encoding='utf8')
    assert context == (
        'target.autodoc_type_aliases.sum(x, y)\n'
        '\n'
        '   docstring\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*myint*)\n'
        '\n'
        '      * **y** (*myint*)\n'
        '\n'
        '   Return type:\n'
        '      myint\n'
    )


def test_autodoc_typehints_format_fully_qualified() -> None:
    config = _AutodocConfig(autodoc_typehints_format='fully-qualified')

    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.typehints', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '   :type: int',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :type: int',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        '   :type: pathlib.PurePosixPath',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s: str, o: typing.Any = None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :type: int',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        '      :type: pathlib.PurePosixPath',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a: str, b: int) -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing() -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '      :type: pathlib.PurePosixPath',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '.. py:class:: NewAnnotation(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1: str, arg2: List[int], arg3: Tuple[int, '
        'Union[str, Unknown]] = None, *args: str, **kwargs: str) -> None',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a: str, b: Optional[str] = None) -> str',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x: tuple[int, int | str]) -> tuple[int, int]',
        '   :module: target.typehints',
        '',
    ]


def test_autodoc_typehints_format_fully_qualified_for_class_alias() -> None:
    config = _AutodocConfig(autodoc_typehints_format='fully-qualified')

    actual = do_autodoc('class', 'target.classes.Alias', config=config)
    assert actual == [
        '',
        '.. py:attribute:: Alias',
        '   :module: target.classes',
        '',
        '   alias of :py:class:`target.classes.Foo`',
    ]


def test_autodoc_typehints_format_fully_qualified_for_generic_alias() -> None:
    config = _AutodocConfig(autodoc_typehints_format='fully-qualified')

    actual = do_autodoc('data', 'target.genericalias.L', config=config)
    assert actual == [
        '',
        '.. py:data:: L',
        '   :module: target.genericalias',
        '',
        '   A list of Class',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`target.genericalias.Class`]',
        '',
    ]


def test_autodoc_typehints_format_fully_qualified_for_newtype_alias() -> None:
    config = _AutodocConfig(autodoc_typehints_format='fully-qualified')

    actual = do_autodoc('class', 'target.typevar.T6', config=config)
    assert actual == [
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`datetime.date`',
        '',
    ]
