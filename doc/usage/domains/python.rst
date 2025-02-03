.. highlight:: rst

=================
The Python Domain
=================

.. versionadded:: 1.0

The Python domain (name **py**) provides the following directives for module
declarations:

.. rst:directive:: .. py:module:: name

   This directive marks the beginning of the description of a module (or package
   submodule, in which case the name should be fully qualified, including the
   package name).  A description of the module such as the docstring can be
   placed in the body of the directive.

   This directive will also cause an entry in the global module index.

   .. versionchanged:: 5.2

      Module directives support body content.

   .. rubric:: options

   .. rst:directive:option:: platform: platforms
      :type: comma separated list

      Indicate platforms which the module is available (if it is available on
      all platforms, the option should be omitted).  The keys are short
      identifiers; examples that are in use include "IRIX", "Mac", "Windows"
      and "Unix".  It is important to use a key which has already been used when
      applicable.

   .. rst:directive:option:: synopsis: purpose
      :type: text

      Consist of one sentence describing the module's purpose -- it is currently
      only used in the Global Module Index.

   .. rst:directive:option:: deprecated
      :type: no argument

      Mark a module as deprecated; it will be designated as such in various
      locations then.


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
                   .. py:function:: name[type parameters](parameters)

   Describes a module-level function.
   The signature should include the parameters,
   together with optional type parameters,
   as given in the Python function definition, see :ref:`signatures`.
   For example::

      .. py:function:: Timer.repeat(repeat=3, number=1_000_000)
      .. py:function:: add[T](a: T, b: T) -> T

   For methods you should use :rst:dir:`py:method`.

   The description normally includes information about the parameters required
   and how they are used (especially whether mutable objects passed as
   parameters are modified), side effects, and possible exceptions.

   This information can (in any ``py`` directive) optionally be given in a
   structured form, see :ref:`info-field-lists`.

   .. rubric:: options

   .. rst:directive:option:: async
      :type: no value

      Indicate the function is an async function.

      .. versionadded:: 2.1

   .. rst:directive:option:: canonical
      :type: full qualified name including module name

      Describe the location where the object is defined if the object is
      imported from other modules

      .. versionadded:: 4.0

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's arguments will be emitted on a single logical
      line, overriding :confval:`python_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

   .. rst:directive:option:: single-line-type-parameter-list
      :type: no value

      Ensure that the function's type parameters are emitted on a single
      logical line, overriding :confval:`python_maximum_signature_line_length`
      and :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1


.. rst:directive:: .. py:data:: name

   Describes global data in a module, including both variables and values used
   as "defined constants."
   Consider using :rst:dir:`py:type` for type aliases instead
   and :rst:dir:`py:attribute` for class variables and instance attributes.

   .. rubric:: options

   .. rst:directive:option:: type: type of the variable
      :type: text

      This will be parsed as a Python expression for cross-referencing
      the type annotation.
      As such, the argument to ``:type:`` should be a valid `annotation expression`_.

      .. caution::
         The valid syntax for the ``:type:`` directive option differs from
         the syntax for the ``:type:`` `info field <info-field-lists_>`__.
         The ``:type:`` directive option does not understand
         reStructuredText markup or the ``or`` or ``of`` keywords,
         meaning unions must use ``|`` and sequences must use square brackets,
         and roles such as ``:ref:`...``` cannot be used.

      .. versionadded:: 2.4

   .. rst:directive:option:: value: initial value of the variable
      :type: text

      .. versionadded:: 2.4

   .. rst:directive:option:: canonical
      :type: full qualified name including module name

      Describe the location where the object is defined if the object is
      imported from other modules

      .. versionadded:: 4.0

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

.. rst:directive:: .. py:exception:: name
                   .. py:exception:: name(parameters)
                   .. py:exception:: name[type parameters](parameters)

   Describes an exception class.
   The signature can, but need not include parentheses with constructor arguments,
   or may optionally include type parameters (see :pep:`695`).

   .. rubric:: options

   .. rst:directive:option:: final
      :type: no value

      Indicate the class is a final class.

      .. versionadded:: 3.1

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      See :rst:dir:`py:class:single-line-parameter-list`.

      .. versionadded:: 7.1

   .. rst:directive:option:: single-line-type-parameter-list
      :type: no value

      See :rst:dir:`py:class:single-line-type-parameter-list`.

      .. versionadded:: 7.1

.. rst:directive:: .. py:class:: name
                   .. py:class:: name(parameters)
                   .. py:class:: name[type parameters](parameters)

   Describes a class.
   The signature can optionally include type parameters (see :pep:`695`)
   or parentheses with parameters which will be shown as the constructor arguments.
   See also :ref:`signatures`.

   Methods and attributes belonging to the class should be placed in this
   directive's body.  If they are placed outside, the supplied name should
   contain the class name so that cross-references still work.  Example::

      .. py:class:: Foo

         .. py:method:: quux()

      -- or --

      .. py:class:: Bar

      .. py:method:: Bar.quux()

   The first way is the preferred one.

   .. rubric:: options

   .. rst:directive:option:: abstract
      :type: no value

      Indicate that the class is an abstract base class.
      This produces the following output:

      .. py:class:: Cheese
         :no-index:
         :abstract:

         A cheesy representation.

      .. versionadded:: 8.2

   .. rst:directive:option:: canonical
      :type: full qualified name including module name

      Describe the location where the object is defined if the object is
      imported from other modules

      .. versionadded:: 4.0

   .. rst:directive:option:: final
      :type: no value

      Indicate the class is a final class.

      .. versionadded:: 3.1

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the class constructor's arguments will be emitted on a single
      logical line, overriding :confval:`python_maximum_signature_line_length`
      and :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

   .. rst:directive:option:: single-line-type-parameter-list
      :type: no value

      Ensure that the class type parameters are emitted on a single logical
      line, overriding :confval:`python_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

