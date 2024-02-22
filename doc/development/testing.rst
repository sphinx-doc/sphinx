.. _testing:

=======
Testing
=======

The :mod:`!sphinx.testing` module provides utility classes, functions, fixtures
and markers for testing with `pytest`_. Objects that are not documented on this
page are considered an implementation detail and can be removed without prior
notice. Enable the plugin by adding the following line in  ``conftest.py``:

.. code-block:: python
   :caption: conftest.py

   pytest_plugins = ['sphinx.testing.fixtures']

This rest of the section is dedicated to documenting the testing features but
the reader is assumed to have some prior knowledge on `pytest`_.

.. _pytest: https://docs.pytest.org/en/latest/

.. todo(picnixz)
.. todo:: Add a tutorial section

Markers
-------

.. todo(picnixz): add force-multi-line-parameter-list when implemented
.. py:decorator:: pytest.mark.sphinx(\
                     buildername="html", *, \
                     srcdir=None, testroot="root", confoverrides=None,\
                     freshenv=False, warningiserror=False, tags=None,\
                     verbosity=0, parallel=0, keep_going=False,\
                     builddir=None, docutils_conf=None, isolate=False\
                  )

   Marker to configure the testing application.

   :param buildername: The builder name.
   :type buildername: str
   :param srcdir: A custom sources directory name where to copy testroot files.
   :type srcdir: str | None
   :param testroot: The testroot ID (see :ref:`testing-testroot`).
   :type testroot: str
   :param confoverrides: User-defined configuration values.
   :type confoverrides: dict[str, Any] | None
   :param freshenv: Indicate whether to use a saved environment or not.
   :type freshenv: bool
   :param warningiserror: Treat warnings as errors.
   :type warningiserror: bool
   :param tags: The list of configuration tags (see :ref:`Tags <conf-tags>`).
   :type tags: list[str]
   :param verbosity: The logger verbosity.
   :type verbosity: int
   :param parallel: The number of parallel workers.
   :type parallel: int
   :param keep_going: Keep going when getting warnings treated as errors.
   :type keep_going: bool
   :param builddir: Absolute path to a custom build directory.
   :type builddir: pathlib.Path | None
   :param docutils_conf: Custom docutils configuration.
   :type docutils_conf: str | None
   :param isolate: The isolation policy (see :ref:`testing-isolation`).
   :type isolate: bool | Literal["none", "once", "always"]

   When *srcdir* is not specified, it is auto-generated according to the
   isolation policy and/or the *testroot* value. If a test requires an
   explicit *srcdir*, it is preferred to use :func:`make_app`.

   .. deprecated:: 7.3

      The *srcdir* parameter is deprecated in favor of ``isolate=True``
      or ``isolate='once'`` combined with :func:`pytest.mark.test_params`.

   .. deprecated:: 7.3

      The *freshenv* parameter is deprecated in favor of ``isolate=True``.

   .. seealso::

      :func:`sphinx.testing.fixtures.rootdir`

      :func:`sphinx.testing.fixtures.default_testroot`

      :func:`sphinx.testing.fixtures.testroot_prefix`

      :func:`sphinx.testing.fixtures.testroot_finder`

      :func:`sphinx.testing.fixtures.sphinx_builder`

      :func:`sphinx.testing.fixtures.sphinx_isolation`

.. py:decorator:: pytest.mark.test_params(*, shared_result=None)

   :param shared_result: The shared result ID (see :ref:`testing-sharing`).
   :type shared_result: str

   .. note::

      The statements ``@pytest.mark.test_params(shared_result=...)``
      and ``@pytest.mark.sphinx(..., srcdir=..., ...)`` are mutually
      exclusive, unless their values are identical.

.. py:decorator:: pytest.mark.isolate(policy=None, /)

   Marker specifying the isolation policy.

   :param policy: The isolation policy (see :ref:`testing-isolation`).
   :type policy: bool | typing.Literal["none", "once", "always"] | None

   .. code-block:: python

      @pytest.mark.isolate('none')
      # or: @pytest.mark.sphinx(..., isolate=False, ...)
      def test(): ...

      @pytest.mark.isolate('once')
      # or: @pytest.mark.sphinx(..., isolate='once', ...)
      def test(): ...

      @pytest.mark.isolate('always')
      # or: @pytest.mark.sphinx(..., isolate='always', ...)
      # or: @pytest.mark.sphinx(..., isolate=True, ...)
      def test(): ...

