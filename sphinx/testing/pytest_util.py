from __future__ import annotations

__all__ = [
    # discovery utilities
    'TestRootFinder',
    # nodes utilities
    'ScopeName',
    'get_node_type_by_scope',
    'find_context',
    # node location
    'TestNodeLocation',
    'get_node_location',
    # marker utilities
    'get_mark_parameters',
    'check_mark_keywords',
    'stack_pytest_markers',
    # testing utilities
    'pytest_not_raises',
    # xdist utilities
    'is_pytest_xdist_enabled',
    'get_pytest_xdist_group',
    'set_pytest_xdist_group',
]

import os
import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Literal, TypeVar, overload

import pytest
from _pytest.nodes import get_fslocation_from_item

from sphinx.locale import __
from sphinx.testing.warning_types import SphinxMarkWarning, SphinxNodeWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Generator, Mapping
    from typing import Any, ClassVar

    # fully-qualified imports to avoid conflicts with Sphinx
    # or other Python packages when generating the docs
    import _pytest.config
    import _pytest.fixtures
    import _pytest.main
    import _pytest.nodes
    import _pytest.python
    import _pytest.scope
    import _pytest.stash


class TestRootFinder:
    """Object responsible for finding the testroot files in *rootdir*.

    For instance::

        finder = TestRootFinder('/foo/bar', 'test-', 'default')

    describes a testroot root directory at ``/foo/bar/roots``. The name of the
    directories in ``/foo/bar/roots`` consist of a *prefix* and an *ID* (in
    this case, the prefix is ``test-`` and the default *ID* is ``default``).

    >>> finder = TestRootFinder('/foo/bar', 'test-', 'default')
    >>> finder.find()
    '/foo/bar/test-default'
    >>> finder.find('abc')
    '/foo/bar/test-abc'
    """

    # Without this attribute, 'pytest' tries to collect this object
    # whenever it is imported in a test. Note that using a NamedTuple
    # is not possible since field names must not start with '_'.
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


T = TypeVar('T')
DT = TypeVar('DT')
NodeType = TypeVar('NodeType', bound="_pytest.nodes.Node")

ScopeName = Literal["session", "package", "module", "class", "function"]
"""Pytest scopes."""

_NODE_TYPE_BY_SCOPE: dict[ScopeName, type[_pytest.nodes.Node]] = {
    'session': pytest.Session,
    'package': pytest.Package,
    'module': pytest.Module,
    'class': pytest.Class,
    'function': pytest.Function,
}


@overload
def get_node_type_by_scope(scope: Literal['session']) -> type[_pytest.main.Session]:
    ...


@overload
def get_node_type_by_scope(scope: Literal['package']) -> type[_pytest.python.Package]:
    ...


@overload
def get_node_type_by_scope(scope: Literal['module']) -> type[_pytest.python.Module]:
    ...


@overload
def get_node_type_by_scope(scope: Literal['class']) -> type[_pytest.python.Class]:
    ...


@overload
def get_node_type_by_scope(scope: Literal['function']) -> type[_pytest.python.Function]:
    ...


def get_node_type_by_scope(scope: ScopeName) -> type[_pytest.nodes.Node]:
    """Get a pytest node type by its scope."""
    return _NODE_TYPE_BY_SCOPE[scope]


@overload
def find_context(
    node: _pytest.nodes.Node, cond: Literal['session'], /, *, include_self: bool = ...,
) -> _pytest.main.Session:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node, cond: Literal['package'], /, *, include_self: bool = ...,
) -> _pytest.python.Package:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node, cond: Literal['module'], /, *, include_self: bool = ...,
) -> _pytest.python.Module:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node, cond: Literal['class'], /, *, include_self: bool = ...,
) -> _pytest.python.Class:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node, cond: Literal['function'], /, *, include_self: bool = ...,
) -> _pytest.python.Function:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: Literal['session'],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.main.Session | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: Literal['package'],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.python.Package | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: Literal['module'],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.python.Module | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: Literal['class'],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.python.Class | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: Literal['function'],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.python.Function | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: ScopeName,
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> _pytest.nodes.Node | DT:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: type[NodeType],
    /,
    *,
    include_self: bool = ...,
) -> NodeType:
    ...


@overload
def find_context(
    node: _pytest.nodes.Node,
    cond: type[NodeType],
    default: DT,
    /,
    *,
    include_self: bool = ...,
) -> NodeType | DT:
    ...


def find_context(
    node: _pytest.nodes.Node,
    cond: ScopeName | type[_pytest.nodes.Node],
    /,
    *default: DT,
    include_self: bool = True,
) -> _pytest.nodes.Node | DT:
    """Get a parent node in the given scope.

    :param node: The node to get an ancestor of.
    :param cond: The ancestor type or scope.
    :param default: A default value.
    :param include_self: Include *node* if possible.
    :return: A node of suitable type.
    """
    if isinstance(cond, str):
        cond = get_node_type_by_scope(cond)

    parent = node.getparent(cond)
    if parent is None or parent is node and not include_self:
        if default:
            return default[0]
        raise AttributeError(__('no parent of type %s for %s') % (cond, node))
    return parent


