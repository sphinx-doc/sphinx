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
   package name).  It does not create content (like e.g. :rst:dir:`py:class`
   does).

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

.. rst:directive:: .. py:function:: name(parameters)

   Describes a module-level function.  The signature should include the
   parameters as given in the Python function definition, see :ref:`signatures`.
   For example::

      .. py:function:: Timer.repeat(repeat=3, number=1000000)

   For methods you should use :rst:dir:`py:method`.

   The description normally includes information about the parameters required
   and how they are used (especially whether mutable objects passed as
   parameters are modified), side effects, and possible exceptions.

   This information can (in any ``py`` directive) optionally be given in a
   structured form, see :ref:`info-field-lists`.

.. rst:directive:: .. py:data:: name

   Describes global data in a module, including both variables and values used
   as "defined constants."  Class and object attributes are not documented
   using this environment.

.. rst:directive:: .. py:exception:: name

   Describes an exception class.  The signature can, but need not include
   parentheses with constructor arguments.

.. rst:directive:: .. py:class:: name
                   .. py:class:: name(parameters)

   Describes a class.  The signature can optionally include parentheses with
   parameters which will be shown as the constructor arguments.  See also
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

.. rst:directive:: .. py:method:: name(parameters)

   Describes an object method.  The parameters should not include the ``self``
   parameter.  The description should include similar information to that
   described for ``function``.  See also :ref:`signatures` and
   :ref:`info-field-lists`.

.. rst:directive:: .. py:staticmethod:: name(parameters)

   Like :rst:dir:`py:method`, but indicates that the method is a static method.

   .. versionadded:: 0.4

.. rst:directive:: .. py:classmethod:: name(parameters)

   Like :rst:dir:`py:method`, but indicates that the method is a class method.

   .. versionadded:: 0.6

.. rst:directive:: .. py:decorator:: name
                   .. py:decorator:: name(parameters)

   Describes a decorator function.  The signature should represent the usage as
   a decorator.  For example, given the functions

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

   (as opposed to ``.. py:decorator:: removename(func)``.)

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
would be written in Python.

Default values for optional arguments can be given (but if they contain commas,
they will confuse the signature parser).  Python 3-style argument annotations
can also be given as well as return type annotations::

   .. py:function:: compile(source : string, filename, symbol='file') -> ast object

For functions with optional parameters that don't have default values (typically
functions implemented in C extension modules without keyword argument support),
you can use brackets to specify the optional parts:

   .. py:function:: compile(source[, filename[, symbol]])

It is customary to put the opening bracket before the comma.


.. _info-field-lists:

Info field lists
~~~~~~~~~~~~~~~~

.. versionadded:: 0.4

Inside Python object description directives, reST field lists with these fields
are recognized and formatted nicely:

* ``param``, ``parameter``, ``arg``, ``argument``, ``key``, ``keyword``:
  Description of a parameter.
* ``type``: Type of a parameter.  Creates a link if possible.
* ``raises``, ``raise``, ``except``, ``exception``: That (and when) a specific
  exception is raised.
* ``var``, ``ivar``, ``cvar``: Description of a variable.
* ``vartype``: Type of a variable.  Creates a link if possible.
* ``returns``, ``return``: Description of the return value.
* ``rtype``: Return type.  Creates a link if possible.

The field names must consist of one of these keywords and an argument (except
for ``returns`` and ``rtype``, which do not need an argument).  This is best
explained by an example::

   .. py:function:: send_message(sender, recipient, message_body, [priority=1])

      Send a message to a recipient

      :param str sender: The person sending the message
      :param str recipient: The recipient of the message
      :param str message_body: The body of the message
      :param priority: The priority of the message, can be a number 1-5
      :type priority: integer or None
      :return: the message id
      :rtype: int
      :raises ValueError: if the message_body exceeds 160 characters
      :raises TypeError: if the message_body is not a basestring

This will render like this:

   .. py:function:: send_message(sender, recipient, message_body, [priority=1])
      :noindex:

      Send a message to a recipient

      :param str sender: The person sending the message
      :param str recipient: The recipient of the message
      :param str message_body: The body of the message
      :param priority: The priority of the message, can be a number 1-5
      :type priority: integer or None
      :return: the message id
      :rtype: int
      :raises ValueError: if the message_body exceeds 160 characters
      :raises TypeError: if the message_body is not a basestring

It is also possible to combine parameter type and description, if the type is a
single word, like this::

   :param int priority: The priority of the message, can be a number 1-5


.. versionadded:: 1.5

