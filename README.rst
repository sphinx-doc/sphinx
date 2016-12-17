.. image:: https://img.shields.io/pypi/v/sphinx.svg
   :target: http://pypi.python.org/pypi/sphinx
.. image:: https://readthedocs.org/projects/sphinx/badge/
   :target: http://www.sphinx-doc.org/
   :alt: Documentation Status
.. image:: https://travis-ci.org/sphinx-doc/sphinx.svg?branch=master
   :target: https://travis-ci.org/sphinx-doc/sphinx

=================
README for Sphinx
=================

This is the Sphinx documentation generator, see http://www.sphinx-doc.org/.


Installing
==========

Install from PyPI to use stable version::

   pip install -U sphinx

Install from PyPI to use beta version::

   pip install -U --pre sphinx

Install from newest dev version in stable branch::

   pip install git+https://github.com/sphinx-doc/sphinx@stable

Install from newest dev version in master branch::

   pip install git+https://github.com/sphinx-doc/sphinx

Install from cloned source::

   pip install .

Install from cloned source as editable::

   pip install -e .


Release signatures
==================

Releases are signed with following keys:

* `498D6B9E <https://pgp.mit.edu/pks/lookup?op=vindex&search=0x102C2C17498D6B9E>`_
* `5EBA0E07 <https://pgp.mit.edu/pks/lookup?op=vindex&search=0x1425F8CE5EBA0E07>`_

Reading the docs
================

You can read them online at <http://www.sphinx-doc.org/>.

Or, after installing::

   cd doc
   make html

Then, direct your browser to ``_build/html/index.html``.

Testing
=======

To run the tests with the interpreter available as ``python``, use::

    make test

If you want to use a different interpreter, e.g. ``python3``, use::

    PYTHON=python3 make test

Continuous testing runs on travis: https://travis-ci.org/sphinx-doc/sphinx


Contributing
============

See `CONTRIBUTING.rst`__

.. __: CONTRIBUTING.rst