TestNodeLocation = tuple[str, int]
"""The location ``(fspath, lineno)`` of a pytest node."""


def get_node_location(node: _pytest.nodes.Node) -> TestNodeLocation | None:
    """The node location ``(fspath, lineno)``, if any.

    If the path or the line number cannot be deduced, a warning is emitted.

    When deduced, the line number is a 0-based integer.
    """
    path, lineno = get_fslocation_from_item(node)
    if not (path := os.fsdecode(path)) or lineno == -1 or lineno is None:
        warnings.warn_explicit(
            __('could not obtain node location for %r') % node,
            category=SphinxNodeWarning, filename=path, lineno=-1,
        )
        return None
    return path, lineno


def get_mark_parameters(
    node: _pytest.nodes.Node,
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
        def test(request: pytest.FixtureRequest):
            args, kwargs = extract_node_parameters(request.node, 'foo')
            assert args == [1, 2]
            assert kwargs == {'a': 1, 'b': 2}
    """
    args, kwargs = list(default_args), default_kwargs
    for info in reversed(list(node.iter_markers(marker))):
        args[:len(info.args)] = info.args
        kwargs |= info.kwargs
    return args, kwargs


def check_mark_keywords(
    mark: str,
    keys: Collection[str],
    kwargs: Mapping[str, object],
    *,
    node: _pytest.nodes.Node | None = None,
    ignore_private: bool = True,
) -> bool:
    """Check the keyword arguments.

    :param mark: The name of the marker being checked.
    :param keys: The marker expected keyword parameters.
    :param kwargs: The keyword arguments to check.
    :param node: Optional node to emit warnings upon invalid arguments.
    :param ignore_private: Ignore keyword arguments with leading underscores.
    :return: Indicate whether extra keyword arguments were given.
    """
    ok = True
    for key in kwargs.keys() - keys:
        if key.startswith('_') and ignore_private:
            continue

        if node:
            warn_msg = f'pytest.mark.{mark}(): unexpected keyword argument: {key}'
            node.warn(SphinxMarkWarning(warn_msg))
        ok = False
    return ok


def stack_pytest_markers(
    marker: pytest.MarkDecorator, /, *markers: pytest.MarkDecorator,
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Create a decorator stacking pytest markers.

    Usage::

        mark1 = pytest.mark.mark1(...)
        mark2 = pytest.mark.mark2(...)
        mark3 = pytest.mark.mark3(...)
        deco = stack_pytest_markers(mark1, mark2, mark3)

        @deco
        def test(): ...
    """
    stack = [marker, *markers]
    stack.reverse()

    def wrapper(func: Callable[..., None]) -> Callable[..., None]:
        for marker in stack:
            func = marker(func)
        return func

    return wrapper


@contextmanager
def pytest_not_raises(*exceptions: type[BaseException]) -> Generator[None, None, None]:
    """Context manager asserting that no exception is raised.

    Usage::

        def test():
            with pytest_nothrow():
                X = 'x'.upper()

        def test():
            with pytest_nothrow(AttributeError):
                X = 'x'.upper()
    """
    try:
        yield
    except exceptions as exc:
        pytest.fail(f'DID RAISE {exc.__class__}')


def is_pytest_xdist_enabled(config: _pytest.config.Config) -> bool:
    """Check that the ``pytest-xdist`` plugin is loaded and active.

    :param config: A pytest configuration object.

    Plugin is assumed to be loaded if ``-p no:xdist`` is not specified.
    """
    return (
        config.pluginmanager.has_plugin('xdist')
        and 'no:xdist' not in config.getoption('-p', [])
    )


def get_pytest_xdist_group(
    node: _pytest.nodes.Node,
    default: str = 'default',
    /,
) -> str | None:
    """Get the ``@pytest.mark.xdist_group`` of a *node*, if any.

    :param node: The pytest node to parse.
    :param default: The default group if the marker has no argument.
    :return: The ``xdist_group`` if any.

    Note that *default* is only used if ``@pytest.mark.xdist_group`` is used.
    """
    if (
        not is_pytest_xdist_enabled(node.config)
        or node.get_closest_marker('xdist_group') is None
    ):
        return None

    args, kwargs = get_mark_parameters(node, 'xdist_group')
    return args[0] if args else kwargs.get('name', default)


def set_pytest_xdist_group(
    node: _pytest.nodes.Node,
    group: str | None = None,
    *,
    append: bool = True,
) -> None:
    """Add a ``@pytest.mark.xdist_group(group)`` to *node*.

    This is a no-op if ``pytest-xdist`` is not active or *group* is ``None``.
    """
    if group is not None and is_pytest_xdist_enabled(node.config):
        node.add_marker(pytest.mark.xdist_group(group), append=append)
