Testing
=======

.. py:module:: sphinx.testing

.. versionadded:: 1.6
   :py:mod:`!sphinx.testing` is added as an experiment.

Utility functions and pytest fixtures for testing are provided in
``sphinx.testing``. If you are a developer of Sphinx extensions, you can write
unit tests by using pytest. At this time, ``sphinx.testing`` will help your
test implementation.

How to use pytest fixtures that are provided by ``sphinx.testing``?  You can
require ``'sphinx.testing.fixtures'`` in your test modules or ``conftest.py``
files like this:

.. code-block:: python

   pytest_plugins = 'sphinx.testing.fixtures'

If you want to know more detailed usage, please refer to ``tests/conftest.py``
and other ``test_*.py`` files under the ``tests`` directory.
