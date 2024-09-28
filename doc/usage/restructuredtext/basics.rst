.. highlight:: rst

.. _rst-primer:

=======================
reStructuredText Primer
=======================

reStructuredText is the default plaintext markup language used by Sphinx.  This
section is a brief introduction to reStructuredText (reST) concepts and syntax,
intended to provide authors with enough information to author documents
productively.  Since reStructuredText was designed to be a simple, unobtrusive markup
language, this will not take too long.

.. seealso::

   The authoritative `reStructuredText User Documentation
   <https://docutils.sourceforge.io/rst.html>`_.
   The "ref" links in this document link to the description of
   the individual constructs in the reStructuredText reference.


Paragraphs
----------

The paragraph (:duref:`ref <paragraphs>`) is the most basic block
in a reStructuredText document.
Paragraphs are simply chunks of text separated by one or more blank lines.
As in Python, indentation is significant in reStructuredText,
so all lines of the same paragraph must be left-aligned
to the same level of indentation.


.. _rst-inline-markup:

Inline markup
-------------

The standard reStructuredText inline markup is quite simple: use

* one asterisk: ``*text*`` for emphasis (italics),
* two asterisks: ``**text**`` for strong emphasis (boldface), and
* backquotes: ````text```` for code samples.

If asterisks or backquotes appear in running text and could be confused with
inline markup delimiters, they have to be escaped with a backslash.

Be aware of some restrictions of this markup:

* it may not be nested,
* content may not start or end with whitespace: ``* text*`` is wrong,
* it must be separated from surrounding text by non-word characters.  Use a
  backslash escaped space to work around that: ``thisis\ *one*\ word``.

These restrictions may be lifted in future versions of the docutils.

It is also possible to replace or expand upon some of this inline markup with
roles. Refer to :ref:`rst-roles` for more information.


Lists and Quote-like blocks
---------------------------

List markup (:duref:`ref <bullet-lists>`) is natural: just place an asterisk at
the start of a paragraph and indent properly.  The same goes for numbered
lists; they can also be autonumbered using a ``#`` sign::

   * This is a bulleted list.
   * It has two items, the second
     item uses two lines.

   1. This is a numbered list.
   2. It has two items too.

   #. This is a numbered list.
   #. It has two items too.

Nested lists are possible, but be aware that they must be separated from the
parent list items by blank lines::

   * this is
   * a list

     * with a nested list
     * and some subitems

   * and here the parent list continues

Definition lists (:duref:`ref <definition-lists>`) are created as follows::

   term (up to a line of text)
      Definition of the term, which must be indented

      and can even consist of multiple paragraphs

   next term
      Description.

Note that the term cannot have more than one line of text.

Quoted paragraphs (:duref:`ref <block-quotes>`) are created by just indenting
them more than the surrounding paragraphs.

Line blocks (:duref:`ref <line-blocks>`) are a way of preserving line breaks::

   | These lines are
   | broken exactly like in
   | the source file.

There are also several more special blocks available:

* field lists (:duref:`ref <field-lists>`, with caveats noted in
  :ref:`rst-field-lists`)
* option lists (:duref:`ref <option-lists>`)
* quoted literal blocks (:duref:`ref <quoted-literal-blocks>`)
* doctest blocks (:duref:`ref <doctest-blocks>`)


.. _rst-literal-blocks:

Literal blocks
--------------

Literal code blocks (:duref:`ref <literal-blocks>`) are introduced by ending a
paragraph with the special marker ``::``.  The literal block must be indented
(and, like all paragraphs, separated from the surrounding ones by blank
lines)::

   This is a normal text paragraph. The next paragraph is a code sample::

      It is not processed in any way, except
      that the indentation is removed.

      It can span multiple lines.

   This is a normal text paragraph again.

The handling of the ``::`` marker is smart:

* If it occurs as a paragraph of its own, that paragraph is completely left out
  of the document.
* If it is preceded by whitespace, the marker is removed.
* If it is preceded by non-whitespace, the marker is replaced by a single
  colon.

That way, the second sentence in the above example's first paragraph would be
rendered as "The next paragraph is a code sample:".

Code highlighting can be enabled for these literal blocks on a document-wide
basis using the :rst:dir:`highlight` directive and on a project-wide basis
using the :confval:`highlight_language` configuration option. The
:rst:dir:`code-block` directive can be used to set highlighting on a
block-by-block basis. These directives are discussed later.


.. _rst-doctest-blocks:

Doctest blocks
--------------

Doctest blocks (:duref:`ref <doctest-blocks>`) are interactive Python sessions
cut-and-pasted into docstrings. They do not require the
:ref:`literal blocks <rst-literal-blocks>` syntax. The doctest block must end
with a blank line and should *not* end with an unused prompt::

    >>> 1 + 1
    2

