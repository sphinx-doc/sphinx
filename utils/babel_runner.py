"""Run babel for translations.

Usage:

babel_runner.py extract
    Extract messages from the source code and update the ".pot" template file.

babel_runner.py update
    Update all language catalogues in "sphinx/locale/<language>/LC_MESSAGES"
    with the current messages in the template file.

babel_runner.py compile
    Compile the ".po" catalogue files to ".mo" and ".js" files.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from os import environ
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.extract import (
    DEFAULT_KEYWORDS,
    extract,
    extract_javascript,
    extract_python,
)
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po
from babel.util import pathmatch
from jinja2.ext import babel_extract as extract_jinja2

IS_CI = 'CI' in environ
ROOT = Path(__file__).resolve().parent.parent
TEX_DELIMITERS = {
    'variable_start_string': '<%=',
    'variable_end_string': '%>',
    'block_start_string': '<%',
    'block_end_string': '%>',
}
METHOD_MAP = [
    # Extraction from Python source files
    ('**.py', extract_python),
    # Extraction from Jinja2 template files
    ('**/templates/latex/**.tex.jinja', extract_jinja2),
    ('**/templates/latex/**.tex_t', extract_jinja2),
    ('**/templates/latex/**.sty.jinja', extract_jinja2),
    ('**/templates/latex/**.sty_t', extract_jinja2),
    # Extraction from Jinja2 HTML templates
    ('**/themes/**.html', extract_jinja2),
    # Extraction from Jinja2 XML templates
    ('**/themes/**.xml', extract_jinja2),
    # Extraction from JavaScript files
    ('**.js', extract_javascript),
    ('**.js.jinja', extract_javascript),
    ('**.js_t', extract_javascript),
]
OPTIONS_MAP = {
    # Extraction from Python source files
    '**.py': {
        'encoding': 'utf-8',
    },
    # Extraction from Jinja2 template files
    '**/templates/latex/**.tex.jinja': TEX_DELIMITERS.copy(),
    '**/templates/latex/**.tex_t': TEX_DELIMITERS.copy(),
    '**/templates/latex/**.sty.jinja': TEX_DELIMITERS.copy(),
    '**/templates/latex/**.sty_t': TEX_DELIMITERS.copy(),
    # Extraction from Jinja2 HTML templates
    '**/themes/**.html': {
        'encoding': 'utf-8',
        'ignore_tags': 'script,style',
        'include_attrs': 'alt title summary',
    },
}
KEYWORDS = {**DEFAULT_KEYWORDS, '_': None, '__': None}


def run_extract() -> None:
    """Message extraction function."""
    log = _get_logger()

    with open('sphinx/__init__.py', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('__version__: Final = '):
            # remove prefix; strip whitespace; remove quotation marks
            sphinx_version = line[21:].strip()[1:-1]
            break

    catalogue = Catalog(project='Sphinx', version=sphinx_version, charset='utf-8')

    base = ROOT / 'sphinx'
    for filename in base.rglob('*'):
        relative_name = filename.relative_to(base)
        for pattern, method in METHOD_MAP:
            if not pathmatch(pattern, str(relative_name)):
                continue

            options = {}
            for opt_pattern, opt_dict in OPTIONS_MAP.items():
                if pathmatch(opt_pattern, str(relative_name)):
                    options = opt_dict
            with open(filename, 'rb') as fileobj:
                for lineno, message, comments, context in extract(
                    method,  # type: ignore[arg-type]
                    fileobj,
                    KEYWORDS,
                    options=options,
                ):
                    catalogue.add(
                        message,
                        None,
                        [(str(relative_name), lineno)],
                        auto_comments=comments,
                        context=context,
                    )
            break

    output_file = ROOT / 'sphinx' / 'locale' / 'sphinx.pot'
    log.info('writing PO template file to %s', output_file.relative_to(ROOT))
    with open(output_file, 'wb') as outfile:
        write_po(outfile, catalogue)


def run_update() -> None:
    """Catalog merging command."""
    log = _get_logger()

    domain = 'sphinx'
    locale_dir = ROOT / 'sphinx' / 'locale'
    template_file = locale_dir / 'sphinx.pot'

    with open(template_file, encoding='utf-8') as infile:
        template = read_po(infile)

    for locale in locale_dir.iterdir():
        filename = locale / 'LC_MESSAGES' / f'{domain}.po'
        if not filename.exists():
            continue

        log.info(
            'updating catalogue %s based on %s',
            filename.relative_to(ROOT),
            template_file.relative_to(ROOT),
        )
        with open(filename, encoding='utf-8') as infile:
            catalogue = read_po(infile, locale=locale.name, domain=domain)

        catalogue.update(template)
        tmp_name = filename.parent / (tempfile.gettempprefix() + filename.name)
        try:
            with open(tmp_name, 'wb') as tmpfile:
                write_po(tmpfile, catalogue)
        except Exception:
            tmp_name.unlink()
            raise

        tmp_name.replace(filename)


def run_compile() -> None:
    """Catalogue compilation command.

    An extended command that writes all message strings that occur in
    JavaScript files to a JavaScript file along with the .mo file.

    Unfortunately, babel's setup command isn't built very extensible, so
    most of the run() code is duplicated here.
    """
    log = _get_logger()

    directory = ROOT / 'sphinx' / 'locale'
    total_errors = {}

    for locale in directory.iterdir():
        po_file = locale / 'LC_MESSAGES' / 'sphinx.po'
        if not po_file.exists():
            continue

        with open(po_file, encoding='utf-8') as infile:
            catalogue = read_po(infile, locale=locale.name)

        if catalogue.fuzzy:
            log.info(
                'catalogue %s is marked as fuzzy, skipping', po_file.relative_to(ROOT)
            )
            continue

        locale_errors = 0
        for message, errors in catalogue.check():
            for error in errors:
                locale_errors += 1
                log.error(
                    'error: %s:%d: %s\nerror:     in message string: %r',
                    po_file.relative_to(ROOT),
                    message.lineno,
                    error,
                    message.string,
                )

        if locale_errors:
            total_errors[locale.name] = locale_errors
            log.info(
                '%d errors encountered in %r locale, skipping',
                locale_errors,
                locale.name,
            )
            continue

        mo_file = locale / 'LC_MESSAGES' / 'sphinx.mo'
        log.info(
            'compiling catalogue %s to %s',
            po_file.relative_to(ROOT),
            mo_file.relative_to(ROOT),
        )
        with open(mo_file, 'wb') as outfile:
            write_mo(outfile, catalogue, use_fuzzy=False)

        js_file = locale / 'LC_MESSAGES' / 'sphinx.js'
        log.info(
            'writing JavaScript strings in catalogue %s to %s',
            po_file.relative_to(ROOT),
            js_file.relative_to(ROOT),
        )
        js_catalogue = {}
        for message in catalogue:
            if any(
                x[0].endswith(('.js', '.js.jinja', '.js_t', '.html'))
                for x in message.locations
            ):
                msgid = message.id
                if isinstance(msgid, (list, tuple)):
                    msgid = msgid[0]
                js_catalogue[msgid] = message.string

        obj = json.dumps(
            {
                'messages': js_catalogue,
                'plural_expr': catalogue.plural_expr,
                'locale': str(catalogue.locale),
            },
            sort_keys=True,
            indent=4,
        )
        with open(js_file, 'wb') as outfile:
            # to ensure lines end with ``\n`` rather than ``\r\n``:
            outfile.write(f'Documentation.addTranslations({obj});'.encode())

    if total_errors:
        _write_pr_body_line('## Babel catalogue errors')
        _write_pr_body_line('')
        for locale_name, err_count in total_errors.items():
            log.error(
                'error: %d errors encountered in %r locale.', err_count, locale_name
            )
            s = 's' if err_count != 1 else ''
            _write_pr_body_line(f'* {locale_name}: {err_count} error{s}')


def _get_logger() -> logging.Logger:
    log = logging.getLogger('babel')
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(handler)
    return log


def _write_pr_body_line(message: str) -> None:
    if not IS_CI:
        return
    with open('babel_compile.txt', 'a', encoding='utf-8') as f:
        f.write(f'{message}\n')


if __name__ == '__main__':
    try:
        action = sys.argv[1].lower()
    except IndexError:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2) from None

    if action == 'extract':
        run_extract()
    elif action == 'update':
        run_update()
    elif action == 'compile':
        run_compile()
    elif action == 'all':
        run_extract()
        run_update()
        run_compile()
    else:
        msg = f"invalid action: '{action}'"
        raise ValueError(msg)
    raise SystemExit
