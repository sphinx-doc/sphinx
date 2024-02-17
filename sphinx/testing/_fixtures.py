"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import os
import uuid
from enum import IntEnum
from enum import auto as _auto
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict, Union, cast

import pytest

from sphinx.locale import __
from sphinx.testing.pytest_util import (
    extract_node_parameters,
    get_node_location,
    get_pytest_xdist_group,
    set_pytest_xdist_group,
)

if TYPE_CHECKING:
    from io import StringIO
    from typing import Any

    from _pytest.nodes import Node

    from sphinx.testing.pytest_util import TestRootFinder

ISOLATION_ONCE_KEY: pytest.StashKey[dict[tuple[str, int], tuple[str, str | None]]]
ISOLATION_ONCE_KEY = pytest.StashKey()


class Isolation(IntEnum):
    """Isolation policy for the testing application."""

    none = _auto()
    """The default isolation mode."""
    once = _auto()
    """Similar to :attr:`always` but for parametrized tests."""
    always = _auto()
    """Copy the original testroot to a unique sources and build directory."""


IsolationPolicy = Union[bool, Literal["none", "once", "always"], Isolation]


class _SphinxMarkKeywords(TypedDict):
    testroot: str | None
    isolate: Isolation


class _AppKwargs(_SphinxMarkKeywords):
    srcdir: Path

    _sphinx_testroot_path: str | None
    _sphinx_shared_result: bool


# TODO(picnixz): replace inheritance with typing.Required when Python 3.11
#                becomes the minimal version (inheritance is used to avoid
#                an additional ``typing_extensions`` dependency).
class AppKwargs(_AppKwargs, total=False):
    """The :class:`sphinx.testing.util.SphinxTestApp` constructor keywords."""

    buildername: str
    builddir: Path | None
    freshenv: bool
    confoverrides: dict[str, Any]
    tags: list[str]
    docutils_conf: str
    parallel: int

    status: StringIO
    warning: StringIO


class AppParams(NamedTuple):
    args: list[Any]
    kwargs: AppKwargs


class TestParams(TypedDict):
    shared_result: str | None


def _parse_isolation_policy(policy: IsolationPolicy | None) -> Isolation:
    if isinstance(policy, Isolation):
        return policy

    if policy is None:
        return Isolation.none

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.none

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    raise TypeError(__('unknown isolation policy: %r') % policy)


def get_app_params(
    node: Node,
    session_temp_dir: str | os.PathLike[str],
    testroot_finder: TestRootFinder,
    default_builder: str,
    default_isolation: IsolationPolicy | None,
    shared_result: str | None = None,
) -> tuple[list[Any], AppKwargs]:
    """Extract the application parameters from a pytest node.

    :param node: The pytest node to parse.
    :param session_temp_dir: The session temporary directory.
    :param testroot_finder: The testroot finder object.
    :param default_builder: The application default builder name.
    :param default_isolation: The isolation default policy.
    :param shared_result: An optional shared result ID.
    :return: The application parameters.

    It *default_testroot* is not specified, an explicit *srcdir* must be
    specified instead.
    """
    # process pytest.mark.sphinx
    args, kwargs = extract_node_parameters(node, 'sphinx')

    # find the builder name
    if not args:
        kwargs.setdefault('buildername', default_builder)
    elif len(args) == 1:
        buildername = args.pop()
        if buildername != kwargs.pop('buildername', buildername):
            pytest.fail('pytest.mark.sphinx() has multiple values for "buildername"')
        kwargs['buildername'] = buildername
    else:
        pytest.fail('pytest.mark.sphinx() takes at most one positional argument')

    # find the isolation policy
    isolation_policy = kwargs.get('isolate', default_isolation)
    kwargs['isolate'] = isolation = _parse_isolation_policy(isolation_policy)

    testroot: str | None = kwargs.setdefault('testroot', testroot_finder.default)
    srcdir: str | os.PathLike[str] | None = kwargs.setdefault('srcdir', None)
    if not testroot and not srcdir:
        pytest.fail('missing "testroot" or "srcdir" parameter')
    kwargs['_sphinx_testroot_path'] = testroot_finder.find(testroot)

    # process pytest.mark.test_params
    if shared_result:
        if srcdir is not None and srcdir != shared_result:
            pytest.fail("'shared_result' and 'srcdir' are mutually exclusive, unless equal")
        srcdir = shared_result

    kwargs['_sphinx_shared_result'] = shared_result is not None
    # construct the sources directory
    srcdir = cast(str, testroot) if srcdir is None else srcdir

    if isolation is Isolation.always:
        srcdir = _get_unique_srcdir(srcdir)
    elif isolation is Isolation.once:
        if (location := get_node_location(node)) is None:
            # if the location cannot be found, full isolation is assumed
            srcdir = _get_unique_srcdir(srcdir)
        else:
            registry: dict[tuple[str, int], tuple[str, str | None]]
            registry = node.session.stash.setdefault(ISOLATION_ONCE_KEY, {})

            if location not in registry:
                # generate the shared sources directory for the sub-tests
                sources_id = shared_result or _get_unique_srcdir(srcdir)
                # make sure that the parametrized tests are executed under the same worker
                registry[location] = (sources_id, get_pytest_xdist_group(node))

            # The ``sources_id`` is unique in the registry but shared
            # across autogenerated (parametrized) sub-tests.
            srcdir, xdist_group = registry[location]
            set_pytest_xdist_group(node, xdist_group)

    kwargs['srcdir'] = Path(session_temp_dir) / srcdir
    return args, cast(AppKwargs, kwargs)


def get_test_params(node: Node) -> TestParams:
    """Get the keyword arguments of a ``@pytest.mark.test_params`` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    env = node.get_closest_marker('test_params')
    result = env.kwargs if env else {}
    shared_result = result.setdefault('shared_result', None)

    if shared_result and not isinstance(shared_result, str):
        pytest.fail(f"expecting a string for 'shared_result', got: {shared_result!r}")
    return cast(TestParams, result)


def _get_unique_srcdir(srcdir: str | os.PathLike[str]) -> str:
    return '-'.join((os.fsdecode(srcdir), uuid.uuid4().hex))
