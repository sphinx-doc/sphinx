Docutils markup API
===================

This section describes the API for adding reStructuredText markup elements
(roles and directives).


Roles
-----

Roles follow the interface described below.
They have to be registered by an extension using
:meth:`.Sphinx.add_role` or :meth:`.Sphinx.add_role_to_domain`.


.. code-block:: python

   def role_function(
       role_name: str, raw_source: str, text: str,
       lineno: int, inliner: Inliner,
       options: dict = {}, content: list = [],
   ) -> tuple[list[Node], list[system_message]]:
       elements = []
       messages = []
       return elements, messages

The *options* and *content* parameters are only used for custom roles
created via the :dudir:`role` directive.
The return value is a tuple of two lists,
the first containing the text nodes and elements from the role,
and the second containing any system messages generated.
For more information, see the `custom role overview`_ from Docutils.

.. _custom role overview: https://docutils.sourceforge.io/docs/howto/rst-roles.html


Creating custom roles
^^^^^^^^^^^^^^^^^^^^^

Sphinx provides two base classes for creating custom roles,
:class:`~sphinx.util.docutils.SphinxRole` and :class:`~sphinx.util.docutils.ReferenceRole`.

These provide a class-based interface for creating roles,
where the main logic must be implemented in your ``run()`` method.
The classes provide a number of useful methods and attributes,
such as ``self.text``, ``self.config``, and ``self.env``.
The ``ReferenceRole`` class implements Sphinx's ``title <target>`` logic,
exposing ``self.target`` and ``self.title`` attributes.
This is useful for creating cross-reference roles.


Directives
----------

Directives are handled by classes derived from
``docutils.parsers.rst.Directive``.  They have to be registered by an extension
using :meth:`.Sphinx.add_directive` or :meth:`.Sphinx.add_directive_to_domain`.

.. module:: docutils.parsers.rst

.. class:: Directive

   The markup syntax of the new directive is determined by the follow five class
   attributes:

   .. autoattribute:: required_arguments
   .. autoattribute:: optional_arguments
   .. autoattribute:: final_argument_whitespace
   .. autoattribute:: option_spec

      Option validator functions take a single parameter, the option argument
      (or ``None`` if not given), and should validate it or convert it to the
      proper form.  They raise :exc:`ValueError` or :exc:`TypeError` to indicate
      failure.

      There are several predefined and possibly useful validators in the
      :mod:`docutils.parsers.rst.directives` module.

   .. autoattribute:: has_content

   New directives must implement the :meth:`run` method:

   .. method:: run()

      This method must process the directive arguments, options and content, and
      return a list of Docutils/Sphinx nodes that will be inserted into the
      document tree at the point where the directive was encountered.

   Instance attributes that are always set on the directive are:

   .. attribute:: name

      The directive name (useful when registering the same directive class under
      multiple names).

   .. attribute:: arguments

      The arguments given to the directive, as a list.

   .. attribute:: options

      The options given to the directive, as a dictionary mapping option names
      to validated/converted values.

   .. attribute:: content

      The directive content, if given, as a :class:`!ViewList`.

   .. attribute:: lineno

      The absolute line number on which the directive appeared.  This is not
      always a useful value; use :attr:`srcline` instead.

   .. attribute:: content_offset

      Internal offset of the directive content.  Used when calling
      ``nested_parse`` (see below).

   .. attribute:: block_text

      The string containing the entire directive.

   .. attribute:: state
                  state_machine

      The state and state machine which controls the parsing.  Used for
      ``nested_parse``.

.. seealso::

   `Creating directives`_ HOWTO of the Docutils documentation

   .. _Creating directives: https://docutils.sourceforge.io/docs/howto/rst-directives.html


.. _parsing-directive-content-as-rest:

Parsing directive content as reStructuredText
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many directives will contain more markup that must be parsed.
To do this, use one of the following APIs from the :meth:`~Directive.run` method:

* :py:meth:`.SphinxDirective.parse_content_to_nodes()`
* :py:meth:`.SphinxDirective.parse_text_to_nodes()`

The first method parses all the directive's content as markup,
whilst the second only parses the given *text* string.
Both methods return the parsed Docutils nodes in a list.

The methods are used as follows:

.. code-block:: python

   def run(self) -> list[Node]:
       # either
       parsed = self.parse_content_to_nodes()
       # or
       parsed = self.parse_text_to_nodes('spam spam spam')
       return parsed

.. note::

   The above utility methods were added in Sphinx 7.4.
   Prior to Sphinx 7.4, the following methods should be used to parse content:

   * ``self.state.nested_parse``
   * :func:`sphinx.util.nodes.nested_parse_with_titles` -- this allows titles in
     the parsed content.

   .. code-block:: python

      def run(self) -> list[Node]:
          container = docutils.nodes.Element()
          # either
          nested_parse_with_titles(self.state, self.result, container, self.content_offset)
          # or
          self.state.nested_parse(self.result, self.content_offset, container)
          parsed = container.children
          return parsed

To parse inline markup,
use :py:meth:`~sphinx.util.docutils.SphinxDirective.parse_inline()`.
This must only be used for text which is a single line or paragraph,
and does not contain any structural elements
(headings, transitions, directives, etc).

.. note::

   ``sphinx.util.docutils.switch_source_input()`` allows changing
   the source (input) file during parsing content in a directive.
   It is useful to parse mixed content, such as in ``sphinx.ext.autodoc``,
   where it is used to parse docstrings.

   .. code-block:: python

      from sphinx.util.docutils import switch_source_input
      from sphinx.util.parsing import nested_parse_to_nodes

      # Switch source_input between parsing content.
      # Inside this context, all parsing errors and warnings are reported as
      # happened in new source_input (in this case, ``self.result``).
      with switch_source_input(self.state, self.result):
          parsed = nested_parse_to_nodes(self.state, self.result)

   .. deprecated:: 1.7

      Until Sphinx 1.6, ``sphinx.ext.autodoc.AutodocReporter`` was used for this
      purpose.  It is replaced by ``switch_source_input()``.


.. _ViewLists:

ViewLists and StringLists
^^^^^^^^^^^^^^^^^^^^^^^^^

Docutils represents document source lines in a ``StringList`` class,
which inherits from ``ViewList``, both in the ``docutils.statemachine`` module.
This is a list with extended functionality,
including that slicing creates views of the original list and
that the list contains information about source line numbers.

The :attr:`Directive.content` attribute is a ``StringList``.
If you generate content to be parsed as reStructuredText,
you have to create a ``StringList`` for the Docutils APIs.
The utility functions provided by Sphinx handle this automatically.
Important for content generation are the following points:

* The ``ViewList`` constructor takes a list of strings (lines)
  and a source (document) name.
* The ``ViewList.append()`` method takes a line and a source name as well.
