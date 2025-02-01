More Sphinx customization
=========================

There are two main ways to customize your documentation beyond what is possible
with core Sphinx: extensions and themes.

Enabling a built-in extension
-----------------------------

In addition to these configuration values, you can customize Sphinx even more
by using :doc:`extensions </usage/extensions/index>`.  Sphinx ships several
:ref:`builtin ones <builtin-extensions>`, and there are many more
:ref:`maintained by the community <third-party-extensions>`.

For example, to enable the :mod:`sphinx.ext.duration` extension,
locate the ``extensions`` list in your ``conf.py`` and add one element as
follows:

.. code-block:: python
   :caption: docs/source/conf.py

   # Add any Sphinx extension module names here, as strings. They can be
   # extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
   # ones.
   extensions = [
       'sphinx.ext.duration',
   ]

After that, every time you generate your documentation, you will see a short
durations report at the end of the console output, like this one:

.. code-block:: console

   (.venv) $ make html
   ...
   The HTML pages are in build/html.

   ====================== slowest reading durations =======================
   0.042 temp/source/index

Using a third-party HTML theme
------------------------------

Themes, on the other hand, are a way to customize the appearance of your
documentation.  Sphinx has several :ref:`builtin themes <builtin-themes>`, and
there are also `third-party ones <https://sphinx-themes.org/>`_.

For example, to use the `Furo <https://pradyunsg.me/furo/>`_ third-party theme
in your HTML documentation, first you will need to install it with ``pip`` in
your Python virtual environment, like this:

.. code-block:: console

   (.venv) $ pip install furo

And then, locate the ``html_theme`` variable on your ``conf.py`` and replace
its value as follows:

.. code-block:: python
   :caption: docs/source/conf.py

   # The theme to use for HTML and HTML Help pages.  See the documentation for
   # a list of builtin themes.
   #
   html_theme = 'furo'

With this change, you will notice that your HTML documentation has now a new
appearance:

.. figure:: /_static/tutorial/lumache-furo.png
   :width: 80%
   :align: center
   :alt: HTML documentation of Lumache with the Furo theme

   HTML documentation of Lumache with the Furo theme

It is now time to :doc:`expand the narrative documentation and split it into
several documents </tutorial/narrative-documentation>`.
