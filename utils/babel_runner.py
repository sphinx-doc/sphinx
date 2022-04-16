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

from babel.messages.frontend import compile_catalog, extract_messages, update_catalog
from babel.messages.pofile import read_po

import sphinx

ROOT = os.path.realpath(os.path.join(os.path.abspath(__file__), "..", ".."))


class compile_catalog_plusjs(compile_catalog):  # NoQA
    """
    An extended command that writes all message strings that occur in
    JavaScript files to a JavaScript file along with the .mo file.

    Unfortunately, babel's setup command isn't built very extensible, so
    most of the run() code is duplicated here.
    """

    def run(self):
        if super().run():
            print("Compiling failed.", file=sys.stderr)
            raise SystemExit(2)

        for domain in self.domain:
            self._run_domain_js(domain)

    def _run_domain_js(self, domain):
        po_files = []
        js_files = []

        if not self.input_file:
            if self.locale:
                po_files.append((self.locale,
                                 os.path.join(self.directory, self.locale,
                                              'LC_MESSAGES',
                                              domain + '.po')))
                js_files.append(os.path.join(self.directory, self.locale,
                                             'LC_MESSAGES',
                                             domain + '.js'))
            else:
                for locale in os.listdir(self.directory):
                    po_file = os.path.join(self.directory, locale,
                                           'LC_MESSAGES',
                                           domain + '.po')
                    if os.path.exists(po_file):
                        po_files.append((locale, po_file))
                        js_files.append(os.path.join(self.directory, locale,
                                                     'LC_MESSAGES',
                                                     domain + '.js'))
        else:
            po_files.append((self.locale, self.input_file))
            if self.output_file:
                js_files.append(self.output_file)
            else:
                js_files.append(os.path.join(self.directory, self.locale,
                                             'LC_MESSAGES',
                                             domain + '.js'))

        for js_file, (locale, po_file) in zip(js_files, po_files):
            with open(po_file, encoding='utf8') as infile:
                catalog = read_po(infile, locale)

            if catalog.fuzzy and not self.use_fuzzy:
                continue

            self.log.info('writing JavaScript strings in catalog %s to %s',
                          po_file, js_file)

            jscatalog = {}
            for message in catalog:
                if any(x[0].endswith(('.js', '.js_t', '.html'))
                       for x in message.locations):
                    msgid = message.id
                    if isinstance(msgid, (list, tuple)):
                        msgid = msgid[0]
                    jscatalog[msgid] = message.string

            obj = json.dumps({
                'messages': jscatalog,
                'plural_expr': catalog.plural_expr,
                'locale': f'{catalog.locale!s}'
            }, sort_keys=True, indent=4)
            with open(js_file, 'w', encoding='utf8') as outfile:
                outfile.write(f'Documentation.addTranslations({obj});')


def _get_logger():
    log = logging.getLogger('babel')
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(handler)
    return log


def run_extract():
    os.chdir(ROOT)
    command = extract_messages()
    command.log = _get_logger()
    command.initialize_options()

    command.keywords = "_ __ l_ lazy_gettext"
    command.mapping_file = "babel.cfg"
    command.output_file = os.path.join("sphinx", "locale", "sphinx.pot")
    command.project = "Sphinx"
    command.version = sphinx.__version__
    command.input_paths = "sphinx"

    command.finalize_options()
    return command.run()


def run_update():
    os.chdir(ROOT)
    command = update_catalog()
    command.log = _get_logger()
    command.initialize_options()

    command.domain = "sphinx"
    command.input_file = os.path.join("sphinx", "locale", "sphinx.pot")
    command.output_dir = os.path.join("sphinx", "locale")

    command.finalize_options()
    return command.run()


def run_compile():
    os.chdir(ROOT)
    command = compile_catalog_plusjs()
    command.log = _get_logger()
    command.initialize_options()

    command.domain = "sphinx"
    command.directory = os.path.join("sphinx", "locale")

    command.finalize_options()
    return command.run()


if __name__ == '__main__':
    try:
        action = sys.argv[1].lower()
    except IndexError:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)

    if action == "extract":
        raise SystemExit(run_extract())
    if action == "update":
        raise SystemExit(run_update())
    if action == "compile":
        raise SystemExit(run_compile())
