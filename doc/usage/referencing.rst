.. _xref:

================
Cross-references
================

One of Sphinx's most useful features is creating automatic cross-references
through semantic cross-referencing roles.
A cross reference to an object description, such as ``:func:`spam```,
will create a link to the place where ``spam()`` is documented,
appropriate to each output format (HTML, PDF, ePUB, etc.).

.. _xref-syntax:

Syntax
------

Sphinx supports various cross-referencing roles to create links
to other elements in the documentation.
In general, writing ``:role:`target``` creates a link to
the object called *target* of the type indicated by *role*.
The link's text depends the role but is often the same as or similar to *target*.

.. _xref-modifiers:

The behavior can be modified in the following ways:

* **Custom link text:**
  You can specify the link text explicitly using the same
  notation as in reStructuredText :ref:`external links <rst-external-links>`:
  ``:role:`custom text <target>``` will refer to *target*
  and display *custom text* as the text of the link.

* **Suppressed link:**
  Prefixing with an exclamation mark (``!``) prevents the creation of a link
  but otherwise keeps the visual output of the role.

  For example, writing ``:py:func:`!target``` displays :py:func:`!target`,
  with no link generated.

  This is helpful for cases in which the link target does not exist;
  e.g. changelog entries that describe removed functionality,
  or third-party libraries that don't support :doc:`intersphinx
  </usage/extensions/intersphinx>`.
  Suppressing the link prevents warnings in :confval:`nitpicky` mode.

* **Modified domain reference:**
  When :ref:`referencing domain objects <ref-objects>`,
  a tilde ``~`` prefix shortens the link text to the last component of the target.
  For example, ``:py:meth:`~queue.Queue.get``` will
  refer to ``queue.Queue.get`` but only display ``get`` as the link text.

  In HTML output, the link's ``title`` attribute
  (that is e.g. shown as a tool-tip on mouse-hover)
  will always be the full target name.


.. _ref-objects:

Cross-referencing objects
-------------------------

These roles are described with their respective domains:

* :ref:`C <c-xref-roles>`
* :ref:`C++ <cpp-xref-roles>`
* :ref:`JavaScript <js-xref-roles>`
* :ref:`reStructuredText <rst-xref-roles>`
* :ref:`Python <python-xref-roles>`


.. _ref-role:

Cross-referencing arbitrary locations
-------------------------------------

.. rst:role:: ref

   To support cross-referencing to arbitrary locations in any document,
   the standard reStructuredText labels are used.
   For this to work label names must be unique
   throughout the entire documentation.
   There are two ways in which you can refer to labels:

   * If you place a label directly before a section title, you can reference to
     it with ``:ref:`label-name```.  For example::

        .. _my-reference-label:

        Section to cross-reference
        --------------------------

        This is the text of the section.

        It refers to the section itself, see :ref:`my-reference-label`.

     The ``:ref:`` role would then generate a link to the section, with the
     link title being "Section to cross-reference".  This works just as well
     when section and reference are in different source files.

     Automatic labels also work with figures. For example::

        .. _my-figure:

        .. figure:: whatever

           Figure caption

     In this case, a  reference ``:ref:`my-figure``` would insert a reference
     to the figure with link text "Figure caption".

     The same works for tables that are given an explicit caption using the
     :dudir:`table` directive.

   * Labels that aren't placed before a section title can still be referenced,
     but you must give the link an explicit title, using this syntax:
     ``:ref:`Link title <label-name>```.

   .. note::

      Reference labels must start with an underscore. When referencing a label,
      the underscore must be omitted (see examples above).

   Using :rst:role:`ref` is advised over standard reStructuredText links to
   sections (like ```Section title`_``) because it works across files, when
   section headings are changed, will raise warnings if incorrect, and works
   for all builders that support cross-references.


Cross-referencing documents
---------------------------

.. versionadded:: 0.6

There is also a way to directly link to documents:

.. rst:role:: doc

   Link to the specified document; the document name can be a relative or absolute
   path and is always case-sensitive, even on Windows.  For example, if the reference
   ``:doc:`parrot``` occurs in the document ``sketches/index``, then the link
   refers to ``sketches/parrot``.  If the reference is ``:doc:`/people``` or
   ``:doc:`../people```, the link refers to ``people``.

   If no explicit link text is given (like usual: ``:doc:`Monty Python members
   </people>```), the link caption will be the title of the given document.


Referencing downloadable files
------------------------------

.. versionadded:: 0.6

.. rst:role:: download

   This role lets you link to files within your source tree
   that are not reStructuredText documents that can be viewed,
   but files that can be downloaded.

   When you use this role, the referenced file is automatically marked for
   inclusion in the output when building (obviously, for HTML output only).
   All downloadable files are put into a ``_downloads/<unique hash>/``
   subdirectory of the output directory; duplicate filenames are handled.

   An example::

      See :download:`this example script <../example.py>`.

   The given filename is usually relative to the directory the current source
   file is contained in, but if it absolute (starting with ``/``), it is taken
   as relative to the top source directory.

   The ``example.py`` file will be copied to the output directory, and a
   suitable link generated to it.

   Not to show unavailable download links, you should wrap whole paragraphs that
   have this role::

      .. only:: builder_html

         See :download:`this example script <../example.py>`.

Cross-referencing figures by figure number
------------------------------------------

.. versionadded:: 1.3

.. versionchanged:: 1.5
   :rst:role:`numref` role can also refer sections.
   And :rst:role:`numref` allows ``{name}`` for the link text.

.. rst:role:: numref

   Link to the specified figures, tables, code-blocks and sections;
   the standard reStructuredText labels are used.
   When you use this role, it will insert a reference to
   the figure with link text by its figure number like "Fig. 1.1".

   If an explicit link text is given (as usual: ``:numref:`Image of Sphinx (Fig.
   %s) <my-figure>```), the link caption will serve as title of the reference.
   As placeholders, `%s` and `{number}` get replaced by the figure
   number and  `{name}` by the figure caption.
   If no explicit link text is given, the :confval:`numfig_format` setting is
   used as fall-back default.

   If :confval:`numfig` is ``False``, figures are not numbered,
   so this role inserts not a reference but the label or the link text.

Cross-referencing other items of interest
-----------------------------------------

The following roles do possibly create a cross-reference, but do not refer to
objects:

.. rst:role:: confval

   A configuration value or setting.
   Index entries are generated.
   Also generates a link to the matching :rst:dir:`confval` directive,
   if it exists.

.. rst:role:: envvar

   An environment variable.  Index entries are generated.  Also generates a link
   to the matching :rst:dir:`envvar` directive, if it exists.

.. rst:role:: token

   The name of a grammar token (used to create links between
   :rst:dir:`productionlist` directives).

.. rst:role:: keyword

   The name of a keyword in Python.  This creates a link to a reference label
   with that name, if it exists.

.. rst:role:: option

   A command-line option to an executable program.  This generates a link to
   a :rst:dir:`option` directive, if it exists.


The following role creates a cross-reference to a term in a
:ref:`glossary <glossary-directive>`:

.. rst:role:: term

   Reference to a term in a glossary.  A glossary is created using the
   ``glossary`` directive containing a definition list with terms and
   definitions.  It does not have to be in the same file as the ``term`` markup,
   for example the Python docs have one global glossary in the ``glossary.rst``
   file.

   If you use a term that's not explained in a glossary, you'll get a warning
   during build.

   This role also supports :ref:`custom link text <xref-modifiers>` from the general
   cross-reference syntax.


.. _any-role:

Cross-referencing anything
--------------------------

.. rst:role:: any

   .. versionadded:: 1.3

   This convenience role tries to do its best to find a valid target for its
   reference text.

   * First, it tries standard cross-reference targets that would be referenced
     by :rst:role:`doc`, :rst:role:`ref` or :rst:role:`option`.

     Custom objects added to the standard domain by extensions (see
     :meth:`.Sphinx.add_object_type`) are also searched.

   * Then, it looks for objects (targets) in all loaded domains.  It is up to
     the domains how specific a match must be.  For example, in the Python
     domain a reference of ``:any:`Builder``` would match the
     ``sphinx.builders.Builder`` class.

   If none or multiple targets are found, a warning will be emitted.  In the
   case of multiple targets, you can change "any" to a specific role.

   This role is a good candidate for setting :confval:`default_role`.  If you
   do, you can write cross-references without a lot of markup overhead.  For
   example, in this Python function documentation::

      .. function:: install()

         This function installs a `handler` for every signal known by the
         `signal` module.  See the section `about-signals` for more information.

   there could be references to a glossary term (usually ``:term:`handler```), a
   Python module (usually ``:py:mod:`signal``` or ``:mod:`signal```) and a
   section (usually ``:ref:`about-signals```).

   The :rst:role:`any` role also works together with the
   :mod:`~sphinx.ext.intersphinx` extension: when no local cross-reference is
   found, all object types of intersphinx inventories are also searched.

