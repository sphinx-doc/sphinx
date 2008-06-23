# -*- coding: utf-8 -*-
import ez_setup
ez_setup.use_setuptools()

import sys
from setuptools import setup, Feature

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

* Output formats: HTML (including Windows HTML Help) and LaTeX,
  for printable PDF versions
* Extensive cross-references: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* Hierarchical structure: easy definition of a document tree, with automatic
  links to siblings, parents and children
* Automatic indices: general index as well as a module index
* Code handling: automatic highlighting using the Pygments highlighter
* Various extensions are available, e.g. for automatic testing of snippets
  and inclusion of appropriately formatted docstrings.
'''

requires = ['Pygments>=0.8', 'Jinja>=1.1', 'docutils>=0.4']

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
    packages=['sphinx'],
    include_package_data=True,
    # replaced by the entry points
    #scripts=['sphinx-build.py', 'sphinx-quickstart.py'],
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx:main',
            'sphinx-quickstart = sphinx.quickstart:main'
        ]
    },
    install_requires=requires,
)