Container types such as lists and dictionaries can be linked automatically
using the following syntax::

   :type priorities: list(int)
   :type priorities: list[int]
   :type mapping: dict(str, int)
   :type mapping: dict[str, int]
   :type point: tuple(float, float)
   :type point: tuple[float, float]

Multiple types in a type field will be linked automatically if separated by
the word "or"::

   :type an_arg: int or None
   :vartype a_var: str or int
   :rtype: float or str

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
   value is ``True`` (the default).

.. rst:role:: py:data

   Reference a module-level variable.

.. rst:role:: py:const

   Reference a "defined" constant.  This may be a Python variable that is not
   intended to be changed.

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
   functions.  This is a simple C-language ``#define``.  Examples of its use in
   the Python documentation include :c:macro:`PyObject_HEAD` and
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

The following directives are available. All declarations can start with
a visibility statement (``public``, ``private`` or ``protected``).

.. rst:directive:: .. cpp:class:: class specifier

   Describe a class/struct, possibly with specification of inheritance, e.g.,::

      .. cpp:class:: MyClass : public MyBase, MyOtherBase

   The class can be directly declared inside a nested scope, e.g.,::

      .. cpp:class:: OuterScope::MyClass : public MyBase, MyOtherBase

   A template class can be declared::

      .. cpp:class:: template<typename T, std::size_t N> std::array

   or with a line break::

      .. cpp:class:: template<typename T, std::size_t N> \
                     std::array

   Full and partial template specialisations can be declared::

      .. cpp:class:: template<> \
                      std::array<bool, 256>

      .. cpp:class:: template<typename T> \
                      std::array<T, 42>


.. rst:directive:: .. cpp:function:: (member) function prototype

   Describe a function or member function, e.g.,::

      .. cpp:function:: bool myMethod(int arg1, std::string arg2)

         A function with parameters and types.

      .. cpp:function:: bool myMethod(int, double)

         A function with unnamed parameters.

      .. cpp:function:: const T &MyClass::operator[](std::size_t i) const

         An overload for the indexing operator.

      .. cpp:function:: operator bool() const

         A casting operator.

      .. cpp:function:: constexpr void foo(std::string &bar[2]) noexcept

         A constexpr function.

      .. cpp:function:: MyClass::MyClass(const MyClass&) = default

         A copy constructor with default implementation.

   Function templates can also be described::

      .. cpp:function:: template<typename U> \
                        void print(U &&u)

   and function template specialisations::

      .. cpp:function:: template<> \
                        void print(int i)


.. rst:directive:: .. cpp:member:: (member) variable declaration
                   .. cpp:var:: (member) variable declaration

   Describe a variable or member variable, e.g.,::

      .. cpp:member:: std::string MyClass::myMember

      .. cpp:var:: std::string MyClass::myOtherMember[N][M]

      .. cpp:member:: int a = 42

   Variable templates can also be described::

      .. cpp:member:: template<class T> \
                      constexpr T pi = T(3.1415926535897932385)


.. rst:directive:: .. cpp:type:: typedef declaration
                   .. cpp:type:: name
                   .. cpp:type:: type alias declaration

   Describe a type as in a typedef declaration, a type alias declaration,
   or simply the name of a type with unspecified type, e.g.,::

      .. cpp:type:: std::vector<int> MyList

         A typedef-like declaration of a type.

      .. cpp:type:: MyContainer::const_iterator

         Declaration of a type alias with unspecified type.

      .. cpp:type:: MyType = std::unordered_map<int, std::string>

         Declaration of a type alias.

   A type alias can also be templated::

      .. cpp:type:: template<typename T> \
                    MyContainer = std::vector<T>

   The example are rendered as follows.

   .. cpp:type:: std::vector<int> MyList

      A typedef-like declaration of a type.

   .. cpp:type:: MyContainer::const_iterator

      Declaration of a type alias with unspecified type.

   .. cpp:type:: MyType = std::unordered_map<int, std::string>

      Declaration of a type alias.

   .. cpp:type:: template<typename T> \
                 MyContainer = std::vector<T>


.. rst:directive:: .. cpp:enum:: unscoped enum declaration
                   .. cpp:enum-struct:: scoped enum declaration
                   .. cpp:enum-class:: scoped enum declaration

   Describe a (scoped) enum, possibly with the underlying type specified.
   Any enumerators declared inside an unscoped enum will be declared both in the enum scope
   and in the parent scope.
   Examples::

      .. cpp:enum:: MyEnum

         An unscoped enum.

      .. cpp:enum:: MySpecificEnum : long

         An unscoped enum with specified underlying type.

      .. cpp:enum-class:: MyScopedEnum

         A scoped enum.

      .. cpp:enum-struct:: protected MyScopedVisibilityEnum : std::underlying_type<MySpecificEnum>::type

         A scoped enum with non-default visibility, and with a specified underlying type.

