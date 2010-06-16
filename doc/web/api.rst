.. _websupportapi:

Web Support API
===============

.. module:: sphinx.websupport.api
.. class:: WebSupport

   The :class:`WebSupport` class provides a central interface for 
   working with Sphinx documentation.

.. method:: init(srcdir='', outdir='')

   Initialize attributes.

.. method:: get_document(docname)

   Retrieve the context dictionary corresponding to the *docname*.