.. rst:directive:: .. py:attribute:: name

   Describes an object data attribute.  The description should include
   information about the type of the data to be expected and whether it may be
   changed directly.
   Type aliases should be documented with :rst:dir:`py:type`.

   .. rubric:: options

   .. rst:directive:option:: type: type of the attribute
      :type: text

      This will be parsed as a Python expression for cross-referencing
      the type annotation.
      As such, the argument to ``:type:`` should be a valid `annotation expression`_.

      .. caution::
         The valid syntax for the ``:type:`` directive option differs from
         the syntax for the ``:type:`` `info field <info-field-lists_>`__.
         The ``:type:`` directive option does not understand
         reStructuredText markup or the ``or`` or ``of`` keywords,
         meaning unions must use ``|`` and sequences must use square brackets,
         and roles such as ``:ref:`...``` cannot be used.

      .. versionadded:: 2.4

   .. rst:directive:option:: value: initial value of the attribute
      :type: text

      .. versionadded:: 2.4

   .. rst:directive:option:: canonical
      :type: full qualified name including module name

      Describe the location where the object is defined if the object is
      imported from other modules

      .. versionadded:: 4.0

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

.. rst:directive:: .. py:property:: name

   Describes an object property.

   .. versionadded:: 4.0

   .. rubric:: options

   .. rst:directive:option:: abstract
                             abstractmethod
      :type: no value

      Indicate the property is abstract.
      This produces the following output:

      .. py:property:: Cheese.amount_in_stock
         :no-index:
         :abstractmethod:

         Cheese levels at the *National Cheese Emporium*.

      .. versionchanged:: 8.2

         The ``:abstract:`` alias is also supported.

   .. rst:directive:option:: classmethod
      :type: no value

      Indicate the property is a classmethod.

      .. versionadded:: 4.2

   .. rst:directive:option:: type: type of the property
      :type: text

      This will be parsed as a Python expression for cross-referencing
      the type annotation.
      As such, the argument to ``:type:`` should be a valid `annotation expression`_.

      .. caution::
         The valid syntax for the ``:type:`` directive option differs from
         the syntax for the ``:type:`` `info field <info-field-lists_>`__.
         The ``:type:`` directive option does not understand
         reStructuredText markup or the ``or`` or ``of`` keywords,
         meaning unions must use ``|`` and sequences must use square brackets,
         and roles such as ``:ref:`...``` cannot be used.

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

.. rst:directive:: .. py:type:: name

   Describe a :ref:`type alias <python:type-aliases>`.

   The type that the alias represents should be described
   with the :rst:dir:`!canonical` option.
   This directive supports an optional description body.

   For example:

   .. code-block:: rst

      .. py:type:: UInt64

         Represent a 64-bit positive integer.

   will be rendered as follows:

   .. py:type:: UInt64
      :no-contents-entry:
      :no-index-entry:

      Represent a 64-bit positive integer.

   .. rubric:: options

   .. rst:directive:option:: canonical
      :type: text

      The canonical type represented by this alias, for example:

      .. code-block:: rst

         .. py:type:: StrPattern
            :canonical: str | re.Pattern[str]

            Represent a regular expression or a compiled pattern.

      This is rendered as:

      .. py:type:: StrPattern
         :no-contents-entry:
         :no-index-entry:
         :canonical: str | re.Pattern[str]

         Represent a regular expression or a compiled pattern.

   .. versionadded:: 7.4

