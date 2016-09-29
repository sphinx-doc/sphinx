# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import os
import sys
from distutils import log
from distutils.cmd import Command

import sphinx

long_desc = '''
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of multiple
reStructuredText sources), written by Georg Brandl.  It was originally created
for the new Python documentation, and has excellent facilities for Python
project documentation, but C/C++ is supported as well, and more languages are
planned.

Sphinx uses reStructuredText as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its parsing
and translating suite, the Docutils.

Among its features are the following:

* Output formats: HTML (including derivative formats such as HTML Help, Epub
  and Qt Help), plain text, manual pages and LaTeX or direct PDF output
  using rst2pdf
* Extensive cross-references: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* Hierarchical structure: easy definition of a document tree, with automatic
  links to siblings, parents and children
* Automatic indices: general index as well as a module index
* Code handling: automatic highlighting using the Pygments highlighter
* Flexible HTML output using the Jinja 2 templating engine
* Various extensions are available, e.g. for automatic testing of snippets
  and inclusion of appropriately formatted docstrings
* Setuptools integration
'''

if sys.version_info < (2, 7) or (3, 0) <= sys.version_info < (3, 4):
    print('ERROR: Sphinx requires at least Python 2.7 or 3.4 to run.')
    sys.exit(1)

requires = [
    'six>=1.5',
    'Jinja2>=2.3',
    'Pygments>=2.0',
    'docutils>=0.11',
    'snowballstemmer>=1.1',
    'babel>=1.3,!=2.0',
    'alabaster>=0.7,<0.8',
    'imagesize',
    'requests',
]
extras_require = {
    # Environment Marker works for wheel 0.24 or later
    ':sys_platform=="win32"': [
        'colorama>=0.3.5',
    ],
    'websupport': [
        'sqlalchemy>=0.9',
        'whoosh>=2.0',
    ],
    'test': [
        'nose',
        'mock',  # it would be better for 'test:python_version in 2.7'
        'simplejson',  # better: 'test:platform_python_implementation=="PyPy"'
        'html5lib',
    ],
}

# for sdist installation with pip-1.5.6
if sys.platform == 'win32':
    requires.append('colorama>=0.3.5')

# Provide a "compile_catalog" command that also creates the translated
# JavaScript files if Babel is available.

cmdclass = {}

try:
    from babel.messages.pofile import read_po
    from babel.messages.frontend import compile_catalog
    try:
        from simplejson import dump
    except ImportError:
        from json import dump
except ImportError:
    pass
else:
    class compile_catalog_plusjs(compile_catalog):
        """
        An extended command that writes all message strings that occur in
        JavaScript files to a JavaScript file along with the .mo file.

        Unfortunately, babel's setup command isn't built very extensible, so
        most of the run() code is duplicated here.
        """

        def run(self):
            compile_catalog.run(self)

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
                with open(po_file, 'r') as infile:
                    catalog = read_po(infile, locale)

                if catalog.fuzzy and not self.use_fuzzy:
                    continue

                log.info('writing JavaScript strings in catalog %r to %r',
                         po_file, js_file)

                jscatalog = {}
                for message in catalog:
                    if any(x[0].endswith(('.js', '.js_t', '.html'))
                           for x in message.locations):
                        msgid = message.id
                        if isinstance(msgid, (list, tuple)):
                            msgid = msgid[0]
                        jscatalog[msgid] = message.string

                with open(js_file, 'wb') as outfile:
                    outfile.write('Documentation.addTranslations(')
                    dump(dict(
                        messages=jscatalog,
                        plural_expr=catalog.plural_expr,
                        locale=str(catalog.locale)
                    ), outfile, sort_keys=True)
                    outfile.write(');')

    cmdclass['compile_catalog'] = compile_catalog_plusjs


class CompileGrammarCommand(Command):
    description = 'Compile python grammar file for pycode'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sphinx.pycode.pgen2.driver import compile_grammar

        compile_grammar('sphinx/pycode/Grammar-py2.txt')
        print('sphinx/pycode/Grammar-py2.txt ... done')

        compile_grammar('sphinx/pycode/Grammar-py3.txt')
        print('sphinx/pycode/Grammar-py3.txt ... done')

    def sub_commands(self):
        pass

cmdclass['compile_grammar'] = CompileGrammarCommand


setup(
    name='Sphinx',
    version=sphinx.__version__,
    url='http://sphinx-doc.org/',
    download_url='https://pypi.python.org/pypi/Sphinx',
    license='BSD',
    author='Georg Brandl',
    author_email='georg@python.org',
    description='Python documentation generator',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Framework :: Sphinx',
        'Framework :: Sphinx :: Extension',
        'Framework :: Sphinx :: Theme',
        'Topic :: Documentation',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx:main',
            'sphinx-quickstart = sphinx.quickstart:main',
            'sphinx-apidoc = sphinx.apidoc:main',
            'sphinx-autogen = sphinx.ext.autosummary.generate:main',
        ],
        'distutils.commands': [
            'build_sphinx = sphinx.setup_command:BuildDoc',
        ],
    },
    install_requires=requires,
    extras_require=extras_require,
    cmdclass=cmdclass,
)
