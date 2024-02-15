"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sphinx.testing._fixtures import AppParams, extract_app_params, extract_test_params
from sphinx.testing.util import SphinxTestApp, SphinxTestAppLazyBuild

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any

    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.monkeypatch import MonkeyPatch
    from _pytest.tmpdir import TempPathFactory

    from sphinx.testing._fixtures import TestParams


DEFAULT_ENABLED_MARKERS = [
    (
        'sphinx('
        '   builder="html", testroot=None, freshenv=False, confoverrides=None,'
        '   tags=None, docutils_conf=None, parallel=0, isolated=False,'
        '): arguments to initialize the sphinx test application.'
    ),
    'test_params(shared_result=None): test configuration.',
]


def pytest_configure(config: Config) -> None:
    """Register custom markers"""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.fixture(scope='session')
def rootdir() -> str | os.PathLike[str] | None:
    return None


@pytest.fixture(scope='session')
def default_testroot() -> str | None:
    """The default (optional) testroot name when none is specified."""
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
    sphinx_test_tempdir: Path,
    rootdir: str | os.PathLike[str] | None,
    default_testroot: str | None,
) -> AppParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.

    .. rubric:: Test isolation

    The ``isolated`` flag indicate whether the test source directory should
    be unique::

        @pytest.mark.sphinx(isolated=True)
        def test(app):
            assert str(app.srcdir).endswith('some-uuid-4')
    """
    args, kwargs = extract_app_params(request.node, test_params,
                                      sphinx_test_tempdir, default_testroot)

    if shared_srcdir := test_params['shared_result']:
        kwargs |= shared_result.restore(shared_srcdir)  # type: ignore[typeddict-item]

    # special support for sphinx/tests
    testroot, srcdir = kwargs['testroot'], kwargs['srcdir']
    if rootdir and not srcdir.exists():
        kwargs['testroot'] = testroot_path = os.path.join(rootdir, f'test-{testroot}')
        shutil.copytree(testroot_path, srcdir)

    return AppParams(args, kwargs)


@pytest.fixture()
def test_params(request: FixtureRequest) -> TestParams:
    """Test parameters that are specified by ``pytest.mark.test_params``.

    .. rubric:: Sharing status and warning messages across tests.

    The ``shared_result`` is a :class:`str` which, when specified, is used
    as the ``srcdir`` parameter, making ``app.status`` and ``app.warning``
    available to any parametrized test with same ``shared_result`` value.

    For instance, this makes::

        @pytest.mark.sphinx('html', testroot='my-testroot')
        @pytest.mark.test_params(shared_result='my-source-dir')
        def test_status_messages(app, status, warning):
            app.build()
            assert app.srcdir == 'my-source-dir'
            assert 'some message' in status.getvalue()

        @pytest.mark.sphinx('html', testroot='my-testroot')
        @pytest.mark.test_params(shared_result='my-source-dir')
        def test_warning_messages(app, status, warning):
            app.build()
            assert 'some warning' in warning.getvalue()

    roughly equivalent to::

        @pytest.mark.sphinx('html', testroot='my-testroot')
        def test_output_files(app, status, warning):
            app.build()

            # order of the assertions should not matter
            assert 'some message' in status.getvalue()
            assert 'some warning' in warning.getvalue()

    .. note::

       The statements ``@pytest.mark.test_params(shared_result=...)``
       and ``@pytest.mark.sphinx(srcdir=...)`` are mutually exclusive,
       unless the values are identical.

    Consider using ``@pytest.mark.usefixtures('optimize_build')`` to speed-up
    parametrized tests supporting a lazy building phase.
    """
    return extract_test_params(request.node)


@pytest.fixture()
def app(
    app_params: AppParams,
    test_params: TestParams,
    make_app: Callable[..., SphinxTestApp],
    shared_result: SharedResult,
) -> Generator[SphinxTestApp, None, None]:
    """Provides the 'sphinx.application.Sphinx' object.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    args, kwargs = app_params  # type: (list[Any], _AppKeywords)
    app = make_app(*args, **kwargs)
    yield app

    print('# isolated:', kwargs['isolated'])
    print('# testroot:', kwargs['testroot'])
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
def make_app(
    request: FixtureRequest,
    test_params: TestParams,
    monkeypatch: MonkeyPatch,
) -> Generator[Callable[..., SphinxTestApp], None, None]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects.

    Use this function to initialize `app` instead of directly calling the
    :class:`~sphinx.testing.util.SphinxTestApp` constructor::

        def test(make_app, app_params):
            args, kwargs = app_params
            ...  # do something on 'args' and 'kwargs' if needed
            app = make_app(*args, **kwargs)
    """
    stack: list[SphinxTestApp] = []
    syspath = sys.path.copy()

    lazy_build = test_params['shared_result'] or 'optimize_build' in request.fixturenames

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        kwargs.setdefault('status', StringIO())
        kwargs.setdefault('warning', StringIO())

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
def shared_result() -> SharedResult:
    return SharedResult()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache() -> None:
    """Cleanup the shared result for the test module."""
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


@pytest.fixture(scope='session')
def sphinx_test_tempdir(tmp_path_factory: TempPathFactory) -> Path:
    """Temporary directory."""
    return tmp_path_factory.getbasetemp()


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
