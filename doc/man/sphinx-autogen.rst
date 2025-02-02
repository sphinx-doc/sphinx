sphinx-autogen
==============

Synopsis
--------

**sphinx-autogen** [*options*] <sourcefile> ...

Description
-----------

:program:`sphinx-autogen` is a tool for automatic generation of Sphinx sources
that, using the :py:mod:`~sphinx.ext.autodoc` extension, document items included
in :rst:dir:`autosummary` listing(s).

*sourcefile* is the path to one or more reStructuredText documents containing
:rst:dir:`autosummary` entries with the ``:toctree:`` option set. *sourcefile*
can be an :py:mod:`fnmatch`-style pattern.

Options
-------

.. program:: sphinx-autogen

.. option:: -o <outputdir>

   Directory to place the output file. If it does not exist, it is created.
   Defaults to the value passed to the ``:toctree:`` option.

.. option:: -s <suffix>, --suffix <suffix>

   Default suffix to use for generated files. Defaults to ``rst``.

.. option:: -t <templates>, --templates <templates>

   Custom template directory. Defaults to ``None``.

.. option:: -i, --imported-members

   Document imported members.

.. option:: -a, --respect-module-all

   Document exactly the members in a module's ``__all__`` attribute.

.. option:: --remove-old

   Remove existing files in the output directory
   that are not generated anymore.

Example
-------

Given the following directory structure::

    docs
    ├── index.rst
    └── ...
    foobar
    ├── foo
    │   └── __init__.py
    └── bar
        ├── __init__.py
        └── baz
            └── __init__.py

and assuming ``docs/index.rst`` contained the following:

.. code-block:: rst

    Modules
    =======

    .. autosummary::
       :toctree: modules

       foobar.foo
       foobar.bar
       foobar.bar.baz

If you run the following:

.. code-block:: console

    $ PYTHONPATH=. sphinx-autogen docs/index.rst

then the following stub files will be created in ``docs``::

    docs
    ├── index.rst
    └── modules
        ├── foobar.bar.rst
        ├── foobar.bar.baz.rst
        └── foobar.foo.rst

and each of those files will contain a :py:mod:`~sphinx.ext.autodoc` directive
and some other information.

See also
--------

:manpage:`sphinx-build(1)`, :manpage:`sphinx-apidoc(1)`
