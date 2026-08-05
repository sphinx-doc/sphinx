.. _intl:

Internationalization
====================

.. versionadded:: 1.1

Complementary to translations provided for Sphinx-generated messages such as
navigation bars, Sphinx provides mechanisms facilitating the translation of
*documents*.  See the :ref:`intl-options` for details on configuration.

.. figure:: /_static/translation.*
   :width: 100%

   Workflow visualization of translations in Sphinx.  (The figure is created by
   `plantuml <https://plantuml.com>`_.)

.. contents::
   :local:

Sphinx internationalization details
-----------------------------------

**gettext** [1]_ is an established standard for internationalization and
localization.  It naively maps messages in a program to a translated string.
Sphinx uses these facilities to translate whole documents.

Initially project maintainers have to collect all translatable strings (also
referred to as *messages*) to make them known to translators.  Sphinx extracts
these through invocation of :command:`sphinx-build -M gettext`.

Every single element in the doctree will end up in a single message which
results in lists being equally split into different chunks while large
paragraphs will remain as coarsely-grained as they were in the original
document.  This grants seamless document updates while still providing a little
bit of context for translators in free-text passages.  It is the maintainer's
task to split up paragraphs which are too large as there is no sane automated
way to do that.

After Sphinx successfully ran the
:class:`~sphinx.builders.gettext.MessageCatalogBuilder` you will find a
collection of ``.pot`` files in your output directory.  These are **catalog
templates** and contain messages in your original language *only*.

They can be delivered to translators which will transform them to ``.po`` files
--- so called **message catalogs** --- containing a mapping from the original
messages to foreign-language strings.

*gettext* compiles them into a binary format known as **binary catalogs**
through :program:`msgfmt` for efficiency reasons.  If you make these files
discoverable with :confval:`locale_dirs` for your :confval:`language`, Sphinx
will pick them up automatically.

An example: you have a document :file:`usage.rst` in your Sphinx project.  The
*gettext* builder will put its messages into :file:`usage.pot`.  Imagine you have
Spanish translations [2]_ stored in :file:`usage.po` --- for your builds to
be translated you need to follow these instructions:

* Compile your message catalog to a locale directory, say ``locale``, so it
  ends up in :file:`./locale/es/LC_MESSAGES/usage.mo` in your source directory
  (where ``es`` is the language code for Spanish.) ::

        msgfmt "usage.po" -o "locale/es/LC_MESSAGES/usage.mo"

* Set :confval:`locale_dirs` to ``["locale/"]``.
* Set :confval:`language` to ``es`` (also possible via
  :option:`-D <sphinx-build -D>`).
* Run your desired build.


In order to protect against mistakes, a warning is emitted if
cross-references in the translated paragraph do not match those from the
original.  This can be turned off globally using the
:confval:`suppress_warnings` configuration variable.  Alternatively, to
turn it off for one message only, end the message with ``#noqa`` like
this::

   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
   risus tortor, luctus id ultrices at. #noqa

(Write ``\#noqa`` in case you want to have "#noqa" literally in the
text.  This does not apply to code blocks, where ``#noqa`` is ignored
because code blocks do not contain references anyway.)

.. versionadded:: 4.5
   The ``#noqa`` mechanism.


Translating with sphinx-intl
----------------------------

Quick guide
~~~~~~~~~~~

`sphinx-intl`_ is a useful tool to work with Sphinx translation flow.  This
section describe an easy way to translate with *sphinx-intl*.

#. Install `sphinx-intl`_.

   .. code-block:: console

      $ pip install sphinx-intl

#. Add configurations to :file:`conf.py`.

   ::

      locale_dirs = ['locale/']   # path is example but recommended.
      gettext_compact = False     # optional.

   This case-study assumes that BUILDDIR is set to ``_build``,
   :confval:`locale_dirs` is set to ``locale/`` and :confval:`gettext_compact`
   is set to ``False`` (the Sphinx document is already configured as such).

#. Extract translatable messages into pot files.

   .. code-block:: console

      $ make gettext

   The generated pot files will be placed in the ``_build/gettext`` directory.
   If you want to customize the output beyond what can be done via the
   :ref:`intl-options`, the
   :download:`default pot file template <../../../sphinx/templates/gettext/message.pot.jinja>`
   can be replaced by a custom :file:`message.pot.jinja` file placed in any
   directory listed in :confval:`templates_path`.

