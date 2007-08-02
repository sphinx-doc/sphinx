
.. _tkinter:

*********************************
Graphical User Interfaces with Tk
*********************************

.. index::
   single: GUI
   single: Graphical User Interface
   single: Tkinter
   single: Tk

Tk/Tcl has long been an integral part of Python.  It provides a robust and
platform independent windowing toolkit, that is available to Python programmers
using the :mod:`Tkinter` module, and its extension, the :mod:`Tix` module.

The :mod:`Tkinter` module is a thin object-oriented layer on top of Tcl/Tk. To
use :mod:`Tkinter`, you don't need to write Tcl code, but you will need to
consult the Tk documentation, and occasionally the Tcl documentation.
:mod:`Tkinter` is a set of wrappers that implement the Tk widgets as Python
classes.  In addition, the internal module :mod:`_tkinter` provides a threadsafe
mechanism which allows Python and Tcl to interact.

Tk is not the only GUI for Python; see section :ref:`other-gui-packages` for
more information on other GUI toolkits for Python.

.. % Other sections I have in mind are
.. % Tkinter internals
.. % Freezing Tkinter applications


.. toctree::


:mod:`Tkinter` --- Python interface to Tcl/Tk
=============================================

.. module:: Tkinter
   :synopsis: Interface to Tcl/Tk for graphical user interfaces
.. moduleauthor:: Guido van Rossum <guido@Python.org>


The :mod:`Tkinter` module ("Tk interface") is the standard Python interface to
the Tk GUI toolkit.  Both Tk and :mod:`Tkinter` are available on most Unix
platforms, as well as on Windows and Macintosh systems.  (Tk itself is not part
of Python; it is maintained at ActiveState.)


.. seealso::

   `Python Tkinter Resources <http://www.python.org/topics/tkinter/>`_
      The Python Tkinter Topic Guide provides a great deal of information on using Tk
      from Python and links to other sources of information on Tk.

   `An Introduction to Tkinter <http://www.pythonware.com/library/an-introduction-to-tkinter.htm>`_
      Fredrik Lundh's on-line reference material.

   `Tkinter reference: a GUI for Python <http://www.nmt.edu/tcc/help/pubs/lang.html>`_
      On-line reference material.

   `Tkinter for JPython <http://jtkinter.sourceforge.net>`_
      The Jython interface to Tkinter.

   `Python and Tkinter Programming <http://www.amazon.com/exec/obidos/ASIN/1884777813>`_
      The book by John Grayson (ISBN 1-884777-81-3).


Tkinter Modules
---------------

Most of the time, the :mod:`Tkinter` module is all you really need, but a number
of additional modules are available as well.  The Tk interface is located in a
binary module named :mod:`_tkinter`. This module contains the low-level
interface to Tk, and should never be used directly by application programmers.
It is usually a shared library (or DLL), but might in some cases be statically
linked with the Python interpreter.

In addition to the Tk interface module, :mod:`Tkinter` includes a number of
Python modules. The two most important modules are the :mod:`Tkinter` module
itself, and a module called :mod:`Tkconstants`. The former automatically imports
the latter, so to use Tkinter, all you need to do is to import one module::

   import Tkinter

Or, more often::

   from Tkinter import *


.. class:: Tk(screenName=None, baseName=None, className='Tk', useTk=1)

   The :class:`Tk` class is instantiated without arguments. This creates a toplevel
   widget of Tk which usually is the main window of an application. Each instance
   has its own associated Tcl interpreter.

   .. % FIXME: The following keyword arguments are currently recognized:

   .. versionchanged:: 2.4
      The *useTk* parameter was added.


.. function:: Tcl(screenName=None, baseName=None, className='Tk', useTk=0)

   The :func:`Tcl` function is a factory function which creates an object much like
   that created by the :class:`Tk` class, except that it does not initialize the Tk
   subsystem.  This is most often useful when driving the Tcl interpreter in an
   environment where one doesn't want to create extraneous toplevel windows, or
   where one cannot (such as Unix/Linux systems without an X server).  An object
   created by the :func:`Tcl` object can have a Toplevel window created (and the Tk
   subsystem initialized) by calling its :meth:`loadtk` method.

   .. versionadded:: 2.4

Other modules that provide Tk support include:

:mod:`ScrolledText`
   Text widget with a vertical scroll bar built in.

:mod:`tkColorChooser`
   Dialog to let the user choose a color.

:mod:`tkCommonDialog`
   Base class for the dialogs defined in the other modules listed here.

:mod:`tkFileDialog`
   Common dialogs to allow the user to specify a file to open or save.

:mod:`tkFont`
   Utilities to help work with fonts.

:mod:`tkMessageBox`
   Access to standard Tk dialog boxes.

:mod:`tkSimpleDialog`
   Basic dialogs and convenience functions.

:mod:`Tkdnd`
   Drag-and-drop support for :mod:`Tkinter`. This is experimental and should become
   deprecated when it is replaced  with the Tk DND.

:mod:`turtle`
   Turtle graphics in a Tk window.


Tkinter Life Preserver
----------------------

.. sectionauthor:: Matt Conway


This section is not designed to be an exhaustive tutorial on either Tk or
Tkinter.  Rather, it is intended as a stop gap, providing some introductory
orientation on the system.

.. % Converted to LaTeX by Mike Clarkson.

Credits:

* Tkinter was written by Steen Lumholt and Guido van Rossum.

* Tk was written by John Ousterhout while at Berkeley.

* This Life Preserver was written by Matt Conway at the University of Virginia.

* The html rendering, and some liberal editing, was produced from a FrameMaker
  version by Ken Manheimer.

* Fredrik Lundh elaborated and revised the class interface descriptions, to get
  them current with Tk 4.2.

* Mike Clarkson converted the documentation to LaTeX, and compiled the  User
  Interface chapter of the reference manual.


How To Use This Section
^^^^^^^^^^^^^^^^^^^^^^^

This section is designed in two parts: the first half (roughly) covers
background material, while the second half can be taken to the keyboard as a
handy reference.

When trying to answer questions of the form "how do I do blah", it is often best
to find out how to do"blah" in straight Tk, and then convert this back into the
corresponding :mod:`Tkinter` call. Python programmers can often guess at the
correct Python command by looking at the Tk documentation. This means that in
order to use Tkinter, you will have to know a little bit about Tk. This document
can't fulfill that role, so the best we can do is point you to the best
documentation that exists. Here are some hints:

* The authors strongly suggest getting a copy of the Tk man pages. Specifically,
  the man pages in the ``mann`` directory are most useful. The ``man3`` man pages
  describe the C interface to the Tk library and thus are not especially helpful
  for script writers.

* Addison-Wesley publishes a book called Tcl and the Tk Toolkit by John
  Ousterhout (ISBN 0-201-63337-X) which is a good introduction to Tcl and Tk for
  the novice.  The book is not exhaustive, and for many details it defers to the
  man pages.

* :file:`Tkinter.py` is a last resort for most, but can be a good place to go
  when nothing else makes sense.


.. seealso::

   `ActiveState Tcl Home Page <http://tcl.activestate.com/>`_
      The Tk/Tcl development is largely taking place at ActiveState.

   `Tcl and the Tk Toolkit <http://www.amazon.com/exec/obidos/ASIN/020163337X>`_
      The book by John Ousterhout, the inventor of Tcl .

   `Practical Programming in Tcl and Tk <http://www.amazon.com/exec/obidos/ASIN/0130220280>`_
      Brent Welch's encyclopedic book.


