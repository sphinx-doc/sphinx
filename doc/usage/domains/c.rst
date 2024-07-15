.. highlight:: rst

============
The C Domain
============

.. versionadded:: 1.0

The C domain (name **c**) is suited for documentation of C API.

.. rst:directive:: .. c:member:: declaration
                   .. c:var:: declaration

   Describes a C struct member or variable. Example signature::

      .. c:member:: PyObject *PyTypeObject.tp_bases

   The difference between the two directives is only cosmetic.

.. rst:directive:: .. c:function:: function prototype

   Describes a C function. The signature should be given as in C, e.g.::

      .. c:function:: PyObject *PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)

   Note that you don't have to backslash-escape asterisks in the signature, as
   it is not parsed by the reStructuredText inliner.

   In the description of a function you can use the following info fields
   (see also :ref:`info-field-lists`).

   * ``param``, ``parameter``, ``arg``, ``argument``,
     Description of a parameter.
   * ``type``: Type of a parameter,
     written as if passed to the :rst:role:`c:expr` role.
   * ``returns``, ``return``: Description of the return value.
   * ``rtype``: Return type,
     written as if passed to the :rst:role:`c:expr` role.
   * ``retval``, ``retvals``: An alternative to ``returns`` for describing
     the result of the function.

   .. versionadded:: 4.3
      The ``retval`` field type.

   For example::

      .. c:function:: PyObject *PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)

         :param type: description of the first parameter.
         :param nitems: description of the second parameter.
         :returns: a result.
         :retval NULL: under some conditions.
         :retval NULL: under some other conditions as well.

   which renders as

   .. c:function:: PyObject *PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)

      ..
         ** for some editors (e.g., vim) to stop bold-highlighting the source

      :no-contents-entry:
      :no-index-entry:
      :param type: description of the first parameter.
      :param nitems: description of the second parameter.
      :returns: a result.
      :retval NULL: under some conditions.
      :retval NULL: under some other conditions as well.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`c_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1


.. rst:directive:: .. c:macro:: name
                   .. c:macro:: name(arg list)

   Describes a C macro, i.e., a C-language ``#define``, without the replacement
   text.

   In the description of a macro you can use the same info fields as for the
   :rst:dir:`c:function` directive.

   .. versionadded:: 3.0
      The function style variant.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the macro's parameters will be emitted on a single logical
      line, overriding :confval:`c_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. c:struct:: name

   Describes a C struct.

   .. versionadded:: 3.0

.. rst:directive:: .. c:union:: name

   Describes a C union.

   .. versionadded:: 3.0

.. rst:directive:: .. c:enum:: name

   Describes a C enum.

   .. versionadded:: 3.0

.. rst:directive:: .. c:enumerator:: name

   Describes a C enumerator.

   .. versionadded:: 3.0

.. rst:directive:: .. c:type:: typedef-like declaration
                   .. c:type:: name

   Describes a C type, either as a typedef, or the alias for an unspecified
   type.

.. _c-xref-roles:

Cross-referencing C constructs
------------------------------

The following roles create cross-references to C-language constructs if they
are defined in the documentation:

.. rst:role:: c:member
              c:data
              c:var
              c:func
              c:macro
              c:struct
              c:union
              c:enum
              c:enumerator
              c:type

   Reference a C declaration, as defined above.
   Note that :rst:role:`c:member`, :rst:role:`c:data`, and
   :rst:role:`c:var` are equivalent.

   .. versionadded:: 3.0
      The var, struct, union, enum, and enumerator roles.


Anonymous Entities
------------------

C supports anonymous structs, enums, and unions.
For the sake of documentation they must be given some name that starts with
``@``, e.g., ``@42`` or ``@data``.
These names can also be used in cross-references,
though nested symbols will be found even when omitted.
The ``@...`` name will always be rendered as **[anonymous]** (possibly as a
link).

Example::

   .. c:struct:: Data

      .. c:union:: @data

         .. c:var:: int a

         .. c:var:: double b

   Explicit ref: :c:var:`Data.@data.a`. Short-hand ref: :c:var:`Data.a`.

This will be rendered as:

.. c:struct:: Data
   :no-contents-entry:
   :no-index-entry:

   .. c:union:: @data
      :no-contents-entry:
      :no-index-entry:

      .. c:var:: int a
         :no-contents-entry:
         :no-index-entry:

      .. c:var:: double b
         :no-contents-entry:
         :no-index-entry:

