
.. _toolbox:

*********************
MacOS Toolbox Modules
*********************

There are a set of modules that provide interfaces to various MacOS toolboxes.
If applicable the module will define a number of Python objects for the various
structures declared by the toolbox, and operations will be implemented as
methods of the object.  Other operations will be implemented as functions in the
module.  Not all operations possible in C will also be possible in Python
(callbacks are often a problem), and parameters will occasionally be different
in Python (input and output buffers, especially).  All methods and functions
have a :attr:`__doc__` string describing their arguments and return values, and
for additional description you are referred to `Inside Macintosh
<http://developer.apple.com/documentation/macos8/mac8.html>`_ or similar works.

These modules all live in a package called :mod:`Carbon`. Despite that name they
are not all part of the Carbon framework: CF is really in the CoreFoundation
framework and Qt is in the QuickTime framework. The normal use pattern is ::

   from Carbon import AE

**Warning!**  These modules are not yet documented.  If you wish to contribute
documentation of any of these modules, please get in touch with docs@python.org.


.. toctree::

   colorpicker.rst
.. % \section{Argument Handling for Toolbox Modules}


:mod:`Carbon.AE` --- Apple Events
=================================

.. module:: Carbon.AE
   :platform: Mac
   :synopsis: Interface to the Apple Events toolbox.



:mod:`Carbon.AH` --- Apple Help
===============================

.. module:: Carbon.AH
   :platform: Mac
   :synopsis: Interface to the Apple Help manager.



:mod:`Carbon.App` --- Appearance Manager
========================================

.. module:: Carbon.App
   :platform: Mac
   :synopsis: Interface to the Appearance Manager.



:mod:`Carbon.CF` --- Core Foundation
====================================

.. module:: Carbon.CF
   :platform: Mac
   :synopsis: Interface to the Core Foundation.


The ``CFBase``, ``CFArray``, ``CFData``, ``CFDictionary``, ``CFString`` and
``CFURL`` objects are supported, some only partially.


:mod:`Carbon.CG` --- Core Graphics
==================================

.. module:: Carbon.CG
   :platform: Mac
   :synopsis: Interface to the Component Manager.



:mod:`Carbon.CarbonEvt` --- Carbon Event Manager
================================================

.. module:: Carbon.CarbonEvt
   :platform: Mac
   :synopsis: Interface to the Carbon Event Manager.



:mod:`Carbon.Cm` --- Component Manager
======================================

.. module:: Carbon.Cm
   :platform: Mac
   :synopsis: Interface to the Component Manager.



:mod:`Carbon.Ctl` --- Control Manager
=====================================

.. module:: Carbon.Ctl
   :platform: Mac
   :synopsis: Interface to the Control Manager.



:mod:`Carbon.Dlg` --- Dialog Manager
====================================

.. module:: Carbon.Dlg
   :platform: Mac
   :synopsis: Interface to the Dialog Manager.



:mod:`Carbon.Evt` --- Event Manager
===================================

.. module:: Carbon.Evt
   :platform: Mac
   :synopsis: Interface to the classic Event Manager.



:mod:`Carbon.Fm` --- Font Manager
=================================

.. module:: Carbon.Fm
   :platform: Mac
   :synopsis: Interface to the Font Manager.



:mod:`Carbon.Folder` --- Folder Manager
=======================================

.. module:: Carbon.Folder
   :platform: Mac
   :synopsis: Interface to the Folder Manager.



:mod:`Carbon.Help` --- Help Manager
===================================

.. module:: Carbon.Help
   :platform: Mac
   :synopsis: Interface to the Carbon Help Manager.



:mod:`Carbon.List` --- List Manager
===================================

.. module:: Carbon.List
   :platform: Mac
   :synopsis: Interface to the List Manager.



:mod:`Carbon.Menu` --- Menu Manager
===================================

.. module:: Carbon.Menu
   :platform: Mac
   :synopsis: Interface to the Menu Manager.



:mod:`Carbon.Mlte` --- MultiLingual Text Editor
===============================================

.. module:: Carbon.Mlte
   :platform: Mac
   :synopsis: Interface to the MultiLingual Text Editor.



:mod:`Carbon.Qd` --- QuickDraw
==============================

.. module:: Carbon.Qd
   :platform: Mac
   :synopsis: Interface to the QuickDraw toolbox.



:mod:`Carbon.Qdoffs` --- QuickDraw Offscreen
============================================

.. module:: Carbon.Qdoffs
   :platform: Mac
   :synopsis: Interface to the QuickDraw Offscreen APIs.



:mod:`Carbon.Qt` --- QuickTime
==============================

.. module:: Carbon.Qt
   :platform: Mac
   :synopsis: Interface to the QuickTime toolbox.



:mod:`Carbon.Res` --- Resource Manager and Handles
==================================================

.. module:: Carbon.Res
   :platform: Mac
   :synopsis: Interface to the Resource Manager and Handles.



:mod:`Carbon.Scrap` --- Scrap Manager
=====================================

.. module:: Carbon.Scrap
   :platform: Mac
   :synopsis: Interface to the Carbon Scrap Manager.



:mod:`Carbon.Snd` --- Sound Manager
===================================

.. module:: Carbon.Snd
   :platform: Mac
   :synopsis: Interface to the Sound Manager.



:mod:`Carbon.TE` --- TextEdit
=============================

.. module:: Carbon.TE
   :platform: Mac
   :synopsis: Interface to TextEdit.



:mod:`Carbon.Win` --- Window Manager
====================================

.. module:: Carbon.Win
   :platform: Mac
   :synopsis: Interface to the Window Manager.


