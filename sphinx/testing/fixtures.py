"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import dataclasses
import itertools
import os
import shutil
import subprocess
import sys
import warnings
from io import StringIO
from typing import TYPE_CHECKING, Optional

import pytest

from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.testing.internal.cache import ModuleCache
from sphinx.testing.internal.isolation import Isolation
from sphinx.testing.internal.markers import (
    AppParams,
    get_location_id,
    process_isolate,
    process_sphinx,
    process_test_params,
)
from sphinx.testing.internal.pytest_util import TestRootFinder, find_context
from sphinx.testing.internal.pytest_xdist import is_pytest_xdist_enabled
from sphinx.testing.util import (
    SphinxTestApp,
    SphinxTestAppLazyBuild, strip_escseq,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from typing import Any, Final

    from sphinx.testing.internal.isolation import IsolationPolicy
    from sphinx.testing.internal.markers import (
        TestParams,
    )

DEFAULT_ENABLED_MARKERS: Final[list[str]] = [
    (
        'sphinx('
        'buildername="html", /, *, '
        'testroot="root", confoverrides=None, '
        'freshenv=None, warningiserror=False, tags=None, '
        'verbosity=0, parallel=0, keep_going=False, '
        'docutils_conf=None, isolate=False'
        '): arguments to initialize the sphinx test application.'
    ),
    'test_params(*, shared_result=None): test configuration.',
    'isolate(policy=None, /): test isolation policy.',
    'sphinx_no_default_xdist(): disable the default xdist-group on tests',
]

###############################################################################
# pytest hooks
###############################################################################


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    if pluginmanager.has_plugin('xdist'):
        from sphinx.testing import _xdist_hooks

        pluginmanager.register(_xdist_hooks, name='sphinx-xdist-hooks')


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if not is_pytest_xdist_enabled(config):
        return

    # *** IMPORTANT ***
    #
    # This hook is executed by every xdist worker and the items
    # are NOT shared across those workers. In particular, it is
    # crucial that the xdist-group that we define later is the
    # same across ALL workers. In other words, the group can
    # only depend on xdist-agnostic data such as the physical
    # location of a test item.
    #
    # In addition, custom plugins that can change the meaning
    # of ``@pytest.mark.parametrize`` might break this plugin,
    # so use them carefully!

    for item in items:
        if (
            item.get_closest_marker('parametrize')
            and item.get_closest_marker('sphinx_no_default_xdist') is None
        ):
            fspath, lineno, _ = item.location  # this is xdist-agnostic
            xdist_group = get_location_id((fspath, lineno or -1))
            item.add_marker(pytest.mark.xdist_group(xdist_group), append=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: pytest.Item) -> Generator[None, None, None]:
    yield  # execute the fixtures teardowns

    # after tearing down the fixtures, we add some report sections
    # for later; without ``xdist``, we would have printed whatever
    # we wanted during the fixture teardown but since ``xdist`` is
    # not print-friendly, we must use the report sections

    if _APP_INFO_KEY in item.stash:
        info: _AppInfo = item.stash[_APP_INFO_KEY]
        del item.stash[_APP_INFO_KEY]

        text = info.render()

        if (
            # do not duplicate the report info when using -rA
            'A' not in item.config.option.reportchars
            and (item.config.option.capture == 'no' or item.config.get_verbosity() >= 2)
            # see: https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html
            and not is_pytest_xdist_enabled(item.config)
        ):
            # use carriage returns to avoid being printed inside the progression bar
            # and additionally show the node ID for visual purposes
            if os.name == 'nt':
                text = strip_escseq(text)
            print('\n\n', f'[{item.nodeid}]', '\n', text, sep='', end='')  # NoQA: T201

        item.add_report_section(f'teardown [{item.nodeid}]', 'fixture %r' % 'app', text)

###############################################################################
# sphinx fixtures
###############################################################################


@pytest.fixture(scope='session')
def sphinx_test_tempdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Fixture for a temporary directory."""
    return tmp_path_factory.getbasetemp()


@pytest.fixture()
def sphinx_builder(request: pytest.FixtureRequest) -> str:
    """Fixture for the default builder name."""
    return getattr(request, 'param', 'html')


@pytest.fixture()
def sphinx_isolation() -> IsolationPolicy:
    """Fixture for the default isolation policy.

    This fixture is ignored when using the legacy plugin.
    """
    return False


@pytest.fixture()
def rootdir() -> str | os.PathLike[str] | None:
    """Fixture for the directory containing the testroot directories."""
    return None


@pytest.fixture()
def testroot_prefix() -> str | None:
    """Fixture for the testroot directories prefix.

    This fixture is ignored when using the legacy plugin.
    """
    return 'test-'


@pytest.fixture()
def default_testroot() -> str | None:
    """Dynamic fixture for the default testroot ID.

    This fixture is ignored when using the legacy plugin.
    """
    return 'root'


@pytest.fixture()
def testroot_finder(
    rootdir: str | os.PathLike[str] | None,
    testroot_prefix: str | None,
    default_testroot: str | None,
) -> TestRootFinder:
    """Fixture for the testroot finder object."""
    return TestRootFinder(rootdir, testroot_prefix, default_testroot)


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


@pytest.fixture()
def app_params(
    request: pytest.FixtureRequest,
    test_params: TestParams,
    module_cache: ModuleCache,
    sphinx_test_tempdir: Path,
    sphinx_builder: str,
    sphinx_isolation: IsolationPolicy,
    testroot_finder: TestRootFinder,
) -> AppParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
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


@pytest.fixture()
def test_params(request: pytest.FixtureRequest) -> TestParams:
    """Test parameters that are specified by ``pytest.mark.test_params``."""
    return process_test_params(request.node)


@dataclasses.dataclass
class _AppInfo:
    """Report to render at the end of a test using the :func:`app` fixture."""

    builder: str
    """The builder name."""

    testroot_path: str | None
    """The absolute path to the sources directory (if any)."""
    shared_result: str | None
    """The user-defined shared result (if any)."""

    srcdir: str
    """The absolute path to the application's sources directory."""
    outdir: str
    """The absolute path to the application's output directory."""

    # fields below are updated when tearing down :func:`app`
    # or requesting :func:`app_test_info` (only *extras* is
    # publicly exposed by the latter)

    messages: str = dataclasses.field(default='', init=False)
    """The application's status messages."""
    warnings: str = dataclasses.field(default='', init=False)
    """The application's warnings messages."""
    extras: dict[str, Any] = dataclasses.field(default_factory=dict, init=False)
    """Attributes added by :func:`sphinx.testing.plugin.app_test_info`."""

    def render(self) -> str:
        """Format the report as a string to print or render."""
        config = [('builder', self.builder)]
        if self.testroot_path:
            config.append(('testroot path', self.testroot_path))
        config.extend([('srcdir', self.srcdir), ('outdir', self.outdir)])
        config.extend((name, repr(value)) for name, value in self.extras.items())

        tw, _ = shutil.get_terminal_size()
        kw = 8 + max(len(name) for name, _ in config)

        lines = itertools.chain(
            [f'{" configuration ":-^{tw}}'],
            (f'{name:{kw}s} {strvalue}' for name, strvalue in config),
            [f'{" messages ":-^{tw}}', text] if (text := self.messages) else (),
            [f'{" warnings ":-^{tw}}', text] if (text := self.warnings) else (),
            ['=' * tw],
        )
        return '\n'.join(lines)


_APP_INFO_KEY: pytest.StashKey[_AppInfo] = pytest.StashKey()


def _get_app_info(
    request: pytest.FixtureRequest,
    app: SphinxTestApp,
    app_params: AppParams,
) -> _AppInfo:
    # request.node.stash is not typed correctly in pytest
    stash: pytest.Stash = request.node.stash
    if _APP_INFO_KEY not in stash:
        stash[_APP_INFO_KEY] = _AppInfo(
            builder=app.builder.name,
            testroot_path=app_params.kwargs['testroot_path'],
            shared_result=app_params.kwargs['shared_result'],
            srcdir=os.fsdecode(app.srcdir),
            outdir=os.fsdecode(app.outdir),
        )
    return stash[_APP_INFO_KEY]


@pytest.fixture()
def app_info_extras(
    request: pytest.FixtureRequest,
    # ``app`` is not used but is marked as a dependency
    app: SphinxTestApp,
    # ``app_params`` is already a dependency of ``app``
    app_params: AppParams,
) -> dict[str, Any]:
    """Fixture to update the information to render at the end of a test.

    Use this fixture in a ``conftest.py`` file or in a test file as follows::

        @pytest.fixture(autouse=True)
        def _add_app_info_extras(app, app_info_extras):
            app_info_extras.update(my_extra=1234)
            app_info_extras.update(app_extras=app.extras)
    """
    app_info = _get_app_info(request, app, app_params)
    return app_info.extras


@pytest.fixture()
def app(
    request: pytest.FixtureRequest,
    app_params: AppParams,
    make_app: Callable[..., SphinxTestApp],
    module_cache: ModuleCache,
) -> Generator[SphinxTestApp, None, None]:
    """A :class:`sphinx.application.Sphinx` object suitable for testing."""
    # the 'app_params' fixture already depends on the 'test_result' fixture
    shared_result = app_params.kwargs['shared_result']
    app = make_app(*app_params.args, **app_params.kwargs)
    yield app

    info = _get_app_info(request, app, app_params)
    # update the messages accordingly
    info.messages = app.status.getvalue()
    info.warnings = app.warning.getvalue()

    if shared_result is not None:
        module_cache.store(shared_result, app)


@pytest.fixture()
def status(app: SphinxTestApp) -> StringIO:
    """Fixture for the :func:`~sphinx.testing.plugin.app` status stream."""
    return app.status


@pytest.fixture()
def warning(app: SphinxTestApp) -> StringIO:
    """Fixture for the :func:`~sphinx.testing.plugin.app` warning stream."""
    return app.warning


@pytest.fixture()
def make_app(test_params: TestParams) -> Generator[Callable[..., SphinxTestApp], None, None]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects."""
    stack: list[SphinxTestApp] = []
    allow_rebuild = test_params['shared_result'] is None

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        if allow_rebuild:
            app = SphinxTestApp(*args, **kwargs)
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


@pytest.fixture()
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


@pytest.fixture()
def if_graphviz_found(app: SphinxTestApp) -> None:  # NoQA: PT004
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


@pytest.fixture()
def rollback_sysmodules() -> Generator[None, None, None]:  # NoQA: PT004
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
###############################################################################


# XXX: RemovedInSphinx90Warning
class SharedResult:
    cache: dict[str, dict[str, str]] = {}

    def __init__(self) -> None:
        warnings.warn("this object is deprecated and will be removed in the future",
                      RemovedInSphinx90Warning, stacklevel=2)

    def store(self, key: str, app_: SphinxTestApp) -> Any:
        if key in self.cache:
            return
        data = {
            'status': app_.status.getvalue(),
            'warning': app_.warning.getvalue(),
        }
        self.cache[key] = data

    def restore(self, key: str) -> dict[str, StringIO]:
        if key not in self.cache:
            return {}
        data = self.cache[key]
        return {
            'status': StringIO(data['status']),
            'warning': StringIO(data['warning']),
        }


@pytest.fixture()
def shared_result() -> SharedResult:
    warnings.warn("this fixture is deprecated; use 'module_cache' instead",
                  RemovedInSphinx90Warning, stacklevel=2)
    return SharedResult()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache() -> None:
    # XXX: RemovedInSphinx90Warning
    SharedResult.cache.clear()
