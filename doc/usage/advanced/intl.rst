.. _intl:

Internationalization
====================

.. versionadded:: 1.1

Complementary to translations provided for Sphinx-generated messages such as
navigation bars, Sphinx provides mechanisms facilitating *document* translations
in itself.  See the :ref:`intl-options` for details on configuration.

.. figure:: /_static/translation.png
   :width: 100%

   Workflow visualization of translations in Sphinx.  (The stick-figure is taken
   from an `XKCD comic <https://xkcd.com/779/>`_.)

.. contents::
   :local:

Sphinx internationalization details
-----------------------------------

**gettext** [1]_ is an established standard for internationalization and
localization.  It naively maps messages in a program to a translated string.
Sphinx uses these facilities to translate whole documents.

Initially project maintainers have to collect all translatable strings (also
referred to as *messages*) to make them known to translators.  Sphinx extracts
these through invocation of ``sphinx-build -b gettext``.

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

An example: you have a document ``usage.rst`` in your Sphinx project.  The
*gettext* builder will put its messages into ``usage.pot``.  Imagine you have
Spanish translations [2]_ stored in ``usage.po`` --- for your builds to
be translated you need to follow these instructions:

* Compile your message catalog to a locale directory, say ``locale``, so it
  ends up in ``./locale/es/LC_MESSAGES/usage.mo`` in your source directory
  (where ``es`` is the language code for Spanish.) ::

        msgfmt "usage.po" -o "locale/es/LC_MESSAGES/usage.mo"

* Set :confval:`locale_dirs` to ``["locale/"]``.
* Set :confval:`language` to ``es`` (also possible via
  :option:`-D <sphinx-build -D>`).
* Run your desired build.


Translating with sphinx-intl
----------------------------

Quick guide
~~~~~~~~~~~

`sphinx-intl`_ is a useful tool to work with Sphinx translation flow.  This
section describe an easy way to translate with *sphinx-intl*.

#. Install `sphinx-intl`_.

   .. code-block:: console

      $ pip install sphinx-intl

#. Add configurations to ``conf.py``.

   ::

      locale_dirs = ['locale/']   # path is example but recommended.
      gettext_compact = False     # optional.

   This case-study assumes that :confval:`locale_dirs` is set to ``locale/`` and
   :confval:`gettext_compact` is set to ``False`` (the Sphinx document is
   already configured as such).

#. Extract translatable messages into pot files.

   .. code-block:: console

      $ make gettext

   The generated pot files will be placed in the ``_build/gettext`` directory.

#. Generate po files.

   We'll use the pot files generated in the above step.

   .. code-block:: console

      $ sphinx-intl update -p _build/gettext -l de -l ja

   Once completed, the generated po files will be placed in the below
   directories:

   * ``./locale/de/LC_MESSAGES/``
   * ``./locale/ja/LC_MESSAGES/``

#. Translate po files.

   AS noted above, these are located in the ``./locale/<lang>/LC_MESSAGES``
   directory.  An example of one such file, from Sphinx, ``builders.po``, is
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

   Please be careful not to break reST notation.  Most po-editors will help you
   with that.

#. Build translated document.

   You need a :confval:`language` parameter in ``conf.py`` or you may also
   specify the parameter on the command line.

   For for BSD/GNU make, run:

   .. code-block:: console

      $ make -e SPHINXOPTS="-D language='de'" html

   For Windows :command:`cmd.exe`, run:

   .. code-block:: console

      > set SPHINXOPTS=-D language=de
      > .\make.bat html

   For PowerShell, run:

   .. code-block:: console

      > Set-Item env:SPHINXOPTS "-D language=de"
      > .\make.bat html

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

   $ sphinx-intl update -p _build/locale


Using Transifex service for team translation
--------------------------------------------

Transifex_ is one of several services that allow collaborative translation via a
web interface.  It has a nifty Python-based command line client that makes it
easy to fetch and push translations.

.. TODO: why use transifex?


#. Install `transifex-client`_.

   You need :command:`tx` command to upload resources (pot files).

   .. code-block:: console

      $ pip install transifex-client

   .. seealso:: `Transifex Client documentation`_

#. Create your transifex_ account and create new project for your document.

   Currently, transifex does not allow for a translation project to have more
   than one version of the document, so you'd better include a version number in
   your project name.

   For example:

   :Project ID: ``sphinx-document-test_1_0``
   :Project URL: ``https://www.transifex.com/projects/p/sphinx-document-test_1_0/``

#. Create config files for :command:`tx` command.

   This process will create ``.tx/config`` in the current directory, as well as
   a ``~/.transifexrc`` file that includes auth information.

   .. code-block:: console

      $ tx init
      Creating .tx folder...
      Transifex instance [https://www.transifex.com]:
      ...
      Please enter your transifex username: <transifex-username>
      Password: <transifex-password>
      ...
      Done.

#. Upload pot files to transifex service.

   Register pot files to ``.tx/config`` file:

   .. code-block:: console

      $ cd /your/document/root
      $ sphinx-intl update-txconfig-resources --pot-dir _build/locale \
        --transifex-project-name sphinx-document-test_1_0

   and upload pot files:

   .. code-block:: console

      $ tx push -s
      Pushing translations for resource sphinx-document-test_1_0.builders:
      Pushing source file (locale/pot/builders.pot)
      Resource does not exist.  Creating...
      ...
      Done.

#. Forward the translation on transifex.

   .. TODO: write this section

#. Pull translated po files and make translated HTML.

   Get translated catalogs and build mo files. For example, to build mo files
   for German (de):

   .. code-block:: console

      $ cd /your/document/root
      $ tx pull -l de
      Pulling translations for resource sphinx-document-test_1_0.builders (...)
       -> de: locale/de/LC_MESSAGES/builders.po
      ...
      Done.

   Invoke :command:`make html` (for BSD/GNU make):

   .. code-block:: console

      $ make -e SPHINXOPTS="-D language='de'" html

That's all!

.. tip:: Translating locally and on Transifex

   If you want to push all language's po files, you can be done by using
   :command:`tx push -t` command.  Watch out! This operation overwrites
   translations in transifex.

   In other words, if you have updated each in the service and local po files,
   it would take much time and effort to integrate them.


Contributing to Sphinx reference translation
--------------------------------------------

The recommended way for new contributors to translate Sphinx reference is to
join the translation team on Transifex.

There is `sphinx translation page`_ for Sphinx (master) documentation.

1. Login to transifex_ service.
2. Go to `sphinx translation page`_.
3. Click ``Request language`` and fill form.
4. Wait acceptance by transifex sphinx translation maintainers.
5. (After acceptance) Translate on transifex.

.. rubric:: Footnotes

.. [1] See the `GNU gettext utilities
       <https://www.gnu.org/software/gettext/manual/gettext.html#Introduction>`_
       for details on that software suite.
.. [2] Because nobody expects the Spanish Inquisition!

.. _`transifex-client`: https://pypi.org/project/transifex-client/
.. _`sphinx-intl`: https://pypi.org/project/sphinx-intl/
.. _Transifex: https://www.transifex.com/
.. _`sphinx translation page`: https://www.transifex.com/sphinx-doc/sphinx-doc/
.. _`Transifex Client documentation`: https://docs.transifex.com/client/introduction/
