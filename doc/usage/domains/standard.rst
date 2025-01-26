.. highlight:: rst

===================
The Standard Domain
===================

.. versionadded:: 1.0

The so-called "standard" domain collects all markup that doesn't warrant a
domain of its own.  Its directives and roles are not prefixed with a domain
name.

The standard domain is also where custom object descriptions, added using the
:func:`~sphinx.application.Sphinx.add_object_type` API, are placed.

There is a set of directives allowing documenting command-line programs:

.. rst:directive:: .. option:: name args, name args, ...

   Describes a command line argument or switch.  Option argument names should
   be enclosed in angle brackets.  Examples::

      .. option:: dest_dir

         Destination directory.

      .. option:: -m <module>, --module <module>

         Run a module as a script.

   The directive will create cross-reference targets for the given options,
   referenceable by :rst:role:`option` (in the example case, you'd use something
   like ``:option:`dest_dir```, ``:option:`-m```, or ``:option:`--module```).

   .. versionchanged:: 5.3

      One can cross-reference including an option value: ``:option:`--module=foobar```,
      ,``:option:`--module[=foobar]``` or ``:option:`--module foobar```.

   Use :confval:`option_emphasise_placeholders` for parsing of
   "variable part" of a literal text (similarly to the :rst:role:`samp` role).

   ``cmdoption`` directive is a deprecated alias for the ``option`` directive.

.. rst:directive:: .. confval:: name

   .. versionadded:: 7.4

   Describes a configuration value or setting that the documented
   code or program uses or defines.
   Referenceable by :rst:role:`confval`.

   .. rst:directive:option:: type
      :type: text

      Describes the type of the configuration value.
      This is optional, and if specified will be interpreted as reStructuredText.

   .. rst:directive:option:: default
      :type: text

      Describes the default value of the configuration value.
      This is optional, and if specified will be interpreted as reStructuredText.

   Example:

   .. code-block:: rst

      .. confval:: the_answer
         :type: ``int`` (a *number*)
         :default: **42**

         This is a setting that controls the value of the answer.

   will be rendered as follows:

   .. confval:: the_answer
      :no-contents-entry:
      :no-index-entry:
      :type: ``int`` (a *number*)
      :default: **42**

      This is a setting that controls the value of the answer.

.. rst:directive:: .. envvar:: name

   Describes an environment variable that the documented code or program uses
   or defines.  Referenceable by :rst:role:`envvar`.

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

      .. option:: -r <revision>

         Specify the revision to work upon.

   then ``:option:`rm -r``` would refer to the first option, while
   ``:option:`svn -r``` would refer to the second one.

   If ``None`` is passed to the argument, the directive will reset the
   current program name.

   The program name may contain spaces (in case you want to document
   subcommands like ``svn add`` and ``svn commit`` separately).

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
