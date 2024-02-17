"""Sphinx test suite utilities"""

from __future__ import annotations

__all__ = [
    'TestRootFinder',
    'extract_node_parameters',
    'get_node_location',
    'has_pytest_xdist',
    'get_pytest_xdist_group',
    'set_pytest_xdist_group',
]

import os
import uuid
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import pytest
from _pytest.nodes import get_fslocation_from_item

from sphinx.locale import __

if TYPE_CHECKING:
    from _pytest.nodes import Node


class TestRootFinder:
    """Object responsible for finding the testroot files in *rootdir*.

    :param rootdir: The path to the directory containing the testroot files.
    :param default: The name of the default test sources directory to use.
    :param prefix: The prefix to prepend to a test sources directory name.

    For instance::

        finder = TestRootFinder('/foo/bar/roots', 'minimal', 'pre-')

    describes a testroot root directory at ``/foo/bar/roots``. The directories
    in ``/foo/bar/roots`` are referred to their *name* stripped from the 'pre-'
    prefix, namely ``config.find('bar') == /foo/bar/roots/pre-bar``.


    >>> finder = TestRootFinder('/foo/bar', 'default', 'my-')
    >>> finder.find()
    '/foo/bar/my-default'
    >>> finder.find('abc')
    '/foo/bar/my-abc'
    """

    def __init__(
        self,
        rootdir: str | os.PathLike[str] | None = None,
        default: str | None = None,
        prefix: str | None = None,
    ) -> None:
        self.rootdir = rootdir
        self.default = default
        self.prefix = prefix

    def find(self, name: str | None = None) -> str | None:
        """Find the directory for a named or the default testroot.

        :param name: A testroot name (without its prefix).
        :return: The path to the testroot directory, if any.
        """
        if not self.rootdir:
            return None

        dir_name = name or self.default
        if not dir_name:
            return None

        fullname = ''.join(filter(None, (self.prefix, dir_name)))
        return os.path.join(self.rootdir, fullname)


def extract_node_parameters(
    node: Node, marker: str | None, /, **defaults: Any,
) -> tuple[list[Any], dict[str, Any]]:
    """Get the positional and keyword arguments of node.

    :param node: The pytest node to analyze.
    :param marker: The name of the marker to extract the parameters of.
    :param defaults: Optional default keyword arguments.
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
    poargs: dict[int, Any] = {}
    kwargs: dict[str, Any] = defaults

    # to avoid stacking positional args
    for info in reversed(list(node.iter_markers(marker))):
        poargs |= dict(enumerate(info.args))
        kwargs |= info.kwargs

    args = [poargs[i] for i in sorted(poargs.keys())]
    return args, kwargs


@lru_cache(maxsize=256)
def get_node_location(node: Node) -> tuple[str, int] | None:
    """The node location ``(fspath, lineno)``.

    If either *fspath* or *lineno* are not specified or unknown,
    a regular warning is emitted and ``None`` is returned.
    """
    path, lineno = get_fslocation_from_item(node)
    if not (path := os.fsdecode(path)) or lineno == -1 or lineno is None:
        warnings.warn_explicit(
            __('could not obtain node location for %r') % node,
            category=RuntimeWarning, filename=path, lineno=-1,
        )
        return None
    return path, lineno


def has_pytest_xdist(node: Node) -> bool:
    return node.session.config.pluginmanager.has_plugin('xdist')


def get_pytest_xdist_group(node: Node) -> str | None:
    if not has_pytest_xdist(node):
        return None

    if m := node.get_closest_marker('xdist_group'):
        return m.args[0] if len(m.args) > 0 else m.kwargs.get('name', 'default')
    return uuid.uuid4().hex


def set_pytest_xdist_group(node: Node, group_id: str | None) -> None:
    if group_id is not None and has_pytest_xdist(node):
        node.add_marker(pytest.mark.xdist_group(group_id))