.. rst:directive:: .. py:method:: name(parameters)
                   .. py:method:: name[type parameters](parameters)

   Describes an object method.  The parameters should not include the ``self``
   parameter.  The description should include similar information to that
   described for ``function``.  See also :ref:`signatures` and
   :ref:`info-field-lists`.

   .. rubric:: options

   .. rst:directive:option:: abstract
                             abstractmethod
      :type: no value

      Indicate the method is an abstract method.
      This produces the following output:

      .. py:method:: Cheese.order_more_stock
         :no-index:
         :abstractmethod:

         Order more cheese (we're fresh out!).

      .. versionadded:: 2.1
      .. versionchanged:: 8.2

         The ``:abstract:`` alias is also supported.

   .. rst:directive:option:: async
      :type: no value

      Indicate the method is an async method.

      .. versionadded:: 2.1

   .. rst:directive:option:: canonical
      :type: full qualified name including module name

      Describe the location where the object is defined if the object is
      imported from other modules

      .. versionadded:: 4.0

   .. rst:directive:option:: classmethod
      :type: no value

      Indicate the method is a class method.

      .. versionadded:: 2.1

   .. rst:directive:option:: final
      :type: no value

      Indicate the method is a final method.

      .. versionadded:: 3.1

   .. rst::directive:option:: module
      :type: text

      Describe the location where the object is defined.  The default value is
      the module specified by :rst:dir:`py:currentmodule`.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the method's arguments will be emitted on a single logical
      line, overriding :confval:`python_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

   .. rst:directive:option:: single-line-type-parameter-list
      :type: no value

      Ensure that the method's type parameters are emitted on a single logical
      line, overriding :confval:`python_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.2

   .. rst:directive:option:: staticmethod
      :type: no value

      Indicate the method is a static method.

      .. versionadded:: 2.1


.. rst:directive:: .. py:staticmethod:: name(parameters)
                   .. py:staticmethod:: name[type parameters](parameters)

   Like :rst:dir:`py:method`, but indicates that the method is a static method.

   .. versionadded:: 0.4

.. rst:directive:: .. py:classmethod:: name(parameters)
                   .. py:classmethod:: name[type parameters](parameters)

   Like :rst:dir:`py:method`, but indicates that the method is a class method.

   .. versionadded:: 0.6

.. rst:directive:: .. py:decorator:: name
                   .. py:decorator:: name(parameters)
                   .. py:decorator:: name[type parameters](parameters)

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

   Refer to a decorator function using the :rst:role:`py:deco` role.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the decorator's arguments will be emitted on a single logical
      line, overriding :confval:`python_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

   .. rst:directive:option:: single-line-type-parameter-list
      :type: no value

      Ensure that the decorator's type parameters are emitted on a single
      logical line, overriding :confval:`python_maximum_signature_line_length`
      and :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.2

.. rst:directive:: .. py:decoratormethod:: name
                   .. py:decoratormethod:: name(signature)
                   .. py:decoratormethod:: name[type parameters](signature)

   Same as :rst:dir:`py:decorator`, but for decorators that are methods.

   Refer to a decorator method using the :rst:role:`py:deco` role.

.. _annotation expression: https://typing.readthedocs.io/en/latest/spec/annotations.html#type-and-annotation-expressions

.. _signatures:

Python Signatures
-----------------

Signatures of functions, methods and class constructors can be given like they
would be written in Python.
This can include default values, positional-only or keyword-only parameters,
type annotations, and type parameters.
For example:

.. code-block:: rst

   .. py:function:: compile(source: str, filename: Path, symbol: str = 'file') -> ast.AST

.. py:function:: compile(source: str, filename: Path, symbol: str = 'file') -> ast.AST
   :no-index:

For functions with optional parameters that don't have default values
(typically functions implemented in C extension modules without keyword
argument support),
you can list multiple versions of the same signature in a single directive:

.. py:function:: compile(source)
                 compile(source, filename)
                 compile(source, filename, symbol)
   :no-index:

Another approach is to use square brackets to specify the optional parts.
When using square brackets, it is customary to place
the opening bracket before the comma (``[,``).

.. py:function:: compile(source[, filename[, symbol]])
   :no-index:

Python 3.12 introduced *type parameters*, which are type variables
declared directly within the class or function definition:

.. code-block:: python

   class AnimalList[AnimalT](list[AnimalT]):
       ...

   def add[T](a: T, b: T) -> T:
       return a + b

The corresponding reStructuredText markup would be:

.. code-block:: rst

   .. py:class:: AnimalList[AnimalT]

   .. py:function:: add[T](a: T, b: T) -> T

.. seealso::

   :pep:`695` and :pep:`696`, for details and the full specification.


.. _info-field-lists:

Info field lists
----------------

.. versionadded:: 0.4
.. versionchanged:: 3.0

   meta fields are added.

Inside Python object description directives,
reStructuredText field lists with these fields
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
* ``meta``: Add metadata to description of the python object.  The metadata will
  not be shown on output document.  For example, ``:meta private:`` indicates
  the python object is private member.  It is used in
  :py:mod:`sphinx.ext.autodoc` for filtering members.

.. note::

   In current release, all ``var``, ``ivar`` and ``cvar`` are represented as
   "Variable".  There is no difference at all.

The field names must consist of one of these keywords and an argument (except
for ``returns`` and ``rtype``, which do not need an argument).  This is best
explained by an example::

   .. py:function:: send_message(sender, recipient, message_body, [priority=1])

      Send a message to a recipient

      :param str sender: The person sending the message
      :param str recipient: The recipient of the message
      :param str message_body: The body of the message
      :param priority: The priority of the message, can be a number 1-5
      :type priority: int or None
      :return: the message id
      :rtype: int
      :raises ValueError: if the message_body exceeds 160 characters
      :raises TypeError: if the message_body is not a basestring

This will render like this:

.. py:function:: send_message(sender, recipient, message_body, [priority=1])
   :no-contents-entry:
   :no-index-entry:

   Send a message to a recipient

   :param str sender: The person sending the message
   :param str recipient: The recipient of the message
   :param str message_body: The body of the message
   :param priority: The priority of the message, can be a number 1-5
   :type priority: int or None
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

Multiple types in a type field will be linked automatically
if separated by either the vertical bar (``|``) or the word "or"::

   :type an_arg: int or None
   :vartype a_var: str or int
   :rtype: float or str

   :type an_arg: int | None
   :vartype a_var: str | int
   :rtype: float | str

.. _python-xref-roles:

Cross-referencing Python objects
--------------------------------

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

.. rst:role:: py:deco

   Reference a Python decorator; dotted names may be used.
   The rendered output will be prepended with an at-sign (``@``),
   for example: ``:py:deco:`removename``` produces :py:deco:`removename`.

   .. py:decorator:: removename
      :no-contents-entry:
      :no-index-entry:
      :no-typesetting:

.. rst:role:: py:data

   Reference a module-level variable.

.. rst:role:: py:const

   Reference a "defined" constant.  This may be a Python variable that is not
   intended to be changed.

.. rst:role:: py:class

   Reference a class; a dotted name may be used.

.. rst:role:: py:meth

   Reference a method of an object.  The role text can include the type name
   and the method name; if it occurs within the description of a type, the type
   name can be omitted.  A dotted name may be used.

.. rst:role:: py:attr

   Reference a data attribute of an object.

   .. note:: The role is also able to refer to property.

.. rst:role:: py:type

   Reference a type alias.

.. rst:role:: py:exc

   Reference an exception.  A dotted name may be used.

.. rst:role:: py:obj

   Reference an object of unspecified type.  Useful e.g. as the
   :confval:`default_role`.

   .. versionadded:: 0.4


Target specification
^^^^^^^^^^^^^^^^^^^^

The target can be specified as a fully qualified name
(e.g. ``:py:meth:`my_module.MyClass.my_method```)
or any shortened version
(e.g. ``:py:meth:`MyClass.my_method``` or ``:py:meth:`my_method```).
See `target resolution`_ for details on the resolution of shortened names.

:ref:`Cross-referencing modifiers <xref-modifiers>` can be applied.
In short:

* You may supply an explicit title and reference target:
  ``:py:mod:`mathematical functions <math>``` will refer to the ``math`` module,
  but the link text will be "mathematical functions".

* If you prefix the content with an exclamation mark (``!``),
  no reference/hyperlink will be created.

* If you prefix the content with ``~``, the link text will only be the last
  component of the target.
  For example, ``:py:meth:`~queue.Queue.get``` will
  refer to ``queue.Queue.get`` but only display ``get`` as the link text.


Target resolution
^^^^^^^^^^^^^^^^^

A given link target name is resolved to an object using the following strategy:

Names in these roles are searched first without any further qualification,
then with the current module name prepended,
then with the current module and class name (if any) prepended.

If you prefix the name with a dot (``.``), this order is reversed.
For example, in the documentation of Python's :py:mod:`codecs` module,
``:py:func:`open``` always refers to the built-in function,
while ``:py:func:`.open``` refers to :func:`codecs.open`.

A similar heuristic is used to determine whether the name is an attribute of
the currently documented class.

Also, if the name is prefixed with a dot, and no exact match is found, the
target is taken as a suffix and all object names with that suffix are searched.
For example, ``:py:meth:`.TarFile.close``` references the
``tarfile.TarFile.close()`` function, even if the current module is not
``tarfile``.  Since this can get ambiguous, if there is more than one possible
match, you will get a warning from Sphinx.

Note that you can combine the ``~`` and ``.`` prefixes:
``:py:meth:`~.TarFile.close``` will reference the ``tarfile.TarFile.close()``
method, but the visible link caption will only be ``close()``.