.. rst:directive:: .. cpp:enumerator:: name
                   .. cpp:enumerator:: name = constant

   Describe an enumerator, optionally with its value defined, e.g.,::

      .. cpp:enumerator:: MyEnum::myEnumerator

      .. cpp:enumerator:: MyEnum::myOtherEnumerator = 42


.. rst:directive:: .. cpp:concept:: template-parameter-list name
                   .. cpp:concept:: template-parameter-list name()

   .. warning:: The support for concepts is experimental. It is based on the
      Concepts Technical Specification, and the features may change as the TS evolves.

   Describe a variable concept or a function concept. Both must have exactly 1
   template parameter list. The name may be a nested name. Examples::

      .. cpp:concept:: template<typename It> std::Iterator

         Proxy to an element of a notional sequence that can be compared,
         indirected, or incremented.

      .. cpp:concept:: template<typename Cont> std::Container()

         Holder of elements, to which it can provide access via
         :cpp:concept:`Iterator` s.

   They will render as follows:

   .. cpp:concept:: template<typename It> std::Iterator

      Proxy to an element of a notional sequence that can be compared,
      indirected, or incremented.

   .. cpp:concept:: template<typename Cont> std::Container()

      Holder of elements, to which it can provide access via
      :cpp:concept:`Iterator` s.

Constrained Templates
~~~~~~~~~~~~~~~~~~~~~

.. warning:: The support for constrained templates is experimental. It is based on the
  Concepts Technical Specification, and the features may change as the TS evolves.

.. note:: Sphinx does not currently support ``requires`` clauses.

Placeholders
............

Declarations may use the name of a concept to introduce constrained template
parameters, or the keyword ``auto`` to introduce unconstrained template parameters::

   .. cpp:function:: void f(auto &&arg)

      A function template with a single unconstrained template parameter.

   .. cpp:function:: void f(std::Iterator it)

      A function template with a single template parameter, constrained by the
      Iterator concept.

Template Introductions
......................

Simple constrained function or class templates can be declared with a
`template introduction` instead of a template parameter list::

   .. cpp:function:: std::Iterator{It} void advance(It &it)

       A function template with a template parameter constrained to be an Iterator.

   .. cpp:class:: std::LessThanComparable{T} MySortedContainer

       A class template with a template parameter constrained to be LessThanComparable.

They are rendered as follows.

.. cpp:function:: std::Iterator{It} void advance(It &it)

   A function template with a template parameter constrained to be an Iterator.

.. cpp:class:: std::LessThanComparable{T} MySortedContainer

   A class template with a template parameter constrained to be LessThanComparable.

Note however that no checking is performed with respect to parameter
compatibility. E.g., ``Iterator{A, B, C}`` will be accepted as an introduction
even though it would not be valid C++.


Namespacing
~~~~~~~~~~~~~~~~~

Declarations in the C++ domain are as default placed in global scope.
The current scope can be changed using three namespace directives.
They manage a stack declarations where ``cpp:namespace`` resets the stack and
changes a given scope.
The ``cpp:namespace-push`` directive changes the scope to a given inner scope
of the current one.
The ``cpp:namespace-pop`` directive undos the most recent ``cpp:namespace-push``
directive.

.. rst:directive:: .. cpp:namespace:: scope specification

   Changes the current scope for the subsequent objects to the given scope,
   and resets the namespace directive stack.
   Note that the namespace does not need to correspond to C++ namespaces,
   but can end in names of classes, e.g.,::

      .. cpp:namespace:: Namespace1::Namespace2::SomeClass::AnInnerClass

   All subsequent objects will be defined as if their name were declared with the scope
   prepended. The subsequent cross-references will be searched for starting in the current scope.

   Using ``NULL``, ``0``, or ``nullptr`` as the scope will change to global scope.

   A namespace declaration can also be templated, e.g.,::

      .. cpp:class:: template<typename T> \
                     std::vector

      .. cpp:namespace:: template<typename T> std::vector

      .. cpp:function:: std::size_t size() const

   declares ``size`` as a member function of the template class ``std::vector``.
   Equivalently this could have been declared using::

      .. cpp:class:: template<typename T> \
                     std::vector

         .. cpp:function:: std::size_t size() const

   or:::

      .. cpp:class:: template<typename T> \
                     std::vector


.. rst:directive:: .. cpp:namespace-push:: scope specification

   Change the scope relatively to the current scope. For example, after::

      .. cpp:namespace:: A::B

      .. cpp:namespace-push:: C::D

   the current scope will be ``A::B::C::D``.

.. rst:directive:: .. cpp:namespace-pop::

   Undo the previous ``cpp:namespace-push`` directive (*not* just pop a scope).
   For example, after::

      .. cpp:namespace:: A::B

      .. cpp:namespace-push:: C::D

      .. cpp:namespace-pop::

   the current scope will be ``A::B`` (*not* ``A::B::C``).

   If no previous ``cpp:namespace-push`` directive has been used, but only a ``cpp:namespace``
   directive, then the current scope will be reset to global scope.
   That is, ``.. cpp:namespace:: A::B`` is equivalent to::

      .. cpp:namespace:: nullptr

      .. cpp:namespace-push:: A::B


Info field lists
~~~~~~~~~~~~~~~~~

The C++ directives support the following info fields (see also :ref:`info-field-lists`):

* `param`, `parameter`, `arg`, `argument`: Description of a parameter.
* `tparam`: Description of a template parameter.
* `returns`, `return`: Description of a return value.
* `throws`, `throw`, `exception`: Description of a possibly thrown exception.


.. _cpp-roles:

Cross-referencing
~~~~~~~~~~~~~~~~~

These roles link to the given declaration types:

.. rst:role:: cpp:any
              cpp:class
              cpp:func
              cpp:member
              cpp:var
              cpp:type
              cpp:concept
              cpp:enum
              cpp:enumerator

   Reference a C++ declaration by name (see below for details).
   The name must be properly qualified relative to the position of the link.

.. admonition:: Note on References with Templates Parameters/Arguments

   Sphinx's syntax to give references a custom title can interfere with
   linking to template classes, if nothing follows the closing angle
   bracket, i.e. if the link looks like this: ``:cpp:class:`MyClass<int>```.
   This is interpreted as a link to ``int`` with a title of ``MyClass``.
   In this case, please escape the opening angle bracket with a backslash,
   like this: ``:cpp:class:`MyClass\<int>```.

.. admonition:: Note on References to Overloaded Functions

   It is currently impossible to link to a specific version of an
   overloaded method.  Currently the C++ domain is the first domain
   that has basic support for overloaded methods and until there is more
   data for comparison we don't want to select a bad syntax to reference a
   specific overload.  Currently Sphinx will link to the first overloaded
   version of the method / function.

Declarations without template parameters and template arguments
.................................................................

For linking to non-templated declarations the name must be a nested name,
e.g., ``f`` or ``MyClass::f``.

Templated declarations
......................

Assume the following declarations.

.. cpp:class:: Wrapper

   .. cpp:class:: template<typename TOuter> \
                  Outer

      .. cpp:class:: template<typename TInner> \
                     Inner

In general the reference must include the template paraemter declarations, e.g.,
``template\<typename TOuter> Wrapper::Outer`` (:cpp:class:`template\<typename TOuter> Wrapper::Outer`).
Currently the lookup only succeed if the template parameter identifiers are equal strings. That is,
``template\<typename UOuter> Wrapper::Outer`` will not work.

The inner template class can not be directly referenced, unless the current namespace
is changed or the following shorthand is used.
If a template parameter list is omitted, then the lookup will assume either a template or a non-template,
but not a partial template specialisation.
This means the following references work.

- ``Wrapper::Outer`` (:cpp:class:`Wrapper::Outer`)
- ``Wrapper::Outer::Inner`` (:cpp:class:`Wrapper::Outer::Inner`)
- ``template\<typename TInner> Wrapper::Outer::Inner`` (:cpp:class:`template\<typename TInner> Wrapper::Outer::Inner`)

(Full) Template Specialisations
................................

Assume the following declarations.

.. cpp:class:: template<typename TOuter> \
               Outer

  .. cpp:class:: template<typename TInner> \
                 Inner

.. cpp:class:: template<> \
               Outer<int>

  .. cpp:class:: template<typename TInner> \
                 Inner

  .. cpp:class:: template<> \
                 Inner<bool>

