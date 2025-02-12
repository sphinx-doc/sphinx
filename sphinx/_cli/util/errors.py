from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from sphinx.errors import SphinxError, SphinxParallelError

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Final, Protocol

    from sphinx.extension import Extension

    class SupportsWrite(Protocol):
        def write(self, text: str, /) -> int | None: ...


_CSI: Final[str] = re.escape('\x1b[')  # 'ESC [': Control Sequence Introducer

# Pattern matching ANSI CSI colors (SGR) and erase line (EL) sequences.
#
# See ``_strip_escape_sequences()`` for details.
_ANSI_CODES: Final[re.Pattern[str]] = re.compile(
    '\x1b'
    r"""\[
    (?:
      (?:\d+;){0,2}\d*m  # ANSI color code    ('m' is equivalent to '0m')
    |
      [012]?K            # ANSI Erase in Line ('K' is equivalent to '0K')
    )""",
    re.VERBOSE | re.ASCII,
)


def terminal_safe(s: str, /) -> str:
    """Safely encode a string for printing to the terminal."""
    return s.encode('ascii', 'backslashreplace').decode('ascii')


def strip_escape_sequences(text: str, /) -> str:
    r"""Remove the ANSI CSI colors and "erase in line" sequences.

    Other `escape sequences <https://en.wikipedia.org/wiki/ANSI_escape_code>`_
    (e.g., VT100-specific functions) are not supported. Only control sequences
    *natively* known to Sphinx (i.e., colour sequences used in Sphinx
    and "erase entire line" (``'\x1b[2K'``)) are stripped by this function.

    .. warning:: This function only for use within Sphinx..

    __ https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    return _ANSI_CODES.sub('', text)


def full_exception_context(
    exception: BaseException,
    *,
    message_log: Collection[str] = (),
    extensions: Collection[Extension] = (),
    full_traceback: bool = True,
) -> str:
    """Return a formatted message containing useful debugging context."""
    messages = [f'    {strip_escape_sequences(msg)}'.rstrip() for msg in message_log]
    while messages and not messages[-1]:
        messages.pop()
    last_msgs = '\n'.join(messages)
    exts_list = '\n'.join(
        f'* {ext.name} ({ext.version})'
        for ext in extensions
        if ext.version != 'builtin'
    )
    exc_format = format_traceback(exception, short_traceback=not full_traceback)
    return error_info(last_msgs or 'None.', exts_list or 'None.', exc_format)


def format_traceback(
    exception: BaseException, /, *, short_traceback: bool = False
) -> str:
    """Format the given exception's traceback."""
    if short_traceback:
        from traceback import TracebackException

        # format an exception with traceback, but only the last frame.
        te = TracebackException.from_exception(exception, limit=-1)
        exc_format = te.stack.format()[-1] + ''.join(te.format_exception_only())
    elif isinstance(exception, SphinxParallelError):
        exc_format = f'(Error in parallel process)\n{exception.traceback}'
    else:
        from traceback import format_exception

        exc_format = ''.join(format_exception(exception))
    return '\n'.join(f'    {line}' for line in exc_format.rstrip().splitlines())


def error_info(messages: str, extensions: str, traceback: str) -> str:
    """Format the traceback and extensions list with environment information."""
    import platform

    import docutils
    import jinja2
    import pygments

    import sphinx

    return f"""\
Versions
========

* Platform:         {sys.platform}; ({platform.platform()})
* Python version:   {platform.python_version()} ({platform.python_implementation()})
* Sphinx version:   {sphinx.__display_version__}
* Docutils version: {docutils.__version__}
* Jinja2 version:   {jinja2.__version__}
* Pygments version: {pygments.__version__}

Last Messages
=============

{messages}

Loaded Extensions
=================

{extensions}

Traceback
=========

{traceback}
"""


def save_traceback(
    exception: BaseException,
    *,
    message_log: Collection[str] = (),
    extensions: Collection[Extension] = (),
) -> str:
    """Save the given exception's traceback in a temporary file."""
    output = full_exception_context(
        exception=exception,
        message_log=message_log,
        extensions=extensions,
    )
    filename = write_temporary_file(output)
    return filename


def write_temporary_file(content: str) -> str:
    """Write content to a temporary file and return the filename."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        'w', encoding='utf-8', suffix='.log', prefix='sphinx-err-', delete=False
    ) as f:
        f.write(content)

    return f.name


def handle_exception(
    exception: BaseException,
    /,
    *,
    stderr: SupportsWrite = sys.stderr,
    use_pdb: bool = False,
    print_traceback: bool = False,
    message_log: Collection[str] = (),
    extensions: Collection[Extension] = (),
) -> None:
    from bdb import BdbQuit

    from docutils.utils import SystemMessage

    from sphinx._cli.util.colour import red
    from sphinx.locale import __

    if isinstance(exception, BdbQuit):
        return

    def print_err(*values: str) -> None:
        print(*values, file=stderr)

    def print_red(*values: str) -> None:
        print_err(*map(red, values))

    print_err()
    if not use_pdb and isinstance(exception, KeyboardInterrupt):
        print_err(__('Interrupted!'))
        return

    if isinstance(exception, SystemMessage):
        print_red(__('reStructuredText markup error!'))

    if isinstance(exception, SphinxError):
        print_red(f'{exception.category}!')

    if isinstance(exception, UnicodeError):
        print_red(__('Encoding error!'))

    if isinstance(exception, RecursionError):
        print_red(__('Recursion error!'))
        print_err()
        print_err(
            __(
                'This can happen with very large or deeply nested source '
                'files. You can carefully increase the default Python '
                'recursion limit of 1,000 in conf.py with e.g.:'
            )
        )
        print_err('\n    import sys\n    sys.setrecursionlimit(1_500)\n')

    print_err()
    error_context = full_exception_context(
        exception,
        message_log=message_log,
        extensions=extensions,
        full_traceback=print_traceback or use_pdb,
    )
    print_err(error_context)
    print_err()

    if use_pdb:
        from pdb import post_mortem

        print_red(__('Starting debugger:'))
        post_mortem(exception.__traceback__)
        return

    # Save full traceback to log file
    traceback_info_path = save_traceback(
        exception, message_log=message_log, extensions=extensions
    )
    print_err(__('The full traceback has been saved in:'))
    print_err(traceback_info_path)
    print_err()
    print_err(
        __(
            'To report this error to the developers, please open an issue '
            'at <https://github.com/sphinx-doc/sphinx/issues/>. Thanks!'
        )
    )
    print_err(
        __(
            'Please also report this if it was a user error, so '
            'that a better error message can be provided next time.'
        )
    )
