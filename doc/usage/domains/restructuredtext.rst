.. highlight:: rst

===========================
The reStructuredText Domain
===========================

.. versionadded:: 1.0

The reStructuredText domain (name **rst**) provides the following directives:

.. rst:directive:: .. rst:directive:: name

   Describes a reStructuredText directive.
   The *name* can be a single directive name or actual directive syntax
   (`..` prefix and `::` suffix) with arguments that will be rendered differently.
   For example::

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.

   will be rendered as:

   .. rst:directive:: foo
      :no-contents-entry:
      :no-index-entry:

      Foo description.

   .. rst:directive:: .. bar:: baz
      :no-contents-entry:
      :no-index-entry:

      Bar description.

.. rst:directive:: .. rst:directive:option:: name

   Describes an option for reStructuredText directive.  The *name* can be a single option
   name or option name with arguments which separated with colon (``:``).
   For example::

       .. rst:directive:: toctree

          .. rst:directive:option:: caption: caption of ToC

          .. rst:directive:option:: glob

   will be rendered as:

   .. rst:directive:: toctree
      :no-index:

      .. rst:directive:option:: caption: caption of ToC
         :no-index:

      .. rst:directive:option:: glob
         :no-index:

   .. rubric:: options

   .. rst:directive:option:: type: description of argument
      :type: text

      Describe the type of option value.

      For example::

         .. rst:directive:: toctree

            .. rst:directive:option:: maxdepth
               :type: integer or no value

      .. versionadded:: 2.1

.. rst:directive:: .. rst:role:: name

   Describes a reStructuredText role.  For example::

      .. rst:role:: foo

         Foo description.

   will be rendered as:

   .. rst:role:: foo
      :no-contents-entry:
      :no-index-entry:

      Foo description.

.. _rst-xref-roles:

These roles are provided to refer to the described objects:

.. rst:role:: rst:dir

   Reference directives and directive options. Examples:

   * Use ``:rst:dir:`my-directive``` to reference a directive.
   * Use ``:rst:dir:`my-directive:my-option``` to reference a
     directive option.

.. rst:role:: rst:role

   Reference a role. Example: ``:rst:role:`my-role```.
