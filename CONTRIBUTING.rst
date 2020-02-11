.. highlight:: console

Sphinx Developer's Guide
========================

.. topic:: Abstract

   This document describes the development process of Sphinx, a documentation
   system used by developers to document systems used by other developers to
   develop other systems that may also be documented using Sphinx.

.. contents::
   :local:

The Sphinx source code is managed using Git and is hosted on GitHub.

    git clone git://github.com/sphinx-doc/sphinx

.. rubric:: Community

sphinx-users <sphinx-users@googlegroups.com>
    Mailing list for user support.

sphinx-dev <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#sphinx-doc on irc.freenode.net
    IRC channel for development questions and user support.


Bug Reports and Feature Requests
--------------------------------

If you have encountered a problem with Sphinx or have an idea for a new
feature, please submit it to the `issue tracker`_ on GitHub or discuss it
on the `sphinx-dev`_ mailing list.

For bug reports, please include the output produced during the build process
and also the log file Sphinx creates after it encounters an unhandled
exception.  The location of this file should be shown towards the end of the
error message.

Including or providing a link to the source files involved may help us fix the
issue.  If possible, try to create a minimal project that produces the error
and post that instead.

.. _`issue tracker`: https://github.com/sphinx-doc/sphinx/issues
.. _`sphinx-dev`: mailto:sphinx-dev@googlegroups.com


Contributing to Sphinx
----------------------

The recommended way for new contributors to submit code to Sphinx is to fork
the repository on GitHub and then submit a pull request after
committing the changes.  The pull request will then need to be approved by one
of the core developers before it is merged into the main repository.

#. Check for open issues or open a fresh issue to start a discussion around a
   feature idea or a bug.
#. If you feel uncomfortable or uncertain about an issue or your changes, feel
   free to email the *sphinx-dev* mailing list.
#. Fork `the repository`_ on GitHub to start making your changes to the
   ``master`` branch for next MAJOR version, or ``X.Y`` branch for next
   MINOR version (see `Branch Model`_).
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.
#. Send a pull request and bug the maintainer until it gets merged and
   published. Make sure to add yourself to AUTHORS_ and the change to
   CHANGES_.

.. _`the repository`: https://github.com/sphinx-doc/sphinx
.. _AUTHORS: https://github.com/sphinx-doc/sphinx/blob/master/AUTHORS
.. _CHANGES: https://github.com/sphinx-doc/sphinx/blob/master/CHANGES


Getting Started
~~~~~~~~~~~~~~~

These are the basic steps needed to start developing on Sphinx.

#. Create an account on GitHub.

#. Fork the main Sphinx repository (`sphinx-doc/sphinx
   <https://github.com/sphinx-doc/sphinx>`_) using the GitHub interface.

#. Clone the forked repository to your machine. ::

       git clone https://github.com/USERNAME/sphinx
       cd sphinx