A Simple Hello World Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. % HelloWorld.html
.. % begin{latexonly}
.. % \begin{figure}[hbtp]
.. % \centerline{\epsfig{file=HelloWorld.gif,width=.9\textwidth}}
.. % \vspace{.5cm}
.. % \caption{HelloWorld gadget image}
.. % \end{figure}
.. % See also the hello-world \ulink{notes}{classes/HelloWorld-notes.html} and
.. % \ulink{summary}{classes/HelloWorld-summary.html}.
.. % end{latexonly}

::

   from Tkinter import *

   class Application(Frame):
       def say_hi(self):
           print "hi there, everyone!"

       def createWidgets(self):
           self.QUIT = Button(self)
           self.QUIT["text"] = "QUIT"
           self.QUIT["fg"]   = "red"
           self.QUIT["command"] =  self.quit

           self.QUIT.pack({"side": "left"})

           self.hi_there = Button(self)
           self.hi_there["text"] = "Hello",
           self.hi_there["command"] = self.say_hi

           self.hi_there.pack({"side": "left"})

       def __init__(self, master=None):
           Frame.__init__(self, master)
           self.pack()
           self.createWidgets()

   root = Tk()
   app = Application(master=root)
   app.mainloop()
   root.destroy()


A (Very) Quick Look at Tcl/Tk
-----------------------------

The class hierarchy looks complicated, but in actual practice, application
programmers almost always refer to the classes at the very bottom of the
hierarchy.

.. % BriefTclTk.html

Notes:

* These classes are provided for the purposes of organizing certain functions
  under one namespace. They aren't meant to be instantiated independently.

* The :class:`Tk` class is meant to be instantiated only once in an application.
  Application programmers need not instantiate one explicitly, the system creates
  one whenever any of the other classes are instantiated.

