Some additional anchors to exercise ignore code

* `Valid url <http://localhost:7777/>`_
* `Bar anchor invalid (trailing slash) <http://localhost:7777/#!bar>`_
* `Bar anchor invalid <http://localhost:7777#!bar>`_ tests that default ignore anchor of #! does not need to be prefixed with /
* `Top anchor invalid <http://localhost:7777/#top>`_
* `'does-not-exist' anchor invalid <http://localhost:7777#does-not-exist>`_
* `Valid local file <conf.py>`_
* `Invalid local file <path/to/notfound>`_

.. image:: http://localhost:7777/image.png
.. figure:: http://localhost:7777/image2.png

* `Valid anchored url <http://localhost:7777/anchor.html#found>`_
