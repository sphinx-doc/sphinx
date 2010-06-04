.. _websupportapi:

Web Support API
===============

.. module:: sphinx.websupport.api
.. class:: WebSupport

   The :class:`WebSupport` class provides a central interface for 
   working with :ref:`~sphinx.websupport.document.Document's.

.. method:: init(srcdir='', outdir='')

   Initialize attributes.

.. method:: get_document(docname)

   Retrieve the :class:`~sphinx.websupport.document.Document` object
   corresponding to the *docname*.

.. module:: sphinx.websupport.document
.. class:: Document
   
   The :class:`Document` provides access to a single document. It
   is not instantiated directly, but is returned by methods of the
   :class:`~sphinx.websupport.api.WebSupport` object.
