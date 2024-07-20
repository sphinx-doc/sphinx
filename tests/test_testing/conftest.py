from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from ._const import PROJECT_PATH, SPHINX_PLUGIN_NAME

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.pytester import Pytester


# change this fixture when the rest of the test suite is changed
@pytest.fixture(scope='package')
def default_testroot():
    return 'minimal'


@pytest.fixture(autouse=True)
def _pytester_pyprojecttoml(pytester: Pytester) -> None:
    # TL;DR: this is a patch to force pytester & xdist using the local plugin
    #        implementation and not a possibly out-of-date installed version.
    #
    # :mod:`xdist.plugin` contains a snapshot of ``sys.path`` which is then
    # passed to the workers; however, the snapshot is created when the module
    # is imported. Apparently, even if ``pytester.syspathinsert(...)`` is used,
    # the ``xdist.plugin`` module is not reloaded and thus the snapshot is not
    # correctly updated, meaning that when ``pytester`` effectively runs a test
    # the ``xdist`` workers are not able to find the local implementation.
    #
    # In addition :mod:`xdist.remote` ignores a user-defined PYTHONPATH when
    # setting its own ``sys.path``, leading to ``ImportError`` at runtime.
    #
    # Note that PyCharm (and probably other IDEs or tools) does not suffer from
    # this since it can be configured to automatically extend ``sys.path`` with
    # the project's sources. The issue seems to only appear when ``pytest`` is
    # directly invoked from the CLI.
    pytester.makepyprojecttoml(f"""
[tool.pytest.ini_options]
addopts = ["--import-mode=prepend", "--strict-config", "--strict-markers"]
pythonpath = [{PROJECT_PATH!r}]
xfail_strict = true
""")


@pytest.fixture(autouse=True)
def _pytester_conftest(pytestconfig: Config, pytester: Pytester) -> None:
    testroot_dir = os.path.join(pytestconfig.rootpath, 'tests', 'roots')
    pytester.makeconftest(f"""
import pytest

pytest_plugins = [{SPHINX_PLUGIN_NAME!r}]
collect_ignore = ['certs', 'roots']

@pytest.fixture()
def sphinx_use_legacy_plugin() -> bool:  # xref RemovedInSphinx90Warning
    return False  # use the new implementation

@pytest.fixture(scope='session')
def rootdir():
    return {testroot_dir!r}

@pytest.fixture(scope='session')
def default_testroot():
    return 'minimal'
""")
