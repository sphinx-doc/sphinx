.. highlight:: rest

Module-specific markup
----------------------

The markup described in this section is used to provide information about a
module being documented.  Normally this markup appears after a title heading; a
typical module section might start like this::

   :mod:`parrot` -- Dead parrot access
   ===================================

   .. module:: parrot
      :platform: Unix, Windows
      :synopsis: Analyze and reanimate dead parrots.
   .. moduleauthor:: Eric Cleese <eric@python.invalid>
   .. moduleauthor:: John Idle <john@python.invalid>


The directives you can use for module declarations are:

.. directive:: .. module:: name

   This directive marks the beginning of the description of a module (or package
   submodule, in which case the name should be fully qualified, including the
   package name).  It does not create content (like e.g. :dir:`class` does).

   This directive will also cause an entry in the global module index.

   The ``platform`` option, if present, is a comma-separated list of the
   platforms on which the module is available (if it is available on all
   platforms, the option should be omitted).  The keys are short identifiers;
   examples that are in use include "IRIX", "Mac", "Windows", and "Unix".  It is
   important to use a key which has already been used when applicable.

   The ``synopsis`` option should consist of one sentence describing the
   module's purpose -- it is currently only used in the Global Module Index.

   The ``deprecated`` option can be given (with no value) to mark a module as
   deprecated; it will be designated as such in various locations then.


.. directive:: .. currentmodule:: name

   This directive tells Sphinx that the classes, functions etc. documented from
   here are in the given module (like :dir:`module`), but it will not create
   index entries, an entry in the Global Module Index, or a link target for
   :role:`mod`.  This is helpful in situations where documentation for things in
   a module is spread over multiple files or sections -- one location has the
   :dir:`module` directive, the others only :dir:`currentmodule`.


.. directive:: .. moduleauthor:: name <email>

   The ``moduleauthor`` directive, which can appear multiple times, names the
   authors of the module code, just like ``sectionauthor`` names the author(s)
   of a piece of documentation.  It too only produces output if the
   :confval:`show_authors` configuration value is True.


.. note::

   It is important to make the section title of a module-describing file
   meaningful since that value will be inserted in the table-of-contents trees
   in overview files.


.. _desc-units:

Object description units
------------------------

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
   given if it enhances clarity; see :ref:`signatures`.  For example::

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
   which will be shown as the constructor arguments.  See also
   :ref:`signatures`.

   Methods and attributes belonging to the class should be placed in this
   directive's body.  If they are placed outside, the supplied name should
   contain the class name so that cross-references still work.  Example::

      .. class:: Foo
         .. method:: quux()

      -- or --

      .. class:: Bar

      .. method:: Bar.quux()

   The first way is the preferred one.

   .. versionadded:: 0.4
      The standard reST directive ``class`` is now provided by Sphinx under
      the name ``cssclass``.

.. directive:: .. attribute:: name

   Describes an object data attribute.  The description should include
   information about the type of the data to be expected and whether it may be
   changed directly.

.. directive:: .. method:: name(signature)

   Describes an object method.  The parameters should not include the ``self``
   parameter.  The description should include similar information to that
   described for ``function``.  See also :ref:`signatures`.

.. directive:: .. staticmethod:: name(signature)

   Like :dir:`method`, but indicates that the method is a static method.

   .. versionadded:: 0.4

.. directive:: .. classmethod:: name(signature)

   Like :dir:`method`, but indicates that the method is a class method.

   .. versionadded:: 0.6


.. _signatures:

Signatures
~~~~~~~~~~

Signatures of functions, methods and class constructors can be given like they
would be written in Python, with the exception that optional parameters can be
indicated by brackets::

   .. function:: compile(source[, filename[, symbol]])

It is customary to put the opening bracket before the comma.  In addition to
this "nested" bracket style, a "flat" style can also be used, due to the fact
that most optional parameters can be given independently::

   .. function:: compile(source[, filename, symbol])

Default values for optional arguments can be given (but if they contain commas,
they will confuse the signature parser).  Python 3-style argument annotations
can also be given as well as return type annotations::

   .. function:: compile(source : string[, filename, symbol]) -> ast object


Info field lists
~~~~~~~~~~~~~~~~

.. versionadded:: 0.4

Inside description unit directives, reST field lists with these fields are
recognized and formatted nicely:

* ``param``, ``parameter``, ``arg``, ``argument``, ``key``, ``keyword``:
  Description of a parameter.
* ``type``: Type of a parameter.
* ``raises``, ``raise``, ``except``, ``exception``: That (and when) a specific
  exception is raised.
* ``var``, ``ivar``, ``cvar``: Description of a variable.
* ``returns``, ``return``: Description of the return value.
* ``rtype``: Return type.

The field names must consist of one of these keywords and an argument (except
for ``returns`` and ``rtype``, which do not need an argument).  This is best
explained by an example::

   .. function:: format_exception(etype, value, tb[, limit=None])

      Format the exception with a traceback.

      :param etype: exception type
      :param value: exception value
      :param tb: traceback object
      :param limit: maximum number of stack frames to show
      :type limit: integer or None
      :rtype: list of strings

This will render like this:

   .. function:: format_exception(etype, value, tb[, limit=None])
      :noindex:

      Format the exception with a traceback.

      :param etype: exception type
      :param value: exception value
      :param tb: traceback object
      :param limit: maximum number of stack frames to show
      :type limit: integer or None
      :rtype: list of strings


Command-line program markup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a set of directives allowing documenting command-line programs:

.. directive:: .. cmdoption:: name args, name args, ...

   Describes a command line option or switch.  Option argument names should be
   enclosed in angle brackets.  Example::

      .. cmdoption:: -m <module>, --module <module>

         Run a module as a script.

   The directive will create a cross-reference target named after the *first*
   option, referencable by :role:`option` (in the example case, you'd use
   something like ``:option:`-m```).

.. directive:: .. envvar:: name

   Describes an environment variable that the documented code or program uses or
   defines.


.. directive:: .. program:: name

   Like :dir:`currentmodule`, this directive produces no output.  Instead, it
   serves to notify Sphinx that all following :dir:`cmdoption` directives
   document options for the program called *name*.

   If you use :dir:`program`, you have to qualify the references in your
   :role:`option` roles by the program name, so if you have the following
   situation ::

      .. program:: rm

      .. cmdoption:: -r

         Work recursively.

      .. program:: svn

      .. cmdoption:: -r revision

         Specify the revision to work upon.

   then ``:option:`rm -r``` would refer to the first option, while
   ``:option:`svn -r``` would refer to the second one.

   The program name may contain spaces (in case you want to document subcommands
   like ``svn add`` and ``svn commit`` separately).

   .. versionadded:: 0.5


Custom description units
~~~~~~~~~~~~~~~~~~~~~~~~

There is also a generic version of these directives:

.. directive:: .. describe:: text

   This directive produces the same formatting as the specific ones explained
   above but does not create index entries or cross-referencing targets.  It is
   used, for example, to describe the directives in this document. Example::

      .. describe:: opcode

         Describes a Python bytecode instruction.

Extensions may add more directives like that, using the
:func:`~sphinx.application.Sphinx.add_description_unit` method.
