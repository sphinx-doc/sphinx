.. Sphinx Tests documentation master file, created by sphinx-quickstart on Wed Jun  4 23:49:58 2008.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Sphinx Tests's documentation!
========================================

Contents:

.. toctree::
   :maxdepth: 2
   :numbered:
   :caption: Table of Contents
   :name: mastertoc

   foo
   bar
   http://sphinx-doc.org/

.. only:: html

   Section for HTML
   ----------------

   .. toctree::

      baz

----------
subsection
----------

subsubsection
-------------

Test for issue #1157
====================

This used to crash:

.. toctree::

.. toctree::
   :hidden:

   Latest reference <http://sphinx-doc.org/latest/>
   Python <http://python.org/>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
