
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

:mod:`bsddb185`
   --- Backwards compatibility module for systems which still use the Berkeley DB
   1.85 module.  It is normally only available on certain BSD Unix-based systems.
   It should never be used directly.


Multimedia
==========

:mod:`audiodev`
   --- Platform-independent API for playing audio data.

:mod:`linuxaudiodev`
   --- Play audio data on the Linux audio device.  Replaced in Python 2.3 by the
   :mod:`ossaudiodev` module.

:mod:`sunaudio`
   --- Interpret Sun audio headers (may become obsolete or a tool/demo).

:mod:`toaiff`
   --- Convert "arbitrary" sound files to AIFF files; should probably become a tool
   or demo.  Requires the external program :program:`sox`.


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

:mod:`timing`
   --- Measure time intervals to high resolution (use :func:`time.clock` instead).


SGI-specific Extension modules
==============================

The following are SGI specific, and may be out of touch with the current version
of reality.

:mod:`cl`
   --- Interface to the SGI compression library.

:mod:`sv`
   --- Interface to the "simple video" board on SGI Indigo (obsolete hardware).

