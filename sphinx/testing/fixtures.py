"""Sphinx test fixtures for pytest.

See the development guide for documentation.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import warnings
from io import StringIO
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.testing._fixtures import (
    AppParams,
    TestParams,
    add_sphinx_xdist_prefix,
    get_app_params,
    get_test_params,
)
from sphinx.testing.pytest_util import (
    TestRootFinder,
    get_context_node,
    get_stashed,
    is_pytest_xdist_enabled,
    set_pytest_xdist_group,
    stash_default_value,
)
from sphinx.testing.util import SphinxTestApp, SphinxTestAppLazyBuild

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from typing import Any

    from sphinx.testing._fixtures import IsolationPolicy


class _EmptyDict(TypedDict):
    pass


class _CacheItem(TypedDict):
    status: str
    warning: str


class _CacheView(TypedDict):
    status: StringIO
    warning: StringIO


DEFAULT_ENABLED_MARKERS = [
    (
        'sphinx('
        'buildername="html", *, '
        'srcdir=None, testroot="root", confoverrides=None, '
        'freshenv=False, warningiserror=False, tags=None, '
        'verbosity=0, parallel=0, keep_going=False, '
        'builddir=None, docutils_conf=None, '
        'isolate=False): arguments to initialize the sphinx test application.'
    ),
    'test_params(shared_result=None): test configuration.',
    'isolate(policy=None, /): test isolation policy.',
]


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Make the Sphinx fixtures compatible with ``pytest-xdist``.

    By default, xdist execu
    """
    if not is_pytest_xdist_enabled(config):
        return

    for item in items:
        if item.get_closest_marker('xdist_group') is None:
            group = add_sphinx_xdist_prefix(item.path.stem)
            set_pytest_xdist_group(item, group)


@pytest.fixture(scope='session')
def sphinx_test_tempdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Fixture for a temporary directory."""
    return tmp_path_factory.getbasetemp()


@pytest.fixture()
def sphinx_builder(request: pytest.FixtureRequest) -> str:
    """Fixture for the default builder name."""
    # use suppress instead of getattr() to keep autocompletion
    with contextlib.suppress(AttributeError):
        return request.param
    return 'html'


@pytest.fixture()
def sphinx_isolation(request: pytest.FixtureRequest) -> IsolationPolicy | None:
    """Fixture for the default isolation policy."""
    with contextlib.suppress(AttributeError):
        return request.param
    return False


@pytest.fixture()
def rootdir(request: pytest.FixtureRequest) -> str | os.PathLike[str] | None:
    """Fixture for the directory containing the testroot directories."""
    with contextlib.suppress(AttributeError):
        return request.param
    return None


@pytest.fixture()
def testroot_prefix(request: pytest.FixtureRequest) -> str | None:
    """Fixture for the testroot directories prefix."""
    with contextlib.suppress(AttributeError):
        return request.param
    return 'test-'


@pytest.fixture()
def default_testroot(request: pytest.FixtureRequest) -> str | None:
    """Dynamic fixture for the default testroot ID."""
    with contextlib.suppress(AttributeError):
        return request.param
    return 'root'


@pytest.fixture()
def testroot_finder(
    rootdir: str | os.PathLike[str] | None,
    testroot_prefix: str | None,
    default_testroot: str | None,
) -> TestRootFinder:
    """Fixture for the testroot finder object."""
    return TestRootFinder(rootdir, testroot_prefix, default_testroot)


class SharedResult:
    __slots__ = ('group', 'cache')

    def __init__(self, group: str | None = None) -> None:
        self.group = group
        self.cache: dict[str, _CacheItem] = {}

    def clear(self) -> None:
        self.cache.clear()

    def store(self, key: str, app: SphinxTestApp) -> None:
        if key not in self.cache:
            status, warning = app.status.getvalue(), app.warning.getvalue()
            self.cache[key] = {'status': status, 'warning': warning}

    def restore(self, key: str) -> _EmptyDict | _CacheView:
        if key not in self.cache:
            return {}

        data = self.cache[key]
        return {'status': StringIO(data['status']), 'warning': StringIO(data['warning'])}


@pytest.fixture()
def app_params(
    request: pytest.FixtureRequest,
    test_params: TestParams,
    shared_result: SharedResult,
    # the value of the fixtures below can be defined at the test file level
    sphinx_test_tempdir: Path,
    testroot_finder: TestRootFinder,
    sphinx_builder: str,
    sphinx_isolation: IsolationPolicy | None,
) -> AppParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    if m := request.node.get_closest_marker('isolate'):
        # isolate() is equivalent to isolate('always')
        sphinx_isolation = m.args[0] if m.args else True

    shared_result_id = test_params['shared_result']
    args, kwargs = get_app_params(
        request.node,
        session_temp_dir=sphinx_test_tempdir,
        testroot_finder=testroot_finder,
        default_builder=sphinx_builder,
        default_isolation=sphinx_isolation,
        shared_result=shared_result_id,
    )
    assert shared_result_id == kwargs['shared_result']

    # restore the I/O stream values
    if shared_result_id and (
        shared := cast(_CacheView, shared_result.restore(shared_result_id))
    ):
        if kwargs.setdefault('status', shared['status']) is not shared['status']:
            pytest.fail('cannot use "shared_result" when "status" is explicitly given')
        if kwargs.setdefault('warning', shared['warning']) is not shared['warning']:
            pytest.fail('cannot use "shared_result" when "warning" is explicitly given')

    # copy the testroot files to the test sources directory
    srcdir, sources = kwargs['srcdir'], kwargs['testroot_path']
    if sources is not None and not srcdir.exists():
        if not os.path.exists(sources):
            pytest.fail(f'testroot does not exist: {sources}')
        shutil.copytree(sources, srcdir)

    return AppParams(args, kwargs)


@pytest.fixture()
def test_params(request: pytest.FixtureRequest) -> TestParams:
    """Test parameters that are specified by ``pytest.mark.test_params``."""
    return get_test_params(request.node)


@pytest.fixture()
def app(
    request: pytest.FixtureRequest,
    app_params: AppParams,
    test_params: TestParams,
    shared_result: SharedResult,
    make_app: Callable[..., SphinxTestApp],
) -> Generator[SphinxTestApp, None, None]:
    """A :class:`sphinx.application.Sphinx` object suitable for testing."""
    shared_result_id = test_params['shared_result']
    assert test_params['shared_result'] == app_params.kwargs['shared_result']
    app = make_app(*app_params.args, **app_params.kwargs)
    yield app

    print('# builder:', app.builder.name)
    print('# sources:', app_params.kwargs['testroot_path'])
    if shared_result_id is not None:
        print('# shared in:', shared_result.group)
        print('# shared id:', shared_result_id)

    print('# srcdir:', app.srcdir)
    print('# outdir:', app.outdir)
    print('# status:', '\n' + app.status.getvalue())
    print('# warning:', '\n' + app.warning.getvalue())

    if shared_result_id is not None:
        shared_result.store(shared_result_id, app)


@pytest.fixture()
def status(app: SphinxTestApp) -> StringIO:
    """Fixture for the :func:`~sphinx.testing.fixtures.app` status stream."""
    return app.status


@pytest.fixture()
def warning(app: SphinxTestApp) -> StringIO:
    """Fixture for the :func:`~sphinx.testing.fixtures.app` warning stream."""
    return app.warning


@pytest.fixture()
def make_app(test_params: TestParams) -> Generator[Callable[..., SphinxTestApp], None, None]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed arguments.

    Use this fixture to create an :class:`~sphinx.testing.util.SphinxTestApp`
    object instead of directly calling its constructor::

        def test(make_app):
            args, kwargs = ...
            app = make_app(*args, **kwargs)

    Use :func:`pytest.mark.sphinx` together with *app_params* to configure the
    arguments passed to the factory instead of constructing them manually::

        @pytest.mark.sphinx(isolate=True)
        def test(app_params, make_app):
            args, kwargs = app_params
            app = make_app(*args, **kwargs)

    In the above example, the keyword arguments are constructed according
    to ``isolate=True`` and thus depend on that value. In particular, the
    following has **no** effect::

        def test(app_params, make_app):
            args, kwargs = app_params
            kwargs['isolate'] = True  # has NO effect on the 'srcdir' value
            app = make_app(*args, **kwargs)
    """
    stack: list[SphinxTestApp] = []
    is_shared = test_params['shared_result'] is not None

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        if is_shared:
            app: SphinxTestApp = SphinxTestAppLazyBuild(*args, **kwargs)
        else:
            app = SphinxTestApp(*args, **kwargs)
        stack.append(app)
        return app

    syspath = sys.path.copy()
    yield make
    sys.path[:] = syspath

    while stack:
        stack.pop().cleanup()


