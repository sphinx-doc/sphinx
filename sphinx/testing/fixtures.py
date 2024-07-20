"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, cast

import pytest

from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.testing._internal.cache import AppInfo, LegacyModuleCache, ModuleCache
from sphinx.testing._internal.isolation import Isolation
from sphinx.testing._internal.markers import (
    AppLegacyParams,
    AppParams,
    process_isolate,
    process_sphinx,
    process_test_params,
)
from sphinx.testing._internal.pytest_util import (
    TestRootFinder,
    find_context,
    get_mark_parameters,
)
from sphinx.testing._internal.pytest_xdist import is_pytest_xdist_enabled
from sphinx.testing.util import (
    SphinxTestApp,
    SphinxTestAppLazyBuild,
    SphinxTestAppWrapperForSkipBuilding,
)
from sphinx.util.console import strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Iterator
    from io import StringIO
    from pathlib import Path
    from typing import Any, Final, Union

    from _pytest.nodes import Node as PytestNode

    from sphinx.testing._internal.isolation import IsolationPolicy
    from sphinx.testing._internal.markers import TestParams

    AnySphinxTestApp = Union[SphinxTestApp, SphinxTestAppWrapperForSkipBuilding]
    AnyAppParams = Union[AppParams, AppLegacyParams]

DEFAULT_ENABLED_MARKERS: Final[list[str]] = [
    # The marker signature differs from the constructor signature
    # since the way it is processed assumes keyword arguments for
    # the 'testroot' and 'srcdir'. In addition, 'freshenv' and
    # 'isolate' are mutually exclusive arguments (and the latter
    # is recommended over the former).
    (
        'sphinx('
        'buildername="html", *, '
        'testroot="root", srcdir=None, '
        'confoverrides=None, freshenv=None, '
        'warningiserror=False, tags=None, verbosity=0, parallel=0, '
        'keep_going=False, builddir=None, docutils_conf=None, '
        'isolate=False'
        '): arguments to initialize the sphinx test application.'
    ),
    'test_params(*, shared_result=None): test configuration.',
    'isolate(policy=None, /): test isolation policy.',
    'sphinx_no_default_xdist(): disable the default xdist-group on tests',
]


###############################################################################
# pytest hooks
#
# *** IMPORTANT ***
#
# The hooks must be compatible with the legacy plugin until Sphinx 9.x.
###############################################################################


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    if pluginmanager.has_plugin('xdist'):
        from sphinx.testing import _xdist_hooks

        # the legacy plugin does not really care about this plugin
        # since it only depends on 'xdist' and not on sphinx itself
        pluginmanager.register(_xdist_hooks, name='sphinx-xdist-hooks')


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.hookimpl()
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> pytest.TestReport | None:
    if call.when != 'teardown' or _APP_INFO_KEY not in item.stash:
        return None

    # handle the delayed test report when using xdist
    info = item.stash[_APP_INFO_KEY]
    text = _cleanup_app_info(info.render(nodeid=item.nodeid))
    item.add_report_section(call.when, 'fixture: %r' % 'app', text)
    return pytest.TestReport.from_item_and_call(item, call)


###############################################################################
# sphinx fixtures
###############################################################################


@pytest.fixture
def sphinx_use_legacy_plugin() -> bool:  # xref RemovedInSphinx90Warning
    """If true, use the legacy implementation of fixtures.

    Redefine this fixture in ``conftest.py`` or at the test level to use
    the new plugin implementation (note that the test code might require
    changes). By default, the new implementation is disabled so that no
    breaking changes occur outside of Sphinx itself.
    """
    return True


