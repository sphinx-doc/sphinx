=================================
Sphinx Document Translation Guide
=================================

.. topic:: Abstract

   This document describes the translation cycle of Sphinx-based document.
   For illustrative purpose, we use Sphinx document itself in this document.

The Sphinx document is included in the Sphinx code.  It is managed by
`Mercurial`_ and is hosted on `BitBucket`_.


    hg clone https://bitbucket.org/birkenfeld/sphinx


.. _`BitBucket`: http://bitbucket.org
.. _`Mercurial`: http://mercurial.selenic.com/


Translate the document
======================

Getting Started
---------------

These are the basic steps needed to start translating the Sphinx document.


#. Clone the sphinx repository to your machine.

   .. code-block:: bash

      hg clone https://bitbucket.org/birkenfeld/sphinx
      cd sphinx/doc


#. Add below settings to sphinx document's conf.py if not exists.

   .. code-block:: bash

      locale_dirs = ['locale/']   #for example
      gettext_compact = False     #optional

   This case-study assumes that :confval:`locale_dirs` is set to 'locale/' and
   :confval:`gettext_compact` is set to `False` (the Sphinx document is
   already configured as such).

#. Generate pot files from the document.

   .. code-block:: bash

      make gettext
      ...

   As a result, many pot files are generated under ``_build/locale``
   directory. By the way, :confval:`locale_dirs` is set to ``locale/``
   then ``locale/pot`` directory is proper location for pot files.

   .. code-block:: bash

      mkdir locale
      cp -R _build/locale locale/pot


