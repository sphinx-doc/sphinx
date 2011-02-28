.. _searchadapters:

.. currentmodule:: sphinx.websupport.search

Search Adapters
===============

To create a custom search adapter you will need to subclass the
:class:`BaseSearch` class.  Then create an instance of the new class and pass
that as the `search` keyword argument when you create the :class:`~.WebSupport`
object::

   support = WebSupport(srcdir=srcdir,
                        builddir=builddir,
                        search=MySearch())

For more information about creating a custom search adapter, please see the
documentation of the :class:`BaseSearch` class below.

.. class:: BaseSearch

   Defines an interface for search adapters.


BaseSearch Methods
~~~~~~~~~~~~~~~~~~

   The following methods are defined in the BaseSearch class. Some methods do
   not need to be overridden, but some (:meth:`~BaseSearch.add_document` and
   :meth:`~BaseSearch.handle_query`) must be overridden in your subclass. For a
   working example, look at the built-in adapter for whoosh.

.. automethod:: BaseSearch.init_indexing

.. automethod:: BaseSearch.finish_indexing

.. automethod:: BaseSearch.feed

.. automethod:: BaseSearch.add_document

.. automethod:: BaseSearch.query

.. automethod:: BaseSearch.handle_query

.. automethod:: BaseSearch.extract_context
