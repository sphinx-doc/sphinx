
:mod:`macpath` --- MacOS path manipulation functions
====================================================

.. module:: macpath
   :synopsis: MacOS path manipulation functions.


.. % Could be labeled \platform{Mac}, but the module should work anywhere and
.. % is distributed with the standard library.

This module is the Mac OS 9 (and earlier) implementation of the :mod:`os.path`
module. It can be used to manipulate old-style Macintosh pathnames on Mac OS X
(or any other platform). Refer to the Python Library Reference (XXX reference:
../lib/lib.html) for documentation of :mod:`os.path`.

The following functions are available in this module: :func:`normcase`,
:func:`normpath`, :func:`isabs`, :func:`join`, :func:`split`, :func:`isdir`,
:func:`isfile`, :func:`walk`, :func:`exists`. For other functions available in
:mod:`os.path` dummy counterparts are available.

