test-domain-py-xref-ambiguous-annotation
=========================================

Multiple classes have an attribute called ``type``, and a data directive
uses ``type[...]`` in its annotation. The bare ``type`` in the annotation
should not trigger "more than one target found" warnings.

.. py:class:: Connector

   .. py:attribute:: type
      :type: str

.. py:class:: ConnectorPayload

   .. py:attribute:: type
      :type: str

.. py:data:: default
   :type: str | type[Sentinel]
