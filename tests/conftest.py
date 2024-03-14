from __future__ import annotations

import fnmatch
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import docutils
import pytest

import sphinx
import sphinx.locale
import sphinx.pycode
from sphinx.testing.internal.pytest_util import get_tmp_path_factory, issue_warning
from sphinx.testing.internal.pytest_xdist import is_pytest_xdist_enabled
from sphinx.testing.internal.warnings import FixtureWarning
from sphinx.testing.util import _clean_up_global_state

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

# for now, we do not enable the 'xdist' plugin
pytest_plugins = ['sphinx.testing.fixtures']

# Exclude resource directories for pytest test collector
collect_ignore = ['certs', 'roots']

os.environ['SPHINX_AUTODOC_RELOAD_MODULES'] = '1'


def pytest_configure(config: Config) -> None:
    config.addinivalue_line('markers', 'serial(): mark a test as non-xdist friendly')
    config.addinivalue_line('markers', 'unload(*pattern): unload matching modules')
    config.addinivalue_line('markers', 'unload_modules(*names, raises=False): unload modules')

    config.addinivalue_line(
        'markers',
        'apidoc(*, coderoot="test-root", excludes=[], options=[]): '
        'sphinx-apidoc command-line options (see test_ext_apidoc).',
    )


def pytest_report_header(config: Config) -> str:
    headers = {
        'libraries': f'Sphinx-{sphinx.__display_version__}, docutils-{docutils.__version__}',
    }
    if (factory := get_tmp_path_factory(config, None)) is not None:
        headers['base tmp_path'] = factory.getbasetemp()
    return '\n'.join(f'{key}: {value}' for key, value in headers.items())


# The test modules in which tests should not be executed in parallel mode,
# unless they are explicitly marked with ``@pytest.mark.parallel()``.
#
# The keys are paths relative to the project directory and values can
# be ``None`` to indicate all tests or a list of (non-parametrized) test
# names, e.g., for a test::
#
#   @pytest.mark.parametrize('value', [1, 2])
#   def test_foo(): ...
#
# the name is ``test_foo`` and not ``test_foo[1]`` or ``test_foo[2]``.
#
# Note that a test class or function should not have '[' in its name.
_SERIAL_TESTS: dict[str, Sequence[str] | None] = {
    'tests/test_builders/test_build_linkcheck.py': None,
    'tests/test_intl/test_intl.py': None,
}


@lru_cache(maxsize=512)
def _serial_matching(relfspath: str, pattern: str) -> bool:
    return fnmatch.fnmatch(relfspath, pattern)


@lru_cache(maxsize=512)
def _findall_main_keys(relfspath: str) -> tuple[str, ...]:
    return tuple(key for key in _SERIAL_TESTS if _serial_matching(relfspath, key))


def _test_basename(name: str) -> str:
    """Get the test name without the parametrization part from an item name."""
    if name.find('[') < name.find(']'):
        # drop the parametrized part
        return name[:name.find('[')]
    return name


@pytest.hookimpl(tryfirst=True)
def pytest_itemcollected(item: Item) -> None:
    if item.get_closest_marker('serial'):
        return

    # check whether the item should be marked with ``@pytest.mark.serial()``
    relfspath, _, _ = item.location
    for key in _findall_main_keys(relfspath):
        names = _SERIAL_TESTS[key]
        if names is None or _test_basename(item.name) in names:
            item.add_marker(pytest.mark.serial())


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    if not is_pytest_xdist_enabled(config):
        # ignore ``@pytest.mark.serial()`` when ``xdist`` is inactive
        return

    # only select items that are marked (manually or automatically) with 'serial'
    items[:] = [item for item in items if item.get_closest_marker('serial') is None]


@pytest.fixture(scope='session')
def rootdir() -> Path:
    return Path(__file__).parent.resolve() / 'roots'


# TODO(picnixz): change this fixture to 'minimal' when all tests using 'root'
#                have been found and explicitly changed
@pytest.fixture(scope='session')
def default_testroot() -> str:
    return 'root'


@pytest.fixture(autouse=True)
def _cleanup_docutils() -> Generator[None, None, None]:
    saved_path = sys.path
    yield  # run the test
    sys.path[:] = saved_path

    _clean_up_global_state()


@pytest.fixture(autouse=True)
def _do_unload(request: FixtureRequest) -> Generator[None, None, None]:
    """Explicitly remove modules.

    The modules to remove can be specified as follows::

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
        warning = FixtureWarning(f'module was not loaded: {modname!r}', '_unload')
        issue_warning(request, warning)

    # teardown by removing from the imported modules the requested modules
    silent_targets.update(frozenset(sys.modules) & expect_targets)
    # teardown by removing from the imported modules the matched modules
    for modname in frozenset(sys.modules):
        if modname in silent_targets:
            silent_targets.remove(modname)
            del sys.modules[modname]
        elif any(p.match(modname) for p in patterns):
            del sys.modules[modname]
