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
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, NoReturn, TypedDict, cast

import pytest

from sphinx.testing._isolation import Isolation, parse_isolation
from sphinx.testing.pytest_util import (
    _pytest_warn,
    check_mark_keywords,
    find_context,
    get_mark_parameters,
    get_node_location,
)
from sphinx.testing.warning_types import MarkDeprecationWarning, MarkWarning

if TYPE_CHECKING:
    from collections.abc import Mapping
    from io import StringIO
    from typing import Any

    from _pytest.nodes import Node as PytestNode
    from typing_extensions import Required

    from sphinx.testing._isolation import IsolationPolicy
    from sphinx.testing.pytest_util import TestNodeLocation, TestRootFinder

ISOLATION_ONCE_KEY: pytest.StashKey[dict[TestNodeLocation, tuple[str, str]]]
ISOLATION_ONCE_KEY = pytest.StashKey()


class SphinxMarkKeywords(TypedDict, total=False):
    """Typed dictionary for the keywords of :func:`pytest.mark.sphinx`.

    Cast dictionaries that should be processed into :class:`AppParams` objects
    to that this type so that ``mypy`` may detect errors in hardcoded keys.
    """

    buildername: str
    srcdir: str | os.PathLike[str] | None
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

    Such objects are constructed from :class:`SphinxMarkKeywords` objects.
    """

    # :class:`sphinx.application.Sphinx` required arguments
    buildername: Required[str]
    """The deduced builder name."""
    srcdir: Required[Path]
    """Path to the test sources directory.

    The uniqueness of this path depends on the isolation policy,
    the location of the test and the application's configuration.
    """
    # :class:`sphinx.application.Sphinx` optional arguments
    confoverrides: dict[str, Any]
    status: StringIO
    warning: StringIO
    freshenv: bool
    warningiserror: bool
    tags: list[str]
    verbosity: int
    parallel: int
    keep_going: bool
    # :class:`sphinx.testing.util.SphinxTestApp` optional arguments
    docutils_conf: str
    builddir: Path | None
    # :class:`sphinx.testing.util.SphinxTestApp` extras arguments
    isolate: Required[Isolation]
    """The deduced isolation policy."""
    testroot: Required[str | None]
    """The deduced testroot ID (possibly None if the default ID is not set)."""
    testroot_path: Required[str | None]
    """The absolute path to the testroot directory, if any."""
    shared_result: Required[str | None]
    """The optional shared result ID."""


class TestParams(TypedDict):
    """A view on the arguments of :func:`pytest.mark.test_params`."""

    shared_result: str | None


class AppParams(NamedTuple):
    """A view on the arguments of :func:`pytest.mark.sphinx`."""

    args: list[Any]
    kwargs: AppInitKwargs


def _mark_fail(mark: str, message: str) -> NoReturn:
    pytest.fail(f'pytest.mark.{mark}(): {message}')


def _chk_sphinx_params(node: PytestNode, kwargs: Mapping[str, Any]) -> None:
    check_mark_keywords('sphinx', SphinxMarkKeywords.__annotations__, kwargs, node=node)
    app_kwargs = cast(SphinxMarkKeywords, kwargs)
    check_mark_str_args('sphinx', buildername=app_kwargs['buildername'])

    if kwargs.get('freshenv', False) is not False:
        fmt = 'an explicit %r is not recommended, use %r or @pytest.mark.isolate() instead'
        msg = fmt % ('freshenv', 'isolate=True')
        _pytest_warn(node, MarkDeprecationWarning(msg, 'sphinx', removed_in=(9, 0)))

    if kwargs.get('srcdir', None) is not None:
        fmt = ('an explicit %r is not recommended, use %r, or '
               '@pytest.mark.test_result(%s=<id>) instead')
        msg = fmt % ('srcdir', 'isolate=True', 'shared_result')
        _pytest_warn(node, MarkDeprecationWarning(msg, 'sphinx', removed_in=(9, 0)))


def _get_sphinx_params(
    node: PytestNode, default_builder: str,
) -> tuple[list[Any], SphinxMarkKeywords]:
    params = get_mark_parameters(node, 'sphinx')
    args, kwargs = params[0], cast(SphinxMarkKeywords, params[1])

    # find the builder name
    if not args:
        kwargs.setdefault('buildername', default_builder)
    elif len(args) == 1:
        buildername = args.pop()
        if buildername != kwargs.pop('buildername', buildername):
            _mark_fail('sphinx', 'multiple values for %r' % 'buildername')
        kwargs['buildername'] = buildername
    else:
        _mark_fail('sphinx', 'expecting at most one positional argument')

    _chk_sphinx_params(node, kwargs)
    return args, kwargs


def _deduce_srcdir_id(
    testroot_id: str | None,
    shared_name: str | None,
    srcdir_name: str | os.PathLike[str] | None,
) -> str:
    """Deduce the sources directory from the given arguments.

    :param testroot_id: An optional testroot ID to use.
    :param shared_name: An optional shared result name.
    :param srcdir_name: An optional explicit sources directory name.
    :return: The sources directory name.
    """
    check_mark_str_args('sphinx', testroot=testroot_id, srcdir=srcdir_name)
    check_mark_str_args('test_params', shared_result=shared_name)

    if shared_name is not None:
        if srcdir_name is not None:
            pytest.fail('%r and %r are mutually exclusive' % ('shared_result', 'srcdir'))
        # include the testroot id for visual purposes
        return '-'.join(filter(None, (testroot_id, shared_name)))

    if srcdir_name is None:
        if testroot_id is None:  # neither an explicit nor the default testroot ID is given
            pytest.fail('missing %r or %r parameter' % ('testroot', 'srcdir'))
        return testroot_id

    # explicit 'srcdir' is given (but not recommended)
    return os.fsdecode(srcdir_name)


def _make_shared_id(node: PytestNode, srcdir: str | os.PathLike[str]) -> str:
    """Get the sources directory for subtests.

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
        # generate the sources directory ID shared by the sub-tests
        sources_id = _make_unique_id(srcdir)
        # Transform the xdist-group into a unique one, so that
        # the parametrized tests use the same sources directory
        # and are executed under the same worker.
        xdist_group = get_pytest_xdist_group(node)
        xdist_group = _make_unique_id(xdist_group)
        registry[location] = (sources_id, xdist_group)

    srcdir, group = registry[location]
    set_pytest_xdist_group(node, group)
    return srcdir