@pytest.fixture(scope='session')
def sphinx_test_tempdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Fixture for a temporary directory."""
    return tmp_path_factory.getbasetemp()


@pytest.fixture
def sphinx_builder(request: pytest.FixtureRequest) -> str:
    """Fixture for the default builder name."""
    return getattr(request, 'param', 'html')


@pytest.fixture
def sphinx_isolation() -> IsolationPolicy:
    """Fixture for the default isolation policy.

    This fixture is ignored when using the legacy plugin.
    """
    return False


@pytest.fixture
def rootdir() -> str | os.PathLike[str] | None:
    """Fixture for the directory containing the testroot directories."""
    return None


@pytest.fixture
def testroot_prefix() -> str | None:
    """Fixture for the testroot directories prefix.

    This fixture is ignored when using the legacy plugin.
    """
    return 'test-'


@pytest.fixture
def default_testroot() -> str | None:
    """Dynamic fixture for the default testroot ID.

    This fixture is ignored when using the legacy plugin.
    """
    return 'root'


@pytest.fixture
def testroot_finder(
    rootdir: str | os.PathLike[str] | None,
    testroot_prefix: str | None,
    default_testroot: str | None,
) -> TestRootFinder:
    """Fixture for the testroot finder object."""
    return TestRootFinder(rootdir, testroot_prefix, default_testroot)


###############################################################################
# fixture: app_params()
###############################################################################


def _init_sources(src: str | None, dst: Path, isolation: Isolation) -> None:
    if src is None or dst.exists():
        return

    if not os.path.exists(src):
        pytest.fail(f'no sources found at: {src!r}')

    # make a copy of the testroot
    shutil.copytree(src, dst)

    # make the files read-only if isolation is not specified
    # to protect the tests against some side-effects (not all
    # side-effects will be prevented)
    if isolation is Isolation.minimal:
        for dirpath, _, filenames in os.walk(dst):
            for filename in filenames:
                os.chmod(os.path.join(dirpath, filename), 0o444)


def __app_params_fixture(
    request: pytest.FixtureRequest,
    test_params: TestParams,
    module_cache: ModuleCache,
    sphinx_test_tempdir: Path,
    sphinx_builder: str,
    sphinx_isolation: IsolationPolicy,
    testroot_finder: TestRootFinder,
) -> AppParams:
    default_isolation = process_isolate(request.node, sphinx_isolation)
    shared_result_id = test_params['shared_result']
    args, kwargs = process_sphinx(
        request.node,
        session_temp_dir=sphinx_test_tempdir,
        testroot_finder=testroot_finder,
        default_builder=sphinx_builder,
        default_isolation=default_isolation,
        shared_result=shared_result_id,
    )
    assert shared_result_id == kwargs['shared_result']
    # restore the I/O stream values
    if shared_result_id and (frame := module_cache.restore(shared_result_id)):
        if kwargs.setdefault('status', frame['status']) is not frame['status']:
            fmt = 'cannot use %r when %r is explicitly given'
            pytest.fail(fmt % ('shared_result', 'status'))
        if kwargs.setdefault('warning', frame['warning']) is not frame['warning']:
            fmt = 'cannot use %r when %r is explicitly given'
            pytest.fail(fmt % ('shared_result', 'warning'))

    # copy the testroot files to the test sources directory
    _init_sources(kwargs['testroot_path'], kwargs['srcdir'], kwargs['isolate'])
    return AppParams(args, kwargs)


@pytest.fixture
def app_params(
    request: pytest.FixtureRequest,
    test_params: TestParams,
    module_cache: ModuleCache,
    shared_result: LegacyModuleCache,  # xref RemovedInSphinx90Warning
    sphinx_test_tempdir: Path,
    sphinx_builder: str,
    sphinx_isolation: IsolationPolicy,
    testroot_finder: TestRootFinder,
    sphinx_use_legacy_plugin: bool,  # xref RemovedInSphinx90Warning
) -> AppParams | AppLegacyParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    if sphinx_use_legacy_plugin:
        msg = ('legacy implementation of sphinx.testing.fixtures is '
               'deprecated; consider redefining sphinx_use_legacy_plugin() '
               'in conftest.py to return False.')
        warnings.warn(msg, RemovedInSphinx90Warning, stacklevel=2)
        return __app_params_fixture_legacy(
            request, test_params, shared_result,
            sphinx_test_tempdir, testroot_finder.path,
        )

    return __app_params_fixture(
        request, test_params, module_cache,
        sphinx_test_tempdir, sphinx_builder,
        sphinx_isolation, testroot_finder,
    )


###############################################################################
# fixture: test_params()
###############################################################################


@pytest.fixture
def test_params(request: pytest.FixtureRequest) -> TestParams:
    """Test parameters that are specified by ``pytest.mark.test_params``.

    This ``pytest.mark.test_params`` marker takes an optional keyword argument,
    namely the *shared_result*, which is a string, e.g.::

        def test_no_shared_result(test_params):
            assert test_params['shared_result'] is None

        @pytest.mark.test_params()
        def test_with_random_shared_result(test_params):
            assert test_params['shared_result'] == 'some-random-string'

        @pytest.mark.test_params(shared_result='foo')
        def test_with_explicit_shared_result(test_params):
            assert test_params['shared_result'] == 'foo'

    If the *shared_result* is provided, the ``app.status`` and ``app.warning``
    objects will be shared in the test functions, possibly parametrized, that
    have the same *shared_result* value.

    .. note::

       The *srcdir* parameter of the ``@pytest.mark.sphinx()`` marker and
       the *shared_result* parameter of the ``@pytest.mark.test_params()``
       marker are mutually exclusive.
    """
    return process_test_params(request.node)


###############################################################################
# fixture: app()
###############################################################################


_APP_INFO_KEY: pytest.StashKey[AppInfo] = pytest.StashKey()


def _cleanup_app_info(text: str) -> str:
    if os.name == 'nt':
        text = strip_escape_sequences(text)
        text = text.encode('ascii', errors='backslashreplace').decode('ascii')
    return text


@contextlib.contextmanager
def _app_info_context(
    node: PytestNode,
    app: SphinxTestApp,
    app_params: AppParams,
) -> Iterator[None]:
    # create or get the current :class:`AppInfo` object of the node
    if _APP_INFO_KEY not in node.stash:
        node.stash[_APP_INFO_KEY] = AppInfo(
            builder=app.builder.name,
            testroot_path=app_params.kwargs['testroot_path'],
            shared_result=app_params.kwargs['shared_result'],
            srcdir=os.fsdecode(app.srcdir),
            outdir=os.fsdecode(app.outdir),
        )

    app_info = node.stash[_APP_INFO_KEY]
    yield
    app_info.update(app)

    if not is_pytest_xdist_enabled(node.config) and node.config.option.capture == 'no':
        # With xdist, we will print at the test the information but only
        # if it is being used with '-s', which has no effect when used by
        # xdist since the latter does not support capturing.
        #
        #
        # In addition, use CRLF to avoid being printed inside the
        # progression bar (note that we need to render it here so
        # that the terminal width is correctly determined).
        text = app_info.render(nodeid=node.nodeid)
        print('\n', _cleanup_app_info(text), sep='', end='')  # NoQA: T201


@pytest.fixture
def app_info_extras(
    request: pytest.FixtureRequest,
    # ``app`` is not used but is marked as a dependency so that
    # the AppInfo() object is automatically created for *app*
    app: AnySphinxTestApp,  # xref RemovedInSphinx90Warning: update type
    sphinx_use_legacy_plugin: bool,  # xref RemovedInSphinx90Warning
) -> dict[str, Any]:
    """Fixture to update the information to render at the end of a test.

    Use this fixture in a ``conftest.py`` file or in a test file as follows::

        @pytest.fixture(autouse=True)
        def _add_app_info_extras(app, app_info_extras):
            app_info_extras.update(my_extra=1234)
            app_info_extras.update(app_extras=app.extras)

    .. note::

       This fixture is only available if :func:`sphinx_use_legacy_plugin` is
       configured to return ``False`` (i.e., the legacy plugin is disabled).
    """
    # xref RemovedInSphinx90Warning: remove the assert
    assert not sphinx_use_legacy_plugin, 'legacy plugin does not support this fixture'
    assert _APP_INFO_KEY in request.node.stash
    return request.node.stash[_APP_INFO_KEY].extras


def __app_fixture(
    request: pytest.FixtureRequest,
    app_params: AppParams,
    make_app: Callable[..., SphinxTestApp],
    module_cache: ModuleCache,
) -> Iterator[SphinxTestApp]:
    shared_result = app_params.kwargs['shared_result']

    app = make_app(*app_params.args, **app_params.kwargs)
    with _app_info_context(request.node, app, app_params):
        yield app

    if shared_result is not None:
        module_cache.store(shared_result, app)


@pytest.fixture
def app(
    request: pytest.FixtureRequest,
    app_params: AnyAppParams,  # xref RemovedInSphinx90Warning: update type
    test_params: TestParams,  # xref RemovedInSphinx90Warning
    make_app: Callable[..., AnySphinxTestApp],  # xref RemovedInSphinx90Warning: update type
    module_cache: ModuleCache,
    shared_result: LegacyModuleCache,  # xref RemovedInSphinx90Warning
    sphinx_use_legacy_plugin: bool,  # xref RemovedInSphinx90Warning
) -> Iterator[AnySphinxTestApp]:  # xref RemovedInSphinx90Warning: update type
    """A :class:`sphinx.application.Sphinx` object suitable for testing."""
    if sphinx_use_legacy_plugin:  # xref RemovedInSphinx90Warning
        # a warning will be emitted by the app_params fixture
        app_params = cast(AppLegacyParams, app_params)
        fixt = __app_fixture_legacy(request, app_params, test_params, make_app, shared_result)
    else:
        # xref RemovedInSphinx90Warning: remove the cast
        app_params = cast(AppParams, app_params)
        make_app = cast(Callable[..., SphinxTestApp], make_app)
        fixt = __app_fixture(request, app_params, make_app, module_cache)

    yield from fixt
    return

###############################################################################
# other fixtures
###############################################################################


@pytest.fixture
def status(app: AnySphinxTestApp) -> StringIO:  # xref RemovedInSphinx90Warning: narrow type
    """Fixture for the :func:`~sphinx.testing.plugin.app` status stream."""
    return app.status


@pytest.fixture
def warning(app: AnySphinxTestApp) -> StringIO:  # xref RemovedInSphinx90Warning: narrow type
    """Fixture for the :func:`~sphinx.testing.plugin.app` warning stream."""
    return app.warning


@pytest.fixture
def make_app(
    test_params: TestParams,
    sphinx_use_legacy_plugin: bool,  # xref RemovedInSphinx90Warning
    # xref RemovedInSphinx90Warning: narrow callable return type
) -> Iterator[Callable[..., AnySphinxTestApp]]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects."""
    stack: list[SphinxTestApp] = []
    allow_rebuild = test_params['shared_result'] is None

    # xref RemovedInSphinx90Warning: narrow return type
    def make(*args: Any, **kwargs: Any) -> AnySphinxTestApp:
        if allow_rebuild:
            app = SphinxTestApp(*args, **kwargs)
        else:
            if sphinx_use_legacy_plugin:  # xref RemovedInSphinx90Warning
                subject = SphinxTestApp(*args, **kwargs)

                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=RemovedInSphinx90Warning)
                    app = SphinxTestAppWrapperForSkipBuilding(subject)  # type: ignore[assignment]  # NoQA: E501
            else:
                app = SphinxTestAppLazyBuild(*args, **kwargs)
        stack.append(app)
        return app

    syspath = sys.path.copy()
    yield make
    sys.path[:] = syspath

    while stack:
        stack.pop().cleanup()


