"""Private utililty functions for :mod:`sphinx.testing.fixtures`.

This module is an implementation detail and any provided function
or class can be altered, removed or moved without prior notice.
"""

from __future__ import annotations

import os
import uuid
from enum import IntEnum
from enum import auto as _auto
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, TypedDict, Union, cast

import pytest

from sphinx.locale import __
from sphinx.testing.pytest_util import (
    extract_node_parameters,
    get_node_location,
    get_pytest_xdist_group,
    set_pytest_xdist_group,
)
from sphinx.testing.warning_types import SphinxMarkWarning

if TYPE_CHECKING:
    from io import StringIO
    from typing import Any

    import _pytest.nodes
    from typing_extensions import Required

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


class SphinxMarkKeywords(TypedDict, total=False):
    """Typed dictionary for the keywords of :func:`pytest.mark.sphinx`.

    Cast dictionaries that should be processed into :class:`AppParams` objects
    to that this type so that ``mypy`` may detect errors in hardcoded keys.
    """

    srcdir: Path
    buildername: str
    confoverrides: dict[str, Any] | None
    status: StringIO | None
    warning: StringIO | None
    freshenv: bool
    warningiserror: bool
    tags: list[str] | None
    parallel: int
    verbosity: int

    docutils_conf: str | None
    builddir: Path | None

    # added or updated in :func:`get_app_params`
    testroot: str | None
    isolate: IsolationPolicy | None
    # added only in :func:`get_app_params` (should never be specified on the node)
    _sphinx_testroot_path: str | None
    _sphinx_shared_result: str | None


_SPHINX_MARK_KEYWORDS: Final[frozenset[str]] = frozenset(
    _ for _ in SphinxMarkKeywords.__annotations__ if not _.startswith('_')
)


class AppInitKwargs(TypedDict, total=False):
    """The type of the keyword arguments after processing.

    Such objects are constructed from :class:`_AppInitKwargs` objects.
    """

    # :class:`sphinx.application.Sphinx` required keyword arguments
    srcdir: Required[Path]
    """Path to the test sources directory.

    The uniqueness of this path depends on the isolation policy.
    """
    buildername: Required[str]
    """The deduced builder name."""
    # :class:`sphinx.application.Sphinx` optional keyword arguments
    confoverrides: dict[str, Any]
    status: StringIO
    warning: StringIO
    freshenv: bool
    warningiserror: bool
    tags: list[str]
    parallel: int
    verbosity: int
    # :class:`sphinx.testing.util.SphinxTestApp` optional keyword arguments
    docutils_conf: str
    builddir: Path | None
    # :class:`sphinx.testing.util.SphinxTestApp` internal keyword arguments
    testroot: Required[str | None]
    """The deduced testroot name."""
    isolate: Required[Isolation]
    """The deduced isolation policy."""
    _sphinx_testroot_path: Required[str | None]
    """The deduced path to the (original) testroot directory."""
    _sphinx_shared_result: Required[str | None]
    """The deduced shared result ID."""


class AppParams(NamedTuple):
    args: list[Any]
    kwargs: AppInitKwargs


class TestParams(TypedDict):
    shared_result: str | None


def normalize_isolation(policy: IsolationPolicy | None) -> Isolation:
    if isinstance(policy, Isolation):
        return policy

    if policy is None:
        return Isolation.none

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.none

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    raise TypeError(__('unknown isolation policy: %r') % policy)


def _get_sphinx_params(
    node: _pytest.nodes.Node, default_builder: str,
) -> tuple[list[Any], SphinxMarkKeywords]:
    params = extract_node_parameters(node, 'sphinx')
    args, kwargs = params[0], cast(SphinxMarkKeywords, params[1])

    # find the builder name
    if not args:
        kwargs.setdefault('buildername', default_builder)
    elif len(args) == 1:
        buildername = args.pop()
        if buildername != kwargs.pop('buildername', buildername):
            pytest.fail('pytest.mark.sphinx() has multiple values for "buildername"')
        kwargs['buildername'] = buildername
    else:
        # for now, we only allow one positional argument
        pytest.fail('pytest.mark.sphinx() takes at most one positional argument')

    return args, validate_sphinx_keywords(node, kwargs)


