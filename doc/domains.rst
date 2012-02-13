.. highlight:: rst

.. _domains:

Sphinx Domains
==============

.. versionadded:: 1.0

What is a Domain?
-----------------

Originally, Sphinx was conceived for a single project, the documentation of the
Python language.  Shortly afterwards, it was made available for everyone as a
documentation tool, but the documentation of Python modules remained deeply
built in -- the most fundamental directives, like ``function``, were designed
for Python objects.  Since Sphinx has become somewhat popular, interest
developed in using it for many different purposes: C/C++ projects, JavaScript,
or even reStructuredText markup (like in this documentation).

While this was always possible, it is now much easier to easily support
documentation of projects using different programming languages or even ones not
supported by the main Sphinx distribution, by providing a **domain** for every
such purpose.

A domain is a collection of markup (reStructuredText :term:`directive`\ s and
:term:`role`\ s) to describe and link to :term:`object`\ s belonging together,
e.g. elements of a programming language.  Directive and role names in a domain
have names like ``domain:name``, e.g. ``py:function``.  Domains can also provide
custom indices (like the Python Module Index).

Having domains means that there are no naming problems when one set of
documentation wants to refer to e.g. C++ and Python classes.  It also means that
extensions that support the documentation of whole new languages are much easier
to write.

This section describes what the domains that come with Sphinx provide.  The
domain API is documented as well, in the section :ref:`domain-api`.


.. _basic-domain-markup:

Basic Markup
------------

Most domains provide a number of :dfn:`object description directives`, used to
describe specific objects provided by modules.  Each directive requires one or
more signatures to provide basic information about what is being described, and
the content should be the description.  The basic version makes entries in the
general index; if no index entry is desired, you can give the directive option
flag ``:noindex:``.  An example using a Python domain directive::

   .. py:function:: spam(eggs)
                    ham(eggs)

      Spam or ham the foo.

