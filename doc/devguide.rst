**************************
 Sphinx Developer's Guide
**************************

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

sphinx-dev  <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#pocoo on irc.freenode.net
    IRC channel for development questions and user support.

    This channel is shared with other Pocoo projects.  Archived logs are
    available `here <http://dev.pocoo.org/irclogs/>`_.

.. _`BitBucket`: http://bitbucket.org
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

.. _`issue tracker`: http://bitbucket.org/birkenfeld/sphinx/issues


Contributing to Sphinx
----------------------

The recommended way to contribute code to Sphinx is to fork the Mercurial
repository on BitBucket and then submit a pull request after committing your
changes.

These are the basic steps needed to start developing.

.. todo::

   Recommend using named branches?


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

#. Setup your Python environment. ::

       virtualenv ~/sphinxenv
       . ~/sphinxenv/bin/activate
       pip install -e .

#. Hack, hack, hack.

   For tips on working with the code, see the `Coding Guide`_.

#. Test, test, test.

   Run the unit tests::

       pip install nose
       make test

   Build the documentation and check the output for different builders::

       cd docs
       make clean html text man info latexpdf

   Run the unit tests under different Python environments using
   :program:`tox`::

       pip install tox
       tox -v

   Add a new unit test in the ``tests`` directory if you can.

   For bug fixes, first add a test that fails without your changes and passes
   after they are applied.

#. Commit your changes. ::

       hg commit -m 'Add useful new feature that does this.'

   BitBucket recognizes `certain phrases`__ that can be used to automatically
   update the issue tracker.

   For example::

       hg commit -m 'Closes #42: Fix invalid markup in docstring of Foo.bar.'

   would close issue #42.

   __ https://confluence.atlassian.com/display/BITBUCKET/Automatically+Resolving+Issues+when+Users+Push+Code

#. Push changes to your forked repo on BitBucket. ::

       hg push

#. Submit a pull request from your repo to ``birkenfeld/sphinx`` using the
   BitBucket interface.


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
  :file:`sphinx/quickstart.py`.

* Use the included :program:`utils/check_sources.py` script to check for
  common formatting issues (trailing whitespace, lengthy lines, etc).


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