_MODULE_CACHE_STASH_KEY: pytest.StashKey[ModuleCache] = pytest.StashKey()


@pytest.fixture
def module_cache(request: pytest.FixtureRequest) -> ModuleCache:
    """A :class:`ModuleStorage` object."""
    module = find_context(request.node, 'module')
    return module.stash.setdefault(_MODULE_CACHE_STASH_KEY, ModuleCache())


@pytest.fixture(scope='module', autouse=True)
def _module_cache_clear(request: pytest.FixtureRequest) -> None:
    """Cleanup the shared result cache for the test module.

    This fixture is automatically invoked.
    """
    module = find_context(request.node, 'module')
    cache = module.stash.get(_MODULE_CACHE_STASH_KEY, None)
    if cache is not None:
        cache.clear()


@pytest.fixture
# xref RemovedInSphinx90Warning: update type
def if_graphviz_found(app: AnySphinxTestApp) -> None:  # NoQA: PT004
    """
    The test will be skipped when using 'if_graphviz_found' fixture and graphviz
    dot command is not found.
    """
    graphviz_dot = getattr(app.config, 'graphviz_dot', '')
    try:
        if graphviz_dot:
            # print the graphviz_dot version, to check that the binary is available
            subprocess.run([graphviz_dot, '-V'], capture_output=True, check=False)
            return
    except OSError:  # No such file or directory
        pass

    pytest.skip('graphviz "dot" is not available')


