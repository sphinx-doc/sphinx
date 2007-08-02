.. _other-gui-packages:

Other Graphical User Interface Packages
=======================================

There are an number of extension widget sets to :mod:`Tkinter`.


.. seealso::

   `Python megawidgets <http://pmw.sourceforge.net/>`_
      is a toolkit for building high-level compound widgets in Python using the
      :mod:`Tkinter` module.  It consists of a set of base classes and a library of
      flexible and extensible megawidgets built on this foundation. These megawidgets
      include notebooks, comboboxes, selection widgets, paned widgets, scrolled
      widgets, dialog windows, etc.  Also, with the Pmw.Blt interface to BLT, the
      busy, graph, stripchart, tabset and vector commands are be available.

      The initial ideas for Pmw were taken from the Tk ``itcl`` extensions ``[incr
      Tk]`` by Michael McLennan and ``[incr Widgets]`` by Mark Ulferts. Several of the
      megawidgets are direct translations from the itcl to Python. It offers most of
      the range of widgets that ``[incr Widgets]`` does, and is almost as complete as
      Tix, lacking however Tix's fast :class:`HList` widget for drawing trees.

   `Tkinter3000 Widget Construction Kit (WCK) <http://tkinter.effbot.org/>`_
      is a library that allows you to write new Tkinter widgets in pure Python.  The
      WCK framework gives you full control over widget creation, configuration, screen
      appearance, and event handling.  WCK widgets can be very fast and light-weight,
      since they can operate directly on Python data structures, without having to
      transfer data through the Tk/Tcl layer.

      .. % 

Other GUI packages are also available for Python:


.. seealso::

   `wxPython <http://www.wxpython.org>`_
      wxPython is a cross-platform GUI toolkit for Python that is built around the
      popular `wxWidgets <http://www.wxwidgets.org/>`_ C++ toolkit.  It provides a
      native look and feel for applications on Windows, Mac OS X, and Unix systems by
      using each platform's native widgets where ever possible, (GTK+ on Unix-like
      systems).  In addition to an extensive set of widgets, wxPython provides classes
      for online documentation and context sensitive help, printing, HTML viewing,
      low-level device context drawing, drag and drop, system clipboard access, an
      XML-based resource format and more, including an ever growing library of user-
      contributed modules.  Both the wxWidgets and wxPython projects are under active
      development and continuous improvement, and have active and helpful user and
      developer communities.

   `wxPython in Action <http://www.amazon.com/exec/obidos/ASIN/1932394621>`_
      The wxPython book, by Noel Rappin and Robin Dunn.

   PyQt
      PyQt is a :program:`sip`\ -wrapped binding to the Qt toolkit.  Qt is an
      extensive C++ GUI toolkit that is available for Unix, Windows and Mac OS X.
      :program:`sip` is a tool for generating bindings for C++ libraries as Python
      classes, and is specifically designed for Python. An online manual is available
      at http://www.opendocspublishing.com/pyqt/ (errata are located at
      http://www.valdyas.org/python/book.html).

   `PyKDE <http://www.riverbankcomputing.co.uk/pykde/index.php>`_
      PyKDE is a :program:`sip`\ -wrapped interface to the KDE desktop libraries.  KDE
      is a desktop environment for Unix computers; the graphical components are based
      on Qt.

   `FXPy <http://fxpy.sourceforge.net/>`_
      is a Python extension module which provides an interface to the  `FOX
      <http://www.cfdrc.com/FOX/fox.html>`_ GUI. FOX is a C++ based Toolkit for
      developing Graphical User Interfaces easily and effectively. It offers a wide,
      and growing, collection of Controls, and provides state of the art facilities
      such as drag and drop, selection, as well as OpenGL widgets for 3D graphical
      manipulation.  FOX also implements icons, images, and user-convenience features
      such as status line help, and tooltips.

      Even though FOX offers a large collection of controls already, FOX leverages C++
      to allow programmers to easily build additional Controls and GUI elements,
      simply by taking existing controls, and creating a derived class which simply
      adds or redefines the desired behavior.

   `PyGTK <http://www.daa.com.au/~james/software/pygtk/>`_
      is a set of bindings for the `GTK <http://www.gtk.org/>`_ widget set. It
      provides an object oriented interface that is slightly higher level than the C
      one. It automatically does all the type casting and reference counting that you
      would have to do normally with the C API. There are also `bindings
      <http://www.daa.com.au/~james/gnome/>`_ to  `GNOME <http://www.gnome.org>`_, and
      a  `tutorial
      <http://laguna.fmedic.unam.mx/~daniel/pygtutorial/pygtutorial/index.html>`_ is
      available.

.. % XXX Reference URLs that compare the different UI packages

