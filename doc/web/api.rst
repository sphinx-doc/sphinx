.. _websupportapi:

.. currentmodule:: sphinx.websupport

The WebSupport Class
====================

.. class:: WebSupport

   The main API class for the web support package. All interactions
   with the web support package should occur through this class.

   :param srcdir: the directory containing the reStructuredText files
   :param outdir: the directory in which to place the built data
   :param search: the search system to use
   :param comments: an instance of a CommentBackend
    
Methods
~~~~~~~

.. automethod:: sphinx.websupport.WebSupport.build

.. automethod:: sphinx.websupport.WebSupport.get_document

.. automethod:: sphinx.websupport.WebSupport.get_data

.. automethod:: sphinx.websupport.WebSupport.add_comment

.. automethod:: sphinx.websupport.WebSupport.process_vote

.. automethod:: sphinx.websupport.WebSupport.get_search_results

