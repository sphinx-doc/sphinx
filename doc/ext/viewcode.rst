:mod:`sphinx.ext.viewcode` -- Add links to highlighted source code
==================================================================

.. module:: sphinx.ext.viewcode
   :synopsis: Add links to a highlighted version of the source code.
.. moduleauthor:: Georg Brandl

.. versionadded:: 1.0


This extension looks at your Python object descriptions (``.. class::``,
``.. function::`` etc.) and tries to find the source files where the objects are
contained.  When found, a separate HTML page will be output for each module with
a highlighted version of the source code, and a link will be added to all object
descriptions that leads to the source code of the described object.  A link back
from the source to the description will also be inserted.

There is an additional config value:

.. confval:: viewcode_import

   If this is ``True``, viewcode extension will follow alias objects that
   imported from another module such as functions, classes and attributes.
   As side effects, this option
   else they produce nothing.  The default is ``True``.

   .. warning::

      :confval:`viewcode_import` **imports** the modules to be followed real
      location.  If any modules have side effects on import, these will be
      executed by ``viewcode`` when ``sphinx-build`` is run.

      If you document scripts (as opposed to library modules), make sure their
      main routine is protected by a ``if __name__ == '__main__'`` condition.

   .. versionadded:: 1.3
