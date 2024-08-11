Testing API
===========

.. py:module:: sphinx.testing
   :synopsis: Utility functions and pytest fixtures for testing.

.. versionadded:: 1.6

Utility functions and pytest fixtures for testing
are provided in :py:mod:`!sphinx.testing`.
If you are a developer of Sphinx extensions,
you can write unit tests with pytest_.

.. _pytest: https://docs.pytest.org/en/latest/

``pytest`` configuration
-------------------------

To use pytest fixtures that are provided by ``sphinx.testing``,
add the ``'sphinx.testing.fixtures'`` plugin
to your test modules or :file:`conftest.py` files as follows:

.. code-block:: python

   pytest_plugins = ('sphinx.testing.fixtures',)

Usage
-----

If you want to know more detailed usage,
please refer to :file:`tests/conftest.py` and other :file:`test_*.py` files
under the :file:`tests/` directory.
