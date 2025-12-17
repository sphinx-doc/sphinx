.. _ext-autodoc:

:mod:`sphinx.ext.autodoc` -- Include documentation from docstrings
==================================================================

.. py:module:: sphinx.ext.autodoc
   :synopsis: Include documentation from docstrings.

.. index:: pair: automatic; documentation
           single: docstring

.. role:: code-py(code)
   :language: Python

This extension can import the modules you are documenting,
and pull in documentation from docstrings in a semi-automatic way.

.. warning::

   :mod:`~sphinx.ext.autodoc` **imports** the modules to be documented.
   If any modules have side effects on import,
   these will be executed by ``autodoc`` when :program:`sphinx-build` is run.

   If you document scripts (as opposed to library modules),
   make sure that the main routine is protected by
   an ``if __name__ == '__main__'`` condition.

For this to work, the docstrings must of course be written in correct
reStructuredText.
You can then use all of the usual Sphinx markup in the docstrings,
and it will end up correctly in the documentation.
Together with hand-written documentation, this technique eases
the pain of having to maintain two locations for documentation,
while at the same time avoiding auto-generated-looking pure API documentation.

If you prefer `NumPy`_ or `Google`_ style docstrings over reStructuredText,
you can also enable the :mod:`napoleon <sphinx.ext.napoleon>` extension.
:mod:`!napoleon` is a preprocessor that converts docstrings
to correct reStructuredText before ``autodoc`` processes them.

.. _Google: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _NumPy: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard


Getting started
---------------


Setup
^^^^^

Activate the plugin by adding ``'sphinx.ext.autodoc'`` to
the :confval:`extensions` list in :file:`conf.py`:

.. code-block:: python

   extensions = [
       ...
       'sphinx.ext.autodoc',
   ]


Ensuring the code can be imported
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:mod:`~sphinx.ext.autodoc` analyses the code and docstrings
by introspection after **importing the modules**.
For importing to work, you have to make sure that your modules can be found
by Sphinx and that dependencies can be resolved
(if your module does ``import foo``, but ``foo`` is not available
in the python environment that Sphinx runs in, your module import will fail).

There are two ways to ensure this:

1. Use an environment that contains your package and Sphinx.
   This can e.g. be your local development environment (with an editable install),
   or an environment in CI in which you install Sphinx and your package.
   The regular installation process ensures that your package can be found
   by Sphinx and that all dependencies are available.

2. It is alternatively possible to patch the Sphinx run so that it can operate
   directly on the sources;
   e.g. if you want to be able to do a Sphinx build from a source checkout.

   * Patch :data:`sys.path` in :file:`conf.py` to include your source path.
     For example if you have a repository structure with :file:`doc/conf.py`
     and your package is at :file:`src/my_package`,
     then you should add the following to your :file:`conf.py`.

     .. code-block:: python

        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path('..', 'src').resolve()))

   * To cope with missing dependencies, specify the missing modules in
     the :confval:`autodoc_mock_imports` setting.


Usage
^^^^^

You can now use the :ref:`autodoc-directives` to add formatted documentation
for Python code elements like functions, classes, modules, etc.
For example, to document the function ``io.open()``,
reading its signature and docstring from the source file, you'd write:

.. code-block:: rst

   .. autofunction:: io.open

You can also document whole classes or even modules automatically,
using member options for the auto directives, like:

.. code-block:: rst

   .. automodule:: io
      :members:

.. tip::
   As a hint to autodoc extension, you can put a ``::`` separator
   between the module name and the object name
   to let autodoc know the correct module, if it is ambiguous:

   .. code-block:: rst

      .. autoclass:: module.name::Noodle


Marking objects as public or private
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


.. _doc-comment:

Doc comments and docstrings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python has no built-in support for docstrings for
module data members or class attributes.
To allow documenting these, ``autodoc`` recognises a special format of
:ref:`comment <python:comments>` called a 'doc comment' or 'documentation comment'.

These comments start with a colon and an optional space character,
``'#:'`` or ``'#: '``.
To be recognised, the comments must appear either on the same line
as the variable or on one or more lines before the variable.
Multi-line doc-comments must always  appear on the lines before the
variable's definition.

For example, all three of the following variables have valid doc-comments:

.. code-block:: python

   egg_and_spam = 1.50  #: A simple meal

   #: Spam! Lovely spam! Lovely spam!
   egg_bacon_sausage_and_spam = 2.49

   #: Truly gourmet cuisine for madam; Lobster Thermidor
   #: aux Crevettes with a mornay sauce garnished with
   #: truffle pate, brandy and a fried egg on top and spam.
   lobster_thermidor = 35.00

