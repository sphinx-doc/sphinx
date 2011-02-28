.. highlight:: rest

:mod:`sphinx.ext.doctest` -- Test snippets in the documentation
===============================================================

.. module:: sphinx.ext.doctest
   :synopsis: Test snippets in the documentation.

.. index:: pair: automatic; testing
           single: doctest
           pair: testing; snippets


This extension allows you to test snippets in the documentation in a natural
way.  It works by collecting specially-marked up code blocks and running them as
doctest tests.

Within one document, test code is partitioned in *groups*, where each group
consists of:

* zero or more *setup code* blocks (e.g. importing the module to test)
* one or more *test* blocks

When building the docs with the ``doctest`` builder, groups are collected for
each document and run one after the other, first executing setup code blocks,
then the test blocks in the order they appear in the file.

There are two kinds of test blocks:

* *doctest-style* blocks mimic interactive sessions by interleaving Python code
  (including the interpreter prompt) and output.

* *code-output-style* blocks consist of an ordinary piece of Python code, and
  optionally, a piece of output for that code.

The doctest extension provides four directives.  The *group* argument is
interpreted as follows: if it is empty, the block is assigned to the group named
``default``.  If it is ``*``, the block is assigned to all groups (including the
``default`` group).  Otherwise, it must be a comma-separated list of group
names.

.. rst:directive:: .. testsetup:: [group]

   A setup code block.  This code is not shown in the output for other builders,
   but executed before the doctests of the group(s) it belongs to.


.. rst:directive:: .. testcleanup:: [group]

   A cleanup code block.  This code is not shown in the output for other
   builders, but executed after the doctests of the group(s) it belongs to.

   .. versionadded:: 1.1


.. rst:directive:: .. doctest:: [group]

   A doctest-style code block.  You can use standard :mod:`doctest` flags for
   controlling how actual output is compared with what you give as output.  By
   default, these options are enabled: ``ELLIPSIS`` (allowing you to put
   ellipses in the expected output that match anything in the actual output),
   ``IGNORE_EXCEPTION_DETAIL`` (not comparing tracebacks),
   ``DONT_ACCEPT_TRUE_FOR_1`` (by default, doctest accepts "True" in the output
   where "1" is given -- this is a relic of pre-Python 2.2 times).

   This directive supports two options:

   * ``hide``, a flag option, hides the doctest block in other builders.  By
     default it is shown as a highlighted doctest block.

   * ``options``, a string option, can be used to give a comma-separated list of
     doctest flags that apply to each example in the tests.  (You still can give
     explicit flags per example, with doctest comments, but they will show up in
     other builders too.)

   Note that like with standard doctests, you have to use ``<BLANKLINE>`` to
   signal a blank line in the expected output.  The ``<BLANKLINE>`` is removed
   when building presentation output (HTML, LaTeX etc.).

   Also, you can give inline doctest options, like in doctest::

      >>> datetime.date.now()   # doctest: +SKIP
      datetime.date(2008, 1, 1)

   They will be respected when the test is run, but stripped from presentation
   output.


.. rst:directive:: .. testcode:: [group]

   A code block for a code-output-style test.

   This directive supports one option:

   * ``hide``, a flag option, hides the code block in other builders.  By
     default it is shown as a highlighted code block.

   .. note::

      Code in a ``testcode`` block is always executed all at once, no matter how
      many statements it contains.  Therefore, output will *not* be generated
      for bare expressions -- use ``print``.  Example::

          .. testcode::

             1+1        # this will give no output!
             print 2+2  # this will give output

          .. testoutput::

             4

      Also, please be aware that since the doctest module does not support
      mixing regular output and an exception message in the same snippet, this
      applies to testcode/testoutput as well.


.. rst:directive:: .. testoutput:: [group]

   The corresponding output, or the exception message, for the last
   :rst:dir:`testcode` block.

   This directive supports two options:

   * ``hide``, a flag option, hides the output block in other builders.  By
     default it is shown as a literal block without highlighting.

   * ``options``, a string option, can be used to give doctest flags
     (comma-separated) just like in normal doctest blocks.

   Example::

      .. testcode::

         print 'Output     text.'

      .. testoutput::
         :hide:
         :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

         Output text.


The following is an example for the usage of the directives.  The test via
:rst:dir:`doctest` and the test via :rst:dir:`testcode` and :rst:dir:`testoutput` are
equivalent. ::

   The parrot module
   =================

   .. testsetup:: *

      import parrot

   The parrot module is a module about parrots.

   Doctest example:

   .. doctest::

      >>> parrot.voom(3000)
      This parrot wouldn't voom if you put 3000 volts through it!

   Test-Output example:

   .. testcode::

      parrot.voom(3000)

   This would output:

   .. testoutput::

      This parrot wouldn't voom if you put 3000 volts through it!


There are also these config values for customizing the doctest extension:

.. confval:: doctest_path

   A list of directories that will be added to :data:`sys.path` when the doctest
   builder is used.  (Make sure it contains absolute paths.)

.. confval:: doctest_global_setup

   Python code that is treated like it were put in a ``testsetup`` directive for
   *every* file that is tested, and for every group.  You can use this to
   e.g. import modules you will always need in your doctests.

   .. versionadded:: 0.6

.. confval:: doctest_global_cleanup

   Python code that is treated like it were put in a ``testcleanup`` directive
   for *every* file that is tested, and for every group.  You can use this to
   e.g. remove any temporary files that the tests leave behind.

   .. versionadded:: 1.1

.. confval:: doctest_test_doctest_blocks

   If this is a nonempty string (the default is ``'default'``), standard reST
   doctest blocks will be tested too.  They will be assigned to the group name
   given.

   reST doctest blocks are simply doctests put into a paragraph of their own,
   like so::

      Some documentation text.

      >>> print 1
      1

      Some more documentation text.

   (Note that no special ``::`` is used to introduce a doctest block; docutils
   recognizes them from the leading ``>>>``.  Also, no additional indentation is
   used, though it doesn't hurt.)

   If this value is left at its default value, the above snippet is interpreted
   by the doctest builder exactly like the following::

      Some documentation text.

      .. doctest::

         >>> print 1
         1

      Some more documentation text.

   This feature makes it easy for you to test doctests in docstrings included
   with the :mod:`~sphinx.ext.autodoc` extension without marking them up with a
   special directive.

   Note though that you can't have blank lines in reST doctest blocks.  They
   will be interpreted as one block ending and another one starting.  Also,
   removal of ``<BLANKLINE>`` and ``# doctest:`` options only works in
   :rst:dir:`doctest` blocks, though you may set :confval:`trim_doctest_flags` to
   achieve that in all code blocks with Python console content.
