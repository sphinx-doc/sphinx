.. _testing:

=======
Testing
=======

The :mod:`!sphinx.testing` module provides utility classes, functions, fixtures
and markers for testing with `pytest`_. Objects that are not documented on this
page are considered an implementation detail and can be removed without prior
notice.

The testing plugin is enabled by adding the following line in  ``conftest.py``:

.. code-block:: python
   :caption: conftest.py

   pytest_plugins = ['sphinx.testing.fixtures']

This rest of the section is dedicated to documenting those features but the
reader is assumed to have prior knowledge on `pytest`_.

.. _pytest: https://docs.pytest.org/en/latest/

To create a :class:`~sphinx.application.Sphinx` object in a test, use
one of the following constructions

.. code-block:: python

   def test_for_(app):
       app.build()


   @pytest.mark.sphinx(confoverrides={'extensions': ['sphinx.ext.autodoc']})
   def test_for_autodoc(app):
       app.build()


Markers
-------

.. py:decorator:: pytest.mark.sphinx(buildername=None, *, testroot=None, srcdir=None,
                                     freshenv=False, confoverrides=None, tags=None,
                                     docutils_conf=None, parallel=0, isolate=None)

   Marker to configure the testing application.

   :param buildername: The builder name.
   :type buildername: str
   :param testroot: The testroot name deprived of its prefix.
   :type testroot: str
   :param srcdir: A custom sources directory name where to copy testroot files.
   :type srcdir: str
   :param freshenv: Create a fresh environment (simulate :option:`-E`).
   :type freshenv: bool
   :param confoverrides: User-defined configuration values.
   :type confoverrides: dict[str, Any]
   :param tags: The list of configuration tags (see :ref:`conf-tags`).
   :type tags: list[str]
   :param docutils_conf: The docutils configuration.
   :type docutils_conf: str
   :param parallel: The number of parallel workers.
   :type parallel: int
   :param isolate: The isolation policy (see :ref:`testing-isolation`).
   :type isolate: bool | Literal["none", "once", "always"]

   .. seealso::

      :func:`sphinx.testing.fixtures.sphinx_builder`

         Session fixture containing the default builder name.

      :func:`sphinx.testing.fixtures.sphinx_testroot_finder`

         Session fixture specifying the testroot configuration.

      :func:`sphinx.testing.fixtures.sphinx_isolation`

         Session fixture specifying the default isolation policy.


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

.. py:function:: sphinx.testing.fixtures.app

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


.. py:function:: sphinx.testing.fixtures.app_params

   Fixture for accessing the application positional and keyword arguments
   specified by :func:`pytest.mark.sphinx` and other markers.

   Usage:

   .. code-block:: python

      @pytest.mark.sphinx(testroot='foo')
      def test(app_params):
          args, kwargs = app_params
          assert kwargs['testroot'] == 'foo'


.. py:function:: sphinx.testing.fixtures.make_params

   Factory function for a :class:`~sphinx.testing.util.SphinxTestApp` object.

   :rtype: collections.abc.Callable[..., sphinx.testing.util.SphinxTestApp]

   Usage:

   .. code-block:: python

      def test_foo(make_params):
          args, kwargs = ...
          app = make_params(*args, **kwargs)

      @pytest.mark.sphinx(testroot='foo')
      def test_foo(app_params, make_params):
          args, kwargs = app_params
          app = make_params(*args, **kwargs)

.. py:function:: sphinx.testing.fixtures.status

   Fixture for accessing the underlying :class:`~io.StringIO` object
   containing the application status messages.

   :rtype: io.StringIO

.. py:function:: sphinx.testing.fixtures.warning

   Fixture for accessing the underlying :class:`~io.StringIO` object
   containing the application warning messages.

   :rtype: io.StringIO

.. py:function:: sphinx.testing.fixtures.sphinx_test_tempdir

   The base temporary directory containing the sources directories
   where testroot files are copied to.

.. py:function:: sphinx.testing.fixtures.sphinx_builder

   The default builder name (defaults: "html").

   :rtype: str

.. py:function:: sphinx.testing.fixtures.rootdir

   The root directory for a testroot (defaults: ``None``).

   :rtype: str | os.PathLike[str] | None

   .. rubric:: Usage

   .. code-block:: python
      :caption: tests/conftest.py

      @pytest.fixture(scope='session')
      def rootdir() -> str:
          return 'testroot-dir'

      @pytest.fixture(scope='session')
      def sphinx_testroot(rootdir: str) -> TestRootConfig:
          return TestRootConfig(rootdir, 'default', 'my-')

   .. code-block:: python
      :caption: tests/test.py

      @pytest.mark.sphinx()
      def test_no_testroot(app_params):
          assert app_params.kwargs['testroot'] == 'testroot-dir/my-default'

      @pytest.mark.sphinx(testroot='bar')
      def test_bar(app_params):
          assert app_params.kwargs['testroot'] == 'testroot-dir/my-bar'

   .. seealso::

      :func:`sphinx.testing.fixtures.sphinx_testroot`

