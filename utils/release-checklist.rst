Release checklist
=================

A stable release is a release where the minor or micro version parts are
incremented.
A major release is a release where the major version part is incremented.

Checks
------

* open "https://github.com/sphinx-doc/sphinx/actions?query=branch:master" and all tests has passed
* Run ``git fetch; git status`` and check that nothing has changed

Bump version
------------

for stable and major releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``python utils/bump_version.py X.Y.Z``
* Check diff by ``git diff``
* ``git commit -am 'Bump to X.Y.Z final'``
* ``git tag vX.Y.Z -m "Sphinx X.Y.Z"``

for beta releases
~~~~~~~~~~~~~~~~~

* ``python utils/bump_version.py X.Y.0bN``
* Check diff by ``git diff``
* ``git commit -am 'Bump to X.Y.0 betaN'``
* ``git tag vX.Y.0b1 -m "Sphinx X.Y.0bN"``

Build Sphinx
------------

* ``make clean``
* ``python -m build .``
* ``twine upload dist/Sphinx-*``
* open https://pypi.org/project/Sphinx/ and check for any obvious errors

for stable and major releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``sh utils/bump_docker.sh X.Y.Z``

Bump to next development version
--------------------------------

for stable and major releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``python utils/bump_version.py --in-develop X.Y.Z+1b0`` (ex. 1.5.3b0)

for beta releases
~~~~~~~~~~~~~~~~~

* ``python utils/bump_version.py --in-develop X.Y.0bN+1`` (ex. 1.6.0b2)

Commit version bump
-------------------

* Check diff by ``git diff``
* ``git commit -am 'Bump version'``
* ``git push origin master --tags``

Final steps
-----------

* Add new version/milestone to tracker categories
* Write announcement and send to sphinx-dev, sphinx-users and python-announce
