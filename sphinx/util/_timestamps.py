from __future__ import annotations

import time
from os import getenv


def _format_rfc3339_microseconds(timestamp: int, /) -> str:
    """Return an RFC 3339 formatted string representing the given timestamp.

    :param timestamp: The timestamp to format, in microseconds.
    """
    seconds, fraction = divmod(timestamp, 10**6)
    time_tuple = time.gmtime(seconds)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_tuple) + f'.{fraction // 1_000}'


def _get_publication_time() -> time.struct_time:
    """Return the publication time to use for the current build.

    If set, use the timestamp from SOURCE_DATE_EPOCH
    https://reproducible-builds.org/specs/source-date-epoch/

    Publication time cannot be projected into the future (beyond the local system
    clock time).
    """
    time.tzset()
    system_time = time.localtime()
    if (source_date_epoch := getenv('SOURCE_DATE_EPOCH')) is not None:
        if (rebuild_time := time.localtime(float(source_date_epoch))) < system_time:
            return rebuild_time
    return system_time