.. _rst-tables:

Tables
------

For *grid tables* (:duref:`ref <grid-tables>`), you have to "paint" the cell
grid yourself.  They look like this::

   +------------------------+------------+----------+----------+
   | Header row, column 1   | Header 2   | Header 3 | Header 4 |
   | (header rows optional) |            |          |          |
   +========================+============+==========+==========+
   | body row 1, column 1   | column 2   | column 3 | column 4 |
   +------------------------+------------+----------+----------+
   | body row 2             | ...        | ...      |          |
   +------------------------+------------+----------+----------+

*Simple tables* (:duref:`ref <simple-tables>`) are easier to write, but
limited: they must contain more than one row, and the first column cells cannot
contain multiple lines.  They look like this::

   =====  =====  =======
   A      B      A and B
   =====  =====  =======
   False  False  False
   True   False  False
   False  True   False
   True   True   True
   =====  =====  =======

Two more syntaxes are supported: *CSV tables* and *List tables*. They use an
*explicit markup block*. Refer to :ref:`table-directives` for more information.


Hyperlinks
----------

External links
~~~~~~~~~~~~~~

Use ```Link text <https://domain.invalid/>`_`` for inline web links.  If the
link text should be the web address, you don't need special markup at all, the
parser finds links and mail addresses in ordinary text.

.. important:: There must be a space between the link text and the opening \< for the URL.

You can also separate the link and the target definition (:duref:`ref
<hyperlink-targets>`), like this::

   This is a paragraph that contains `a link`_.

   .. _a link: https://domain.invalid/

Internal links
~~~~~~~~~~~~~~

Internal linking is done via a special reStructuredText role provided by Sphinx,
see the section on specific markup, :ref:`ref-role`.


.. _rst-sections:

Sections
--------

Section headers (:duref:`ref <sections>`) are created by underlining (and
optionally overlining) the section title with a punctuation character, at least
as long as the text::

   =================
   This is a heading
   =================

Normally, there are no heading levels assigned to certain characters as the
structure is determined from the succession of headings.  However, this
convention is used in `Python Developer's Guide for documenting
<https://devguide.python.org/documentation/markup/#sections>`_ which you may
follow:

* ``#`` with overline, for parts
* ``*`` with overline, for chapters
* ``=`` for sections
* ``-`` for subsections
* ``^`` for subsubsections
* ``"`` for paragraphs

Of course, you are free to use your own marker characters (see the reStructuredText
documentation), and use a deeper nesting level, but keep in mind that most
target formats (HTML, LaTeX) have a limited supported nesting depth.


.. _rst-field-lists:

Field Lists
-----------

Field lists (:duref:`ref <field-lists>`) are sequences of fields marked up like
this::

   :fieldname: Field content

They are commonly used in Python documentation::

    def my_function(my_arg, my_other_arg):
        """A function just for me.

        :param my_arg: The first of my arguments.
        :param my_other_arg: The second of my arguments.

        :returns: A message (just for me, of course).
        """

Sphinx extends standard docutils behavior and intercepts field lists specified
at the beginning of documents.  Refer to :doc:`field-lists` for more
information.


.. _rst-roles:

Roles
-----

A role or "custom interpreted text role" (:dupage:`ref <roles>`) is an inline
piece of explicit markup. It signifies that the enclosed text should be
interpreted in a specific way.  Sphinx uses this to provide semantic markup and
cross-referencing of identifiers, as described in the appropriate section.  The
general syntax is ``:rolename:`content```.

Docutils supports the following roles:

* :durole:`emphasis` -- equivalent of ``*emphasis*``
* :durole:`strong` -- equivalent of ``**strong**``
* :durole:`literal` -- equivalent of ````literal````
* :durole:`subscript` -- subscript text
* :durole:`superscript` -- superscript text
* :durole:`title-reference` -- for titles of books, periodicals, and other
  materials

Refer to :doc:`roles` for roles added by Sphinx.


Explicit Markup
---------------

"Explicit markup" (:duref:`ref <explicit-markup-blocks>`) is used in
reStructuredText for most constructs that need special handling, such as footnotes,
specially-highlighted paragraphs, comments, and generic directives.

An explicit markup block begins with a line starting with ``..`` followed by
whitespace and is terminated by the next paragraph at the same level of
indentation.  (There needs to be a blank line between explicit markup and
normal paragraphs.  This may all sound a bit complicated, but it is intuitive
enough when you write it.)


.. _rst-directives:

Directives
----------

A directive (:duref:`ref <directives>`) is a generic block of explicit markup.
Along with roles, it is one of the extension mechanisms of reStructuredText,
and Sphinx makes heavy use of it.

