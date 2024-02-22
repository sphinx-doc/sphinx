"""Private utililty functions for :mod:`sphinx.testing.fixtures`.

This module is an implementation detail and any provided function
or class can be altered, removed or moved without prior notice.
"""

from __future__ import annotations

__all__ = ()

import os
import threading
import uuid
from enum import IntEnum
from enum import auto as _auto
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict, Union, cast

import pytest

from sphinx.locale import __
from sphinx.testing.pytest_util import (
    check_mark_keywords,
    find_context,
    get_mark_parameters,
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

    from sphinx.testing.pytest_util import TestNodeLocation, TestRootFinder

ISOLATION_ONCE_KEY: pytest.StashKey[dict[TestNodeLocation, tuple[str, str | None]]]
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


class TestExtras(TypedDict):
    isolation: Isolation
    """The deduced isolation policy."""
    testroot_id: str | None
    """The deduced testroot ID."""
    testroot_path: str | None
    """The deduced path to the (original) testroot directory."""
    shared_result: str | None
    """The deduced shared result ID."""


class SphinxMarkKeywords(TypedDict, total=False):
    """Typed dictionary for the keywords of :func:`pytest.mark.sphinx`.

    Cast dictionaries that should be processed into :class:`AppParams` objects
    to that this type so that ``mypy`` may detect errors in hardcoded keys.
    """

    srcdir: str | os.PathLike[str] | None
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

    # added or replaced in :func:`get_app_params`
    testroot: str | None
    isolate: IsolationPolicy | None


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
    # extra keyword arguments
    isolate: Required[Isolation]
    testroot: Required[str | None]
    testroot_path: Required[str | None]
    shared_result: Required[str | None]


class AppParams(NamedTuple):
    args: list[Any]
    kwargs: AppInitKwargs


class TestParams(TypedDict):
    shared_result: str | None


def _normalize_isolation(policy: IsolationPolicy | None) -> Isolation:
    if isinstance(policy, Isolation):
        return policy

    if policy is None:
        return Isolation.none

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.none

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    raise TypeError(__('unknown isolation policy: %r') % policy)


_SPHINX_MARK_KEYWORDS = frozenset(SphinxMarkKeywords.__annotations__)


def _get_sphinx_params(
    node: _pytest.nodes.Node, default_builder: str,
) -> tuple[list[Any], SphinxMarkKeywords]:
    params = get_mark_parameters(node, 'sphinx')
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

    check_mark_keywords('sphinx', _SPHINX_MARK_KEYWORDS, kwargs, node=node)
    return args, kwargs


def _normalize_srcdir(
    testroot_id: str | None,
    shared_result: str | None,
    srcdir: str | os.PathLike[str] | None,
) -> str | os.PathLike[str]:
    _check_nonempty_string('testroot', testroot_id)
    _check_nonempty_string('shared_result', shared_result)
    _check_nonempty_string('srcdir', srcdir)

    if shared_result is not None:
        if srcdir is not None:
            pytest.fail("'shared_result' and 'srcdir' are mutually exclusive")
        srcdir = shared_result

    if srcdir is None:
        if testroot_id is None:
            pytest.fail('missing "testroot" or "srcdir" parameter')
        return testroot_id
    return srcdir


def _getcontextid(value: str | None) -> str | None:
    return None if value is None else format(hash(value), '16x')


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
    :return: The application parameters and extra information.
    """
    # process pytest.mark.sphinx
    app_args, kwargs = _get_sphinx_params(node, default_builder)
    if kwargs.get('freshenv'):
        node.warn(SphinxMarkWarning(
            'using "freshenv=True" is not recommended, '
            'use "isolate=True" instead',
        ))

    if kwargs.get('srcdir'):
        node.warn(SphinxMarkWarning(
            'using "srcdir" is not recommended, use "isolate=True" '
            'or pytest.mark.test_params(shared_result=...) instead',
        ))

    # normalize the isolation policy
    isolation = kwargs.setdefault('isolate', default_isolation)
    isolation = kwargs['isolate'] = _normalize_isolation(isolation)
    # deduce the base srcdir
    testroot_id = kwargs['testroot'] = kwargs.get('testroot', testroot_finder.default)
    srcdir = _normalize_srcdir(testroot_id, shared_result, kwargs.get('srcdir', None))

    if isolation is Isolation.always:
        srcdir = make_unique_id(srcdir)
    elif isolation is Isolation.once:
        srcdir = _handle_isolation_once(node, shared_result, srcdir)

    app_kwargs = cast(AppInitKwargs, kwargs)

    # Ensure that tests in different test files always have distinct
    # sources, even if they are identical. Stated otherwise, even if
    # test1.py::test and test2.py::test have the same SRCDIR and are
    # not isolated, their real sources are in `/tmp/.../test1/SRCDIR`
    # and `/tmp/.../test2/SRCDIR` respectively. A similar logic is
    # done for tests within classes.
    namespace = _get_node_namespace(node)
    app_kwargs['srcdir'] = Path(session_temp_dir) / namespace / srcdir
    app_kwargs['testroot_path'] = testroot_finder.find(testroot_id)
    app_kwargs['shared_result'] = shared_result
    return app_args, app_kwargs


def _get_node_namespace(node: _pytest.nodes.Node) -> str:
    def get_context_id(scope: Literal['class', 'module']) -> str | None:
        ctx = find_context(node, scope, None)
        try:
            return ctx.obj.__name__ or None  # type: ignore[union-attr]
        except AttributeError:
            return None

    testmodid = get_context_id('module')
    testclsid = get_context_id('class')
    testobjid = ''.join(filter(None, (testmodid, testclsid))) or uuid.uuid4().hex
    # also isolate by processes to avoid side-effects due to pytest-xdist
    testenvid = f'{os.getpid()}-{threading.get_ident()}'
    return _object_id_uuid3(f'{testobjid}{testenvid}')


@cache
def _object_id_uuid3(object_name: str) -> str:
    return uuid.uuid3(uuid.NAMESPACE_OID, object_name).hex


def _handle_isolation_once(
    node: _pytest.nodes.Node,
    shared_result: str | None,
    srcdir: str | os.PathLike[str],
) -> str:
    if (location := get_node_location(node)) is None:
        # if the location cannot be found, full isolation is assumed
        return make_unique_id(srcdir)

    registry: dict[TestNodeLocation, tuple[str, str | None]]
    registry = node.session.stash.setdefault(ISOLATION_ONCE_KEY, {})

    if location not in registry:
        # Generate the shared sources directory for the sub-tests,
        # possibly using a 'shared_result' if the latter is given.
        sources_id = shared_result or make_unique_id(srcdir)
        # Transform the xdist-group into a unique one, so that
        # the parametrized tests use the same sources directory
        # and are executed under the same worker.
        xdist_group = get_pytest_xdist_group(node)
        xdist_group = make_unique_id(xdist_group)
        registry[location] = (sources_id, xdist_group)

    # The ``sources_id`` is unique in the registry but shared
    # across autogenerated (parametrized) sub-tests.
    srcdir, xdist_group = registry[location]
    set_pytest_xdist_group(node, xdist_group)
    return srcdir


_TEST_PARAMS_MARK_KEYWORDS = frozenset(TestParams.__annotations__)


def get_test_params(node: _pytest.nodes.Node) -> TestParams:
    """Get the keyword arguments of a ``@pytest.mark.test_params`` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    kwargs = TestParams(shared_result=None)
    if (marker := node.get_closest_marker('test_params')) is not None:
        kwargs |= marker.kwargs  # type: ignore[typeddict-item]
    check_mark_keywords('test_params', _TEST_PARAMS_MARK_KEYWORDS, kwargs, node=node)
    _check_nonempty_string('shared_result', kwargs['shared_result'])
    return kwargs


def make_unique_id(prefix: str | os.PathLike[str] | None = None) -> str:
    """Add a unique suffix to *prefix*.

    Uniqueness is guaranteed up to a probability of a collision on UUID-4s.
    """
    # We can be extremely unlucky (or lucky) to have collisions on UUIDs
    # but for the sake of efficiency (and since there are no real security
    # concerns in Sphinx), we will not enforce uniqueness.
    suffix = uuid.uuid4().hex
    return '-'.join((os.fsdecode(prefix), suffix)) if prefix else suffix


def _check_nonempty_string(name: str, value: Any) -> None:
    if value and not isinstance(value, str) or not value and value is not None:
        msg = "expecting a non-empty string or None for %r, got: %r"
        pytest.fail(msg % (name, value))
