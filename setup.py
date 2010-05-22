# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import os
import sys
from distutils import log

import sphinx

long_desc = '''
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of
multiple reStructuredText sources), written by Georg Brandl.
It was originally created to translate the new Python documentation,
but has now been cleaned up in the hope that it will be useful to many
other projects.

Sphinx uses reStructuredText as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its
parsing and translating suite, the Docutils.

Although it is still under constant development, the following features
are already present, work fine and can be seen "in action" in the Python docs:

* Output formats: HTML (including Windows HTML Help), plain text and LaTeX,
  for printable PDF versions
* Extensive cross-references: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* Hierarchical structure: easy definition of a document tree, with automatic
  links to siblings, parents and children
* Automatic indices: general index as well as a module index
* Code handling: automatic highlighting using the Pygments highlighter
* Various extensions are available, e.g. for automatic testing of snippets
  and inclusion of appropriately formatted docstrings.

A development egg can be found `here
<http://bitbucket.org/birkenfeld/sphinx/get/tip.gz#egg=Sphinx-dev>`_.
'''

requires = ['Pygments>=0.8', 'Jinja2>=2.1', 'docutils>=0.4']

if sys.version_info < (2, 4):
    print 'ERROR: Sphinx requires at least Python 2.4 to run.'
    sys.exit(1)

if sys.version_info < (2, 5):
    # Python 2.4's distutils doesn't automatically install an egg-info,
    # so an existing docutils install won't be detected -- in that case,
    # remove the dependency from setup.py
    try:
        import docutils
        if int(docutils.__version__[2]) < 4:
            raise ValueError('docutils not recent enough')
    except:
        pass
    else:
        del requires[-1]


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

            po_files = []
            js_files = []

            if not self.input_file:
                if self.locale:
                    po_files.append((self.locale,
                                     os.path.join(self.directory, self.locale,
                                                  'LC_MESSAGES',
                                                  self.domain + '.po')))
                    js_files.append(os.path.join(self.directory, self.locale,
                                                 'LC_MESSAGES',
                                                 self.domain + '.js'))
                else:
                    for locale in os.listdir(self.directory):
                        po_file = os.path.join(self.directory, locale,
                                               'LC_MESSAGES',
                                               self.domain + '.po')
                        if os.path.exists(po_file):
                            po_files.append((locale, po_file))
                            js_files.append(os.path.join(self.directory, locale,
                                                         'LC_MESSAGES',
                                                         self.domain + '.js'))
            else:
                po_files.append((self.locale, self.input_file))
                if self.output_file:
                    js_files.append(self.output_file)
                else:
                    js_files.append(os.path.join(self.directory, self.locale,
                                                 'LC_MESSAGES',
                                                 self.domain + '.js'))

            for js_file, (locale, po_file) in zip(js_files, po_files):
                infile = open(po_file, 'r')
                try:
                    catalog = read_po(infile, locale)
                finally:
                    infile.close()

                if catalog.fuzzy and not self.use_fuzzy:
                    continue

                log.info('writing JavaScript strings in catalog %r to %r',
                         po_file, js_file)

                jscatalog = {}
                for message in catalog:
                    if any(x[0].endswith('.js') for x in message.locations):
                        msgid = message.id
                        if isinstance(msgid, (list, tuple)):
                            msgid = msgid[0]
                        jscatalog[msgid] = message.string

                outfile = open(js_file, 'wb')
                try:
                    outfile.write('Documentation.addTranslations(');
                    dump(dict(
                        messages=jscatalog,
                        plural_expr=catalog.plural_expr,
                        locale=str(catalog.locale)
                        ), outfile)
                    outfile.write(');')
                finally:
                    outfile.close()

    cmdclass['compile_catalog'] = compile_catalog_plusjs


setup(
    name='Sphinx',
    version=sphinx.__version__,
    url='http://sphinx.pocoo.org/',
    download_url='http://pypi.python.org/pypi/Sphinx',
    license='BSD',
    author='Georg Brandl',
    author_email='georg@python.org',
    description='Python documentation generator',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx:main',
            'sphinx-quickstart = sphinx.quickstart:main',
            'sphinx-autogen = sphinx.ext.autosummary.generate:main',
        ],
        'distutils.commands': [
            'build_sphinx = sphinx.setup_command:BuildDoc',
        ],
    },
    install_requires=requires,
    cmdclass=cmdclass,
)
