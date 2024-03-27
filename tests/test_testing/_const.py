"""Private constants."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import sphinx

if TYPE_CHECKING:
    from typing import Final

PROJECT_PATH: Final[str] = os.path.realpath(os.path.dirname(os.path.dirname(sphinx.__file__)))
"""Directory containing the current (local) sphinx's implementation."""

SPHINX_PLUGIN_NAME: Final[str] = 'sphinx.testing.fixtures'
