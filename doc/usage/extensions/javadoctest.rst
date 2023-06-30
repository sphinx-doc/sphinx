.. highlight:: rest

:mod:`sphinx.ext.javadoctest` -- Test Java snippets in the documentation
========================================================================

.. module:: sphinx.ext.javadoctest
   :synopsis: Test Java snippets in the documentation.

.. index:: pair: automatic; testing
           single: javadoctest
           pair: testing; snippets


It is often helpful to include snippets of Java code in your documentation and
demonstrate the results of executing them. But it is important to ensure that
the documentation stays up-to-date with the code.

This extension allows you to test such code snippets in the documentation in
a natural way. If you mark the code blocks as shown here, the ``javadoctest``
builder will collect them and run them as javadoctest tests.

Within each document, you can assign each snippet to a *group*. Each group
consists of one or more *test* blocks.

When building the docs with the ``javadoctest`` builder, groups are collected for
each document and run one after the other in the order they appear in the file.


Directives
----------

The *group* argument below is interpreted as follows: if it is empty, the block
is assigned to the group named ``default``.  If it is ``*``, the block is
assigned to all groups (including the ``default`` group).  Otherwise, it must be
a comma-separated list of group names.

.. rst:directive:: .. javatestcode:: [group]

   A Java code block for a code-output-style test.

   This directive supports this option:

   * ``hide``, a flag option, hides the code block in other builders.  By
     default it is shown as a highlighted code block.

   .. note::

      Code in a ``testcode`` block is always executed all at once, no matter how
      many statements it contains.  Therefore, output will *not* be generated
      for bare expressions -- use ``System.out.println``.  Example::

         .. javatestcode:: [basic]
            :hide:

            int x = 3;                // this will give no output!
            System.out.println(x+2);  // this will give output

         .. javatestoutput:: [basic]

            5

      Also, please be aware that since the doctest module does not support
      mixing regular output and an exception message in the same snippet, this
      applies to javatestcode/javatestoutput as well.


.. rst:directive:: .. javatestoutput:: [group]

   The corresponding output, or the exception message, for the last
   :rst:dir:`javatestcode` block.

   This directive supports this option:

   * ``hide``, a flag option, hides the output block in other builders.  By
     default it is shown as a literal block without highlighting.

   Example::

      .. javatestcode:: [basic]

         System.out.println("Output     text.");

      .. javatestoutput:: [basic]
         :hide:

         Output     text.

The following is an example for the usage of the directives.  The test via
:rst:dir:`javatestcode` and :rst:dir:`javatestoutput` are equivalent. ::

   The parrot module
   =================

   Test-Output example:

   .. javatestcode:: [advanced]

      void voom(String input) {
         System.out.println("This parrot wouldn't voom if you put " + input + " volts through it!");
      }

      voom("3000");

   This would output:

   .. javatestoutput:: [advanced]

      This parrot wouldn't voom if you put 3000 volts through it!


Skipping tests conditionally
----------------------------

``skipif``, a string option, can be used to skip directives conditionally. This
may be useful e.g. when a different set of tests should be run depending on the
environment (hardware, network/VPN, optional dependencies or different versions
of dependencies). The ``skipif`` option is supported by all of the doctest
directives. Below are typical use cases for ``skipif`` when used for different
directives:

- :rst:dir:`javatestcode`

  - conditionally skip a test
  - customize test code per environment

- :rst:dir:`javatestoutput`

  - conditionally skip output assertion for a skipped test
  - expect different output depending on the environment

The value of the ``skipif`` option is evaluated as a Java expression. If the
result is a true value, the directive is omitted from the test run just as if
it wasn't present in the file at all.

Instead of repeating an expression, the :confval:`doctest_global_setup`
configuration option can be used to assign it to a variable which can then be
used instead.

Here's an example which skips some tests if JDK version is lower than 11:

.. code-block:: py
   :caption: conf.py

   extensions = ['sphinx.ext.javadoctest']
   doctest_global_setup = '''
   int java_version = Integer.parseInt(System.getProperty("java.version").split("\\\.")[0]);
   '''

.. code-block:: rst
   :caption: contents.rst

   .. testcode::
      :skipif: java_version < 11

      System.out.println("42");

   .. testoutput::
      :skipif: java_version < 11

      42


Configuration
-------------

The doctest extension uses the following configuration values:

.. confval:: doctest_default_flags

   By default, these options are enabled:

   - ``ELLIPSIS``, allowing you to put ellipses in the expected output that
     match anything in the actual output;
   - ``IGNORE_EXCEPTION_DETAIL``, causing everything following the leftmost
     colon and any module information in the exception name to be ignored;
   - ``DONT_ACCEPT_TRUE_FOR_1``, rejecting "True" in the output where "1" is
     given -- the default behavior of accepting this substitution is a relic of
     pre-Python 2.2 times.

   .. versionadded:: 1.0

.. confval:: doctest_path

   A list of directories that will be added to :data:`sys.path` when the doctest
   builder is used.  (Make sure it contains absolute paths.)

.. confval:: doctest_global_setup

   Java code that is treated like it were put in a ``testsetup`` directive for
   *every* file that is tested, and for every group.  You can use this to
   e.g. define variables you will always need in your doctests.

   .. versionadded:: 1.0

.. confval:: doctest_global_cleanup

   Python code that is treated like it were put in a ``testcleanup`` directive
   for *every* file that is tested, and for every group.  You can use this to
   e.g. remove any temporary files that the tests leave behind.

   .. versionadded:: 1.0

.. confval:: doctest_test_doctest_blocks

   If this is a nonempty string (the default is ``'default'``), standard reST
   doctest blocks will be tested too.  They will be assigned to the group name
   given.

   reST doctest blocks are simply doctests put into a paragraph of their own,
   like so::

      Some documentation text.

      >>> print(1)
      1

      Some more documentation text.

   (Note that no special ``::`` is used to introduce a doctest block; docutils
   recognizes them from the leading ``>>>``.  Also, no additional indentation is
   used, though it doesn't hurt.)

   If this value is left at its default value, the above snippet is interpreted
   by the doctest builder exactly like the following::

      Some documentation text.

      .. doctest::

         >>> print(1)
         1

      Some more documentation text.

   This feature makes it easy for you to test doctests in docstrings included
   with the :mod:`~sphinx.ext.autodoc` extension without marking them up with a
   special directive.

   Note though that you can't have blank lines in reST doctest blocks.  They
   will be interpreted as one block ending and another one starting.  Also,
   removal of ``<BLANKLINE>`` and ``# doctest:`` options only works in
   :rst:dir:`doctest` blocks, though you may set :confval:`trim_doctest_flags`
   to achieve that in all code blocks with Python console content.
