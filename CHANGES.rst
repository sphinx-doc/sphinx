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
* #13497: Support C domain objects in the table of contents.
* #13535: html search: Update to the latest version of Snowball (v3.0.1).
  Patch by Adam Turner.
* #13704: autodoc: Detect :py:func:`typing_extensions.overload <typing.overload>`
  and :py:func:`~typing.final` decorators.
  Patch by Spencer Brown.
* #13508: Initial support for PEP 695 type aliases.
  Patch by Martin Matouš.

Bugs fixed
----------

* #13369: Correctly parse and cross-reference unpacked type annotations.
  Patch by Alicia Garcia-Raboso.
* #13528: Add tilde ``~`` prefix support for :rst:role:`py:deco`.
  Patch by Shengyu Zhang and Adam Turner.

Testing
-------
