=================
Installing Sphinx
=================

Sphinx is a Python application. It can be installed in one of the ways described
below.

.. contents:: Installation methods
   :depth: 2
   :local:
   :backlinks: none

.. highlight:: console

After installation, you can check that Sphinx is available by running ::

   $ sphinx-build --version

This should print out the Sphinx version number.


.. tip::

   For local development, it is
   generally recommended to install Sphinx into a non-global environment
   (using for example `venv`__ or `conda`__ environments).
   This will allow for the use of separate sphinx versions and third-party extensions
   for each sphinx project.

   __ https://docs.python.org/3/library/venv.html
   __ https://conda.io/projects/conda/en/latest/user-guide/getting-started.html


.. _install-pypi:

PyPI package
------------

Sphinx packages are published on the `Python Package Index
<https://pypi.org/project/Sphinx/>`_ (PyPI).  The preferred tool for installing
packages from PyPI is :command:`pip`, which is included in all modern versions of
Python.

Run the following command::

   $ pip install -U sphinx

.. tip::

   To avoid issues when rebuilding your environment,
   it is advisable to pin sphinx and third-party extension
   versions in a `requirements.txt file`__::

      $ pip install -r requirements.txt

   Or, if writing documentation for a Python package,
   place the dependencies in the `pyproject.toml file`__::

      $ pip install . --group docs

   __ https://pip.pypa.io/en/stable/reference/requirements-file-format/
   __ https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#dependencies-optional-dependencies

.. _install-conda:

Conda package
-------------
To work with :command:`conda`, you need a conda-based Python distribution such as
`anaconda`__, `miniconda`__, `miniforge`__ or `micromamba`__.

__ https://docs.anaconda.com/anaconda/
__ https://docs.anaconda.com/miniconda/
__ https://github.com/conda-forge/miniforge/
__ https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html


Sphinx is available both via the *anaconda main* channel (maintained by Anaconda
Inc.)

::

   $ conda install sphinx

as well as via the *conda-forge* community channel ::

   $ conda install -c conda-forge sphinx

OS-specific package manager
---------------------------

You may install a global version of Sphinx into your system using OS-specific
package managers. However, be aware that this is less flexible and you may run into
compatibility issues if you want to work across different projects.

Linux
~~~~~

Debian/Ubuntu
"""""""""""""

Install either ``python3-sphinx`` using :command:`apt-get`:

::

   $ apt-get install python3-sphinx

If it not already present, this will install Python for you.

RHEL, CentOS
""""""""""""

Install ``python-sphinx`` using :command:`yum`:

::

   $ yum install python-sphinx

If it not already present, this will install Python for you.

Other distributions
"""""""""""""""""""

Most Linux distributions have Sphinx in their package repositories.  Usually
the package is called ``python3-sphinx``, ``python-sphinx`` or ``sphinx``.  Be
aware that there are at least two other packages with ``sphinx`` in their name:
a speech recognition toolkit (*CMU Sphinx*) and a full-text search database
(*Sphinx search*).

macOS
~~~~~

Sphinx can be installed using `Homebrew`__, `MacPorts`__.

__ https://brew.sh/
__ https://www.macports.org/

Homebrew
""""""""

::

   $ brew install sphinx-doc

For more information, refer to the `package overview`__.

__ https://formulae.brew.sh/formula/sphinx-doc

MacPorts
""""""""

Install either ``python3x-sphinx`` using :command:`port`:

::

   $ sudo port install py314-sphinx

To set up the executable paths, use the ``port select`` command:

::

   $ sudo port select --set python python314
   $ sudo port select --set sphinx py314-sphinx

For more information, refer to the `package overview`__.

__ https://www.macports.org/ports.php?by=library&substr=py314-sphinx

Windows
~~~~~~~

Sphinx can be installed using `Chocolatey`__.

__ https://chocolatey.org/

Chocolatey
""""""""""

::

   $ choco install sphinx

You would need to `install Chocolatey
<https://chocolatey.org/install>`_
before running this.

For more information, refer to the `chocolatey page`__.

__ https://chocolatey.org/packages/sphinx/

Docker
------

Docker images for Sphinx are published on the `Docker Hub`_.  There are two kind
of images:

- `sphinxdoc/sphinx`_
- `sphinxdoc/sphinx-latexpdf`_

.. _Docker Hub: https://hub.docker.com/
.. _sphinxdoc/sphinx: https://hub.docker.com/r/sphinxdoc/sphinx
.. _sphinxdoc/sphinx-latexpdf: https://hub.docker.com/r/sphinxdoc/sphinx-latexpdf

Former one is used for standard usage of Sphinx, and latter one is mainly used for
PDF builds using LaTeX.  Please choose one for your purpose.

.. note::

   sphinxdoc/sphinx-latexpdf contains TeXLive packages. So the image is very large
   (over 2GB!).

.. hint::

   When using docker images, please use ``docker run`` command to invoke sphinx
   commands.  For example, you can use following command to create a Sphinx
   project:

   .. code-block:: console

      $ docker run -it --rm -v /path/to/document:/docs sphinxdoc/sphinx sphinx-quickstart

   And you can use the following command to build HTML document:

   .. code-block:: console

      $ docker run --rm -v /path/to/document:/docs sphinxdoc/sphinx make html

For more details, please read `README file`__ of docker images.

.. __: https://hub.docker.com/r/sphinxdoc/sphinx

Installation of the latest development release
----------------------------------------------

You can install the latest development from *PyPI* using the ``--pre`` flag::

   $ pip install -U --pre sphinx

.. warning::

   You will not generally need (or want) to do this, but it can be
   useful if you see a possible bug in the latest stable release.

Installation from source
------------------------

You can install Sphinx directly from a clone of the `Git repository`__.  This
can be done either by cloning the repo and installing from the local clone, on
simply installing directly via :command:`git`.

::

   $ git clone https://github.com/sphinx-doc/sphinx
   $ cd sphinx
   $ pip install .

::

   $ pip install git+https://github.com/sphinx-doc/sphinx

You can also download a snapshot of the Git repo in either `tar.gz`__ or
`zip`__ format.  Once downloaded and extracted, these can be installed with
:command:`pip` as above.

.. highlight:: default

__ https://github.com/sphinx-doc/sphinx
__ https://github.com/sphinx-doc/sphinx/archive/master.tar.gz
__ https://github.com/sphinx-doc/sphinx/archive/master.zip
