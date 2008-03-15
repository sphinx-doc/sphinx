.. highlight:: rest

Miscellaneous markup
====================

File-wide metadata
------------------

reST has the concept of "field lists"; these are a sequence of fields marked up
like this::

   :Field name: Field content

A field list at the very top of a file is parsed as the "docinfo", which in
normal documents can be used to record the author, date of publication and
other metadata.  In Sphinx, the docinfo is used as metadata, too, but not
displayed in the output.

At the moment, only one metadata field is recognized:

``nocomments``
   If set, the web application won't display a comment form for a page generated
   from this source file.


Meta-information markup
-----------------------

.. directive:: sectionauthor

   Identifies the author of the current section.  The argument should include
   the author's name such that it can be used for presentation and email
   address.  The domain name portion of the address should be lower case.
   Example::

      .. sectionauthor:: Guido van Rossum <guido@python.org>

   By default, this markup isn't reflected in the output in any way (it helps
   keep track of contributions), but you can set the configuration value
   :confval:`show_authors` to True to make them produce a paragraph in the
   output.
