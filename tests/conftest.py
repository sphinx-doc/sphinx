from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import docutils
import pytest

import sphinx
import sphinx.locale
import sphinx.pycode
from sphinx.testing._internal.pytest_util import get_tmp_path_factory
from sphinx.testing._internal.pytest_xdist import is_pytest_xdist_enabled
from sphinx.testing._internal.util import get_location_id
from sphinx.testing.util import _clean_up_global_state

if TYPE_CHECKING:
    from collections.abc import Iterator

    from _pytest.config import Config


def _init_console(
    locale_dir: str | None = sphinx.locale._LOCALE_DIR, catalog: str = 'sphinx',
) -> tuple[sphinx.locale.NullTranslations, bool]:
    """Monkeypatch ``init_console`` to skip its action.

    Some tests rely on warning messages in English. We don't want
    CLI tests to bleed over those tests and make their warnings
    translated.
    """
    return sphinx.locale.NullTranslations(), False


sphinx.locale.init_console = _init_console

# For now, we do not enable the 'xdist' plugin but we
# need the 'pytester' plugin declared in the top-level
# conftest.py file.
#
# See https://docs.pytest.org/en/stable/deprecations.html#pytest-plugins-in-non-top-level-conftest-files.
pytest_plugins = ['sphinx.testing.fixtures', 'pytester']

# Exclude resource directories for pytest test collector
collect_ignore = ['certs', 'roots']

os.environ['SPHINX_AUTODOC_RELOAD_MODULES'] = '1'


###############################################################################
# pytest hooks
###############################################################################


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        'markers',
        'apidoc(*, coderoot="test-root", excludes=[], options=[]): '
        'sphinx-apidoc command-line options (see test_ext_apidoc).',
    )

    config.addinivalue_line('markers', 'serial(): mark a test as serial-only')


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

    for item in items:
        if item.get_closest_marker('parametrize'):
            fspath, lineno, _ = item.location  # this is xdist-agnostic
            lineno = -1 if lineno is None else lineno
            xdist_group = get_location_id((fspath, lineno))
            item.add_marker(pytest.mark.xdist_group(xdist_group), append=True)


def pytest_report_header(config: Config) -> str:
    headers: dict[str, str] = {
        'libraries': f'Sphinx-{sphinx.__display_version__}, docutils-{docutils.__version__}',
    }
    if (factory := get_tmp_path_factory(config, None)) is not None:
        headers['base tmp_path'] = os.fsdecode(factory.getbasetemp())
    return '\n'.join(f'{key}: {value}' for key, value in headers.items())


###############################################################################
# fixtures
###############################################################################


@pytest.fixture
def sphinx_use_legacy_plugin() -> bool:  # xref RemovedInSphinx90Warning
    return False  # use the new implementation


@pytest.fixture(scope='session')
def rootdir() -> Path:
    return Path(__file__).parent.resolve() / 'roots'


# TODO(picnixz): change this fixture to 'minimal' when all tests using 'root'
#                have been found and explicitly changed
@pytest.fixture(scope='session')
def default_testroot() -> str:
    return 'root'


@pytest.fixture(autouse=True)
def _cleanup_docutils() -> Iterator[None]:
    saved_path = sys.path
    yield  # run the test
    sys.path[:] = saved_path

    _clean_up_global_state()
