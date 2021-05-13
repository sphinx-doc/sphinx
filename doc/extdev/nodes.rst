.. _nodes:

Doctree node classes added by Sphinx
====================================

.. module:: sphinx.addnodes

Nodes for domain-specific object descriptions
---------------------------------------------

Top-level nodes
...............

These nodes form the top-most levels of object descriptions.

.. autoclass:: desc
.. autoclass:: desc_signature
.. autoclass:: desc_signature_line
.. autoclass:: desc_content
.. autoclass:: desc_inline

Nodes for high-level structure in signatures
............................................

These nodes occur in in non-multiline :py:class:`desc_signature` nodes
and in :py:class:`desc_signature_line` nodes.

.. autoclass:: desc_name
.. autoclass:: desc_addname

.. autoclass:: desc_type
.. autoclass:: desc_returns
.. autoclass:: desc_parameterlist
.. autoclass:: desc_parameter
.. autoclass:: desc_optional
.. autoclass:: desc_annotation

New admonition-like constructs
------------------------------

.. autoclass:: versionmodified
.. autoclass:: seealso

Other paragraph-level nodes
-------------------------------

.. autoclass:: compact_paragraph

New inline nodes
----------------

.. autoclass:: index
.. autoclass:: pending_xref
.. autoclass:: pending_xref_condition
.. autoclass:: literal_emphasis
.. autoclass:: download_reference

Special nodes
-------------

.. autoclass:: only
.. autoclass:: meta
.. autoclass:: highlightlang

You should not need to generate the nodes below in extensions.

.. autoclass:: glossary
.. autoclass:: toctree
.. autoclass:: start_of_file
.. autoclass:: productionlist
.. autoclass:: production
