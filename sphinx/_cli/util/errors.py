from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING
from pathlib import Path
from traceback import TracebackException
from collections import defaultdict, Counter

from sphinx.errors import SphinxError, SphinxParallelError
from sphinx._cli.util.colour import red, yellow, blue, bold

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
    pretty: bool = True,
) -> None:
    from bdb import BdbQuit

    from docutils.utils import SystemMessage

    from sphinx.locale import __

    if isinstance(exception, BdbQuit):
        return

    def print_err(*values: str) -> None:
        print(*values, file=stderr)

    def print_red(*values: str) -> None:
        print_err(*map(red, values))

    def print_yellow(*values: str) -> None:
        print_err(*map(yellow, values))

    def print_blue(*values: str) -> None:
        print_err(*map(blue, values))

    def print_bold(*values: str) -> None:
        print_err(*map(bold, values))

    print_err()
    if not use_pdb and isinstance(exception, KeyboardInterrupt):
        print_err(__('Interrupted!'))
        return

    # Pretty error mode - only use if not explicitly requesting full output
    if pretty and not print_traceback and not use_pdb:
        try:
            pretty_exception_context(
                exception,
                message_log=message_log,
                extensions=extensions,
                stderr=stderr,
                print_red=print_red,
                print_yellow=print_yellow,
                print_blue=print_blue,
                print_bold=print_bold,
                print_err=print_err,
            )
            return
        except Exception:
            # Fall back to full output if pretty formatting fails
            pass

    # Legacy full output for --show-traceback, pdb, or fallback
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


def _extract_code_frame(exception: BaseException) -> tuple[str, int, int] | None:
    """Extract source code context around the error location."""
    import inspect
    from docutils.utils import get_source_line

    try:
        # Get the traceback
        tb = exception.__traceback__
        if tb is None:
            return None

        # Get the frame where the error occurred
        frame = tb.tb_frame
        if frame is None:
            return None

        # Get filename and line number
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        # Try to get the source line
        try:
            lines, line_number = get_source_line(filename, lineno)
        except (OSError, IndexError, TypeError):
            return None

        # Extract a few lines around the error
        start_line = max(1, line_number - 2)
        end_line = min(len(lines), line_number + 2)
        context_lines = lines[start_line-1:end_line]

        return '\n'.join(context_lines), line_number, line_number - start_line + 1

    except Exception:
        return None


def _get_error_hints(exception: BaseException) -> list[str]:
    """Provide actionable hints for common errors."""
    hints: list[str] = []
    error_str = str(exception).lower()

    # SphinxError hints
    if isinstance(exception, SphinxError):
        if 'reference' in error_str and 'not found' in error_str:
            hints.extend([
                "Check if the referenced document, section, or target exists",
                "Verify spelling and case sensitivity of the reference",
                "Use :doc:`path/to/doc` for document references",
                "Use :ref:`label` for cross-references with labels"
            ])
        elif 'role' in error_str and ('not' in error_str or 'unknown' in error_str):
            hints.extend([
                "Check if the role is defined or installed",
                "Verify the role syntax: :role:`content`",
                "Install missing extensions that provide this role"
            ])
        elif 'directive' in error_str:
            hints.extend([
                "Check directive syntax and required options",
                "Verify the directive is supported by the domain",
                "Ensure all required arguments are provided"
            ])
        elif 'template' in error_str:
            hints.extend([
                "Check template variable names and syntax",
                "Ensure the template file exists and is readable",
                "Verify Jinja2 template syntax is correct"
            ])

    # ImportError hints
    elif isinstance(exception, ImportError):
        hints.extend([
            "Check if the module/package is installed",
            "Verify the import path is correct",
            "Ensure Python path includes the required directories"
        ])

    # FileNotFoundError hints
    elif isinstance(exception, FileNotFoundError):
        hints.extend([
            "Check if the file path is correct",
            "Verify the file exists and is readable",
            "Check for typos in the filename"
        ])

    # Unicode errors
    elif isinstance(exception, UnicodeError):
        hints.extend([
            "Check file encoding - try adding 'utf-8' to source_suffix",
            "Use :encoding: utf-8 in the document header",
            "Ensure source files are saved with UTF-8 encoding"
        ])

    return hints


def _group_warnings(message_log: Collection[str]) -> dict[str, int]:
    """Group similar warning messages and count occurrences."""
    groups: dict[str, int] = defaultdict(int)

    for msg in message_log:
        # Extract the core message (remove location prefixes)
        core_msg = msg
        # Remove common prefixes like "WARNING: ", "doc.rst:123: ", etc.
        prefixes = [
            r'WARNING: ',
            r'ERROR: ',
            r'^[^:]+:\d+:\s*',  # filename:line:
            r'^[^:]+:\s*',      # filename:
        ]

        for prefix in prefixes:
            core_msg = re.sub(prefix, '', core_msg, flags=re.IGNORECASE)

        groups[core_msg.strip()] += 1

    return dict(groups)


def pretty_exception_context(
    exception: BaseException,
    *,
    message_log: Collection[str] = (),
    extensions: Collection[Extension] = (),
    stderr: SupportsWrite,
    print_red: callable,
    print_yellow: callable,
    print_blue: callable,
    print_bold: callable,
    print_err: callable,
) -> None:
    """Format exception with pretty, actionable output."""
    from sphinx.locale import __

    # Get error location and code frame
    code_frame = _extract_code_frame(exception)

    # Get actionable hints
    hints = _get_error_hints(exception)

    # Group warnings
    grouped_warnings = _group_warnings(message_log)

    # Print main error
    print_bold('ERROR')
    print_red(str(exception))
    print_err()

    # Print code frame if available
    if code_frame:
        lines, line_num, pointer_line = code_frame
        print_blue('Source:')
        print_err(lines)
        print_err(' ' * (len(str(line_num)) + pointer_line) + '^')
        print_err()

    # Print actionable hints
    if hints:
        print_yellow('Suggestions:')
        for hint in hints:
            print_err(f'  • {hint}')
        print_err()

    # Print grouped warnings
    if grouped_warnings:
        print_yellow('Warnings:')
        for warning, count in sorted(grouped_warnings.items(), key=lambda x: x[1], reverse=True):
            if count > 1:
                print_err(f'  • {warning} (×{count})')
            else:
                print_err(f'  • {warning}')
        print_err()

    # Print extensions if any
    if extensions:
        ext_names = [ext.name for ext in extensions if ext.version != 'builtin']
        if ext_names:
            print_blue('Loaded extensions:')
            for ext in sorted(ext_names):
                print_err(f'  • {ext}')
            print_err()

    # Always save full traceback to file
    traceback_info_path = save_traceback(
        exception, message_log=message_log, extensions=extensions
    )
    print_blue('Full traceback saved to:')
    print_err(f'  {traceback_info_path}')
    print_err()

    # Add helpful tip
    print_blue('Tip:')
    print_err('  Use --show-traceback (-T) for full Python traceback')
    print_err('  Use --pdb (-P) to debug interactively')
    print_err('  Report issues at: https://github.com/sphinx-doc/sphinx/issues')
    print_err()


