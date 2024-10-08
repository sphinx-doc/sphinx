.. highlight:: rst

=====
Roles
=====

Sphinx uses interpreted text roles to insert semantic markup into documents.
They are written as ``:rolename:`content```.

.. note::

   The default role (```content```) has no special meaning by default.  You are
   free to use it for anything you like, e.g. variable names; use the
   :confval:`default_role` config value to set it to a known role -- the
   :rst:role:`any` role to find anything or the :rst:role:`py:obj` role to find
   Python objects are very useful for this.

See :doc:`/usage/domains/index` for roles added by domains.


Cross-references
----------------

See :doc:`/usage/referencing/`.

Cross-reference roles include:

* :rst:role:`any`
* :rst:role:`doc`
* :rst:role:`download`
* :rst:role:`envvar`
* :rst:role:`keyword`
* :rst:role:`numref`
* :rst:role:`option` (and the deprecated :rst:role:`!cmdoption`)
* :rst:role:`ref`
* :rst:role:`term`
* :rst:role:`token`


Inline code highlighting
------------------------

.. rst:role:: code

   An *inline* code example.  When used directly, this role just displays the
   text *without* syntax highlighting, as a literal.

   .. code-block:: rst

      By default, inline code such as :code:`1 + 2` just displays without
      highlighting.

   Displays: By default, inline code such as :code:`1 + 2` just displays without
   highlighting.

   Unlike the :rst:dir:`code-block` directive, this role does not respect the
   default language set by the :rst:dir:`highlight` directive.

   To enable syntax highlighting, you must first use the Docutils :dudir:`role`
   directive to define a custom role associated with a specific language:

   .. code-block:: rst

      .. role:: python(code)
         :language: python

      In Python, :python:`1 + 2` is equal to :python:`3`.

   To display a multi-line code example, use the :rst:dir:`code-block` directive
   instead.

Math
----

.. rst:role:: math

   Role for inline math.  Use like this::

      Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

   Displays: Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

.. rst:role:: eq

   Same as :rst:role:`math:numref`.


Other semantic markup
---------------------

The following roles don't do anything special except formatting the text in a
different style:

.. rst:role:: abbr

   An abbreviation.  If the role content contains a parenthesized explanation,
   it will be treated specially: it will be shown in a tool-tip in HTML, and
   output only once in LaTeX.

   For example: ``:abbr:`LIFO (last-in, first-out)``` displays
   :abbr:`LIFO (last-in, first-out)`.

   .. versionadded:: 0.6

.. rst:role:: command

   The name of an OS-level command, such as ``rm``.

   For example: :command:`rm`

.. rst:role:: dfn

   Mark the defining instance of a term in the text.  (No index entries are
   generated.)

   For example: :dfn:`binary mode`

.. rst:role:: file

   The name of a file or directory.  Within the contents, you can use curly
   braces to indicate a "variable" part, for example::

      ... is installed in :file:`/usr/lib/python3.{x}/site-packages` ...

   Displays: ... is installed in :file:`/usr/lib/python3.{x}/site-packages` ...

   In the built documentation, the ``x`` will be displayed differently to
   indicate that it is to be replaced by the Python minor version.

.. rst:role:: guilabel

   Labels presented as part of an interactive user interface should be marked
   using ``guilabel``.  This includes labels from text-based interfaces such as
   those created using :mod:`curses` or other text-based libraries.  Any label
   used in the interface should be marked with this role, including button
   labels, window titles, field names, menu and menu selection names, and even
   values in selection lists.

   .. versionchanged:: 1.0
      An accelerator key for the GUI label can be included using an ampersand;
      this will be stripped and displayed underlined in the output (for example:
      ``:guilabel:`&Cancel``` displays :guilabel:`&Cancel`).  To include a literal
      ampersand, double it.

.. rst:role:: kbd

   Mark a sequence of keystrokes.  What form the key sequence takes may depend
   on platform- or application-specific conventions.  When there are no
   relevant conventions, the names of modifier keys should be spelled out, to
   improve accessibility for new users and non-native speakers.  For example,
   an *xemacs* key sequence may be marked like ``:kbd:`C-x C-f```, but without
   reference to a specific application or platform, the same sequence should be
   marked as ``:kbd:`Control-x Control-f```, displaying :kbd:`C-x C-f` and
   :kbd:`Control-x Control-f` respectively.

.. rst:role:: mailheader

   The name of an RFC 822-style mail header.  This markup does not imply that
   the header is being used in an email message, but can be used to refer to
   any header of the same "style."  This is also used for headers defined by
   the various MIME specifications.  The header name should be entered in the
   same way it would normally be found in practice, with the camel-casing
   conventions being preferred where there is more than one common usage. For
   example: ``:mailheader:`Content-Type``` displays :mailheader:`Content-Type`.

.. rst:role:: makevar

   The name of a :command:`make` variable.

   For example: :makevar:`help`