Docutils supports the following directives:

* Admonitions: :dudir:`attention`, :dudir:`caution`, :dudir:`danger`,
  :dudir:`error`, :dudir:`hint`, :dudir:`important`, :dudir:`note`,
  :dudir:`tip`, :dudir:`warning` and the generic
  :dudir:`admonition <admonitions>`.  (Most themes style only "note" and
  "warning" specially.)

* Images:

  - :dudir:`image` (see also Images_ below)
  - :dudir:`figure` (an image with caption and optional legend)

* Additional body elements:

  - :dudir:`contents <table-of-contents>` (a local, i.e. for the current file
    only, table of contents)
  - :dudir:`container` (a container with a custom class, useful to generate an
    outer ``<div>`` in HTML)
  - :dudir:`rubric` (a heading without relation to the document sectioning)
  - :dudir:`topic`, :dudir:`sidebar` (special highlighted body elements)
  - :dudir:`parsed-literal` (literal block that supports inline markup)
  - :dudir:`epigraph` (a block quote with optional attribution line)
  - :dudir:`highlights`, :dudir:`pull-quote` (block quotes with their own
    class attribute)
  - :dudir:`compound <compound-paragraph>` (a compound paragraph)

* Special tables:

  - :dudir:`table` (a table with title)
  - :dudir:`csv-table` (a table generated from comma-separated values)
  - :dudir:`list-table` (a table generated from a list of lists)

* Special directives:

  - :dudir:`raw <raw-data-pass-through>` (include raw target-format markup)
  - :dudir:`include` (include reStructuredText from another file) -- in Sphinx,
    when given an absolute include file path, this directive takes it as
    relative to the source directory

    .. _rstclass:

  - :dudir:`class` (assign a class attribute to the next element)

    .. note::

       When the default domain contains a ``class`` directive, this directive
       will be shadowed.  Therefore, Sphinx re-exports it as ``rst-class``.

    .. tip::

       If you want to add a class to a directive,
       you may consider the ``:class:`` :dudir:`option <common-options>` instead,
       which is supported by most directives and allows for a more compact notation.

* HTML specifics:

  - :dudir:`meta`
    (generation of HTML ``<meta>`` tags, see also :ref:`html-meta` below)
  - :dudir:`title <metadata-document-title>` (override document title)

* Influencing markup:

  - :dudir:`default-role` (set a new default role)
  - :dudir:`role` (create a new role)

  Since these are only per-file, better use Sphinx's facilities for setting the
  :confval:`default_role`.

.. warning::

   Do *not* use the directives :dudir:`sectnum`, :dudir:`header` and
   :dudir:`footer`.

Directives added by Sphinx are described in :doc:`directives`.

Basically, a directive consists of a name, arguments, options and content.
(Keep this terminology in mind, it is used in the next chapter describing
custom directives.)  Looking at this example, ::

   .. function:: foo(x)
                 foo(y, z)
      :module: some.module.name

      Return a line of text input from the user.

``function`` is the directive name.  It is given two arguments here, the
remainder of the first line and the second line, as well as one option
``module`` (as you can see, options are given in the lines immediately
following the arguments and indicated by the colons).  Options must be indented
to the same level as the directive content.

The directive content follows after a blank line and is indented relative to
the directive start or if options are present, by the same amount as the
options.

Be careful as the indent is not a fixed number of whitespace, e.g. three, but
any number whitespace.  This can be surprising when a fixed indent is used
throughout the document and can make a difference for directives which are
sensitive to whitespace. Compare::

   .. code-block::
      :caption: A cool example

          The output of this line starts with four spaces.

   .. code-block::

          The output of this line has no spaces at the beginning.

In the first code block, the indent for the content was fixated by the option
line to three spaces, consequently the content starts with four spaces.
In the latter the indent was fixed by the content itself to seven spaces, thus
it does not start with a space.


Images
------

reStructuredText supports an image directive (:dudir:`ref <image>`), used like so::

   .. image:: gnu.png
      (options)

When used within Sphinx, the file name given (here ``gnu.png``) must either be
relative to the source file, or absolute which means that they are relative to
the top source directory.  For example, the file ``sketch/spam.rst`` could
refer to the image ``images/spam.png`` as ``../images/spam.png`` or
``/images/spam.png``.

Sphinx will automatically copy image files over to a subdirectory of the output
directory on building (e.g. the ``_static`` directory for HTML output.)

Interpretation of image size options (``width`` and ``height``) is as follows:
if the size has no unit or the unit is pixels, the given size will only be
respected for output channels that support pixels. Other units (like ``pt`` for
points) will be used for HTML and LaTeX output (the latter replaces ``pt`` by
``bp`` as this is the TeX unit such that ``72bp=1in``).

