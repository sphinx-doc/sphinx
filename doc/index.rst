======
Sphinx
======

.. cssclass:: sphinx-tagline
.. epigraph:: Create intelligent and beautiful documentation with ease

.. container:: sphinx-features

   .. admonition:: 📝 Rich Text Formatting
      :class: sphinx-feature

      Author in :ref:`reStructuredText <rst-primer>`
      or :ref:`MyST Markdown <markdown>`
      to create highly structured technical documents,
      including tables, highlighted code blocks, mathematical notations, and more.

   .. admonition:: 🔗 Powerful Cross-Referencing
      :class: sphinx-feature

      Create :ref:`cross-references <xref>`
      within your project,
      and even across :ref:`different projects <ext-intersphinx>`.
      Include references to
      sections, figures, tables, citations, glossaries, code objects,
      and more.

   .. admonition:: 📚 Versatile Documentation Formats
      :class: sphinx-feature

      Generate documentation in the preferred formats of your audience, including
      HTML, LaTeX (for PDF), ePub, Texinfo, :ref:`and more <builders>`.

   .. admonition:: 🎨 Extensive Theme Support
      :class: sphinx-feature

      Create visually appealing documentation,
      with a wide choice of :ref:`built-in <builtin-themes>`
      and :ref:`third-party <third-party-themes>` HTML themes
      and the ability to customize
      or :ref:`create new themes <extension-html-theme>`.

   .. admonition:: 🔌 Fully Extensible
      :class: sphinx-feature

      Add custom functionality,
      via robust :ref:`extension mechanisms <extending-sphinx>`
      with numerous :ref:`built-in <builtin-extensions>`
      and :ref:`third-party <third-party-extensions>`
      extensions available for tasks like
      creating diagrams, testing code, and more.

   .. admonition:: 🛠️ Automatic API Documentation
      :class: sphinx-feature

      Generate API documentation for
      Python, C++ and other :ref:`software domains <usage-domains>`,
      manually or :ref:`automatically from docstrings <ext-autodoc>`,
      ensuring your code documentation
      stays up-to-date with minimal effort.

   .. admonition:: 🌍 Internationalization (i18n)
      :class: sphinx-feature

      Add documentation :ref:`translations <intl>`
      multiple languages to reach a global audience.

   .. admonition:: 🌟 Active Community and Support
      :class: sphinx-feature

      Benefit from an :ref:`active community <support-index>`,
      with numerous resources, tutorials, forums, and examples.

   .. .. admonition:: 🌐 Integration with Version Control
   ..    :class: sphinx-feature

   ..    Sphinx integrates seamlessly with version control systems like Git.
   ..    This allows for easy collaboration, version tracking,
   ..    and deployment of documentation as part of a continuous integration pipeline.

----------------

.. container:: sphinx-users

   As used by:

   .. container:: sphinx-users-logos

      .. figure:: _static/python-logo.png
         :alt: Python Logo
         :height: 100px
         :align: center
         :target: https://docs.python.org

         Python

      .. figure:: _static/linux-logo.png
         :alt: Linux Logo
         :height: 100px
         :align: center
         :target: https://docs.kernel.org/

         Linux Kernel

      .. figure:: _static/jupyter-logo.png
         :alt: Jupyter Logo
         :height: 100px
         :align: center
         :target: https://docs.jupyter.org

         Project Jupyter

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

User guide
==========

These sections cover various topics in using and extending Sphinx for various
use-cases. They are a comprehensive guide to using Sphinx in many contexts and
assume more knowledge of Sphinx. If you are new to Sphinx, we recommend
starting with :ref:`get-started`.

.. toctree::
   :maxdepth: 2
   :caption: User guide

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
   changes/index
   examples
