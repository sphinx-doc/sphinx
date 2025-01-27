.. highlight:: rst

==============
The C++ Domain
==============

.. versionadded:: 1.0

The C++ domain (name **cpp**) supports documenting C++ projects.

Directives for Declaring Entities
---------------------------------

The following directives are available. All declarations can start with a
visibility statement (``public``, ``private`` or ``protected``).

.. rst:directive:: .. cpp:class:: class specifier
                   .. cpp:struct:: class specifier

   Describe a class/struct, possibly with specification of inheritance, e.g.,::

      .. cpp:class:: MyClass : public MyBase, MyOtherBase

   The difference between :rst:dir:`cpp:class` and :rst:dir:`cpp:struct` is
   only cosmetic: the prefix rendered in the output, and the specifier shown
   in the index.

   The class can be directly declared inside a nested scope, e.g.,::

      .. cpp:class:: OuterScope::MyClass : public MyBase, MyOtherBase

   A class template can be declared::

      .. cpp:class:: template<typename T, std::size_t N> std::array

   or with a line break::

      .. cpp:class:: template<typename T, std::size_t N> \
                     std::array

   Full and partial template specialisations can be declared::

      .. cpp:class:: template<> \
                     std::array<bool, 256>

      .. cpp:class:: template<typename T> \
                     std::array<T, 42>

   .. versionadded:: 2.0
      The :rst:dir:`cpp:struct` directive.

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

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`cpp_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

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

   Describe a type as in a typedef declaration, a type alias declaration, or
   simply the name of a type with unspecified type, e.g.,::

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
      :no-contents-entry:
      :no-index-entry:

      A typedef-like declaration of a type.

   .. cpp:type:: MyContainer::const_iterator
      :no-contents-entry:
      :no-index-entry:

      Declaration of a type alias with unspecified type.

   .. cpp:type:: MyType = std::unordered_map<int, std::string>
      :no-contents-entry:
      :no-index-entry:

      Declaration of a type alias.

   .. cpp:type:: template<typename T> \
                 MyContainer = std::vector<T>
      :no-contents-entry:
      :no-index-entry:

.. rst:directive:: .. cpp:enum:: unscoped enum declaration
                   .. cpp:enum-struct:: scoped enum declaration
                   .. cpp:enum-class:: scoped enum declaration

   Describe a (scoped) enum, possibly with the underlying type specified.  Any
   enumerators declared inside an unscoped enum will be declared both in the
   enum scope and in the parent scope.  Examples::

      .. cpp:enum:: MyEnum

         An unscoped enum.

      .. cpp:enum:: MySpecificEnum : long

         An unscoped enum with specified underlying type.

      .. cpp:enum-class:: MyScopedEnum

         A scoped enum.

      .. cpp:enum-struct:: protected MyScopedVisibilityEnum : std::underlying_type<MySpecificEnum>::type

         A scoped enum with non-default visibility, and with a specified
         underlying type.

.. rst:directive:: .. cpp:enumerator:: name
                   .. cpp:enumerator:: name = constant

   Describe an enumerator, optionally with its value defined, e.g.,::

      .. cpp:enumerator:: MyEnum::myEnumerator

      .. cpp:enumerator:: MyEnum::myOtherEnumerator = 42

.. rst:directive:: .. cpp:union:: name

   Describe a union.

   .. versionadded:: 1.8

.. rst:directive:: .. cpp:concept:: template-parameter-list name

   .. warning:: The support for concepts is experimental. It is based on the
      current draft standard and the Concepts Technical Specification.
      The features may change as they evolve.

   Describe a concept. It must have exactly 1 template parameter list. The name
   may be a nested name. Example::

      .. cpp:concept:: template<typename It> std::Iterator

         Proxy to an element of a notional sequence that can be compared,
         indirected, or incremented.

         **Notation**

         .. cpp:var:: It r

            An lvalue.

         **Valid Expressions**

         - :cpp:expr:`*r`, when :cpp:expr:`r` is dereferenceable.
         - :cpp:expr:`++r`, with return type :cpp:expr:`It&`, when
           :cpp:expr:`r` is incrementable.

   This will render as follows:

   .. cpp:concept:: template<typename It> std::Iterator
      :no-contents-entry:
      :no-index-entry:

      Proxy to an element of a notional sequence that can be compared,
      indirected, or incremented.

      **Notation**

      .. cpp:var:: It r

         An lvalue.

      **Valid Expressions**

      - :cpp:expr:`*r`, when :cpp:expr:`r` is dereferenceable.
      - :cpp:expr:`++r`, with return type :cpp:expr:`It&`, when :cpp:expr:`r`
        is incrementable.

   .. versionadded:: 1.5


Options
~~~~~~~

Some directives support options:

- ``:no-index-entry:`` and ``:no-contents-entry:``, see :ref:`basic-domain-markup`.
- ``:tparam-line-spec:``, for templated declarations.
  If specified, each template parameter will be rendered on a separate line.

  .. versionadded:: 1.6

Anonymous Entities
------------------

C++ supports anonymous namespaces, classes, enums, and unions.
For the sake of documentation they must be given some name that starts with
``@``, e.g., ``@42`` or ``@data``.
These names can also be used in cross-references and (type) expressions,
though nested symbols will be found even when omitted.
The ``@...`` name will always be rendered as **[anonymous]** (possibly as a
link).

Example::

   .. cpp:class:: Data

      .. cpp:union:: @data

         .. cpp:var:: int a

         .. cpp:var:: double b

   Explicit ref: :cpp:var:`Data::@data::a`. Short-hand ref: :cpp:var:`Data::a`.

This will be rendered as:

.. cpp:class:: Data
   :no-contents-entry:
   :no-index-entry:

   .. cpp:union:: @data
      :no-contents-entry:
      :no-index-entry:

      .. cpp:var:: int a
         :no-contents-entry:
         :no-index-entry:

      .. cpp:var:: double b
         :no-contents-entry:
         :no-index-entry:

Explicit ref: :cpp:var:`Data::@data::a`. Short-hand ref: :cpp:var:`Data::a`.

.. versionadded:: 1.8


Aliasing Declarations
---------------------

Sometimes it may be helpful list declarations elsewhere than their main
documentation, e.g., when creating a synopsis of a class interface.
The following directive can be used for this purpose.

.. rst:directive:: .. cpp:alias:: name or function signature

   Insert one or more alias declarations. Each entity can be specified
   as they can in the :rst:role:`cpp:any` role.
   If the name of a function is given (as opposed to the complete signature),
   then all overloads of the function will be listed.

   For example::

       .. cpp:alias:: Data::a
                      overload_example::C::f

   becomes

   .. cpp:alias:: Data::a
                  overload_example::C::f

   whereas::

       .. cpp:alias:: void overload_example::C::f(double d) const
                      void overload_example::C::f(double d)

   becomes

   .. cpp:alias:: void overload_example::C::f(double d) const
                  void overload_example::C::f(double d)

   .. versionadded:: 2.0


   .. rubric:: Options

   .. rst:directive:option:: maxdepth: int

      Insert nested declarations as well, up to the total depth given.
      Use 0 for infinite depth and 1 for just the mentioned declaration.
      Defaults to 1.

      .. versionadded:: 3.5

   .. rst:directive:option:: noroot

      Skip the mentioned declarations and only render nested declarations.
      Requires ``maxdepth`` either 0 or at least 2.

      .. versionadded:: 3.5


Constrained Templates
---------------------

.. warning:: The support for concepts is experimental. It is based on the
  current draft standard and the Concepts Technical Specification.
  The features may change as they evolve.

.. note:: Sphinx does not currently support ``requires`` clauses.

Placeholders
~~~~~~~~~~~~

Declarations may use the name of a concept to introduce constrained template
parameters, or the keyword ``auto`` to introduce unconstrained template
parameters::

   .. cpp:function:: void f(auto &&arg)

      A function template with a single unconstrained template parameter.

   .. cpp:function:: void f(std::Iterator it)

      A function template with a single template parameter, constrained by the
      Iterator concept.

Template Introductions
~~~~~~~~~~~~~~~~~~~~~~

Simple constrained function or class templates can be declared with a `template
introduction` instead of a template parameter list::

   .. cpp:function:: std::Iterator{It} void advance(It &it)

       A function template with a template parameter constrained to be an
       Iterator.

   .. cpp:class:: std::LessThanComparable{T} MySortedContainer

       A class template with a template parameter constrained to be
       LessThanComparable.

They are rendered as follows.

.. cpp:function:: std::Iterator{It} void advance(It &it)
   :no-contents-entry:
   :no-index-entry:

   A function template with a template parameter constrained to be an Iterator.

.. cpp:class:: std::LessThanComparable{T} MySortedContainer
   :no-contents-entry:
   :no-index-entry:

   A class template with a template parameter constrained to be
   LessThanComparable.

Note however that no checking is performed with respect to parameter
compatibility. E.g., ``Iterator{A, B, C}`` will be accepted as an introduction
even though it would not be valid C++.

Inline Expressions and Types
----------------------------

.. rst:role:: cpp:expr
              cpp:texpr

   Insert a C++ expression or type either as inline code (``cpp:expr``)
   or inline text (``cpp:texpr``). For example::

      .. cpp:var:: int a = 42

      .. cpp:function:: int f(int i)

      An expression: :cpp:expr:`a * f(a)` (or as text: :cpp:texpr:`a * f(a)`).

      A type: :cpp:expr:`const MySortedContainer<int>&`
      (or as text :cpp:texpr:`const MySortedContainer<int>&`).

   will be rendered as follows:

   .. cpp:var:: int a = 42
      :no-contents-entry:
      :no-index-entry:

   .. cpp:function:: int f(int i)
      :no-contents-entry:
      :no-index-entry:

   An expression: :cpp:expr:`a * f(a)` (or as text: :cpp:texpr:`a * f(a)`).

   A type: :cpp:expr:`const MySortedContainer<int>&`
   (or as text :cpp:texpr:`const MySortedContainer<int>&`).

   .. versionadded:: 1.7
      The :rst:role:`cpp:expr` role.

   .. versionadded:: 1.8
      The :rst:role:`cpp:texpr` role.

Namespacing
-----------

Declarations in the C++ domain are as default placed in global scope.  The
current scope can be changed using three namespace directives.  They manage a
stack declarations where ``cpp:namespace`` resets the stack and changes a given
scope.

The ``cpp:namespace-push`` directive changes the scope to a given inner scope
of the current one.

The ``cpp:namespace-pop`` directive undoes the most recent
``cpp:namespace-push`` directive.

.. rst:directive:: .. cpp:namespace:: scope specification

   Changes the current scope for the subsequent objects to the given scope, and
   resets the namespace directive stack.  Note that the namespace does not need
   to correspond to C++ namespaces, but can end in names of classes, e.g.,::

      .. cpp:namespace:: Namespace1::Namespace2::SomeClass::AnInnerClass

   All subsequent objects will be defined as if their name were declared with
   the scope prepended. The subsequent cross-references will be searched for
   starting in the current scope.

   Using ``NULL``, ``0``, or ``nullptr`` as the scope will change to global
   scope.

   A namespace declaration can also be templated, e.g.,::

      .. cpp:class:: template<typename T> \
                     std::vector

      .. cpp:namespace:: template<typename T> std::vector

      .. cpp:function:: std::size_t size() const

   declares ``size`` as a member function of the class template
   ``std::vector``.  Equivalently this could have been declared using::

      .. cpp:class:: template<typename T> \
                     std::vector

         .. cpp:function:: std::size_t size() const

   or::

      .. cpp:class:: template<typename T> \
                     std::vector

.. rst:directive:: .. cpp:namespace-push:: scope specification

   Change the scope relatively to the current scope. For example, after::

      .. cpp:namespace:: A::B

      .. cpp:namespace-push:: C::D

   the current scope will be ``A::B::C::D``.

   .. versionadded:: 1.4

.. rst:directive:: .. cpp:namespace-pop::

   Undo the previous ``cpp:namespace-push`` directive (*not* just pop a scope).
   For example, after::

      .. cpp:namespace:: A::B

      .. cpp:namespace-push:: C::D

      .. cpp:namespace-pop::

   the current scope will be ``A::B`` (*not* ``A::B::C``).

   If no previous ``cpp:namespace-push`` directive has been used, but only a
   ``cpp:namespace`` directive, then the current scope will be reset to global
   scope.  That is, ``.. cpp:namespace:: A::B`` is equivalent to::

      .. cpp:namespace:: nullptr

      .. cpp:namespace-push:: A::B

   .. versionadded:: 1.4

Info field lists
----------------

All the C++ directives for declaring entities support the following
info fields (see also :ref:`info-field-lists`):

* ``tparam``: Description of a template parameter.

The :rst:dir:`cpp:function` directive additionally supports the
following fields:

* ``param``, ``parameter``, ``arg``, ``argument``: Description of a parameter.
* ``returns``, ``return``: Description of a return value.
* ``retval``, ``retvals``: An alternative to ``returns`` for describing
  the result of the function.
* ``throws``, ``throw``, ``exception``: Description of a possibly thrown exception.

.. versionadded:: 4.3
   The ``retval`` field type.

.. _cpp-xref-roles:

Cross-referencing
-----------------

These roles link to the given declaration types:

.. rst:role:: cpp:any
              cpp:class
              cpp:struct
              cpp:func
              cpp:member
              cpp:var
              cpp:type
              cpp:concept
              cpp:enum
              cpp:enumerator

   Reference a C++ declaration by name (see below for details).  The name must
   be properly qualified relative to the position of the link.

   .. versionadded:: 2.0
      The :rst:role:`cpp:struct` role as alias for the :rst:role:`cpp:class`
      role.

.. admonition:: Note on References with Templates Parameters/Arguments

   These roles follow the Sphinx :ref:`xref-syntax` rules. This means care must
   be taken when referencing a (partial) template specialization, e.g. if the
   link looks like this: ``:cpp:class:`MyClass<int>```.
   This is interpreted as a link to ``int`` with a title of ``MyClass``.
   In this case, escape the opening angle bracket with a backslash,
   like this: ``:cpp:class:`MyClass\<int>```.

   When a custom title is not needed it may be useful to use the roles for
   inline expressions, :rst:role:`cpp:expr` and :rst:role:`cpp:texpr`, where
   angle brackets do not need escaping.

Declarations without template parameters and template arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For linking to non-templated declarations the name must be a nested name, e.g.,
``f`` or ``MyClass::f``.


Overloaded (member) functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a (member) function is referenced using just its name, the reference
will point to an arbitrary matching overload.
The :rst:role:`cpp:any` and :rst:role:`cpp:func` roles use an alternative
format, which simply is a complete function declaration.
This will resolve to the exact matching overload.
As example, consider the following class declaration:

.. cpp:namespace-push:: overload_example
.. cpp:class:: C
   :no-contents-entry:
   :no-index-entry:

   .. cpp:function:: void f(double d) const
      :no-contents-entry:
      :no-index-entry:
   .. cpp:function:: void f(double d)
      :no-contents-entry:
      :no-index-entry:
   .. cpp:function:: void f(int i)
      :no-contents-entry:
      :no-index-entry:
   .. cpp:function:: void f()
      :no-contents-entry:
      :no-index-entry:

References using the :rst:role:`cpp:func` role:

- Arbitrary overload: ``C::f``, :cpp:func:`C::f`
- Also arbitrary overload: ``C::f()``, :cpp:func:`C::f()`
- Specific overload: ``void C::f()``, :cpp:func:`void C::f()`
- Specific overload: ``void C::f(int)``, :cpp:func:`void C::f(int)`
- Specific overload: ``void C::f(double)``, :cpp:func:`void C::f(double)`
- Specific overload: ``void C::f(double) const``,
  :cpp:func:`void C::f(double) const`

Note that the :confval:`add_function_parentheses` configuration variable
does not influence specific overload references.

.. cpp:namespace-pop::


Templated declarations
~~~~~~~~~~~~~~~~~~~~~~

Assume the following declarations.

.. cpp:class:: Wrapper
   :no-contents-entry:
   :no-index-entry:

   .. cpp:class:: template<typename TOuter> \
                  Outer
      :no-contents-entry:
      :no-index-entry:

      .. cpp:class:: template<typename TInner> \
                     Inner
         :no-contents-entry:
         :no-index-entry:

In general the reference must include the template parameter declarations,
and template arguments for the prefix of qualified names. For example:

- ``template\<typename TOuter> Wrapper::Outer``
  (:cpp:class:`template\<typename TOuter> Wrapper::Outer`)
- ``template\<typename TOuter> template\<typename TInner> Wrapper::Outer<TOuter>::Inner``
  (:cpp:class:`template\<typename TOuter> template\<typename TInner> Wrapper::Outer<TOuter>::Inner`)

Currently the lookup only succeed if the template parameter identifiers are
equal strings.  That is, ``template\<typename UOuter> Wrapper::Outer`` will not
work.

As a shorthand notation, if a template parameter list is omitted,
then the lookup will assume either a primary template or a non-template,
but not a partial template specialisation.
This means the following references work as well:

- ``Wrapper::Outer``
  (:cpp:class:`Wrapper::Outer`)
- ``Wrapper::Outer::Inner``
  (:cpp:class:`Wrapper::Outer::Inner`)
- ``template\<typename TInner> Wrapper::Outer::Inner``
  (:cpp:class:`template\<typename TInner> Wrapper::Outer::Inner`)

(Full) Template Specialisations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assume the following declarations.

.. cpp:class:: template<typename TOuter> \
               Outer
   :no-contents-entry:
   :no-index-entry:

   .. cpp:class:: template<typename TInner> \
                  Inner
      :no-contents-entry:
      :no-index-entry:

.. cpp:class:: template<> \
               Outer<int>
   :no-contents-entry:
   :no-index-entry:

   .. cpp:class:: template<typename TInner> \
                  Inner
      :no-contents-entry:
      :no-index-entry:

   .. cpp:class:: template<> \
                  Inner<bool>
      :no-contents-entry:
      :no-index-entry:

In general the reference must include a template parameter list for each
template argument list.  The full specialisation above can therefore be
referenced with ``template\<> Outer\<int>`` (:cpp:class:`template\<>
Outer\<int>`) and ``template\<> template\<> Outer\<int>::Inner\<bool>``
(:cpp:class:`template\<> template\<> Outer\<int>::Inner\<bool>`).  As a
shorthand the empty template parameter list can be omitted, e.g.,
``Outer\<int>`` (:cpp:class:`Outer\<int>`) and ``Outer\<int>::Inner\<bool>``
(:cpp:class:`Outer\<int>::Inner\<bool>`).

Partial Template Specialisations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assume the following declaration.

.. cpp:class:: template<typename T> \
               Outer<T*>
   :no-contents-entry:
   :no-index-entry:

References to partial specialisations must always include the template
parameter lists, e.g., ``template\<typename T> Outer\<T*>``
(:cpp:class:`template\<typename T> Outer\<T*>`).  Currently the lookup only
succeed if the template parameter identifiers are equal strings.

Configuration Variables
-----------------------

See :ref:`cpp-config`.
