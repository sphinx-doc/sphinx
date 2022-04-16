from io import StringIO
from json import dump
import os
import sys

from babel.messages.frontend import compile_catalog
from babel.messages.pofile import read_po

# Provide a "compile_catalog" command that also creates the translated
# JavaScript files if Babel is available.


class Tee:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = StringIO()

    def write(self, s):
        self.stream.write(s)
        self.buffer.write(s)

    def flush(self):
        self.stream.flush()


class compile_catalog_plusjs(compile_catalog):
    """
    An extended command that writes all message strings that occur in
    JavaScript files to a JavaScript file along with the .mo file.

    Unfortunately, babel's setup command isn't built very extensible, so
    most of the run() code is duplicated here.
    """

    def run(self):
        try:
            sys.stderr = Tee(sys.stderr)
            compile_catalog.run(self)
        finally:
            if sys.stderr.buffer.getvalue():
                print("Compiling failed.")
                sys.exit(1)

        if isinstance(self.domain, list):
            for domain in self.domain:
                self._run_domain_js(domain)
        else:
            self._run_domain_js(self.domain)

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

            self.log.info('writing JavaScript strings in catalog %r to %r',
                          po_file, js_file)

            jscatalog = {}
            for message in catalog:
                if any(x[0].endswith(('.js', '.js_t', '.html'))
                       for x in message.locations):
                    msgid = message.id
                    if isinstance(msgid, (list, tuple)):
                        msgid = msgid[0]
                    jscatalog[msgid] = message.string

            with open(js_file, 'wt', encoding='utf8') as outfile:
                outfile.write('Documentation.addTranslations(')
                dump({
                    'messages': jscatalog,
                    'plural_expr': catalog.plural_expr,
                    'locale': str(catalog.locale)
                }, outfile, sort_keys=True, indent=4)
                outfile.write(');')

