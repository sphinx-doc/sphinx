Utilities
=========

Sphinx provides utility classes and functions to develop extensions.

Base classes for components
---------------------------

These base classes are useful to allow your extensions to obtain Sphinx
components (e.g. :class:`.Config`, :class:`.BuildEnvironment` and so on) easily.

.. note:: The subclasses of them might not work with bare docutils because they
          are strongly coupled with Sphinx.

.. autoclass:: sphinx.transforms.SphinxTransform
   :members:

.. autoclass:: sphinx.transforms.post_transforms.SphinxPostTransform
   :members:

.. autoclass:: sphinx.util.docutils.SphinxDirective
   :members:

.. autoclass:: sphinx.util.docutils.SphinxRole
   :members:

.. autoclass:: sphinx.util.docutils.ReferenceRole
   :members:

.. autoclass:: sphinx.transforms.post_transforms.images.ImageConverter
   :members:

Utility components
------------------

.. autoclass:: sphinx.events.EventManager
   :members:
