Release 8.2.0 (in development)
==============================

Dependencies
------------

* #13000: Drop Python 3.10 support.

Incompatible changes
--------------------

* #13044: Remove the internal and undocumented ``has_equations`` data and
  :py:meth:`!has_equations` method from the :py:class:`!MathDomain`` domain.
  Patch by Adam Turner.

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
* LaTeX: fix a ``7.4.0`` typo in a default for ``\sphinxboxsetup``
  (refs: PR #13152).
  Patch by Jean-François B.

Testing
-------
