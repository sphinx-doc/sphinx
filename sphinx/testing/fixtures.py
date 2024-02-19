"""Sphinx test fixtures for pytest.

See the development guide for documentation.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
from io import StringIO
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from sphinx.testing._fixtures import AppParams, get_app_params, get_test_params
from sphinx.testing.pytest_util import TestRootFinder
from sphinx.testing.util import SphinxTestApp, SphinxTestAppLazyBuild

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from typing import Any

    from sphinx.testing._fixtures import IsolationPolicy, TestParams


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


@pytest.fixture(scope='session')
def sphinx_test_tempdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Fixture for a temporary directory."""
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope='session')
def sphinx_builder(request: pytest.FixtureRequest) -> str:
    """Fixture for the default builder name."""
    # use suppress instead of getattr() to keep autocompletion
    with contextlib.suppress(AttributeError):
        return request.param
    return 'html'


@pytest.fixture(scope='session')
def sphinx_isolation(request: pytest.FixtureRequest) -> IsolationPolicy | None:
    """Fixture for the default isolation policy."""
    with contextlib.suppress(AttributeError):
        return request.param
    return False


@pytest.fixture(scope='module')
def rootdir(request: pytest.FixtureRequest) -> str | os.PathLike[str] | None:
    """Fixture for the directory containing the testroot directories."""
    with contextlib.suppress(AttributeError):
        return request.param
    return None


@pytest.fixture(scope='module')
def testroot_prefix(request: pytest.FixtureRequest) -> str | None:
    """Fixture for the testroot directories prefix."""
    with contextlib.suppress(AttributeError):
        return request.param
    return 'test-'


@pytest.fixture(scope='module')
def default_testroot(request: pytest.FixtureRequest) -> str | None:
    """Dynamic fixture for the default testroot ID."""
    with contextlib.suppress(AttributeError):
        return request.param
    return 'root'


@pytest.fixture(scope='module')
def testroot_finder(
    rootdir: str | os.PathLike[str] | None,
    testroot_prefix: str | None,
    default_testroot: str | None,
) -> TestRootFinder:
    """Fixture for the testroot finder object."""
    return TestRootFinder(rootdir, testroot_prefix, default_testroot)


class SharedResult:
    cache: dict[str, _CacheItem] = {}

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

    # restore the I/O stream values
    if shared_result_id and (
        shared := cast(_CacheView, shared_result.restore(shared_result_id))
    ):
        if kwargs.setdefault('status', shared['status']) is not shared['status']:
            pytest.fail('cannot use "shared_result" when "status" is explicitly given')
        if kwargs.setdefault('warning', shared['warning']) is not shared['warning']:
            pytest.fail('cannot use "shared_result" when "warning" is explicitly given')

    # copy the testroot files to the test sources directory
    srcdir, sources = kwargs['srcdir'], kwargs['_sphinx_testroot_path']
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
    app_params: AppParams,
    test_params: TestParams,
    shared_result: SharedResult,
    make_app: Callable[..., SphinxTestApp],
) -> Generator[SphinxTestApp, None, None]:
    """A :class:`sphinx.application.Sphinx` object suitable for testing."""
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    yield app

    print('# builder:', app.builder.name)
    print('# using:', kwargs['_sphinx_testroot_path'])
    print('# srcdir:', app.srcdir)
    print('# outdir:', app.outdir)
    print('# status:', '\n' + app.status.getvalue())
    print('# warning:', '\n' + app.warning.getvalue())

    if test_params['shared_result']:
        shared_result.store(test_params['shared_result'], app)


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
    is_shared = bool(test_params['shared_result'])

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        if is_shared:
            app = SphinxTestAppLazyBuild(*args, **kwargs)
        else:
            app = SphinxTestApp(*args, **kwargs)
        stack.append(app)
        return app

    syspath = sys.path.copy()
    yield make
    sys.path[:] = syspath
    while stack:
        stack.pop().cleanup()


@pytest.fixture()
def shared_result(request: pytest.FixtureRequest) -> SharedResult:
    return SharedResult()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache() -> None:
    """Cleanup the shared result cache for the test module."""
    SharedResult.cache.clear()


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