Fixtures
--------

.. py:currentmodule:: sphinx.testing.fixtures

.. py:function:: app() -> SphinxTestApp

   Fixture for the test :class:`~sphinx.testing.util.SphinxTestApp` object.

   This makes

   .. code-block:: python

      def test(app):
          app.build()

   equivalent to

   .. code-block:: python

      def test(app_params, make_app):
          args, kwargs = app_params
          app = make_app(*args, **kwargs)
          app.build()

.. py:function:: app_params() -> tuple[list[Any], dict[str, Any]]

   Fixture for accessing the application positional and keyword arguments
   specified by :func:`pytest.mark.sphinx` and other markers.

   Usage:

   .. code-block:: python

      @pytest.mark.sphinx(testroot='foo')
      def test(app_params):
          args, kwargs = app_params
          assert kwargs['testroot'] == 'foo'

.. py:function:: make_app() -> Callable[..., SphinxTestApp]

   Factory function for a :class:`~sphinx.testing.util.SphinxTestApp` object.

   Usage:

   .. code-block:: python

      @pytest.mark.sphinx(testroot='foo')
      def test_foo(app_params, make_app):
          args, kwargs = app_params
          app = make_app(*args, **kwargs)

.. py:function:: status() -> io.StringIO

   Fixture for accessing the underlying :class:`~io.StringIO` object
   containing the application status messages.

.. py:function:: warning() -> io.StringIO

   Fixture for accessing the underlying :class:`~io.StringIO` object
   containing the application warning messages.

.. py:function:: sphinx_test_tempdir() -> pathlib.Path

   The base temporary directory containing the sources directories
   where testroot directories are copied to.

   This fixture only supports redefinition in a ``conftest.py`` file.

.. py:function:: sphinx_builder() -> str

   The default builder name (defaults: ``"html"``).

   This fixture supports redefinition in a ``conftest.py`` file or directly
   in the test module file and indirect parametrization at the function level.

   .. code-block:: python

      @pytest.fixture()
      def sphinx_builder():
          return 'dummy'

      @pytest.mark.sphinx()
      def test(app):
          assert app.builder.name == 'dummy'

.. py:function:: sphinx_isolation() -> bool | None
                 sphinx_isolation() -> Literal["none", "once", "always"]

   The default isolation policy (defaults: ``False``).

   .. seealso:: :ref:`testing-isolation`

   This fixture supports redefinition in a ``conftest.py`` file or directly
   in the test module file and indirect parametrization at the function level.

   .. code-block:: python

      @pytest.fixture()
      def sphinx_isolation():
          return True

Testroot-related fixtures
^^^^^^^^^^^^^^^^^^^^^^^^^

The following fixtures are used to configure how testroot files are discovered.

See :ref:`testing-testroot` for details.

.. py:function:: rootdir() -> str | os.PathLike[str] | None

   The root directory containing testroot directories (defaults: ``None``).

   This fixture supports redefinition in a ``conftest.py`` file or directly
   in the test module file and indirect parametrization at the function level.

   .. seealso::

      :func:`sphinx.testing.fixtures.default_testroot`
      :func:`sphinx.testing.fixtures.testroot_prefix`
      :func:`sphinx.testing.fixtures.testroot_finder`

.. py:function:: testroot_prefix() -> str | None

   The testroot prefix (defaults: ``"test-"``).

   This fixture supports redefinition in a ``conftest.py`` file or directly
   in the test module file and indirect parametrization at the function level.

   .. code-block:: python

      @pytest.fixture()
      def testroot_prefix():
          return '0000-'

      @pytest.mark.sphinx(testroot='foo')
      def test(app):
          assert app.srcdir.name.startswith('0000-foo')

.. py:function:: default_testroot() -> str | None

   Fixture containing the default testroot ID (defaults: ``"root"``).

   This fixture supports redefinition in a ``conftest.py`` file or directly
   in the test module file and indirect parametrization at the function level.

   .. code-block:: python

      @pytest.fixture()
      def default_testroot():
          return 'new-default'

      @pytest.mark.sphinx()
      def test(app, testroot_prefix):
          srcdir_name = testroot_prefix + 'new-default'
          assert app.srcdir.name.startswith(srcdir_name)