This describes the two Python functions ``spam`` and ``ham``.  (Note that when
signatures become too long, you can break them if you add a backslash to lines
that are continued in the next line.  Example::

   .. py:function:: filterwarnings(action, message='', category=Warning, \
                                   module='', lineno=0, append=False)
      :noindex:

(This example also shows how to use the ``:noindex:`` flag.)

The domains also provide roles that link back to these object descriptions.  For
example, to link to one of the functions described in the example above, you
could say ::

   The function :py:func:`spam` does a similar thing.

As you can see, both directive and role names contain the domain name and the
directive name.

.. rubric:: Default Domain

To avoid having to writing the domain name all the time when you e.g. only
describe Python objects, a default domain can be selected with either the config
value :confval:`primary_domain` or this directive:

.. rst:directive:: .. default-domain:: name

   Select a new default domain.  While the :confval:`primary_domain` selects a
   global default, this only has an effect within the same file.

If no other default is selected, the Python domain (named ``py``) is the default
one, mostly for compatibility with documentation written for older versions of
Sphinx.

Directives and roles that belong to the default domain can be mentioned without
giving the domain name, i.e. ::

   .. function:: pyfunc()

      Describes a Python function.

   Reference to :func:`pyfunc`.


Cross-referencing syntax
~~~~~~~~~~~~~~~~~~~~~~~~

For cross-reference roles provided by domains, the same facilities exist as for
general cross-references.  See :ref:`xref-syntax`.

In short:

* You may supply an explicit title and reference target: ``:role:`title
  <target>``` will refer to *target*, but the link text will be *title*.

* If you prefix the content with ``!``, no reference/hyperlink will be created.

* If you prefix the content with ``~``, the link text will only be the last
  component of the target.  For example, ``:py:meth:`~Queue.Queue.get``` will
  refer to ``Queue.Queue.get`` but only display ``get`` as the link text.


The Python Domain
-----------------

The Python domain (name **py**) provides the following directives for module
declarations:

.. rst:directive:: .. py:module:: name

   This directive marks the beginning of the description of a module (or package
   submodule, in which case the name should be fully qualified, including the
   package name).  It does not create content (like e.g. :rst:dir:`py:class` does).

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


.. rst:directive:: .. py:currentmodule:: name

   This directive tells Sphinx that the classes, functions etc. documented from
   here are in the given module (like :rst:dir:`py:module`), but it will not
   create index entries, an entry in the Global Module Index, or a link target
   for :rst:role:`py:mod`.  This is helpful in situations where documentation
   for things in a module is spread over multiple files or sections -- one
   location has the :rst:dir:`py:module` directive, the others only
   :rst:dir:`py:currentmodule`.


The following directives are provided for module and class contents:

.. rst:directive:: .. py:data:: name

   Describes global data in a module, including both variables and values used
   as "defined constants."  Class and object attributes are not documented
   using this environment.

.. rst:directive:: .. py:exception:: name

   Describes an exception class.  The signature can, but need not include
   parentheses with constructor arguments.

.. rst:directive:: .. py:function:: name(signature)

   Describes a module-level function.  The signature should include the
   parameters, enclosing optional parameters in brackets.  Default values can be
   given if it enhances clarity; see :ref:`signatures`.  For example::

      .. py:function:: Timer.repeat([repeat=3[, number=1000000]])

   Object methods are not documented using this directive. Bound object methods
   placed in the module namespace as part of the public interface of the module
   are documented using this, as they are equivalent to normal functions for
   most purposes.

   The description should include information about the parameters required and
   how they are used (especially whether mutable objects passed as parameters
   are modified), side effects, and possible exceptions.  A small example may be
   provided.

.. rst:directive:: .. py:class:: name[(signature)]

   Describes a class.  The signature can include parentheses with parameters
   which will be shown as the constructor arguments.  See also
   :ref:`signatures`.

   Methods and attributes belonging to the class should be placed in this
   directive's body.  If they are placed outside, the supplied name should
   contain the class name so that cross-references still work.  Example::

      .. py:class:: Foo
         .. py:method:: quux()

      -- or --

      .. py:class:: Bar

      .. py:method:: Bar.quux()

   The first way is the preferred one.

.. rst:directive:: .. py:attribute:: name

   Describes an object data attribute.  The description should include
   information about the type of the data to be expected and whether it may be
   changed directly.

.. rst:directive:: .. py:method:: name(signature)

   Describes an object method.  The parameters should not include the ``self``
   parameter.  The description should include similar information to that
   described for ``function``.  See also :ref:`signatures`.

.. rst:directive:: .. py:staticmethod:: name(signature)

   Like :rst:dir:`py:method`, but indicates that the method is a static method.

   .. versionadded:: 0.4

.. rst:directive:: .. py:classmethod:: name(signature)

   Like :rst:dir:`py:method`, but indicates that the method is a class method.

   .. versionadded:: 0.6

.. rst:directive:: .. py:decorator:: name
                   .. py:decorator:: name(signature)

   Describes a decorator function.  The signature should *not* represent the
   signature of the actual function, but the usage as a decorator.  For example,
   given the functions

   .. code-block:: python

      def removename(func):
          func.__name__ = ''
          return func

      def setnewname(name):
          def decorator(func):
              func.__name__ = name
              return func
          return decorator

   the descriptions should look like this::

      .. py:decorator:: removename

         Remove name of the decorated function.

      .. py:decorator:: setnewname(name)

         Set name of the decorated function to *name*.

   There is no ``py:deco`` role to link to a decorator that is marked up with
   this directive; rather, use the :rst:role:`py:func` role.

.. rst:directive:: .. py:decoratormethod:: name
                   .. py:decoratormethod:: name(signature)

   Same as :rst:dir:`py:decorator`, but for decorators that are methods.

   Refer to a decorator method using the :rst:role:`py:meth` role.


.. _signatures:

Python Signatures
~~~~~~~~~~~~~~~~~

Signatures of functions, methods and class constructors can be given like they
would be written in Python, with the exception that optional parameters can be
indicated by brackets::

   .. py:function:: compile(source[, filename[, symbol]])

It is customary to put the opening bracket before the comma.  In addition to
this "nested" bracket style, a "flat" style can also be used, due to the fact
that most optional parameters can be given independently::

   .. py:function:: compile(source[, filename, symbol])

Default values for optional arguments can be given (but if they contain commas,
they will confuse the signature parser).  Python 3-style argument annotations
can also be given as well as return type annotations::

   .. py:function:: compile(source : string[, filename, symbol]) -> ast object


Info field lists
~~~~~~~~~~~~~~~~

.. versionadded:: 0.4

Inside Python object description directives, reST field lists with these fields
are recognized and formatted nicely:

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

   .. py:function:: format_exception(etype, value, tb[, limit=None])

      Format the exception with a traceback.

      :param etype: exception type
      :param value: exception value
      :param tb: traceback object
      :param limit: maximum number of stack frames to show
      :type limit: integer or None
      :rtype: list of strings

This will render like this:

   .. py:function:: format_exception(etype, value, tb[, limit=None])
      :noindex:

      Format the exception with a traceback.

      :param etype: exception type
      :param value: exception value
      :param tb: traceback object
      :param limit: maximum number of stack frames to show
      :type limit: integer or None
      :rtype: list of strings

It is also possible to combine parameter type and description, if the type is a
single word, like this::

   :param integer limit: maximum number of stack frames to show


.. _python-roles:

Cross-referencing Python objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following roles refer to objects in modules and are possibly hyperlinked if
a matching identifier is found:

.. rst:role:: py:mod

   Reference a module; a dotted name may be used.  This should also be used for
   package names.

.. rst:role:: py:func

   Reference a Python function; dotted names may be used.  The role text needs
   not include trailing parentheses to enhance readability; they will be added
   automatically by Sphinx if the :confval:`add_function_parentheses` config
   value is true (the default).

.. rst:role:: py:data

   Reference a module-level variable.

.. rst:role:: py:const

   Reference a "defined" constant.  This may be a C-language ``#define`` or a
   Python variable that is not intended to be changed.

.. rst:role:: py:class

   Reference a class; a dotted name may be used.

.. rst:role:: py:meth

   Reference a method of an object.  The role text can include the type name and
   the method name; if it occurs within the description of a type, the type name
   can be omitted.  A dotted name may be used.

.. rst:role:: py:attr

   Reference a data attribute of an object.

.. rst:role:: py:exc

   Reference an exception.  A dotted name may be used.

.. rst:role:: py:obj

   Reference an object of unspecified type.  Useful e.g. as the
   :confval:`default_role`.

   .. versionadded:: 0.4

The name enclosed in this markup can include a module name and/or a class name.
For example, ``:py:func:`filter``` could refer to a function named ``filter`` in
the current module, or the built-in function of that name.  In contrast,
``:py:func:`foo.filter``` clearly refers to the ``filter`` function in the
``foo`` module.

Normally, names in these roles are searched first without any further
qualification, then with the current module name prepended, then with the
current module and class name (if any) prepended.  If you prefix the name with a
dot, this order is reversed.  For example, in the documentation of Python's
:mod:`codecs` module, ``:py:func:`open``` always refers to the built-in
function, while ``:py:func:`.open``` refers to :func:`codecs.open`.

A similar heuristic is used to determine whether the name is an attribute of the
currently documented class.

Also, if the name is prefixed with a dot, and no exact match is found, the
target is taken as a suffix and all object names with that suffix are
searched.  For example, ``:py:meth:`.TarFile.close``` references the
``tarfile.TarFile.close()`` function, even if the current module is not
``tarfile``.  Since this can get ambiguous, if there is more than one possible
match, you will get a warning from Sphinx.

Note that you can combine the ``~`` and ``.`` prefixes:
``:py:meth:`~.TarFile.close``` will reference the ``tarfile.TarFile.close()``
method, but the visible link caption will only be ``close()``.


.. _c-domain:

The C Domain
------------

The C domain (name **c**) is suited for documentation of C API.

.. rst:directive:: .. c:function:: type name(signature)

   Describes a C function. The signature should be given as in C, e.g.::

      .. c:function:: PyObject* PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)

   This is also used to describe function-like preprocessor macros.  The names
   of the arguments should be given so they may be used in the description.

   Note that you don't have to backslash-escape asterisks in the signature, as
   it is not parsed by the reST inliner.

