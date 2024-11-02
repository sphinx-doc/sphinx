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

Bugs fixed
----------

* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison
* #13097: HTML Search: add a precautionary check for query term
  presence in index properties before accessing them.
  Patch by James Addison

Testing
-------
