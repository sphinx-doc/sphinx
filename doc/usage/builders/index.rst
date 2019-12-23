.. _builders:

========
Builders
========

Sphinx builders take parsed documents and perform actions on them. Normally,
builders translate the documents to an output format, but it is also possible
to use the builder to check for broken links in the documentation, or build
coverage information.

This chapter describes the builders provided by Sphinx. If you are interested
in writing your own builders, refer to :doc:`/extdev/builderapi`.


Built-in builders
-----------------

These are the built-in Sphinx builders.  More builders can be added by
:doc:`extensions </usage/extensions/index>`.

.. toctree::

   html
   latex
   xml
   serializing
   others

Extension-based builders
------------------------

A number of built-in Sphinx extensions offer additional builders.

* :mod:`~sphinx.ext.doctest`
* :mod:`~sphinx.ext.coverage`


Third-party builders
--------------------

Additional builders can be distributed as extensions like anything else. For
more information on extensions, refer to :doc:`/usage/extensions/index`.
