Configuring builders
====================

Discover builders by entry point
--------------------------------

.. versionadded:: 1.6

:term:`builder` extensions can be discovered by means of `entry points`_ so
that they do not have to be listed in the :confval:`extensions` configuration
value.

Builder extensions should define an entry point in the ``sphinx.builders``
group. The name of the entry point needs to match your builder's
:attr:`~.Builder.name` attribute, which is the name passed to the
:option:`sphinx-build -b` option. The entry point value should equal the
dotted name of the extension module. Here is an example of how an entry point
for 'mybuilder' can be defined in the extension's ``setup.py``

.. code-block:: python

   setup(
       # ...
       entry_points={
           'sphinx.builders': [
               'mybuilder = my.extension.module',
           ],
       }
   )

Note that it is still necessary to register the builder using
:meth:`~.Sphinx.add_builder` in the extension's :func:`setup` function.

.. _entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
