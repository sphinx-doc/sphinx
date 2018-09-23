.. _setuptools:

Setuptools integration
======================

Sphinx supports integration with setuptools and distutils through a custom
command - :class:`~sphinx.setup_command.BuildDoc`.

Using setuptools integration
----------------------------

The Sphinx build can then be triggered from distutils, and some Sphinx
options can be set in ``setup.py`` or ``setup.cfg`` instead of Sphinx's own
configuration file.

For instance, from ``setup.py``::

    # this is only necessary when not using setuptools/distribute
    from sphinx.setup_command import BuildDoc
    cmdclass = {'build_sphinx': BuildDoc}

    name = 'My project'
    version = '1.2'
    release = '1.2.0'
    setup(
        name=name,
        author='Bernard Montgomery',
        version=release,
        cmdclass=cmdclass,
        # these are optional and override conf.py settings
        command_options={
            'build_sphinx': {
                'project': ('setup.py', name),
                'version': ('setup.py', version),
                'release': ('setup.py', release),
                'source_dir': ('setup.py', 'doc')}},
    )

.. note::

    If you set Sphinx options directly in the ``setup()`` command, replace
    hyphens in variable names with underscores. In the example above,
    ``source-dir`` becomes ``source_dir``.

Or add this section in ``setup.cfg``::

    [build_sphinx]
    project = 'My project'
    version = 1.2
    release = 1.2.0
    source-dir = 'doc'

Once configured, call this by calling the relevant command on ``setup.py``::

    $ python setup.py build_sphinx

Options for setuptools integration
----------------------------------

.. confval:: fresh-env

   A boolean that determines whether the saved environment should be discarded
   on build. Default is false.

   This can also be set by passing the `-E` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -E

.. confval:: all-files

   A boolean that determines whether all files should be built from scratch.
   Default is false.

   This can also be set by passing the `-a` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -a

.. confval:: source-dir

   The target source directory. This can be relative to the ``setup.py`` or
   ``setup.cfg`` file, or it can be absolute.  It defaults to ``./doc`` or
   ``./docs`` if either contains a file named ``conf.py`` (checking ``./doc``
   first); otherwise it defaults to the current directory.

   This can also be set by passing the `-s` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -s $SOURCE_DIR

.. confval:: build-dir

   The target build directory. This can be relative to the ``setup.py`` or
   ``setup.cfg`` file, or it can be absolute. Default is ``./build/sphinx``.

.. confval:: config-dir

   Location of the configuration directory. This can be relative to the
   ``setup.py`` or ``setup.cfg`` file, or it can be absolute. Default is to use
   `source-dir`.

   This can also be set by passing the `-c` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -c $CONFIG_DIR

   .. versionadded:: 1.0

.. confval:: builder

   The builder or list of builders to use. Default is ``html``.

   This can also be set by passing the `-b` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -b $BUILDER

   .. versionchanged:: 1.6
      This can now be a comma- or space-separated list of builders

.. confval:: warning-is-error

   A boolean that ensures Sphinx warnings will result in a failed build.
   Default is false.

   This can also be set by passing the `-W` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -W

   .. versionadded:: 1.5

.. confval:: project

   The documented project's name. Default is ``''``.

   .. versionadded:: 1.0

.. confval:: version

   The short X.Y version. Default is ``''``.

   .. versionadded:: 1.0

.. confval:: release

   The full version, including alpha/beta/rc tags. Default is ``''``.

   .. versionadded:: 1.0

.. confval:: today

   How to format the current date, used as the replacement for ``|today|``.
   Default is ``''``.

   .. versionadded:: 1.0

.. confval:: link-index

   A boolean that ensures index.html will be linked to the master doc. Default
   is false.

   This can also be set by passing the `-i` flag to ``setup.py``:

   .. code-block:: bash

      $ python setup.py build_sphinx -i

   .. versionadded:: 1.0

.. confval:: copyright

   The copyright string. Default is ``''``.

   .. versionadded:: 1.3

.. confval:: nitpicky

   Run in nit-picky mode.  Currently, this generates warnings for all missing
   references.  See the config value :confval:`nitpick_ignore` for a way to
   exclude some references as "known missing".

   .. versionadded:: 1.8

.. confval:: pdb

   A boolean to configure ``pdb`` on exception. Default is false.

   .. versionadded:: 1.5