_SHARED_RESULT_CACHE_KEY: pytest.StashKey[SharedResult]
_SHARED_RESULT_CACHE_KEY = pytest.StashKey[SharedResult]()


@pytest.fixture()
def shared_result(request: pytest.FixtureRequest) -> SharedResult:
    """A :class:`SharedResult` object."""
    module = get_context_node(request.node, 'module')
    # TODO(picnixz): how should distribute the shared results with xdist?
    return stash_default_value(module, _SHARED_RESULT_CACHE_KEY, SharedResult(module.nodeid))


def _shared_result_cache_clear_impl(request: pytest.FixtureRequest) -> None:
    cache = get_stashed(request.node, _SHARED_RESULT_CACHE_KEY, None, context='module')
    if cache is not None:
        cache.clear()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache_clear(request: pytest.FixtureRequest) -> None:
    """Cleanup the shared result cache for the test module.

    This fixture is automatically invoked.
    """
    _shared_result_cache_clear_impl(request)


# for backwards compatibility
@pytest.fixture(scope='module')
def _shared_result_cache(request: pytest.FixtureRequest) -> None:
    warnings.warn(
        f'{_shared_result_cache.__name__!r} is deprecated, use '
        f'{_shared_result_cache_clear.__name__!r} instead',
        category=RemovedInSphinx90Warning, stacklevel=2,
    )
    _shared_result_cache_clear_impl(request)


@pytest.fixture()
def if_graphviz_found(app: SphinxTestApp) -> None:  # NoQA: PT004
    """Skip the test if the graphviz ``dot`` command is not found.

    Usage::

        @pytest.mark.usefixtures('if_graphviz_found')
        def test_if_dot_command_exists(): ...
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


@pytest.fixture()
def rollback_sysmodules() -> Generator[None, None, None]:  # NoQA: PT004
    """
    Rollback sys.modules to its value before testing to unload modules
    during tests.

    For example, used in test_ext_autosummary.py to permit unloading the
    target module to clear its cache.
    """
    # test setup
    sys_module_names = frozenset(sys.modules)
    # run the test
    yield
    # test teardown (in the reverse-order the modules are inserted)
    for name in reversed(list(sys.modules)):
        if name not in sys_module_names:
            del sys.modules[name]
