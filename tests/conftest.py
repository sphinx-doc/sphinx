import os
import shutil
from pathlib import Path

import docutils
import pytest

import sphinx
import sphinx.locale


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


@pytest.fixture(scope='session')
def rootdir():
    return Path(__file__).parent.absolute() / 'roots'


def pytest_report_header(config):
    header = f"libraries: Sphinx-{sphinx.__display_version__}, docutils-{docutils.__version__}"
    if hasattr(config, '_tmp_path_factory'):
        header += f"\nbase tmp_path: {config._tmp_path_factory.getbasetemp()}"
    return header


def _initialize_test_directory(session):
    if 'SPHINX_TEST_TEMPDIR' in os.environ:
        tmp_path = os.path.abspath(os.getenv('SPHINX_TEST_TEMPDIR'))
        print(f'Temporary files will be placed in {tmp_path}.')

        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

        os.mkdir(tmp_path)


def pytest_sessionstart(session):
    _initialize_test_directory(session)