Alternatively, ``autodoc`` can recognise a docstring
on the line immediately following the definition.

In the the following class definition,
all attributes have documentation recognised by ``autodoc``:

.. code-block:: python

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


.. _autodoc-directives:

Directives
----------

:mod:`autodoc` provides several directives that are versions of
the usual :rst:dir:`py:module`, :rst:dir:`py:class` and so forth.
On parsing time, they import the corresponding module
and extract the docstring of the given objects,
inserting them into the page source under a suitable
:rst:dir:`py:module`, :rst:dir:`py:class` etc. directive.

.. note::

   Just as :rst:dir:`py:class` respects the current
   :rst:dir:`py:module`, :rst:dir:`autoclass` will also do so.
   Likewise, :rst:dir:`automethod` will respect the current :rst:dir:`py:class`.


Default directive options
^^^^^^^^^^^^^^^^^^^^^^^^^

To make any of the options described below the default,
use the :confval:`autodoc_default_options` dictionary in :file:`conf.py`.

If using defaults for the ``:members:``, ``:exclude-members:``,
``:private-members:``, or ``:special-members:`` options,
setting the option on a directive will override the default.
Instead, to extend the default list with the per-directive option,
the list may be prepended with a plus sign (``+``),
as follows:

.. code-block:: rst

   .. autoclass:: Noodle
      :members: eat
      :private-members: +_spicy, _garlickly

.. tip::
   If using :confval:`autodoc_default_options`,
   the defaults can be disabled per-directive with the negated form,
   :samp:`:no-{option}:` as an option of the directive
   For example:

   .. code-block:: rst

      .. automodule:: foo
         :no-undoc-members:


