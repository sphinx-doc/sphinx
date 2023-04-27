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

import json
import logging
import os
import sys
import tempfile

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

ROOT = os.path.realpath(os.path.join(os.path.abspath(__file__), "..", ".."))
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
    ('**/templates/latex/**.tex_t', extract_jinja2),
    ('**/templates/latex/**.sty_t', extract_jinja2),
    # Extraction from Jinja2 HTML templates
    ('**/themes/**.html', extract_jinja2),
    # Extraction from Jinja2 XML templates
    ('**/themes/**.xml', extract_jinja2),
    # Extraction from JavaScript files
    ('**.js', extract_javascript),
    ('**.js_t', extract_javascript),
]
OPTIONS_MAP = {
    # Extraction from Python source files
    '**.py': {
        'encoding': 'utf-8',
    },
    # Extraction from Jinja2 template files
    '**/templates/latex/**.tex_t': TEX_DELIMITERS.copy(),
    '**/templates/latex/**.sty_t': TEX_DELIMITERS.copy(),
    # Extraction from Jinja2 HTML templates
    '**/themes/**.html': {
        'encoding': 'utf-8',
        'ignore_tags': 'script,style',
        'include_attrs': 'alt title summary',
    },
}
KEYWORDS = {**DEFAULT_KEYWORDS, '_': None, '__': None}


def run_extract():
    """Message extraction function."""
    log = _get_logger()

    with open('sphinx/__init__.py', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line.startswith('__version__ = '):
                # remove prefix; strip whitespace; remove quotation marks
                sphinx_version = line[14:].strip()[1:-1]
                break

    input_path = 'sphinx'
    catalogue = Catalog(project='Sphinx', version=sphinx_version, charset='utf-8')

    base = os.path.abspath(input_path)
    for root, dirnames, filenames in os.walk(base):
        relative_root = os.path.relpath(root, base) if root != base else ''
        dirnames.sort()
        for filename in sorted(filenames):
            relative_name = os.path.join(relative_root, filename)
            for pattern, method in METHOD_MAP:
                if not pathmatch(pattern, relative_name):
                    continue

                options = {}
                for opt_pattern, opt_dict in OPTIONS_MAP.items():
                    if pathmatch(opt_pattern, relative_name):
                        options = opt_dict
                with open(os.path.join(root, filename), 'rb') as fileobj:
                    for lineno, message, comments, context in extract(
                        method, fileobj, KEYWORDS, options=options,
                    ):
                        filepath = os.path.join(input_path, relative_name)
                        catalogue.add(
                            message, None, [(filepath, lineno)],
                            auto_comments=comments, context=context,
                        )
                break

    output_file = os.path.join('sphinx', 'locale', 'sphinx.pot')
    log.info('writing PO template file to %s', output_file)
    with open(output_file, 'wb') as outfile:
        write_po(outfile, catalogue)


def run_update():
    """Catalog merging command."""

    log = _get_logger()

    domain = 'sphinx'
    locale_dir = os.path.join('sphinx', 'locale')
    template_file = os.path.join(locale_dir, 'sphinx.pot')

    with open(template_file, encoding='utf-8') as infile:
        template = read_po(infile)

    for locale in os.listdir(locale_dir):
        filename = os.path.join(locale_dir, locale, 'LC_MESSAGES', f'{domain}.po')
        if not os.path.exists(filename):
            continue

        log.info('updating catalog %s based on %s', filename, template_file)
        with open(filename, encoding='utf-8') as infile:
            catalog = read_po(infile, locale=locale, domain=domain)

        catalog.update(template)
        tmp_name = os.path.join(
            os.path.dirname(filename), tempfile.gettempprefix() + os.path.basename(filename),
        )
        try:
            with open(tmp_name, 'wb') as tmpfile:
                write_po(tmpfile, catalog)
        except Exception:
            os.remove(tmp_name)
            raise

        os.replace(tmp_name, filename)


def run_compile():
    """
    Catalog compilation command.

    An extended command that writes all message strings that occur in
    JavaScript files to a JavaScript file along with the .mo file.

    Unfortunately, babel's setup command isn't built very extensible, so
    most of the run() code is duplicated here.
    """

    log = _get_logger()

    directory = os.path.join('sphinx', 'locale')
    total_errors = 0

    for locale in os.listdir(directory):
        po_file = os.path.join(directory, locale, 'LC_MESSAGES', 'sphinx.po')
        if not os.path.exists(po_file):
            continue

        with open(po_file, encoding='utf-8') as infile:
            catalog = read_po(infile, locale)

        if catalog.fuzzy:
            log.info('catalog %s is marked as fuzzy, skipping', po_file)
            continue

        for message, errors in catalog.check():
            for error in errors:
                total_errors += 1
                log.error('error: %s:%d: %s', po_file, message.lineno, error)

        mo_file = os.path.join(directory, locale, 'LC_MESSAGES', 'sphinx.mo')
        log.info('compiling catalog %s to %s', po_file, mo_file)
        with open(mo_file, 'wb') as outfile:
            write_mo(outfile, catalog, use_fuzzy=False)

        js_file = os.path.join(directory, locale, 'LC_MESSAGES', 'sphinx.js')
        log.info('writing JavaScript strings in catalog %s to %s', po_file, js_file)
        js_catalogue = {}
        for message in catalog:
            if any(
                    x[0].endswith(('.js', '.js.jinja', '.js_t', '.html'))
                    for x in message.locations
            ):
                msgid = message.id
                if isinstance(msgid, (list, tuple)):
                    msgid = msgid[0]
                js_catalogue[msgid] = message.string

        obj = json.dumps({
            'messages': js_catalogue,
            'plural_expr': catalog.plural_expr,
            'locale': str(catalog.locale),
        }, sort_keys=True, indent=4)
        with open(js_file, 'wb') as outfile:
            # to ensure lines end with ``\n`` rather than ``\r\n``:
            outfile.write(f'Documentation.addTranslations({obj});'.encode())

    if total_errors > 0:
        log.error('%d errors encountered.', total_errors)
        print("Compiling failed.", file=sys.stderr)
        raise SystemExit(2)


def _get_logger():
    log = logging.getLogger('babel')
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(handler)
    return log


if __name__ == '__main__':
    try:
        action = sys.argv[1].lower()
    except IndexError:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)

    os.chdir(ROOT)
    if action == "extract":
        raise SystemExit(run_extract())
    if action == "update":
        raise SystemExit(run_update())
    if action == "compile":
        raise SystemExit(run_compile())
    if action == "all":
        exit_code = run_extract()
        if exit_code:
            raise SystemExit(exit_code)
        exit_code = run_update()
        if exit_code:
            raise SystemExit(exit_code)
        raise SystemExit(run_compile())