#. Generate po files.

   We'll use the pot files generated in the above step.

   .. code-block:: console

      $ sphinx-intl update -p _build/gettext -l de -l ja

   Once completed, the generated po files will be placed in the below
   directories:

   * ``./locale/de/LC_MESSAGES/``
   * ``./locale/ja/LC_MESSAGES/``

#. Translate po files.

   As noted above, these are located in the ``./locale/<lang>/LC_MESSAGES``
   directory.  An example of one such file, from Sphinx, :file:`builders.po`, is
   given below.

   .. code-block:: po

      # a5600c3d2e3d48fc8c261ea0284db79b
      #: ../../builders.rst:4
      msgid "Available builders"
      msgstr "<FILL HERE BY TARGET LANGUAGE>"

   Another case, msgid is multi-line text and contains reStructuredText syntax:

   .. code-block:: po

      # 302558364e1d41c69b3277277e34b184
      #: ../../builders.rst:9
      msgid ""
      "These are the built-in Sphinx builders. More builders can be added by "
      ":ref:`extensions <extensions>`."
      msgstr ""
      "FILL HERE BY TARGET LANGUAGE FILL HERE BY TARGET LANGUAGE FILL HERE "
      "BY TARGET LANGUAGE :ref:`EXTENSIONS <extensions>` FILL HERE."

   Please be careful not to break reStructuredText notation.
   Most po-editors will help you with that.

#. Build translated document.

   You need a :confval:`language` parameter in :file:`conf.py` or you may also
   specify the parameter on the command line.

   For BSD/GNU make, run:

   .. code-block:: console

      $ make -e SPHINXOPTS="-D language='de'" html

   For Windows :command:`cmd.exe`, run:

   .. code-block:: doscon

      > set SPHINXOPTS=-D language=de
      > .\make.bat html

   For PowerShell, run:

   .. code-block:: ps1con

      PS> Set-Item env:SPHINXOPTS "-D language=de"
      PS> .\make.bat html

Congratulations! You got the translated documentation in the ``_build/html``
directory.

.. versionadded:: 1.3

   :program:`sphinx-build` that is invoked by make command will build po files
   into mo files.

   If you are using 1.2.x or earlier, please invoke :command:`sphinx-intl build`
   command before :command:`make` command.

Translating
~~~~~~~~~~~

Update your po files by new pot files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a document is updated, it is necessary to generate updated pot files and to
apply differences to translated po files.  In order to apply the updates from a
pot file to the po file, use the :command:`sphinx-intl update` command.

.. code-block:: console

   $ sphinx-intl update -p _build/gettext


Using Transifex service for team translation
--------------------------------------------

Transifex_ is one of several services that allow collaborative translation via a
web interface.  It has a nifty Go-based command line client that makes it
easy to fetch and push translations.

.. TODO: why use transifex?


#. Install the `Transifex CLI tool`_.

   You need the :command:`tx` command line tool for uploading resources (pot files).
   The official installation process place the :file:`tx` binary file in
   the current directory along with a README and a LICENSE file, and adds
   the current directory to ``$PATH``.

   .. code-block:: console

      $ curl -o- https://raw.githubusercontent.com/transifex/cli/master/install.sh | bash

   .. seealso:: `Transifex Client documentation`_

#. Create your Transifex_ account and create a new project and an organization
   for your document.

   Currently, Transifex does not allow for a translation project to have more
   than one version of the document, so you'd better include a version number in
   your project name.

   For example:

   :Organization ID: ``sphinx-document``
   :Project ID: ``sphinx-document-test_1_0``
   :Project URL: ``https://www.transifex.com/projects/p/sphinx-document-test_1_0/``

#. Create an API token to be used in the command-line.

   Go to your `Transifex API token`_ page and generate a token.
   Copy the generated token now, as you will not be able to see it again later.

