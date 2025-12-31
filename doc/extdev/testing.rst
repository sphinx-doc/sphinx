Testing API
===========

.. versionadded:: 1.6

Sphinx provides utility functions and pytest fixtures to make it easier
to write test suites that build multiple Sphinx documentation projects.

Using the ``pytest`` plugin
---------------------------

To use pytest helpers that are provided by ``sphinx.testing``, add the
``'sphinx.testing.fixtures'`` plugin to your :file:`conftest.py` file
as follows:

.. code-block:: python

   pytest_plugins = ['sphinx.testing.fixtures']

Markers
~~~~~~~

.. py:decorator:: pytest.mark.sphinx(buildername='html', *, testroot='root', ...)

   Arguments to initialize the Sphinx test application.

   :param str buildername: Builder to use.
   :kwparam str testroot: Test root directory to use.
   :kwparam srcdir: Source directory to use.
   :kwparam dict confoverrides: Configuration values to override.
   :kwparam bool freshenv: Whether to refresh the environment.
   :kwparam bool warningiserror: Treat warnings as errors.
   :kwparam tags: List of tags to set.
   :kwparam int verbosity: Verbosity level.
   :kwparam int parallel: Number of parallel processes.
   :kwparam builddir: Build directory.
   :kwparam docutils_conf: Docutils configuration.

   .. code-block:: python

      @pytest.mark.sphinx('html', testroot='something')
      def test_html_output(app: SphinxTestApp) -> None:
          app.build()
          # ... test something about the HTML output ...

.. py:decorator:: pytest.mark.test_params(*, shared_result=...)

   Parameters associated with a test.

   :kwparam str shared_result:
       A key that allows sharing the build result, status, and warnings
       between tests that use the same key.

   When multiple tests with a module are marked with the same
   ``shared_result`` value, they will share the same build result as
   well as status and warning buffers. This allows related tests to
   avoid redundant rebuilds and reuse the same build context.

   .. attention:: *shared_result* and *srcdir* are mutually incompatible.

   .. code-block:: python

      @pytest.mark.test_params(shared_result='html_build')
      def test_html_title(app: SphinxTestApp) -> None:
          app.build()
          # ... test something about the HTML output ...

      @pytest.mark.test_params(shared_result='html_build')
      def test_html_index(app: SphinxTestApp) -> None:
          app.build()
          # ... test something else about the HTML output ...

Fixtures
~~~~~~~~

.. py:data:: sphinx.testing.fixtures.app
   :type: SphinxTestApp

   :scope: function

   Provides a :class:`~sphinx.testing.util.SphinxTestApp` instance.
   This is the most common way to get a Sphinx application for testing.

   The app can be configured by using the :deco:`pytest.mark.sphinx` marker.

   .. code-block:: python

      def test_something(app: SphinxTestApp) -> None:
          app.build()
          # ... test something about the built documentation ...

.. py:function:: sphinx.testing.fixtures.make_app(*args: Any, **kwargs: Any) -> SphinxTestApp

   :scope: function

   Factory function that constructs a :class:`~sphinx.testing.util.SphinxTestApp`
   instance for use in tests. This is the preferred way to create instances
   of the :class:`~sphinx.application.Sphinx` object, as it handles clean-up.
   The arguments are the same as those to ``SphinxTestApp``.

   .. code-block:: python

      def test_something(make_app: Callable[..., SphinxTestApp]) -> None:
          app = make_app('html')
          app.build()
          # ... test something about the built documentation ...

.. py:data:: sphinx.testing.fixtures.app_params
   :type: tuple[Sequence[Any], Mapping[str, Any]]

   :scope: function

   The positional keyword arguments used to create the
   :class:`~sphinx.testing.util.SphinxTestApp` for this test.
   These are derived from the markers_ applied to the test function.

   Returns a namedtuple of ``(args, kwargs)``.

.. py:data:: sphinx.testing.fixtures.rootdir
   :type: pathlib.Path | None

   :scope: session

   Default is ``None``, meaning tests use empty temporary directories.

   Can be overridden in a project's :file:`conftest.py` to return a
   :class:`~pathlib.Path` to a directory, containing multiple Sphinx
   documentation sources under sub-directories prefixed with ``test-``.

   .. code-block:: python

      @pytest.fixture(scope='session')
      def rootdir() -> Path:
          return Path(__file__).resolve().parent / 'roots'

   .. code-block:: text

      tests/
      ├── conftest.py  <-- defines rootdir fixture
      ├── roots/
      │   ├── test-example1/
      │   │   ├── conf.py
      │   │   └── index.rst
      │   └── test-example2/
      │       ├── conf.py
      │       └── index.rst
      └── test_something.py

.. py:data:: sphinx.testing.fixtures.sphinx_test_tempdir
   :type: pathlib.Path

   :scope: session

   Base temporary directory :class:`~pathlib.Path` used for building
   the test apps.

Utilities
---------

.. autoclass:: sphinx.testing.util.SphinxTestApp
   :members:
   :show-inheritance:

.. autoclass:: sphinx.testing.util.SphinxTestAppWrapperForSkipBuilding
   :members:
   :show-inheritance:

Examples
--------

For practical examples, refer to :file:`tests/conftest.py`
and other :file:`test_*.py` files under the :file:`tests/` directory
of the Sphinx source code.