Automatically document modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rst:directive:: automodule

   Document a module.
   By default, the directive only inserts the docstring of the module itself:

   .. code-block:: rst

      .. automodule:: noodles

   will produce source like this:

   .. code-block:: rst

      .. py:module:: noodles

         The noodles module.

   The directive can also contain content of its own,
   which will be inserted into the resulting non-auto directive source
   after the docstring (but before any automatic member documentation).

   Therefore, you can also mix automatic and non-automatic member documentation,
   as follows:

   .. code-block:: rst

      .. automodule:: noodles
         :members: Noodle

         .. py:function:: boiled_noodle(time=10)

            Create a noodle that has been boiled for *time* minutes.

   .. rubric:: Options

   .. rst:directive:option:: no-index
      :type:

      Do not generate an index entry for the documented module
      or any auto-documented members.

      .. versionadded:: 0.4

   .. rst:directive:option:: no-index-entry
      :type:

      Do not generate an index entry for the documented module
      or any auto-documented members.
      Unlike ``:no-index:``, cross-references are still created.

      .. versionadded:: 8.2

   .. rst:directive:option:: platform: platforms
      :type: comma separated list

      Indicate platforms on which the module is available.
      This is identical to :rst:dir:`py:module`'s ``:platform:`` option.

   .. rst:directive:option:: synopsis: purpose
      :type: text

      A sentence describing the module's purpose.
      This is identical to :rst:dir:`py:module`'s ``:synopsis:`` option.

      .. versionadded:: 0.5

   .. rst:directive:option:: deprecated
      :type:

      Mark a module as deprecated.
      This is identical to :rst:dir:`py:module`'s ``:deprecated:`` option.

      .. versionadded:: 0.5

   .. rst:directive:option:: ignore-module-all
      :type: no value

      Do not use ``__all__`` when analysing the module to document.

      .. versionadded:: 1.7

   .. rubric:: Options for selecting members to document

   .. rst:directive:option:: members
      :type: no value or comma separated list

      Generate automatic documentation for all members of the target module:

      .. code-block:: rst

         .. automodule:: noodles
            :members:

      By default, ``autodoc`` only includes public members
      with a docstring or :ref:`doc-comment <doc-comment>` (``#:``).
      If ``__all__`` exists, it will be used to define which members are public,
      unless the :rst:dir:`:ignore-module-all: <automodule:ignore-module-all>`
      option is set.

      To only document certain members, an explicit comma-separated list
      may be used as the argument to ``:members:``:

      .. code-block:: rst

         .. automodule:: noodles
            :members: Noodle

   .. rst:directive:option:: exclude-members
      :type: comma separated list

      Exclude the given names from the members to document.
      For example:

      .. code-block:: rst

         .. automodule:: noodles
            :members:
            :exclude-members: NoodleBase

      .. versionadded:: 0.6

   .. rst:directive:option:: imported-members
      :type: no value

      To prevent documentation of imported classes or functions,
      in an :rst:dir:`!automodule` directive with the ``members`` option set,
      only module members where the ``__module__`` attribute is equal
      to the module name given to ``automodule`` will be documented.

      Set the ``imported-members`` option if you want to prevent this behavior
      and document all available members.

      Note that attributes from imported modules will not be documented,
      because attribute documentation is discovered by
      parsing the source file of the current module.

      .. versionadded:: 1.2

   .. rst:directive:option:: undoc-members
      :type:

      Generate automatic documentation for members of the target module
      that don't have a docstring or doc-comment.
      For example:

      .. code-block:: rst

         .. automodule:: noodles
            :members:
            :undoc-members:

   .. rst:directive:option:: private-members
      :type: no value or comma separated list

      Generate automatic documentation for private members of the target module.
      This includes names with a leading underscore (e.g. ``_private``)
      and those members explicitly marked as private with ``:meta private:``.

      .. code-block:: rst

         .. automodule:: noodles
            :members:
            :private-members:

      To only document certain private members, an explicit comma-separated list
      may be used as the argument to ``:private-members:``:

      .. code-block:: rst

         .. automodule:: noodles
            :members:
            :private-members: _spicy, _garlickly

      .. versionadded:: 1.1
      .. versionchanged:: 3.2
         The option can now take a comma-separated list of arguments.

   .. rst:directive:option:: special-members
      :type: no value or comma separated list

      Generate automatic documentation for special members of the target module,
      also known as :ref:`'dunder' names <python:specialnames>`.
      This includes all names enclosed with a double-underscore,
      e.g. ``__special__``:

      .. code-block:: rst

         .. automodule:: my.Class
            :members:
            :special-members:

      To only document certain special members, an explicit comma-separated list
      may be used as the argument to ``:special-members:``:

      .. code-block:: rst

         .. automodule:: noodles
            :members:
            :special-members: __version__

      .. versionadded:: 1.1

      .. versionchanged:: 1.2
         The option can now take a comma-separated list of arguments.

   .. rubric:: Options for documented members

   .. rst:directive:option:: member-order
      :type: alphabetical, bysource, or groupwise

      Choose the ordering of automatically documented members
      (default: ``alphabetical``).
      This overrides the :confval:`autodoc_member_order` setting.

      * ``alphabetical``:
        Use simple alphabetical order.
      * ``groupwise``:
        Group by object type (class, function, etc),
        use alphabetical order within groups.
      * ``bysource``:
        Use the order of objects in the module's source.
        The ``__all__`` variable can be used to override this order.

      Note that for source order, the module must be a Python module with the
      source code available.

      .. versionadded:: 0.6
      .. versionchanged:: 1.0
         Support the ``'bysource'`` option.

   .. rst:directive:option:: show-inheritance
      :type: no value

      Enable the :rst:dir:`:show-inheritance: <autoclass:show-inheritance>`
      option for all members of the module,
      if ``:members:`` is enabled.

      .. versionadded:: 0.4


Automatically document classes or exceptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rst:directive:: autoclass
                   autoexception

   Document a class.
   For exception classes, prefer ``.. autoexception::``.
   By default, the directive only inserts the docstring of the class itself:

   .. code-block:: rst

      .. autoclass:: noodles.Noodle

   will produce source like this:

   .. code-block:: rst

      .. py:class:: Noodle

         The Noodle class's docstring.

   The directive can also contain content of its own,
   which will be inserted into the resulting non-auto directive source
   after the docstring (but before any automatic member documentation).

   Therefore, you can also mix automatic and non-automatic member documentation,
   as follows:

   .. code-block:: rst

      .. autoclass:: noodles.Noodle
         :members: eat, slurp

         .. py:method:: boil(time=10)

            Boil the noodle for *time* minutes.

   .. rubric:: Advanced usage

   * It is possible to override the signature for explicitly documented
     callable objects (functions, methods, classes) with the regular syntax
     that will override the signature gained from introspection:

     .. code-block:: rst

        .. autoclass:: noodles.Noodle(type)

           .. automethod:: eat(persona)

     This is useful if the signature from the method is hidden by a decorator.

     .. versionadded:: 0.4

   .. rubric:: Options

   .. rst:directive:option:: no-index
      :type:

      Do not generate an index entry for the documented class
      or any auto-documented members.

      .. versionadded:: 0.4

   .. rst:directive:option:: no-index-entry
      :type:

      Do not generate an index entry for the documented class
      or any auto-documented members.
      Unlike ``:no-index:``, cross-references are still created.

      .. versionadded:: 8.2

   .. rst:directive:option:: class-doc-from
      :type: class, init, or both

      Select which docstring will be used for the main body of the directive.
      This overrides the global value of :confval:`autoclass_content`.
      The possible values are:

      * ``class``:
        Only use the class's docstring.
        The :meth:`!__init__` method can be separately documented
        using the ``:members:`` option or :rst:dir:`automethod`.
      * ``init``:
        Only use the docstring of the :meth:`!__init__` method.
      * ``both``:
        Use both, appending the docstring of the :meth:`!__init__` method
        to the class's docstring.

      If the :meth:`!__init__` method doesn't exist or has a blank docstring,
      ``autodoc`` will attempt to use the :meth:`!__new__` method's docstring,
      if it exists and is not blank.

      .. versionadded:: 4.1

   .. rubric:: Options for selecting members to document

   .. rst:directive:option:: members
      :type: no value or comma separated list

      Generate automatic documentation for all members of the target class:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:

      By default, ``autodoc`` only includes public members
      with a docstring or :ref:`doc-comment <doc-comment>` (``#:``)
      that are attributes of the target class (i.e. not inherited).

      To only document certain members, an explicit comma-separated list
      may be used as the argument to ``:members:``:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members: eat, slurp

   .. rst:directive:option:: exclude-members
      :type: comma separated list

      Exclude the given names from the members to document.
      For example:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :exclude-members: prepare

      .. versionadded:: 0.6

   .. rst:directive:option:: inherited-members
      :type: comma separated list

      To generate automatic documentation for members inherited
      from base classes, use the ``:inherited-members:`` option:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :inherited-members:

      This can be combined with the ``:undoc-members:`` option to generate
      automatic documentation for *all* available members of the class.

      The members of classes listed in the argument to ``:inherited-members:``
      are excluded from the automatic documentation.
      This defaults to :py:class:`python:object` if no argument is provided,
      meaning that members of the ``object`` class are not documented.
      To include these, use ``None`` as the argument.

      For example; If your class ``MyList`` is derived from ``list`` class and
      you don't want to document ``list.__len__()``, you should specify a
      option ``:inherited-members: list`` to avoid special members of list
      class.

      .. note::
         Should any of the inherited members use a format other than
         reStructuredText for their docstrings,
         there may be markup warnings or errors.

      .. versionadded:: 0.3

      .. versionchanged:: 3.0
         ``:inherited-members:`` now takes the name of a base class
         to exclude as an argument.

      .. versionchanged:: 5.0
         A comma separated list of base class names can be used.

   .. rst:directive:option:: undoc-members
      :type: no value

      Generate automatic documentation for members of the target class
      that don't have a docstring or doc-comment.
      For example:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :undoc-members:

   .. rst:directive:option:: private-members
      :type: no value or comma separated list

      Generate automatic documentation for private members of the target class.
      This includes names with a leading underscore (e.g. ``_private``)
      and those members explicitly marked as private with ``:meta private:``.

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :private-members:

      To only document certain private members, an explicit comma-separated list
      may be used as the argument to ``:private-members:``:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :private-members: _spicy, _garlickly

      .. versionadded:: 1.1
      .. versionchanged:: 3.2
         The option can now take arguments.

   .. rst:directive:option:: special-members
      :type: no value or comma separated list

      Generate automatic documentation for special members of the target class,
      also known as :ref:`'dunder' names <python:specialnames>`.
      This includes all names enclosed with a double-underscore,
      e.g. ``__special__``:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :special-members:

      To only document certain special members, an explicit comma-separated list
      may be used as the argument to ``:special-members:``:

      .. code-block:: rst

         .. autoclass:: noodles.Noodle
            :members:
            :special-members: __init__, __name__

      .. versionadded:: 1.1

      .. versionchanged:: 1.2
         The option can now take a comma-separated list of arguments.

   .. rubric:: Options for documented members

   .. rst:directive:option:: member-order
      :type: alphabetical, bysource, or groupwise

      Choose the ordering of automatically documented members
      (default: ``alphabetical``).
      This overrides the :confval:`autodoc_member_order` setting.

      * ``'alphabetical'``:
        Use simple alphabetical order.
      * ``'groupwise'``:
        Group by object type (class, function, etc),
        use alphabetical order within groups.
      * ``'bysource'``:
        Use the order of objects in the module's source.
        The ``__all__`` variable can be used to override this order.

      Note that for source order, the module must be a Python module with the
      source code available.

      .. versionadded:: 0.6
      .. versionchanged:: 1.0
         Support the ``'bysource'`` option.

   .. rst:directive:option:: show-inheritance
      :type: no value

      Insert the class's base classes after the class signature.

      .. versionadded:: 0.4


Automatically document function-like objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rst:directive:: autofunction
                   automethod
                   autoproperty
                   autodecorator

   Document a function, method, property, or decorator.
   By default, the directive only inserts the docstring of the function itself:

   .. code-block:: rst

      .. autofunction:: noodles.average_noodle

   will produce source like this:

   .. code-block:: rst

      .. py:function:: noodles.average_noodle

         The average_noodle function's docstring.

   The directive can also contain content of its own,
   which will be inserted into the resulting non-auto directive source
   after the docstring.

   Therefore, you can also mix automatic and non-automatic documentation,
   as follows:

   .. code-block:: rst

      .. autofunction:: noodles.average_noodle

         .. note:: For more flexibility, use the :py:class:`!Noodle` class.

   .. versionadded:: 2.0
      :rst:dir:`autodecorator`.
   .. versionadded:: 2.1
      :rst:dir:`autoproperty`.

   .. note::

      If you document decorated functions or methods,
      keep in mind that ``autodoc`` retrieves its docstrings
      by importing the module and inspecting the ``__doc__`` attribute
      of the given function or method.
      That means that if a decorator replaces the decorated function with another,
      it must copy the original ``__doc__`` to the new function.

   .. rubric:: Advanced usage

   * It is possible to override the signature for explicitly documented
     callable objects (functions, methods, classes) with the regular syntax
     that will override the signature gained from introspection:

     .. code-block:: rst

        .. autoclass:: Noodle(type)

           .. automethod:: eat(persona)

     This is useful if the signature from the method is hidden by a decorator.

     .. versionadded:: 0.4

   .. rubric:: Options

   .. rst:directive:option:: no-index
      :type:

      Do not generate an index entry for the documented function.

      .. versionadded:: 0.4

   .. rst:directive:option:: no-index-entry
      :type:

      Do not generate an index entry for the documented function.
      Unlike ``:no-index:``, cross-references are still created.

      .. versionadded:: 8.2


Automatically document attributes or data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rst:directive:: autodata
                   autoattribute

   Document a module level variable or constant ('data') or class attribute.
   By default, the directive only inserts the docstring of the variable itself:

   .. code-block:: rst

      .. autodata:: noodles.FLOUR_TYPE

   will produce source like this:

   .. code-block:: rst

      .. py:data:: noodles.FLOUR_TYPE

         The FLOUR_TYPE constant's docstring.

   The directive can also contain content of its own,
   which will be inserted into the resulting non-auto directive source
   after the docstring.

   Therefore, you can also mix automatic and non-automatic member documentation,
   as follows:

   .. code-block:: rst

      .. autodata:: noodles.FLOUR_TYPE

         .. hint:: Cooking time can vary by which flour type is used.

   .. versionchanged:: 0.6
      :rst:dir:`autodata` and :rst:dir:`autoattribute`
      can now extract docstrings.
   .. versionchanged:: 1.1
      Doc-comments are now allowed on the same line of an assignment.

   .. rubric:: Options

   .. rst:directive:option:: no-index
      :type:

      Do not generate an index entry for the documented variable or constant.

      .. versionadded:: 0.4

   .. rst:directive:option:: no-index-entry
      :type:

      Do not generate an index entry for the documented variable or constant.
      Unlike ``:no-index:``, cross-references are still created.

      .. versionadded:: 8.2

   .. rst:directive:option:: annotation: value
      :type: string

      .. versionadded:: 1.2

      By default, ``autodoc`` attempts to obtain the type annotation
      and value of the variable by introspection,
      displaying it after the variable's name.
      To override this, a custom string for the variable's value
      may be used as the argument to ``annotation``.

      For example, if the runtime value of ``FILE_MODE`` is ``0o755``,
      the displayed value will be ``493`` (as ``oct(493) == '0o755'``).
      This can be fixed by setting ``:annotation: = 0o755``.

      If ``:annotation:`` is used without arguments,
      no value or type hint will be shown for the variable.

   .. rst:directive:option:: no-value

      .. versionadded:: 3.4

      To display the type hint of the variable without a value,
      use the ``:no-value:`` option.
      If both the ``:annotation:`` and ``:no-value:`` options are used,
      ``:no-value:`` has no effect.


Automatically document type aliases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rst:directive:: autotype

   .. versionadded:: 9.0

   Document a :pep:`695` type alias (the :keyword:`type` statement).
   By default, the directive only inserts the docstring of the alias itself:

   The directive can also contain content of its own,
   which will be inserted into the resulting non-auto directive source
   after the docstring (but before any automatic member documentation).

   Therefore, you can also mix automatic and non-automatic member documentation.

   .. rubric:: Options

   .. rst:directive:option:: no-index
      :type:

      Do not generate an index entry for the documented class
      or any auto-documented members.

   .. rst:directive:option:: no-index-entry
      :type:

      Do not generate an index entry for the documented class
      or any auto-documented members.
      Unlike ``:no-index:``, cross-references are still created.


Configuration
-------------

There are also config values that you can set:

.. confval:: autodoc_use_legacy_class_based
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If true, autodoc will use the legacy class-based implementation.
   This is the behaviour prior to Sphinx 9.0.
   It is based on the ``Documenter`` class hierarchy.

   This setting is provided for backwards compatibility if your documentation
   or an extension you use uses or monkeypatches the legacy class-based API
   in Python code.
   If this is the case, set ``autodoc_use_legacy_class_based = True``
   in your :file:`conf.py`.
   Please also add a comment to `the tracking issue on GitHub
   <https://github.com/sphinx-doc/sphinx/issues/14089>`__ so that the maintainers
   are aware of your use case, for possible future improvements.

   .. note:: The legacy class-based implementation does not support
             PEP 695 type aliases.

.. confval:: autoclass_content
   :type: :code-py:`str`
   :default: :code-py:`'class'`

   This value selects what content will be inserted into the main body of an
   :rst:dir:`autoclass` directive.  The possible values are:

   ``'class'``
      Only the class' docstring is inserted.  You can
      still document ``__init__`` as a separate method using
      :rst:dir:`automethod` or the ``members`` option to :rst:dir:`autoclass`.
   ``'both'``
      Both the class' and the ``__init__`` method's docstring are concatenated
      and inserted.
   ``'init'``
      Only the ``__init__`` method's docstring is inserted.

   .. versionadded:: 0.3

   If the class has no ``__init__`` method or if the ``__init__`` method's
   docstring is empty, but the class has a ``__new__`` method's docstring,
   it is used instead.

   .. versionadded:: 1.4

.. confval:: autodoc_class_signature
   :type: :code-py:`str`
   :default: :code-py:`'mixed'`

   This value selects how the signature will be displayed for the class defined
   by :rst:dir:`autoclass` directive.  The possible values are:

   ``'mixed'``
      Display the signature with the class name.
   ``'separated'``
      Display the signature as a method.

   .. versionadded:: 4.1

.. confval:: autodoc_member_order
   :type: :code-py:`str`
   :default: :code-py:`'alphabetical'`

   Define the order in which :rst:dir:`automodule` and :rst:dir:`autoclass`
   members are listed. Supported values are:

   * ``'alphabetical'``:
     Use alphabetical order.

   * ``'groupwise'``: order by member type. The order is:

     * for modules, exceptions, classes, functions, data
     * for classes: class methods, static methods, methods,
                    and properties/attributes

     Members are ordered alphabetically within groups.

   * ``'bysource'``:
     Use the order in which the members appear in the source code.
     This requires that the module must be a Python module with the
     source code available.

   .. versionadded:: 0.6
   .. versionchanged:: 1.0
      Support for ``'bysource'``.

.. confval:: autodoc_default_options
   :type: :code-py:`dict[str, str | bool]`
   :default: :code-py:`{}`

   The default options for autodoc directives.  They are applied to all autodoc
   directives automatically.  It must be a dictionary which maps option names
   to the values.  For example:

   .. code-block:: python

       autodoc_default_options = {
           'members': 'var1, var2',
           'member-order': 'bysource',
           'special-members': '__init__',
           'undoc-members': True,
           'exclude-members': '__weakref__'
       }

   Setting ``None`` or ``True`` to the value is equivalent to giving only the
   option name to the directives.

   The supported options are:

   * ``'members'``: See :rst:dir:`automodule:members`.
   * ``'undoc-members'`` See :rst:dir:`automodule:undoc-members`.
   * ``'private-members'``: See :rst:dir:`automodule:private-members`.
   * ``'special-members'``: See :rst:dir:`automodule:special-members`.
   * ``'inherited-members'``: See :rst:dir:`autoclass:inherited-members`.
   * ``'imported-members'``: See :rst:dir:`automodule:imported-members`.
   * ``'exclude-members'``: See :rst:dir:`automodule:exclude-members`.
   * ``'ignore-module-all'``: See :rst:dir:`automodule:ignore-module-all`.
   * ``'member-order'``: See :rst:dir:`automodule:member-order`.
   * ``'show-inheritance'``: See :rst:dir:`autoclass:show-inheritance`.
   * ``'class-doc-from'``: See :rst:dir:`autoclass:class-doc-from`.
   * ``'no-value'``: See :rst:dir:`autodata:no-value`.
   * ``'no-index'``: See :rst:dir:`automodule:no-index`.
   * ``'no-index-entry'``: See :rst:dir:`automodule:no-index-entry`.

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
   :type: :code-py:`bool`
   :default: :code-py:`True`

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
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   This value contains a list of modules to be mocked up. This is useful when
   some external dependencies are not met at build time and break the building
   process. You may only specify the root package of the dependencies
   themselves and omit the sub-modules:

   .. code-block:: python

      autodoc_mock_imports = ['django']

   Will mock all imports under the ``django`` package.

   .. versionadded:: 1.3

   .. versionchanged:: 1.6
      This config value only requires to declare the top-level modules that
      should be mocked.

.. confval:: autodoc_typehints
   :type: :code-py:`str`
   :default: :code-py:`'signature'`

   This value controls how to represent typehints.  The setting takes the
   following values:

   * ``'signature'`` -- Show typehints in the signature
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
   :type: :code-py:`str`
   :default: :code-py:`'all'`

   This value controls whether the types of
   undocumented parameters and return values are documented
   when :confval:`autodoc_typehints` is set to ``'description'``.
   Supported values:

   * ``'all'``:
     Types are documented for all parameters and return values,
     whether they are documented or not.
   * ``'documented'``:
     Types will only be documented for a parameter
     or a return value that is already documented by the docstring.
   * ``'documented_params'``:
     Parameter types will only be annotated if the
     parameter is documented in the docstring. The return type is always
     annotated (except if it is ``None``).

   .. versionadded:: 4.0

   .. versionadded:: 5.0

      New option ``'documented_params'`` is added.

.. confval:: autodoc_type_aliases
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   A dictionary for users defined `type aliases`__ that maps a type name to the
   full-qualified object name.  It is used to keep type aliases not evaluated in
   the document.

   The type aliases are only available if your program enables :pep:`Postponed
   Evaluation of Annotations (PEP 563) <563>` feature via ``from __future__ import
   annotations``.

   For example, there is code using a type alias:

   .. code-block:: python

     from __future__ import annotations

     AliasType = Union[List[Dict[Tuple[int, str], Set[int]]], Tuple[str, List[str]]]

     def f() -> AliasType:
         ...

   If ``autodoc_type_aliases`` is not set, autodoc will generate internal mark-up
   from this code as following:

   .. code-block:: rst

      .. py:function:: f() -> Union[List[Dict[Tuple[int, str], Set[int]]], Tuple[str, List[str]]]

         ...

   If you set ``autodoc_type_aliases`` as
   ``{'AliasType': 'your.module.AliasType'}``, it generates the following document
   internally:

   .. code-block:: rst

      .. py:function:: f() -> your.module.AliasType:

         ...

   .. __: https://mypy.readthedocs.io/en/latest/kinds_of_types.html#type-aliases
   .. versionadded:: 3.3

.. confval:: autodoc_typehints_format
   :type: :code-py:`str`
   :default: :code-py:`'short'`

   This value controls the format of typehints.  The setting takes the
   following values:

   * ``'fully-qualified'`` -- Show the module name and its name of typehints
   * ``'short'`` -- Suppress the leading module names of the typehints
     (e.g. ``io.StringIO`` -> ``StringIO``)

   .. versionadded:: 4.4

   .. versionchanged:: 5.0

      The default setting was changed to ``'short'``

.. confval:: autodoc_preserve_defaults
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If True, the default argument values of functions will be not evaluated on
   generating document.  It preserves them as is in the source code.

   .. versionadded:: 4.0

      Added as an experimental feature.  This will be integrated into autodoc core
      in the future.

.. confval:: autodoc_use_type_comments
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Attempt to read ``# type: ...`` comments from source code
   to supplement missing type annotations, if True.

   This can be disabled if your source code does not use type comments,
   for example if it exclusively uses type annotations or
   does not use type hints of any kind.

   .. versionadded:: 8.2

      Added the option to disable the use of type comments in
      via the new :confval:`!autodoc_use_type_comments` option,
      which defaults to :code-py:`True` for backwards compatibility.
      The default will change to :code-py:`False` in Sphinx 10.

      .. xref RemovedInSphinx10Warning

.. confval:: autodoc_warningiserror
   :type: :code-py:`bool`
   :default: :code-py:`True`

   This value controls the behavior of :option:`sphinx-build --fail-on-warning`
   during importing modules.
   If ``False`` is given, autodoc forcedly suppresses the error if the imported
   module emits warnings.

   .. versionchanged:: 8.1
      This option now has no effect as :option:`!--fail-on-warning`
      no longer exits early.

.. confval:: autodoc_inherit_docstrings
   :type: :code-py:`bool`
   :default: :code-py:`True`

   This value controls the docstrings inheritance.
   If set to True the docstring for classes or methods, if not explicitly set,
   is inherited from parents.

   .. versionadded:: 1.7

.. confval:: suppress_warnings
   :no-index:
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   :mod:`autodoc` supports suppressing warning messages
   via :confval:`suppress_warnings`.
   It defines the following additional warnings types:

   * autodoc
   * autodoc.import_object


Docstring preprocessing
-----------------------

autodoc provides the following additional events:

.. event:: autodoc-process-docstring (app, obj_type, name, obj, options, lines)

   .. versionadded:: 0.4

   Emitted when autodoc has read and processed a docstring.  *lines* is a list
   of strings -- the lines of the processed docstring -- that the event handler
   can modify **in place** to change what Sphinx puts into the output.

   :param app: the Sphinx application object
   :param obj_type: the type of the object which the docstring belongs to (one of
      ``'module'``, ``'class'``, ``'exception'``, ``'function'``, ``'decorator'``,
      ``'method'``, ``'property'``, ``'attribute'``, ``'data'``, or ``'type'``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param options: the options given to the directive: an object with attributes
      corresponding to the options used in the auto directive, e.g.
      ``inherited_members``, ``undoc_members``, or ``show_inheritance``.
   :param lines: the lines of the docstring, see above

.. event:: autodoc-before-process-signature (app, obj, bound_method)

   .. versionadded:: 2.4

   Emitted before autodoc formats a signature for an object. The event handler
   can modify an object to change its signature.

   :param app: the Sphinx application object
   :param obj: the object itself
   :param bound_method: a boolean indicates an object is bound method or not

.. event:: autodoc-process-signature (app, obj_type, name, obj, options, signature, return_annotation)

   .. versionadded:: 0.5

   Emitted when autodoc has formatted a signature for an object. The event
   handler can return a new tuple ``(signature, return_annotation)`` to change
   what Sphinx puts into the output.

   :param app: the Sphinx application object
   :param obj_type: the type of the object which the docstring belongs to (one of
      ``'module'``, ``'class'``, ``'exception'``, ``'function'``, ``'decorator'``,
      ``'method'``, ``'property'``, ``'attribute'``, ``'data'``, or ``'type'``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param options: the options given to the directive: an object with attributes
      corresponding to the options used in the auto directive, e.g.
      ``inherited_members``, ``undoc_members``, or ``show_inheritance``.
   :param signature: function signature, as a string of the form
      ``'(parameter_1, parameter_2)'``, or ``None`` if introspection didn't
      succeed and signature wasn't specified in the directive.
   :param return_annotation: function return annotation as a string of the form
      ``'annotation'``, or ``''`` if there is no return annotation.

The :mod:`sphinx.ext.autodoc` module provides factory functions for commonly
needed docstring processing in event :event:`autodoc-process-docstring`:

.. autofunction:: cut_lines
.. autofunction:: between

.. event:: autodoc-process-bases (app, name, obj, _unused, bases)

   Emitted when autodoc has read and processed a class to determine the
   base-classes.  *bases* is a list of classes that the event handler can
   modify **in place** to change what Sphinx puts into the output.  It's
   emitted only if the ``show-inheritance`` option is given.

   :param app: the Sphinx application object
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param _unused: unused placeholder
   :param bases: the list of base classes signature. see above.

   .. versionadded:: 4.1
   .. versionchanged:: 4.3

      ``bases`` can contain a string as a base class name.
      It will be processed as reStructuredText.


Skipping members
----------------

autodoc allows the user to define a custom method for determining whether a
member should be included in the documentation by using the following event:

.. event:: autodoc-skip-member (app, obj_type, name, obj, skip, options)

   .. versionadded:: 0.5

   Emitted when autodoc has to decide whether a member should be included in the
   documentation.  The member is excluded if a handler returns ``True``.  It is
   included if the handler returns ``False``.

   If more than one enabled extension handles the ``autodoc-skip-member``
   event, autodoc will use the first non-``None`` value returned by a handler.
   Handlers should return ``None`` to fall back to the skipping behavior of
   autodoc and other enabled extensions.

   :param app: the Sphinx application object
   :param obj_type: the type of the object which the docstring belongs to (one of
      ``'module'``, ``'class'``, ``'exception'``, ``'function'``, ``'decorator'``,
      ``'method'``, ``'property'``, ``'attribute'``, ``'data'``, or ``'type'``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param skip: a boolean indicating if autodoc will skip this member if the
      user handler does not override the decision
   :param options: the options given to the directive: an object with attributes
      corresponding to the options used in the auto directive, e.g.
      ``inherited_members``, ``undoc_members``, or ``show_inheritance``.
