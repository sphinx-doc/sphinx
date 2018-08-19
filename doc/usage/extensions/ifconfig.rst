.. highlight:: rest

:mod:`sphinx.ext.ifconfig` -- Include content based on configuration
====================================================================

.. module:: sphinx.ext.ifconfig
   :synopsis: Include documentation content based on configuration values.

This extension is quite simple, and features only one directive:

.. rst:directive:: ifconfig

   Include content of the directive only if the Python expression given as an
   argument is ``True``, evaluated in the namespace of the project's
   configuration (that is, all registered variables from :file:`conf.py` are
   available).

   For example, one could write ::

      .. ifconfig:: releaselevel in ('alpha', 'beta', 'rc')

         This stuff is only included in the built docs for unstable versions.

   To make a custom config value known to Sphinx, use
   :func:`~sphinx.application.Sphinx.add_config_value` in the setup function in
   :file:`conf.py`, e.g.::

      def setup(app):
          app.add_config_value('releaselevel', '', 'env')

   The second argument is the default value, the third should always be ``'env'``
   for such values (it selects if Sphinx re-reads the documents if the value
   changes).