_HOST_ONLINE_ERROR = pytest.StashKey[Optional[str]]()


def _query(address: tuple[str, int]) -> str | None:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(5)
            sock.connect(address)
        except OSError as exc:
            # other type of errors are propagated
            return str(exc)
        return None


@pytest.fixture(scope='session')
def sphinx_remote_query_address() -> tuple[str, int]:
    """Address to which a query is made to check that the host is online.

    By default, onlineness is tested by querying the DNS server ``1.1.1.1``
    but users concerned about privacy might change it in ``conftest.py``.
    """
    return ('1.1.1.1', 80)


@pytest.fixture(scope='session')
def if_online(  # NoQA: PT004
    request: pytest.FixtureRequest,
    sphinx_remote_query_address: tuple[str, int],
) -> None:
    """Skip the test if the host has no connection.

    Usage::

        @pytest.mark.usefixtures('if_online')
        def test_if_host_is_online(): ...
    """
    if _HOST_ONLINE_ERROR not in request.session.stash:
        # do not use setdefault() to avoid creating a socket connection
        lookup_error = _query(sphinx_remote_query_address)
        request.session.stash[_HOST_ONLINE_ERROR] = lookup_error
    if (error := request.session.stash[_HOST_ONLINE_ERROR]) is not None:
        pytest.skip('host appears to be offline (%s)' % error)


