:mod:`sphinx.ext.oldcmarkup` -- Compatibility extension for old C markup
========================================================================

.. module:: sphinx.ext.oldcmarkup
   :synopsis: Allow further use of the pre-domain C markup
.. moduleauthor:: Georg Brandl

.. versionadded:: 1.0


This extension is a transition helper for projects that used the old
(pre-domain) C markup, i.e. the directives like ``cfunction`` and roles like
``cfunc``.  Since the introduction of domains, they must be called by their
fully-qualified name (``c:function`` and ``c:func``, respectively) or, with the
default domain set to ``c``, by their new name (``function`` and ``func``).
(See :ref:`c-domain` for the details.)

If you activate this extension, it will register the old names, and you can
use them like before Sphinx 1.0.  The directives are:

- ``cfunction``
- ``cmember``
- ``cmacro``
- ``ctype``
- ``cvar``

The roles are:

- ``cdata``
- ``cfunc``
- ``cmacro``
- ``ctype``

However, it is advised to migrate to the new markup -- this extension is a
compatibility convenience and will disappear in a future version of Sphinx.
