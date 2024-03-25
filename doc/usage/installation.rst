=================
Installing Sphinx
=================

.. contents::
   :depth: 1
   :local:
   :backlinks: none

.. highlight:: console

Overview
--------

Sphinx is written in `Python`__ and supports Python 3.9+. It builds upon the
shoulders of many third-party libraries such as `Docutils`__ and `Jinja`__,
which are installed when Sphinx is installed.

__ https://docs.python-guide.org/
__ https://docutils.sourceforge.io/
__ https://jinja.palletsprojects.com/


Linux
-----

Debian/Ubuntu
~~~~~~~~~~~~~

Install either ``python3-sphinx`` using :command:`apt-get`:

::

   $ apt-get install python3-sphinx

If it not already present, this will install Python for you.

RHEL, CentOS
~~~~~~~~~~~~

Install ``python-sphinx`` using :command:`yum`:

::

   $ yum install python-sphinx

If it not already present, this will install Python for you.

Other distributions
~~~~~~~~~~~~~~~~~~~

Most Linux distributions have Sphinx in their package repositories.  Usually
the package is called ``python3-sphinx``, ``python-sphinx`` or ``sphinx``.  Be
aware that there are at least two other packages with ``sphinx`` in their name:
a speech recognition toolkit (*CMU Sphinx*) and a full-text search database
(*Sphinx search*).


macOS
-----

Sphinx can be installed using `Homebrew`__, `MacPorts`__, or as part of
a Python distribution such as `Anaconda`__.

__ https://brew.sh/
__ https://www.macports.org/
__ https://www.anaconda.com/download

Homebrew
~~~~~~~~

::

   $ brew install sphinx-doc

For more information, refer to the `package overview`__.

__ https://formulae.brew.sh/formula/sphinx-doc

MacPorts
~~~~~~~~

Install either ``python3x-sphinx`` using :command:`port`:

::

   $ sudo port install py39-sphinx

To set up the executable paths, use the ``port select`` command:

::

   $ sudo port select --set python python39
   $ sudo port select --set sphinx py39-sphinx

For more information, refer to the `package overview`__.

__ https://www.macports.org/ports.php?by=library&substr=py39-sphinx

Anaconda
~~~~~~~~

::

   $ conda install sphinx

Windows
-------

Sphinx can be install using `Chocolatey`__ or
:ref:`installed manually <windows-other-method>`.

__ https://chocolatey.org/

Chocolatey
~~~~~~~~~~

::

   $ choco install sphinx

You would need to `install Chocolatey
<https://chocolatey.org/install>`_
before running this.

For more information, refer to the `chocolatey page`__.

__ https://chocolatey.org/packages/sphinx/

.. _windows-other-method:

Other Methods
~~~~~~~~~~~~~

Most Windows users do not have Python installed by default, so we begin with
the installation of Python itself.  To check if you already have Python
installed, open the *Command Prompt* (:kbd:`⊞Win-r` and type :command:`cmd`).
Once the command prompt is open, type :command:`python --version` and press
Enter.  If Python is installed, you will see the version of Python printed to
the screen.  If you do not have Python installed, refer to the `Hitchhikers
Guide to Python's`__ Python on Windows installation guides. You must install
`Python 3`__.

Once Python is installed, you can install Sphinx using :command:`pip`.  Refer
to the :ref:`pip installation instructions <install-pypi>` below for more
information.

__ https://docs.python-guide.org/
__ https://docs.python-guide.org/starting/install3/win/


.. _install-pypi:

Installation from PyPI
----------------------

Sphinx packages are published on the `Python Package Index
<https://pypi.org/project/Sphinx/>`_.  The preferred tool for installing
packages from *PyPI* is :command:`pip`.  This tool is provided with all modern
versions of Python.

On Linux or MacOS, you should open your terminal and run the following command.

::

   $ pip install -U sphinx

On Windows, you should open *Command Prompt* (:kbd:`⊞Win-r` and type
:command:`cmd`) and run the same command.

.. code-block:: doscon

   C:\> pip install -U sphinx

After installation, type :command:`sphinx-build --version` on the command
prompt.  If everything worked fine, you will see the version number for the
Sphinx package you just installed.

Installation from *PyPI* also allows you to install the latest development
release.  You will not generally need (or want) to do this, but it can be
useful if you see a possible bug in the latest stable release.  To do this, use
the ``--pre`` flag.

::

   $ pip install -U --pre sphinx

Using virtual environments
~~~~~~~~~~~~~~~~~~~~~~~~~~

When installing Sphinx using pip,
it is highly recommended to use *virtual environments*,
which isolate the installed packages from the system packages,
thus removing the need to use administrator privileges.
To create a virtual environment in the ``.venv`` directory,
use the following command.

::

   $ python -m venv .venv

.. seealso:: :mod:`venv` -- creating virtual environments

.. warning::

   Note that in some Linux distributions, such as Debian and Ubuntu,
   this might require an extra installation step as follows.

   .. code-block:: console

      $ apt-get install python3-venv

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
