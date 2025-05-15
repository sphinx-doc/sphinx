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
* #10385: Add RTL (right-to-left) support for all Sphinx themes via the ``is_rtl``
  theme option. Includes automatic layout mirroring, and bidirectional text support.
  Patch by Alireza Shabani.

Bugs fixed
----------

* #13369: Correctly parse and cross-reference unpacked type annotations.
  Patch by Alicia Garcia-Raboso.

Testing
-------
