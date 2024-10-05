========================
Sphinx's release process
========================

Versioning
----------

Sphinx adheres to :pep:`440` versions, with a ``major.minor.micro`` scheme for
the *release segment* (e.g. 1.2.3).
The major, minor, and micro version parts should be altered as follows:

* The major version part should be incremented for incompatible behavior change and
  public API updates.

* The minor version part should be incremented for most releases of Sphinx, where
  backwards-compatibility of API and features are preserves.

* The micro version part should only be incremented for urgent bugfix-only releases.

When the major version part is incremented, the minor and micro version parts
must be set to ``0``.
When the minor version part is incremented, the micro version part must be set
to ``0``.

New major versions should come with a beta-testing period before the final
release.


Deprecating a feature
---------------------

There are a couple reasons that code in Sphinx might be deprecated:

* If a feature has been improved or modified in a backwards-incompatible way,
  the old feature or behavior will be deprecated.

* Sometimes Sphinx will include a backport of a Python library that's not
  included in a version of Python that Sphinx currently supports. When Sphinx
  no longer needs to support the older version of Python that doesn't include
  the library, the library will be deprecated in Sphinx.

As the :ref:`deprecation-policy` describes, the first release of Sphinx that
deprecates a feature (``A.B``) should raise a ``RemovedInSphinxXXWarning``
(where ``XX`` is the Sphinx version where the feature will be removed) when the
deprecated feature is invoked. Assuming we have good test coverage, these
warnings are converted to errors when running the test suite with warnings
enabled::

    pytest -Wall

Thus, when adding a ``RemovedInSphinxXXWarning`` you need to eliminate or
silence any warnings generated when running the tests.


.. _deprecation-policy:

Deprecation policy
------------------

MAJOR and MINOR releases may deprecate certain features from previous
releases. If a feature is deprecated in a release A.x, it will continue to
work in all A.x.x versions (for all versions of x). It will continue to work
in all B.x.x versions but raise deprecation warnings. Deprecated features
will be removed at the C.0.0. It means the deprecated feature will work during
2 MAJOR releases at least.

So, for example, if we decided to start the deprecation of a function in
Sphinx 2.x:

* Sphinx 2.x will contain a backwards-compatible replica of the function
  which will raise a ``RemovedInSphinx40Warning``.
  This is a subclass of :exc:`python:PendingDeprecationWarning`, i.e. it
  will not get displayed by default.

* Sphinx 3.x will still contain the backwards-compatible replica, but
  ``RemovedInSphinx40Warning`` will be a subclass of
  :exc:`python:DeprecationWarning` then, and gets displayed by default.

* Sphinx 4.0 will remove the feature outright.

Deprecation warnings
~~~~~~~~~~~~~~~~~~~~

Sphinx will enable its ``RemovedInNextVersionWarning`` warnings by default, if
:envvar:`python:PYTHONWARNINGS` is not set.  Therefore you can disable them
using:

* ``PYTHONWARNINGS= make html`` (Linux/Mac)
* ``export PYTHONWARNINGS=`` and do ``make html`` (Linux/Mac)
* ``set PYTHONWARNINGS=`` and do ``make html`` (Windows)

But you can also explicitly enable the pending ones using e.g.
``PYTHONWARNINGS=default`` (see the :ref:`Python docs on configuring warnings
<python:describing-warning-filters>`) for more details.

Python version support policy
-----------------------------

Sphinx supports at all minor versions of Python released in the past 3 years
from the anticipated release date with a minimum of 3 minor versions of Python.
This policy is derived from `SPEC 0`_, a scientific Python domain standard.

.. _SPEC 0: https://scientific-python.org/specs/spec-0000/

For example, a version of Sphinx released in May 2025 would support Python 3.11,
3.12, and 3.13.

This is a summary table with the current policy:

=========== ======
Date        Python
=========== ======
05 Oct 2023 3.10+
----------- ------
04 Oct 2024 3.11+
----------- ------
24 Oct 2025 3.12+
----------- ------
01 Oct 2026 3.13+
----------- ------
01 Oct 2027 3.14+
=========== ======

Release procedures
------------------

The release procedures are listed in :file:`utils/release-checklist.rst`.