.. rst:directive:: .. c:member:: type name

   Describes a C struct member. Example signature::

      .. c:member:: PyObject* PyTypeObject.tp_bases

   The text of the description should include the range of values allowed, how
   the value should be interpreted, and whether the value can be changed.
   References to structure members in text should use the ``member`` role.

.. rst:directive:: .. c:macro:: name

   Describes a "simple" C macro.  Simple macros are macros which are used for
   code expansion, but which do not take arguments so cannot be described as
   functions.  This is not to be used for simple constant definitions.  Examples
   of its use in the Python documentation include :c:macro:`PyObject_HEAD` and
   :c:macro:`Py_BEGIN_ALLOW_THREADS`.

.. rst:directive:: .. c:type:: name

   Describes a C type (whether defined by a typedef or struct). The signature
   should just be the type name.

.. rst:directive:: .. c:var:: type name

   Describes a global C variable.  The signature should include the type, such
   as::

      .. c:var:: PyObject* PyClass_Type


.. _c-roles:

Cross-referencing C constructs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following roles create cross-references to C-language constructs if they are
defined in the documentation:

.. rst:role:: c:data

   Reference a C-language variable.

.. rst:role:: c:func

   Reference a C-language function. Should include trailing parentheses.

.. rst:role:: c:macro

   Reference a "simple" C macro, as defined above.

