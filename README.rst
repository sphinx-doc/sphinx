=================
README for Sphinx
=================

Installing
==========

Use ``setup.py``::

   python setup.py build
   sudo python setup.py install


Reading the docs
================

After installing::

   cd doc
   sphinx-build . _build/html

Then, direct your browser to ``_build/html/index.html``.

Or read them online at <http://sphinx-doc.org/>.


Testing
=======

To run the tests with the interpreter available as ``python``, use::

    make test

If you want to use a different interpreter, e.g. ``python3``, use::

    PYTHON=python3 make test

Continuous testing runs on drone.io:

.. image:: https://drone.io/bitbucket.org/birkenfeld/sphinx/status.png
   :target: https://drone.io/bitbucket.org/birkenfeld/sphinx/


Contributing
============

#. Check for open issues or open a fresh issue to start a discussion around a
   feature idea or a bug. There are Non Assigned issues:
   https://bitbucket.org/birkenfeld/sphinx/issues?status=new&status=open&responsible=
#. If you feel uncomfortable or uncertain about an issue or your changes, feel
   free to email sphinx-dev@googlegroups.com.
#. Fork the repository on Bitbucket https://bitbucket.org/birkenfeld/sphinx
   to start making your changes to the **default** branch for next major
   version, or **stable** branch for next minor version.
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.
#. Send a pull request and bug the maintainer until it gets merged and
   published. Make sure to add yourself to AUTHORS
   <https://bitbucket.org/birkenfeld/sphinx/src/tip/AUTHORS> and the change to
   CHANGES <https://bitbucket.org/birkenfeld/sphinx/src/tip/CHANGES>.
