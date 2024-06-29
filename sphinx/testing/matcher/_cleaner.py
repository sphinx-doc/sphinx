from __future__ import annotations

from functools import partial
from itertools import filterfalse
from typing import TYPE_CHECKING, TypedDict, final

from sphinx.testing.matcher._util import unique_everseen, unique_justseen

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from typing_extensions import TypeAlias

    from sphinx.testing.matcher.options import OpCode, OptionsHolder, PrunePattern, StripChars

    DispatcherFunc: TypeAlias = Callable[[Iterable[str]], Iterable[str]]


@final
class HandlerMap(TypedDict):
    # Whenever a new operation code is supported, do not forget to
    # update :func:`get_dispatcher_map` and :func.`get_active_opcodes`.
    strip: DispatcherFunc
    check: DispatcherFunc
    compress: DispatcherFunc
    unique: DispatcherFunc
    prune: DispatcherFunc
    filter: DispatcherFunc


def get_active_opcodes(options: OptionsHolder) -> Iterable[OpCode]:
    """Get the iterable of operation's codes to execute."""
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

    return filterfalse(disable.__contains__, options.ops)


def make_handlers(args: OptionsHolder) -> HandlerMap:
    return {
        'strip': partial(_strip_lines_aux, args.strip_line),
        'check': partial(filter, None),
        'compress': unique_justseen,
        'unique': unique_everseen,
        'prune': partial(_prune_lines_aux, args.prune),
        'filter': partial(filterfalse, args.ignore),
    }


# we do not want to expose a non-positional-only public interface
# and we want to be able to have a pickable right partialization
# in case future multi-processing is added
def _strip_lines_aux(chars: StripChars, lines: Iterable[str]) -> Iterable[str]:
    # local import to break circular imports (but the module should already
    # be loaded since `get_handlers` is expected to be called from there)
    from .cleaner import strip_lines

    return strip_lines(lines, chars)


# we do not want to expose a non-positional-only public interface
# and we want to be able to have a pickable right partialization
# in case future multi-processing is added
def _prune_lines_aux(patterns: PrunePattern, lines: Iterable[str]) -> Iterable[str]:
    # local import to break circular imports (but the module should already
    # be loaded since `get_handlers` is expected to be called from there)
    from .cleaner import prune_lines

    return prune_lines(lines, patterns, trace=None)
