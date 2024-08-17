.. highlight:: rst

.. _ext-autodoc:

:mod:`sphinx.ext.autodoc` -- Include documentation from docstrings
==================================================================

.. module:: sphinx.ext.autodoc
   :synopsis: Include documentation from docstrings.

.. index:: pair: automatic; documentation
           single: docstring

This extension can import the modules you are documenting, and pull in
documentation from docstrings in a semi-automatic way.

.. warning::

   :mod:`~sphinx.ext.autodoc` **imports** the modules to be documented.  If any
   modules have side effects on import, these will be executed by ``autodoc``
   when ``sphinx-build`` is run.

   If you document scripts (as opposed to library modules), make sure their main
   routine is protected by a ``if __name__ == '__main__'`` condition.

For this to work, the docstrings must of course be written in correct
reStructuredText.  You can then use all of the usual Sphinx markup in the
docstrings, and it will end up correctly in the documentation.  Together with
hand-written documentation, this technique eases the pain of having to maintain
two locations for documentation, while at the same time avoiding
auto-generated-looking pure API documentation.

If you prefer `NumPy`_ or `Google`_ style docstrings over reStructuredText,
you can also enable the :mod:`napoleon <sphinx.ext.napoleon>` extension.
:mod:`napoleon <sphinx.ext.napoleon>` is a preprocessor that converts your
docstrings to correct reStructuredText before :mod:`autodoc` processes them.

.. _Google: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _NumPy: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard

Getting started
---------------

Setup
.....
Activate the plugin by adding ``'sphinx.ext.autodoc'`` to the :confval:`extensions`
in your :file:`conf.py`::

   extensions = [
       ...
       'sphinx.ext.autodoc',
   ]

Ensuring the code can be imported
.................................

:mod:`~sphinx.ext.autodoc` analyses the code and docstrings by introspection after
importing the modules. For importing to work, you have to make sure that your
modules can be found by Sphinx and that dependencies can be resolved (if your
module does ``import foo``, but ``foo`` is not available in the python environment
that Sphinx runs in, your module import will fail).

There are two ways to ensure this:

1. Use an environment that contains your package and Sphinx. This can e.g. be your
   local dev environment (with an editable install), or an environment in CI in
   which you install Sphinx and your package. The regular installation process
   ensures that your package can be found by Sphinx and that all dependencies are
   available.

2. It is alternatively possible to patch the Sphinx run so that it can operate
   directly on the sources; e.g. if you want to be able to do a Sphinx build from a
   source checkout.

   - Patch :data:`sys.path` in your Sphinx :file:`conf.py` to include the folder of
     your sources. E.g. if you have a repository structure with :file:`doc/conf.py`
     and your package is at :file:`src/mypackage`, then you should add::

        sys.path.insert(0, os.path.abspath('../src'))

     to your :file:`conf.py`.

   - To cope with missing dependencies, specify the missing modules in
     :confval:`autodoc_mock_imports`.

Usage
.....

You can now use the :ref:`autodoc-directives` to add formatted documentation for
Python code elements like functions, classes, modules, etc. For example, to document
the function ``io.open()``, reading its signature and docstring from the source file,
you'd write ::

   .. autofunction:: io.open

You can also document whole classes or even modules automatically, using member
options for the auto directives, like ::

   .. automodule:: io
      :members:

.. _autodoc-directives:

Directives
----------

:mod:`autodoc` provides several directives that are versions of the usual
:rst:dir:`py:module`, :rst:dir:`py:class` and so forth.  On parsing time, they
import the corresponding module and extract the docstring of the given objects,
inserting them into the page source under a suitable :rst:dir:`py:module`,
:rst:dir:`py:class` etc.  directive.

.. note::

   Just as :rst:dir:`py:class` respects the current :rst:dir:`py:module`,
   :rst:dir:`autoclass` will also do so.  Likewise, :rst:dir:`automethod` will
   respect the current :rst:dir:`py:class`.


