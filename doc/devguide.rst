Sphinx Developer's Guide
========================

.. topic:: Abstract

   This document describes the development process of Sphinx, a documentation
   system used by developers to document systems used by other developers to
   develop other systems that may also be documented using Sphinx.

The Sphinx source code is managed using `Mercurial`_ and is hosted on
`BitBucket`_.

    hg clone https://bitbucket.org/birkenfeld/sphinx

.. rubric:: Community

sphinx-users <sphinx-users@googlegroups.com>
    Mailing list for user support.

sphinx-dev <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#sphinx-doc on irc.freenode.net
    IRC channel for development questions and user support.

.. _`BitBucket`: https://bitbucket.org/
.. _`Mercurial`: http://mercurial.selenic.com/


Bug Reports and Feature Requests
--------------------------------

If you have encountered a problem with Sphinx or have an idea for a new
feature, please submit it to the `issue tracker`_ on BitBucket or discuss it
on the sphinx-dev mailing list.

For bug reports, please include the output produced during the build process
and also the log file Sphinx creates after it encounters an un-handled
exception.  The location of this file should be shown towards the end of the
error message.

Including or providing a link to the source files involved may help us fix the
issue.  If possible, try to create a minimal project that produces the error
and post that instead.

.. _`issue tracker`: https://bitbucket.org/birkenfeld/sphinx/issues


Contributing to Sphinx
----------------------

The recommended way for new contributors to submit code to Sphinx is to fork
the Mercurial repository on BitBucket and then submit a pull request after
committing the changes.  The pull request will then need to be approved by one
of the core developers before it is merged into the main repository.


Getting Started
~~~~~~~~~~~~~~~

These are the basic steps needed to start developing on Sphinx.

#. Create an account on BitBucket.

#. Fork the main Sphinx repository (`birkenfeld/sphinx
   <https://bitbucket.org/birkenfeld/sphinx>`_) using the BitBucket interface.

#. Clone the forked repository to your machine. ::

       hg clone https://bitbucket.org/USERNAME/sphinx-fork
       cd sphinx-fork

#. Checkout the appropriate branch.

   For changes that should be included in the next minor release (namely bug
   fixes), use the ``stable`` branch. ::

       hg checkout stable

   For new features or other substantial changes that should wait until the
   next major release, use the ``default`` branch.

#. Optional: setup a virtual environment. ::

       virtualenv ~/sphinxenv
       . ~/sphinxenv/bin/activate
       pip install -e .

#. Hack, hack, hack.

   For tips on working with the code, see the `Coding Guide`_.

#. Test, test, test.  Possible steps:

   * Run the unit tests::

       pip install nose mock
       make test

   * Build the documentation and check the output for different builders::

       cd doc
       make clean html latexpdf

   * Run the unit tests under different Python environments using
     :program:`tox`::

       pip install tox
       tox -v

   * Add a new unit test in the ``tests`` directory if you can.

   * For bug fixes, first add a test that fails without your changes and passes
     after they are applied.

#. Please add a bullet point to :file:`CHANGES` if the fix or feature is not trivial
   (small doc updates, typo fixes).  Then commit::

       hg commit -m '#42: Add useful new feature that does this.'

   BitBucket recognizes `certain phrases`__ that can be used to automatically
   update the issue tracker.

   For example::

       hg commit -m 'Closes #42: Fix invalid markup in docstring of Foo.bar.'

   would close issue #42.

   __ https://confluence.atlassian.com/display/BITBUCKET/Resolve+issues+automatically+when+users+push+code

#. Push changes to your forked repository on BitBucket. ::

       hg push

#. Submit a pull request from your repository to ``birkenfeld/sphinx`` using
   the BitBucket interface.

#. Wait for a core developer to review your changes.


Core Developers
~~~~~~~~~~~~~~~

The core developers of Sphinx have write access to the main repository.  They
can commit changes, accept/reject pull requests, and manage items on the issue
tracker.

You do not need to be a core developer or have write access to be involved in
the development of Sphinx.  You can submit patches or create pull requests
from forked repositories and have a core developer add the changes for you.

The following are some general guidelines for core developers:

* Questionable or extensive changes should be submitted as a pull request
  instead of being committed directly to the main repository.  The pull
  request should be reviewed by another core developer before it is merged.

* Trivial changes can be committed directly but be sure to keep the repository
  in a good working state and that all tests pass before pushing your changes.

* When committing code written by someone else, please attribute the original
  author in the commit message and any relevant :file:`CHANGES` entry.

* Using Mercurial named branches other than ``default`` and ``stable`` is not
  encouraged.


Locale updates
~~~~~~~~~~~~~~

The parts of messages in Sphinx that go into builds are translated into several
locales.  The translations are kept as gettext ``.po`` files translated from the
master template ``sphinx/locale/sphinx.pot``.

Sphinx uses `Babel <http://babel.edgewall.org>`_ to extract messages and
maintain the catalog files.  It is integrated in ``setup.py``:

* Use ``python setup.py extract_messages`` to update the ``.pot`` template.
* Use ``python setup.py update_catalog`` to update all existing language
  catalogs in ``sphinx/locale/*/LC_MESSAGES`` with the current messages in the
  template file.
* Use ``python setup.py compile_catalog`` to compile the ``.po`` files to binary
  ``.mo`` files and ``.js`` files.

When an updated ``.po`` file is submitted, run compile_catalog to commit both
the source and the compiled catalogs.

When a new locale is submitted, add a new directory with the ISO 639-1 language
identifier and put ``sphinx.po`` in there.  Don't forget to update the possible
values for :confval:`language` in ``doc/config.rst``.

The Sphinx core messages can also be translated on `Transifex
<https://www.transifex.com/>`_.  There exists a client tool named ``tx`` in the Python
package "transifex_client", which can be used to pull translations in ``.po``
format from Transifex.  To do this, go to ``sphinx/locale`` and then run
``tx pull -f -l LANG`` where LANG is an existing language identifier.  It is
good practice to run ``python setup.py update_catalog`` afterwards to make sure
the ``.po`` file has the canonical Babel formatting.


Coding Guide
------------

* Try to use the same code style as used in the rest of the project.  See the
  `Pocoo Styleguide`__ for more information.

  __ http://flask.pocoo.org/docs/styleguide/

* For non-trivial changes, please update the :file:`CHANGES` file.  If your
  changes alter existing behavior, please document this.

* New features should be documented.  Include examples and use cases where
  appropriate.  If possible, include a sample that is displayed in the
  generated output.

* When adding a new configuration variable, be sure to document it and update
  :file:`sphinx/quickstart.py` if it's important enough.

* Use the included :program:`utils/check_sources.py` script to check for
  common formatting issues (trailing whitespace, lengthy lines, etc).

* Add appropriate unit tests.


Debugging Tips
~~~~~~~~~~~~~~

* Delete the build cache before building documents if you make changes in the
  code by running the command ``make clean`` or using the
  :option:`sphinx-build -E` option.

* Use the :option:`sphinx-build -P` option to run Pdb on exceptions.

* Use ``node.pformat()`` and ``node.asdom().toxml()`` to generate a printable
  representation of the document structure.

* Set the configuration variable :confval:`keep_warnings` to True so warnings
  will be displayed in the generated output.

* Set the configuration variable :confval:`nitpicky` to True so that Sphinx
  will complain about references without a known target.

* Set the debugging options in the `Docutils configuration file
  <http://docutils.sourceforge.net/docs/user/config.html>`_.
