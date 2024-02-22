from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def pytester_source(pytester, pytestconfig):
    sphinx_conftest = Path(__file__).parent.parent / 'conftest.py'
    # make sure to disable 'xdist' when testing our plugin
    source = sphinx_conftest.read_text('utf-8') + '''
try:
    pytest_plugins = [name for name in pytest_plugins if name != 'xdist']
except NameError:
    pass
'''
    return pytester.makeconftest(source)