#. Generate po files from pot files.

   Sphinx expects that translated po files are under
   ``locale/<lang>/LC_MESSAGES/`` directory. For Japanese, you need
   ``locale/ja/LC_MESSAGE/`` directory and po files under the
   directory. The po files can be copied and renamed from pot files:

   .. code-block:: bash

      mkdir -p locale/ja/LC_MESSAGES
      cp -R locale/pot/* ja/LC_MESSAGES
      cd locale/ja/LC_MESSAGES

      find . -name "*.pot" -type f -print0 |while read -r -d '' file; do
      mv "$file" "${file%.*}.po";
      done

#. Translating!

   Translate po file under ``sphinx/doc/locale/ja/LC_MESSAGES`` directory.
   The case of builders.po:

   .. code-block:: po

      # a5600c3d2e3d48fc8c261ea0284db79b
      #: ../../builders.rst:4
      msgid "Available builders"
      msgstr "<FILL HERE BY TARGET LANGUAGE>"

   Another case, msgid is multi-line text and contains reStructuredText
   syntax:

   .. code-block:: po

      # 302558364e1d41c69b3277277e34b184
      #: ../../builders.rst:9
      msgid ""
      "These are the built-in Sphinx builders. More builders can be added by "
      ":ref:`extensions <extensions>`."
      msgstr ""
      "FILL HERE BY TARGET LANGUAGE FILL HERE BY TARGET LANGUAGE FILL HERE "
      "BY TARGET LANGUAGE :ref:`EXTENSIONS <extensions>` FILL HERE."

   Please be careful not to break reST notation.


#. Compile po files into mo.

   You need msgfmt_ command line tool to compile po files. For example,
   the case of debian, you can install the command by this command:

   .. code-block:: bash

      sudo apt-get install gettext

   and do compile each po files:

   .. code-block:: bash

      cd sphinx/doc/locale/ja/LC_MESSAGES
      msgfmt builders.po -o builders.mo
      ...

   in one line:

   .. code-block:: bash

      find . -name "*.po" -type f -print0 | while read -r -d '' file; do \
      msgfmt "$file" -o "${file%.*}.mo"; \
      done



#. Make translated html (or other format).

   Now you are ready to make the translated document by the
   :command:`make html` command. You need :confval:`language` parameter in
   ``conf.py`` or you may also specify the parameter on the command line.

   .. code-block:: bash

      $ cd sphinx/doc
      $ make -e SPHINXOPTS="-D language='ja'" html

   Congratulations!! You got the translated document in ``_build/html``
   directory.


Update your po files by new pot files
--------------------------------------

If the document is updated, it is necessary to generate updated pot files
and to apply differences to translated po files.
In order to apply the updating difference of a pot file to po file,
using msgmerge_ command.

.. code-block:: bash

   $ msgmerge -U locale/pot/builders.pot locale/ja/LC_MESSAGES/builders.po
   ........... done.


.. TODO: write loop command


Using Transifex service for team translation
============================================

.. TODO: why use transifex?


Make new translation project
----------------------------

1. Create your transifex_ account (if not have) and login.

   For example:

   :Transifex UserName: <transifex-username>
   :Transifex Password: <transifex-password>

2. Create new project for your document.

   Currently, transifex does not allow for a translation project to
   have more than one version of document, so you'd better include a
   version number in your project name.

   For example:

   :Project ID: ``sphinx-document-test_1_0``
   :Project URL: https://www.transifex.com/projects/p/sphinx-document-test_1_0/


Install transifex client: tx
-----------------------------

You need ``tx`` command to upload resources (pot files).

.. code-block:: bash

   $ pip install transifex-client

.. seealso:: `Transifex Client v0.8 &mdash; Transifex documentation`_


Create config files for tx command
----------------------------------

.. code-block:: bash

   $ tx init --user=<transifex-username> --pass=<transifex-password>
   Creating .tx folder...
   Transifex instance [https://www.transifex.com]:
   Creating skeleton...
   Creating config file...
   No authentication data found.
   No entry found for host https://www.transifex.com. Creating...
   Updating /home/ubuntu/.transifexrc file...
   Done.

This process will create ``.tx/config`` in the current directory, as
well as ``~/.transifexrc`` file that includes auth information.


.....


Register pot files in transifex
-----------------------------------

.. code-block:: bash

   $ cd $BASEDIR/sphinx/doc
   $ tx push -s
   Pushing translations for resource sphinx-document-test_1_0.builders:
   Pushing source file (locale/pot/builders.pot)
   Resource does not exist.  Creating...
   ...
   Done.


.. note::

   there is tx command wrapper tool to easier.

   https://bitbucket.org/shimizukawa/sphinx-transifex


Forward the translation on transifex
------------------------------------


Pull translated po files and make translated html
-------------------------------------------------

Get translated catalogs and build mo files (ex. for 'ja'):

.. code-block:: bash

   $ cd $BASEDIR/sphinx/doc
   $ tx pull -l ja
   Pulling translations for resource sphinx-document-test_1_0.builders (source: locale/pot/builders.pot)
    -> ja: locale/ja/LC_MESSAGES/builders.po
   ...
   Done.


convert po files into mo::

   $ msgfmt ....


Build html (ex. for 'ja')::

   $ make -e SPHINXOPTS="-D language='ja'" html

Done.



Tranlating Tips
================

* Translating local vs Transifex

  If you want to push all language's po files, you can use `tx push -t`.
  (this operation overwrites translations in transifex.)


* rebuild

   :command:`make clean && make html`


Contributing to Sphinx reference translation
============================================

The recommended way for new contributors to translate Sphinx reference
is to join the translation team on Transifex.

There is `sphinx translation page`_ for Sphinx-1.2 document.

1. login to transifex_ service.
2. go to `sphinx translation page`_.
3. push ``Request language`` and fill form.
4. wait acceptance by transifex sphinx translation maintainers.
5. (after acceptance) translate on transifex.



.. _Transifex: https://www.transifex.com/
.. _msgmerge: http://www.gnu.org/software/gettext/manual/html_node/index.html
.. _msgfmt: http://www.gnu.org/software/gettext/manual/html_node/index.html

.. _`sphinx translation page`: https://www.transifex.com/projects/p/sphinx-doc-1_2_0/ 

.. _`Transifex Client v0.8 &mdash; Transifex documentation`: http://help.transifex.com/features/client/index.html

