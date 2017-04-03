Sphinx vs. docutils
===================

tl;dr: *docutils* converts reStructuredText to multiple output formats. Sphinx
builds upon docutils to allow construction of cross-referenced and indexed
bodies of documentation.

docutils
--------

`docutils`__ is a text processing system for converting plain text
documentation into other, richer formats. docutils uses *readers* to read a
document, *parsers* for parsing plain text formats into an internal tree
representation made up of different types of *nodes*, and *writers* to output
this tree in various document formats [1]_.  docutils provides parsers for one
plain text format - `reStructuredText`__ - though other, *out-of-tree* parsers
have been implemented including Sphinx's :doc:`Markdown parser
</usage/markdown>`. On the other hand, it provides writers for many different
formats including HTML, LaTeX, man pages, Open Document Format and XML [2]_.

docutils exposes all of its functionality through a variety of front-end tools,
such as ``rst2html``, ``rst2odt`` and ``rst2xml`` [3]_. Crucially though, all
of these tools, and docutils itself, are concerned with individual documents.
They don't support concepts such as cross-referencing, indexing of documents,
or the construction of a document hierarchy (typically manifesting in a table
of contents).

For more information on docutils, refer to the `docutils documentation`__.

__ http://docutils.sourceforge.net/
__ http://docutils.sourceforge.net/rst.html
__ http://docutils.sourceforge.net/

Sphinx
------

Sphinx builds upon docutils by harnessing docutils' readers and parsers and
providing its own :doc:`/usage/builders/index`. As a result, Sphinx doesn't use
any of the *writers* provided by docutils. This allows Sphinx to provide many
features that would simply not be possible with docutils, such as those
outlined above.

.. [1] http://docutils.sourceforge.net/docs/dev/hacking.html
.. [2] http://docutils.sourceforge.net/index.html
.. [3] http://docutils.sourceforge.net/docs/user/tools.html