.. py:function:: sphinx.testing.fixtures.sphinx_testroot_finder

   Fixture specifying how testroot files are to be found.

   :rtype: sphinx.testing.pytest_util.TestRootFinder

   See :func:`sphinx.testing.fixtures.rootdir` for an example usage.

.. py:function:: sphinx.testing.fixtures.sphinx_isolation

   The default isolation policy.

   :rtype: bool | Literal["none", "once", "always"] | None

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

      Use :class:`sphinx.testing.util.SphinxTestAppLazyBuild` instead.

Utility functions
-----------------

.. autofunction:: sphinx.test.pytest_util.extract_node_parameters
.. autofunction:: sphinx.test.pytest_util.get_node_location

.. _testing-sharing:

Sharing
-------
Using ``shared_result`` in :func:`pytest.mark.test_params` is equivalent to
concatenate the tests using the same ``shared_result`` value. For instance,
this makes

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


In addition, the :func:`status` and :func:`warning` fixtures are available
to parametrized test with the same ``shared_result`` value, making:

.. code-block:: python

   @pytest.mark.sphinx(testroot='foo')
   @pytest.mark.test_params(shared_result='shared-foo')
   def test_status_messages(app, status, warning):
       app.build()
       assert str(app.srcdir).endswith('shared-foo')
       assert 'some message' in status.getvalue()

   @pytest.mark.sphinx(testroot='foo')
   @pytest.mark.test_params(shared_result='shared-foo')
   def test_warning_messages(app, status, warning):
       app.build()
       assert str(app.srcdir).endswith('shared-foo')
       assert 'some warning' in warning.getvalue()

equivalent to:

.. code-block:: python

   @pytest.mark.sphinx(testroot='my-testroot')
   def test_status_messages(app, status, warning):
       app.build()
       assert str(app.srcdir).endswith('shared-foo')
       assert 'some message' in status.getvalue()
       assert 'some warning' in warning.getvalue()

.. _testing-isolation:

Isolation
---------

Recall that the original testroot is copied to the sources directory. By
default, the sources directory is the same for *each* test using the *same*
testroot, e.g.,:

.. code-block:: python

   @pytest.mark.sphinx(testroot='minimal')
   def test_1(app, sphinx_test_tempdir):
       assert app.srcdir == sphinx_test_tempdir / 'minimal'
       assert not app.srcdir.joinpath('1234').exists()
       app.srcdir.joinpath('1234').touch()

   @pytest.mark.sphinx(testroot='minimal')
   def test_2(app, sphinx_test_tempdir):
       assert app.srcdir == sphinx_test_tempdir / 'minimal'
       assert not app.srcdir.joinpath('1234').exists()

In particular, running sequentially ``test_1`` and ``test_2`` fails. To avoid
undesirable side-effects, consider isolating ``test_1`` as follows:

.. code-block:: python

   # Method 1 (recommended)
   @pytest.mark.isolate()
   @pytest.mark.sphinx(testroot='foo')
   def test(app, sphinx_test_tempdir):
       assert app.srcdir == sphinx_test_tempdir / 'foo' / 'unique-random-id'

   # Method 2
   @pytest.mark.sphinx(testroot='foo', srcdir='unique-foo-id')
   def test(app, sphinx_test_tempdir):
       assert app.srcdir == sphinx_test_tempdir / 'unique-foo-id'

While manually specifying ``srcdir`` is correct, this requires the user
to guarantee its uniquess across the test files. If the output should be
shared, consider using :func:`pytest.mark.test_params`.

Optimized isolation
-------------------

Using ``@pytest.mark.isolate()`` on *parametrized* tests forces the generated
sub-tests to create their own directories. Since parametrization is usually a
substitute for a :keyword:`for` loop, this greatly increases the running time.

Instead, using ``@pytest.mark.isolate('once')`` ensures that the generated
sub-tests use a common sources and build directories. Note that this is not
the same as just specifying a ``shared_result`` or a ``srcdir`` for the base
test since those might be used by other tests without the user noticing it.

More generally, this makes

.. code-block:: python

   @pytest.mark.isolate('once')
   @pytest.mark.parametrize('param', [1, 2])
   def test(app, param): ...

roughly equivalent to:

.. code-block:: python

   @pytest.mark.parametrize('param', [1, 2])
   @pytest.mark.test_params(shared_result='my-test-group-with-a-unique-id')
   def test(app, param): ...


.. note::

   This mode is incompatible with tests that modify their sources
   or tests for which a set of parameters might affect the output
   directory in a non-compatible way (note that implementing such
   tests is usually not recommended).

.. note::

   When used with `pytest-xdist`_, the generated sub-tests will be
   executed by the same worker.

   .. _pytest-xdist: https://github.com/pytest-dev/pytest-xdist
