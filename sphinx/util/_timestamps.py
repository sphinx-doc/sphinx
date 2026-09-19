from __future__ import annotations

import os
import time


def _get_source_date_epoch() -> int | None:
    """Return ``SOURCE_DATE_EPOCH`` as integer seconds, if configured."""
    value = os.getenv('SOURCE_DATE_EPOCH')
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        msg = f'Invalid SOURCE_DATE_EPOCH value {value!r}; expected an integer'
        raise ValueError(msg) from None


def _format_rfc3339_microseconds(timestamp: int, /) -> str:
    """Return an RFC 3339 formatted string representing the given timestamp.

    :param timestamp: The timestamp to format, in microseconds.
    """
    seconds, fraction = divmod(timestamp, 10**6)
    time_tuple = time.gmtime(seconds)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_tuple) + f'.{fraction // 1_000}'
