from __future__ import annotations

import os
import zlib
from typing import TYPE_CHECKING

from sphinx.errors import ThemeError

if TYPE_CHECKING:
    from pathlib import Path


def _file_checksum(outdir: Path, filename: str | os.PathLike[str]) -> str:
    filename = os.fspath(filename)
    # Don't generate checksums for HTTP URIs
    if '://' in filename:
        return ''
    # Some themes and extensions have used query strings
    # for a similar asset checksum feature.
    # As we cannot safely strip the query string,
    # raise an error to the user.
    if '?' in filename:
        msg = f'Local asset file paths must not contain query strings: {filename!r}'
        raise ThemeError(msg)
    try:
        # Remove all carriage returns to avoid checksum differences
        content = outdir.joinpath(filename).read_bytes().translate(None, b'\r')
    except FileNotFoundError:
        return ''
    if not content:
        return ''
    return f'{zlib.crc32(content):08x}'
