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

* #13180: napoleon: In Numpy-style docstrings, move ``Attributes`` and
  ``Methods`` sections after ``Parameters``.
  Patch by David Arnal.
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

Testing
-------
