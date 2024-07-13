Depend on another extension
===========================

Sometimes your extension depends on the functionality of another
Sphinx extension. Most Sphinx extensions are activated in a
project's :file:`conf.py` file, but this is not available to you as an
extension developer.

.. module:: sphinx.application
   :no-index:

To ensure that another extension is activated as a part of your own extension,
use the :meth:`sphinx.application.Sphinx.setup_extension` method. This will
activate another extension at run-time, ensuring that you have access to its
functionality.

For example, the following code activates the :mod:`sphinx.ext.autodoc` extension:

.. code-block:: python

    def setup(app):
        app.setup_extension('sphinx.ext.autodoc')

.. note::

   Since your extension will depend on another, make sure to include
   it as a part of your extension's installation requirements.