.. rst:role:: c:type

   Reference a C-language type.


The C++ Domain
--------------

The C++ domain (name **cpp**) supports documenting C++ projects.

The following directives are available:

.. rst:directive:: .. cpp:class:: signatures
               .. cpp:function:: signatures
               .. cpp:member:: signatures
               .. cpp:type:: signatures

   Describe a C++ object.  Full signature specification is supported -- give the
   signature as you would in the declaration.  Here some examples::

      .. cpp:function:: bool namespaced::theclass::method(int arg1, std::string arg2)

         Describes a method with parameters and types.

      .. cpp:function:: bool namespaced::theclass::method(arg1, arg2)

         Describes a method without types.

      .. cpp:function:: const T &array<T>::operator[]() const

         Describes the constant indexing operator of a templated array.

      .. cpp:function:: operator bool() const

         Describe a casting operator here.

      .. cpp:function:: constexpr void foo(std::string &bar[2]) noexcept

         Describe a constexpr function here.

      .. cpp:member:: std::string theclass::name

      .. cpp:member:: std::string theclass::name[N][M]

      .. cpp:type:: theclass::const_iterator

   Will be rendered like this:

      .. cpp:function:: bool namespaced::theclass::method(int arg1, std::string arg2)

         Describes a method with parameters and types.

      .. cpp:function:: bool namespaced::theclass::method(arg1, arg2)

         Describes a method without types.

      .. cpp:function:: const T &array<T>::operator[]() const

         Describes the constant indexing operator of a templated array.

      .. cpp:function:: operator bool() const

         Describe a casting operator here.

      .. cpp:function:: constexpr void foo(std::string &bar[2]) noexcept

         Describe a constexpr function here.

      .. cpp:member:: std::string theclass::name

      .. cpp:member:: std::string theclass::name[N][M]

      .. cpp:type:: theclass::const_iterator

.. rst:directive:: .. cpp:namespace:: namespace

   Select the current C++ namespace for the following objects.


.. _cpp-roles:

These roles link to the given object types:

.. rst:role:: cpp:class
          cpp:func
          cpp:member
          cpp:type

   Reference a C++ object.  You can give the full signature (and need to, for
   overloaded functions.)

   .. note::

      Sphinx' syntax to give references a custom title can interfere with
      linking to template classes, if nothing follows the closing angle
      bracket, i.e. if the link looks like this: ``:cpp:class:`MyClass<T>```.
      This is interpreted as a link to ``T`` with a title of ``MyClass``.
      In this case, please escape the opening angle bracket with a backslash,
      like this: ``:cpp:class:`MyClass\<T>```.

.. admonition:: Note on References

   It is currently impossible to link to a specific version of an
   overloaded method.  Currently the C++ domain is the first domain
   that has basic support for overloaded methods and until there is more
   data for comparison we don't want to select a bad syntax to reference a
   specific overload.  Currently Sphinx will link to the first overloaded
   version of the method / function.


The Standard Domain
-------------------

The so-called "standard" domain collects all markup that doesn't warrant a
domain of its own.  Its directives and roles are not prefixed with a domain
name.

The standard domain is also where custom object descriptions, added using the
:func:`~sphinx.application.Sphinx.add_object_type` API, are placed.

There is a set of directives allowing documenting command-line programs:

