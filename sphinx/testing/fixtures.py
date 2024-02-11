"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import uuid
from collections import namedtuple
from io import StringIO
from typing import TYPE_CHECKING, Any, cast

import pytest

from sphinx.testing.util import SphinxTestApp, SphinxTestAppWrapperForSkipBuilding

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Node
    from _pytest.tmpdir import TempPathFactory

DEFAULT_ENABLED_MARKERS = [
    (
        'sphinx(builder, testroot=None, freshenv=False, confoverrides=None, tags=None, '
        'docutils_conf=None, parallel=0, isolated=None): '
        'arguments to initialize the sphinx test application.'
    ),
    'test_params(shared_result=...): test parameters.',
    'unload(*pattern): unload the matched modules',
    'unload_modules(*names, raises=False): unload the named modules',
]


def pytest_configure(config: Config) -> None:
    """Register custom markers"""
    for marker in DEFAULT_ENABLED_MARKERS:
        config.addinivalue_line('markers', marker)


@pytest.fixture(scope='session')
def rootdir() -> str | None:
    return None


class SharedResult:
    cache: dict[str, dict[str, str]] = {}

    def store(self, key: str, app: SphinxTestApp) -> None:
        if key not in self.cache:
            status, warning = app._status.getvalue(), app._warning.getvalue()
            self.cache[key] = {'status': status, 'warning': warning}

    def restore(self, key: str) -> dict[str, StringIO]:
        if key not in self.cache:
            return {}

        data = self.cache[key]
        return {'status': StringIO(data['status']), 'warning': StringIO(data['warning'])}


def _sphinx_params(node: Node) -> tuple[list[Any], dict[str, Any]]:
    pargs: dict[int, Any] = {}
    kwargs: dict[str, Any] = {}

    # to avoid stacking positional args
    for info in reversed(list(node.iter_markers("sphinx"))):
        pargs |= dict(enumerate(info.args))
        kwargs.update(info.kwargs)

    args = [pargs[i] for i in sorted(pargs.keys())]
    return args, kwargs


_TESTROOTS_REGISTRY: dict[str, str] = dict()


@pytest.fixture()
def app_params(
    request: FixtureRequest,
    test_params: dict[str, Any],
    shared_result: SharedResult,
    sphinx_test_tempdir: Path,
    rootdir: str | None,
) -> _app_params:
    """Parameters that are specified by ``pytest.mark.sphinx``.

    See :class:`sphinx.testing.util.SphinxTestApp` for the allowed parameters.
    """
    # ##### process pytest.mark.sphinx

    args, kwargs = _sphinx_params(request.node)

    # ##### process pytest.mark.test_params
    if shared := test_params['shared_result']:
        # todo: make it work
        # if 'srcdir' in kwargs:
        #     msg = 'You can not specify shared_result and srcdir in same time.'
        #     raise pytest.fail(msg)
        #
        # kwargs['srcdir'] = test_params['shared_result']
        # restore = shared_result.restore(test_params['shared_result'])
        # kwargs.update(restore)
        shared = False

    # ##### prepare Application params

    isolated = 'testroot' in kwargs and rootdir is not None and not shared
    isolated = kwargs.setdefault('isolated', isolated)
    testroot = kwargs.setdefault('testroot', 'root')
    srcdir = sphinx_test_tempdir / kwargs.get('srcdir', testroot)

    if isolated:
        # ensure that the source directory is unique, unless its output is shared
        srcdir = srcdir / str(uuid.uuid4())

    kwargs['srcdir'] = srcdir

    # special support for sphinx/tests
    if rootdir and not srcdir.exists():
        kwargs['testroot'] = testroot_path = os.path.join(rootdir, 'test-' + testroot)
        shutil.copytree(testroot_path, srcdir)

    return _app_params(args, kwargs)


_app_params = namedtuple('_app_params', 'args,kwargs')


