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


Configuration
-------------

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

   The ``start_line`` and ``end_line`` keys are also always present in the
   ``info`` dictionnary, but may be None if they are not found. By default,
   theses values are found using the :event:`viewcode-find-source` event but you
   can set the :confval:`linkcode_line_try_import` setting to ``True`` to use
   the same import mechanism as in :mod:`sphinx.ext.viewcode`.

   Example:

   .. code-block:: python

      def linkcode_resolve(domain, info):
          if domain != 'py':
              return None
          if not info['module']:
              return None
          filename = info['module'].replace('.', '/')
          line_anchor = ""
          if info['start_line'] is not None:
            line_anchor = "#L%s" % info['start_line']
          return "https://somesite/sourcerepo/%s.py%s" % filename, line_anchor

.. confval:: linkcode_line_try_import

   .. versionadded:: 4.1.3

   If this is ``True``, the extension will try to find the related source lines
   using the same import mechanism used by :mod:`sphinx.ext.viewcode`
   (:class:`~sphinx.pycode.ModuleAnalyzer`) after the
   :event:`viewcode-find-source` event has been tried. Otherwise only the event
   is used.

   .. warning::

      The same warning as in :mod:`sphinx.ext.viewcode` applies: using this
      method will import the modules being linked to.
      If any modules have side effects on import, these will be executed when
      ``sphinx-build`` is run.

      If you document scripts (as opposed to library modules), make sure their
      main routine is protected by a ``if __name__ == '__main__'`` condition.

   The default is ``False``.

.. event:: viewcode-find-source (app, modname)

   .. versionadded:: 4.1.3

   Find the source code for a module.
   An event handler for this event should return a tuple of the source code
   itself and a dictionary of tags.
   The dictionary maps the name of a class, function, attribute, etc to a tuple
   of its type, the start line number, and the end line number.
   The type should be one of "class", "def", or "other".

   :param app: The Sphinx application object.
   :param modname: The name of the module to find source code for.
