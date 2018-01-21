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
   :confval:`show_authors` to ``True`` to make them produce a paragraph in the
   output.


.. rst:directive:: .. codeauthor:: name <email>

   The :rst:dir:`codeauthor` directive, which can appear multiple times, names
   the authors of the described code, just like :rst:dir:`sectionauthor` names
   the author(s) of a piece of documentation.  It too only produces output if
   the :confval:`show_authors` configuration value is ``True``.


Index-generating markup
-----------------------

Sphinx automatically creates index entries from all object descriptions (like
functions, classes or attributes) like discussed in :ref:`domains`.

However, there is also explicit markup available, to make the index more
comprehensive and enable index entries in documents where information is not
mainly contained in information units, such as the language reference.

.. rst:directive:: .. index:: <entries>

   This directive contains one or more index entries.  Each entry consists of a
   type and a value, separated by a colon.

   For example::

      .. index::
         single: execution; context
         module: __main__
         module: sys
         triple: module; search; path

      The execution context
      ---------------------

      ...

   This directive contains five entries, which will be converted to entries in
   the generated index which link to the exact location of the index statement
   (or, in case of offline media, the corresponding page number).

   Since index directives generate cross-reference targets at their location in
   the source, it makes sense to put them *before* the thing they refer to --
   e.g. a heading, as in the example above.

   The possible entry types are:

   single
      Creates a single index entry.  Can be made a subentry by separating the
      subentry text with a semicolon (this notation is also used below to
      describe what entries are created).
   pair
      ``pair: loop; statement`` is a shortcut that creates two index entries,
      namely ``loop; statement`` and ``statement; loop``.
   triple
      Likewise, ``triple: module; search; path`` is a shortcut that creates
      three index entries, which are ``module; search path``, ``search; path,
      module`` and ``path; module search``.
   see
      ``see: entry; other`` creates an index entry that refers from ``entry`` to
      ``other``.
   seealso
      Like ``see``, but inserts "see also" instead of "see".
   module, keyword, operator, object, exception, statement, builtin
      These all create two index entries.  For example, ``module: hashlib``
      creates the entries ``module; hashlib`` and ``hashlib; module``.  (These
      are Python-specific and therefore deprecated.)

   You can mark up "main" index entries by prefixing them with an exclamation
   mark.  The references to "main" entries are emphasized in the generated
   index.  For example, if two pages contain ::

      .. index:: Python

   and one page contains ::

      .. index:: ! Python

   then the backlink to the latter page is emphasized among the three backlinks.

   For index directives containing only "single" entries, there is a shorthand
   notation::

      .. index:: BNF, grammar, syntax, notation

   This creates four index entries.

   .. versionchanged:: 1.1
      Added ``see`` and ``seealso`` types, as well as marking main entries.

.. rst:role:: index

   While the :rst:dir:`index` directive is a block-level markup and links to the
   beginning of the next paragraph, there is also a corresponding role that sets
   the link target directly where it is used.

   The content of the role can be a simple phrase, which is then kept in the
   text and used as an index entry.  It can also be a combination of text and
   index entry, styled like with explicit targets of cross-references.  In that
   case, the "target" part can be a full entry as described for the directive
   above.  For example::

      This is a normal reST :index:`paragraph` that contains several
      :index:`index entries <pair: index; entry>`.

   .. versionadded:: 1.1


.. _tags:

Including content based on tags
-------------------------------

