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

* #13098: HTML Search: the contents of the search index are sanitised
  (reassigned to frozen null-prototype JavaScript objects), to reduce
  the risk of unintended access or modification.
  Patch by James Addison

Bugs fixed
----------

* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison

Testing
-------