#. Checkout the appropriate branch.

   Sphinx adopts Semantic Versioning 2.0.0 (refs: https://semver.org/ ).

   For changes that preserves backwards-compatibility of API and features,
   they should be included in the next MINOR release, use the ``X.Y`` branch.
   ::

       git checkout X.Y

   For incompatible or other substantial changes that should wait until the
   next MAJOR release, use the ``master`` branch.

   For urgent release, a new PATCH branch must be branched from the newest
   release tag (see `Branch Model`_ for detail).

#. Setup a virtual environment.

   This is not necessary for unit testing, thanks to ``tox``, but it is
   necessary if you wish to run ``sphinx-build`` locally or run unit tests
   without the help of ``tox``. ::

       virtualenv ~/.venv
       . ~/.venv/bin/activate
       pip install -e .

#. Create a new working branch.  Choose any name you like. ::

       git checkout -b feature-xyz

#. Hack, hack, hack.

   For tips on working with the code, see the `Coding Guide`_.

#. Test, test, test.

   Testing is best done through ``tox``, which provides a number of targets and
   allows testing against multiple different Python environments:

   * To list all possible targets::

         tox -av

   * To run unit tests for a specific Python version, such as 3.6::

         tox -e py36

   * To run unit tests for a specific Python version and turn on deprecation
     warnings on so they're shown in the test output::

         PYTHONWARNINGS=all tox -e py36

   * To run code style and type checks::

         tox -e mypy
         tox -e flake8

   * Arguments to ``pytest`` can be passed via ``tox``, e.g. in order to run a
     particular test::

       tox -e py36 tests/test_module.py::test_new_feature

   * To build the documentation::

         tox -e docs

   * To build the documentation in multiple formats::

         tox -e docs -- -b html,latexpdf

   * To run JavaScript tests with `Karma <https://karma-runner.github.io>`_,
     execute the following commands (requires `Node.js <https://nodejs.org>`_)::

      npm install
      npm run test

   You can also test by installing dependencies in your local environment. ::

       pip install .[test]

   New unit tests should be included in the ``tests`` directory where
   necessary:

   * For bug fixes, first add a test that fails without your changes and passes
     after they are applied.

   * Tests that need a ``sphinx-build`` run should be integrated in one of the
     existing test modules if possible.  New tests that to ``@with_app`` and
     then ``build_all`` for a few assertions are not good since *the test suite
     should not take more than a minute to run*.

#. Please add a bullet point to :file:`CHANGES` if the fix or feature is not
   trivial (small doc updates, typo fixes).  Then commit::

       git commit -m '#42: Add useful new feature that does this.'

   GitHub recognizes certain phrases that can be used to automatically
   update the issue tracker.

   For example::

       git commit -m 'Closes #42: Fix invalid markup in docstring of Foo.bar.'

   would close issue #42.

#. Push changes in the branch to your forked repository on GitHub. ::

       git push origin feature-xyz

#. Submit a pull request from your branch to the respective branch (``master``
   or ``X.Y``).

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


Locale updates
~~~~~~~~~~~~~~

The parts of messages in Sphinx that go into builds are translated into several
locales.  The translations are kept as gettext ``.po`` files translated from the
master template ``sphinx/locale/sphinx.pot``.

Sphinx uses `Babel <http://babel.pocoo.org/en/latest/>`_ to extract messages
and maintain the catalog files.  It is integrated in ``setup.py``:

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
values for :confval:`language` in ``doc/usage/configuration.rst``.

The Sphinx core messages can also be translated on `Transifex
<https://www.transifex.com/>`_.  There exists a client tool named ``tx`` in the
Python package "transifex_client", which can be used to pull translations in
``.po`` format from Transifex.  To do this, go to ``sphinx/locale`` and then run
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
  :file:`sphinx/cmd/quickstart.py` if it's important enough.

* Add appropriate unit tests.


Debugging Tips
~~~~~~~~~~~~~~

* Delete the build cache before building documents if you make changes in the
  code by running the command ``make clean`` or using the
  :option:`sphinx-build -E` option.

* Use the :option:`sphinx-build -P` option to run ``pdb`` on exceptions.

* Use ``node.pformat()`` and ``node.asdom().toxml()`` to generate a printable
  representation of the document structure.

* Set the configuration variable :confval:`keep_warnings` to ``True`` so
  warnings will be displayed in the generated output.

* Set the configuration variable :confval:`nitpicky` to ``True`` so that Sphinx
  will complain about references without a known target.

* Set the debugging options in the `Docutils configuration file
  <http://docutils.sourceforge.net/docs/user/config.html>`_.