.. rst:directive:: .. only:: <expression>

   Include the content of the directive only if the *expression* is true.  The
   expression should consist of tags, like this::

      .. only:: html and draft

   Undefined tags are false, defined tags (via the ``-t`` command-line option or
   within :file:`conf.py`, see :ref:`here <conf-tags>`) are true.  Boolean
   expressions, also using parentheses (like ``html and (latex or draft)``) are
   supported.

   The *format* and the *name* of the current builder (``html``, ``latex`` or
   ``text``) are always set as a tag [#]_.  To make the distinction between
   format and name explicit, they are also added with the prefix ``format_`` and
   ``builder_``, e.g. the epub builder defines the tags  ``html``, ``epub``,
   ``format_html`` and ``builder_epub``.

   These standard tags are set *after* the configuration file is read, so they
   are not available there.

   All tags must follow the standard Python identifier syntax as set out in
   the `Identifiers and keywords
   <https://docs.python.org/2/reference/lexical_analysis.html#identifiers>`_
   documentation.  That is, a tag expression may only consist of tags that
   conform to the syntax of Python variables.  In ASCII, this consists of the
   uppercase and lowercase letters ``A`` through ``Z``, the underscore ``_``
   and, except for the first character, the digits ``0`` through ``9``.

   .. versionadded:: 0.6
   .. versionchanged:: 1.2
      Added the name of the builder and the prefixes.

   .. warning::

      This directive is designed to control only content of document.  It could
      not control sections, labels and so on.


Tables
------

Use :ref:`reStructuredText tables <rst-tables>`, i.e. either

- grid table syntax (:duref:`ref <grid-tables>`),
- simple table syntax (:duref:`ref <simple-tables>`),
- :dudir:`csv-table` syntax,
- or :dudir:`list-table` syntax.

The :dudir:`table` directive serves as optional wrapper of the *grid* and
*simple* syntaxes.

They work fine in
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
   |``L``| flush left column with automatic width   |
   +-----+------------------------------------------+
   |``R``| flush right column with automatic width  |
   +-----+------------------------------------------+
   |``C``| centered column with automatic width     |
   +-----+------------------------------------------+
   |``J``| justified column with automatic width    |
   +-----+------------------------------------------+

   The automatic widths of the ``LRCJ`` columns are attributed by ``tabulary``
   in proportion to the observed shares in a first pass where the table cells
   are rendered at their natural "horizontal" widths.

   By default, Sphinx uses a table layout with ``J`` for every column.

   .. versionadded:: 0.3

   .. versionchanged:: 1.6
      Merged cells may now contain multiple paragraphs and are much better
      handled, thanks to custom Sphinx LaTeX macros. This novel situation
      motivated the switch to ``J`` specifier and not ``L`` by default.

   .. hint::

      Sphinx actually uses ``T`` specifier having done ``\newcolumntype{T}{J}``.
      To revert to previous default, insert ``\newcolumntype{T}{L}`` in the
      LaTeX preamble (see :confval:`latex_elements`).

      A frequent issue with tabulary is that columns with little contents are
      "squeezed". The minimal column width is a tabulary parameter called
      ``\tymin``. You may set it globally in the LaTeX preamble via
      ``\setlength{\tymin}{40pt}`` for example.

      Else, use the :rst:dir:`tabularcolumns` directive with an explicit
      ``p{40pt}`` (for example) for that column. You may use also ``l``
      specifier but this makes the task of setting column widths more difficult
      if some merged cell intersects that column.

   .. warning::

      Tables with more than 30 rows are rendered using ``longtable``, not
      ``tabulary``, in order to allow pagebreaks. The ``L``, ``R``, ... specifiers
      do not work for these tables.

      Tables that contain list-like elements such as object descriptions,
      blockquotes or any kind of lists cannot be set out of the box with
      ``tabulary``. They are therefore set with the standard LaTeX ``tabular`` (or
      ``longtable``) environment if you don't give a ``tabularcolumns`` directive.
      If you do, the table will be set with ``tabulary`` but you must use the
      ``p{width}`` construct (or Sphinx's ``\X`` and ``\Y`` specifiers described
      below) for the columns containing these elements.

      Literal blocks do not work with ``tabulary`` at all, so tables containing
      a literal block are always set with ``tabular``. The verbatim environment
      used for literal blocks only works in ``p{width}`` (and ``\X`` or ``\Y``)
      columns, hence Sphinx generates such column specs for tables containing
      literal blocks.

   Since Sphinx 1.5, the ``\X{a}{b}`` specifier is used (there *is* a backslash
   in the specifier letter). It is like ``p{width}`` with the width set to a
   fraction ``a/b`` of the current line width. You can use it in the
   :rst:dir:`tabularcolumns` (it is not a problem if some LaTeX macro is also
   called ``\X``.)

   It is *not* needed for ``b`` to be the total number of columns, nor for the
   sum of the fractions of the ``\X`` specifiers to add  up to one. For example
   ``|\X{2}{5}|\X{1}{5}|\X{1}{5}|`` is legitimate and the table will occupy
   80% of the line width, the first of its three columns having the same width
   as the sum  of the next two.

   This is used by the ``:widths:`` option of the :dudir:`table` directive.

   Since Sphinx 1.6, there is also the ``\Y{f}`` specifier which admits a
   decimal argument, such has ``\Y{0.15}``: this would have the same effect as
   ``\X{3}{20}``.

   .. versionchanged:: 1.6

      Merged cells from complex grid tables (either multi-row, multi-column, or
      both) now allow blockquotes, lists, literal blocks, ... as do regular cells.

      Sphinx's merged cells interact well with ``p{width}``, ``\X{a}{b}``, ``Y{f}``
      and tabulary's columns.

   .. note::

      :rst:dir:`tabularcolumns` conflicts with ``:widths:`` option of table
      directives.  If both are specified, ``:widths:`` option will be ignored.

Math
----

See :ref:`math-support`.

.. rubric:: Footnotes

.. [#] For most builders name and format are the same. At the moment only
       builders derived from the html builder distinguish between the builder
       format and the builder name.

       Note that the current builder tag is not available in ``conf.py``, it is
       only available after the builder is initialized.

