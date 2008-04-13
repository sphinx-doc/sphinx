.. highlight:: rest

Extension API
=============

Each Sphinx extension is a Python module with at least a :func:`setup` function.
This function is called at initialization time with one argument, the
application object representing the Sphinx process.  This application object has
the following public API:

.. method:: Sphinx.add_builder(builder)

   Register a new builder.  *builder* must be a class that inherits from
   :class:`~sphinx.builder.Builder`.

.. method:: Sphinx.add_config_value(name, default, rebuild_env)

   Register a configuration value.  This is necessary for Sphinx to recognize
   new values and set default values accordingly.  The *name* should be prefixed
   with the extension name, to avoid clashes.  The *default* value can be any
   Python object.  The boolean value *rebuild_env* must be ``True`` if a change
   in the setting only takes effect when a document is parsed -- this means that
   the whole environment must be rebuilt.

.. method:: Sphinx.add_event(name)

   Register an event called *name*.

.. method:: Sphinx.add_node(node)

   Register a Docutils node class.  This is necessary for Docutils internals.
   It may also be used in the future to validate nodes in the parsed documents.

.. method:: Sphinx.add_directive(name, cls, content, arguments, **options)

   Register a Docutils directive.  *name* must be the prospective directive
   name, *func* the directive function for details about the signature and
   return value.  *content*, *arguments* and *options* are set as attributes on
   the function and determine whether the directive has content, arguments and
   options, respectively.  For their exact meaning, please consult the Docutils
   documentation.

   .. XXX once we target docutils 0.5, update this
   
.. method:: Sphinx.add_role(name, role)

   Register a Docutils role.  *name* must be the role name that occurs in the
   source, *role* the role function (see the `Docutils documentation
   <http://docutils.sourceforge.net/docs/howto/rst-roles.html>`_ on details).

.. method:: Sphinx.add_description_unit(directivename, rolename, indextemplate='', parse_node=None, ref_nodeclass=None)

   This method is a very convenient way to add a new type of information that
   can be cross-referenced.  It will do this:

   * Create a new directive (called *directivename*) for a :term:`description
     unit`.  It will automatically add index entries if *indextemplate* is
     nonempty; if given, it must contain exactly one instance of ``%s``.  See
     the example below for how the template will be interpreted.
   * Create a new role (called *rolename*) to cross-reference to these
     description units.
   * If you provide *parse_node*, it must be a function that takes a string and
     a docutils node, and it must populate the node with children parsed from
     the string.  It must then return the name of the item to be used in
     cross-referencing and index entries.  See the :file:`ext.py` file in the
     source for this documentation for an example.

   For example, if you have this call in a custom Sphinx extension::

      app.add_description_unit('directive', 'dir', 'pair: %s; directive')

   you can use this markup in your documents::

      .. directive:: function

         Document a function.

      <...>

      See also the :dir:`function` directive.

   For the directive, an index entry will be generated as if you had prepended ::

      .. index:: pair: function; directive

   The reference node will be of class ``literal`` (so it will be rendered in a
   proportional font, as appropriate for code) unless you give the *ref_nodeclass*
   argument, which must be a docutils node class (most useful are
   ``docutils.nodes.emphasis`` or ``docutils.nodes.strong`` -- you can also use
   ``docutils.nodes.generated`` if you want no further text decoration).

   For the role content, you have the same options as for standard Sphinx roles
   (see :ref:`xref-syntax`).

.. method:: Sphinx.add_crossref_type(directivename, rolename, indextemplate='', ref_nodeclass=None)

   This method is very similar to :meth:`add_description_unit` except that the
   directive it generates must be empty, and will produce no output.

   That means that you can add semantic targets to your sources, and refer to
   them using custom roles instead of generic ones (like :role:`ref`).  Example
   call::

      app.add_crossref_type('topic', 'topic', 'single: %s', docutils.nodes.emphasis)

   Example usage::

      .. topic:: application API

      The application API
      -------------------

      <...>

      See also :topic:`this section <application API>`.

   (Of course, the element following the ``topic`` directive needn't be a
   section.)

.. method:: Sphinx.add_transform(transform)

   Add the standard docutils :class:`Transform` subclass *transform* to the list
   of transforms that are applied after Sphinx parses a reST document.

.. method:: Sphinx.connect(event, callback)

   Register *callback* to be called when *event* is emitted.  For details on
   available core events and the arguments of callback functions, please see
   :ref:`events`.

   The method returns a "listener ID" that can be used as an argument to
   :meth:`disconnect`.

.. method:: Sphinx.disconnect(listener_id)

   Unregister callback *listener_id*.

.. method:: Sphinx.emit(event, *arguments)

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
