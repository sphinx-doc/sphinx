=================
README for Sphinx
=================

This is the Sphinx documentation generator, see http://sphinx-doc.org/.


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

Releases are signed with `498D6B9E <https://pgp.mit.edu/pks/lookup?op=vindex&search=0x102C2C17498D6B9E>`_


Reading the docs
================

After installing::

   cd doc
   make html

Then, direct your browser to ``_build/html/index.html``.

Or read them online at <http://sphinx-doc.org/>.


Testing
=======

To run the tests with the interpreter available as ``python``, use::

    make test

If you want to use a different interpreter, e.g. ``python3``, use::

    PYTHON=python3 make test

Continuous testing runs on travis:

.. image:: https://travis-ci.org/sphinx-doc/sphinx.svg?branch=master
   :target: https://travis-ci.org/sphinx-doc/sphinx


Contributing
============

#. Check for open issues or open a fresh issue to start a discussion around a
   feature idea or a bug.
#. If you feel uncomfortable or uncertain about an issue or your changes, feel
   free to email sphinx-dev@googlegroups.com.
#. Fork the repository on GitHub https://github.com/sphinx-doc/sphinx
   to start making your changes to the **master** branch for next major
   version, or **stable** branch for next minor version.
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.  Use ``make test`` to run the test suite.
#. Send a pull request and bug the maintainer until it gets merged and
   published.  Make sure to add yourself to AUTHORS
   <https://github.com/sphinx-doc/sphinx/blob/master/AUTHORS> and the change to
   CHANGES <https://github.com/sphinx-doc/sphinx/blob/master/CHANGES>.
