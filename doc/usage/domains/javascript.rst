.. highlight:: rst

=====================
The JavaScript Domain
=====================

.. versionadded:: 1.0

The JavaScript domain (name **js**) provides the following directives:

.. rst:directive:: .. js:module:: name

   This directive sets the module name for object declarations that follow
   after. The module name is used in the global module index and in cross
   references. This directive does not create an object heading like
   :rst:dir:`py:class` would, for example.

   By default, this directive will create a linkable entity and will cause an
   entry in the global module index, unless the ``no-index`` option is
   specified.  If this option is specified, the directive will only update the
   current module name.

   .. versionadded:: 1.6
   .. versionchanged:: 5.2

      Module directives support body content.

.. rst:directive:: .. js:function:: name(signature)

   Describes a JavaScript function or method.  If you want to describe
   arguments as optional use square brackets as :ref:`documented <signatures>`
   for Python signatures.

   You can use fields to give more details about arguments and their expected
   types, errors which may be thrown by the function, and the value being
   returned::

      .. js:function:: $.getJSON(href, callback[, errback])

         :param string href: An URI to the location of the resource.
         :param callback: Gets called with the object.
         :param errback:
             Gets called in case the request fails. And a lot of other
             text so we need multiple lines.
         :throws SomeError: For whatever reason in that case.
         :returns: Something.

   This is rendered as:

   .. js:function:: $.getJSON(href, callback[, errback])
      :no-contents-entry:
      :no-index-entry:

      :param string href: An URI to the location of the resource.
      :param callback: Gets called with the object.
      :param errback:
          Gets called in case the request fails. And a lot of other
          text so we need multiple lines.
      :throws SomeError: For whatever reason in that case.
      :returns: Something.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:method:: name(signature)

   This directive is an alias for :rst:dir:`js:function`, however it describes
   a function that is implemented as a method on a class object.

   .. versionadded:: 1.6

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:class:: name

   Describes a constructor that creates an object.  This is basically like a
   function but will show up with a `class` prefix::

      .. js:class:: MyAnimal(name[, age])

         :param string name: The name of the animal
         :param number age: an optional age for the animal

   This is rendered as:

   .. js:class:: MyAnimal(name[, age])
      :no-contents-entry:
      :no-index-entry:

      :param string name: The name of the animal
      :param number age: an optional age for the animal

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:data:: name

   Describes a global variable or constant.

.. rst:directive:: .. js:attribute:: object.name

   Describes the attribute *name* of *object*.

.. _js-xref-roles:

These roles are provided to refer to the described objects:

.. rst:role:: js:mod
              js:func
              js:meth
              js:class
              js:data
              js:attr
