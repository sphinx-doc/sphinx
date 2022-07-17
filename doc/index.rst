=======
Welcome
=======

**Sphinx makes it easy to create intelligent and beautiful documentation.**

Install
=======

Install Sphinx with ``pip install -U Sphinx``. See :doc:`usage/installation` for
further details.

Features
========

* **Output formats:** HTML (including Windows HTML Help), LaTeX (for printable
  PDF versions), ePub, Texinfo, manual pages, plain text
* **Extensive cross-references:** semantic markup and automatic links for
  functions, classes, citations, glossary terms and similar pieces of
  information
* **Hierarchical structure:** easy definition of a document tree, with automatic
  links to siblings, parents and children
* **Automatic indices:** general index as well as a language-specific module
  indices
* **Code handling:** automatic highlighting using the Pygments_ highlighter
* **Extensions:** automatic testing of code snippets, inclusion of docstrings
  from Python modules (API docs), and :ref:`more <builtin-extensions>`
* **Contributed extensions:** dozens of extensions
  :ref:`contributed by users <third-party-extensions>`; most of them installable
  from PyPI

.. _Pygments: https://pygments.org/

Sphinx uses reStructuredText_ as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its parsing
and translating suite, the Docutils_.

.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _Docutils: https://docutils.sourceforge.io/

Documentation
=============

* :doc:`First steps with Sphinx <usage/quickstart>`: overview of basic tasks
* :doc:`Tutorial <tutorial/index>`: beginners tutorial
* :ref:`Search page <search>`: search the documentation
* :doc:`Changes <changes>`: release history
* :ref:`General Index <genindex>`: all functions, classes, terms
* :ref:`Python Module Index <modindex>`: the index of Python modules
* :doc:`Glossary <glossary>`: definitions of various terms
* :doc:`Sphinx's Authors <internals/authors>`: the Sphinx developers
* `Contents <contents.html>`__: full table of contents

Support
=======

For questions or to report problems with Sphinx, join the `sphinx-users`_
mailing list on Google Groups, come to the ``#sphinx-doc`` channel on
`libera.chat`_, or open an issue at the tracker_.

.. _sphinx-users: https://groups.google.com/group/sphinx-users
.. _libera.chat: https://web.libera.chat/?channel=#sphinx-doc
.. _tracker: https://github.com/sphinx-doc/sphinx/issues

Examples of other projects using Sphinx can be found in the :doc:`examples page
<examples>`. A useful tutorial_ has been written by the matplotlib developers.

.. _tutorial: http://matplotlib.sourceforge.net/sampledoc/

There is a translation team in Transifex_ of this documentation, thanks to the
Sphinx document translators.

.. _Transifex: https://www.transifex.com/sphinx-doc/sphinx-doc/dashboard/

Contributor guide
=================

See the :doc:`Sphinx contributors' guide <internals/contributing>` if you would
like to contribute to the project.

.. master toctree:

.. toctree::
   :maxdepth: 5
   :hidden:

   usage/index
   tutorial/index
   development/index
   man/index

   templating
   latex
   extdev/index

   internals/index

   faq
   glossary
   changes
   examples
