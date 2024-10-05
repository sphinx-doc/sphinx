.. _parser-api:

Parser API
==========

`The docutils documentation describes`__ parsers as follows:

    The Parser analyzes the input document and creates a node tree
    representation.

__ https://docutils.sourceforge.io/docs/dev/hacking.html#parsing-the-document

In Sphinx, the parser modules works as same as docutils.  The parsers are
registered to Sphinx by extensions using Application APIs;
:meth:`.Sphinx.add_source_suffix` and :meth:`.Sphinx.add_source_parser`.

The *source suffix* is a mapping from file suffix to file type.  For example,
``.rst`` file is mapped to ``'restructuredtext'`` type.  Sphinx uses the
file type to looking for parsers from registered list.  On searching,
Sphinx refers to the ``Parser.supported`` attribute and picks up a parser
which contains the file type in the attribute.

The users can override the source suffix mappings using
:confval:`source_suffix` like following::

    # a mapping from file suffix to file types
    source_suffix = {
        '.rst': 'restructuredtext',
        '.md': 'markdown',
    }

You should indicate file types your parser supports. This will allow users
to configure their settings appropriately.

.. module:: sphinx.parsers

.. autoclass:: Parser
   :members:
