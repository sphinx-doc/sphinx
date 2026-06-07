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

Accessing the Sphinx config and environment
-------------------------------------------

A custom parser can read Sphinx :class:`~sphinx.config.Config` values and the
:class:`~sphinx.environment.BuildEnvironment` through the inherited
``Parser.config`` and ``Parser.env`` properties.  Sphinx populates the
backing ``_config`` and ``_env`` attributes when it instantiates a parser
registered via :meth:`.Sphinx.add_source_parser`, so they are available
from the start of ``parse()``.

.. code-block:: python

   from sphinx.parsers import Parser


   class MyParser(Parser):
       supported = ('mytype',)

       def parse(self, inputstring, document):
           # ``self.config`` and ``self.env`` are populated by Sphinx
           encoding = self.config.source_encoding
           docname = self.env.docname
           ...

.. versionchanged:: 9.2
   ``Parser.config`` and ``Parser.env`` are no longer deprecated.

.. deprecated:: 9.0
   The ``Parser.set_application`` hook is deprecated and will be removed in
   Sphinx 10.  Sphinx now populates ``_config`` and ``_env`` directly when
   the parser instance is created, so custom parsers no longer need to
   override ``set_application`` to capture these objects.