* JavaScript stemming algorithms in ``sphinx/search/*.py`` (except ``en.py``)
  are generated by this
  `modified snowballcode generator <https://github.com/shibukawa/snowball>`_.
  Generated `JSX <https://jsx.github.io/>`_ files are
  in `this repository <https://github.com/shibukawa/snowball-stemmer.jsx>`_.
  You can get the resulting JavaScript files using the following command::

     npm install
     node_modules/.bin/grunt build # -> dest/*.global.js


Branch Model
------------

Sphinx project uses following branches for developing that conforms to Semantic
Versioning 2.0.0 (refs: https://semver.org/ ).

``master``
    Development for MAJOR version.
    All changes including incompatible behaviors and public API updates are
    allowed.

``X.Y``
    Where ``X.Y`` is the ``MAJOR.MINOR`` release.  Used to maintain current
    MINOR release. All changes are allowed if the change preserves
    backwards-compatibility of API and features.

    Only the most recent ``MAJOR.MINOR`` branch is currently retained. When a
    new MAJOR version is released, the old ``MAJOR.MINOR`` branch will be
    deleted and replaced by an equivalent tag.

``X.Y.Z``
    Where ``X.Y.Z`` is the ``MAJOR.MINOR.PATCH`` release.  Only
    backwards-compatible bug fixes are allowed. In Sphinx project, PATCH
    version is used for urgent bug fix.

    ``MAJOR.MINOR.PATCH`` branch will be branched from the ``v`` prefixed
    release tag (ex. make 2.3.1 that branched from v2.3.0) when a urgent
    release is needed. When new PATCH version is released, the branch will be
    deleted and replaced by an equivalent tag (ex. v2.3.1).


Deprecating a feature
---------------------

There are a couple reasons that code in Sphinx might be deprecated:

* If a feature has been improved or modified in a backwards-incompatible way,
  the old feature or behavior will be deprecated.

* Sometimes Sphinx will include a backport of a Python library that's not
  included in a version of Python that Sphinx currently supports. When Sphinx
  no longer needs to support the older version of Python that doesn't include
  the library, the library will be deprecated in Sphinx.

As the :ref:`deprecation-policy` describes, the first release of Sphinx that
deprecates a feature (``A.B``) should raise a ``RemovedInSphinxXXWarning``
(where ``XX`` is the Sphinx version where the feature will be removed) when the
deprecated feature is invoked. Assuming we have good test coverage, these
warnings are converted to errors when running the test suite with warnings
enabled::

    pytest -Wall

Thus, when adding a ``RemovedInSphinxXXWarning`` you need to eliminate or
silence any warnings generated when running the tests.

.. _deprecation-policy:

Deprecation policy
------------------

MAJOR and MINOR releases may deprecate certain features from previous
releases. If a feature is deprecated in a release A.x, it will continue to
work in all A.x.x versions (for all versions of x). It will continue to work
in all B.x.x versions but raise deprecation warnings. Deprecated features
will be removed at the C.0.0. It means the deprecated feature will work during
2 MAJOR releases at least.

So, for example, if we decided to start the deprecation of a function in
Sphinx 2.x:

* Sphinx 2.x will contain a backwards-compatible replica of the function
  which will raise a ``RemovedInSphinx40Warning``.

* Sphinx 3.x will still contain the backwards-compatible replica.

* Sphinx 4.0 will remove the feature outright.

The warnings are displayed by default. You can turn off display of these
warnings with:

* ``PYTHONWARNINGS= make html`` (Linux/Mac)
* ``export PYTHONWARNINGS=`` and do ``make html`` (Linux/Mac)
* ``set PYTHONWARNINGS=`` and do ``make html`` (Windows)

Unit Testing
------------

Sphinx has been tested with pytest runner. Sphinx developers write unit tests
using pytest notation. Utility functions and pytest fixtures for testing are
provided in ``sphinx.testing``. If you are a developer of Sphinx extensions,
you can write unit tests with using pytest. At this time, ``sphinx.testing``
will help your test implementation.

How to use pytest fixtures that are provided by ``sphinx.testing``?
You can require ``'sphinx.testing.fixtures'`` in your test modules or
``conftest.py`` files like this::

   pytest_plugins = 'sphinx.testing.fixtures'

If you want to know more detailed usage, please refer to ``tests/conftest.py``
and other ``test_*.py`` files under ``tests`` directory.

.. note::

   Prior to Sphinx - 1.5.2, Sphinx was running the test with nose.

.. versionadded:: 1.6
   ``sphinx.testing`` as a experimental.

.. versionadded:: 1.8
   Sphinx also runs JavaScript tests.
