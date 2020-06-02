========================
Sphinx's release process
========================

Branch Model
------------

Sphinx project uses following branches for developing that conforms to
`Semantic Versioning 2.0.0`__.

.. __: https://semver.org/

``master``
    Development for next release. Typically this is a MINOR release. New
    features are allowed but must be backwards-compatible, preserving API
    compatibility.

``devel``
    Development for the next MAJOR release. All changes including incompatible
    behaviors and public API updates are allowed.

``A.B.x`` (ex. ``2.4.x``)
    Where ``A.B.x`` is the ``MAJOR.MINOR.PATCH`` release.  Only
    backwards-compatible bug fixes are allowed. In Sphinx project, PATCH
    version is used for urgent bug fix.

    ``MAJOR.MINOR.PATCH`` branch will be branched from the ``v`` prefixed
    release tag (for example, make ``2.3.1`` that branched from ``v2.3.0``)
    when a urgent release is needed. When new PATCH version is released, the
    branch will be deleted and replaced by an equivalent tag (ex. v2.3.1).


Release schedule
----------------

Sphinx uses a time-based release schedule with releases roughly every three
months. Every fourth release is a major version, in which it is possible to
make :ref:`breaking changes <deprecation-policy>`. Future releases are listed
on `GitHub <https://github.com/sphinx-doc/sphinx/milestones>`.


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

Release procedures
------------------

The release procedures are listed in ``utils/release-checklist``.
