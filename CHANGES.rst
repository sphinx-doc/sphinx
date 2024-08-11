Release 8.1.0 (in development)
==============================

Dependencies
------------

* #12756: Add lower-bounds to the ``sphinxcontrib-*`` dependencies.
  Patch by Adam Turner.

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

* #12587: Do not warn when potential ambiguity detected during Intersphinx
  resolution occurs due to duplicate targets that differ case-insensitively.
  Patch by James Addison.

Testing
-------

* #12141: Migrate from the deprecated ``karma`` JavaScript test framework to
  the actively-maintained ``jasmine`` framework.  Test coverage is unaffected.
  Patch by James Addison.
