========
 Sphinx
========

.. image:: https://github.com/sphinx-doc/sphinx/actions/workflows/main.yml/badge.svg
   :target: https://github.com/sphinx-doc/sphinx/actions/workflows/main.yml
   :alt: Build Status

.. image:: https://img.shields.io/pypi/v/sphinx.svg
   :target: https://pypi.org/project/Sphinx/
   :alt: Package on PyPI

.. image:: https://readthedocs.org/projects/sphinx/badge/?version=master
   :target: https://www.sphinx-doc.org/
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/License-BSD%202--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-2-Clause
   :alt: BSD 2 Clause

.. image:: https://img.shields.io/pypi/dm/Sphinx?label=PyPI%20Installs
   :target: https://pypistats.org/packages/sphinx
   :alt: Monthly PyPI installs

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

For more information, refer to the `the documentation`_.

Installation
============

Sphinx is published on `PyPI`_ and can be installed from there::

   pip install -U sphinx

We also publish beta releases::

   pip install -U --pre sphinx

If you wish to install Sphinx for development purposes, refer to
`the contributors guide`_.

Contributing
============

We appreciate all contributions! Refer to `the contributors guide`_ for
information.

Release signatures
==================

Releases are signed with following keys:

* `498D6B9E <https://pgp.mit.edu/pks/lookup?op=vindex&search=0x102C2C17498D6B9E>`_
* `5EBA0E07 <https://pgp.mit.edu/pks/lookup?op=vindex&search=0x1425F8CE5EBA0E07>`_

.. _the documentation:
.. _sphinx-doc.org: https://www.sphinx-doc.org/
.. _the contributors guide: https://www.sphinx-doc.org/en/master/internals/contributing.html
.. _PyPI: https://pypi.org/project/Sphinx/
