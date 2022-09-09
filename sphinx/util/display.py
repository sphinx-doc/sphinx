from __future__ import annotations

import functools
from typing import Any, Callable, Iterable, Iterator, TypeVar

from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.console import bold, colorize, term_width_line  # type: ignore

if False:
    from types import TracebackType

logger = logging.getLogger(__name__)


def display_chunk(chunk: Any) -> str:
    if isinstance(chunk, (list, tuple)):
        if len(chunk) == 1:
            return str(chunk[0])
        return f'{chunk[0]} .. {chunk[-1]}'
    return str(chunk)


T = TypeVar('T')


def status_iterator(
    iterable: Iterable[T],
    summary: str,
    color: str = 'darkgreen',
    length: int = 0,
    verbosity: int = 0,
    stringify_func: Callable[[Any], str] = display_chunk,
) -> Iterator[T]:
    if length == 0:
        logger.info(bold(summary), nonl=True)
    for i, item in enumerate(iterable, start=1):
        item_str = colorize(color, stringify_func(item))
        if length == 0:
            logger.info(item_str, nonl=True)
            logger.info(' ', nonl=True)
        else:
            s = f'{bold(summary)}[{int(100 * i / length): >3d}%] {item_str}'
            if verbosity:
                logger.info(s + '\n', nonl=True)
            else:
                logger.info(term_width_line(s), nonl=True)
        yield item
    logger.info('')


class SkipProgressMessage(Exception):
    pass


class progress_message:
    def __init__(self, message: str) -> None:
        self.message = message

    def __enter__(self) -> None:
        logger.info(bold(self.message + '... '), nonl=True)

    def __exit__(
        self,
        typ: type[BaseException] | None,
        val: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if isinstance(val, SkipProgressMessage):
            logger.info(__('skipped'))
            if val.args:
                logger.info(*val.args)
            return True
        elif val:
            logger.info(__('failed'))
        else:
            logger.info(__('done'))

        return False

    def __call__(self, f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return f(*args, **kwargs)

        return wrapper
