Release 8.1.0 (in development)
==============================

Dependencies
------------

Incompatible changes
--------------------

Deprecated
----------

Features added
--------------

* #12704: LaTeX: make :dudir:`contents <table-of-contents>`, :dudir:`topic`,
  and :dudir:`sidebar` directives separately customizable for PDF output.
  Patch by Jean-François B.

Bugs fixed
----------

* #12514: intersphinx: fix the meaning of a negative value for
  :confval:`intersphinx_cache_limit`.
  Patch by Shengyu Zhang.

* #12730: The ``UnreferencedFootnotesDetector`` transform has been improved
  to more consistently detect unreferenced footnotes.
  Note, the priority of the transform has been changed from 200 to 622,
  so that it now runs after the docutils ``Footnotes`` resolution transform.
  Patch by Chris Sewell.

Testing
-------
