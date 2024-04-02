"""Private utililty functions for markers in :mod:`sphinx.testing.plugin`.

This module is an implementation detail and any provided function
or class can be altered, removed or moved without prior notice.
"""

from __future__ import annotations

__all__ = ()

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypedDict, cast

import pytest

from sphinx.testing._internal.isolation import Isolation, normalize_isolation_policy
from sphinx.testing._internal.pytest_util import (
    check_mark_keywords,
    check_mark_str_args,
    format_mark_failure,
    get_mark_parameters,
    get_node_location,
)
from sphinx.testing._internal.util import (
    get_container_id,
    get_location_id,
    get_objects_checksum,
    make_unique_id,
)

if TYPE_CHECKING:
    import os
    from io import StringIO
    from typing import Any

    from _pytest.nodes import Node as PytestNode
    from typing_extensions import Required

    from sphinx.testing._internal.isolation import NormalizableIsolation
    from sphinx.testing._internal.pytest_util import TestRootFinder


class SphinxMarkEnviron(TypedDict, total=False):
    """Typed dictionary for the arguments of :func:`pytest.mark.sphinx`.

    For the :func:`!pytest.mark.sphinx` marker, we only allow keyword
    arguments and not positional arguments except the builder name.

    Note that this differs from the :class:`~sphinx.testing.util.SphinxTestApp`
    constructor which accepts both positional and keyword arguments; however
    this is done as such so that it makes easier to check the marker itself.
    """

    buildername: str
    srcdir: str

    confoverrides: dict[str, Any]
    # using freshenv=True will be treated as equivalent to use isolate=True
    # but in the future, we might want to deprecate this marker keyword in
    # favor of "isolate" (that way, we don't need to maintain it)
    freshenv: bool
    warningiserror: bool
    tags: list[str]
    verbosity: int
    parallel: int
    keep_going: bool

    builddir: str
    docutils_conf: str

    # added or updated fields
    testroot: str | None
    isolate: NormalizableIsolation


class SphinxInitKwargs(TypedDict, total=False):
    """The type of the keyword arguments after processing.

    Such objects are constructed from :class:`SphinxMarkEnviron` objects.
    """

    # :class:`sphinx.application.Sphinx` positional arguments as keywords
    buildername: Required[str]
    """The deduced builder name."""
    # :class:`sphinx.application.Sphinx` required arguments
    srcdir: Required[Path]
    """Absolute path to the test sources directory.

    The uniqueness of this path depends on the isolation policy,
    the location of the test and the application's configuration.
    """
    # :class:`sphinx.application.Sphinx` optional arguments
    confoverrides: dict[str, Any] | None
    status: StringIO | None
    warning: StringIO | None
    freshenv: bool
    warningiserror: bool
    tags: list[str] | None
    verbosity: int
    parallel: int
    keep_going: bool
    # :class:`sphinx.testing.util.SphinxTestApp` optional arguments
    builddir: Path | None
    docutils_conf: str | None
    # :class:`sphinx.testing.util.SphinxTestApp` extras arguments
    isolate: Required[Isolation]
    """The deduced isolation policy."""
    testroot: Required[str | None]
    """The deduced testroot ID (possibly None if the default ID is not set)."""
    testroot_path: Required[str | None]
    """The absolute path to the testroot directory, if any."""
    shared_result: Required[str | None]
    """The optional shared result ID."""


class AppParams(NamedTuple):
    """The processed arguments of :func:`pytest.mark.sphinx`.

    The *args* and *kwargs* values can be directly used as inputs
    to the :class:`~sphinx.testing.util.SphinxTestApp` constructor.
    """

    args: list[Any]
    """The constructor positional arguments, except ``buildername``."""
    kwargs: SphinxInitKwargs
    """The constructor keyword arguments, including ``buildername``."""


class AppLegacyParams(NamedTuple):
    args: list[Any]
    kwargs: dict[str, Any]


class TestParams(TypedDict):
    """A view on the arguments of :func:`pytest.mark.test_params`."""

    shared_result: str | None


