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

There are currently no configuration values for this extension; you just need to
add ``'sphinx.ext.viewcode'`` to your :confval:`extensions` value for it to work.
