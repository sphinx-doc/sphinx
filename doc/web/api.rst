.. _websupportapi:

Web Support API
===============

.. module:: sphinx.websupport.api
.. class:: WebSupport

   The :class:`WebSupport` class provides a central interface for 
   working with Sphinx documentation.

.. method:: init(srcdir='', outdir='')

   Initialize attributes.

.. method:: build()

   Build the data used by the web support package.

.. method:: get_document(docname)

   Retrieve the context dictionary corresponding to the *docname*.
