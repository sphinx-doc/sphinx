"""Internal utility functions for interacting with pytest."""

from __future__ import annotations

__all__ = ()

import os
import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Literal, TypeVar, overload

import pytest
from _pytest.nodes import Node as PytestNode
from _pytest.nodes import get_fslocation_from_item

from sphinx.testing._internal.warnings import MarkWarning, NodeWarning, SphinxTestingWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Iterator
    from typing import Any, ClassVar, Final

    T = TypeVar('T')
    DT = TypeVar('DT')
    NodeType = TypeVar('NodeType', bound='PytestNode')


class TestRootFinder:
    """Object responsible for finding the testroot files in *rootdir*.

    For instance::

        finder = TestRootFinder('/foo/bar', 'test-', 'default')

    describes a testroot root directory at ``/foo/bar/``. The name of the
    directories in ``/foo/bar/`` consist of a *prefix* and an *ID* (in this
    case, the prefix is ``test-`` and the default *ID* is ``default``).

    >>> finder = TestRootFinder('/foo/bar', 'test-', 'default')
    >>> finder.find()
    '/foo/bar/test-default'
    >>> finder.find('abc')
    '/foo/bar/test-abc'
    """

    # This is needed to avoid this class being considered as a test by pytest.
    __test__: ClassVar[Literal[False]] = False

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        prefix: str | None = None,
        default: str | None = None,
    ) -> None:
        """Construct a :class:`TestRootFinder` object.

        :param path: Optional non-empty root path containing the testroots.
        :param prefix: Optional prefix to prepend to a testroot ID.
        :param default: Optional non-empty string for a default testroot ID.
        :raise ValueError: Empty strings are given instead of ``None``.
        """
        for arg, val in (('path', path), ('default', default)):
            if not val and val is not None:
                msg = 'expecting a non-empty string or None for %r'
                raise ValueError(msg % arg)

        self.path: str | None = os.fsdecode(path) if path else None

        assert prefix is None or isinstance(prefix, str)
        self.prefix: str = prefix or ''

        assert default is None or isinstance(default, str)
        self.default: str | None = default

    def find(self, testroot_id: str | None = None) -> str | None:
        """Find the sources directory for a named or the default testroot.

        :param testroot_id: A testroot ID (non-prefixed string).
        :return: The path to the testroot directory, if any.
        """
        if not (path := self.path):
            return None

        if not (testroot_id := testroot_id or self.default):
            return None

        # upon construction, we ensured that 'prefix' is empty if None
        return os.path.join(path, f'{self.prefix}{testroot_id}')


ScopeName = Literal['session', 'package', 'module', 'class', 'function']
"""Pytest scopes."""

_NODE_TYPE_BY_SCOPE: Final[dict[ScopeName, type[PytestNode]]] = {
    'session': pytest.Session,
    'package': pytest.Package,
    'module': pytest.Module,
    'class': pytest.Class,
    'function': pytest.Function,
}


# fmt: off
@overload
def get_node_type_by_scope(scope: Literal['session']) -> type[pytest.Session]: ...  # NoQA: E501, E704
@overload
def get_node_type_by_scope(scope: Literal['package']) -> type[pytest.Package]: ...  # NoQA: E501, E704
@overload
def get_node_type_by_scope(scope: Literal['module']) -> type[pytest.Module]: ...  # NoQA: E704
@overload
def get_node_type_by_scope(scope: Literal['class']) -> type[pytest.Class]: ...  # NoQA: E704
@overload
def get_node_type_by_scope(scope: Literal['function']) -> type[pytest.Function]: ...  # NoQA: E501, E704
# fmt: on
def get_node_type_by_scope(scope: ScopeName) -> type[PytestNode]:  # NoQA: E302
    """Get a pytest node type by its scope.

    :param scope: The scope name.
    :return: The corresponding pytest node type.
    """
    return _NODE_TYPE_BY_SCOPE[scope]


