Release 8.3.0 (in development)
==============================

Dependencies
------------

Incompatible changes
--------------------

Deprecated
----------

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
* #13535: html search: Update to the latest version of Snowball (v3.0.1).
  Patch by Adam Turner.
* #13704: autodoc: Detect :py:func:`typing_extensions.overload <typing.overload>`
  and :py:func:`~typing.final` decorators.
  Patch by Spencer Brown.
* Allow `Pygments style <https://pygments.org/styles/>`_ overriding on a per-block 
  basis via new options (:rst:dir:`code-block:style-light` and 
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

Testing
-------