.. rst:directive:: automodule
                   autoclass
                   autoexception

   Document a module, class or exception.  All three directives will by default
   only insert the docstring of the object itself::

      .. autoclass:: Noodle

   will produce source like this::

      .. class:: Noodle

         Noodle's docstring.

   The "auto" directives can also contain content of their own, it will be
   inserted into the resulting non-auto directive source after the docstring
   (but before any automatic member documentation).

   Therefore, you can also mix automatic and non-automatic member documentation,
   like so::

      .. autoclass:: Noodle
         :members: eat, slurp

         .. method:: boil(time=10)

            Boil the noodle *time* minutes.

   .. rubric:: Options

   .. rst:directive:option:: members
      :type: no value or comma separated list

      If set, autodoc will generate document for the members of the target
      module, class or exception.

      For example::

        .. automodule:: noodle
           :members:

      will document all module members (recursively), and ::

        .. autoclass:: Noodle
           :members:

      will document all class member methods and properties.

      By default, autodoc will not generate document for the members that are
      private, not having docstrings, inherited from super class, or special
      members.

      For modules, ``__all__`` will be respected when looking for members unless
      you give the ``ignore-module-all`` flag option.  Without
      ``ignore-module-all``, the order of the members will also be the order in
      ``__all__``.

      You can also give an explicit list of members; only these will then be
      documented::

        .. autoclass:: Noodle
           :members: eat, slurp

   .. rst:directive:option:: undoc-members
      :type: no value

      If set, autodoc will also generate document for the members not having
      docstrings::

        .. automodule:: noodle
           :members:
           :undoc-members:

   .. rst:directive:option:: private-members
      :type: no value or comma separated list

      If set, autodoc will also generate document for the private members
      (that is, those named like ``_private`` or ``__private``)::

        .. automodule:: noodle
           :members:
           :private-members:

      It can also take an explicit list of member names to be documented as
      arguments::

        .. automodule:: noodle
           :members:
           :private-members: _spicy, _garlickly

      .. versionadded:: 1.1
      .. versionchanged:: 3.2
         The option can now take arguments.

   .. rst:directive:option:: special-members
      :type: no value or comma separated list

      If set, autodoc will also generate document for the special members
      (that is, those named like ``__special__``)::

        .. autoclass:: my.Class
           :members:
           :special-members:

      It can also take an explicit list of member names to be documented as
      arguments::

        .. autoclass:: my.Class
           :members:
           :special-members: __init__, __name__

      .. versionadded:: 1.1

      .. versionchanged:: 1.2
         The option can now take arguments

   **Options and advanced usage**

   * If you want to make the ``members`` option (or other options described
     below) the default, see :confval:`autodoc_default_options`.

     .. tip::

        You can use a negated form, :samp:`'no-{flag}'`, as an option of
        autodoc directive, to disable it temporarily.  For example::

           .. automodule:: foo
              :no-undoc-members:

     .. tip::

        You can use autodoc directive options to temporarily override or
        extend default options which takes list as an input. For example::

           .. autoclass:: Noodle
              :members: eat
              :private-members: +_spicy, _garlickly

     .. versionchanged:: 3.5
        The default options can be overridden or extended temporarily.

   * autodoc considers a member private if its docstring contains
     ``:meta private:`` in its :ref:`info-field-lists`.
     For example:

     .. code-block:: python

        def my_function(my_arg, my_other_arg):
            """blah blah blah

            :meta private:
            """

     .. versionadded:: 3.0

   * autodoc considers a member public if its docstring contains
     ``:meta public:`` in its :ref:`info-field-lists`, even if it starts with
     an underscore.
     For example:

     .. code-block:: python

        def _my_function(my_arg, my_other_arg):
            """blah blah blah

            :meta public:
            """

     .. versionadded:: 3.1

   * autodoc considers a variable member does not have any default value if its
     docstring contains ``:meta hide-value:`` in its :ref:`info-field-lists`.
     Example:

     .. code-block:: python

        var1 = None  #: :meta hide-value:

     .. versionadded:: 3.5

   * For classes and exceptions, members inherited from base classes will be
     left out when documenting all members, unless you give the
     ``inherited-members`` option, in addition to ``members``::

        .. autoclass:: Noodle
           :members:
           :inherited-members:

     This can be combined with ``undoc-members`` to document *all* available
     members of the class or module.

     It can take an ancestor class not to document inherited members from it.
     By default, members of ``object`` class are not documented.  To show them
     all, give ``None`` to the option.

     For example; If your class ``Foo`` is derived from ``list`` class and
     you don't want to document ``list.__len__()``, you should specify a
     option ``:inherited-members: list`` to avoid special members of list
     class.

     Another example; If your class Foo has ``__str__`` special method and
     autodoc directive has both ``inherited-members`` and ``special-members``,
     ``__str__`` will be documented as in the past, but other special method
     that are not implemented in your class ``Foo``.

     Since v5.0, it can take a comma separated list of ancestor classes.  It
     allows to suppress inherited members of several classes on the module at
     once by specifying the option to :rst:dir:`automodule` directive.

     Note: this will lead to markup errors if the inherited members come from a
     module whose docstrings are not reStructuredText formatted.

     .. versionadded:: 0.3

     .. versionchanged:: 3.0

        It takes an ancestor class name as an argument.

     .. versionchanged:: 5.0

        It takes a comma separated list of ancestor class names.

   * It's possible to override the signature for explicitly documented callable
     objects (functions, methods, classes) with the regular syntax that will
     override the signature gained from introspection::

        .. autoclass:: Noodle(type)

           .. automethod:: eat(persona)

     This is useful if the signature from the method is hidden by a decorator.

     .. versionadded:: 0.4

   * The :rst:dir:`automodule`, :rst:dir:`autoclass` and
     :rst:dir:`autoexception` directives also support a flag option called
     ``show-inheritance``.  When given, a list of base classes will be inserted
     just below the class signature (when used with :rst:dir:`automodule`, this
     will be inserted for every class that is documented in the module).

     .. versionadded:: 0.4

   * All autodoc directives support the ``no-index`` flag option that has the
     same effect as for standard :rst:dir:`py:function` etc. directives: no
     index entries are generated for the documented object (and all
     autodocumented members).

     .. versionadded:: 0.4

   * :rst:dir:`automodule` also recognizes the ``synopsis``, ``platform`` and
     ``deprecated`` options that the standard :rst:dir:`py:module` directive
     supports.

     .. versionadded:: 0.5

   * :rst:dir:`automodule` and :rst:dir:`autoclass` also has an ``member-order``
     option that can be used to override the global value of
     :confval:`autodoc_member_order` for one directive.

     .. versionadded:: 0.6

   * The directives supporting member documentation also have a
     ``exclude-members`` option that can be used to exclude single member names
     from documentation, if all members are to be documented.

     .. versionadded:: 0.6

   * In an :rst:dir:`automodule` directive with the ``members`` option set, only
     module members whose ``__module__`` attribute is equal to the module name
     as given to ``automodule`` will be documented.  This is to prevent
     documentation of imported classes or functions.  Set the
     ``imported-members`` option if you want to prevent this behavior and
     document all available members.  Note that attributes from imported modules
     will not be documented, because attribute documentation is discovered by
     parsing the source file of the current module.

     .. versionadded:: 1.2

   * Add a list of modules in the :confval:`autodoc_mock_imports` to prevent
     import errors to halt the building process when some external dependencies
     are not importable at build time.

     .. versionadded:: 1.3

   * As a hint to autodoc extension, you can put a ``::`` separator in between
     module name and object name to let autodoc know the correct module name if
     it is ambiguous. ::

        .. autoclass:: module.name::Noodle

   * :rst:dir:`autoclass` also recognizes the ``class-doc-from`` option that
     can be used to override the global value of :confval:`autoclass_content`.

     .. versionadded:: 4.1

