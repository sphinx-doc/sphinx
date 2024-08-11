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

* #12717: LaTeX: let :option:`-q <sphinx-build -q>` (quiet) option for
  :program:`sphinx-build -M latexpdf` or :program:`make latexpdf` (``O=-q``)
  get passed to :program:`latexmk`.  Let :option:`-Q <sphinx-build -Q>`
  (silent) apply as well to the PDF build phase.
  Patch by Jean-François B.
  
Testing
-------
