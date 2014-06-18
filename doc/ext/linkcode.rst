:mod:`sphinx.ext.linkcode` -- Add external links to source code
===============================================================

.. module:: sphinx.ext.linkcode
   :synopsis: Add external links to source code.
.. moduleauthor:: Pauli Virtanen

.. versionadded:: 1.2

This extension looks at your object descriptions (``.. class::``,
``.. function::`` etc.) and adds external links to code hosted
somewhere on the web. The intent is similar to the
``sphinx.ext.viewcode`` extension, but assumes the source code can be
found somewhere on the Internet.

In your configuration, you need to specify a :confval:`linkcode_resolve`
function that returns an URL based on the object.

.. confval:: linkcode_resolve

   This is a function ``linkcode_resolve(domain, info)``,
   which should return the URL to source code corresponding to
   the object in given domain with given information.

   The function should return ``None`` if no link is to be added.

   The argument ``domain`` specifies the language domain the object is
   in. ``info`` is a dictionary with the following keys guaranteed to
   be present (dependent on the domain):

   - ``py``: ``module`` (name of the module), ``fullname`` (name of the object)
   - ``c``: ``names`` (list of names for the object)
   - ``cpp``: ``names`` (list of names for the object)
   - ``javascript``: ``object`` (name of the object), ``fullname``
     (name of the item)

   Example:

   .. code-block:: python

      def linkcode_resolve(domain, info):
          if domain != 'py':
              return None
          if not info['module']:
              return None
          filename = info['module'].replace('.', '/')
          return "http://somesite/sourcerepo/%s.py" % filename
