import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def pytester_source(pytester, pytestconfig):
    sphinx_conftest = Path(__file__).parent.parent / 'conftest.py'
    # make sure to disable 'xdist' when testing our plugin
    source = sphinx_conftest.read_text('utf-8') + f'''
from pathlib import Path

import pytest

@pytest.fixture(scope='session')
def rootdir():
    return Path({os.fsdecode(sphinx_conftest.parent)!r}) / 'roots'

try:
    pytest_plugins = [name for name in pytest_plugins if name != 'xdist']
except NameError:
    pass
'''
    return pytester.makeconftest(source)