# fmt: off
@overload
def find_context(node: PytestNode, cond: Literal['session'], /, *, include_self: bool = ...) -> pytest.Session: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['package'], /, *, include_self: bool = ...) -> pytest.Package: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['module'], /, *, include_self: bool = ...) -> pytest.Module: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['class'], /, *, include_self: bool = ...) -> pytest.Class: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['function'], /, *, include_self: bool = ...) -> pytest.Function: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: ScopeName, /, *, include_self: bool = ...) -> PytestNode: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['session'], default: DT, /, *, include_self: bool = ...) -> pytest.Session | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['package'], default: DT, /, *, include_self: bool = ...) -> pytest.Package | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['module'], default: DT, /, *, include_self: bool = ...) -> pytest.Module | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['class'], default: DT, /, *, include_self: bool = ...) -> pytest.Class | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: Literal['function'], default: DT, /, *, include_self: bool = ...) -> pytest.Function | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: ScopeName, default: DT, /, *, include_self: bool = ...) -> PytestNode | DT: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: type[NodeType], /, *, include_self: bool = ...) -> NodeType: ...  # NoQA: E501, E704
@overload
def find_context(node: PytestNode, cond: type[NodeType], default: DT, /, *, include_self: bool = ...) -> NodeType | DT: ...  # NoQA: E501, E704
# fmt: on
def find_context(  # NoQA: E302
    node: Any,
    cond: ScopeName | type[PytestNode],
    /,
    *default: Any,
    include_self: bool = True,
) -> Any:
    """Get a parent node in the given scope.

    Use this function to have a correct typing of the returned object,
    until ``pytest`` provides a better typing.

    :param node: The node to get an ancestor of.
    :param cond: The ancestor type or scope.
    :param default: A default value.
    :param include_self: Include *node* if possible.
    :return: A node in the ancestor chain (possibly *node*) of desired type.
    """
    if isinstance(cond, str):
        cond = get_node_type_by_scope(cond)

    parent = node.getparent(cond)
    if parent is None or parent is node and not include_self:
        if default:
            return default[0]
        msg = f'no parent of type {cond} for {node}'
        raise AttributeError(msg)
    return parent


TestNodeLocation = tuple[str, int]
"""The location ``(fspath, lineno)`` of a pytest node.

* The *fspath* is relative to :attr:`pytest.Config.rootpath`.
* The line number is a 0-based integer.
"""


def get_node_location(node: PytestNode) -> TestNodeLocation | None:
    """The node location ``(fspath, lineno)``, if any.

    If the path or the line number cannot be deduced, a warning is emitted.

    When deduced, the line number is a 0-based integer.
    """
    path, lineno = get_fslocation_from_item(node)
    if not (path := os.fsdecode(path)) or lineno == -1 or lineno is None:
        msg = f'could not obtain node location for {node!r}'
        warnings.warn_explicit(msg, category=NodeWarning, filename=path, lineno=-1)
        return None
    return path, lineno


def get_mark_parameters(
    node: PytestNode,
    marker: str,
    /,
    *default_args: Any,
    **default_kwargs: Any,
) -> tuple[list[Any], dict[str, Any]]:
    """Get the positional and keyword arguments of node.

    :param node: The pytest node to analyze.
    :param marker: The name of the marker to extract the parameters of.
    :param default_args: Optional default positional arguments.
    :param default_kwargs: Optional default keyword arguments.
    :return: The positional and keyword arguments.

    By convention, arguments are not stacked and are collected in
    the *reverse* order the marker decorators are specified, e.g.::

        @pytest.mark.foo('ignored', 2, a='ignored', b=2)
        @pytest.mark.foo(1, a=1)
        def test(request):
            args, kwargs = get_mark_parameters(request.node, 'foo')
            assert args == [1, 2]
            assert kwargs == {'a': 1, 'b': 2}
    """
    args, kwargs = list(default_args), default_kwargs
    for info in reversed(list(node.iter_markers(marker))):
        args[:len(info.args)] = info.args  # fmt: skip
        kwargs |= info.kwargs
    return args, kwargs


def check_mark_keywords(
    mark: str,
    expect: Collection[str],
    actual: Iterable[str],
    *,
    node: PytestNode | None = None,
    ignore_private: bool = False,
    strict: bool = False,
) -> bool:
    """Check the keyword arguments.

    :param mark: The name of the marker being checked.
    :param expect: The marker expected keyword parameter names.
    :param actual: The keyword arguments to check.
    :param node: Optional node to emit warnings upon invalid arguments.
    :param ignore_private: Ignore keyword arguments with leading underscores.
    :param strict: If true, raises an exception instead of a warning.
    :return: Indicate if the keyword arguments were recognized or not.

    >>> check_mark_keywords('_', ['a', 'b'], {'a': 1, 'b': 2, 'c': 3})
    False
    >>> check_mark_keywords('_', ['a', 'b'], {'a': 1, 'b': 2, '_private': 3},
    ...                     ignore_private=True)
    True
    """
    keys = set(actual).difference(expect)
    extras = sorted(key for key in keys if not (key.startswith('_') and ignore_private))
    if extras and node:
        msg = 'unexpected keyword argument(s): %s' % ', '.join(sorted(extras))
        if strict:
            pytest.fail(format_mark_failure(mark, msg))

        issue_warning(node, MarkWarning(msg, mark))
        return False
    return len(extras) == 0