.. rst:directive:: .. option:: name args, name args, ...

   Describes a command line option or switch.  Option argument names should be
   enclosed in angle brackets.  Example::

      .. option:: -m <module>, --module <module>

         Run a module as a script.

   The directive will create a cross-reference target named after the *first*
   option, referencable by :rst:role:`option` (in the example case, you'd use
   something like ``:option:`-m```).

.. rst:directive:: .. envvar:: name

   Describes an environment variable that the documented code or program uses or
   defines.  Referencable by :rst:role:`envvar`.

.. rst:directive:: .. program:: name

   Like :rst:dir:`py:currentmodule`, this directive produces no output.  Instead, it
   serves to notify Sphinx that all following :rst:dir:`option` directives
   document options for the program called *name*.

   If you use :rst:dir:`program`, you have to qualify the references in your
   :rst:role:`option` roles by the program name, so if you have the following
   situation ::

      .. program:: rm

      .. option:: -r

         Work recursively.

      .. program:: svn

      .. option:: -r revision

         Specify the revision to work upon.

   then ``:option:`rm -r``` would refer to the first option, while
   ``:option:`svn -r``` would refer to the second one.

   The program name may contain spaces (in case you want to document subcommands
   like ``svn add`` and ``svn commit`` separately).

   .. versionadded:: 0.5


There is also a very generic object description directive, which is not tied to
any domain:

.. rst:directive:: .. describe:: text
               .. object:: text

   This directive produces the same formatting as the specific ones provided by
   domains, but does not create index entries or cross-referencing targets.
   Example::

      .. describe:: PAPER

         You can set this variable to select a paper size.


The JavaScript Domain
---------------------

The JavaScript domain (name **js**) provides the following directives:

.. rst:directive:: .. js:function:: name(signature)

   Describes a JavaScript function or method.  If you want to describe
   arguments as optional use square brackets as :ref:`documented
   <signatures>` for Python signatures.

   You can use fields to give more details about arguments and their expected
   types, errors which may be thrown by the function, and the value being
   returned::

      .. js:function:: $.getJSON(href, callback[, errback])

         :param string href: An URI to the location of the resource.
         :param callback: Get's called with the object.
         :param errback:
             Get's called in case the request fails. And a lot of other
             text so we need multiple lines
         :throws SomeError: For whatever reason in that case.
         :returns: Something

   This is rendered as:

      .. js:function:: $.getJSON(href, callback[, errback])

        :param string href: An URI to the location of the resource.
        :param callback: Get's called with the object.
        :param errback:
            Get's called in case the request fails. And a lot of other
            text so we need multiple lines.
        :throws SomeError: For whatever reason in that case.
        :returns: Something

.. rst:directive:: .. js:class:: name

   Describes a constructor that creates an object.  This is basically like
   a function but will show up with a `class` prefix::

      .. js:class:: MyAnimal(name[, age])

         :param string name: The name of the animal
         :param number age: an optional age for the animal

   This is rendered as:

      .. js:class:: MyAnimal(name[, age])

         :param string name: The name of the animal
         :param number age: an optional age for the animal

.. rst:directive:: .. js:data:: name

   Describes a global variable or constant.

.. rst:directive:: .. js:attribute:: object.name

   Describes the attribute *name* of *object*.

.. _js-roles:

These roles are provided to refer to the described objects:

.. rst:role:: js:func
          js:class
          js:data
          js:attr


The reStructuredText domain
---------------------------

The reStructuredText domain (name **rst**) provides the following directives:

.. rst:directive:: .. rst:directive:: name

   Describes a reST directive.  The *name* can be a single directive name or
   actual directive syntax (`..` prefix and `::` suffix) with arguments that
   will be rendered differently.  For example::

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.

   will be rendered as:

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.

.. rst:directive:: .. rst:role:: name

   Describes a reST role.  For example::

      .. rst:role:: foo

         Foo description.

   will be rendered as:

      .. rst:role:: foo

         Foo description.

.. _rst-roles:

These roles are provided to refer to the described objects:

.. rst:role:: rst:dir
              rst:role


More domains
------------

The sphinx-contrib_ repository contains more domains available as extensions;
currently a Ruby and an Erlang domain.


.. _sphinx-contrib: https://bitbucket.org/birkenfeld/sphinx-contrib/