@pytest.fixture
def rollback_sysmodules() -> Iterator[None]:  # NoQA: PT004
    """
    Rollback sys.modules to its value before testing to unload modules
    during tests.

    For example, used in test_ext_autosummary.py to permit unloading the
    target module to clear its cache.
    """
    sysmodules = frozenset(sys.modules)
    try:
        yield
    finally:
        for modname in list(sys.modules):
            if modname not in sysmodules:
                sys.modules.pop(modname)


###############################################################################
# sphinx deprecated fixtures
#
# Once we are in version 9.x, we can remove the private implementations
# and clean-up the fixtures so that they use a single implementation.
###############################################################################


def __app_params_fixture_legacy(  # xref RemovedInSphinx90Warning
    request: pytest.FixtureRequest,
    test_params: TestParams,
    shared_result: LegacyModuleCache,
    sphinx_test_tempdir: Path,
    rootdir: str | os.PathLike[str] | None,
) -> AppLegacyParams:
    """
    Parameters that are specified by 'pytest.mark.sphinx' for
    sphinx.application.Sphinx initialization
    """
    # ##### process pytest.mark.sphinx
    args, kwargs = get_mark_parameters(request.node, 'sphinx')

    # ##### process pytest.mark.test_params
    if test_params['shared_result']:
        if 'srcdir' in kwargs:
            msg = 'You can not specify shared_result and srcdir in same time.'
            pytest.fail(msg)
        kwargs['srcdir'] = test_params['shared_result']
        restore = shared_result.restore(test_params['shared_result'])
        kwargs.update(restore)

    testroot = kwargs.pop('testroot', 'root')
    kwargs['srcdir'] = srcdir = sphinx_test_tempdir / kwargs.get('srcdir', testroot)

    # special support for sphinx/tests
    if rootdir and not srcdir.exists():
        testroot_path = os.path.join(rootdir, 'test-' + testroot)
        shutil.copytree(testroot_path, srcdir)

    return AppLegacyParams(args, kwargs)


def __app_fixture_legacy(  # xref RemovedInSphinx90Warning
    request: pytest.FixtureRequest,
    app_params: AppLegacyParams,
    test_params: TestParams,
    make_app: Callable[..., AnySphinxTestApp],
    shared_result: LegacyModuleCache,
) -> Iterator[AnySphinxTestApp]:
    app = make_app(*app_params.args, **app_params.kwargs)
    yield app

    print('# testroot:', app_params.kwargs.get('testroot', 'root'))
    print('# builder:', app.builder.name)
    print('# srcdir:', app.srcdir)
    print('# outdir:', app.outdir)
    print('# status:', '\n' + app.status.getvalue())
    print('# warning:', '\n' + app.warning.getvalue())

    if test_params['shared_result']:
        shared_result.store(test_params['shared_result'], app)


@pytest.fixture
def shared_result(  # xref RemovedInSphinx90Warning
    request: pytest.FixtureRequest,
    sphinx_use_legacy_plugin: bool,
) -> LegacyModuleCache:
    if (
        not {'app', 'app_params'}.intersection(request.fixturenames)
        and not sphinx_use_legacy_plugin
    ):
        # warn a direct usage of this fixture
        warnings.warn("this fixture is deprecated", RemovedInSphinx90Warning, stacklevel=2)
    return LegacyModuleCache()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache() -> None:  # xref RemovedInSphinx90Warning
    LegacyModuleCache.cache.clear()


SharedResult = LegacyModuleCache  # xref RemovedInSphinx90Warning