def get_app_params(
    node: PytestNode,
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
    isolation = kwargs['isolate'] = parse_isolation(isolation)
    # deduce the base srcdir
    testroot_id = kwargs['testroot'] = kwargs.get('testroot', testroot_finder.default)
    srcdir_id = _deduce_srcdir_id(testroot_id, shared_result, kwargs.get('srcdir'))

    if isolation is Isolation.always:
        srcdir_id = _make_unique_id(srcdir_id)
    elif isolation is Isolation.grouped:
        if node.get_closest_marker('parametrize') is None:
            msg = 'isolation %r without @pytest.mark.parametrize() is inefficient'
            _pytest_warn(node, MarkWarning(msg % isolation.name, 'isolate'))
        srcdir_id = _make_shared_id(node, srcdir_id)

    # Do a somewhat hash on configuration values to give a minimal protection
    # against side-effects (two tests with the same configuration should have
    # the same output; if they mess up with their sources directory, then they
    # should be isolated accordingly).
    namespace = _get_node_namespace(node)
    # compute the test configuration checksum for non-pure isolation
    env_crc32 = 0 if isolation is Isolation.always else _get_environ_checksum(
        kwargs['buildername'],
        kwargs.get('confoverrides'),
        kwargs.get('freshenv', False),
        kwargs.get('warningiserror', False),
        kwargs.get('tags'),
        kwargs.get('verbosity', 0),
        kwargs.get('parallel', 0),
        kwargs.get('keep_going', False),
    )

    app_kwargs = cast(AppInitKwargs, kwargs)
    app_kwargs['srcdir'] = Path(session_temp_dir) / namespace / str(env_crc32) / srcdir_id
    app_kwargs['testroot_path'] = testroot_finder.find(testroot_id)
    app_kwargs['shared_result'] = shared_result
    return app_args, app_kwargs


def _get_shared_result_id(node: PytestNode) -> str | None:
    marker = node.get_closest_marker('test_params')
    if marker is None:
        return None

    args, kwds = list(marker.args), dict(**marker.kwargs)
    if args:
        shared_result_id = args.pop()
    else:
        if 'shared_result' in kwds:
            # type-checking of this will be done below
            shared_result_id = kwds.pop('shared_result')
        else:
            if (location := get_node_location(node)) is None:
                shared_result_id = uuid.uuid4().hex
            else:
                fspath, lineno = location
                stem = os.path.basename(os.path.splitext(fspath)[0])
                shared_result_id = f'{stem}_L{lineno + 1}'

    if args:
        _mark_fail('test_params', 'expecting at most one positional argument')

    if kwds:
        _mark_fail('test_params', 'expecting at most one keyword argument')

    check_mark_str_args('test_params', shared_result=shared_result_id)
    # use of an assertion to ensure that the revealed type is str or None
    assert shared_result_id is None or isinstance(shared_result_id, str)
    return shared_result_id


def get_test_params(node: PytestNode) -> TestParams:
    """Process the :func:`pytest.mark.test_params` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    shared_result_id = _get_shared_result_id(node)
    ret = TestParams(shared_result=shared_result_id)
    check_mark_keywords('test_params', TestParams.__annotations__, ret, node=node)
    return ret


def check_mark_str_args(mark: str, /, **kwargs: Any) -> None:
    """Check that marker string arguments are either None or non-empty."""
    for argname, value in kwargs.items():
        if value and not isinstance(value, str) or not value and value is not None:
            msg = "expecting a non-empty string or None for %r, got: %r"
            _mark_fail(mark, msg % (argname, value))


def _get_environ_checksum(*args: Any) -> int:
    def default_encoder(x: object) -> int:
        try:
            return hash(x)
        except Exception:
            return id(x)

    # use the most compact JSON format
    env = json.dumps(args, ensure_ascii=False, sort_keys=True, indent=None,
                     separators=(',', ':'), default=default_encoder)
    return binascii.crc32(env.encode('utf-8', errors='backslashreplace'))


def _get_node_namespace(node: PytestNode) -> str:
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


def is_pytest_xdist_enabled(config: pytest.Config) -> bool:
    """Check that the ``pytest-xdist`` plugin is loaded and active.

    :param config: A pytest configuration object.

    Plugin is assumed to be loaded if ``-p no:xdist`` is not specified.
    """
    return (
        config.pluginmanager.has_plugin('xdist')
        and 'no:xdist' not in config.getoption('-p', [])
    )


def get_pytest_xdist_group(node: PytestNode, default: str = 'default', /) -> str | None:
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

    # to avoid circular imports
    from sphinx.testing.pytest_util import get_mark_parameters

    args, kwargs = get_mark_parameters(node, 'xdist_group')
    return args[0] if args else kwargs.get('name', default)


def set_pytest_xdist_group(node: PytestNode, group: str, /, *, append: bool = True) -> None:
    """Add a ``@pytest.mark.xdist_group(group)`` to *node*.

    This is a no-op if ``pytest-xdist`` is not active or *group* is ``None``.
    """
    if is_pytest_xdist_enabled(node.config):
        node.add_marker(pytest.mark.xdist_group(group), append=append)