.. rst:directive:: autofunction
                   autodecorator
                   autodata
                   automethod
                   autoattribute
                   autoproperty

   These work exactly like :rst:dir:`autoclass` etc.,
   but do not offer the options used for automatic member documentation.

   :rst:dir:`autodata` and :rst:dir:`autoattribute` support the ``annotation``
   option.  The option controls how the value of variable is shown.  If specified
   without arguments, only the name of the variable will be printed, and its value
   is not shown::

      .. autodata:: CD_DRIVE
         :annotation:

   If the option specified with arguments, it is printed after the name as a value
   of the variable::

      .. autodata:: CD_DRIVE
         :annotation: = your CD device name

   By default, without ``annotation`` option, Sphinx tries to obtain the value of
   the variable and print it after the name.

   The ``no-value`` option can be used instead of a blank ``annotation`` to show the
   type hint but not the value::

      .. autodata:: CD_DRIVE
         :no-value:

   If both the ``annotation`` and ``no-value`` options are used, ``no-value`` has no
   effect.

   For module data members and class attributes, documentation can either be put
   into a comment with special formatting (using a ``#:`` to start the comment
   instead of just ``#``), or in a docstring *after* the definition.  Comments
   need to be either on a line of their own *before* the definition, or
   immediately after the assignment *on the same line*.  The latter form is
   restricted to one line only.

   This means that in the following class definition, all attributes can be
   autodocumented::

      class Foo:
          """Docstring for class Foo."""

          #: Doc comment for class attribute Foo.bar.
          #: It can have multiple lines.
          bar = 1

          flox = 1.5   #: Doc comment for Foo.flox. One line only.

          baz = 2
          """Docstring for class attribute Foo.baz."""

          def __init__(self):
              #: Doc comment for instance attribute qux.
              self.qux = 3

              self.spam = 4
              """Docstring for instance attribute spam."""

   .. versionchanged:: 0.6
      :rst:dir:`autodata` and :rst:dir:`autoattribute` can now extract
      docstrings.
   .. versionchanged:: 1.1
      Comment docs are now allowed on the same line after an assignment.
   .. versionchanged:: 1.2
      :rst:dir:`autodata` and :rst:dir:`autoattribute` have an ``annotation``
      option.
   .. versionchanged:: 2.0
      :rst:dir:`autodecorator` added.
   .. versionchanged:: 2.1
      :rst:dir:`autoproperty` added.
   .. versionchanged:: 3.4
      :rst:dir:`autodata` and :rst:dir:`autoattribute` now have a ``no-value``
      option.

   .. note::

      If you document decorated functions or methods, keep in mind that autodoc
      retrieves its docstrings by importing the module and inspecting the
      ``__doc__`` attribute of the given function or method.  That means that if
      a decorator replaces the decorated function with another, it must copy the
      original ``__doc__`` to the new function.


Configuration
-------------

There are also config values that you can set:

.. confval:: autoclass_content

   This value selects what content will be inserted into the main body of an
   :rst:dir:`autoclass` directive.  The possible values are:

   ``"class"``
      Only the class' docstring is inserted.  This is the default.  You can
      still document ``__init__`` as a separate method using
      :rst:dir:`automethod` or the ``members`` option to :rst:dir:`autoclass`.
   ``"both"``
      Both the class' and the ``__init__`` method's docstring are concatenated
      and inserted.
   ``"init"``
      Only the ``__init__`` method's docstring is inserted.

   .. versionadded:: 0.3

   If the class has no ``__init__`` method or if the ``__init__`` method's
   docstring is empty, but the class has a ``__new__`` method's docstring,
   it is used instead.

   .. versionadded:: 1.4

.. confval:: autodoc_class_signature

   This value selects how the signature will be displayed for the class defined
   by :rst:dir:`autoclass` directive.  The possible values are:

   ``"mixed"``
      Display the signature with the class name.
   ``"separated"``
      Display the signature as a method.

   The default is ``"mixed"``.

   .. versionadded:: 4.1

.. confval:: autodoc_member_order

   This value selects if automatically documented members are sorted
   alphabetical (value ``'alphabetical'``), by member type (value
   ``'groupwise'``) or by source order (value ``'bysource'``).  The default is
   alphabetical.

   Note that for source order, the module must be a Python module with the
   source code available.

   .. versionadded:: 0.6
   .. versionchanged:: 1.0
      Support for ``'bysource'``.

.. confval:: autodoc_default_flags

   This value is a list of autodoc directive flags that should be automatically
   applied to all autodoc directives.  The supported flags are ``'members'``,
   ``'undoc-members'``, ``'private-members'``, ``'special-members'``,
   ``'inherited-members'``, ``'show-inheritance'``, ``'ignore-module-all'``
   and ``'exclude-members'``.

   .. versionadded:: 1.0

   .. deprecated:: 1.8

      Integrated into :confval:`autodoc_default_options`.

.. confval:: autodoc_default_options

   The default options for autodoc directives.  They are applied to all autodoc
   directives automatically.  It must be a dictionary which maps option names
   to the values.  For example::

       autodoc_default_options = {
           'members': 'var1, var2',
           'member-order': 'bysource',
           'special-members': '__init__',
           'undoc-members': True,
           'exclude-members': '__weakref__'
       }

   Setting ``None`` or ``True`` to the value is equivalent to giving only the
   option name to the directives.

   The supported options are ``'members'``, ``'member-order'``,
   ``'undoc-members'``, ``'private-members'``, ``'special-members'``,
   ``'inherited-members'``, ``'show-inheritance'``, ``'ignore-module-all'``,
   ``'imported-members'``, ``'exclude-members'``, ``'class-doc-from'`` and
   ``'no-value'``.

   .. versionadded:: 1.8

   .. versionchanged:: 2.0
      Accepts ``True`` as a value.

   .. versionchanged:: 2.1
      Added ``'imported-members'``.

   .. versionchanged:: 4.1
      Added ``'class-doc-from'``.

   .. versionchanged:: 4.5
      Added ``'no-value'``.

.. confval:: autodoc_docstring_signature

   Functions imported from C modules cannot be introspected, and therefore the
   signature for such functions cannot be automatically determined.  However, it
   is an often-used convention to put the signature into the first line of the
   function's docstring.

   If this boolean value is set to ``True`` (which is the default), autodoc will
   look at the first line of the docstring for functions and methods, and if it
   looks like a signature, use the line as the signature and remove it from the
   docstring content.

   autodoc will continue to look for multiple signature lines,
   stopping at the first line that does not look like a signature.
   This is useful for declaring overloaded function signatures.

   .. versionadded:: 1.1
   .. versionchanged:: 3.1

      Support overloaded signatures

   .. versionchanged:: 4.0

      Overloaded signatures do not need to be separated by a backslash

.. confval:: autodoc_mock_imports

   This value contains a list of modules to be mocked up. This is useful when
   some external dependencies are not met at build time and break the building
   process. You may only specify the root package of the dependencies
   themselves and omit the sub-modules:

   .. code-block:: python

      autodoc_mock_imports = ["django"]

   Will mock all imports under the ``django`` package.

   .. versionadded:: 1.3

   .. versionchanged:: 1.6
      This config value only requires to declare the top-level modules that
      should be mocked.

.. confval:: autodoc_typehints

   This value controls how to represent typehints.  The setting takes the
   following values:

   * ``'signature'`` -- Show typehints in the signature (default)
   * ``'description'`` -- Show typehints as content of the function or method
     The typehints of overloaded functions or methods will still be represented
     in the signature.
   * ``'none'`` -- Do not show typehints
   * ``'both'`` -- Show typehints in the signature and as content of
     the function or method

   Overloaded functions or methods will not have typehints included in the
   description because it is impossible to accurately represent all possible
   overloads as a list of parameters.

   .. versionadded:: 2.1
   .. versionadded:: 3.0

      New option ``'description'`` is added.

   .. versionadded:: 4.1

      New option ``'both'`` is added.

.. confval:: autodoc_typehints_description_target

   This value controls whether the types of undocumented parameters and return
   values are documented when ``autodoc_typehints`` is set to ``description``.

   The default value is ``"all"``, meaning that types are documented for all
   parameters and return values, whether they are documented or not.

   When set to ``"documented"``, types will only be documented for a parameter
   or a return value that is already documented by the docstring.

   With ``"documented_params"``, parameter types will only be annotated if the
   parameter is documented in the docstring. The return type is always
   annotated (except if it is ``None``).

   .. versionadded:: 4.0

   .. versionadded:: 5.0

      New option ``'documented_params'`` is added.

.. confval:: autodoc_type_aliases

   A dictionary for users defined `type aliases`__ that maps a type name to the
   full-qualified object name.  It is used to keep type aliases not evaluated in
   the document.  Defaults to empty (``{}``).

   The type aliases are only available if your program enables :pep:`Postponed
   Evaluation of Annotations (PEP 563) <563>` feature via ``from __future__ import
   annotations``.

   For example, there is code using a type alias::

     from __future__ import annotations

     AliasType = Union[List[Dict[Tuple[int, str], Set[int]]], Tuple[str, List[str]]]

     def f() -> AliasType:
         ...

   If ``autodoc_type_aliases`` is not set, autodoc will generate internal mark-up
   from this code as following::

     .. py:function:: f() -> Union[List[Dict[Tuple[int, str], Set[int]]], Tuple[str, List[str]]]

        ...

   If you set ``autodoc_type_aliases`` as
   ``{'AliasType': 'your.module.AliasType'}``, it generates the following document
   internally::

     .. py:function:: f() -> your.module.AliasType:

        ...

   .. __: https://mypy.readthedocs.io/en/latest/kinds_of_types.html#type-aliases
   .. versionadded:: 3.3

.. confval:: autodoc_typehints_format

   This value controls the format of typehints.  The setting takes the
   following values:

   * ``'fully-qualified'`` -- Show the module name and its name of typehints
   * ``'short'`` -- Suppress the leading module names of the typehints
     (e.g. ``io.StringIO`` -> ``StringIO``)  (default)

   .. versionadded:: 4.4

   .. versionchanged:: 5.0

      The default setting was changed to ``'short'``

.. confval:: autodoc_preserve_defaults

   If True, the default argument values of functions will be not evaluated on
   generating document.  It preserves them as is in the source code.

   .. versionadded:: 4.0

      Added as an experimental feature.  This will be integrated into autodoc core
      in the future.

.. confval:: autodoc_warningiserror

   This value controls the behavior of :option:`sphinx-build --fail-on-warning`
   during importing modules.
   If ``False`` is given, autodoc forcedly suppresses the error if the imported
   module emits warnings.  By default, ``True``.

   .. versionchanged:: 8.1
      This option now has no effect as :option:`!--fail-on-warning`
      no longer exits early.

.. confval:: autodoc_inherit_docstrings

   This value controls the docstrings inheritance.
   If set to True the docstring for classes or methods, if not explicitly set,
   is inherited from parents.

   The default is ``True``.

   .. versionadded:: 1.7

.. confval:: suppress_warnings
   :no-index:

   :mod:`autodoc` supports to suppress warning messages via
   :confval:`suppress_warnings`.  It allows following warnings types in
   addition:

   * autodoc
   * autodoc.import_object


Docstring preprocessing
-----------------------

autodoc provides the following additional events:

.. event:: autodoc-process-docstring (app, what, name, obj, options, lines)

   .. versionadded:: 0.4

   Emitted when autodoc has read and processed a docstring.  *lines* is a list
   of strings -- the lines of the processed docstring -- that the event handler
   can modify **in place** to change what Sphinx puts into the output.

   :param app: the Sphinx application object
   :param what: the type of the object which the docstring belongs to (one of
      ``"module"``, ``"class"``, ``"exception"``, ``"function"``, ``"method"``,
      ``"attribute"``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param options: the options given to the directive: an object with attributes
      ``inherited_members``, ``undoc_members``, ``show_inheritance`` and
      ``no-index`` that are true if the flag option of same name was given to the
      auto directive
   :param lines: the lines of the docstring, see above

.. event:: autodoc-before-process-signature (app, obj, bound_method)

   .. versionadded:: 2.4

   Emitted before autodoc formats a signature for an object. The event handler
   can modify an object to change its signature.

   :param app: the Sphinx application object
   :param obj: the object itself
   :param bound_method: a boolean indicates an object is bound method or not

.. event:: autodoc-process-signature (app, what, name, obj, options, signature, return_annotation)

   .. versionadded:: 0.5

   Emitted when autodoc has formatted a signature for an object. The event
   handler can return a new tuple ``(signature, return_annotation)`` to change
   what Sphinx puts into the output.

   :param app: the Sphinx application object
   :param what: the type of the object which the docstring belongs to (one of
      ``"module"``, ``"class"``, ``"exception"``, ``"function"``, ``"method"``,
      ``"attribute"``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param options: the options given to the directive: an object with attributes
      ``inherited_members``, ``undoc_members``, ``show_inheritance`` and
      ``no-index`` that are true if the flag option of same name was given to the
      auto directive
   :param signature: function signature, as a string of the form
      ``"(parameter_1, parameter_2)"``, or ``None`` if introspection didn't
      succeed and signature wasn't specified in the directive.
   :param return_annotation: function return annotation as a string of the form
      ``" -> annotation"``, or ``None`` if there is no return annotation

The :mod:`sphinx.ext.autodoc` module provides factory functions for commonly
needed docstring processing in event :event:`autodoc-process-docstring`:

.. autofunction:: cut_lines
.. autofunction:: between

.. event:: autodoc-process-bases (app, name, obj, options, bases)

   Emitted when autodoc has read and processed a class to determine the
   base-classes.  *bases* is a list of classes that the event handler can
   modify **in place** to change what Sphinx puts into the output.  It's
   emitted only if ``show-inheritance`` option given.

   :param app: the Sphinx application object
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param options: the options given to the class directive
   :param bases: the list of base classes signature. see above.

   .. versionadded:: 4.1
   .. versionchanged:: 4.3

      ``bases`` can contain a string as a base class name.
      It will be processed as reStructuredText.


Skipping members
----------------

autodoc allows the user to define a custom method for determining whether a
member should be included in the documentation by using the following event:

.. event:: autodoc-skip-member (app, what, name, obj, skip, options)

   .. versionadded:: 0.5

   Emitted when autodoc has to decide whether a member should be included in the
   documentation.  The member is excluded if a handler returns ``True``.  It is
   included if the handler returns ``False``.

   If more than one enabled extension handles the ``autodoc-skip-member``
   event, autodoc will use the first non-``None`` value returned by a handler.
   Handlers should return ``None`` to fall back to the skipping behavior of
   autodoc and other enabled extensions.

   :param app: the Sphinx application object
   :param what: the type of the object which the docstring belongs to (one of
      ``"module"``, ``"class"``, ``"exception"``, ``"function"``, ``"method"``,
      ``"attribute"``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param skip: a boolean indicating if autodoc will skip this member if the
      user handler does not override the decision
   :param options: the options given to the directive: an object with attributes
      ``inherited_members``, ``undoc_members``, ``show_inheritance`` and
      ``no-index`` that are true if the flag option of same name was given to the
      auto directive
