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
from typing import TYPE_CHECKING, Literal, cast

import pytest

from sphinx.testing._fixtures import AppParams, get_app_params, get_test_params
from sphinx.testing.pytest_util import TestRootFinder
from sphinx.testing.util import SphinxTestApp, SphinxTestAppLazyBuild

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from typing import Any

    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.tmpdir import TempPathFactory

    from sphinx.testing._fixtures import IsolationPolicy, TestParams

DEFAULT_ENABLED_MARKERS = [
    (
        'sphinx(buildername=None, *, '
        'srcdir=None, testroot=None, freshenv=False, '
        'confoverrides=None, tags=None, docutils_conf=None, '
        'parallel=0, isolate=None): arguments to initialize the sphinx test application.'
    ),
    'test_params(shared_result=None): test configuration.',
    'isolate(policy=None, /): test isolation policy.',
]


def pytest_configure(config: Config) -> None:
    """Register custom markers"""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.fixture(scope='session')
def rootdir() -> str | os.PathLike[str] | None:
    return None


@pytest.fixture(scope='session')
def sphinx_test_tempdir(request: FixtureRequest, tmp_path_factory: TempPathFactory) -> Path:
    with contextlib.suppress(AttributeError):
        return request.param
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope='session')
def sphinx_builder(request: FixtureRequest) -> str:
    with contextlib.suppress(AttributeError):
        return request.param
    return 'html'


@pytest.fixture(scope='session')
def sphinx_testroot_finder(
    request: FixtureRequest,
    # the fixtures below are not used directly but are present
    # so that *request* can query their value during the setup
    rootdir: str | os.PathLike[str] | None,
) -> TestRootFinder:
    with contextlib.suppress(AttributeError):
        return request.param

    rootdir = request.getfixturevalue('rootdir')
    return TestRootFinder(rootdir, 'root', 'test-')


@pytest.fixture(scope='session')
def sphinx_default_isolation(request: FixtureRequest) -> IsolationPolicy | None:
    with contextlib.suppress(AttributeError):
        return request.param
    return None


class SharedResult:
    cache: dict[str, dict[str, str]] = {}

    def store(self, key: str, app: SphinxTestApp) -> None:
        if key not in self.cache:
            status, warning = app.status.getvalue(), app.warning.getvalue()
            self.cache[key] = {'status': status, 'warning': warning}

    def restore(self, key: str) -> dict[str, Any]:
        if key not in self.cache:
            return {}

        data = self.cache[key]
        return {'status': StringIO(data['status']), 'warning': StringIO(data['warning'])}


_app_params = AppParams  # for backwards compatibility


@pytest.fixture()
def app_params(
    request: FixtureRequest,
    test_params: TestParams,
    shared_result: SharedResult,
    # the fixtures below are not used directly but are present
    # so that *request* can query their value during the setup
    sphinx_test_tempdir: Path,
    sphinx_builder: str,
    sphinx_testroot_finder: TestRootFinder,
    sphinx_default_isolation: IsolationPolicy | None,
) -> AppParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    # get the dynamic values of the dependent fixtures
    sphinx_test_tempdir = request.getfixturevalue('sphinx_test_tempdir')
    sphinx_builder = request.getfixturevalue('sphinx_builder')
    sphinx_testroot_finder = request.getfixturevalue('sphinx_testroot_finder')

    if m := request.node.get_closest_marker('isolate'):
        # isolate() is equivalent to isolate('always')
        sphinx_default_isolation = m.args[0] if m.args else True
    else:
        # use getfixturevalue() to get a possibly overridden value (the value
        # of 'sphinx_default_isolation' is the value of this module's fixture)
        sphinx_default_isolation = request.getfixturevalue('sphinx_default_isolation')

    sphinx_shared_result = test_params['shared_result']

    args, kwargs = get_app_params(
        request.node,
        session_temp_dir=sphinx_test_tempdir,
        testroot_finder=sphinx_testroot_finder,
        default_builder=sphinx_builder,
        default_isolation=sphinx_default_isolation,
        shared_result=sphinx_shared_result,
    )

    # update the I/O streams
    if sphinx_shared_result and (buffers := shared_result.restore(sphinx_shared_result)):
        for reserved in cast(tuple[Literal['status', 'warning'], ...], ('status', 'warning')):
            if reserved in kwargs and kwargs[reserved] != buffers[reserved]:
                pytest.fail('cannot use "shared_result" when {reserved!r} is specified')
            kwargs[reserved] = buffers[reserved]

    srcdir, sources = kwargs['srcdir'], kwargs['_sphinx_testroot_path']
    if sources is not None and not srcdir.exists():
        if not os.path.exists(sources):
            pytest.fail(f'testroot does not exist: {sources}')
        shutil.copytree(sources, srcdir)

    return AppParams(args, kwargs)


@pytest.fixture()
def test_params(request: FixtureRequest) -> TestParams:
    """Test parameters that are specified by ``pytest.mark.test_params``."""
    return get_test_params(request.node)


@pytest.fixture()
def app(
    app_params: AppParams,
    test_params: TestParams,
    shared_result: SharedResult,
    make_app: Callable[..., SphinxTestApp],
) -> Generator[SphinxTestApp, None, None]:
    """Provides the 'sphinx.application.Sphinx' object.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    yield app

    print('# testroot:', kwargs['_sphinx_testroot_path'])
    print('# builder:', app.builder.name)
    print('# srcdir:', app.srcdir)
    print('# outdir:', app.outdir)
    print('# status:', '\n' + app.status.getvalue())
    print('# warning:', '\n' + app.warning.getvalue())

    if test_params['shared_result']:
        shared_result.store(test_params['shared_result'], app)


@pytest.fixture()
def status(app: SphinxTestApp) -> StringIO:
    """Fixture for the application's status stream."""
    return app.status


@pytest.fixture()
def warning(app: SphinxTestApp) -> StringIO:
    """Fixture for the application's warning stream."""
    return app.warning


@pytest.fixture()
def make_app(test_params: TestParams) -> Generator[Callable[..., SphinxTestApp], None, None]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects.

    Use this fixture to create an :class:`~sphinx.testing.util.SphinxTestApp`
    object instead of directly calling its constructor::

        def test(make_app):
            app = make_app(*args, **kwargs)
    """
    stack: list[SphinxTestApp] = []
    syspath = sys.path.copy()

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        if '_sphinx_shared_result' in kwargs:
            lazy_build = kwargs.pop('_sphinx_shared_result')
        else:
            lazy_build = test_params['shared_result']

        if lazy_build:
            app = SphinxTestAppLazyBuild(*args, **kwargs)
        else:
            app = SphinxTestApp(*args, **kwargs)

        stack.append(app)
        return app

    yield make

    sys.path[:] = syspath
    while stack:
        # remove the app from the known stack
        app = stack.pop()  # clean up applications from the new ones
        app.cleanup()


@pytest.fixture()
def shared_result(request: FixtureRequest) -> SharedResult:
    return SharedResult()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache() -> None:
    """Cleanup the shared result cache for the test module."""
    SharedResult.cache.clear()


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


@pytest.fixture()
def rollback_sysmodules() -> Generator[None, None, None]:  # NoQA: PT004
    """
    Rollback sys.modules to its value before testing to unload modules
    during tests.

    For example, used in test_ext_autosummary.py to permit unloading the
    target module to clear its cache.
    """
    pre_sys_modules = frozenset(sys.modules)

    try:
        yield
    finally:
        for name in tuple(sys.modules):
            if name not in pre_sys_modules:
                del sys.modules[name]