Sphinx extends the standard docutils behavior by allowing an asterisk for the
extension::

   .. image:: gnu.*

Sphinx then searches for all images matching the provided pattern and
determines their type.  Each builder then chooses the best image out of these
candidates.  For instance, if the file name ``gnu.*`` was given and two files
:file:`gnu.pdf` and :file:`gnu.png` existed in the source tree, the LaTeX
builder would choose the former, while the HTML builder would prefer the
latter.  Supported image types and choosing priority are defined at
:doc:`/usage/builders/index`.

Note that image file names should not contain spaces.

.. versionchanged:: 0.4
   Added the support for file names ending in an asterisk.

.. versionchanged:: 0.6
   Image paths can now be absolute.

.. versionchanged:: 1.5
   latex target supports pixels (default is ``96px=1in``).


Footnotes
---------

For footnotes (:duref:`ref <footnotes>`), use ``[#name]_`` to mark the footnote
location, and add the footnote body at the bottom of the document after a
"Footnotes" rubric heading, like so::

   Lorem ipsum [#f1]_ dolor sit amet ... [#f2]_

   .. rubric:: Footnotes

   .. [#f1] Text of the first footnote.
   .. [#f2] Text of the second footnote.

You can also explicitly number the footnotes (``[1]_``) or use auto-numbered
footnotes without names (``[#]_``).


Citations
---------

Standard reStructuredText citations (:duref:`ref <citations>`) are supported,
with the additional feature that they are "global",
i.e. all citations can be referenced from all files.  Use them like so::

   Lorem ipsum [Ref]_ dolor sit amet.

   .. [Ref] Book or article reference, URL or whatever.

Citation usage is similar to footnote usage, but with a label that is not
numeric or begins with ``#``.


Substitutions
-------------

reStructuredText supports "substitutions" (:duref:`ref <substitution-definitions>`),
which are pieces of text and/or markup referred to in the text by ``|name|``.
They are defined like footnotes with explicit markup blocks, like this::

   .. |name| replace:: replacement *text*

or this::

   .. |caution| image:: warning.png
                :alt: Warning!

See the :duref:`reStructuredText reference for substitutions
<substitution-definitions>` for details.

.. index:: ! pair: global; substitutions

If you want to use some substitutions for all documents, put them into
:confval:`rst_prolog` or :confval:`rst_epilog` or put them into a separate file
and include it into all documents you want to use them in, using the
:dudir:`include` directive.  (Be sure to give the include file a file name
extension differing from that of other source files, to avoid Sphinx finding it
as a standalone document.)

Sphinx defines some default substitutions, see :ref:`default-substitutions`.


Comments
--------

Every explicit markup block which isn't a valid markup construct (like the
footnotes above) is regarded as a comment (:duref:`ref <comments>`).  For
example::

   .. This is a comment.

You can indent text after a comment start to form multiline comments::

   ..
      This whole indented block
      is a comment.

      Still in the comment.


.. _html-meta:

HTML Metadata
-------------

The :dudir:`meta` directive allows specifying the HTML
`metadata element`_ of a Sphinx documentation page.  For example, the
directive::

   .. meta::
      :description: The Sphinx documentation builder
      :keywords: Sphinx, documentation, builder

will generate the following HTML output:

.. code-block:: html

   <meta name="description" content="The Sphinx documentation builder">
   <meta name="keywords" content="Sphinx, documentation, builder">

Also, Sphinx will add the keywords as specified in the meta directive to the
search index.  Thereby, the ``lang`` attribute of the meta element is
considered.  For example, the directive::

   .. meta::
      :keywords: backup
      :keywords lang=en: pleasefindthiskey pleasefindthiskeytoo
      :keywords lang=de: bittediesenkeyfinden

adds the following words to the search indices of builds with different language
configurations:

* ``pleasefindthiskey``, ``pleasefindthiskeytoo`` to *English* builds;
* ``bittediesenkeyfinden`` to *German* builds;
* ``backup`` to builds in all languages.

.. _metadata element: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta


Source encoding
---------------

Since the easiest way to include special characters like em dashes or copyright
signs in reStructuredText is to directly write them as Unicode characters, one has to
specify an encoding.  Sphinx assumes source files to be encoded in UTF-8 by
default; you can change this with the :confval:`source_encoding` config value.


Gotchas
-------

There are some problems one commonly runs into
while authoring reStructuredText documents:

* **Separation of inline markup:** As said above, inline markup spans must be
  separated from the surrounding text by non-word characters, you have to use a
  backslash-escaped space to get around that.  See :duref:`the reference
  <substitution-definitions>` for the details.

* **No nested inline markup:** Something like ``*see :func:`foo`*`` is not
  possible.
