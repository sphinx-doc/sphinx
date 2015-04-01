.. highlight:: rest

:mod:`sphinx.ext.asyncio` -- Support for asyncio
================================================

.. module:: sphinx.ext.asyncio
   :synopsis: Add directives for asyncio.
.. moduleauthor:: Xavier Barbosa

.. versionadded:: 1.4

Adds directives for :py:class:`asyncio`:

.. rst:directive:: .. py:coroutine:: name(parameters)

   Like :rst:dir:`py:function`, but for :py:class:`asyncio.coroutine`.

.. rst:directive:: .. py:coroutinemethod:: name(parameters)

   Like :rst:dir:`py:method`, but for :py:class:`asyncio.coroutine`.


.. note::

   asyncio or trollius must be installed in order to use
   :mod:`sphinx.ext.autodoc`.