.. py:function:: testroot_finder() -> TestRootFinder

   Fixture specifying the object responsible for finding the testroot files.

   This fixture can be overridden in a ``conftest.py`` file or customized
   via :func:`.rootdir`, :func:`.testroot_prefix` or :func:`.default_testroot`.

   Indirect parametrization should be done on the aforementioned fixtures and
   not on this fixture directly.

Utility classes
---------------

.. autoclass:: sphinx.testing.pytest_util.TestRootFinder
   :members:

.. autoclass:: sphinx.testing.util.SphinxTestApp
   :members:

.. autoclass:: sphinx.testing.util.SphinxTestAppLazyBuild
   :members:

.. autoclass:: sphinx.testing.util.SphinxTestAppWrapperForSkipBuilding

   .. deprecated:: 7.3

      Use :class:`~sphinx.testing.util.SphinxTestAppLazyBuild` instead.

Utility functions
-----------------

.. autofunction:: sphinx.testing.pytest_util.extract_node_parameters
.. autofunction:: sphinx.testing.pytest_util.get_node_location

.. autofunction:: sphinx.testing.pytest_util.is_pytest_xdist_enabled
.. autofunction:: sphinx.testing.pytest_util.get_pytest_xdist_group
.. autofunction:: sphinx.testing.pytest_util.set_pytest_xdist_group

.. _testing-testroot:

Testroot configuration
----------------------

.. py:currentmodule:: sphinx.testing.pytest_util

Testing usually requires additional resources. In the case of Sphinx, those
resources are in ``tests/roots``, e.g.: ``tests/roots/test-ext-autodoc``.

In this section, we use the following terminology:

* A *testroot directory* is a directory containing files serving initial data.
* A *rootdir* is a directory containing one or more *testroot directories*.

It is common to name a testroot directory with some prefix, say ``test-``,
as Sphinx does in ``tests/roots``. While this prefix has no real meaning
except highlighting the nature of the directory, referring to a testroot
as its full path or directory name (e.g., ``test-ext-autodoc``) becomes
redundant and pedantic when writing tests.

As such, the :class:`TestRootFinder` class eases the discovery of testroots
inside a given *rootdir*. More precisely, such object is constructed from a
*rootdir*, a default *testroot directory ID* and a testroot *prefix*.

For instance, the :class:`TestRootFinder` for Sphinx's tests is:

.. code-block:: python

   # we assume that the Sphinx source code was decompressed into /tmp/sphinx
   finder = TestRootFinder('/tmp/sphinx/tests/roots', 'minimal', 'test-')

By *testroot directory ID* (or simply *testroot ID*), we mean the name
of the testroot directory deprived of the testroot *prefix* (note that
a :class:`TestRootFinder` only finds the testroots with the same prefix).

For instance, ``test-ext-autodoc`` consists of the prefix ``test-``
and the testroot ID ``ext-autodoc``. This makes

.. code-block:: python

   @pytest.mark.sphinx(testroot='ext-autodoc')
   def test_autodoc(app): ...
       app.build()

equivalent to

.. code-block:: python

   def test_autodoc(make_app, sphinx_test_tempdir):
       srcdir = sphinx_test_tempdir / 'ext-autodoc'
       # copy the original sources to a temporary sources directory
       shutil.copytree('/tmp/sphinx/tests/roots/test-ext-autodoc', srcdir)
       app = make_app('html', srcdir=srcdir, ...)
       app.build()

In general, users (and developers) should only specify the *rootdir*, the
default testroot ID, and the testroot prefix in ``conftest.py`` once.

.. _testing-sharing:

Sharing sources and outputs
---------------------------

.. py:currentmodule:: sphinx.testing.fixtures

Using ``shared_result`` in :func:`pytest.mark.test_params` is equivalent to
concatenate the tests using the same ``shared_result`` value.

.. important::

   Using ``shared_result`` may result in undesirable side-effects, especially
   when the test execution order is arbitrary.

For instance, this makes

.. code-block:: python

   @pytest.mark.test_params(shared_result='check-files-a-and-b')
   def test_check_file_a(app):
       app.build()
       check_file_a(app)

   @pytest.mark.test_params(shared_result='check-files-a-and-b')
   def test_check_file_b(app):
       app.build()
       check_file_b(app)

