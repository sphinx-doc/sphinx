from __future__ import annotations

__all__ = [
    'TestRootFinder',
    'extract_node_parameters',
    'get_node_location',
    'is_pytest_xdist_enabled',
    'get_pytest_xdist_group',
    'set_pytest_xdist_group',
]

import os
import uuid
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING

import pytest
from _pytest.nodes import get_fslocation_from_item

from sphinx.locale import __
from sphinx.testing.warning_types import SphinxNodeWarning

if TYPE_CHECKING:
    from typing import Any, ClassVar, Literal

    import _pytest.config
    import _pytest.nodes


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
        rootdir: str | os.PathLike[str] | None = None,
        prefix: str | None = None,
        default: str | None = None,
        *,
        allow_empty: bool = False,
    ) -> None:
        """Construct a :class:`TestRootFinder` object.

        :param rootdir: The path to the directory with the testroot files.
        :param prefix: The prefix to prepend to a testroot ID.
        :param default: The ID of the default test sources directory.
        :param allow_empty: If false, empty IDs are equivalent to ``None``.
        :raise ValueError: The *root* is an empty string (use ``"."`` instead).

        The *allow_empty* flag is useful to avoid constructing paths possibly
        shorter than expected. In particular, testroots IDs equal to the prefix
        are not supported by default.
        """
        if not rootdir and rootdir is not None:
            msg = 'expecting None or a non-empty string for "root"'
            raise ValueError(msg)

        self.rootdir = rootdir
        self.prefix = prefix if allow_empty else (prefix or None)
        self.default = default if allow_empty else (default or None)
        self.allow_empty = allow_empty

    def find(self, name: str | None = None) -> str | None:
        """Find the sources directory for a named or the default testroot.

        :param name: A testroot name (without its prefix).
        :return: The path to the testroot directory, if any.
        """
        if not (rootdir := self.rootdir):
            return None

        prefix, default = self.prefix, self.default

        if self.allow_empty:
            name = default if name is None else name
        else:
            name = name or default

        if name is not None and prefix is not None:
            name = f'{prefix}{name}'
        return None if name is None else os.path.join(rootdir, name)


def extract_node_parameters(
    node: _pytest.nodes.Node, marker: str, /, *args: Any, **kwargs: Any,
) -> tuple[list[Any], dict[str, Any]]:
    """Get the positional and keyword arguments of node.

    :param node: The pytest node to analyze.
    :param marker: The name of the marker to extract the parameters of.
    :param args: Optional default positional arguments.
    :param kwargs: Optional default keyword arguments.
    :return: The positional and keyword arguments.

    By convention, arguments are not stacked, that is, they are collected
    in the *reverse* order the marker decorators are specified, e.g.::

        @pytest.mark.foo('ignored', 2, a='ignored', b=2)
        @pytest.mark.foo(1, a=1)
        def test(request: pytest.FixtureRequest):
            args, kwargs = extract_node_parameters(request.node, 'foo')
            assert args == [1, 2]
            assert kwargs == {'a': 1, 'b': 2}
    """
    poargs = list(args)  # new variable name is needed for mypy
    for info in reversed(list(node.iter_markers(marker))):
        poargs[:len(info.args)] = info.args
        kwargs |= info.kwargs
    return poargs, kwargs


@lru_cache(maxsize=256)
def get_node_location(node: _pytest.nodes.Node) -> tuple[str, int] | None:
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


def is_pytest_xdist_enabled(config: _pytest.config.Config) -> bool:
    """Check that the ``pytest-xdist`` plugin is loaded and active.

    :param config: A pytest configuration object.
    """
    return (
        config.pluginmanager.has_plugin('xdist')
        and config.getoption("dist", "no") != "no"
    )


def get_pytest_xdist_group(node: _pytest.nodes.Node) -> str | None:
    """Get the ``@pytest.mark.xdist_group`` of a *node*, if any."""
    if not is_pytest_xdist_enabled(node.config):
        return None

    if m := node.get_closest_marker('xdist_group'):
        return m.args[0] if len(m.args) > 0 else m.kwargs.get('name', 'default')
    return uuid.uuid4().hex


def set_pytest_xdist_group(
    node: _pytest.nodes.Node,
    group: str | None = None,
) -> None:
    """Add a ``@pytest.mark.xdist_group(group)`` to *node*.

    This is a no-op if ``pytest-xdist`` is not active or *group* is ``None``.
    """
    if group is not None and is_pytest_xdist_enabled(node.config):
        node.add_marker(pytest.mark.xdist_group(group))
