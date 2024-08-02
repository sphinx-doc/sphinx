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
* #11970: singlehtml builder: make target URIs to be same-document references in
  the sense of :rfc:`RFC 3986, §4.4 <3986#section-4.4>`, e.g., ``index.html#foo``
  becomes ``#foo``. (note: continuation of a partial fix added in v7.3.0)
  Patch by Eric Norige, James Addison.

* #12514: intersphinx: fix the meaning of a negative value for
  :confval:`intersphinx_cache_limit`.
  Patch by Shengyu Zhang.

Testing
-------
