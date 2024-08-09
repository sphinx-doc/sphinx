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

* #12743: No longer exit on the first warning when
  :option:`--fail-on-warning  <sphinx-build --fail-on-warning>` is used.
  Instead, exit with a non-zero status if any warnings were generated
  during the build.
  Patch by Adam Turner.
* #12743: Add :option:`sphinx-build --debug-warnings` to debug warnings when
  :option:`sphinx-build --pdb` is specified.
  Patch by Adam Turner and Jeremy Maitin-Shepard.

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
