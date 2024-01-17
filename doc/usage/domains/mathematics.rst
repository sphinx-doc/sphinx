.. highlight:: rst

======================
The Mathematics Domain
======================

.. versionadded:: 1.8

The math domain (name **math**) provides the following roles:

.. rst:role:: math:numref

   Role for cross-referencing equations defined by :rst:dir:`math` directive
   via their label.  Example::

      .. math:: e^{i\pi} + 1 = 0
         :label: euler

      Euler's identity, equation :math:numref:`euler`, was elected one of the
      most beautiful mathematical formulas.

   .. versionadded:: 1.8
