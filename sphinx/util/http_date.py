"""Convert times to and from HTTP-date serialisations.

Reference: https://www.rfc-editor.org/rfc/rfc7231#section-7.1.1.1
"""

import time
from email.utils import formatdate, parsedate


def epoch_to_rfc1123(epoch: float) -> str:
    """Return HTTP-date string from epoch offset."""
    return formatdate(epoch, usegmt=True)


def rfc1123_to_epoch(rfc1123: str) -> float:
    """Return epoch offset from HTTP-date string."""
    t = parsedate(rfc1123)
    if t:
        return time.mktime(t)
    raise ValueError
