Testing API
===========

.. versionadded:: 1.6

Sphinx provides utility functions and pytest fixtures to make it easier
to write test suites that build multiple Sphinx documentation projects.

Using ``pytest`` plugin
-----------------------

To use pytest helpers that are provided by ``sphinx.testing``, add the
``'sphinx.testing.fixtures'`` plugin to your :file:`conftest.py` file
as follows:

.. code-block:: python

   pytest_plugins = ['sphinx.testing.fixtures']

Markers
~~~~~~~

.. py:decorator:: pytest.mark.test_params(...)

    Parameters associated with a test.

    :param str shared_result: A key that allows sharing the build result, status, and warning between tests that use the same key.

    When multiple tests with a module are marked with the same
    ``shared_result`` value, they will share the same build result as
    well as status and warning buffers. This allows related tests to
    avoid redundant rebuilds and reuse the same build context.

    .. code-block:: python

        @pytest.mark.test_params(shared_result="html_build")
        def test_html_title(app: SphinxTestApp) -> None:
            app.build()
            # ... test something about the HTML output ...

        @pytest.mark.test_params(shared_result="html_build")
        def test_html_index(app: SphinxTestApp) -> None:
            app.build()
            # ... test something else about the HTML output ...

.. py:decorator:: pytest.mark.sphinx(buildername="html", *, testroot="root", ...)

    Arguments to initialize the Sphinx test application.

    :param str buildername: Builder to use.
    :param str testroot: Test root directory to use.
    :param srcdir: Source directory (overridden when ``shared_result`` is used).
    :param dict confoverrides: Configuration values to override.
    :param bool freshenv: Whether to refresh the environment.
    :param bool warningiserror: Treat warnings as errors.
    :param tags: List of tags to set.
    :param int verbosity: Verbosity level.
    :param int parallel: Number of parallel processes.
    :param builddir: Build directory.
    :param docutils_conf: Docutils configuration.

    .. code-block:: python

        @pytest.mark.sphinx("html", testroot="something")
        def test_html_output(app: SphinxTestApp) -> None:
            app.build()
            # ... test something about the HTML output ...

Fixtures
~~~~~~~~

.. py:function:: sphinx.testing.fixtures.rootdir

    :scope: session

    Defaults to ``None`` so tests operate on (empty) temporary paths.

    Can be overridden in a project's :file:`conftest.py` to return a
    :class:`~pathlib.Path` to a directory, containing multiple Sphinx
    documentation sources under sub-directories prefixed with `test-`.

    .. code-block:: python

        @pytest.fixture(scope='session')
        def rootdir() -> pathlib.Path | None:
            return pathlib.Path(__file__).parent / 'docsets'

    .. code-block:: text

        tests/
        ├── conftest.py  <-- defines rootdir fixture
        ├── docsets/
        ├── test-example1/
        │   ├── conf.py
        │   └── index.rst
        ├── test-example2/
        │   ├── conf.py
        │   └── index.rst
        └── test_something.py

.. py:function:: sphinx.testing.fixtures.sphinx_test_tempdir

    :scope: session

    Base temporary directory :class:`~pathlib.Path` used for building
    the test apps.

.. py:function:: sphinx.testing.fixtures.app_params

    The positional ``args`` and keyword ``kwargs`` used to build the
    :py:class:`~sphinx.testing.util.SphinxTestApp` for this test. These are derived from the
    :py:func:`pytest.mark.sphinx`, :py:func:`pytest.mark.test_params`,
    and default settings.

    If ``rootdir`` fixture is not :py:obj:`None`, the contents of
    ``rootdir / f'test-{testroot}'`` get copied into the source directory
    that the app would build in.

    Returns a namedtuple of ``(args, kwargs)``.

.. py:function:: sphinx.testing.fixtures.make_app

    Factory function that constructs a :class:`~sphinx.testing.util.SphinxTestApp`
    from ``app_params``.

    .. code-block:: python

        def test_something(make_app: Callable[..., SphinxTestApp]) -> None:
            app = make_app("html")
            app.build()
            # ... test something about the built documentation ...

.. py:function:: sphinx.testing.fixtures.app

    A :class:`~sphinx.testing.util.SphinxTestApp` constructed from
    ``app_params``.

    .. code-block:: python

        def test_something(app: SphinxTestApp) -> None:
            app.build()
            # ... test something about the built documentation ...

.. py:function:: sphinx.testing.fixtures.if_graphviz_found

    Skip the test if :confval:`graphviz_dot` is not configured or the binary is
    unavailable.

    .. code-block:: python

        @pytest.mark.usefixtures('if_graphviz_found')
        def test_graphviz_diagram(app: SphinxTestApp) -> None:
            app.build()
            # ... test something about the graphviz diagram ...

.. py:function:: sphinx.testing.fixtures.rollback_sysmodules

    Iterator that snapshots ``sys.modules`` before the test and removes any
    modules imported during the test body. Helps tests reload target modules to
    clear caches.

    This mostly exists to help test :mod:`sphinx.ext.autodoc`.

    .. code-block:: python

        @pytest.mark.usefixtures('rollback_sysmodules')
        def test_module_reload(app: SphinxTestApp) -> None:
            import my_extension
            # ... test something about my_extension ...

.. py:function:: sphinx.testing.fixtures.status

    Compatibility fixture returning ``app.status`` (``StringIO``).

.. py:function:: sphinx.testing.fixtures.warning

    Compatibility fixture returning ``app.warning`` (``StringIO``).

Utilities
---------

.. autoclass:: sphinx.testing.util.SphinxTestApp
    :members:
    :show-inheritance:

    .. py:attribute:: extras

        A dictionary to store arbitrary data associated with this app.

.. autoclass:: sphinx.testing.util.SphinxTestAppWrapperForSkipBuilding
    :members:
    :show-inheritance:

Usage
-----

If you want to know more detailed usage,
please refer to :file:`tests/conftest.py` and other :file:`test_*.py` files
under the :file:`tests/` directory of the Sphinx source code.
