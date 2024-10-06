.. _tutorial-adding-domain:

Adding a reference domain
=========================

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
  steps, along with a ``:contains:`` option highlighting the main ingredients
  of the recipe.

* A ``ref`` :term:`role`, which provides a cross-reference to the recipe
  itself.

* A ``recipe`` :term:`domain`, which allows us to tie together the above role
  and domain, along with things like indices.

For that, we will need to add the following elements to Sphinx:

* A new directive called ``recipe``

* New indexes to allow us to reference ingredient and recipes

* A new domain called ``recipe``, which will contain the ``recipe`` directive
  and ``ref`` role


Prerequisites
-------------

We need the same setup as in
:ref:`the previous extensions <tutorial-extend-build>`.
This time,
we will be putting out extension in a file called :file:`recipe.py`.

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── recipe.py
          ├── conf.py
          └── index.rst


Writing the extension
---------------------

Open :file:`recipe.py` and paste the following code in it, all of which we will
explain in detail shortly:

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:

Let's look at each piece of this extension step-by-step to explain what's going
on.

.. rubric:: The directive class

The first thing to examine is the ``RecipeDirective`` directive:

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :pyobject: RecipeDirective

Unlike :ref:`tutorial-extending-syntax` and :ref:`tutorial-extend-build`,
this directive doesn't derive from
:class:`docutils.parsers.rst.Directive` and doesn't define a ``run`` method.
Instead, it derives from :class:`sphinx.directives.ObjectDescription` and
defines  ``handle_signature`` and ``add_target_and_index`` methods. This is
because ``ObjectDescription`` is a special-purpose directive that's intended
for describing things like classes, functions, or, in our case, recipes. More
specifically, ``handle_signature`` implements parsing the signature of the
directive and passes on the object's name and type to its superclass, while
``add_target_and_index`` adds a target (to link to) and an entry to the index
for this node.

We also see that this directive defines ``has_content``, ``required_arguments``
and ``option_spec``. Unlike the ``TodoDirective`` directive added in the
:ref:`previous tutorial <tutorial-extend-build>`,
this directive takes a single argument,
the recipe name, and an option, ``contains``,
in addition to the nested reStructuredText in the body.

.. rubric:: The index classes

.. currentmodule:: sphinx.domains

.. todo:: Add brief overview of indices

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :pyobject: IngredientIndex

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :pyobject: RecipeIndex

Both ``IngredientIndex`` and ``RecipeIndex`` are derived from :class:`Index`.
They implement custom logic to generate a tuple of values that define the
index. Note that ``RecipeIndex`` is a simple index that has only one entry.
Extending it to cover more object types is not yet part of the code.

Both indices use the method :meth:`Index.generate` to do their work. This
method combines the information from our domain, sorts it, and returns it in a
list structure that will be accepted by Sphinx. This might look complicated but
all it really is is a list of tuples like ``('tomato', 'TomatoSoup', 'test',
'rec-TomatoSoup',...)``. Refer to the :doc:`domain API guide
</extdev/domainapi>` for more information on this API.

These index pages can be referenced with the :rst:role:`ref` role by combining
the domain name and the index ``name`` value. For example, ``RecipeIndex`` can be
referenced with ``:ref:`recipe-recipe``` and ``IngredientIndex`` can be referenced
with ``:ref:`recipe-ingredient```.

.. rubric:: The domain

A Sphinx domain is a specialized container that ties together roles,
directives, and indices, among other things. Let's look at the domain we're
creating here.

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :pyobject: RecipeDomain

There are some interesting things to note about this ``recipe`` domain and domains
in general. Firstly, we actually register our directives, roles and indices
here, via the ``directives``, ``roles`` and ``indices`` attributes, rather than
via calls later on in ``setup``. We can also note that we aren't actually
defining a custom role and are instead reusing the
:class:`sphinx.roles.XRefRole` role and defining the
:class:`sphinx.domains.Domain.resolve_xref` method. This method takes two
arguments, ``typ`` and ``target``, which refer to the cross-reference type and
its target name. We'll use ``target`` to resolve our destination from our
domain's ``recipes`` because we currently have only one type of node.

Moving on, we can see that we've defined ``initial_data``. The values defined in
``initial_data`` will be copied to ``env.domaindata[domain_name]`` as the
initial data of the domain, and domain instances can access it via
``self.data``. We see that we have defined two items in ``initial_data``:
``recipes`` and ``recipe_ingredients``. Each contains a list of all objects
defined (i.e. all recipes) and a hash that maps a canonical ingredient name to
the list of objects. The way we name objects is common across our extension and
is defined in the ``get_full_qualified_name`` method. For each object created,
the canonical name is ``recipe.<recipename>``, where ``<recipename>`` is the
name the documentation writer gives the object (a recipe). This enables the
extension to use different object types that share the same name. Having a
canonical name and central place for our objects is a huge advantage. Both our
indices and our cross-referencing code use this feature.

.. rubric:: The ``setup`` function

.. currentmodule:: sphinx.application

:ref:`As always <tutorial-extend-build>`,
the ``setup`` function is a requirement and is used to
hook the various parts of our extension into Sphinx. Let's look at the
``setup`` function for this extension.

.. literalinclude:: examples/recipe.py
   :language: python
   :linenos:
   :pyobject: setup

This looks a little different to what we're used to seeing. There are no calls
to :meth:`~Sphinx.add_directive` or even :meth:`~Sphinx.add_role`. Instead, we
have a single call to :meth:`~Sphinx.add_domain` followed by some
initialization of the :doc:`standard domain </usage/domains/standard>`.
This is because we had already registered our directives,
roles and indexes as part of the directive itself.


Using the extension
-------------------

You can now use the extension throughout your project. For example:

.. code-block:: rst
   :caption: index.rst

   Joe's Recipes
   =============

   Below are a collection of my favourite recipes. I highly recommend the
   :recipe:ref:`TomatoSoup` recipe in particular!

   .. toctree::

      tomato-soup

.. code-block:: rst
   :caption: tomato-soup.rst

   The recipe contains `tomato` and `cilantro`.

   .. recipe:recipe:: TomatoSoup
      :contains: tomato, cilantro, salt, pepper

      This recipe is a tasty tomato soup, combine all ingredients
      and cook.

The important things to note are the use of the ``:recipe:ref:`` role to
cross-reference the recipe actually defined elsewhere (using the
``:recipe:recipe:`` directive).


Further reading
---------------

For more information, refer to the `docutils`_ documentation and
:doc:`/extdev/index`.

If you wish to share your extension across multiple projects or with others,
check out the :ref:`third-party-extensions` section.

.. _docutils: https://docutils.sourceforge.io/docs/
