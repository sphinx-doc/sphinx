.. _extensions:

Sphinx Extensions
=================

.. module:: sphinx.application
   :synopsis: Application class and extensibility interface.

Since many projects will need special features in their documentation, Sphinx is
designed to be extensible on several levels.

First, you can add new :term:`builder`\s to support new output formats or
actions on the parsed documents.  Then, it is possible to register custom
reStructuredText roles and directives, extending the markup.  And finally, there
are so-called "hook points" at strategic places throughout the build process,
where an extension can register a hook and run specialized code.

Each Sphinx extension is a Python module with at least a :func:`setup` function.
This function is called at initialization time with one argument, the
application object representing the Sphinx process.  This application object has
the following public API:

.. method:: Application.add_builder(builder)

   Register a new builder.  *builder* must be a class that inherits from
   :class:`~sphinx.builder.Builder`.

.. method:: Application.add_config_value(name, default, rebuild_env)

   Register a configuration value.  This is necessary for Sphinx to recognize
   new values and set default values accordingly.  The *name* should be prefixed
   with the extension name, to avoid clashes.  The *default* value can be any
   Python object.  The boolean value *rebuild_env* must be ``True`` if a change
   in the setting only takes effect when a document is parsed -- this means that
   the whole environment must be rebuilt.

.. method:: Application.add_event(name)

   Register an event called *name*.

.. method:: Application.add_node(node)

   Register a Docutils node class.  This is necessary for Docutils internals.
   It may also be used in the future to validate nodes in the parsed documents.

.. method:: Application.add_directive(name, cls, content, arguments, **options)

   Register a Docutils directive.  *name* must be the prospective directive
   name, *func* the directive function (see the Docutils documentation - XXX
   ref) for details about the signature and return value.  *content*,
   *arguments* and *options* are set as attributes on the function and determine
   whether the directive has content, arguments and options, respectively.  For
   their exact meaning, please consult the Docutils documentation.
   
.. method:: Application.add_role(name, role)

   Register a Docutils role.  *name* must be the role name that occurs in the
   source, *role* the role function (see the Docutils documentation on details).

.. method:: Application.add_description_unit(directivename, rolename, indexdesc='', parse_node=None)

   XXX

.. method:: Application.connect(event, callback)

   Register *callback* to be called when *event* is emitted.  For details on
   available core events and the arguments of callback functions, please see
   :ref:`events`.

   The method returns a "listener ID" that can be used as an argument to
   :meth:`disconnect`.

.. method:: Application.disconnect(listener_id)

   Unregister callback *listener_id*.

.. method:: Application.emit(event, *arguments)

   Emit *event* and pass *arguments* to the callback functions.  Do not emit
   core Sphinx events in extensions!


.. exception:: ExtensionError

   All these functions raise this exception if something went wrong with the
   extension API.

Examples of using the Sphinx extension API can be seen in the :mod:`sphinx.ext`
package.


.. _events:

Sphinx core events
------------------

These events are known to the core:

====================== =================================== =========
Event name             Emitted when                        Arguments
====================== =================================== =========
``'builder-inited'``   the builder object has been created -none-
``'doctree-read'``     a doctree has been parsed and read  *doctree*
                       by the environment, and is about to
                       be pickled
``'doctree-resolved'`` a doctree has been "resolved" by    *doctree*, *docname*
                       the environment, that is, all
                       references and TOCs have been
                       inserted
====================== =================================== =========