In general the reference must include a template parameter list for each template argument list.
The full specialisation above can therefore be referenced with ``template\<> Outer\<int>`` (:cpp:class:`template\<> Outer\<int>`)
and ``template\<> template\<> Outer\<int>::Inner\<bool>`` (:cpp:class:`template\<> template\<> Outer\<int>::Inner\<bool>`).
As a shorthand the empty template parameter list can be omitted, e.g., ``Outer\<int>`` (:cpp:class:`Outer\<int>`)
and ``Outer\<int>::Inner\<bool>`` (:cpp:class:`Outer\<int>::Inner\<bool>`).


Partial Template Specialisations
.................................

Assume the following declaration.

.. cpp:class:: template<typename T> \
               Outer<T*>

References to partial specialisations must always include the template parameter lists, e.g.,
``template\<typename T> Outer\<T*>`` (:cpp:class:`template\<typename T> Outer\<T*>`).
Currently the lookup only succeed if the template parameter identifiers are equal strings.


Configuration Variables
~~~~~~~~~~~~~~~~~~~~~~~

See :ref:`cpp-config`.


The Standard Domain
-------------------

The so-called "standard" domain collects all markup that doesn't warrant a
domain of its own.  Its directives and roles are not prefixed with a domain
name.

The standard domain is also where custom object descriptions, added using the
:func:`~sphinx.application.Sphinx.add_object_type` API, are placed.

There is a set of directives allowing documenting command-line programs:

.. rst:directive:: .. option:: name args, name args, ...

   Describes a command line argument or switch.  Option argument names should be
   enclosed in angle brackets.  Examples::

      .. option:: dest_dir

         Destination directory.

      .. option:: -m <module>, --module <module>

         Run a module as a script.

   The directive will create cross-reference targets for the given options,
   referencable by :rst:role:`option` (in the example case, you'd use something
   like ``:option:`dest_dir```, ``:option:`-m```, or ``:option:`--module```).

   ``cmdoption`` directive is a deprecated alias for the ``option`` directive.

.. rst:directive:: .. envvar:: name

   Describes an environment variable that the documented code or program uses or
   defines.  Referencable by :rst:role:`envvar`.

.. rst:directive:: .. program:: name

   Like :rst:dir:`py:currentmodule`, this directive produces no output.
   Instead, it serves to notify Sphinx that all following :rst:dir:`option`
   directives document options for the program called *name*.

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
         :param callback: Gets called with the object.
         :param errback:
             Gets called in case the request fails. And a lot of other
             text so we need multiple lines.
         :throws SomeError: For whatever reason in that case.
         :returns: Something.

   This is rendered as:

      .. js:function:: $.getJSON(href, callback[, errback])

        :param string href: An URI to the location of the resource.
        :param callback: Gets called with the object.
        :param errback:
            Gets called in case the request fails. And a lot of other
            text so we need multiple lines.
        :throws SomeError: For whatever reason in that case.
        :returns: Something.

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
currently Ada_, CoffeeScript_, Erlang_, HTTP_, Lasso_, MATLAB_, PHP_, and Ruby_
domains. Also available are domains for `Chapel`_, `Common Lisp`_, dqn_, Go_,
Jinja_, Operation_, and Scala_.


.. _sphinx-contrib: https://bitbucket.org/birkenfeld/sphinx-contrib/

.. _Ada: https://pypi.python.org/pypi/sphinxcontrib-adadomain
.. _Chapel: https://pypi.python.org/pypi/sphinxcontrib-chapeldomain
.. _CoffeeScript: https://pypi.python.org/pypi/sphinxcontrib-coffee
.. _Common Lisp: https://pypi.python.org/pypi/sphinxcontrib-cldomain
.. _dqn: https://pypi.python.org/pypi/sphinxcontrib-dqndomain
.. _Erlang: https://pypi.python.org/pypi/sphinxcontrib-erlangdomain
.. _Go: https://pypi.python.org/pypi/sphinxcontrib-golangdomain
.. _HTTP: https://pypi.python.org/pypi/sphinxcontrib-httpdomain
.. _Jinja: https://pypi.python.org/pypi/sphinxcontrib-jinjadomain
.. _Lasso: https://pypi.python.org/pypi/sphinxcontrib-lassodomain
.. _MATLAB: https://pypi.python.org/pypi/sphinxcontrib-matlabdomain
.. _Operation: https://pypi.python.org/pypi/sphinxcontrib-operationdomain
.. _PHP: https://pypi.python.org/pypi/sphinxcontrib-phpdomain
.. _Ruby: https://bitbucket.org/birkenfeld/sphinx-contrib/src/default/rubydomain
.. _Scala: https://pypi.python.org/pypi/sphinxcontrib-scaladomain
