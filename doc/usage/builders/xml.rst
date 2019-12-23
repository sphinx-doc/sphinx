===
XML
===

XML builder
-----------

.. versionadded:: 1.2

This builder produces Docutils-native XML files. The output can be transformed
with standard XML tools such as XSLT processors into arbitrary final forms.

.. module:: sphinx.builders.xml
.. class:: XMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Pseudo XML builder
------------------

.. versionadded:: 1.2

This builder is used for debugging the Sphinx/Docutils "Reader to Transform
to Writer" pipeline. It produces compact pretty-printed "pseudo-XML", files
where nesting is indicated by indentation (no end-tags). External
attributes for all elements are output, and internal attributes for any
leftover "pending" elements are also given.

.. class:: PseudoXMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types
