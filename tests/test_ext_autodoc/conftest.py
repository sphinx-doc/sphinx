from __future__ import annotations

import sys

import pytest

from tests.utils import TEST_ROOTS_DIR

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='module')
def inject_autodoc_root_into_sys_path() -> Iterator[None]:
    autodoc_root_path = str(TEST_ROOTS_DIR / 'test-ext-autodoc')

    sys.path.insert(0, autodoc_root_path)
    yield
    sys.path[:] = [p for p in sys.path if p != autodoc_root_path]
