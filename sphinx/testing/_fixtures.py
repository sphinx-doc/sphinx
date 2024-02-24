"""Private utililty functions for :mod:`sphinx.testing.fixtures`.

This module is an implementation detail and any provided function
or class can be altered, removed or moved without prior notice.
"""

from __future__ import annotations

__all__ = ()

import binascii
import json
import os
import threading
import uuid
from enum import IntEnum
from enum import auto as _auto
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict, Union, cast

import pytest

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
    from collections.abc import Mapping
    from io import StringIO
    from typing import Any

    import _pytest.nodes
    from typing_extensions import Required

    from sphinx.testing.pytest_util import TestNodeLocation, TestRootFinder

ISOLATION_ONCE_KEY: pytest.StashKey[dict[TestNodeLocation, tuple[str, str]]]
ISOLATION_ONCE_KEY = pytest.StashKey()


class Isolation(IntEnum):
    """Isolation policy for the testing application."""

    minimal = _auto()
    """Minimal isolation mode."""
    grouped = _auto()
    """Similar to :attr:`always` but for parametrized tests."""
    always = _auto()
    """Copy the original testroot to a unique sources and build directory."""


IsolationPolicy = Union[bool, Literal["minimal", "grouped", "always"], Isolation]


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
    verbosity: int
    parallel: int
    keep_going: bool

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
    verbosity: int
    parallel: int
    keep_going: bool
    # :class:`sphinx.testing.util.SphinxTestApp` optional keyword arguments
    docutils_conf: str
    builddir: Path | None
    # extra keyword arguments
    isolate: Required[Isolation]
    testroot: Required[str | None]
    testroot_path: Required[str | None]
    shared_result: Required[str | None]


class AppParams(NamedTuple):
    """A view on the arguments of :func:`pytest.mark.sphinx`."""

    args: list[Any]
    kwargs: AppInitKwargs


class TestParams(TypedDict):
    """A view on the arguments of :func:`pytest.mark.test_params`."""

    shared_result: str | None


def _parse_isolation(policy: IsolationPolicy | None) -> Isolation:
    if isinstance(policy, Isolation):
        return policy

    if policy is None:
        return Isolation.minimal

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.minimal

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    msg = f'unknown isolation policy: {policy!r}'
    raise TypeError(msg)


def _chk_sphinx_params(node: _pytest.nodes.Node, kwargs: Mapping[str, Any]) -> None:
    check_mark_keywords('sphinx', SphinxMarkKeywords.__annotations__, kwargs, node=node)

    if kwargs.get('freshenv'):
        msg = f"using {'freshenv=True'!r} is not recommended, use {'isolate=True'!r} instead"
        node.warn(SphinxMarkWarning(msg))

    if kwargs.get('srcdir'):
        msg = (f"using {'srcdir'!r} is not recommended, use {'isolate=True'!r} "
               f"or @pytest.mark.test_params({'shared_result'}=...) instead")
        node.warn(SphinxMarkWarning(msg))


def _get_sphinx_params(
    node: _pytest.nodes.Node, default_builder: str,
) -> tuple[list[Any], SphinxMarkKeywords]:
    _check_nonempty_string('buildername', default_builder)
    params = get_mark_parameters(node, 'sphinx')
    args, kwargs = params[0], cast(SphinxMarkKeywords, params[1])

    # find the builder name
    if not args:
        kwargs.setdefault('buildername', default_builder)
    elif len(args) == 1:
        buildername = args.pop()
        if buildername != kwargs.pop('buildername', buildername):
            pytest.fail('pytest.mark.sphinx() has multiple values for %r' % 'buildername')
        kwargs['buildername'] = buildername
    else:
        # for now, we only allow one positional argument
        pytest.fail('pytest.mark.sphinx() takes at most one positional argument')

    _chk_sphinx_params(node, kwargs)
    return args, kwargs


def _deduce_srcdir_id(
    testroot_id: str | None,
    shared_result: str | None,
    srcdir: str | os.PathLike[str] | None,
) -> str:
    """Deduce the sources directory from the given arguments.

    :param testroot_id: An optional testroot ID string.
    :param shared_result: An optional shared result ID.
    :param srcdir: An optional explicit sources directory.
    :return: The sources directory name.
    """
    _check_nonempty_string('testroot', testroot_id)
    _check_nonempty_string('shared_result', shared_result)
    _check_nonempty_string('srcdir', srcdir)

    if shared_result is not None:
        if srcdir is not None:
            pytest.fail('%r and %r are mutually exclusive' % ('shared_result', 'srcdir'))
        return shared_result

    if srcdir is None:
        if testroot_id is None:
            pytest.fail('missing %r or %r parameter' % ('testroot', 'srcdir'))
        return testroot_id
    return os.fsdecode(srcdir)


def _make_once_srcdir_id(node: _pytest.nodes.Node, srcdir: str | os.PathLike[str]) -> str:
    """Get the sources directory in 'once' isolation.

    Nodes with the same locations will use the same sources directory
    and will be executed by the same ``xdist`` worker if needed.
    """
    if (location := get_node_location(node)) is None:
        # if the location cannot be found, full isolation is assumed
        return _make_unique_id(srcdir)

    registry: dict[TestNodeLocation, tuple[str, str]]
    # TODO(picnix): check if the stash is shared correctly
    registry = node.session.stash.setdefault(ISOLATION_ONCE_KEY, {})

    if location not in registry:
        # Generate the shared sources directory for the sub-tests.
        sources_id = _make_unique_id(srcdir)
        # Transform the xdist-group into a unique one, so that
        # the parametrized tests use the same sources directory
        # and are executed under the same worker.
        xdist_group = get_pytest_xdist_group(node)
        xdist_group = _make_unique_id(xdist_group)
        registry[location] = (sources_id, xdist_group)

    # The ``sources_id`` is unique in the registry but shared
    # across autogenerated (parametrized) sub-tests.
    srcdir, xdist_group = registry[location]
    set_pytest_xdist_group(node, xdist_group)
    return srcdir


