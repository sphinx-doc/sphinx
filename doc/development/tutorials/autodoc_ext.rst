.. _autodoc_ext_tutorial:

Developing autodoc extension for IntEnum
========================================

The objective of this tutorial is to create an extension that adds
support for new type for autodoc. This autodoc extension will format
the ``IntEnum`` class from Python standard library. (module ``enum``)

Overview
--------

We want the extension that will create auto-documentation for IntEnum.
``IntEnum`` is the integer enum class from standard library ``enum`` module.

Currently this class has no special auto documentation behavior.

We want to add following to autodoc:

* A new ``autointenum`` directive that will document the ``IntEnum`` class.
* The generated documentation will have all the enum possible values
  with names.
* The ``autointenum`` directive will have an option ``:hex:`` which will
  cause the integers be printed in hexadecimal form.


Prerequisites
-------------

We need the same setup as in :doc:`the previous extensions <todo>`. This time,
we will be putting out extension in a file called :file:`autodoc_intenum.py`.
The :file:`my_enums.py` will contain the sample enums we will document.

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── autodoc_intenum.py
          ├── conf.py
          ├── index.rst
          └── my_enums.py


Writing the extension
---------------------

Start with ``setup`` function for the extension.

.. literalinclude:: examples/autodoc_intenum.py
   :language: python
   :linenos:
   :pyobject: setup


The :meth:`~Sphinx.setup_extension` method will pull the autodoc extension
because our new extension depends on autodoc. :meth:`~Sphinx.add_autodocumenter`
is the method that registers our new auto documenter class.

We want to import certain objects from the autodoc extension:

.. literalinclude:: examples/autodoc_intenum.py
   :language: python
   :linenos:
   :lines: 1-7


There are several different documenter classes such as ``MethodDocumenter``
or ``AttributeDocumenter`` available in the autodoc extension but
our new class is the subclass of ``ClassDocumenter`` which a
documenter class used by autodoc to document classes.

This is the definition of our new the auto-documenter class:

.. literalinclude:: examples/autodoc_intenum.py
   :language: python
   :linenos:
   :pyobject: IntEnumDocumenter


Important attributes of the new class:

**objtype**
    This attribute determines the ``auto`` directive name. In
    this case the auto directive will be ``autointenum``.

**directivetype**
    This attribute sets the generated directive name. In
    this example the generated directive will be ``.. :py:class::``.

**priority**
    the larger the number the higher is the priority. We want our
    documenter be higher priority than the parent.

**option_spec**
    option specifications. We copy the parent class options and
    add a new option *hex*.


Overridden members:

**can_document_member**
    This member is important to override. It should
    return *True* when the passed object can be documented by this class.

**add_directive_header**
    This method generates the directive header. We add
    **:final:** directive option. Remember to call **super** or no directive
    will be generated.

**add_content**
    This method generates the body of the class documentation.
    After calling the super method we generate lines for enum description.


Using the extension
-------------------

You can now use the new autodoc directive to document any ``IntEnum``.

For example, you have the following ``IntEnum``:

.. code-block:: python
   :caption: my_enums.py
   
   class Colors(IntEnum):
       """Colors enumerator"""
       NONE = 0
       RED = 1
       GREEN = 2
       BLUE = 3


This will be the documentation file with auto-documentation directive:

.. code-block:: rst
   :caption: index.rst

   .. autointenum:: my_enums.Colors


