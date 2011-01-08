.. highlight:: rest

Miscellaneous markup
====================

.. _metadata:

File-wide metadata
------------------

reST has the concept of "field lists"; these are a sequence of fields marked up
like this::

   :fieldname: Field content

A field list near the top of a file is parsed by docutils as the "docinfo"
which is normally used to record the author, date of publication and other
metadata.  *In Sphinx*, a field list preceding any other markup is moved from
the docinfo to the Sphinx environment as document metadata and is not displayed
in the output; a field list appearing after the document title will be part of
the docinfo as normal and will be displayed in the output.

At the moment, these metadata fields are recognized:

``tocdepth``
   The maximum depth for a table of contents of this file.

   .. versionadded:: 0.4

``nocomments``
   If set, the web application won't display a comment form for a page generated
   from this source file.

``orphan``
   If set, warnings about this file not being included in any toctree will be
   suppressed.

   .. versionadded:: 1.0


Meta-information markup
-----------------------

.. rst:directive:: .. sectionauthor:: name <email>

   Identifies the author of the current section.  The argument should include
   the author's name such that it can be used for presentation and email
   address.  The domain name portion of the address should be lower case.
   Example::

      .. sectionauthor:: Guido van Rossum <guido@python.org>

   By default, this markup isn't reflected in the output in any way (it helps
   keep track of contributions), but you can set the configuration value
   :confval:`show_authors` to True to make them produce a paragraph in the
   output.


.. rst:directive:: .. codeauthor:: name <email>

   The :rst:dir:`codeauthor` directive, which can appear multiple times, names the
   authors of the described code, just like :rst:dir:`sectionauthor` names the
   author(s) of a piece of documentation.  It too only produces output if the
   :confval:`show_authors` configuration value is True.


.. _tags:

Including content based on tags
-------------------------------

.. rst:directive:: .. only:: <expression>

   Include the content of the directive only if the *expression* is true.  The
   expression should consist of tags, like this::

      .. only:: html and draft

   Undefined tags are false, defined tags (via the ``-t`` command-line option or
   within :file:`conf.py`) are true.  Boolean expressions, also using
   parentheses (like ``html and (latex or draft)``) are supported.

   The format of the current builder (``html``, ``latex`` or ``text``) is always
   set as a tag.

   .. versionadded:: 0.6


Tables
------

Use :ref:`standard reStructuredText tables <rst-tables>`.  They work fine in
HTML output, however there are some gotchas when using tables in LaTeX: the
column width is hard to determine correctly automatically.  For this reason, the
following directive exists:

.. rst:directive:: .. tabularcolumns:: column spec

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

   Tables that contain list-like elements such as object descriptions,
   blockquotes or any kind of lists cannot be set out of the box with
   ``tabulary``.  They are therefore set with the standard LaTeX ``tabular``
   environment if you don't give a ``tabularcolumns`` directive.  If you do, the
   table will be set with ``tabulary``, but you must use the ``p{width}``
   construct for the columns that contain these elements.

   Literal blocks do not work with ``tabulary`` at all, so tables containing a
   literal block are always set with ``tabular``.  Also, the verbatim
   environment used for literal blocks only works in ``p{width}`` columns, which
   means that by default, Sphinx generates such column specs for such tables.
   Use the :rst:dir:`tabularcolumns` directive to get finer control over such
   tables.