def _get_sphinx_environ(node: PytestNode, default_builder: str) -> SphinxMarkEnviron:
    args, kwargs = get_mark_parameters(node, 'sphinx')

    if len(args) > 1:
        err = 'expecting at most one positional argument'
        pytest.fail(format_mark_failure('sphinx', err))

    env = cast(SphinxMarkEnviron, kwargs)

    if args:
        buildername = args.pop()
        if buildername != env.pop('buildername', buildername):
            err = '%r has duplicated values' % 'buildername'
            pytest.fail(format_mark_failure('sphinx', err))
        env['buildername'] = buildername
    else:
        buildername = env.setdefault('buildername', default_builder)

    if not buildername:
        pytest.fail(format_mark_failure('sphinx', 'missing builder name'))

    check_mark_keywords('sphinx', SphinxMarkEnviron.__annotations__, env, node=node)
    return env


def _get_test_srcdir(
    srcdir: str | None,
    testroot: str | None,
    shared_result: str | None,
) -> str:
    """Deduce the sources directory from the given arguments.

    :param srcdir: An optional explicit source directory name.
    :param testroot: An optional testroot ID to use.
    :param shared_result: An optional shared result ID.
    :return: The sources directory name *srcdir* (non-empty string).
    """
    check_mark_str_args('sphinx', srcdir=srcdir, testroot=testroot)
    check_mark_str_args('test_params', shared_result=shared_result)

    if srcdir is not None:
        # the srcdir is explicitly given, so we use this name
        # and we do not bother to make it unique (the user is
        # responsible for that !)
        return srcdir

    if shared_result is not None:
        # include the testroot id for visual purposes (unless it is
        # not specified, which only occurs when there is no rootdir)
        return f'{testroot}-{shared_result}' if testroot else shared_result

    if testroot is None:
        # neither an explicit nor the default testroot ID is given
        pytest.fail('missing %r or %r parameter' % ('testroot', 'srcdir'))

    return testroot


def _get_common_config_checksum(
    # positional-only to avoid _get_config_checksum(name, **kwargs)
    # raising a "duplicated values for 'buildername'" ValueError
    buildername: str,
    /,
    *,
    # The default values must be kept in sync with the constructor
    # default values of :class:`sphinx.testing.util.SphinxTestApp`
    #
    # Note that 'srcdir' and 'builddir' are not used to construct
    # the checksum since otherwise the checksum is unique (and we
    # only want a uniqueness that only depend on common user-defined
    # values). Similarly, 'status' and 'warning' are not used to
    # construct the checksum they are stream objects in general.
    confoverrides: dict[str, Any] | None = None,
    freshenv: bool = False,
    warningiserror: bool = False,
    tags: list[str] | None = None,
    verbosity: int = 0,
    parallel: int = 0,
    keep_going: bool = False,
    # extra constructor argument
    docutils_conf: str | None = None,
    # ignored keyword arguments when computing the checksum
    **_ignored: Any,
) -> int:
    # fmt: off
    return get_objects_checksum(
        buildername, confoverrides=confoverrides, freshenv=freshenv,
        warningiserror=warningiserror, tags=tags, verbosity=verbosity,
        parallel=parallel, keep_going=keep_going,
        # extra constructor arguments
        docutils_conf=docutils_conf,
    )
    # fmt: on


