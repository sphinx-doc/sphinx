=======
Welcome
=======

.. epigraph:: Sphinx makes it easy to create intelligent and beautiful documentation.

Here are some of Sphinx's major features:

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
  from Python modules (API docs) via :ref:`built-in extensions
  <builtin-extensions>`, and much more functionality via :ref:`third-party
  extensions <third-party-extensions>`.
* **Themes:** modify the look and feel of outputs via :doc:`creating themes
  <development/theming>`, and re-use many :ref:`third-party themes
  <third-party-themes>`.
* **Contributed extensions:** dozens of extensions :ref:`contributed by users
  <third-party-extensions>`; most of them installable from PyPI.

.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _Docutils: https://docutils.sourceforge.io/
.. _Pygments: https://pygments.org/

Sphinx uses the reStructuredText_ markup language by default, and can read
:ref:`MyST markdown <markdown>` via third-party extensions. Both of these
are powerful and straightforward to use, and have functionality
for complex documentation and publishing workflows. They both build upon
Docutils_ to parse and write documents.

See below for how to navigate Sphinx's documentation.

.. seealso::

   The `Sphinx documentation Table of Contents <contents.html>`_ has
   a full list of this site's pages.

.. _get-started:

Get started
===========

These sections cover the basics of getting started with Sphinx, including
creating and building your own documentation from scratch.

.. toctree::
   :maxdepth: 2
   :caption: Get started

   usage/quickstart
   usage/installation
   tutorial/index

.. _user-guides:

User Guides
===========

These sections cover various topics in using and extending Sphinx for various
use-cases. They are a comprehensive guide to using Sphinx in many contexts and
assume more knowledge of Sphinx. If you are new to Sphinx, we recommend
starting with :ref:`get-started`.

.. toctree::
   :maxdepth: 2
   :caption: User Guides

   usage/index
   development/index
   latex
   extdev/index

Community guide
===============

Sphinx is community supported and welcomes contributions from anybody.
The sections below should help you get started joining the Sphinx community
as well as contributing.

See the :doc:`Sphinx contributors' guide <internals/contributing>` if you would
like to contribute to the project.

.. toctree::
   :maxdepth: 2
   :caption: Community

   support
   internals/index
   faq
   authors

Reference guide
===============

Reference documentation is more complete and programmatic in nature, it is a
collection of information that can be quickly referenced. If you would like
usecase-driven documentation, see :ref:`get-started` or :ref:`user-guides`.

.. toctree::
   :maxdepth: 2
   :caption: Reference

   man/index
   usage/configuration
   usage/extensions/index
   usage/restructuredtext/index
   glossary
   changes
   examples
