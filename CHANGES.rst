Release 8.3.0 (in development)
==============================

Dependencies
------------

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
  Patch by Adam Turner.
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
* #13611: Allow `Pygments style <https://pygments.org/styles/>`_ overriding on a
  per-block basis via new options (:rst:dir:`code-block:style-light` and
  :rst:dir:`code-block:style-dark`) for the :rst:dir:`code-block`,
  :rst:dir:`sourcecode`, :rst:dir:`literalinclude` and :rst:dir:`code`.
  Patch by Héctor Medina Abarca.

Bugs fixed
----------

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

Testing
-------
