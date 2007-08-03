
.. _undoc:

********************
Undocumented Modules
********************

Here's a quick listing of modules that are currently undocumented, but that
should be documented.  Feel free to contribute documentation for them!  (Send
via email to docs@python.org.)

The idea and original contents for this chapter were taken from a posting by
Fredrik Lundh; the specific contents of this chapter have been substantially
revised.


Frameworks
==========

Frameworks tend to be harder to document, but are well worth the effort spent.


   None at this time.


Miscellaneous useful utilities
==============================

Some of these are very old and/or not very robust; marked with "hmm."

:mod:`bdb`
   --- A generic Python debugger base class (used by pdb).

:mod:`ihooks`
   --- Import hook support (for :mod:`rexec`; may become obsolete).


Platform specific modules
=========================

These modules are used to implement the :mod:`os.path` module, and are not
documented beyond this mention.  There's little need to document these.

:mod:`ntpath`
   --- Implementation of :mod:`os.path` on Win32, Win64, WinCE, and OS/2 platforms.

:mod:`posixpath`
   --- Implementation of :mod:`os.path` on POSIX.


Multimedia
==========

:mod:`linuxaudiodev`
   --- Play audio data on the Linux audio device.  Replaced in Python 2.3 by the
   :mod:`ossaudiodev` module.

:mod:`sunaudio`
   --- Interpret Sun audio headers (may become obsolete or a tool/demo).


.. _obsolete-modules:

Obsolete
========

These modules are not normally available for import; additional work must be
done to make them available.

These extension modules written in C are not built by default. Under Unix, these
must be enabled by uncommenting the appropriate lines in :file:`Modules/Setup`
in the build tree and either rebuilding Python if the modules are statically
linked, or building and installing the shared object if using dynamically-loaded
extensions.

.. % %% lib-old is empty as of Python 2.5
.. % Those which are written in Python will be installed into the directory
.. % \file{lib-old/} installed as part of the standard library.  To use
.. % these, the directory must be added to \code{sys.path}, possibly using
.. % \envvar{PYTHONPATH}.

.. % XXX need Windows instructions!


   --- This section should be empty for Python 3.0.

