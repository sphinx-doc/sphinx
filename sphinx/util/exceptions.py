from __future__ import annotations

import sys
import traceback

from sphinx._cli.util.errors import save_traceback

__all__ = 'save_traceback', 'format_exception_cut_frames'


def format_exception_cut_frames(x: int = 1) -> str:
    """Format an exception with traceback, but only the last x frames."""
    typ, val, tb = sys.exc_info()
    # res = ['Traceback (most recent call last):\n']
    res: list[str] = []
    tbres = traceback.format_tb(tb)
    res += tbres[-x:]
    res += traceback.format_exception_only(typ, val)
    return ''.join(res)
