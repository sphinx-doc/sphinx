
.. _undocumented-modules:

********************
Undocumented Modules
********************

The modules in this chapter are poorly documented (if at all).  If you wish to
contribute documentation of any of these modules, please get in touch with
`docs@python.org <mailto:docs@python.org>`_.


.. toctree::


:mod:`applesingle` --- AppleSingle decoder
==========================================

.. module:: applesingle
   :platform: Mac
   :synopsis: Rudimentary decoder for AppleSingle format files.



:mod:`buildtools` --- Helper module for BuildApplet and Friends
===============================================================

.. module:: buildtools
   :platform: Mac
   :synopsis: Helper module for BuildApplet, BuildApplication and macfreeze.


.. deprecated:: 2.4

:mod:`cfmfile` --- Code Fragment Resource module
================================================

.. module:: cfmfile
   :platform: Mac
   :synopsis: Code Fragment Resource module.


:mod:`cfmfile` is a module that understands Code Fragments and the accompanying
"cfrg" resources. It can parse them and merge them, and is used by
BuildApplication to combine all plugin modules to a single executable.

.. deprecated:: 2.4

:mod:`icopen` --- Internet Config replacement for :meth:`open`
==============================================================

.. module:: icopen
   :platform: Mac
   :synopsis: Internet Config replacement for open().


Importing :mod:`icopen` will replace the builtin :meth:`open` with a version
that uses Internet Config to set file type and creator for new files.


:mod:`macerrors` --- Mac OS Errors
==================================

.. module:: macerrors
   :platform: Mac
   :synopsis: Constant definitions for many Mac OS error codes.


:mod:`macerrors` contains constant definitions for many Mac OS error codes.


:mod:`macresource` --- Locate script resources
==============================================

.. module:: macresource
   :platform: Mac
   :synopsis: Locate script resources.


:mod:`macresource` helps scripts finding their resources, such as dialogs and
menus, without requiring special case code for when the script is run under
MacPython, as a MacPython applet or under OSX Python.


:mod:`Nav` --- NavServices calls
================================

.. module:: Nav
   :platform: Mac
   :synopsis: Interface to Navigation Services.


A low-level interface to Navigation Services.


:mod:`PixMapWrapper` --- Wrapper for PixMap objects
===================================================

.. module:: PixMapWrapper
   :platform: Mac
   :synopsis: Wrapper for PixMap objects.


:mod:`PixMapWrapper` wraps a PixMap object with a Python object that allows
access to the fields by name. It also has methods to convert to and from
:mod:`PIL` images.


:mod:`videoreader` --- Read QuickTime movies
============================================

.. module:: videoreader
   :platform: Mac
   :synopsis: Read QuickTime movies frame by frame for further processing.


:mod:`videoreader` reads and decodes QuickTime movies and passes a stream of
images to your program. It also provides some support for audio tracks.


:mod:`W` --- Widgets built on :mod:`FrameWork`
==============================================

.. module:: W
   :platform: Mac
   :synopsis: Widgets for the Mac, built on top of FrameWork.


The :mod:`W` widgets are used extensively in the :program:`IDE`.

