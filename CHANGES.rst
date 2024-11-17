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

Bugs fixed
----------

* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison

* #13130: LaTeX docs: ``pdflatex`` index creation may fail for index entries
  in French.  See :confval:`latex_use_xindy`.
  Patch by Jean-François B.

Testing
-------
