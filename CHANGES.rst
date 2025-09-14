Release 8.3.0 (in development)
==============================

Dependencies
------------

* #13786: Support `Docutils 0.22`_. Patch by Adam Turner.

  .. _Docutils 0.22: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-22-2026-07-29

Incompatible changes
--------------------

* #13639: :py:meth:`!SphinxComponentRegistry.create_source_parser` no longer
  has an *app* parameter, instead taking *config* and *env*.
  Patch by Adam Turner.

Deprecated
----------

* 13627: Deprecate remaining public :py:attr:`!.app` attributes,
  including ``builder.app``, ``env.app``, ``events.app``,
  and ``SphinxTransform.`app``.
  Patch by Adam Turner.
* #13637: Deprecate the :py:meth:`!set_application` method
  of :py:class:`~sphinx.parsers.Parser` objects.
  Patch by Adam Turner.
* #13644: Deprecate the :py:attr:`!Parser.config` and :py:attr:`!env` attributes.
  Patch by Adam Turner.
* #13665: Deprecate support for non-UTF 8 source encodings,
  scheduled for removal in Sphinx 10.
  Patch by Adam Turner.
* #13679: Non-decodable characters in source files will raise an error in Sphinx 9.
  Currently, such bytes are replaced with '?' along with logging a warning.
  Patch by Adam Turner.
* #13682: Deprecate :py:mod:`!sphinx.io`.
  Sphinx no longer uses the :py:mod:`!sphinx.io` classes,
  having replaced them with standard Python I/O.
  The entire :py:mod:`!sphinx.io` module will be removed in Sphinx 10.
  Patch by Adam Turner.

Features added
--------------

* #13332: Add :confval:`doctest_fail_fast` option to exit after the first failed
  test.
  Patch by Till Hoffmann.
* #13439: linkcheck: Permit warning on every redirect with
  ``linkcheck_allowed_redirects = {}``.
  Patch by Adam Turner and James Addison.
* #13497: Support C domain objects in the table of contents.
* #13500: LaTeX: add support for ``fontawesome6`` package.
  Patch by Jean-François B.
* #13509: autodoc: Detect :py:func:`typing_extensions.overload <typing.overload>`
  and :py:func:`~typing.final` decorators.
  Patch by Spencer Brown.
* #13535: html search: Update to the latest version of Snowball (v3.0.1).
  Patch by Adam Turner.
* #13647: LaTeX: allow more cases of table nesting.
  Patch by Jean-François B.
* #13657: LaTeX: support CSS3 length units.
  Patch by Jean-François B.
* #13684: intersphinx: Add a file-based cache for remote inventories.
  The location of the cache directory must not be relied upon externally,
  as it may change without notice or warning in future releases.
  Patch by Adam Turner.
* #13805: LaTeX: add support for ``fontawesome7`` package.
  Patch by Jean-François B.

Bugs fixed
----------

* #1327: LaTeX: tables using longtable raise error if
  :rst:dir:`tabularcolumns` specifies automatic widths
  (``L``, ``R``, ``C``, or ``J``).
  Patch by Jean-François B.
* #3447: LaTeX: when assigning longtable class to table for PDF, it may render
  "horizontally" and overflow in right margin.
  Patch by Jean-François B.
* #8828: LaTeX: adding a footnote to a longtable cell causes table to occupy
  full width.
  Patch by Jean-François B.
* #11498: LaTeX: Table in cell fails to build if it has many rows.
  Patch by Jean-François B.
* #11515: LaTeX: longtable does not allow nested table.
  Patch by Jean-François B.
* #11973: LaTeX: links in table captions do not work in PDF.
  Patch by Jean-François B.
* #12821: LaTeX: URLs/links in section titles should render in PDF.
  Patch by Jean-François B.
* #13369: Correctly parse and cross-reference unpacked type annotations.
  Patch by Alicia Garcia-Raboso.
* #13528: Add tilde ``~`` prefix support for :rst:role:`py:deco`.
  Patch by Shengyu Zhang and Adam Turner.
* #13597: LaTeX: table nested in a merged cell leads to invalid LaTeX mark-up
  and PDF cannot be built.
  Patch by Jean-François B.
* #13619: LaTeX: possible duplicated footnotes in PDF from object signatures
  (typically if :confval:`latex_show_urls` ``= 'footnote'``).
  Patch by Jean-François B.
* #13635: LaTeX: if a cell contains a table, row coloring is turned off for
  the next table cells.
  Patch by Jean-François B.
* #13685: gettext: Correctly ignore trailing backslashes.
  Patch by Bénédikt Tran.
* #13712: intersphinx: Don't add "v" prefix to non-numeric versions.
  Patch by Szymon Karpinski.
* #13688: HTML builder: Replace ``<em class="property">`` with
  ``<span class="property">`` for attribute type annotations
  to improve `semantic HTML structure
  <https://html.spec.whatwg.org/multipage/text-level-semantics.html>`__.
  Patch by Mark Ostroth.
* #13812 (discussion): LaTeX: long :rst:dir:`confval` value does not wrap at
  spaces in PDF.
  Patch by Jean-François B.
* #10785: Autodoc: Allow type aliases defined in the project to be properly
  cross-referenced when used as type annotations. This makes it possible
  for objects documented as ``:py:data:`` to be hyperlinked in function signatures.
* #13858: doctest: doctest blocks are now correctly added to a group defined by the
  configuration variable ``doctest_test_doctest_blocks``.


Testing
-------
