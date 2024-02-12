from __future__ import annotations

import re
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import docutils
import pytest

import sphinx
import sphinx.locale
import sphinx.pycode
from sphinx.testing.util import _clean_up_global_state

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from _pytest.config import Config
    from _pytest.main import Session
    from _pytest.nodes import Item
    from _pytest.fixtures import FixtureRequest


def _init_console(locale_dir=sphinx.locale._LOCALE_DIR, catalog='sphinx'):
    """Monkeypatch ``init_console`` to skip its action.

    Some tests rely on warning messages in English. We don't want
    CLI tests to bleed over those tests and make their warnings
    translated.
    """
    return sphinx.locale.NullTranslations(), False


sphinx.locale.init_console = _init_console

pytest_plugins = 'sphinx.testing.fixtures'

# Exclude 'roots' dirs for pytest test collector
collect_ignore = ['roots']

os.environ['SPHINX_AUTODOC_RELOAD_MODULES'] = '1'


def pytest_configure(config: Config) -> None:
    config.addinivalue_line('markers', 'unload(*pattern): unload matching modules')
    config.addinivalue_line('markers', 'unload_modules(*names, raises=False): unload modules')


def pytest_report_header(config):
    header = f"libraries: Sphinx-{sphinx.__display_version__}, docutils-{docutils.__version__}"
    if hasattr(config, '_tmp_path_factory'):
        header += f"\nbase tmp_path: {config._tmp_path_factory.getbasetemp()}"
    return header


@pytest.fixture(scope='session')
def rootdir() -> Path:
    return Path(__file__).parent.resolve() / 'roots'


@pytest.fixture(autouse=True)
def _cleanup_docutils():
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
    patterns = []
    for marker in request.node.iter_markers('unload'):
        patterns.extend(map(re.compile, marker.args))

    # find the exact module names and the flag indicating whether
    # to abort the test if unloading them is not possible
    targets: dict[str, bool] = {}
    for marker in request.node.iter_markers('unload_modules'):
        raises = marker.kwargs.get('raises', False)
        targets |= dict.fromkeys(marker.args, raises)

    yield  # run the test

    # nothing to do
    if not targets and not patterns:
        return

    # teardown by removing from the imported modules the requested modules
    for modname in frozenset(sys.modules):
        if modname in targets:
            if targets[modname] and modname not in sys.modules:
                pytest.fail(f'cannot unload module: {modname!r}')
            sys.modules.pop(modname, None)
        elif any(p.match(modname) for p in patterns):
            sys.modules.pop(modname, None)


_FORCE_SERIAL: dict[str, Sequence[str] | None] = {
    'test_builders/test_build_linkcheck.py': None,
    'test_intl/test_intl.py': None
}

def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    for item in items:
        if item.get_closest_marker('parallel'):
            continue

        relfspath, _, parametrized_name = item.location
        serial_tests = _FORCE_SERIAL.get(relfspath, ())
        if serial_tests is None or item.name in serial_tests:
            item.add_marker('serial')
            print(123, item.name)
