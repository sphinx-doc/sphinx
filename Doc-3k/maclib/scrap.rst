
:mod:`Carbon.Scrap` --- Scrap Manager
=====================================

.. module:: Carbon.Scrap
   :platform: Mac
   :synopsis: The Scrap Manager provides basic services for implementing cut & paste and
              clipboard operations.


This module is only fully available on MacOS9 and earlier under classic PPC
MacPython.  Very limited functionality is available under Carbon MacPython.

.. index:: single: Scrap Manager

The Scrap Manager supports the simplest form of cut & paste operations on the
Macintosh.  It can be use for both inter- and intra-application clipboard
operations.

The :mod:`Scrap` module provides low-level access to the functions of the Scrap
Manager.  It contains the following functions:


.. function:: InfoScrap()

   Return current information about the scrap.  The information is encoded as a
   tuple containing the fields ``(size, handle, count, state, path)``.

   +----------+---------------------------------------------+
   | Field    | Meaning                                     |
   +==========+=============================================+
   | *size*   | Size of the scrap in bytes.                 |
   +----------+---------------------------------------------+
   | *handle* | Resource object representing the scrap.     |
   +----------+---------------------------------------------+
   | *count*  | Serial number of the scrap contents.        |
   +----------+---------------------------------------------+
   | *state*  | Integer; positive if in memory, ``0`` if on |
   |          | disk, negative if uninitialized.            |
   +----------+---------------------------------------------+
   | *path*   | Filename of the scrap when stored on disk.  |
   +----------+---------------------------------------------+


.. seealso::

   `Scrap Manager <http://developer.apple.com/documentation/mac/MoreToolbox/MoreToolbox-109.html>`_
      Apple's documentation for the Scrap Manager gives a lot of useful information
      about using the Scrap Manager in applications.

