.. highlight:: rest

:mod:`sphinx.ext.autodoc` -- Include documentation from docstrings
==================================================================

.. module:: sphinx.ext.autodoc
   :synopsis: Include documentation from docstrings.

.. index:: pair: automatic; documentation
           single: docstring

This extension can import the modules you are documenting, and pull in
documentation from docstrings in a semi-automatic way.

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

   If you want to automatically document members, there's a ``members``
   option::

      .. autoclass:: Noodle
         :members:

   will document all non-private member functions and properties (that is, those
   whose name doesn't start with ``_``), while ::

      .. autoclass:: Noodle
         :members: eat, slurp

   will document exactly the specified members.

   Members without docstrings will be left out, unless you give the
   ``undoc-members`` flag option.

   The "auto" directives can also contain content of their own, it will be
   inserted into the resulting non-auto directive source after the docstring
   (but before any automatic member documentation).

   Therefore, you can also mix automatic and non-automatic member documentation,
   like so::

      .. autoclass:: Noodle
         :members: eat, slurp

         .. method:: boil(time=10)

            Boil the noodle *time* minutes.

   .. note::

      In an :dir:`automodule` directive with the ``members`` option set, only
      module members whose ``__module__`` attribute is equal to the module name
      as given to ``automodule`` will be documented.  This is to prevent
      documentation of imported classes or functions.


.. directive:: autofunction
               automethod
               autoattribute

   These work exactly like :dir:`autoclass` etc., but do not offer the options
   used for automatic member documentation.


There's also one new config value that you can set:

.. confval:: automodule_skip_lines

   This value (whose default is ``0``) can be used to skip an amount of lines in
   every module docstring that is processed by an :dir:`automodule` directive.
   This is provided because some projects like to put headings in the module
   docstring, which would then interfere with your sectioning, or automatic
   fields with version control tags, that you don't want to put in the generated
   documentation.