def process_sphinx(
    node: PytestNode,
    session_temp_dir: str | os.PathLike[str],
    testroot_finder: TestRootFinder,
    default_builder: str,
    default_isolation: NormalizableIsolation,
    shared_result: str | None,
) -> tuple[list[Any], SphinxInitKwargs]:
    """Process the :func:`pytest.mark.sphinx` marker.

    :param node: The pytest node to parse.
    :param session_temp_dir: The session temporary directory.
    :param testroot_finder: The testroot finder object.
    :param default_builder: The application default builder name.
    :param default_isolation: The isolation default policy.
    :param shared_result: An optional shared result ID.
    :return: The application positional and keyword arguments.
    """
    # process pytest.mark.sphinx
    env = _get_sphinx_environ(node, default_builder)

    # deduce the testroot ID
    testroot_id = env['testroot'] = env.get('testroot', testroot_finder.default)
    # deduce the srcdir name (possibly explicitly given)
    srcdir_name = env.get('srcdir', None)
    srcdir = _get_test_srcdir(srcdir_name, testroot_id, shared_result)
    is_unique_srcdir_id = srcdir_name is not None

    # deduce the isolation policy from freshenv if possible
    freshenv: bool | None = env.pop('freshenv', None)
    if freshenv is not None:
        if 'isolate' in env:
            err = '%r and %r are mutually exclusive' % ('freshenv', 'isolate')
            pytest.fail(format_mark_failure('sphinx', err))

        isolation = env['isolate'] = Isolation.always if freshenv else default_isolation
    else:
        freshenv = env['freshenv'] = False

    # deduce the final isolation policy
    isolation = is_unique_srcdir_id or env.setdefault('isolate', default_isolation)
    isolation = env['isolate'] = normalize_isolation_policy(isolation)

    # process the srcdir ID according to the isolation policy
    if isolation is Isolation.always and srcdir_name is None:
        # srcdir = XYZ-(RANDOM-UID)
        srcdir = make_unique_id(srcdir)
        is_unique_srcdir_id = True
    elif isolation is Isolation.grouped:
        if (location := get_node_location(node)) is None:
            srcdir = make_unique_id(srcdir)
            is_unique_srcdir_id = True
        else:
            # For a 'grouped' isolation, we want the same prefix (the deduced
            # sources dierctory), but with a unique suffix based on the node
            # location. In particular, parmetrized tests will have the same
            # final ``srcdir`` value as they have the same location.
            suffix = get_location_id(location)
            # srcdir = XYZ-(RANDOM-UID)
            srcdir = f'{srcdir}-{suffix}'

    if is_unique_srcdir_id:
        # when the sources directory is known to be unique across
        # all other tests, we do not include a namespace or checksum
        namespace, checksum = '-', 0
    else:
        namespace = get_container_id(node)
        # Do a somewhat hash on configuration values to give a minimal protection
        # against side-effects (two tests with the same configuration should have
        # the same output; if they mess up with their sources directory, then they
        # should be isolated accordingly). If there is a bug in the test suite, we
        # can reduce the number of tests that can have dependencies by adding some
        # isolation safeguards.
        checksum = _get_common_config_checksum(env['buildername'], **env)

    kwargs = cast(SphinxInitKwargs, env)
    kwargs['srcdir'] = Path(session_temp_dir, namespace, str(checksum), srcdir)
    # ensure that the type of a possible 'builddir' argument is indeed a Path
    kwargs['builddir'] = Path(builddir) if (builddir := env.get('builddir')) else None
    kwargs['testroot_path'] = testroot_finder.find(testroot_id)
    kwargs['shared_result'] = shared_result
    return [], kwargs


def process_test_params(node: PytestNode) -> TestParams:
    """Process the :func:`pytest.mark.test_params` marker.

    :param node: The pytest node to parse.
    :return: The desired keyword arguments.
    """
    ret = TestParams(shared_result=None)
    if (m := node.get_closest_marker('test_params')) is None:
        return ret

    if m.args:
        pytest.fail(format_mark_failure('test_params', 'unexpected positional argument'))

    kwargs, allowed_keywords = m.kwargs, TestParams.__annotations__
    check_mark_keywords('test_params', allowed_keywords, kwargs, node=node, strict=True)

    if (shared_result_id := kwargs.get('shared_result', None)) is None:
        # generate a random shared_result for @pytest.mark.test_params()
        # based on either the location of node (so that it is the same
        # when using @pytest.mark.parametrize())
        if (location := get_node_location(node)) is None:
            shared_result_id = make_unique_id()
        else:
            shared_result_id = get_location_id(location)

    ret['shared_result'] = shared_result_id
    return ret


def process_isolate(node: PytestNode, default: NormalizableIsolation) -> NormalizableIsolation:
    """Process the :func:`pytest.mark.isolate` marker.

    :param node: The pytest node to parse.
    :param default: The default isolation policy given by an external fixture.
    :return: The isolation policy given by the marker.
    """
    # try to find an isolation policy from the 'isolate' marker
    if m := node.get_closest_marker('isolate'):
        # do not allow keyword arguments
        check_mark_keywords('isolate', [], m.kwargs, node=node, strict=True)
        if not m.args:
            # isolate() is equivalent to a full isolation
            return Isolation.always

        if len(m.args) == 1:
            return normalize_isolation_policy(m.args[0])

        err = 'expecting at most one positional argument'
        pytest.fail(format_mark_failure('isolate', err))
    return default