@pytest.fixture()
def test_params(request: FixtureRequest) -> dict:
    """Test parameters that are specified by ``pytest.mark.test_params``.

    Usage::

        @pytest.mark.test_params(shared_result='some-testroot')
        def test(): ...

    When ``shared_result`` is specified, ``app._status`` and ``app._warning``
    objects will be shared in the parametrized test functions and/or test
    functions that have same 'shared_result' value.

    .. note::

       The parameters ``shared_result`` and ``srcdir`` are mutually exclusive.
    """
    env = request.node.get_closest_marker('test_params')
    kwargs = env.kwargs if env else {}
    result = {'shared_result': None} | kwargs

    if result['shared_result'] and not isinstance(result['shared_result'], str):
        msg = 'You can only provide a string type of value for "shared_result"'
        pytest.fail(msg)
    return result


@pytest.fixture()
def app(
    test_params: dict,
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

    print(f'# isolated:', app.isolated)
    print(f'# testroot:', app.testroot)
    print(f'# builder:', app.builder.name)
    print(f'# srcdir:', app.srcdir)
    print(f'# outdir:', app.outdir)
    print(f'# status:', '\n' + app._status.getvalue())
    print(f'# warning:', '\n' + app._warning.getvalue())

    if test_params['shared_result']:
        shared_result.store(test_params['shared_result'], app)


@pytest.fixture()
def status(app: SphinxTestApp) -> StringIO:
    """Back-compatibility for testing with previous @with_app decorator."""
    return app._status


@pytest.fixture()
def warning(app: SphinxTestApp) -> StringIO:
    """Back-compatibility for testing with previous @with_app decorator."""
    return app._warning


@pytest.fixture()
def make_app(
    test_params: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[..., SphinxTestApp], None, None]:
    """Fixture to create :class:`~sphinx.testing.util.SphinxTestApp` objects.

    Use this function to initialize `app` instead of directly calling the
    :class:`~sphinx.testing.util.SphinxTestApp` constructor::

        def test(make_app, app_params):
            args, kwargs = app_params
            ...  # do something on 'args' and 'kwargs' if needed
            app = make_app(*args, **kwargs)
    """
    apps: list[SphinxTestApp] = []
    syspath = sys.path.copy()

    def make(*args: Any, **kwargs: Any) -> SphinxTestApp:
        kwargs.setdefault('status', StringIO())
        kwargs.setdefault('warning', StringIO())
        app = SphinxTestApp(*args, **kwargs)
        apps.append(app)

        if test_params['shared_result']:
            proxy = SphinxTestAppWrapperForSkipBuilding(app)
            return cast(SphinxTestApp, proxy)
        return app

    yield make

    sys.path[:] = syspath
    for app_ in reversed(apps):  # clean up applications from the new ones
        app_.cleanup()


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


@pytest.fixture(autouse=True)
def _unload(request: FixtureRequest) -> Generator[None, None, None]:
    """Explicitly remove modules.

    Modules to remove can be specified using either syntax::

        # remove any module matching one the regular expressions
        @pytest.mark.unload('foo.*', 'bar.*')
        def test(): ...

        # silently remove modules using exact module names
        @pytest.mark.unload_modules('pkg.mod')
        def test(): ...

        # remove using exact module names and fails if a module was not loaded
        @pytest.mark.unload_modules('pkg.mod', raises=True)
        def test(): ...
    """
    patterns = []
    for marker in request.node.iter_markers('unload'):
        patterns.extend(map(re.compile, marker.args))

    targets: dict[str, bool] = {}
    for marker in request.node.iter_markers('unload_modules'):
        raises = marker.kwargs.get('raises', False)
        targets |= dict.fromkeys(marker.args, raises)

    yield

    if not targets and not patterns:
        return

    for modname in frozenset(sys.modules):
        if modname in targets:
            if targets[modname] and not modname in sys.modules:
                pytest.fail(f'cannot unload module: {modname!r}')
            sys.modules.pop(modname, None)
        elif any(p.match(modname) for p in patterns):
            sys.modules.pop(modname, None)