#. Set your Transifex API token in the user configuration file
   :file:`$HOME/.transifexrc`.

   .. code-block:: ini

      [https://app.transifex.com]
      rest_hostname = https://rest.api.transifex.com
      token         = paste_your_api_token_here

#. Alternatively, you can store your Transifex API token as the environment variable
   ``TX_TOKEN``, which is recognized and used by :command:`tx`.

   .. code-block:: console

      $ export TX_TOKEN=paste_your_api_token_here

#. Create the project's config file for :command:`tx` command.

   This process will create ``.tx/config`` in the current directory.

   .. code-block:: console

      $ cd /your/document/root
      $ tx init

      Successful creation of '.tx/config' file

#. Upload pot files to Transifex service.

   Register pot files to ``.tx/config`` file using
   :command:`sphinx-intl update-txconfig-resources`, adjusting
   ``--pot-dir`` value to your project's pot files' directory:

   .. code-block:: console

      $ cd /your/document/root
      $ sphinx-intl update-txconfig-resources --pot-dir _build/locale \
        --transifex-organization-name=sphinx-document \
        --transifex-project-name=sphinx-document-test_1_0

   You can use the ``SPHINXINTL_TRANSIFEX_ORGANIZATION_NAME`` and
   ``SPHINXINTL_TRANSIFEX_PROJECT_NAME`` environment variables
   instead of the respective command line arguments.

   .. seealso:: `sphinx-intl update-txconfig-resources documentation`_

   and upload pot files:

   .. code-block:: console

      $ tx push -s
      # Getting info about resources

      sphinx-document-test_1_0.builders - Getting info
      sphinx-document-test_1_0.builders - Done

      # Pushing source files

      sphinx-document-test_1_0.builders - Uploading file
      sphinx-document-test_1_0.builders - Done

#. Forward the translation on Transifex.

   .. TODO: write this section

#. Pull translated po files and make translated HTML.

   Get translated catalogs and build mo files. For example, to build mo files
   for German (de):

   .. code-block:: console

      $ cd /your/document/root
      $ tx pull -l de
      # Getting info about resources

      sphinx-document-test_1_0.builders - Getting info
      sphinx-document-test_1_0.builders - Done

      # Pulling files

      sphinx-document-test_1_0.builders [de] - Pulling file
      sphinx-document-test_1_0.builders [de] - Creating download job
      sphinx-document-test_1_0.builders [de] - Done

   Invoke :command:`make html` (for BSD/GNU make) passing the language code:

   .. code-block:: console

      $ make -e SPHINXOPTS="-D language='de'" html

That's all!

.. tip:: Translating locally and on Transifex

   If you want to push all language's po files, you can be done by using
   :command:`tx push -t` command.  Watch out! This operation overwrites
   translations in Transifex.

   In other words, if you have updated each in the service and local po files,
   it would take much time and effort to integrate them.


Using Weblate service for team translation
------------------------------------------

Read more in `Weblate's documentation`_.


Contributing to Sphinx reference translation
--------------------------------------------

The recommended way for new contributors to translate Sphinx reference is to
join the translation team on Transifex.

There is a `Sphinx translation page`_ for Sphinx (master) documentation.

1. Login to Transifex_ service.
2. Go to the `"Sphinx's documentation" translation project
   <https://app.transifex.com/sphinx-doc/sphinx-doc/>`__.
3. Click ``Request language`` and fill form.
4. Wait acceptance by Transifex sphinx translation maintainers.
5. (After acceptance) Translate on Transifex.

Detail is here:
https://help.transifex.com/en/articles/6248698-getting-started-as-a-translator


Translation progress and statistics
-----------------------------------

.. versionadded:: 7.1.0

During the rendering process,
Sphinx marks each translatable node with a ``translated`` attribute,
indicating if a translation was found for the text in that node.

The :confval:`translation_progress_classes` configuration value
can be used to add a class to each element,
depending on the value of the ``translated`` attribute.

The ``|translation progress|`` substitution can be used to display the
percentage of nodes that have been translated on a per-document basis.

.. rubric:: Footnotes

.. [1] See the `GNU gettext utilities
       <https://www.gnu.org/software/gettext/manual/gettext.html#Introduction>`_
       for details on that software suite.
.. [2] Because nobody expects the Spanish Inquisition!

.. _`Transifex CLI tool`: https://github.com/transifex/cli/
.. _`sphinx-intl`: https://pypi.org/project/sphinx-intl/
.. _Transifex: https://app.transifex.com/
.. _Weblate's documentation: https://docs.weblate.org/en/latest/devel/sphinx.html
.. _`Sphinx translation page`: https://explore.transifex.com/sphinx-doc/sphinx-doc/
.. _`Transifex Client documentation`: https://developers.transifex.com/docs/using-the-client
.. _`Transifex API token`: https://app.transifex.com/user/settings/api/
.. _`sphinx-intl update-txconfig-resources documentation`: https://sphinx-intl.readthedocs.io/en/master/refs.html#sphinx-intl-update-txconfig-resources
