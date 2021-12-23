.. _setuptools:

Setuptools integration
======================

.. versionremoved:: 5.0

Sphinx 0.5 to 4.x used to support an integration with distutils (and,
by extension, setuptools) through a custom ``build_sphinx`` command.

This support was removed in 5.0, since:

- this was built using ``distutils``, which has been deprecated
  in Python 3.10, according to :pep:`632`.
- this extended the ``setup.py``-based interface, which
  `is considered deprecated <setup.py-deprecated>` by the maintainers
  of ``setuptools`` and ``distutils``.
- this did not have feature-parity with the ``sphinx-build`` command
  line script, which caused subtle issues and additional maintenance
  workload (for Sphinx maintainers as well as downstream users) due to
  these behaviour differences.

Projects which depend upon this integration should switch to using
``sphinx-build`` directly.

.. _setup.py-deprecated: https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
