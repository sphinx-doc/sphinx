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

Sphinx is written in `Python`__ and supports Python 3.5+.

__ https://docs.python-guide.org/


Linux
-----

Debian/Ubuntu
~~~~~~~~~~~~~

Install either ``python3-sphinx`` (Python 3) or ``python-sphinx`` (Python 2)
using :command:`apt-get`:

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
__ https://www.anaconda.com/download/#macos

Homebrew
~~~~~~~~

::

   $ brew install sphinx-doc

For more information, refer to the `package overview`__.

__ https://formulae.brew.sh/formula/sphinx-doc

MacPorts
~~~~~~~~

Install either ``python36-sphinx`` (Python 3) or ``python27-sphinx`` (Python 2)
using :command:`port`:

::

   $ sudo port install py36-sphinx

To set up the executable paths, use the ``port select`` command:

::

   $ sudo port select --set python python36
   $ sudo port select --set sphinx py36-sphinx

For more information, refer to the `package overview`__.

__ https://www.macports.org/ports.php?by=library&substr=py36-sphinx

Anaconda
~~~~~~~~

::

   $ conda install sphinx

Windows
-------

.. todo:: Could we start packaging this?

Most Windows users do not have Python installed by default, so we begin with
the installation of Python itself.  If you are unsure, open the *Command
Prompt* (:kbd:`⊞Win-r` and type :command:`cmd`).  Once the command prompt is
open, type :command:`python --version` and press Enter.  If Python is
available, you will see the version of Python printed to the screen.  If you do
not have Python installed, refer to the `Hitchhikers Guide to Python's`__
Python on Windows installation guides. You must install `Python 3`__.

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