equivalent to

.. code-block:: python

   @pytest.mark.sphinx(srcdir='check-files-a-and-b')
   def test_check_file_a_and_b(app):
       app.build()
       check_file_a(app)
       check_file_b(app)

The :func:`.status` and :func:`.warning` fixtures are also available to all
parametrized tests with the same ``shared_result`` value, making

.. code-block:: python

   @pytest.mark.sphinx(testroot='foo')
   @pytest.mark.test_params(shared_result='shared-foo')
   def test_status_messages(app, status, warning):
       app.build()
       assert app.srcdir.name == 'shared-foo'
       assert 'some message' in status.getvalue()

   @pytest.mark.sphinx(testroot='foo')
   @pytest.mark.test_params(shared_result='shared-foo')
   def test_warning_messages(app, status, warning):
       app.build()
       assert app.srcdir.name == 'shared-foo'
       assert 'some warning' in warning.getvalue()

equivalent to

.. code-block:: python

   @pytest.mark.sphinx(testroot='my-testroot')
   def test_status_messages(app, status, warning):
       app.build()
       assert app.srcdir.name == 'shared-foo'
       assert 'some message' in status.getvalue()
       assert 'some warning' in warning.getvalue()

.. _testing-isolation:

Isolation
---------

Recall that the original testroot is copied to the sources directory. By
default, the sources directory is the same for *each* test using the *same*
testroot, e.g.,:

.. code-block:: python

   @pytest.mark.sphinx(testroot='foo')
   def test_1(app):
       assert app.srcdir.name == 'foo'
       assert not app.srcdir.joinpath('1234').exists()
       app.srcdir.joinpath('1234').touch()

   @pytest.mark.sphinx(testroot='foo')
   def test_2(app):
       assert app.srcdir.name == 'foo'
       assert not app.srcdir.joinpath('1234').exists()

In particular, running sequentially ``test_1`` and ``test_2`` **fails**. To
avoid undesirable side-effects, consider isolating ``test_1`` as follows:

.. code-block:: python

   # Method 1 (recommended)
   @pytest.mark.isolate()
   @pytest.mark.sphinx(testroot='foo')
   def test(app):
       assert app.srcdir.name == 'foo-unique-random-id'

   # Method 2
   @pytest.mark.sphinx(testroot='foo', srcdir='unique-foo-id')
   def test(app):
       assert app.srcdir.name == 'unique-foo-id'

While manually specifying ``srcdir`` is correct, this requires the user
to guarantee its uniquess across *all* test files.

Optimized isolation
^^^^^^^^^^^^^^^^^^^

Using :func:`pytest.mark.isolate` on *parametrized* tests forces the generated
sub-tests to create their own directories, namely, this makes

.. code-block:: python

   @pytest.mark.parametrize('value', [1, 2])
   @pytest.mark.isolate()
   def test(app): ...

eqivalent to:

.. code-block:: python

   @pytest.mark.sphinx(srcdir='some-unique-id-1')
   def test_value_1(app):
       value = 1

   @pytest.mark.sphinx(srcdir='some-unique-id-2')
   def test_value_2(app):
       value = 2

Since parametrization is usually a substitute for a :keyword:`for` loop,
this greatly increases the test execution time.

Instead, using ``@pytest.mark.isolate("once")`` ensures that the generated
sub-tests use a common sources and build directories. Note that this is not
the same as specifying a ``shared_result`` or a ``srcdir`` for the base test
since those might be used by other tests without the user noticing it.

More generally, this makes

.. code-block:: python

   @pytest.mark.isolate('once')
   @pytest.mark.parametrize('param', [1, 2])
   def test(app, param): ...

equivalent to

.. code-block:: python

   @pytest.mark.parametrize('param', [1, 2])
   @pytest.mark.sphinx(srcdir='my-test-group-with-a-unique-id')
   def test(app, param): ...

.. important::

   This mode is incompatible with tests that modify their sources
   or tests for which a set of parameters might affect the output
   directory in a non-compatible way (note that implementing such
   tests is usually not recommended).

.. note::

   When used with `pytest-xdist`_, the generated sub-tests will be
   part of the *same* ``xdist_group``, i.e., the sub-tests will be
   executed by the same worker.

   .. _pytest-xdist: https://github.com/pytest-dev/pytest-xdist