* The :class:`Widget` class is not meant to be instantiated, it is meant only
  for subclassing to make "real" widgets (in C++, this is called an 'abstract
  class').

To make use of this reference material, there will be times when you will need
to know how to read short passages of Tk and how to identify the various parts
of a Tk command.   (See section :ref:`tkinter-basic-mapping` for the
:mod:`Tkinter` equivalents of what's below.)

Tk scripts are Tcl programs.  Like all Tcl programs, Tk scripts are just lists
of tokens separated by spaces.  A Tk widget is just its *class*, the *options*
that help configure it, and the *actions* that make it do useful things.

To make a widget in Tk, the command is always of the form::

   classCommand newPathname options

*classCommand*
   denotes which kind of widget to make (a button, a label, a menu...)

*newPathname*
   is the new name for this widget.  All names in Tk must be unique.  To help
   enforce this, widgets in Tk are named with *pathnames*, just like files in a
   file system.  The top level widget, the *root*, is called ``.`` (period) and
   children are delimited by more periods.  For example,
   ``.myApp.controlPanel.okButton`` might be the name of a widget.

*options*
   configure the widget's appearance and in some cases, its behavior.  The options
   come in the form of a list of flags and values. Flags are preceded by a '-',
   like Unix shell command flags, and values are put in quotes if they are more
   than one word.

For example::

   button   .fred   -fg red -text "hi there"
      ^       ^     \_____________________/
      |       |                |
    class    new            options
   command  widget  (-opt val -opt val ...)

Once created, the pathname to the widget becomes a new command.  This new
*widget command* is the programmer's handle for getting the new widget to
perform some *action*.  In C, you'd express this as someAction(fred,
someOptions), in C++, you would express this as fred.someAction(someOptions),
and in Tk, you say::

   .fred someAction someOptions 

Note that the object name, ``.fred``, starts with a dot.

As you'd expect, the legal values for *someAction* will depend on the widget's
class: ``.fred disable`` works if fred is a button (fred gets greyed out), but
does not work if fred is a label (disabling of labels is not supported in Tk).

The legal values of *someOptions* is action dependent.  Some actions, like
``disable``, require no arguments, others, like a text-entry box's ``delete``
command, would need arguments to specify what range of text to delete.


.. _tkinter-basic-mapping:

Mapping Basic Tk into Tkinter
-----------------------------

Class commands in Tk correspond to class constructors in Tkinter. ::

   button .fred                =====>  fred = Button()

The master of an object is implicit in the new name given to it at creation
time.  In Tkinter, masters are specified explicitly. ::

   button .panel.fred          =====>  fred = Button(panel)

The configuration options in Tk are given in lists of hyphened tags followed by
values.  In Tkinter, options are specified as keyword-arguments in the instance
constructor, and keyword-args for configure calls or as instance indices, in
dictionary style, for established instances.  See section
:ref:`tkinter-setting-options` on setting options. ::

   button .fred -fg red        =====>  fred = Button(panel, fg = "red")
   .fred configure -fg red     =====>  fred["fg"] = red
                               OR ==>  fred.config(fg = "red")

In Tk, to perform an action on a widget, use the widget name as a command, and
follow it with an action name, possibly with arguments (options).  In Tkinter,
you call methods on the class instance to invoke actions on the widget.  The
actions (methods) that a given widget can perform are listed in the Tkinter.py
module. ::

   .fred invoke                =====>  fred.invoke()

To give a widget to the packer (geometry manager), you call pack with optional
arguments.  In Tkinter, the Pack class holds all this functionality, and the
various forms of the pack command are implemented as methods.  All widgets in
:mod:`Tkinter` are subclassed from the Packer, and so inherit all the packing
methods. See the :mod:`Tix` module documentation for additional information on
the Form geometry manager. ::

   pack .fred -side left       =====>  fred.pack(side = "left")


How Tk and Tkinter are Related
------------------------------

.. % Relationship.html

.. note::

   This was derived from a graphical image; the image will be used more directly in
   a subsequent version of this document.

From the top down:

Your App Here (Python)
   A Python application makes a :mod:`Tkinter` call.

Tkinter (Python Module)
   This call (say, for example, creating a button widget), is implemented in the
   *Tkinter* module, which is written in Python.  This Python function will parse
   the commands and the arguments and convert them into a form that makes them look
   as if they had come from a Tk script instead of a Python script.

tkinter (C)
   These commands and their arguments will be passed to a C function in the
   *tkinter* - note the lowercase - extension module.

Tk Widgets (C and Tcl)
   This C function is able to make calls into other C modules, including the C
   functions that make up the Tk library.  Tk is implemented in C and some Tcl.
   The Tcl part of the Tk widgets is used to bind certain default behaviors to
   widgets, and is executed once at the point where the Python :mod:`Tkinter`
   module is imported. (The user never sees this stage).

Tk (C)
   The Tk part of the Tk Widgets implement the final mapping to ...

Xlib (C)
   the Xlib library to draw graphics on the screen.


Handy Reference
---------------


.. _tkinter-setting-options:

Setting Options
^^^^^^^^^^^^^^^

Options control things like the color and border width of a widget. Options can
be set in three ways:

At object creation time, using keyword arguments
   ::

      fred = Button(self, fg = "red", bg = "blue")

After object creation, treating the option name like a dictionary index
   ::

      fred["fg"] = "red"
      fred["bg"] = "blue"

Use the config() method to update multiple attrs subsequent to object creation
   ::

      fred.config(fg = "red", bg = "blue")

For a complete explanation of a given option and its behavior, see the Tk man
pages for the widget in question.

Note that the man pages list "STANDARD OPTIONS" and "WIDGET SPECIFIC OPTIONS"
for each widget.  The former is a list of options that are common to many
widgets, the latter are the options that are idiosyncratic to that particular
widget.  The Standard Options are documented on the :manpage:`options(3)` man
page.

No distinction between standard and widget-specific options is made in this
document.  Some options don't apply to some kinds of widgets. Whether a given
widget responds to a particular option depends on the class of the widget;
buttons have a ``command`` option, labels do not.

The options supported by a given widget are listed in that widget's man page, or
can be queried at runtime by calling the :meth:`config` method without
arguments, or by calling the :meth:`keys` method on that widget.  The return
value of these calls is a dictionary whose key is the name of the option as a
string (for example, ``'relief'``) and whose values are 5-tuples.

Some options, like ``bg`` are synonyms for common options with long names
(``bg`` is shorthand for "background"). Passing the ``config()`` method the name
of a shorthand option will return a 2-tuple, not 5-tuple. The 2-tuple passed
back will contain the name of the synonym and the "real" option (such as
``('bg', 'background')``).

+-------+---------------------------------+--------------+
| Index | Meaning                         | Example      |
+=======+=================================+==============+
| 0     | option name                     | ``'relief'`` |
+-------+---------------------------------+--------------+
| 1     | option name for database lookup | ``'relief'`` |
+-------+---------------------------------+--------------+
| 2     | option class for database       | ``'Relief'`` |
|       | lookup                          |              |
+-------+---------------------------------+--------------+
| 3     | default value                   | ``'raised'`` |
+-------+---------------------------------+--------------+
| 4     | current value                   | ``'groove'`` |
+-------+---------------------------------+--------------+

Example::

   >>> print fred.config()
   {'relief' : ('relief', 'relief', 'Relief', 'raised', 'groove')}

Of course, the dictionary printed will include all the options available and
their values.  This is meant only as an example.


The Packer
^^^^^^^^^^

.. index:: single: packing (widgets)

.. % Packer.html

The packer is one of Tk's geometry-management mechanisms.    Geometry managers
are used to specify the relative positioning of the positioning of widgets
within their container - their mutual *master*.  In contrast to the more
cumbersome *placer* (which is used less commonly, and we do not cover here), the
packer takes qualitative relationship specification - *above*, *to the left of*,
*filling*, etc - and works everything out to determine the exact placement
coordinates for you.

.. % See also \citetitle[classes/ClassPacker.html]{the Packer class interface}.

The size of any *master* widget is determined by the size of the "slave widgets"
inside.  The packer is used to control where slave widgets appear inside the
master into which they are packed.  You can pack widgets into frames, and frames
into other frames, in order to achieve the kind of layout you desire.
Additionally, the arrangement is dynamically adjusted to accommodate incremental
changes to the configuration, once it is packed.

Note that widgets do not appear until they have had their geometry specified
with a geometry manager.  It's a common early mistake to leave out the geometry
specification, and then be surprised when the widget is created but nothing
appears.  A widget will appear only after it has had, for example, the packer's
:meth:`pack` method applied to it.

The pack() method can be called with keyword-option/value pairs that control
where the widget is to appear within its container, and how it is to behave when
the main application window is resized.  Here are some examples::

   fred.pack()                     # defaults to side = "top"
   fred.pack(side = "left")
   fred.pack(expand = 1)


Packer Options
^^^^^^^^^^^^^^

For more extensive information on the packer and the options that it can take,
see the man pages and page 183 of John Ousterhout's book.

anchor 
   Anchor type.  Denotes where the packer is to place each slave in its parcel.

expand
   Boolean, ``0`` or ``1``.

fill
   Legal values: ``'x'``, ``'y'``, ``'both'``, ``'none'``.

ipadx and ipady
   A distance - designating internal padding on each side of the slave widget.

padx and pady
   A distance - designating external padding on each side of the slave widget.

side
   Legal values are: ``'left'``, ``'right'``, ``'top'``, ``'bottom'``.


Coupling Widget Variables
^^^^^^^^^^^^^^^^^^^^^^^^^

The current-value setting of some widgets (like text entry widgets) can be
connected directly to application variables by using special options.  These
options are ``variable``, ``textvariable``, ``onvalue``, ``offvalue``, and
``value``.  This connection works both ways: if the variable changes for any
reason, the widget it's connected to will be updated to reflect the new value.

.. % VarCouplings.html

Unfortunately, in the current implementation of :mod:`Tkinter` it is not
possible to hand over an arbitrary Python variable to a widget through a
``variable`` or ``textvariable`` option.  The only kinds of variables for which
this works are variables that are subclassed from a class called Variable,
defined in the :mod:`Tkinter` module.

There are many useful subclasses of Variable already defined:
:class:`StringVar`, :class:`IntVar`, :class:`DoubleVar`, and
:class:`BooleanVar`.  To read the current value of such a variable, call the
:meth:`get` method on it, and to change its value you call the :meth:`set`
method.  If you follow this protocol, the widget will always track the value of
the variable, with no further intervention on your part.

For example::

   class App(Frame):
       def __init__(self, master=None):
           Frame.__init__(self, master)
           self.pack()

           self.entrythingy = Entry()
           self.entrythingy.pack()

           # here is the application variable
           self.contents = StringVar()
           # set it to some value
           self.contents.set("this is a variable")
           # tell the entry widget to watch this variable
           self.entrythingy["textvariable"] = self.contents

           # and here we get a callback when the user hits return.
           # we will have the program print out the value of the
           # application variable when the user hits return
           self.entrythingy.bind('<Key-Return>',
                                 self.print_contents)

       def print_contents(self, event):
           print "hi. contents of entry is now ---->", \
                 self.contents.get()


The Window Manager
^^^^^^^^^^^^^^^^^^

.. index:: single: window manager (widgets)

.. % WindowMgr.html

In Tk, there is a utility command, ``wm``, for interacting with the window
manager.  Options to the ``wm`` command allow you to control things like titles,
placement, icon bitmaps, and the like.  In :mod:`Tkinter`, these commands have
been implemented as methods on the :class:`Wm` class.  Toplevel widgets are
subclassed from the :class:`Wm` class, and so can call the :class:`Wm` methods
directly.

To get at the toplevel window that contains a given widget, you can often just
refer to the widget's master.  Of course if the widget has been packed inside of
a frame, the master won't represent a toplevel window.  To get at the toplevel
window that contains an arbitrary widget, you can call the :meth:`_root` method.
This method begins with an underscore to denote the fact that this function is
part of the implementation, and not an interface to Tk functionality.

.. % See also \citetitle[classes/ClassWm.html]{the Wm class interface}.

Here are some examples of typical usage::

   from Tkinter import *
   class App(Frame):
       def __init__(self, master=None):
           Frame.__init__(self, master)
           self.pack()


   # create the application
   myapp = App()

   #
   # here are method calls to the window manager class
   #
   myapp.master.title("My Do-Nothing Application")
   myapp.master.maxsize(1000, 400)

   # start the program
   myapp.mainloop()


Tk Option Data Types
^^^^^^^^^^^^^^^^^^^^

.. index:: single: Tk Option Data Types

.. % OptionTypes.html

anchor
   Legal values are points of the compass: ``"n"``, ``"ne"``, ``"e"``, ``"se"``,
   ``"s"``, ``"sw"``, ``"w"``, ``"nw"``, and also ``"center"``.

bitmap
   There are eight built-in, named bitmaps: ``'error'``, ``'gray25'``,
   ``'gray50'``, ``'hourglass'``, ``'info'``, ``'questhead'``, ``'question'``,
   ``'warning'``.  To specify an X bitmap filename, give the full path to the file,
   preceded with an ``@``, as in ``"@/usr/contrib/bitmap/gumby.bit"``.

boolean
   You can pass integers 0 or 1 or the strings ``"yes"`` or ``"no"`` .

callback
   This is any Python function that takes no arguments.  For example::

      def print_it():
              print "hi there"
      fred["command"] = print_it

color
   Colors can be given as the names of X colors in the rgb.txt file, or as strings
   representing RGB values in 4 bit: ``"#RGB"``, 8 bit: ``"#RRGGBB"``, 12 bit"
   ``"#RRRGGGBBB"``, or 16 bit ``"#RRRRGGGGBBBB"`` ranges, where R,G,B here
   represent any legal hex digit.  See page 160 of Ousterhout's book for details.

cursor
   The standard X cursor names from :file:`cursorfont.h` can be used, without the
   ``XC_`` prefix.  For example to get a hand cursor (:const:`XC_hand2`), use the
   string ``"hand2"``.  You can also specify a bitmap and mask file of your own.
   See page 179 of Ousterhout's book.

distance
   Screen distances can be specified in either pixels or absolute distances.
   Pixels are given as numbers and absolute distances as strings, with the trailing
   character denoting units: ``c`` for centimetres, ``i`` for inches, ``m`` for
   millimetres, ``p`` for printer's points.  For example, 3.5 inches is expressed
   as ``"3.5i"``.

font
   Tk uses a list font name format, such as ``{courier 10 bold}``. Font sizes with
   positive numbers are measured in points; sizes with negative numbers are
   measured in pixels.

geometry
   This is a string of the form ``widthxheight``, where width and height are
   measured in pixels for most widgets (in characters for widgets displaying text).
   For example: ``fred["geometry"] = "200x100"``.

justify
   Legal values are the strings: ``"left"``, ``"center"``, ``"right"``, and
   ``"fill"``.

region
   This is a string with four space-delimited elements, each of which is a legal
   distance (see above).  For example: ``"2 3 4 5"`` and ``"3i 2i 4.5i 2i"`` and
   ``"3c 2c 4c 10.43c"``  are all legal regions.

relief
   Determines what the border style of a widget will be.  Legal values are:
   ``"raised"``, ``"sunken"``, ``"flat"``, ``"groove"``, and ``"ridge"``.

scrollcommand
   This is almost always the :meth:`set` method of some scrollbar widget, but can
   be any widget method that takes a single argument.   Refer to the file
   :file:`Demo/tkinter/matt/canvas-with-scrollbars.py` in the Python source
   distribution for an example.

wrap:
   Must be one of: ``"none"``, ``"char"``, or ``"word"``.


Bindings and Events
^^^^^^^^^^^^^^^^^^^

.. index::
   single: bind (widgets)
   single: events (widgets)

.. % Bindings.html

The bind method from the widget command allows you to watch for certain events
and to have a callback function trigger when that event type occurs.  The form
of the bind method is::

   def bind(self, sequence, func, add=''):

where:

sequence
   is a string that denotes the target kind of event.  (See the bind man page and
   page 201 of John Ousterhout's book for details).

func
   is a Python function, taking one argument, to be invoked when the event occurs.
   An Event instance will be passed as the argument. (Functions deployed this way
   are commonly known as *callbacks*.)

add
   is optional, either ``''`` or ``'+'``.  Passing an empty string denotes that
   this binding is to replace any other bindings that this event is associated
   with.  Passing a ``'+'`` means that this function is to be added to the list
   of functions bound to this event type.

For example::

   def turnRed(self, event):
       event.widget["activeforeground"] = "red"

   self.button.bind("<Enter>", self.turnRed)

Notice how the widget field of the event is being accessed in the
:meth:`turnRed` callback.  This field contains the widget that caught the X
event.  The following table lists the other event fields you can access, and how
they are denoted in Tk, which can be useful when referring to the Tk man pages.
::

   Tk      Tkinter Event Field             Tk      Tkinter Event Field 
   --      -------------------             --      -------------------
   %f      focus                           %A      char
   %h      height                          %E      send_event
   %k      keycode                         %K      keysym
   %s      state                           %N      keysym_num
   %t      time                            %T      type
   %w      width                           %W      widget
   %x      x                               %X      x_root
   %y      y                               %Y      y_root


The index Parameter
^^^^^^^^^^^^^^^^^^^

A number of widgets require"index" parameters to be passed.  These are used to
point at a specific place in a Text widget, or to particular characters in an
Entry widget, or to particular menu items in a Menu widget.

.. % Index.html

Entry widget indexes (index, view index, etc.)
   Entry widgets have options that refer to character positions in the text being
   displayed.  You can use these :mod:`Tkinter` functions to access these special
   points in text widgets:

   AtEnd()
      refers to the last position in the text

   AtInsert()
      refers to the point where the text cursor is

   AtSelFirst()
      indicates the beginning point of the selected text

   AtSelLast()
      denotes the last point of the selected text and finally

   At(x[, y])
      refers to the character at pixel location *x*, *y* (with *y* not used in the
      case of a text entry widget, which contains a single line of text).

Text widget indexes
   The index notation for Text widgets is very rich and is best described in the Tk
   man pages.

Menu indexes (menu.invoke(), menu.entryconfig(), etc.)
   Some options and methods for menus manipulate specific menu entries. Anytime a
   menu index is needed for an option or a parameter, you may pass in:

* an integer which refers to the numeric position of the entry in the widget,
     counted from the top, starting with 0;

* the string ``'active'``, which refers to the menu position that is currently
     under the cursor;

* the string ``"last"`` which refers to the last menu item;

* An integer preceded by ``@``, as in ``@6``, where the integer is interpreted
     as a y pixel coordinate in the menu's coordinate system;

* the string ``"none"``, which indicates no menu entry at all, most often used
     with menu.activate() to deactivate all entries, and finally,

* a text string that is pattern matched against the label of the menu entry, as
     scanned from the top of the menu to the bottom.  Note that this index type is
     considered after all the others, which means that matches for menu items
     labelled ``last``, ``active``, or ``none`` may be interpreted as the above
     literals, instead.


Images
^^^^^^

Bitmap/Pixelmap images can be created through the subclasses of
:class:`Tkinter.Image`:

* :class:`BitmapImage` can be used for X11 bitmap data.

* :class:`PhotoImage` can be used for GIF and PPM/PGM color bitmaps.

Either type of image is created through either the ``file`` or the ``data``
option (other options are available as well).

The image object can then be used wherever an ``image`` option is supported by
some widget (e.g. labels, buttons, menus). In these cases, Tk will not keep a
reference to the image. When the last Python reference to the image object is
deleted, the image data is deleted as well, and Tk will display an empty box
wherever the image was used.


:mod:`Tix` --- Extension widgets for Tk
=======================================

.. module:: Tix
   :synopsis: Tk Extension Widgets for Tkinter
.. sectionauthor:: Mike Clarkson <mikeclarkson@users.sourceforge.net>


.. index:: single: Tix

The :mod:`Tix` (Tk Interface Extension) module provides an additional rich set
of widgets. Although the standard Tk library has many useful widgets, they are
far from complete. The :mod:`Tix` library provides most of the commonly needed
widgets that are missing from standard Tk: :class:`HList`, :class:`ComboBox`,
:class:`Control` (a.k.a. SpinBox) and an assortment of scrollable widgets.
:mod:`Tix` also includes many more widgets that are generally useful in a wide
range of applications: :class:`NoteBook`, :class:`FileEntry`,
:class:`PanedWindow`, etc; there are more than 40 of them.

With all these new widgets, you can introduce new interaction techniques into
applications, creating more useful and more intuitive user interfaces. You can
design your application by choosing the most appropriate widgets to match the
special needs of your application and users.


.. seealso::

   `Tix Homepage <http://tix.sourceforge.net/>`_
      The home page for :mod:`Tix`.  This includes links to additional documentation
      and downloads.

   `Tix Man Pages <http://tix.sourceforge.net/dist/current/man/>`_
      On-line version of the man pages and reference material.

   `Tix Programming Guide <http://tix.sourceforge.net/dist/current/docs/tix-book/tix.book.html>`_
      On-line version of the programmer's reference material.

   `Tix Development Applications <http://tix.sourceforge.net/Tide/>`_
      Tix applications for development of Tix and Tkinter programs. Tide applications
      work under Tk or Tkinter, and include :program:`TixInspect`, an inspector to
      remotely modify and debug Tix/Tk/Tkinter applications.


Using Tix
---------


.. class:: Tix(screenName[, baseName[, className]])

   Toplevel widget of Tix which represents mostly the main window of an
   application. It has an associated Tcl interpreter.

   Classes in the :mod:`Tix` module subclasses the classes in the :mod:`Tkinter`
   module. The former imports the latter, so to use :mod:`Tix` with Tkinter, all
   you need to do is to import one module. In general, you can just import
   :mod:`Tix`, and replace the toplevel call to :class:`Tkinter.Tk` with
   :class:`Tix.Tk`::

      import Tix
      from Tkconstants import *
      root = Tix.Tk()

To use :mod:`Tix`, you must have the :mod:`Tix` widgets installed, usually
alongside your installation of the Tk widgets. To test your installation, try
the following::

   import Tix
   root = Tix.Tk()
   root.tk.eval('package require Tix')

If this fails, you have a Tk installation problem which must be resolved before
proceeding. Use the environment variable :envvar:`TIX_LIBRARY` to point to the
installed :mod:`Tix` library directory, and make sure you have the dynamic
object library (:file:`tix8183.dll` or :file:`libtix8183.so`) in  the same
directory that contains your Tk dynamic object library (:file:`tk8183.dll` or
:file:`libtk8183.so`). The directory with the dynamic object library should also
have a file called :file:`pkgIndex.tcl` (case sensitive), which contains the
line::

   package ifneeded Tix 8.1 [list load "[file join $dir tix8183.dll]" Tix]

.. % $ <-- bow to font-lock


Tix Widgets
-----------

`Tix <http://tix.sourceforge.net/dist/current/man/html/TixCmd/TixIntro.htm>`_
introduces over 40 widget classes to the :mod:`Tkinter`  repertoire.  There is a
demo of all the :mod:`Tix` widgets in the :file:`Demo/tix` directory of the
standard distribution.

.. % The Python sample code is still being added to Python, hence commented out


Basic Widgets
^^^^^^^^^^^^^


.. class:: Balloon()

   A `Balloon
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixBalloon.htm>`_ that
   pops up over a widget to provide help.  When the user moves the cursor inside a
   widget to which a Balloon widget has been bound, a small pop-up window with a
   descriptive message will be shown on the screen.

.. % Python Demo of:
.. % \ulink{Balloon}{http://tix.sourceforge.net/dist/current/demos/samples/Balloon.tcl}


.. class:: ButtonBox()

   The `ButtonBox
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixButtonBox.htm>`_
   widget creates a box of buttons, such as is commonly used for ``Ok Cancel``.

.. % Python Demo of:
.. % \ulink{ButtonBox}{http://tix.sourceforge.net/dist/current/demos/samples/BtnBox.tcl}


.. class:: ComboBox()

   The `ComboBox
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixComboBox.htm>`_
   widget is similar to the combo box control in MS Windows. The user can select a
   choice by either typing in the entry subwdget or selecting from the listbox
   subwidget.

.. % Python Demo of:
.. % \ulink{ComboBox}{http://tix.sourceforge.net/dist/current/demos/samples/ComboBox.tcl}


.. class:: Control()

   The `Control
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixControl.htm>`_
   widget is also known as the :class:`SpinBox` widget. The user can adjust the
   value by pressing the two arrow buttons or by entering the value directly into
   the entry. The new value will be checked against the user-defined upper and
   lower limits.

.. % Python Demo of:
.. % \ulink{Control}{http://tix.sourceforge.net/dist/current/demos/samples/Control.tcl}


.. class:: LabelEntry()

   The `LabelEntry
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixLabelEntry.htm>`_
   widget packages an entry widget and a label into one mega widget. It can be used
   be used to simplify the creation of "entry-form" type of interface.

.. % Python Demo of:
.. % \ulink{LabelEntry}{http://tix.sourceforge.net/dist/current/demos/samples/LabEntry.tcl}


.. class:: LabelFrame()

   The `LabelFrame
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixLabelFrame.htm>`_
   widget packages a frame widget and a label into one mega widget.  To create
   widgets inside a LabelFrame widget, one creates the new widgets relative to the
   :attr:`frame` subwidget and manage them inside the :attr:`frame` subwidget.

.. % Python Demo of:
.. % \ulink{LabelFrame}{http://tix.sourceforge.net/dist/current/demos/samples/LabFrame.tcl}


.. class:: Meter()

   The `Meter
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixMeter.htm>`_ widget
   can be used to show the progress of a background job which may take a long time
   to execute.

.. % Python Demo of:
.. % \ulink{Meter}{http://tix.sourceforge.net/dist/current/demos/samples/Meter.tcl}


.. class:: OptionMenu()

   The `OptionMenu
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixOptionMenu.htm>`_
   creates a menu button of options.

.. % Python Demo of:
.. % \ulink{OptionMenu}{http://tix.sourceforge.net/dist/current/demos/samples/OptMenu.tcl}


.. class:: PopupMenu()

   The `PopupMenu
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixPopupMenu.htm>`_
   widget can be used as a replacement of the ``tk_popup`` command. The advantage
   of the :mod:`Tix` :class:`PopupMenu` widget is it requires less application code
   to manipulate.

.. % Python Demo of:
.. % \ulink{PopupMenu}{http://tix.sourceforge.net/dist/current/demos/samples/PopMenu.tcl}


.. class:: Select()

   The `Select
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixSelect.htm>`_ widget
   is a container of button subwidgets. It can be used to provide radio-box or
   check-box style of selection options for the user.

.. % Python Demo of:
.. % \ulink{Select}{http://tix.sourceforge.net/dist/current/demos/samples/Select.tcl}


.. class:: StdButtonBox()

   The `StdButtonBox
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixStdButtonBox.htm>`_
   widget is a group of standard buttons for Motif-like dialog boxes.

.. % Python Demo of:
.. % \ulink{StdButtonBox}{http://tix.sourceforge.net/dist/current/demos/samples/StdBBox.tcl}


File Selectors
^^^^^^^^^^^^^^


.. class:: DirList()

   The `DirList
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixDirList.htm>`_
   widget displays a list view of a directory, its previous directories and its
   sub-directories. The user can choose one of the directories displayed in the
   list or change to another directory.

.. % Python Demo of:
.. % \ulink{DirList}{http://tix.sourceforge.net/dist/current/demos/samples/DirList.tcl}


.. class:: DirTree()

   The `DirTree
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixDirTree.htm>`_
   widget displays a tree view of a directory, its previous directories and its
   sub-directories. The user can choose one of the directories displayed in the
   list or change to another directory.

.. % Python Demo of:
.. % \ulink{DirTree}{http://tix.sourceforge.net/dist/current/demos/samples/DirTree.tcl}


.. class:: DirSelectDialog()

   The `DirSelectDialog
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixDirSelectDialog.htm>`_
   widget presents the directories in the file system in a dialog window.  The user
   can use this dialog window to navigate through the file system to select the
   desired directory.

.. % Python Demo of:
.. % \ulink{DirSelectDialog}{http://tix.sourceforge.net/dist/current/demos/samples/DirDlg.tcl}


.. class:: DirSelectBox()

   The :class:`DirSelectBox` is similar to the standard Motif(TM) directory-
   selection box. It is generally used for the user to choose a directory.
   DirSelectBox stores the directories mostly recently selected into a ComboBox
   widget so that they can be quickly selected again.


.. class:: ExFileSelectBox()

   The `ExFileSelectBox
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixExFileSelectBox.htm>`_
   widget is usually embedded in a tixExFileSelectDialog widget. It provides an
   convenient method for the user to select files. The style of the
   :class:`ExFileSelectBox` widget is very similar to the standard file dialog on
   MS Windows 3.1.

.. % Python Demo of:
.. % \ulink{ExFileSelectDialog}{http://tix.sourceforge.net/dist/current/demos/samples/EFileDlg.tcl}


.. class:: FileSelectBox()

   The `FileSelectBox
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixFileSelectBox.htm>`_
   is similar to the standard Motif(TM) file-selection box. It is generally used
   for the user to choose a file. FileSelectBox stores the files mostly recently
   selected into a :class:`ComboBox` widget so that they can be quickly selected
   again.

.. % Python Demo of:
.. % \ulink{FileSelectDialog}{http://tix.sourceforge.net/dist/current/demos/samples/FileDlg.tcl}


.. class:: FileEntry()

   The `FileEntry
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixFileEntry.htm>`_
   widget can be used to input a filename. The user can type in the filename
   manually. Alternatively, the user can press the button widget that sits next to
   the entry, which will bring up a file selection dialog.

.. % Python Demo of:
.. % \ulink{FileEntry}{http://tix.sourceforge.net/dist/current/demos/samples/FileEnt.tcl}


Hierachical ListBox
^^^^^^^^^^^^^^^^^^^


.. class:: HList()

   The `HList
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixHList.htm>`_ widget
   can be used to display any data that have a hierarchical structure, for example,
   file system directory trees. The list entries are indented and connected by
   branch lines according to their places in the hierarchy.

.. % Python Demo of:
.. % \ulink{HList}{http://tix.sourceforge.net/dist/current/demos/samples/HList1.tcl}


.. class:: CheckList()

   The `CheckList
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixCheckList.htm>`_
   widget displays a list of items to be selected by the user. CheckList acts
   similarly to the Tk checkbutton or radiobutton widgets, except it is capable of
   handling many more items than checkbuttons or radiobuttons.

.. % Python Demo of:
.. % \ulink{ CheckList}{http://tix.sourceforge.net/dist/current/demos/samples/ChkList.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledHList (1)}{http://tix.sourceforge.net/dist/current/demos/samples/SHList.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledHList (2)}{http://tix.sourceforge.net/dist/current/demos/samples/SHList2.tcl}


.. class:: Tree()

   The `Tree
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixTree.htm>`_ widget
   can be used to display hierarchical data in a tree form. The user can adjust the
   view of the tree by opening or closing parts of the tree.

.. % Python Demo of:
.. % \ulink{Tree}{http://tix.sourceforge.net/dist/current/demos/samples/Tree.tcl}
.. % Python Demo of:
.. % \ulink{Tree (Dynamic)}{http://tix.sourceforge.net/dist/current/demos/samples/DynTree.tcl}


Tabular ListBox
^^^^^^^^^^^^^^^


.. class:: TList()

   The `TList
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixTList.htm>`_ widget
   can be used to display data in a tabular format. The list entries of a
   :class:`TList` widget are similar to the entries in the Tk listbox widget.  The
   main differences are (1) the :class:`TList` widget can display the list entries
   in a two dimensional format and (2) you can use graphical images as well as
   multiple colors and fonts for the list entries.

.. % Python Demo of:
.. % \ulink{ScrolledTList (1)}{http://tix.sourceforge.net/dist/current/demos/samples/STList1.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledTList (2)}{http://tix.sourceforge.net/dist/current/demos/samples/STList2.tcl}
.. % Grid has yet to be added to Python
.. % \subsubsection{Grid Widget}
.. % Python Demo of:
.. % \ulink{Simple Grid}{http://tix.sourceforge.net/dist/current/demos/samples/SGrid0.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledGrid}{http://tix.sourceforge.net/dist/current/demos/samples/SGrid1.tcl}
.. % Python Demo of:
.. % \ulink{Editable Grid}{http://tix.sourceforge.net/dist/current/demos/samples/EditGrid.tcl}


Manager Widgets
^^^^^^^^^^^^^^^


.. class:: PanedWindow()

   The `PanedWindow
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixPanedWindow.htm>`_
   widget allows the user to interactively manipulate the sizes of several panes.
   The panes can be arranged either vertically or horizontally.  The user changes
   the sizes of the panes by dragging the resize handle between two panes.

.. % Python Demo of:
.. % \ulink{PanedWindow}{http://tix.sourceforge.net/dist/current/demos/samples/PanedWin.tcl}


.. class:: ListNoteBook()

   The `ListNoteBook
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixListNoteBook.htm>`_
   widget is very similar to the :class:`TixNoteBook` widget: it can be used to
   display many windows in a limited space using a notebook metaphor. The notebook
   is divided into a stack of pages (windows). At one time only one of these pages
   can be shown. The user can navigate through these pages by choosing the name of
   the desired page in the :attr:`hlist` subwidget.

.. % Python Demo of:
.. % \ulink{ListNoteBook}{http://tix.sourceforge.net/dist/current/demos/samples/ListNBK.tcl}


.. class:: NoteBook()

   The `NoteBook
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixNoteBook.htm>`_
   widget can be used to display many windows in a limited space using a notebook
   metaphor. The notebook is divided into a stack of pages. At one time only one of
   these pages can be shown. The user can navigate through these pages by choosing
   the visual "tabs" at the top of the NoteBook widget.

.. % Python Demo of:
.. % \ulink{NoteBook}{http://tix.sourceforge.net/dist/current/demos/samples/NoteBook.tcl}

.. % \subsubsection{Scrolled Widgets}
.. % Python Demo of:
.. % \ulink{ScrolledListBox}{http://tix.sourceforge.net/dist/current/demos/samples/SListBox.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledText}{http://tix.sourceforge.net/dist/current/demos/samples/SText.tcl}
.. % Python Demo of:
.. % \ulink{ScrolledWindow}{http://tix.sourceforge.net/dist/current/demos/samples/SWindow.tcl}
.. % Python Demo of:
.. % \ulink{Canvas Object View}{http://tix.sourceforge.net/dist/current/demos/samples/CObjView.tcl}


Image Types
^^^^^^^^^^^

The :mod:`Tix` module adds:

* `pixmap <http://tix.sourceforge.net/dist/current/man/html/TixCmd/pixmap.htm>`_
  capabilities to all :mod:`Tix` and :mod:`Tkinter` widgets to create color images
  from XPM files.

  .. % Python Demo of:
  .. % \ulink{XPM Image In Button}{http://tix.sourceforge.net/dist/current/demos/samples/Xpm.tcl}
  .. % Python Demo of:
  .. % \ulink{XPM Image In Menu}{http://tix.sourceforge.net/dist/current/demos/samples/Xpm1.tcl}

* `Compound
  <http://tix.sourceforge.net/dist/current/man/html/TixCmd/compound.htm>`_ image
  types can be used to create images that consists of multiple horizontal lines;
  each line is composed of a series of items (texts, bitmaps, images or spaces)
  arranged from left to right. For example, a compound image can be used to
  display a bitmap and a text string simultaneously in a Tk :class:`Button`
  widget.

  .. % Python Demo of:
  .. % \ulink{Compound Image In Buttons}{http://tix.sourceforge.net/dist/current/demos/samples/CmpImg.tcl}
  .. % Python Demo of:
  .. % \ulink{Compound Image In NoteBook}{http://tix.sourceforge.net/dist/current/demos/samples/CmpImg2.tcl}
  .. % Python Demo of:
  .. % \ulink{Compound Image Notebook Color Tabs}{http://tix.sourceforge.net/dist/current/demos/samples/CmpImg4.tcl}
  .. % Python Demo of:
  .. % \ulink{Compound Image Icons}{http://tix.sourceforge.net/dist/current/demos/samples/CmpImg3.tcl}


Miscellaneous Widgets
^^^^^^^^^^^^^^^^^^^^^


.. class:: InputOnly()

   The `InputOnly
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixInputOnly.htm>`_
   widgets are to accept inputs from the user, which can be done with the ``bind``
   command (Unix only).


Form Geometry Manager
^^^^^^^^^^^^^^^^^^^^^

In addition, :mod:`Tix` augments :mod:`Tkinter` by providing:


.. class:: Form()

   The `Form
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tixForm.htm>`_ geometry
   manager based on attachment rules for all Tk widgets.

.. % begin{latexonly}
.. % \subsection{Tix Class Structure}
.. % 
.. % \begin{figure}[hbtp]
.. % \centerline{\epsfig{file=hierarchy.png,width=.9\textwidth}}
.. % \vspace{.5cm}
.. % \caption{The Class Hierarchy of Tix Widgets}
.. % \end{figure}
.. % end{latexonly}


Tix Commands
------------


.. class:: tixCommand()

   The `tix commands
   <http://tix.sourceforge.net/dist/current/man/html/TixCmd/tix.htm>`_ provide
   access to miscellaneous elements of :mod:`Tix`'s internal state and the
   :mod:`Tix` application context.  Most of the information manipulated by these
   methods pertains to the application as a whole, or to a screen or display,
   rather than to a particular window.

   To view the current settings, the common usage is::

      import Tix
      root = Tix.Tk()
      print root.tix_configure()


.. method:: tixCommand.tix_configure([cnf,] **kw)

   Query or modify the configuration options of the Tix application context. If no
   option is specified, returns a dictionary all of the available options.  If
   option is specified with no value, then the method returns a list describing the
   one named option (this list will be identical to the corresponding sublist of
   the value returned if no option is specified).  If one or more option-value
   pairs are specified, then the method modifies the given option(s) to have the
   given value(s); in this case the method returns an empty string. Option may be
   any of the configuration options.


.. method:: tixCommand.tix_cget(option)

   Returns the current value of the configuration option given by *option*. Option
   may be any of the configuration options.


.. method:: tixCommand.tix_getbitmap(name)

   Locates a bitmap file of the name ``name.xpm`` or ``name`` in one of the bitmap
   directories (see the :meth:`tix_addbitmapdir` method).  By using
   :meth:`tix_getbitmap`, you can avoid hard coding the pathnames of the bitmap
   files in your application. When successful, it returns the complete pathname of
   the bitmap file, prefixed with the character ``@``.  The returned value can be
   used to configure the ``bitmap`` option of the Tk and Tix widgets.


.. method:: tixCommand.tix_addbitmapdir(directory)

   Tix maintains a list of directories under which the :meth:`tix_getimage` and
   :meth:`tix_getbitmap` methods will search for image files.  The standard bitmap
   directory is :file:`$TIX_LIBRARY/bitmaps`. The :meth:`tix_addbitmapdir` method
   adds *directory* into this list. By using this method, the image files of an
   applications can also be located using the :meth:`tix_getimage` or
   :meth:`tix_getbitmap` method.


.. method:: tixCommand.tix_filedialog([dlgclass])

   Returns the file selection dialog that may be shared among different calls from
   this application.  This method will create a file selection dialog widget when
   it is called the first time. This dialog will be returned by all subsequent
   calls to :meth:`tix_filedialog`.  An optional dlgclass parameter can be passed
   as a string to specified what type of file selection dialog widget is desired.
   Possible options are ``tix``, ``FileSelectDialog`` or ``tixExFileSelectDialog``.


.. method:: tixCommand.tix_getimage(self, name)

   Locates an image file of the name :file:`name.xpm`, :file:`name.xbm` or
   :file:`name.ppm` in one of the bitmap directories (see the
   :meth:`tix_addbitmapdir` method above). If more than one file with the same name
   (but different extensions) exist, then the image type is chosen according to the
   depth of the X display: xbm images are chosen on monochrome displays and color
   images are chosen on color displays. By using :meth:`tix_getimage`, you can
   avoid hard coding the pathnames of the image files in your application. When
   successful, this method returns the name of the newly created image, which can
   be used to configure the ``image`` option of the Tk and Tix widgets.


.. method:: tixCommand.tix_option_get(name)

   Gets the options maintained by the Tix scheme mechanism.


.. method:: tixCommand.tix_resetoptions(newScheme, newFontSet[, newScmPrio])

   Resets the scheme and fontset of the Tix application to *newScheme* and
   *newFontSet*, respectively.  This affects only those widgets created after this
   call.  Therefore, it is best to call the resetoptions method before the creation
   of any widgets in a Tix application.

   The optional parameter *newScmPrio* can be given to reset the priority level of
   the Tk options set by the Tix schemes.

   Because of the way Tk handles the X option database, after Tix has been has
   imported and inited, it is not possible to reset the color schemes and font sets
   using the :meth:`tix_config` method. Instead, the :meth:`tix_resetoptions`
   method must be used.


:mod:`ScrolledText` --- Scrolled Text Widget
============================================

.. module:: ScrolledText
   :platform: Tk
   :synopsis: Text widget with a vertical scroll bar.
.. sectionauthor:: Fred L. Drake, Jr. <fdrake@acm.org>


The :mod:`ScrolledText` module provides a class of the same name which
implements a basic text widget which has a vertical scroll bar configured to do
the "right thing."  Using the :class:`ScrolledText` class is a lot easier than
setting up a text widget and scroll bar directly.  The constructor is the same
as that of the :class:`Tkinter.Text` class.

The text widget and scrollbar are packed together in a :class:`Frame`, and the
methods of the :class:`Grid` and :class:`Pack` geometry managers are acquired
from the :class:`Frame` object.  This allows the :class:`ScrolledText` widget to
be used directly to achieve most normal geometry management behavior.

Should more specific control be necessary, the following attributes are
available:


.. attribute:: ScrolledText.frame

   The frame which surrounds the text and scroll bar widgets.


.. attribute:: ScrolledText.vbar

   The scroll bar widget.

XXX: input{libturtle} :XXX

.. _idle:

Idle
====

.. moduleauthor:: Guido van Rossum <guido@Python.org>


.. % \declaremodule{standard}{idle}
.. % \modulesynopsis{A Python Integrated Development Environment}

.. index::
   single: Idle
   single: Python Editor
   single: Integrated Development Environment

Idle is the Python IDE built with the :mod:`Tkinter` GUI toolkit.

IDLE has the following features:

* coded in 100% pure Python, using the :mod:`Tkinter` GUI toolkit

* cross-platform: works on Windows and Unix (on Mac OS, there are currently
  problems with Tcl/Tk)

* multi-window text editor with multiple undo, Python colorizing and many other
  features, e.g. smart indent and call tips

* Python shell window (a.k.a. interactive interpreter)

* debugger (not complete, but you can set breakpoints, view  and step)


Menus
-----


File menu
^^^^^^^^^

New window
   create a new editing window

Open...
   open an existing file

Open module...
   open an existing module (searches sys.path)

Class browser
   show classes and methods in current file

Path browser
   show sys.path directories, modules, classes and methods

.. index::
   single: Class browser
   single: Path browser

Save
   save current window to the associated file (unsaved windows have a \* before and
   after the window title)

Save As...
   save current window to new file, which becomes the associated file

Save Copy As...
   save current window to different file without changing the associated file

Close
   close current window (asks to save if unsaved)

Exit
   close all windows and quit IDLE (asks to save if unsaved)


Edit menu
^^^^^^^^^

Undo
   Undo last change to current window (max 1000 changes)

Redo
   Redo last undone change to current window

Cut
   Copy selection into system-wide clipboard; then delete selection

Copy
   Copy selection into system-wide clipboard

Paste
   Insert system-wide clipboard into window

Select All
   Select the entire contents of the edit buffer

Find...
   Open a search dialog box with many options

Find again
   Repeat last search

Find selection
   Search for the string in the selection

Find in Files...
   Open a search dialog box for searching files

Replace...
   Open a search-and-replace dialog box

Go to line
   Ask for a line number and show that line

Indent region
   Shift selected lines right 4 spaces

Dedent region
   Shift selected lines left 4 spaces

Comment out region
   Insert ## in front of selected lines

Uncomment region
   Remove leading # or ## from selected lines

Tabify region
   Turns *leading* stretches of spaces into tabs

Untabify region
   Turn *all* tabs into the right number of spaces

Expand word
   Expand the word you have typed to match another word in the same buffer; repeat
   to get a different expansion

Format Paragraph
   Reformat the current blank-line-separated paragraph

Import module
   Import or reload the current module

Run script
   Execute the current file in the __main__ namespace

.. index::
   single: Import module
   single: Run script


Windows menu
^^^^^^^^^^^^

Zoom Height
   toggles the window between normal size (24x80) and maximum height.

The rest of this menu lists the names of all open windows; select one to bring
it to the foreground (deiconifying it if necessary).


Debug menu (in the Python Shell window only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Go to file/line
   look around the insert point for a filename and linenumber, open the file, and
   show the line.

Open stack viewer
   show the stack traceback of the last exception

Debugger toggle
   Run commands in the shell under the debugger

JIT Stack viewer toggle
   Open stack viewer on traceback

.. index::
   single: stack viewer
   single: debugger


Basic editing and navigation
----------------------------

* :kbd:`Backspace` deletes to the left; :kbd:`Del` deletes to the right

* Arrow keys and :kbd:`Page Up`/:kbd:`Page Down` to move around

* :kbd:`Home`/:kbd:`End` go to begin/end of line

* :kbd:`C-Home`/:kbd:`C-End` go to begin/end of file

* Some :program:`Emacs` bindings may also work, including :kbd:`C-B`,
  :kbd:`C-P`, :kbd:`C-A`, :kbd:`C-E`, :kbd:`C-D`, :kbd:`C-L`


Automatic indentation
^^^^^^^^^^^^^^^^^^^^^

After a block-opening statement, the next line is indented by 4 spaces (in the
Python Shell window by one tab).  After certain keywords (break, return etc.)
the next line is dedented.  In leading indentation, :kbd:`Backspace` deletes up
to 4 spaces if they are there. :kbd:`Tab` inserts 1-4 spaces (in the Python
Shell window one tab). See also the indent/dedent region commands in the edit
menu.


Python Shell window
^^^^^^^^^^^^^^^^^^^

* :kbd:`C-C` interrupts executing command

* :kbd:`C-D` sends end-of-file; closes window if typed at a ``>>>`` prompt

* :kbd:`Alt-p` retrieves previous command matching what you have typed

* :kbd:`Alt-n` retrieves next

* :kbd:`Return` while on any previous command retrieves that command

* :kbd:`Alt-/` (Expand word) is also useful here

.. index:: single: indentation


Syntax colors
-------------

The coloring is applied in a background "thread," so you may occasionally see
uncolorized text.  To change the color scheme, edit the ``[Colors]`` section in
:file:`config.txt`.

Python syntax colors:
   Keywords
      orange

   Strings 
      green

   Comments
      red

   Definitions
      blue

Shell colors:
   Console output
      brown

   stdout
      blue

   stderr
      dark green

   stdin
      black


Command line usage
^^^^^^^^^^^^^^^^^^

::

   idle.py [-c command] [-d] [-e] [-s] [-t title] [arg] ...

   -c command  run this command
   -d          enable debugger
   -e          edit mode; arguments are files to be edited
   -s          run $IDLESTARTUP or $PYTHONSTARTUP first
   -t title    set title of shell window

If there are arguments:

#. If :option:`-e` is used, arguments are files opened for editing and
   ``sys.argv`` reflects the arguments passed to IDLE itself.

#. Otherwise, if :option:`-c` is used, all arguments are placed in
   ``sys.argv[1:...]``, with ``sys.argv[0]`` set to ``'-c'``.

#. Otherwise, if neither :option:`-e` nor :option:`-c` is used, the first
   argument is a script which is executed with the remaining arguments in
   ``sys.argv[1:...]``  and ``sys.argv[0]`` set to the script name.  If the script
   name is '-', no script is executed but an interactive Python session is started;
   the arguments are still available in ``sys.argv``.


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

