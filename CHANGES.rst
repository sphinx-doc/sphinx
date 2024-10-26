Release 8.2.0 (in development)
==============================

Dependencies
------------

* #13000: Drop Python 3.10 support.

Incompatible changes
--------------------

Deprecated
----------

Features added
--------------

* #12975: Add the possibility to avoid rendering a trailing comma in Python and
Javascript multi-line signatures, via
:confval:`python_trailing_comma_in_multi_line_signatures` and
:confval:`javascript_trailing_comma_in_multi_line_signatures`, respectively.

Bugs fixed
----------

* #12975: Avoid rendering a trailing comma in C and C++ multi-line signatures.
* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison

Testing
-------
