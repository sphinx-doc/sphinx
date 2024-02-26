from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import docutils
import pytest

import sphinx
import sphinx.locale
import sphinx.pycode
from sphinx.testing.util import _clean_up_global_state
from sphinx.testing.warning_types import FixtureWarning

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.main import Session
    from _pytest.nodes import Item


def _init_console(locale_dir=sphinx.locale._LOCALE_DIR, catalog='sphinx'):
    """Monkeypatch ``init_console`` to skip its action.

    Some tests rely on warning messages in English. We don't want
    CLI tests to bleed over those tests and make their warnings
    translated.
    """
    return sphinx.locale.NullTranslations(), False


sphinx.locale.init_console = _init_console

pytest_plugins = ['sphinx.testing.fixtures', 'pytester', 'xdist']

# Exclude resource directories for pytest test collector
collect_ignore = ['certs', 'roots']

os.environ['SPHINX_AUTODOC_RELOAD_MODULES'] = '1'


def pytest_configure(config: Config) -> None:
    config.addinivalue_line('markers', 'unload(*pattern): unload matching modules')
    config.addinivalue_line('markers', 'unload_modules(*names, raises=False): unload modules')


def pytest_report_header(config: Config) -> str:
    header = f"libraries: Sphinx-{sphinx.__display_version__}, docutils-{docutils.__version__}"
    if hasattr(config, '_tmp_path_factory'):
        header += f"\nbase tmp_path: {config._tmp_path_factory.getbasetemp()}"
    return header


#: The test modules in which tests should not be executed in parallel mode,
#: unless they are explicitly marked with ``@pytest.mark.parallel()``.
#:
#: The keys are paths relative to the project directory and values can
#: be ``None`` to indicate all tests or a list of test names.
_FORCE_SERIAL: dict[str, Sequence[str] | None] = {
    'tests/test_builders/test_build_linkcheck.py': None,
    'tests/test_intl/test_intl.py': None,
}


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    for item in items:
        if item.get_closest_marker('parallel'):
            continue

        relfspath, _, _ = item.location
        serial_tests = _FORCE_SERIAL.get(relfspath, ())
        if serial_tests is None or item.name in serial_tests:
            item.add_marker('serial')


@pytest.fixture(scope='session')
def rootdir(request: FixtureRequest) -> Path:
    return getattr(request, 'param', Path(__file__).parent.resolve() / 'roots')


@pytest.fixture(scope='session')
def default_testroot(request: FixtureRequest) -> str:
    return getattr(request, 'param', 'minimal')


@pytest.fixture(scope='session')
def testroot_prefix(request: FixtureRequest) -> str:
    return getattr(request, 'param', 'test-')


@pytest.fixture(autouse=True)
def _cleanup_docutils() -> Generator[None, None, None]:
    saved_path = sys.path
    yield  # run the test
    sys.path[:] = saved_path

    _clean_up_global_state()


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
    # find the module names patterns
    patterns: list[re.Pattern[str]] = []
    for marker in request.node.iter_markers('unload'):
        patterns.extend(map(re.compile, marker.args))

    # find the exact module names and the flag indicating whether
    # to abort the test if unloading them is not possible
    silent_targets: set[str] = set()
    expect_targets: set[str] = set()
    for marker in request.node.iter_markers('unload_modules'):
        if marker.kwargs.get('raises', False):
            silent_targets.update(marker.args)
        else:
            expect_targets.update(marker.args)

    yield  # run the test

    # nothing to do
    if not silent_targets and not expect_targets and not patterns:
        return

    for modname in expect_targets - sys.modules.keys():
        request.node.warn(FixtureWarning(f'module was not loaded: {modname!r}', '_unload'))

    # teardown by removing from the imported modules the requested modules
    silent_targets.update(frozenset(sys.modules) & expect_targets)
    # teardown by removing from the imported modules the matched modules
    for modname in frozenset(sys.modules):
        if modname in silent_targets:
            silent_targets.remove(modname)
            del sys.modules[modname]
        elif any(p.match(modname) for p in patterns):
            del sys.modules[modname]
