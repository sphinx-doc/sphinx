:mod:`sphinx.ext.linkcode` -- Add external links to source code
===============================================================

.. module:: sphinx.ext.linkcode
   :synopsis: Add external links to source code.
.. moduleauthor:: Pauli Virtanen

.. versionadded:: 1.2

.. role:: code-py(code)
   :language: Python

This extension looks at your object descriptions (``.. class::``,
``.. function::`` etc.) and adds external links to code hosted
somewhere on the web. The intent is similar to the
``sphinx.ext.viewcode`` extension, but assumes the source code can be
found somewhere on the Internet.

In your configuration, you need to specify a :confval:`linkcode_resolve`
function that returns an URL based on the object.


Configuration
-------------

.. confval:: linkcode_resolve
   :type: :code-py:`Callable[[str, dict[str, str]], str | None] | None`
   :default: :code-py:`None`

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
          return "https://somesite/sourcerepo/%s.py" % filename


Third-party domains
-------------------

Support for other domains can be added by extensions with
:py:func:`.add_linkcode_domain()`.
For example, a Sphinx extension that provides a ``php`` domain
could use the following code to support :mod:`~sphinx.ext.linkcode`:

.. code-block:: python

   from sphinx.ext.linkcode import add_linkcode_domain

   def setup(app):
       add_linkcode_domain('php', ['namespace', 'class', 'fullname'])

.. autofunction:: add_linkcode_domain
