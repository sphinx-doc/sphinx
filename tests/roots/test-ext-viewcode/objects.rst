Testing object descriptions
===========================

.. function:: func_without_module(a, b, *c[, d])

   Does something.

.. function:: func_without_body()

.. function:: func_noindex
   :no-index:

.. function:: func_with_module
   :module: foolib

Referring to :func:`func with no index <func_noindex>`.
Referring to :func:`nothing <>`.

.. module:: mod
   :synopsis: Module synopsis.
   :platform: UNIX

.. function:: func_in_module

.. class:: Cls

   .. method:: meth1

   .. staticmethod:: meths

   .. attribute:: attr

.. explicit class given
.. method:: Cls.meth2

.. explicit module given
.. exception:: Error(arg1, arg2)
   :module: errmod

.. data:: var


.. currentmodule:: None

.. function:: func_without_module2() -> annotation

.. object:: long(parameter, \
              list)
            another one

.. class:: TimeInt

   Has only one parameter (triggers special behavior...)

   :param moo: |test|
   :type moo: |test|

.. |test| replace:: Moo

.. class:: Time(hour, minute, isdst)

   :param year: The year.
   :type year: TimeInt
   :param TimeInt minute: The minute.
   :param isdst: whether it's DST
   :type isdst: * some complex
                * expression
   :returns: a new :class:`Time` instance
   :rtype: :class:`Time`
   :raises ValueError: if the values are out of range
   :ivar int hour: like *hour*
   :ivar minute: like *minute*
   :vartype minute: int
   :param hour: Some parameter
   :type hour: DuplicateType
   :param hour: Duplicate param.  Should not lead to crashes.
   :type hour: DuplicateType
   :param .Cls extcls: A class from another module.


C items
=======

.. c:function:: Sphinx_DoSomething()

.. c:member:: SphinxStruct.member

.. c:macro:: SPHINX_USE_PYTHON

.. c:type:: SphinxType

.. c:var:: sphinx_global


Javascript items
================

.. js:function:: foo()

.. js:data:: bar

.. documenting the method of any object
.. js:function:: bar.baz(href, callback[, errback])

   :param string href: The location of the resource.
   :param callback: Gets called with the data returned by the resource.
   :throws InvalidHref: If the `href` is invalid.
   :returns: `undefined`

.. js:attribute:: bar.spam

References
==========

Referencing :class:`mod.Cls` or :Class:`mod.Cls` should be the same.

With target: :c:func:`Sphinx_DoSomething()` (parentheses are handled),
:c:member:`SphinxStruct.member`, :c:macro:`SPHINX_USE_PYTHON`,
:c:type:`SphinxType *` (pointer is handled), :c:data:`sphinx_global`.

Without target: :c:func:`CFunction`. :c:func:`!malloc`.

:js:func:`foo()`
:js:func:`foo`

:js:data:`bar`
:js:func:`bar.baz()`
:js:func:`bar.baz`
:js:func:`~bar.baz()`

:js:attr:`bar.baz`


Others
======

.. envvar:: HOME

.. program:: python

.. cmdoption:: -c command

.. program:: perl

.. cmdoption:: -c

.. option:: +p

Link to :option:`perl +p`.


User markup
===========

.. userdesc:: myobj:parameter

   Description of userdesc.


Referencing :userdescrole:`myobj`.


CPP domain
==========

.. cpp:class:: n::Array<T,d>

   .. cpp:function:: T& operator[]( unsigned j )
                     const T& operator[]( unsigned j ) const