def get_app_params(
    node: _pytest.nodes.Node,
    session_temp_dir: str | os.PathLike[str],
    testroot_finder: TestRootFinder,
    default_builder: str,
    default_isolation: IsolationPolicy | None,
    shared_result: str | None = None,
) -> tuple[list[Any], AppInitKwargs]:
    """Extract the application parameters from a pytest node.

    :param node: The pytest node to parse.
    :param session_temp_dir: The session temporary directory.
    :param testroot_finder: The testroot finder object.
    :param default_builder: The application default builder name.
    :param default_isolation: The isolation default policy.
    :param shared_result: An optional shared result ID.
    :return: The application parameters.
    """
    # process pytest.mark.sphinx
    args, kwargs = _get_sphinx_params(node, default_builder)
    # set some default values
    isolation: IsolationPolicy | None = kwargs.setdefault('isolate', default_isolation)
    # normalize the isolation policy
    isolation = kwargs['isolate'] = normalize_isolation(isolation)

    testroot_id: str | None = kwargs.setdefault('testroot', testroot_finder.default)
    srcdir: str | os.PathLike[str] | None = kwargs.get('srcdir', None)
    if not testroot_id and not srcdir:
        pytest.fail('missing "testroot" or "srcdir" parameter')

    # process pytest.mark.test_params
    shared_result = validate_shared_result_id(node, shared_result)
    if shared_result:
        if srcdir is not None and srcdir != shared_result:
            pytest.fail("'shared_result' and 'srcdir' are mutually exclusive, unless equal")
        srcdir = shared_result

    # construct the sources directory
    srcdir = testroot_id if srcdir is None else srcdir
    assert srcdir is not None

    if isolation is Isolation.always:
        srcdir = get_unique_srcdir(srcdir)
    elif isolation is Isolation.once:
        if (location := get_node_location(node)) is None:
            # if the location cannot be found, full isolation is assumed
            srcdir = get_unique_srcdir(srcdir)
        else:
            registry: dict[tuple[str, int], tuple[str, str | None]]
            registry = node.session.stash.setdefault(ISOLATION_ONCE_KEY, {})

            if location not in registry:
                # Generate the shared sources directory for the sub-tests,
                # possibly using a 'shared_result' if the latter is given.
                #
                # The caller is responsible to handle any side-effect
                # if the 'shared_result' value is not unique.
                sources_id = shared_result or get_unique_srcdir(srcdir)
                # make sure that the parametrized tests are executed under the same worker
                registry[location] = (sources_id, get_pytest_xdist_group(node))

            # The ``sources_id`` is unique in the registry but shared
            # across autogenerated (parametrized) sub-tests.
            srcdir, xdist_group = registry[location]
            set_pytest_xdist_group(node, xdist_group)

    kwargs['srcdir'] = Path(session_temp_dir) / srcdir
    # add some extra information for fixtures
    kwargs['_sphinx_testroot_path'] = testroot_finder.find(testroot_id)
    kwargs['_sphinx_shared_result'] = shared_result
    return args, cast(AppInitKwargs, kwargs)


def get_test_params(node: _pytest.nodes.Node) -> TestParams:
    """Get the keyword arguments of a ``@pytest.mark.test_params`` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    env = node.get_closest_marker('test_params')
    result = env.kwargs if env else {}
    shared_result = result.setdefault('shared_result', None)
    validate_shared_result_id(node, shared_result)
    return cast(TestParams, result)


def get_unique_srcdir(srcdir: str | os.PathLike[str]) -> str:
    return '-'.join((os.fsdecode(srcdir), uuid.uuid4().hex))


def validate_sphinx_keywords(
    node: _pytest.nodes.Node,
    kwargs: SphinxMarkKeywords,
) -> SphinxMarkKeywords:
    for key in kwargs.keys() - _SPHINX_MARK_KEYWORDS:
        node.warn(SphinxMarkWarning(f'unexpected keyword argument: {key}'))
    return kwargs


def validate_shared_result_id(node: _pytest.nodes.Node, value: Any) -> str | None:
    if value and not isinstance(value, str) or not value and value is not None:
        pytest.fail(f"expecting a string or None for 'shared_result', got: {value!r}")
    return value
