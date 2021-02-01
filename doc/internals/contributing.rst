======================
Contributing to Sphinx
======================

There are many ways you can contribute to Sphinx, be it filing bug reports or
feature requests, writing new documentation or submitting patches for new or
fixed behavior. This guide serves to illustrate how you can get started with
this.

Getting help
------------

The Sphinx community maintains a number of mailing lists and IRC channels.

Stack Overflow with tag `python-sphinx`_
    Questions and answers about use and development.

sphinx-users <sphinx-users@googlegroups.com>
    Mailing list for user support.

sphinx-dev <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#sphinx-doc on irc.freenode.net
    IRC channel for development questions and user support.

.. _python-sphinx: https://stackoverflow.com/questions/tagged/python-sphinx

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


Writing code
------------

The Sphinx source code is managed using Git and is hosted on `GitHub`__.  The
recommended way for new contributors to submit code to Sphinx is to fork this
repository and submit a pull request after committing changes to their fork.
The pull request will then need to be approved by one of the core developers
before it is merged into the main repository.

.. __: https://github.com/sphinx-doc/sphinx

Getting started
~~~~~~~~~~~~~~~

Before starting on a patch, we recommend checking for open issues or open a
fresh issue to start a discussion around a feature idea or a bug. If you feel
uncomfortable or uncertain about an issue or your changes, feel free to email
the *sphinx-dev* mailing list.

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
   they should be included in the next MINOR release, use the ``A.x`` branch.
   ::

       git checkout A.x

   For incompatible or other substantial changes that should wait until the
   next MAJOR release, use the ``master`` branch.

   For urgent release, a new PATCH branch must be branched from the newest
   release tag (see :doc:`release-process` for detail).

#. Setup a virtual environment.

   This is not necessary for unit testing, thanks to ``tox``, but it is
   necessary if you wish to run ``sphinx-build`` locally or run unit tests
   without the help of ``tox``::

       virtualenv ~/.venv
       . ~/.venv/bin/activate
       pip install -e .

#. Create a new working branch. Choose any name you like. ::

       git checkout -b feature-xyz

#. Hack, hack, hack.

   Write your code along with tests that shows that the bug was fixed or that
   the feature works as expected.

#. Add a bullet point to :file:`CHANGES` if the fix or feature is not trivial
   (small doc updates, typo fixes), then commit::

       git commit -m '#42: Add useful new feature that does this.'

   GitHub recognizes certain phrases that can be used to automatically
   update the issue tracker. For example::

       git commit -m 'Closes #42: Fix invalid markup in docstring of Foo.bar.'

   would close issue #42.

#. Push changes in the branch to your forked repository on GitHub::

       git push origin feature-xyz

#. Submit a pull request from your branch to the respective branch (``master``
   or ``A.x``).

#. Wait for a core developer to review your changes.

Coding style
~~~~~~~~~~~~

Please follow these guidelines when writing code for Sphinx:

* Try to use the same code style as used in the rest of the project.

* For non-trivial changes, please update the :file:`CHANGES` file.  If your
  changes alter existing behavior, please document this.

* New features should be documented.  Include examples and use cases where
  appropriate.  If possible, include a sample that is displayed in the
  generated output.

* When adding a new configuration variable, be sure to document it and update
  :file:`sphinx/cmd/quickstart.py` if it's important enough.

* Add appropriate unit tests.

Style and type checks can be run using ``tox``::

    tox -e mypy
    tox -e flake8

Unit tests
~~~~~~~~~~

Sphinx is tested using `pytest`__ for Python code and `Karma`__ for JavaScript.

.. __: https://docs.pytest.org/en/latest/
.. __: https://karma-runner.github.io

To run Python unit tests, we recommend using ``tox``, which provides a number
of targets and allows testing against multiple different Python environments:

* To list all possible targets::

      tox -av

* To run unit tests for a specific Python version, such as Python 3.6::

      tox -e py36

* To run unit tests for a specific Python version and turn on deprecation
  warnings on so they're shown in the test output::

      PYTHONWARNINGS=all tox -e py36

* Arguments to ``pytest`` can be passed via ``tox``, e.g. in order to run a
  particular test::

      tox -e py36 tests/test_module.py::test_new_feature

You can also test by installing dependencies in your local environment::

    pip install .[test]

To run JavaScript tests, use ``npm``::

    npm install
    npm run test

New unit tests should be included in the ``tests`` directory where
necessary:

* For bug fixes, first add a test that fails without your changes and passes
  after they are applied.

* Tests that need a ``sphinx-build`` run should be integrated in one of the
  existing test modules if possible.  New tests that to ``@with_app`` and
  then ``build_all`` for a few assertions are not good since *the test suite
  should not take more than a minute to run*.

.. versionadded:: 1.8

   Sphinx also runs JavaScript tests.

.. versionadded:: 1.6

   ``sphinx.testing`` is added as a experimental.

.. versionchanged:: 1.5.2

   Sphinx was switched from nose to pytest.

.. todo:: The below belongs in the developer guide

Utility functions and pytest fixtures for testing are provided in
``sphinx.testing``. If you are a developer of Sphinx extensions, you can write
unit tests with using pytest. At this time, ``sphinx.testing`` will help your
test implementation.

How to use pytest fixtures that are provided by ``sphinx.testing``?  You can
require ``'sphinx.testing.fixtures'`` in your test modules or ``conftest.py``
files like this::

   pytest_plugins = 'sphinx.testing.fixtures'

If you want to know more detailed usage, please refer to ``tests/conftest.py``
and other ``test_*.py`` files under ``tests`` directory.


Writing documentation
---------------------

.. todo:: Add a more extensive documentation contribution guide.

You can build documentation using ``tox``::

    tox -e docs

Translations
~~~~~~~~~~~~

The parts of messages in Sphinx that go into builds are translated into several
locales.  The translations are kept as gettext ``.po`` files translated from the
master template :file:`sphinx/locale/sphinx.pot`.

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
<https://www.transifex.com/sphinx-doc/sphinx-1/>`_.  There ``tx`` client tool,
which is provided by the ``transifex_client`` Python package, can be used to
pull translations in ``.po`` format from Transifex.  To do this, go to
``sphinx/locale`` and then run ``tx pull -f -l LANG`` where ``LANG`` is an
existing language identifier.  It is good practice to run ``python setup.py
update_catalog`` afterwards to make sure the ``.po`` file has the canonical
Babel formatting.


Debugging tips
--------------

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
  are generated by this `modified snowballcode generator
  <https://github.com/shibukawa/snowball>`_.  Generated `JSX
  <https://jsx.github.io/>`_ files are in `this repository
  <https://github.com/shibukawa/snowball-stemmer.jsx>`_.  You can get the
  resulting JavaScript files using the following command::

      npm install
      node_modules/.bin/grunt build # -> dest/*.global.js
