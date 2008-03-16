.. highlight:: rest

Module-specific markup
----------------------

The markup described in this section is used to provide information about a
module being documented.  Each module should be documented in its own file.
Normally this markup appears after the title heading of that file; a typical
file might start like this::

   :mod:`parrot` -- Dead parrot access
   ===================================

   .. module:: parrot
      :platform: Unix, Windows
      :synopsis: Analyze and reanimate dead parrots.
   .. moduleauthor:: Eric Cleese <eric@python.invalid>
   .. moduleauthor:: John Idle <john@python.invalid>

As you can see, the module-specific markup consists of two directives, the
``module`` directive and the ``moduleauthor`` directive.

.. directive:: .. module:: name

   This directive marks the beginning of the description of a module (or package
   submodule, in which case the name should be fully qualified, including the
   package name).

   The ``platform`` option, if present, is a comma-separated list of the
   platforms on which the module is available (if it is available on all
   platforms, the option should be omitted).  The keys are short identifiers;
   examples that are in use include "IRIX", "Mac", "Windows", and "Unix".  It is
   important to use a key which has already been used when applicable.

   The ``synopsis`` option should consist of one sentence describing the
   module's purpose -- it is currently only used in the Global Module Index.

   The ``deprecated`` option can be given (with no value) to mark a module as
   deprecated; it will be designated as such in various locations then.

.. directive:: .. moduleauthor:: name <email>

   The ``moduleauthor`` directive, which can appear multiple times, names the
   authors of the module code, just like ``sectionauthor`` names the author(s)
   of a piece of documentation.  It too only produces output if the
   :confval:`show_authors` configuration value is True.


.. note::

   It is important to make the section title of a module-describing file
   meaningful since that value will be inserted in the table-of-contents trees
   in overview files.


Description units
-----------------

There are a number of directives used to describe specific features provided by
modules.  Each directive requires one or more signatures to provide basic
information about what is being described, and the content should be the
description.  The basic version makes entries in the general index; if no index
entry is desired, you can give the directive option flag ``:noindex:``.  The
following example shows all of the features of this directive type::

    .. function:: spam(eggs)
                  ham(eggs)
       :noindex:

       Spam or ham the foo.

The signatures of object methods or data attributes should always include the
type name (``.. method:: FileInput.input(...)``), even if it is obvious from the
context which type they belong to; this is to enable consistent
cross-references.  If you describe methods belonging to an abstract protocol,
such as "context managers", include a (pseudo-)type name too to make the
index entries more informative.

The directives are:

.. directive:: .. cfunction:: type name(signature)

   Describes a C function. The signature should be given as in C, e.g.::

      .. cfunction:: PyObject* PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)

   This is also used to describe function-like preprocessor macros.  The names
   of the arguments should be given so they may be used in the description.

   Note that you don't have to backslash-escape asterisks in the signature,
   as it is not parsed by the reST inliner.

.. directive:: .. cmember:: type name

   Describes a C struct member. Example signature::

      .. cmember:: PyObject* PyTypeObject.tp_bases

   The text of the description should include the range of values allowed, how
   the value should be interpreted, and whether the value can be changed.
   References to structure members in text should use the ``member`` role.

.. directive:: .. cmacro:: name

   Describes a "simple" C macro.  Simple macros are macros which are used
   for code expansion, but which do not take arguments so cannot be described as
   functions.  This is not to be used for simple constant definitions.  Examples
   of its use in the Python documentation include :cmacro:`PyObject_HEAD` and
   :cmacro:`Py_BEGIN_ALLOW_THREADS`.

.. directive:: .. ctype:: name

   Describes a C type. The signature should just be the type name.

.. directive:: .. cvar:: type name

   Describes a global C variable.  The signature should include the type, such
   as::

      .. cvar:: PyObject* PyClass_Type

.. directive:: .. data:: name

   Describes global data in a module, including both variables and values used
   as "defined constants."  Class and object attributes are not documented
   using this environment.

.. directive:: .. exception:: name

   Describes an exception class.  The signature can, but need not include
   parentheses with constructor arguments.

.. directive:: .. function:: name(signature)

   Describes a module-level function.  The signature should include the
   parameters, enclosing optional parameters in brackets.  Default values can be
   given if it enhances clarity.  For example::

      .. function:: Timer.repeat([repeat=3[, number=1000000]])

   Object methods are not documented using this directive. Bound object methods
   placed in the module namespace as part of the public interface of the module
   are documented using this, as they are equivalent to normal functions for
   most purposes.

   The description should include information about the parameters required and
   how they are used (especially whether mutable objects passed as parameters
   are modified), side effects, and possible exceptions.  A small example may be
   provided.

.. directive:: .. class:: name[(signature)]

   Describes a class.  The signature can include parentheses with parameters
   which will be shown as the constructor arguments.

.. directive:: .. attribute:: name

   Describes an object data attribute.  The description should include
   information about the type of the data to be expected and whether it may be
   changed directly.

.. directive:: .. method:: name(signature)

   Describes an object method.  The parameters should not include the ``self``
   parameter.  The description should include similar information to that
   described for ``function``.

.. directive:: .. opcode:: name

   Describes a Python bytecode instruction (this is not very useful for projects
   other than Python itself).

.. directive:: .. cmdoption:: name args

   Describes a command line option or switch.  Option argument names should be
   enclosed in angle brackets.  Example::

      .. cmdoption:: -m <module>

         Run a module as a script.

.. directive:: .. envvar:: name

   Describes an environment variable that the documented code uses or defines.


There is also a generic version of these directives:

.. directive:: .. describe:: text

   This directive produces the same formatting as the specific ones explained
   above but does not create index entries or cross-referencing targets.  It is
   used, for example, to describe the directives in this document. Example::

      .. describe:: opcode

         Describes a Python bytecode instruction.
