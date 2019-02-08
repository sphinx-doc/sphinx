Developing a "recipe" extension
===============================

The objective of this tutorial is to illustrate roles, directives and domains.
Once complete, we will be able to use this extension to describe a recipe and
reference that recipe from elsewhere in our documentation.

.. note::

   This tutorial is based on a guide first published on `opensource.com`_ and
   is provided here with the original author's permission.

   .. _opensource.com: https://opensource.com/article/18/11/building-custom-workflows-sphinx


Overview
--------

We want the extension to add the following to Sphinx:

* A ``recipe`` :term:`directive`, containing some content describing the recipe
  steps, along with a ``:contains:`` argument highlighting the main ingredients
  of the recipe.

* A ``reref`` :term:`role`, which provides a cross-reference to the recipe
  itself.

* A ``rcp`` :term:`domain`, which allows us to tie together the above role and
  domain, along with things like indices.

For that, we will need to add the following elements to Sphinx:

* A new directive called ``recipe``

* New indexes to allow us to reference ingredient and recipes

* A new domain called ``rcp``, which will contain the ``recipe`` directive and
  ``reref`` role


Prerequisites
-------------

As with :doc:`the previous extensions <todo>`, we will not be distributing this
plugin via PyPI so once again we need a Sphinx project to call this from.  You
can use an existing project or create a new one using
:program:`sphinx-quickstart`.

We assume you are using separate source (:file:`source`) and build
(:file:`build`) folders. Your extension file could be in any folder of your
project. In our case, let's do the following:

#. Create an :file:`_ext` folder in :file:`source`
#. Create a new Python file in the :file:`_ext` folder called :file:`recipe.py`

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── todo.py
          ├── conf.py
          └── index.rst


Writing the extension
---------------------

Open :file:`receipe.py` and paste the following code in it, all of which we
will explain in detail shortly:

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:

Let's look at each piece of this extension step-by-step to explain what's going
on.

.. rubric:: The directive class

The first thing to examine is the ``RecipeNode`` directive:

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :lines: 15-40

Unlike :doc:`helloworld` and :doc:`todo`, this directive doesn't derive from
:class:`docutils.parsers.rst.Directive` and doesn't define a ``run`` method.
Instead, it derives from :class:`sphinx.directives.ObjectDescription` and
defines  ``handle_signature`` and ``add_target_and_index`` methods. This is
because ``ObjectDescription`` is a special-purpose directive that's intended
for describing things like classes, functions, or, in our case, recipes. More
specifically, ``handle_signature`` implements parsing the signature of the
directive and passes on the object's name and type to its superclass, while
``add_taget_and_index`` adds a target (to link to) and an entry to the index
for this node.

We also see that this directive defines ``has_content``, ``required_arguments``
and ``option_spec``. Unlike the ``TodoDirective`` directive added in the
:doc:`previous tutorial <todo>`, this directive takes a single argument, the
recipe name, and an optional argument, ``contains``, in addition to the nested
reStructuredText in the body.

.. rubric:: The index classes

.. currentmodule:: sphinx.domains

.. todo:: Add brief overview of indices

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :lines: 44-172

Both ``IngredientIndex`` and ``RecipeIndex`` are derived from :class:`Index`.
They implement custom logic to generate a tuple of values that define the
index. Note that ``RecipeIndex`` is a degenerate index that has only one entry.
Extending it to cover more object types is not yet part of the code.

Both indices use the method :meth:`Index.generate` to do their work. This
method combines the information from our domain, sorts it, and returns it in a
list structure that will be accepted by Sphinx. This might look complicated but
all it really is is a list of tuples like ``('tomato', 'TomatoSoup', 'test',
'rec-TomatoSoup',...)``. Refer to the :doc:`domain API guide
</extdev/domainapi>` for more information on this API.

.. rubric:: The domain

A Sphinx domain is a specialized container that ties together roles,
directives, and indices, among other things. Let's look at the domain we're
creating here.

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :lines: 175-223

There are some interesting things to note about this ``rcp`` domain and domains
in general. Firstly, we actually register our directives, roles and indices
here, via the ``directives``, ``roles`` and ``indices`` attributes, rather than
via calls later on in ``setup``. We can also note that we aren't actually
defining a custom role and are instead reusing the
:class:`sphinx.roles.XRefRole` role and defining the
:class:`sphinx.domains.Domain.resolve_xref` method. This method takes two
arguments, ``typ`` and ``target``, which refer to the cross-reference type and
its target name. We'll use ``target`` to resolve our destination from our
domain's ``objects`` because we currently have only one type of node.

Moving on, we can see that we've defined two items in ``intitial_data``:
``objects`` and ``obj2ingredient``. These contain a list of all objects defined
(i.e. all recipes) and a hash that maps a canonical ingredient name to the list
of objects. The way we name objects is common across our extension and is
defined in the ``get_full_qualified_name`` method. For each object created, the
canonical name is ``rcp.<typename>.<objectname>``, where ``<typename>`` is the
Python type of the object, and ``<objectname>`` is the name the documentation
writer gives the object. This enables the extension to use different object
types that share the same name. Having a canonical name and central place for
our objects is a huge advantage. Both our indices and our cross-referencing
code use this feature.

.. rubric:: The ``setup`` function

.. currentmodule:: sphinx.application

:doc:`As always <todo>`, the ``setup`` function is a requirement and is used to
hook the various parts of our extension into Sphinx. Let's look at the
``setup`` function for this extension.

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :lines: 226-

This looks a little different to what we're used to seeing. There are no calls
to :meth:`~Sphinx.add_directive` or even :meth:`~Sphinx.add_role`. Instead, we
have a single call to :meth:`~Sphinx.add_domain` followed by some
initialization of the :ref:`standard domain <domains-std>`. This is because we
had already registered our directives, roles and indexes as part of the
directive itself.


Using the extension
-------------------

You can now use the extension throughout your project. For example:

.. code-block:: rst
   :caption: index.rst

   Joe's Recipes
   =============

   Below are a collection of my favourite receipes. I highly recommend the
   :rcp:reref:`TomatoSoup` receipe in particular!

   .. toctree::

      tomato-soup

.. code-block:: rst
   :caption: tomato-soup.rst

   The recipe contains `tomato` and `cilantro`.

   .. rcp:recipe:: TomatoSoup
     :contains: tomato cilantro salt pepper

    This recipe is a tasty tomato soup, combine all ingredients
    and cook.

The important things to note are the use of the ``:rcp:recipe:`` role to
cross-reference the recipe actually defined elsewhere (using the
``:rcp:recipe:`` directive.


Further reading
---------------

For more information, refer to the `docutils`_ documentation and
:doc:`/extdev/index`.

.. _docutils: http://docutils.sourceforge.net/docs/