Explicit ref: :c:var:`Data.@data.a`. Short-hand ref: :c:var:`Data.a`.

.. versionadded:: 3.0


Aliasing Declarations
---------------------

.. c:namespace-push:: @alias

Sometimes it may be helpful list declarations elsewhere than their main
documentation, e.g., when creating a synopsis of an interface.
The following directive can be used for this purpose.

.. rst:directive:: .. c:alias:: name

   Insert one or more alias declarations. Each entity can be specified
   as they can in the :rst:role:`c:any` role.

   For example::

       .. c:var:: int data
       .. c:function:: int f(double k)

       .. c:alias:: data
                    f

   becomes

   .. c:var:: int data
      :no-contents-entry:
      :no-index-entry:

   .. c:function:: int f(double k)
      :no-contents-entry:
      :no-index-entry:

   .. c:alias:: data
                f

   .. versionadded:: 3.2


   .. rubric:: Options

   .. rst:directive:option:: maxdepth: int

      Insert nested declarations as well, up to the total depth given.
      Use 0 for infinite depth and 1 for just the mentioned declaration.
      Defaults to 1.

      .. versionadded:: 3.3

   .. rst:directive:option:: noroot

      Skip the mentioned declarations and only render nested declarations.
      Requires ``maxdepth`` either 0 or at least 2.

      .. versionadded:: 3.5


.. c:namespace-pop::


Inline Expressions and Types
----------------------------

.. rst:role:: c:expr
              c:texpr

   Insert a C expression or type either as inline code (``cpp:expr``)
   or inline text (``cpp:texpr``). For example::

      .. c:var:: int a = 42

      .. c:function:: int f(int i)

      An expression: :c:expr:`a * f(a)` (or as text: :c:texpr:`a * f(a)`).

      A type: :c:expr:`const Data*`
      (or as text :c:texpr:`const Data*`).

   will be rendered as follows:

   .. c:var:: int a = 42
      :no-contents-entry:
      :no-index-entry:

   .. c:function:: int f(int i)
      :no-contents-entry:
      :no-index-entry:

   An expression: :c:expr:`a * f(a)` (or as text: :c:texpr:`a * f(a)`).

   A type: :c:expr:`const Data*`
   (or as text :c:texpr:`const Data*`).

   .. versionadded:: 3.0


Namespacing
-----------

.. versionadded:: 3.1

The C language it self does not support namespacing, but it can sometimes be
useful to emulate it in documentation, e.g., to show alternate declarations.
The feature may also be used to document members of structs/unions/enums
separate from their parent declaration.

The current scope can be changed using three namespace directives.  They manage
a stack declarations where ``c:namespace`` resets the stack and changes a given
scope.

The ``c:namespace-push`` directive changes the scope to a given inner scope
of the current one.

The ``c:namespace-pop`` directive undoes the most recent
``c:namespace-push`` directive.

.. rst:directive:: .. c:namespace:: scope specification

   Changes the current scope for the subsequent objects to the given scope, and
   resets the namespace directive stack. Note that nested scopes can be
   specified by separating with a dot, e.g.::

      .. c:namespace:: Namespace1.Namespace2.SomeStruct.AnInnerStruct

   All subsequent objects will be defined as if their name were declared with
   the scope prepended. The subsequent cross-references will be searched for
   starting in the current scope.

   Using ``NULL`` or ``0`` as the scope will change to global scope.

.. rst:directive:: .. c:namespace-push:: scope specification

   Change the scope relatively to the current scope. For example, after::

      .. c:namespace:: A.B

      .. c:namespace-push:: C.D

   the current scope will be ``A.B.C.D``.

.. rst:directive:: .. c:namespace-pop::

   Undo the previous ``c:namespace-push`` directive (*not* just pop a scope).
   For example, after::

      .. c:namespace:: A.B

      .. c:namespace-push:: C.D

      .. c:namespace-pop::

   the current scope will be ``A.B`` (*not* ``A.B.C``).

   If no previous ``c:namespace-push`` directive has been used, but only a
   ``c:namespace`` directive, then the current scope will be reset to global
   scope.  That is, ``.. c:namespace:: A.B`` is equivalent to::

      .. c:namespace:: NULL

      .. c:namespace-push:: A.B

Configuration Variables
-----------------------

See :ref:`c-config`.
