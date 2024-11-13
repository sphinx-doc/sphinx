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
* #11233: linkcheck: match redirect URIs against :confval:`linkcheck_ignore` by
  overriding session-level ``requests.get_redirect_target``.

Testing
-------
