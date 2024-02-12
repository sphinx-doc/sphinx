"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from io import StringIO
from typing import TYPE_CHECKING, NamedTuple, cast

import pytest

from sphinx.testing.util import DEFAULT_TESTROOT, SphinxTestApp, SphinxTestAppLazyBuild

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from typing import Any, TypedDict

    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.monkeypatch import MonkeyPatch
    from _pytest.tmpdir import TempPathFactory

    class _AppKeywords(TypedDict, total=False):
        srcdir: Path
        testroot: str
        freshenv: bool
        confoverrides: dict[str, Any]
        tags: list[str]
        docutils_conf: str
        parallel: int
        isolated: bool

        status: StringIO
        warning: StringIO

    class _TestParams(TypedDict):
        shared_result: str | None


DEFAULT_ENABLED_MARKERS = [
    (
        'sphinx('
        '   builder="html", testroot="root", freshenv=False, confoverrides=None,'
        '   tags=None, docutils_conf=None, parallel=0, isolated=None,'
        '): arguments to initialize the sphinx test application.'
    ),
    'test_params(shared_result=None): test configuration.',
]

OPTIMIZE_BUILD_KEY = pytest.StashKey[int]()


def pytest_configure(config: Config) -> None:
    """Register custom markers"""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.fixture(scope='session')
def rootdir() -> str | os.PathLike[str] | None:
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


@pytest.fixture()
def app_params(
    request: FixtureRequest,
    test_params: _TestParams,
    shared_result: SharedResult,
    sphinx_test_tempdir: Path,
    rootdir: str | os.PathLike[str] | None,
) -> _AppParams:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.

    .. rubric:: Test isolation

    The ``isolated`` flag indicate whether the test source directory should
    be unique::

        @pytest.mark.sphinx(isolated=True)
        def test(app):
            assert str(app.srcdir).endswith('some-uuid-4')
    """
    # ##### process pytest.mark.sphinx

    poargs: dict[int, Any] = {}
    kwargs: dict[str, Any] = {}

    # to avoid stacking positional args
    for info in reversed(list(request.node.iter_markers("sphinx"))):
        poargs |= dict(enumerate(info.args))
        kwargs.update(info.kwargs)

    args = [poargs[i] for i in sorted(poargs.keys())]

    # hash the positional and keyword arguments to ensure that applications
    # cannot use the same 'shared_result' if they are configured differently

    # ##### process pytest.mark.test_params
    if shared_srcdir := test_params['shared_result']:
        if 'srcdir' in kwargs and kwargs['srcdir'] != shared_srcdir:
            msg = 'You can not specify shared_result and srcdir in same time.'
            raise pytest.fail(msg)

        # set the (common) source directory
        kwargs['srcdir'] = shared_srcdir
        # do not isolate (unless requested otherwise)
        if kwargs.get('isolated', None) is None:
            kwargs.setdefault('isolated', False)
        kwargs |= shared_result.restore(shared_srcdir)

    # ##### prepare Application params

    isolated = kwargs.setdefault('isolated', True)
    testroot = kwargs.setdefault('testroot', DEFAULT_TESTROOT)
    srcdir = sphinx_test_tempdir / kwargs.get('srcdir', testroot)

    if isolated:
        # ensure that the source directory is unique if needed
        srcdir = srcdir / str(uuid.uuid4())

    kwargs['srcdir'] = srcdir

    # special support for sphinx/tests
    if rootdir and not srcdir.exists():
        kwargs['testroot'] = testroot_path = os.path.join(rootdir, 'test-' + testroot)
        shutil.copytree(testroot_path, srcdir)

    return _AppParams(args, cast('_AppKeywords', kwargs))


class _AppParams(NamedTuple):
    args: list[Any]
    kwargs: _AppKeywords


# for backwards compatibility
_app_params = _AppParams


@pytest.fixture()
def test_params(request: FixtureRequest) -> _TestParams:
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
    env = request.node.get_closest_marker('test_params')
    kwargs = env.kwargs if env else {}
    result = {'shared_result': None} | kwargs

    if result['shared_result'] and not isinstance(result['shared_result'], str):
        msg = 'You can only provide a string type of value for "shared_result"'
        pytest.fail(msg)
    return cast('_TestParams', result)


@pytest.fixture()
def app(
    test_params: _TestParams,
    app_params: _app_params,
    make_app: Callable[..., SphinxTestApp],
    shared_result: SharedResult,
) -> Generator[SphinxTestApp, None, None]:
    """Provides the 'sphinx.application.Sphinx' object.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    yield app

    print('# isolated:', app.isolated)
    print('# testroot:', app.testroot)
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
    test_params: _TestParams,
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


@pytest.fixture()
def optimize_build(request: FixtureRequest) -> None:  # NoQA: PT004
    r"""Speed-up build in tests marked with ``@pytest.mark.parametrize``.

    For instance, this makes::

        @pytest.mark.parametrize(('file', 'value'), [('a', '1'), ('b', '2')])
        @pytest.mark.sphinx('html', testroot='my-testroot')
        @pytest.mark.usefixtures('optimize_build')
        def test(app, file, value):
            app.build()
            assert value in (app.outdir / file).read_text(encoding='utf8')

    roughly equivalent to::

        @pytest.mark.sphinx('html', testroot='my-testroot')
        def test(app):
            app.build()

            for file, value in [('file1', 'foo'), ('file2', 'bar')]:
                assert value in (app.outdir / file).read_text(encoding='utf8')

    .. note::

       This fixture should only be used when ``@pytest.mark.parametrize``
       is used as a semantic substitute for a :keyword:`for` loop.

    It is possible to combine ``@pytest.mark.test_params(shared_result=...)``
    together with ``@pytest.mark.usefixtures('optimize_build')``. The test
    being decorated will use the specified shared result, but only if the
    latter exists.

    This fixture has **no** effect when ``@pytest.mark.sphinx(isolated=True)``
    is used.
    """
    path, lineno, _ = request.node.location
    testid = (path, lineno)

    env = request.node.get_closest_marker('test_params')
    shared_result = env.kwargs.get('shared_result') if env else None

    # registry containing the unique source directories by test (without parametrization)
    registry: dict[tuple[str, int | None], str]
    registry = request.node.session.stash.setdefault(OPTIMIZE_BUILD_KEY, {})
    if testid not in registry:
        # do not use setdefault() to avoid calling uuid.uuid4()
        registry[testid] = shared_result or registry.get(testid) or str(uuid.uuid4())

    srcdir = shared_result or registry[testid]
    # set the correct source directory and use isolated=None to indicate that
    # we want to be non-isolated *if* possible (but at the time we are calling
    # this fixture, we do not know whether the application should indeed be in
    # an isolated build or not)
    request.applymarker(pytest.mark.sphinx(srcdir=srcdir, isolated=None))