def check_mark_str_args(mark: str, /, **kwargs: Any) -> None:
    """Check that marker string arguments are either None or non-empty.

    :param mark: The marker name.
    :param kwargs: A mapping of marker argument names and their values.
    :raise pytest.Failed: The validation failed.
    """
    for argname, value in kwargs.items():
        if value and not isinstance(value, str) or not value and value is not None:
            fmt = 'expecting a non-empty string or None for %r, got: %r'
            pytest.fail(format_mark_failure(mark, fmt % (argname, value)))


def stack_pytest_markers(
    marker: pytest.MarkDecorator, /, *markers: pytest.MarkDecorator
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Create a decorator stacking pytest markers."""
    stack = [marker, *markers]
    stack.reverse()

    def wrapper(func: Callable[..., None]) -> Callable[..., None]:
        for marker in stack:
            func = marker(func)
        return func

    return wrapper


@contextmanager
def pytest_not_raises(*exceptions: type[BaseException]) -> Iterator[None]:
    """Context manager asserting that no exception is raised."""
    try:
        yield
    except exceptions as exc:
        pytest.fail(f'DID RAISE {exc.__class__}')


# fmt: off
@overload
def issue_warning(config: pytest.Config, warning: Warning, /) -> None: ...  # NoQA: E704
@overload
def issue_warning(config: pytest.Config, fmt: Any, /, *args: Any, category: type[Warning] | None = ...) -> None: ...  # NoQA: E501, E704
@overload
def issue_warning(request: pytest.FixtureRequest, warning: Warning, /) -> None: ...  # NoQA: E501, E704
@overload
def issue_warning(request: pytest.FixtureRequest, fmt: Any, /, *args: Any, category: type[Warning] | None = ...) -> None: ...  # NoQA: E501, E704
@overload
def issue_warning(node: PytestNode, warning: Warning, /) -> None: ...  # NoQA: E704
@overload
def issue_warning(node: PytestNode, fmt: Any, /, *args: Any, category: type[Warning] | None = ...) -> None: ...  # NoQA: E501, E704
# fmt: on
def issue_warning(  # NoQA: E302
    ctx: Any, fmt: Any, /, *args: Any, category: type[Warning] | None = None
) -> None:
    """Public helper for emitting a warning on a pytest object.

    This is typically useful for debugging when plugins capturing ``print``
    such as ``xdist`` are active. Warnings are (apparently) always printed
    on the console.
    """
    if isinstance(fmt, Warning):
        warning = fmt
    else:
        message = str(fmt)
        if args:  # allow str(fmt) to contain '%s'
            message = message % args
        warning = SphinxTestingWarning(message) if category is None else category(message)

    if isinstance(ctx, pytest.Config):
        ctx.issue_config_time_warning(warning, stacklevel=2)
        return

    node = ctx.node if isinstance(ctx, pytest.FixtureRequest) else ctx
    if not isinstance(node, PytestNode):
        err = f'expecting a session, a fixture request or a pytest node, got {node!r}'
        raise TypeError(err)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', NodeWarning)
        location = get_node_location(node)

    if location is None:
        filename = os.fsdecode(node.path or 'unknown location')
        lineno = -1
    else:
        filename, lineno = location
        lineno = lineno + 1

    warnings.warn_explicit(warning, category=None, filename=filename, lineno=lineno)


def format_mark_failure(mark: str, message: str) -> str:
    return f'pytest.mark.{mark}(): {message}'


###############################################################################
# _pytest.config.Config accessor
###############################################################################


def get_pytest_config(
    subject: pytest.Config | pytest.FixtureRequest | PytestNode, /
) -> pytest.Config:
    """Get the underlying pytest configuration of the *subject*."""
    if isinstance(subject, pytest.Config):
        return subject

    config = getattr(subject, 'config', None)
    if config is None or not isinstance(config, pytest.Config):
        msg = f'no configuration accessor for {type(subject)} objects'
        raise TypeError(msg)
    return config


###############################################################################
# _pytest.tempdir.TempPathFactory accessor
###############################################################################

_DT = TypeVar('_DT')


# fmt: off
@overload
def get_tmp_path_factory(subject: Any, /) -> pytest.TempPathFactory: ...  # NoQA: E704
@overload
def get_tmp_path_factory(subject: Any, default: _DT, /) -> pytest.TempPathFactory | _DT: ...  # NoQA: E501, E704
# fmt: on
def get_tmp_path_factory(subject: Any, /, *default: Any) -> Any:  # NoQA: E302
    """Get the optional underlying path factory of the *subject*."""
    config = get_pytest_config(subject)
    factory = getattr(config, '_tmp_path_factory', None)
    if factory is None:
        if default:
            return default[0]

        msg = f'cannot extract the underlying temporary path factory from {subject!r}'
        raise AttributeError(msg)
    assert isinstance(factory, pytest.TempPathFactory)
    return factory