.. rst:role:: manpage

   A reference to a Unix manual page including the section, e.g.
   ``:manpage:`ls(1)``` displays :manpage:`ls(1)`. Creates a hyperlink to an
   external site rendering the manpage if :confval:`manpages_url` is defined.

   .. versionchanged:: 7.3
      Allow specifying a target with ``<>``, like hyperlinks.
      For example, ``:manpage:`blah <ls(1)>``` displays :manpage:`blah <ls(1)>`.

.. rst:role:: menuselection

   Menu selections should be marked using the ``menuselection`` role.  This is
   used to mark a complete sequence of menu selections, including selecting
   submenus and choosing a specific operation, or any subsequence of such a
   sequence.  The names of individual selections should be separated by
   ``-->``.

   For example, to mark the selection "Start > Programs", use this markup::

      :menuselection:`Start --> Programs`

   Displays: :menuselection:`Start --> Programs`

   When including a selection that includes some trailing indicator, such as
   the ellipsis some operating systems use to indicate that the command opens a
   dialog, the indicator should be omitted from the selection name.

   ``menuselection`` also supports ampersand accelerators just like
   :rst:role:`guilabel`.

.. rst:role:: mimetype

   The name of a MIME type, or a component of a MIME type (the major or minor
   portion, taken alone).

   For example: :mimetype:`text/plain`

.. rst:role:: newsgroup

   The name of a Usenet newsgroup.

   For example: :newsgroup:`comp.lang.python`

.. todo:: Is this not part of the standard domain?

.. rst:role:: program

   The name of an executable program.  This may differ from the file name for
   the executable for some platforms.  In particular, the ``.exe`` (or other)
   extension should be omitted for Windows programs.

   For example: :program:`curl`

.. rst:role:: regexp

   A regular expression. Quotes should not be included.

   For example: :regexp:`([abc])+`

.. rst:role:: samp

   A piece of literal text, such as code.  Within the contents, you can use
   curly braces to indicate a "variable" part, as in :rst:role:`file`.  For
   example, in ``:samp:`print(1+{variable})```, the part ``variable`` would be
   emphasized: :samp:`print(1+{variable})`

   If you don't need the "variable part" indication, use the standard
   :rst:role:`code` role instead.

   .. versionchanged:: 1.8
      Allowed to escape curly braces with double backslash.  For example, in
      ``:samp:`print(f"answer=\\{1+{variable}*2\\}")```, the part ``variable``
      would be emphasized and the escaped curly braces would be displayed:
      :samp:`print(f"answer=\\{1+{variable}*2\\}")`

There is also an :rst:role:`index` role to generate index entries.

The following roles generate external links:

.. rst:role:: cve

   A reference to a `Common Vulnerabilities and Exposures`_ record.
   This generates appropriate index entries.
   The text "CVE *number*\ " is generated;
   with a link to an online copy of the specified CVE.
   You can link to a specific section by using ``:cve:`number#anchor```.

   .. _Common Vulnerabilities and Exposures: https://www.cve.org/

   For example: :cve:`2020-10735`

   .. versionadded:: 8.1

.. rst:role:: cwe

   A reference to a `Common Weakness Enumeration`_.
   This generates appropriate index entries.
   The text "CWE *number*\ " is generated; in the HTML output,
   with a link to an online copy of the specified CWE.
   You can link to a specific section by using ``:cwe:`number#anchor```.

   .. _Common Weakness Enumeration: https://cwe.mitre.org/

   For example: :cwe:`787`

   .. versionadded:: 8.1

.. rst:role:: pep

   A reference to a Python Enhancement Proposal.  This generates appropriate
   index entries. The text "PEP *number*\ " is generated; in the HTML output,
   this text is a hyperlink to an online copy of the specified PEP.  You can
   link to a specific section by saying ``:pep:`number#anchor```.

   For example: :pep:`8`

.. rst:role:: rfc

   A reference to an Internet Request for Comments.  This generates appropriate
   index entries. The text "RFC *number*\ " is generated; in the HTML output,
   this text is a hyperlink to an online copy of the specified RFC.  You can
   link to a specific section by saying ``:rfc:`number#anchor```.

   For example: :rfc:`2324`

Note that there are no special roles for including hyperlinks as you can use
the standard reStructuredText markup for that purpose.


.. _default-substitutions:

Substitutions
-------------

The documentation system provides some substitutions that are defined by
default. They are set in the build configuration file.

.. describe:: |release|

   Replaced by the project release the documentation refers to.  This is meant
   to be the full version string including alpha/beta/release candidate tags,
   e.g. ``2.5.2b3``.  Set by :confval:`release`.

.. describe:: |version|

   Replaced by the project version the documentation refers to. This is meant to
   consist only of the major and minor version parts, e.g. ``2.5``, even for
   version 2.5.1.  Set by :confval:`version`.

.. describe:: |today|

   Replaced by either today's date (the date on which the document is read), or
   the date set in the build configuration file.  Normally has the format
   ``April 14, 2007``.  Set by :confval:`today_fmt` and :confval:`today`.

.. describe:: |translation progress|

   Replaced by the translation progress of the document.
   This substitution is intended for use by document translators
   as a marker for the translation progress of the document.
