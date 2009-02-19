.. highlight:: rest

Miscellaneous markup
====================

.. _metadata:

File-wide metadata
------------------

reST has the concept of "field lists"; these are a sequence of fields marked up
like this::

   :Field name: Field content

A field list at the very top of a file is parsed as the "docinfo", which in
normal documents can be used to record the author, date of publication and
other metadata.  In Sphinx, the docinfo is used as metadata, too, but not
displayed in the output.

At the moment, these metadata fields are recognized:

``tocdepth``
   The maximum depth for a table of contents of this file.

   .. versionadded:: 0.4

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


.. _tags:

Including content based on tags
-------------------------------

.. directive:: .. only:: <expression>

   Include the content of the directive only if the *expression* is true.  The
   expression should consist of tags, like this::

      .. only:: html and draft

   Undefined tags are false, defined tags (via the ``-t`` command-line option or
   within :file:`conf.py`) are true.  Boolean expressions, also using
   parentheses (like ``html and (latex or draft)`` are supported.

   The format of the current builder (``html``, ``latex`` or ``text``) is always
   set as a tag.

   .. versionadded:: 0.6


Tables
------

Use standard reStructuredText tables.  They work fine in HTML output, however
there are some gotchas when using tables in LaTeX: the column width is hard to
determine correctly automatically.  For this reason, the following directive
exists:

.. directive:: .. tabularcolumns:: column spec

   This directive gives a "column spec" for the next table occurring in the
   source file.  The spec is the second argument to the LaTeX ``tabulary``
   package's environment (which Sphinx uses to translate tables).  It can have
   values like ::

      |l|l|l|

   which means three left-adjusted, nonbreaking columns.  For columns with
   longer text that should automatically be broken, use either the standard
   ``p{width}`` construct, or tabulary's automatic specifiers:

   +-----+------------------------------------------+
   |``L``| ragged-left column with automatic width  |
   +-----+------------------------------------------+
   |``R``| ragged-right column with automatic width |
   +-----+------------------------------------------+
   |``C``| centered column with automatic width     |
   +-----+------------------------------------------+
   |``J``| justified column with automatic width    |
   +-----+------------------------------------------+

   The automatic width is determined by rendering the content in the table, and
   scaling them according to their share of the total width.

   By default, Sphinx uses a table layout with ``L`` for every column.

   .. versionadded:: 0.3

.. warning::

   Tables that contain literal blocks cannot be set with ``tabulary``.  They are
   therefore set with the standard LaTeX ``tabular`` environment.  Also, the
   verbatim environment used for literal blocks only works in ``p{width}``
   columns, which means that by default, Sphinx generates such column specs for
   such tables.  Use the :dir:`tabularcolumns` directive to get finer control
   over such tables.
