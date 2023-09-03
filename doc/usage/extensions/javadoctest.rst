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
a natural way.  If you mark the code blocks as shown here, the ``javadoctest``
builder will collect them and run them as javadoctest tests.

Within each document, you can assign each snippet to a *group*. Each group
consists of:

* zero or more *setup code* blocks (e.g. importing the module to test)
* one or more *test* blocks

When building the docs with the ``javadoctest`` builder, groups are collected for
each document and run one after the other, first executing setup code blocks,
then the test blocks in the order they appear in the file.

There are two kinds of test blocks:

* *doctest-style* blocks mimic interactive sessions by interleaving Java code
  (including the interpreter prompt) and output.

* *code-output-style* blocks consist of an ordinary piece of Java code, and
  optionally, a piece of output for that code.


Directives
----------

The *group* argument below is interpreted as follows: if it is empty, the block
is assigned to the group named ``default``.  If it is ``*``, the block is
assigned to all groups (including the ``default`` group).  Otherwise, it must be
a comma-separated list of group names.

.. rst:directive:: .. javatestsetup:: [group]

   A setup code block.  This code is not shown in the output for other builders,
   but executed before the doctests of the group(s) it belongs to.


.. rst:directive:: .. javatestcleanup:: [group]

   A cleanup code block.  This code is not shown in the output for other
   builders, but executed after the doctests of the group(s) it belongs to.


.. rst:directive:: .. javadoctest:: [group]

   A doctest-style code block.  You can use standard :mod:`doctest` flags for
   controlling how actual output is compared with what you give as output.  The
   default set of flags is specified by the `doctest_default_flags`
   configuration variable.

   This directive supports five options:

   * ``hide``, a flag option, hides the doctest block in other builders.  By
     default it is shown as a highlighted doctest block.

   * ``options``, a string option, can be used to give a comma-separated list of
     doctest flags that apply to each example in the tests.  (You still can give
     explicit flags per example, with doctest comments, but they will show up in
     other builders too.)

   * ``javaversion``, a string option, can be used to specify the required Java
     version for the example to be tested. For instance, in the following case
     the example will be tested only for Java versions greater than 11.0::

         .. doctest::
            :javaversion: > 11.0

     The following operands are supported:

     * ``~=``: Compatible release clause
     * ``==``: Version matching clause
     * ``!=``: Version exclusion clause
     * ``<=``, ``>=``: Inclusive ordered comparison clause
     * ``<``, ``>``: Exclusive ordered comparison clause
     * ``===``: Arbitrary equality clause.

     ``javaversion`` option is followed :pep:`PEP-440: Version Specifiers
     <440#version-specifiers>`.

   * ``trim-doctest-flags`` and ``no-trim-doctest-flags``, a flag option,
     doctest flags (comments looking like ``# doctest: FLAG, ...``) at the
     ends of lines and ``<BLANKLINE>`` markers are removed (or not removed)
     individually.  Default is ``trim-doctest-flags``.

   Note that like with standard doctests, you have to use ``<BLANKLINE>`` to
   signal a blank line in the expected output.  The ``<BLANKLINE>`` is removed
   when building presentation output (HTML, LaTeX etc.).

.. rst:directive:: .. javatestcode:: [group]

   A code block for a code-output-style test.

   This directive supports three options:

   * ``hide``, a flag option, hides the code block in other builders.  By
     default it is shown as a highlighted code block.

   * ``trim-doctest-flags`` and ``no-trim-doctest-flags``, a flag option,
     doctest flags (comments looking like ``# doctest: FLAG, ...``) at the
     ends of lines and ``<BLANKLINE>`` markers are removed (or not removed)
     individually.  Default is ``trim-doctest-flags``.

   .. note::

      Code in a ``javatestcode`` block is always executed all at once, no matter how
      many statements it contains.  Therefore, output will *not* be generated
      for bare expressions -- use ``System.out.print``.  Example::

         .. javatestcode:: [basic]
            :hide:

            int x = 3;                // this will give no output!
            System.out.print(x+2);  // this will give output

         .. javatestoutput:: [basic]

            5

.. rst:directive:: .. javatestoutput:: [group]

   The corresponding output, or the exception message, for the last
   :rst:dir:`javatestcode` block.

   This directive supports four options:

   * ``hide``, a flag option, hides the output block in other builders.  By
     default it is shown as a literal block without highlighting.

   * ``options``, a string option, can be used to give doctest flags
     (comma-separated) just like in normal doctest blocks.

   * ``trim-doctest-flags`` and ``no-trim-doctest-flags``, a flag option,
     doctest flags (comments looking like ``# doctest: FLAG, ...``) at the
     ends of lines and ``<BLANKLINE>`` markers are removed (or not removed)
     individually.  Default is ``trim-doctest-flags``.

   Example::

     .. javatestcode::
        :hide:

         System.out.println("Output         text.");

     .. javatestoutput::
        :hide:
        :options: +NORMALIZE_WHITESPACE

         Output text.

The following is an example for the usage of the directives.  The test via
:rst:dir:`javadoctest` and the test via :rst:dir:`javatestcode` and
:rst:dir:`javatestoutput` are equivalent. ::

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

- :rst:dir:`javatestsetup` and :rst:dir:`javatestcleanup`

  - conditionally skip test setup and/or cleanup
  - customize setup/cleanup code per environment

- :rst:dir:`javadoctest`

  - conditionally skip both a test and its output verification

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

   .. javatestcode::
      :skipif: java_version < 11

      System.out.println("42");

   .. javatestoutput::
      :skipif: java_version < 11

      42


Configuration
-------------

The doctest extension uses the following configuration values:

.. confval:: javadoctest_global_setup

   Java code that is treated like it were put in a ``javatestsetup`` directive for
   *every* file that is tested, and for every group.  You can use this to
   e.g. import modules you will always need in your doctests.

.. confval:: javadoctest_global_cleanup

   Java code that is treated like it were put in a ``javatestcleanup`` directive
   for *every* file that is tested, and for every group.  You can use this to
   e.g. remove any temporary files that the tests leave behind.

.. confval:: javadoctest_config

   In case we need to test documentation for projects that consume only Java native
   libraries then only is needed to define `conf.py` with flavor `java`. This is a
   default configuration.

   .. code-block:: rst
      :caption: conf.py
      :emphasize-lines: 6-8

         extensions = [
             'sphinx.ext.javadoctest',
         ]
         project = 'test project for javadoctest'
         root_doc = 'javadoctest'
         java_doctest_config = {
             'flavor': 'java',
         }


   If we need to test documentation for projects that consume Java native libraries
   and third-party Java dependencies, then these dependencies need to be configured
   or added through a dependency management tool such as Maven or Gradle. Currently,
   only Maven is supported. In this case is needed to define by `conf.py` a flavor
   with `java_with_maven`, and also define where is your maven project that contains
   third dependencies thru an absolute `path`.

   .. code-block:: rst
      :caption: conf.py
      :emphasize-lines: 7-10

         import pathlib
         extensions = [
           'sphinx.ext.javadoctest',
         ]
         project = 'Test project for javadoctest with Java Maven'
         root_doc = 'maven'
         javadoctest_config = {
           'flavor': 'java_with_maven',
           'path': pathlib.Path(__file__).parent / 'example',