def get_app_params(
    node: _pytest.nodes.Node,
    session_temp_dir: str | os.PathLike[str],
    testroot_finder: TestRootFinder,
    default_builder: str,
    default_isolation: IsolationPolicy | None,
    shared_result: str | None = None,
) -> tuple[list[Any], AppInitKwargs]:
    """Process the :func:`pytest.mark.sphinx` marker.

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

    # normalize the isolation policy
    isolation = kwargs.setdefault('isolate', default_isolation)
    isolation = kwargs['isolate'] = _parse_isolation(isolation)
    # deduce the base srcdir
    testroot_id = kwargs['testroot'] = kwargs.get('testroot', testroot_finder.default)
    srcdir = _deduce_srcdir_id(testroot_id, shared_result, kwargs.get('srcdir', None))

    if isolation is Isolation.always:
        srcdir = _make_unique_id(srcdir)
    elif isolation is Isolation.grouped:
        srcdir = _make_once_srcdir_id(node, srcdir)

    app_kwargs = cast(AppInitKwargs, kwargs)
    # Do a somewhat hash on configuration values to give a minimal protection
    # against side-effects (two tests with the same configuration should have
    # the same output; if they mess up with their sources directory, then they
    # should be isolated accordingly).
    namespace = _get_node_namespace(node)
    # arguments that somewhat uniquely describe a test context (with an
    # explicit isolation, this is not really required since
    environ = [
        kwargs['buildername'], kwargs.get('confoverrides'),
        kwargs.get('freshenv'), kwargs.get('warningiserror'), kwargs.get('tags'),
        kwargs.get('verbosity'), kwargs.get('parallel'), kwargs.get('keep_going'),
    ]
    env_crc32 = _get_environ_checksum(environ)

    app_kwargs['srcdir'] = Path(session_temp_dir) / namespace / str(env_crc32) / srcdir
    app_kwargs['testroot_path'] = testroot_finder.find(testroot_id)
    app_kwargs['shared_result'] = shared_result
    return app_args, app_kwargs


def get_test_params(node: _pytest.nodes.Node) -> TestParams:
    """Process the :func:`pytest.mark.test_params` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    ret = TestParams(shared_result=None)
    if (m := node.get_closest_marker('test_params')) is not None:
        args, kwds = list(m.args), dict(**m.kwargs)
        if args:
            shared_result_id = args.pop()
        else:
            if 'shared_result' in kwds:
                shared_result_id = kwds.pop('shared_result')
            else:
                location = get_node_location(node)
                if location is None:
                    shared_result_id = uuid.uuid4().hex
                else:
                    shared_result_id = ':'.join(map(str, location))

        if args:
            pytest.fail('pytest.mark.test_params() takes at most one positional argument')

        if kwds:
            pytest.fail('pytest.mark.test_params() takes at most one keyword argument')

        ret['shared_result'] = shared_result_id

    check_mark_keywords('test_params', TestParams.__annotations__, ret, node=node)
    _check_nonempty_string('shared_result', ret['shared_result'])
    return ret


def _check_nonempty_string(argname: str, value: Any) -> None:
    if value and not isinstance(value, str) or not value and value is not None:
        msg = "expecting a non-empty string or None for %r, got: %r"
        pytest.fail(msg % (argname, value))


def _get_environ_checksum(environ: Any) -> int:
    def default_encoder(x: object) -> int:
        try:
            return hash(x)
        except Exception:
            return id(x)

    serialized = json.dumps(environ, ensure_ascii=False,
                            sort_keys=True, indent=None,
                            default=default_encoder)
    return binascii.crc32(serialized.encode('utf-8', errors='backslashreplace'))


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
    return _get_unique_oid(f'{testobjid}{testenvid}')


@cache
def _get_unique_oid(object_name: str) -> str:
    """Get a (cached) hexadecimal for an object name.

    :param object_name: The name of the object to get a unique ID of.
    :return: A unique hexadecimal identifier for *object_name*.

    The *object_name* must be an UTF-8 string.
    """
    assert all(0 <= ord(x) <= 0x10ffff for x in object_name)
    return uuid.uuid5(uuid.NAMESPACE_OID, object_name).hex


def _make_unique_id(prefix: str | os.PathLike[str] | None = None) -> str:
    r"""Generate a unique identifier prefixed by *prefix*.

    :param prefix: An optional prefix to prepend to the unique identifier.
    :return: A unique identifier.

    .. note:: The probability for generating two identical IDs is negligible
              for a security parameter :math:`\lambda = 128`.
    """
    # We can be extremely unlucky (or lucky) to have collisions on UUIDs
    # but for the sake of efficiency (and since there are no real security
    # concerns in Sphinx), we can live with 128-bit AES equivalent security.
    suffix = uuid.uuid4().hex
    return '-'.join((os.fsdecode(prefix), suffix)) if prefix else suffix
