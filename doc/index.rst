======
Sphinx
======

.. epigraph:: *Create intelligent and beautiful documentation with ease*

.. container:: sphinx-features

   .. admonition:: 📝 Rich Text Formatting
      :class: sphinx-feature

      Using reStructuredText_ or :ref:`MyST Markdown <markdown>`,
      Sphinx supports rich text formatting, including
      tables, highlighted code blocks, mathematical notations, and more.
      This enables the creation of
      highly detailed and structured technical documents.

   .. admonition:: 🔗 Powerful Cross-Referencing
      :class: sphinx-feature

      Sphinx excels in its ability to create :ref:`cross-references <xref-syntax>`
      within the documentation,
      and even across :ref:`different projects <ext-intersphinx>`,
      with automated index generation.
      This includes references to
      sections, figures, tables, citations, glossaries and code objects.

   .. admonition:: 📚 Versatile Documentation Formats
      :class: sphinx-feature

      Sphinx can generate documentation in various formats
      including HTML, LaTeX (for PDF), ePub, Texinfo, and more.
      This versatility ensures that your documentation
      can be easily accessed and read in the preferred format of your audience.

   .. admonition:: 🎨 Extensive Theme Support
      :class: sphinx-feature

      With a wide range of :ref:`built-in <builtin-themes>`
      and :ref:`third-party <third-party-themes>` HTML themes
      and the ability to customize
      or :ref:`create new themes <extension-html-theme>`,
      Sphinx allows you to create visually appealing documentation
      that aligns with your branding and aesthetic preferences.

   .. admonition:: 🔌 Fully Extensible
      :class: sphinx-feature

      Sphinx has robust :ref:`extension mechanisms <extending-sphinx>`
      that allow you to add custom functionality for complex documentation needs.
      There are numerous :ref:`built-in <builtin-extensions>`
      and :ref:`third-party <third-party-extensions>`
      extensions available for tasks like
      creating diagrams, testing code, and more.

   .. admonition:: 🛠️ Automatic API Documentation
      :class: sphinx-feature

      For Python, C++ and other software projects, Sphinx can automatically
      :ref:`generate API documentation <ext-autodoc>` from docstrings.
      This ensures that your code documentation
      stays up-to-date with minimal manual effort.

   .. admonition:: 🌍 Internationalization (i18n)
      :class: sphinx-feature

      Sphinx supports :ref:`internationalization <intl>`,
      allowing you to create documentation in multiple languages.
      This is particularly beneficial for projects with a global audience.

   .. admonition:: 🌟 Active Community and Support
      :class: sphinx-feature

      Sphinx has an :ref:`active community <support-index>`
      and extensive documentation itself.
      There are numerous resources, including tutorials, forums, and examples,
      which can help users get the most out of the tool.

   .. .. admonition:: 🌐 Integration with Version Control
   ..    :class: sphinx-feature

   ..    Sphinx integrates seamlessly with version control systems like Git.
   ..    This allows for easy collaboration, version tracking,
   ..    and deployment of documentation as part of a continuous integration pipeline.

.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _Pygments: https://pygments.org/

----------------

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
   :caption: The Basics

   usage/installation
   usage/quickstart
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
   extdev/index
   latex

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
