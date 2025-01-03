from __future__ import annotations

import sys
import traceback
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from sphinx._cli.util.errors import format_traceback

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def save_traceback(app: Sphinx | None, exc: BaseException) -> str:
    """Save the given exception's traceback in a temporary file."""
    with NamedTemporaryFile(
        'w', encoding='utf-8', suffix='.log', prefix='sphinx-err-', delete=False
    ) as f:
        f.write(format_traceback(app, exc))
    return f.name


def format_exception_cut_frames(x: int = 1) -> str:
    """Format an exception with traceback, but only the last x frames."""
    typ, val, tb = sys.exc_info()
    # res = ['Traceback (most recent call last):\n']
    res: list[str] = []
    tbres = traceback.format_tb(tb)
    res += tbres[-x:]
    res += traceback.format_exception_only(typ, val)
    return ''.join(res)
