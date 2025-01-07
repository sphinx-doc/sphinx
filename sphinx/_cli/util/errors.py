from __future__ import annotations

import re
import sys
import tempfile
from typing import TYPE_CHECKING, TextIO

from sphinx.errors import SphinxParallelError

if TYPE_CHECKING:
    from typing import Final

    from sphinx.application import Sphinx


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


def format_traceback(app: Sphinx | None, exc: BaseException) -> str:
    """Format the given exception's traceback with environment information."""
    if isinstance(exc, SphinxParallelError):
        exc_format = '(Error in parallel process)\n' + exc.traceback
    else:
        import traceback

        exc_format = traceback.format_exc()

    last_msgs = exts_list = ''
    if app is not None:
        extensions = app.extensions.values()
        last_msgs = '\n'.join(f'* {strip_escape_sequences(s)}' for s in app.messagelog)
        exts_list = '\n'.join(
            f'* {ext.name} ({ext.version})'
            for ext in extensions
            if ext.version != 'builtin'
        )

    return error_info(last_msgs, exts_list, exc_format)


def save_traceback(app: Sphinx | None, exc: BaseException) -> str:
    """Save the given exception's traceback in a temporary file."""
    output = format_traceback(app=app, exc=exc)
    filename = write_temporary_file(output)
    return filename


def write_temporary_file(content: str) -> str:
    """Write content to a temporary file and return the filename."""
    with tempfile.NamedTemporaryFile(
        'w', encoding='utf-8', suffix='.log', prefix='sphinx-err-', delete=False
    ) as f:
        f.write(content)

    return f.name


def handle_exception(
    exception: BaseException,
    /,
    *,
    stderr: TextIO = sys.stderr,
    use_pdb: bool = False,
    print_traceback: bool = False,
    app: Sphinx | None = None,
) -> None:
    from bdb import BdbQuit
    from traceback import TracebackException, print_exc

    from docutils.utils import SystemMessage

    from sphinx._cli.util.colour import red
    from sphinx.errors import SphinxError
    from sphinx.locale import __

    if isinstance(exception, BdbQuit):
        return

    def print_err(*values: str) -> None:
        print(*values, file=stderr)

    def print_red(*values: str) -> None:
        print_err(*map(red, values))

    print_err()
    if print_traceback or use_pdb:
        print_exc(file=stderr)
        print_err()

    if use_pdb:
        from pdb import post_mortem

        print_red(__('Exception occurred, starting debugger:'))
        post_mortem()
        return

    if isinstance(exception, KeyboardInterrupt):
        print_err(__('Interrupted!'))
        return

    if isinstance(exception, SystemMessage):
        print_red(__('reStructuredText markup error:'))
        print_err(str(exception))
        return

    if isinstance(exception, SphinxError):
        print_red(f'{exception.category}:')
        print_err(str(exception))
        return

    if isinstance(exception, UnicodeError):
        print_red(__('Encoding error:'))
        print_err(str(exception))
        return

    if isinstance(exception, RecursionError):
        print_red(__('Recursion error:'))
        print_err(str(exception))
        print_err()
        print_err(
            __(
                'This can happen with very large or deeply nested source '
                'files. You can carefully increase the default Python '
                'recursion limit of 1000 in conf.py with e.g.:'
            )
        )
        print_err('\n    import sys\n    sys.setrecursionlimit(1_500)\n')
        return

    # format an exception with traceback, but only the last frame.
    te = TracebackException.from_exception(exception, limit=-1)
    formatted_tb = te.stack.format()[-1] + ''.join(te.format_exception_only()).rstrip()

    print_red(__('Exception occurred:'))
    print_err(formatted_tb)
    traceback_info_path = save_traceback(app, exception)
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
