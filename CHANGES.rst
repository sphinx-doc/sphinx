Release 8.2.0 (in development)
==============================

Dependencies
------------

* #13000: Drop Python 3.10 support.

Incompatible changes
--------------------

Deprecated
----------

* #13037: Deprecate the ``SingleHTMLBuilder.fix_refuris`` method.
  Patch by James Addison.

Features added
--------------

* Add a new ``duplicate_declaration`` warning type,
  with ``duplicate_declaration.c`` and ``duplicate_declaration.cpp`` subtypes.
  Patch by Julien Lecomte and Adam Turner.

Bugs fixed
----------

* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison
* #13130: LaTeX docs: ``pdflatex`` index creation may fail for index entries
  in French.  See :confval:`latex_use_xindy`.
  Patch by Jean-François B.
* LaTeX: fix a ``7.4.0`` typo in a default for ``\sphinxboxsetup``
  (refs: PR #13152).
  Patch by Jean-François B.
* #13096: HTML Search: check that query terms exist as properties in
  term indices before accessing them.

Testing
-------
