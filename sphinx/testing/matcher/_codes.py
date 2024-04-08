from __future__ import annotations

import functools
import itertools
from typing import TYPE_CHECKING, TypedDict, final

from sphinx.testing.matcher._util import unique_everseen, unique_justseen

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from sphinx.testing.matcher.options import OpCode, OptionsHolder

    DispatcherFunc = Callable[[Iterable[str]], Iterable[str]]


@final
class DispatcherMap(TypedDict):
    # Whenever a new operation code is supported, do not forget to
    # update :func:`get_dispatcher_map` and :func.`get_active_opcodes`.
    strip: DispatcherFunc
    check: DispatcherFunc
    compress: DispatcherFunc
    unique: DispatcherFunc
    prune: DispatcherFunc
    filter: DispatcherFunc


def get_dispatcher_map(
    options: OptionsHolder,
    # here, we pass the functions so that we do not need to import them
    strip_lines: DispatcherFunc,
    prune_lines: DispatcherFunc,
) -> DispatcherMap:
    return {
        'strip': strip_lines,
        'check': functools.partial(filter, None),
        'compress': unique_justseen,
        'unique': unique_everseen,
        'prune': prune_lines,
        'filter': functools.partial(itertools.filterfalse, options.ignore),
    }


def get_active_opcodes(options: OptionsHolder) -> Iterable[OpCode]:
    disable: set[OpCode] = set()

    if options.strip_line is False:
        disable.add('strip')

    if options.keep_empty:
        disable.add('check')

    if not options.compress:
        disable.add('compress')

    if not options.unique:
        disable.add('unique')

    if not isinstance(prune_patterns := options.prune, str) and not prune_patterns:
        disable.add('prune')

    if not callable(options.ignore):
        disable.add('filter')

    return itertools.filterfalse(disable.__contains__, options.ops)
