from __future__ import annotations

import pytest


@pytest.fixture(scope='package')
def sphinx_builder():
    # test for domains should only parse doctrees by default
    return 'dummy'
