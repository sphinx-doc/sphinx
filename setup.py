# -*- coding: utf-8 -*-
import ez_setup
ez_setup.use_setuptools()
import sphinx

from setuptools import setup, Feature

long_desc = '''
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects, written by Georg Brandl.
It was originally created to translate the new Python documentation,
but has now been cleaned up in the hope that it will be useful to many
other projects.

Although it is still under constant development, the following features
are already present, work fine and can be seen “in action” in the Python docs:

* Output formats: HTML (including Windows HTML Help) and LaTeX,
  for printable PDF versions
* Extensive cross-references: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* Hierarchical structure: easy definition of a document tree, with automatic
  links to siblings, parents and children
* Automatic indices: general index as well as a module index
* Code handling: automatic highlighting using the Pygments highlighter

Sphinx uses reStructuredText as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its
parsing and translating suite, the Docutils.
'''

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
    lassifiers=[
        'Development Status :: 2 - Pre-Alpha',
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
    scripts=['sphinx-build.py', 'sphinx-web.py', 'sphinx-quickstart.py'],
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx:main',
            'sphinx-web = sphinx.web:main',
            'sphinx-quickstart = sphinx.quickstart:main'
        ]
    },
    install_requires=['Pygments>=0.8', 'docutils==0.4']
)
