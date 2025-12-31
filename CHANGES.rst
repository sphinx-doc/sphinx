Release 9.1.0 (released Dec 31, 2025)
=====================================

Dependencies
------------

* #14153: Drop Python 3.11 support.
* #12555: Drop Docutils 0.20 support.
  Patch by Adam Turner

Features added
--------------

* Add :meth:`~sphinx.application.Sphinx.add_static_dir` for copying static
  assets from extensions to the build output.
  Patch by Jared Dillard

Bugs fixed
----------
* #13383: Emit an info-level message about duplicate internal hyperlink
  declarations.
  Patch by James Addison.

* #14189: autodoc: Fix duplicate ``:no-index-entry:`` for modules.
  Patch by Adam Turner
* #13713: Fix compatibility with MyST-Parser.
  Patch by Adam Turner
* Fix tests for Python 3.15.
  Patch by Adam Turner
* #14089: autodoc: Fix default option parsing.
  Patch by Adam Turner
* Remove incorrect static typing assertions.
  Patch by Adam Turner
* #14050: LaTeXTranslator fails to build documents using the "acronym"
  standard role.
  Patch by Günter Milde
* LaTeX: Fix rendering for grid filled merged vertical cell.
  Patch by Tim Nordell
* #14228: LaTeX: Fix overrun footer for cases of merged vertical table cells.
  Patch by Tim Nordell
* #14207: Fix creating ``HTMLThemeFactory`` objects in third-party extensions.
  Patch by Adam Turner
* #3099: LaTeX: PDF build crashes if a code-block contains more than
  circa 1350 codelines (about 27 a4-sized pages at default pointsize).
  Patch by Jean-François B.
* #14064: LaTeX: TABs ending up in sphinxVerbatim fail to obey tab stops.
  Patch by Jean-François B.
* #14089: autodoc: Improve support for non-weakreferencable objects.
  Patch by Adam Turner
* LaTeX: Fix accidental removal at ``3.5.0`` (#8854) of the documentation of
  ``literalblockcappos`` key of  :ref:`'sphinxsetup' <latexsphinxsetup>`.
  Patch by Jean-François B.
