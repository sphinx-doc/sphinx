Release 9.1.0 (in development)
==============================

Dependencies
------------

* #14153: Drop Python 3.11 support.
* #12555: Drop Docutils 0.20 support.
  Patch by Adam Turner

Incompatible changes
--------------------

Deprecated
----------

Features added
--------------

Bugs fixed
----------

* LaTeX: Fix rendering for grid filled merged vertical cell
  (PR #14024).
  Patch by Tim Nordell
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
* #14207: Fix creating ``HTMLThemeFactory`` objects in third-party extensions.
  Patch by Adam Turner

Testing
-------
