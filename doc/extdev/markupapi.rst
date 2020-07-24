Docutils markup API
===================

This section describes the API for adding ReST markup elements (roles and
directives).

Roles
-----


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

      The directive content, if given, as a :class:`.ViewList`.

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


ViewLists
^^^^^^^^^

Docutils represents document source lines in a class
``docutils.statemachine.ViewList``.  This is a list with extended functionality
-- for one, slicing creates views of the original list, and also the list
contains information about the source line numbers.

The :attr:`Directive.content` attribute is a ViewList.  If you generate content
to be parsed as ReST, you have to create a ViewList yourself.  Important for
content generation are the following points:

* The constructor takes a list of strings (lines) and a source (document) name.

* The ``.append()`` method takes a line and a source name as well.


Parsing directive content as ReST
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many directives will contain more markup that must be parsed.  To do this, use
one of the following APIs from the :meth:`Directive.run` method:

* ``self.state.nested_parse``
* :func:`sphinx.util.nodes.nested_parse_with_titles` -- this allows titles in
  the parsed content.

Both APIs parse the content into a given node. They are used like this::

   node = docutils.nodes.paragraph()
   # either
   nested_parse_with_titles(self.state, self.result, node)
   # or
   self.state.nested_parse(self.result, 0, node)

.. note::

   ``sphinx.util.docutils.switch_source_input()`` allows to change a target file
   during nested_parse.  It is useful to mixed contents.  For example, ``sphinx.
   ext.autodoc`` uses it to parse docstrings::

       from sphinx.util.docutils import switch_source_input

       # Switch source_input between parsing content.
       # Inside this context, all parsing errors and warnings are reported as
       # happened in new source_input (in this case, ``self.result``).
       with switch_source_input(self.state, self.result):
           node = docutils.nodes.paragraph()
           self.state.nested_parse(self.result, 0, node)

   .. deprecated:: 1.7

      Until Sphinx-1.6, ``sphinx.ext.autodoc.AutodocReporter`` is used for this
      purpose.  For now, it is replaced by ``switch_source_input()``.

If you don't need the wrapping node, you can use any concrete node type and
return ``node.children`` from the Directive.


.. seealso::

   `Creating directives`_ HOWTO of the Docutils documentation

.. _Creating directives: http://docutils.sourceforge.net/docs/howto/rst-directives.html
