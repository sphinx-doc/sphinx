.. highlight:: rest

:mod:`sphinx.ext.ifconfig` -- Include content based on configuration
====================================================================

.. module:: sphinx.ext.ifconfig
   :synopsis: Include documentation content based on configuration values.

This extension is quite simple, and features only one directive:

.. directive:: ifconfig

   Include content of the directive only if the Python expression given as an
   argument is ``True``, evaluated in the namespace of the project's
   configuration (that is, all variables from :file:`conf.py` are available).

   For example, one could write ::

      .. ifconfig:: releaselevel in ('alpha', 'beta', 'rc')

         This stuff is only included in the built docs for unstable versions.
