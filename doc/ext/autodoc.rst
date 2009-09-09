.. highlight:: rest

:mod:`sphinx.ext.autodoc` -- Include documentation from docstrings
==================================================================

.. module:: sphinx.ext.autodoc
   :synopsis: Include documentation from docstrings.

.. index:: pair: automatic; documentation
           single: docstring

This extension can import the modules you are documenting, and pull in
documentation from docstrings in a semi-automatic way.

.. note::

   For Sphinx (actually, the Python interpreter that executes Sphinx) to find
   your module, it must be importable.  That means that the module or the
   package must be in one of the directories on :data:`sys.path` -- adapt your
   :data:`sys.path` in the configuration file accordingly.

For this to work, the docstrings must of course be written in correct
reStructuredText.  You can then use all of the usual Sphinx markup in the
docstrings, and it will end up correctly in the documentation.  Together with
hand-written documentation, this technique eases the pain of having to maintain
two locations for documentation, while at the same time avoiding
auto-generated-looking pure API documentation.

:mod:`autodoc` provides several directives that are versions of the usual
:dir:`module`, :dir:`class` and so forth.  On parsing time, they import the
corresponding module and extract the docstring of the given objects, inserting
them into the page source under a suitable :dir:`module`, :dir:`class` etc.
directive.

.. note::

   Just as :dir:`class` respects the current :dir:`module`, :dir:`autoclass`
   will also do so, and likewise with :dir:`method` and :dir:`class`.


.. directive:: automodule
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

   **Options and advanced usage**

   * If you want to automatically document members, there's a ``members``
     option::

        .. automodule:: noodle
           :members:

     will document all module members (recursively), and ::

        .. autoclass:: Noodle
           :members:

     will document all non-private member functions and properties (that is,
     those whose name doesn't start with ``_``).

     You can also give an explicit list of members; only these will then be
     documented::

        .. autoclass:: Noodle
           :members: eat, slurp

   * Members without docstrings will be left out, unless you give the
     ``undoc-members`` flag option::

        .. automodule:: noodle
           :members:
           :undoc-members:

   * For classes and exceptions, members inherited from base classes will be
     left out, unless you give the ``inherited-members`` flag option, in
     addition to ``members``::

        .. autoclass:: Noodle
           :members:
           :inherited-members:

     This can be combined with ``undoc-members`` to document *all* available
     members of the class or module.

     Note: this will lead to markup errors if the inherited members come from a
     module whose docstrings are not reST formatted.

     .. versionadded:: 0.3

   * It's possible to override the signature for explicitly documented callable
     objects (functions, methods, classes) with the regular syntax that will
     override the signature gained from introspection::

        .. autoclass:: Noodle(type)

           .. automethod:: eat(persona)

     This is useful if the signature from the method is hidden by a decorator.

     .. versionadded:: 0.4

   * The :dir:`automodule`, :dir:`autoclass` and :dir:`autoexception` directives
     also support a flag option called ``show-inheritance``.  When given, a list
     of base classes will be inserted just below the class signature (when used
     with :dir:`automodule`, this will be inserted for every class that is
     documented in the module).

     .. versionadded:: 0.4

   * All autodoc directives support the ``noindex`` flag option that has the
     same effect as for standard :dir:`function` etc. directives: no index
     entries are generated for the documented object (and all autodocumented
     members).

     .. versionadded:: 0.4

   * :dir:`automodule` also recognizes the ``synopsis``, ``platform`` and
     ``deprecated`` options that the standard :dir:`module` directive supports.

     .. versionadded:: 0.5

   * :dir:`automodule` and :dir:`autoclass` also has an ``member-order`` option
     that can be used to override the global value of
     :confval:`autodoc_member_order` for one directive.

     .. versionadded:: 0.6

   * The directives supporting member documentation also have a
     ``exclude-members`` option that can be used to exclude single member names
     from documentation, if all members are to be documented.

     .. versionadded:: 0.6

   .. note::

      In an :dir:`automodule` directive with the ``members`` option set, only
      module members whose ``__module__`` attribute is equal to the module name
      as given to ``automodule`` will be documented.  This is to prevent
      documentation of imported classes or functions.


.. directive:: autofunction
               autodata
               automethod
               autoattribute

   These work exactly like :dir:`autoclass` etc., but do not offer the options
   used for automatic member documentation.

   For module data members and class attributes, documentation can either be put
   into a special-formatted comment *before* the attribute definition, or in a
   docstring *after* the definition.  This means that in the following class
   definition, both attributes can be autodocumented::

      class Foo:
          """Docstring for class Foo."""

          #: Doc comment for attribute Foo.bar.
          bar = 1

          baz = 2
          """Docstring for attribute Foo.baz."""

   .. versionchanged:: 0.6
      :dir:`autodata` and :dir:`autoattribute` can now extract docstrings.

   .. note::

      If you document decorated functions or methods, keep in mind that autodoc
      retrieves its docstrings by importing the module and inspecting the
      ``__doc__`` attribute of the given function or method.  That means that if
      a decorator replaces the decorated function with another, it must copy the
      original ``__doc__`` to the new function.

      From Python 2.5, :func:`functools.wraps` can be used to create
      well-behaved decorating functions.


There are also new config values that you can set:

.. confval:: autoclass_content

   This value selects what content will be inserted into the main body of an
   :dir:`autoclass` directive.  The possible values are:

   ``"class"``
      Only the class' docstring is inserted.  This is the default.  You can
      still document ``__init__`` as a separate method using :dir:`automethod`
      or the ``members`` option to :dir:`autoclass`.
   ``"both"``
      Both the class' and the ``__init__`` method's docstring are concatenated
      and inserted.
   ``"init"``
      Only the ``__init__`` method's docstring is inserted.

   .. versionadded:: 0.3

.. confval:: autodoc_member_order

   This value selects if automatically documented members are sorted
   alphabetical (value ``'alphabetical'``) or by member type (value
   ``'groupwise'``).  The default is alphabetical.

   .. versionadded:: 0.6


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
      ``noindex`` that are true if the flag option of same name was given to the
      auto directive
   :param lines: the lines of the docstring, see above

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
      ``noindex`` that are true if the flag option of same name was given to the
      auto directive
   :param signature: function signature, as a string of the form
      ``"(parameter_1, parameter_2)"``, or ``None`` if introspection didn't succeed
      and signature wasn't specified in the directive.
   :param return_annotation: function return annotation as a string of the form
      ``" -> annotation"``, or ``None`` if there is no return annotation

The :mod:`sphinx.ext.autodoc` module provides factory functions for commonly
needed docstring processing in event :event:`autodoc-process-docstring`:

.. autofunction:: cut_lines
.. autofunction:: between


Skipping members
----------------

autodoc allows the user to define a custom method for determining whether a
member should be included in the documentation by using the following event:

.. event:: autodoc-skip-member (app, what, name, obj, skip, options)

   .. versionadded:: 0.5

   Emitted when autodoc has to decide whether a member should be included in the
   documentation.  The member is excluded if a handler returns ``True``.  It is
   included if the handler returns ``False``.

   :param app: the Sphinx application object
   :param what: the type of the object which the docstring belongs to (one of
      ``"module"``, ``"class"``, ``"exception"``, ``"function"``, ``"method"``,
      ``"attribute"``)
   :param name: the fully qualified name of the object
   :param obj: the object itself
   :param skip: a boolean indicating if autodoc will skip this member if the user
      handler does not override the decision
   :param options: the options given to the directive: an object with attributes
      ``inherited_members``, ``undoc_members``, ``show_inheritance`` and
      ``noindex`` that are true if the flag option of same name was given to the
      auto directive
