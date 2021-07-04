import os
import sys
from distutils import log
from io import StringIO

from setuptools import find_packages, setup

import sphinx

with open('README.rst') as f:
    long_desc = f.read()

if sys.version_info < (3, 6):
    print('ERROR: Sphinx requires at least Python 3.6 to run.')
    sys.exit(1)

install_requires = [
    'sphinxcontrib-applehelp',
    'sphinxcontrib-devhelp',
    'sphinxcontrib-jsmath',
    'sphinxcontrib-htmlhelp',
    'sphinxcontrib-serializinghtml',
    'sphinxcontrib-qthelp',
    'Jinja2>=2.3',
    'Pygments>=2.0',
    'docutils>=0.14,<0.18',
    'snowballstemmer>=1.1',
    'babel>=1.3',
    'alabaster>=0.7,<0.8',
    'imagesize',
    'requests>=2.5.0',
    'setuptools',
    'packaging',
]

extras_require = {
    # Environment Marker works for wheel 0.24 or later
    ':sys_platform=="win32"': [
        'colorama>=0.3.5',
    ],
    'docs': [
        'sphinxcontrib-websupport',
    ],
    'lint': [
        'flake8>=3.5.0',
        'isort',
        'mypy>=0.900',
        'docutils-stubs',
        "types-typed-ast",
        "types-pkg_resources",
        "types-requests",
    ],
    'test': [
        'pytest',
        'pytest-cov',
        'html5lib',
        "typed_ast; python_version < '3.8'",
        'cython',
    ],
}

# Provide a "compile_catalog" command that also creates the translated
# JavaScript files if Babel is available.

cmdclass = {}


class Tee:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = StringIO()

    def write(self, s):
        self.stream.write(s)
        self.buffer.write(s)

    def flush(self):
        self.stream.flush()


try:
    from json import dump

    from babel.messages.frontend import compile_catalog
    from babel.messages.pofile import read_po
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

                with open(js_file, 'wt', encoding='utf8') as outfile:
                    outfile.write('Documentation.addTranslations(')
                    dump({
                        'messages': jscatalog,
                        'plural_expr': catalog.plural_expr,
                        'locale': str(catalog.locale)
                    }, outfile, sort_keys=True, indent=4)
                    outfile.write(');')

    cmdclass['compile_catalog'] = compile_catalog_plusjs


setup(
    name='Sphinx',
    version=sphinx.__version__,
    url='https://sphinx-doc.org/',
    download_url='https://pypi.org/project/Sphinx/',
    license='BSD',
    author='Georg Brandl',
    author_email='georg@python.org',
    description='Python documentation generator',
    long_description=long_desc,
    long_description_content_type='text/x-rst',
    project_urls={
        "Code": "https://github.com/sphinx-doc/sphinx",
        "Issue tracker": "https://github.com/sphinx-doc/sphinx/issues",
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Setuptools Plugin',
        'Framework :: Sphinx',
        'Framework :: Sphinx :: Extension',
        'Framework :: Sphinx :: Theme',
        'Topic :: Documentation',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Printing',
        'Topic :: Software Development',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Indexing',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: LaTeX',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(exclude=['tests', 'utils']),
    package_data = {
        'sphinx': ['py.typed'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx.cmd.build:main',
            'sphinx-quickstart = sphinx.cmd.quickstart:main',
            'sphinx-apidoc = sphinx.ext.apidoc:main',
            'sphinx-autogen = sphinx.ext.autosummary.generate:main',
        ],
        'distutils.commands': [
            'build_sphinx = sphinx.setup_command:BuildDoc',
        ],
    },
    python_requires=">=3.6",
    install_requires=install_requires,
    extras_require=extras_require,
    cmdclass=cmdclass,
)
